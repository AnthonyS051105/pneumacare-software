import logging
from time import monotonic

import librosa
import torch
from torch import nn
import pytorch_lightning as pl
from transformers import ASTFeatureExtractor
from torchmetrics.classification import (
    MulticlassAccuracy,
    MulticlassF1Score,
)
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
from transformers import get_cosine_schedule_with_warmup
import numpy as np

logger = logging.getLogger(__name__)

MODEL_NAME = "MIT/ast-finetuned-audioset-10-10-0.4593"
MAX_LEN = 512
SR = 16000
DURATION = 5
TARGET_LENGTH = SR * DURATION

def fix_length(y):
    y = np.asarray(y, dtype=np.float32)
    if len(y) == 0:
        return np.zeros(TARGET_LENGTH, dtype=np.float32)
    if len(y) < TARGET_LENGTH // 2:
        repeat_count = int(np.ceil(TARGET_LENGTH / len(y)))
        y = np.tile(y, repeat_count)
    if len(y) > TARGET_LENGTH:
        start = (len(y) - TARGET_LENGTH) // 2
        y = y[start:start + TARGET_LENGTH]

    if len(y) < TARGET_LENGTH:
        y = np.pad(y, (0, TARGET_LENGTH - len(y)))

    return y.astype(np.float32)

class RespiratoryClassifier(pl.LightningModule):
    def __init__(
        self,
        model_type="efficientnet_b0",
        num_classes=2,
        learning_rate=3e-5,
        weight_decay=1e-2,
        pretrained=True,
        max_length=512,
        warmup_ratio=0.1,
    ):
        super().__init__()
        self.save_hyperparameters()

        if model_type != "efficientnet_b0":
            raise ValueError("model_type harus 'efficientnet_b0'")
        weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
        self.model = efficientnet_b0(weights=weights)
        self.model.classifier[-1] = nn.Linear(
            self.model.classifier[-1].in_features, num_classes
        )

        self.criterion = nn.CrossEntropyLoss()

        self.train_acc = MulticlassAccuracy(num_classes=num_classes)
        self.val_acc = MulticlassAccuracy(num_classes=num_classes)
        self.val_f1 = MulticlassF1Score(num_classes=num_classes, average="macro")
        self.test_acc = MulticlassAccuracy(num_classes=num_classes)
        self.test_f1 = MulticlassF1Score(num_classes=num_classes, average="macro")

    def forward(self, x):
        x = x.transpose(1, 2).unsqueeze(1).repeat(1, 3, 1, 1)
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        preds = logits.argmax(dim=1)

        self.train_acc.update(preds, y)

        self.log("train_loss", loss, on_step=False, on_epoch=True,
                 prog_bar=True, batch_size=x.size(0))
        self.log("train_acc", self.train_acc, on_step=False, on_epoch=True,
                 prog_bar=True, batch_size=x.size(0))
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        preds = logits.argmax(dim=1)

        self.val_acc.update(preds, y)
        self.val_f1.update(preds, y)

        self.log("val_loss", loss, on_epoch=True, prog_bar=True, batch_size=x.size(0))
        self.log("val_acc", self.val_acc, on_epoch=True, prog_bar=True, batch_size=x.size(0))
        self.log("val_f1", self.val_f1, on_epoch=True, prog_bar=True, batch_size=x.size(0))

    def test_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        preds = logits.argmax(dim=1)

        self.test_acc.update(preds, y)
        self.test_f1.update(preds, y)

        self.log("test_loss", loss, on_epoch=True, batch_size=x.size(0))
        self.log("test_acc", self.test_acc, on_epoch=True, prog_bar=True, batch_size=x.size(0))
        self.log("test_f1", self.test_f1, on_epoch=True, prog_bar=True, batch_size=x.size(0))

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.hparams.learning_rate,
            weight_decay=self.hparams.weight_decay,
        )

        total_steps = self.trainer.estimated_stepping_batches
        warmup_steps = int(self.hparams.warmup_ratio * total_steps)
        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps,
        )

        return {
            "optimizer": optimizer,
            "lr_scheduler": {"scheduler": scheduler, "interval": "step"},
        }

class LungSoundClassifier:
    def __init__(self, model):
        self.model = model
        self.extractor = ASTFeatureExtractor.from_pretrained(MODEL_NAME, max_length=MAX_LEN)

    def preprocess(self, input_data, type="wav"):
        if type != "wav":
            raise ValueError(f"Tipe input tidak didukung: {type}")
        audio, sr = librosa.load(input_data, sr=16000, mono=True)
        audio = fix_length(audio)
        return self.wav_to_ast(audio, sr)

    def predict(self, input_data):
        started = monotonic()
        preprocessed_at = None
        input_device = "unknown"
        status = "error"
        try:
            self.model.eval()
            x = self.preprocess(input_data).unsqueeze(0)
            x = x.to(next(self.model.parameters()).device)
            preprocessed_at = monotonic()
            input_device = str(x.device)
            with torch.no_grad():
                logits = self.model(x)
            probs = torch.softmax(logits, dim=-1)[0]
            # Preserve calculations and serialization. Output conversion also waits
            # for accelerator work, so forward_output_ms is not just GPU enqueue time.
            result = {
                "class" : int(probs.argmax()),
                "confidence" : float(probs.max()),
                "probabilities" : probs.tolist()
            }
            status = "ok"
            return result
        finally:
            ended = monotonic()
            preprocessing_ms = ((preprocessed_at if preprocessed_at is not None else ended)
                                - started) * 1000
            forward_output_ms = ((ended - preprocessed_at) * 1000
                                 if preprocessed_at is not None else 0.0)
            logger.info("ml_prediction status=%s input_device=%s preprocessing_ms=%.3f "
                        "forward_output_ms=%.3f total_ms=%.3f", status, input_device,
                        preprocessing_ms, forward_output_ms, (ended - started) * 1000)

    def wav_to_ast(self, y, sr=16000):
        out = self.extractor(y, sampling_rate=sr, return_tensors="pt")
        return out["input_values"].squeeze(0)
