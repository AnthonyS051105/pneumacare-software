import librosa
import torch
from torch import nn
import pytorch_lightning as pl
from transformers import ASTFeatureExtractor
from torchmetrics.classification import (
    MulticlassAccuracy,
    MulticlassF1Score,
)
from transformers import (
    ASTConfig,
    ASTForAudioClassification,
    get_cosine_schedule_with_warmup,
)
import numpy as np

MODEL_NAME = "MIT/ast-finetuned-audioset-10-10-0.4593"
MAX_LEN = 512
SR = 16000
DURATION = 5
TARGET_LENGTH = SR * DURATION

def crop_ast_position_embeddings(model, max_length):
    emb = model.audio_spectrogram_transformer.embeddings
    cfg = model.config

    f_dim = (cfg.num_mel_bins - cfg.patch_size) // cfg.frequency_stride + 1
    old_t = (cfg.max_length - cfg.patch_size) // cfg.time_stride + 1
    new_t = (max_length - cfg.patch_size) // cfg.time_stride + 1
    if new_t > old_t:
        raise ValueError("max_length baru tidak boleh lebih besar dari bawaan.")

    pos = emb.position_embeddings.data
    special, patch = pos[:, :2], pos[:, 2:]
    D = patch.shape[-1]

    patch = patch.reshape(1, f_dim, old_t, D)
    start = (old_t - new_t) // 2
    patch = patch[:, :, start:start + new_t, :]
    patch = patch.reshape(1, f_dim * new_t, D)

    emb.position_embeddings = nn.Parameter(torch.cat([special, patch], dim=1))
    cfg.max_length = max_length
    emb.config.max_length = max_length
    return model

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

class RespiratoryAST(pl.LightningModule):
    def __init__(
        self,
        num_classes=2,
        learning_rate=3e-5,
        weight_decay=1e-2,
        pretrained=True,
        max_length=512,
        warmup_ratio=0.1,
    ):
        super().__init__()
        self.save_hyperparameters()

        if pretrained:
            self.model = ASTForAudioClassification.from_pretrained(
                MODEL_NAME,
                num_labels=num_classes,
                ignore_mismatched_sizes=True,
            )
            crop_ast_position_embeddings(self.model, max_length)
        else:
            config = ASTConfig(max_length=max_length, num_labels=num_classes)
            self.model = ASTForAudioClassification(config)

        self.criterion = nn.CrossEntropyLoss()

        self.train_acc = MulticlassAccuracy(num_classes=num_classes)
        self.val_acc = MulticlassAccuracy(num_classes=num_classes)
        self.val_f1 = MulticlassF1Score(num_classes=num_classes, average="macro")
        self.test_acc = MulticlassAccuracy(num_classes=num_classes)
        self.test_f1 = MulticlassF1Score(num_classes=num_classes, average="macro")

    def forward(self, x):
        return self.model(input_values=x).logits

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
        self.model.eval()
        x = self.preprocess(input_data).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(x)
        probs = torch.softmax(logits, dim=-1)[0]
        return {
            "class" : int(probs.argmax()),
            "confidence" : float(probs.max()),
            "probabilities" : probs.tolist()
        }

    def wav_to_ast(self, y, sr=16000):
        out = self.extractor(y, sampling_rate=sr, return_tensors="pt")
        return out["input_values"].squeeze(0)