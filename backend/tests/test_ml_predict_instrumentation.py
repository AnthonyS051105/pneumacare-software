"""Run ML inference methods with tiny CPU models, without heavy dependencies.

Extracting the class avoids importing unavailable librosa/transformers/Lightning.
This verifies input layout, output preservation and instrumentation, not accuracy.
"""
import ast
import logging
import math
from pathlib import Path
from time import monotonic
from types import SimpleNamespace

import pytest


def test_predict_output_preserved_and_preprocessing_forward_times_logged(caplog, monkeypatch):
    torch = pytest.importorskip('torch')
    source = Path(__file__).resolve().parents[2] / 'ml-service/modules/model.py'
    module = ast.parse(source.read_text())
    class_node = next(node for node in module.body
                      if isinstance(node, ast.ClassDef) and node.name == 'LungSoundClassifier')
    isolated = ast.Module(body=[class_node], type_ignores=[])
    namespace = {'torch':torch, 'logger':logging.getLogger('isolated_ml_predict'),
                 'monotonic':monotonic}
    monkeypatch.setattr(namespace['logger'], 'propagate', True)
    exec(compile(isolated, str(source), 'exec'), namespace)
    classifier = namespace['LungSoundClassifier'].__new__(namespace['LungSoundClassifier'])
    class TinyCPUModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.logits = torch.nn.Parameter(torch.tensor([[-2., 1.]]))

        def forward(self, inputs):
            assert inputs.device == self.logits.device
            assert not torch.is_grad_enabled()
            return self.logits.detach()
    classifier.model = TinyCPUModel()
    classifier.preprocess = lambda _: torch.zeros(4)
    with caplog.at_level(logging.INFO):
        result = classifier.predict(b'opaque-input-not-read')
    expected = math.exp(3)/(1+math.exp(3))
    assert result['class'] == 1
    assert result['confidence'] == pytest.approx(expected)
    assert result['probabilities'] == pytest.approx([1-expected, expected])
    assert classifier.model.training is False
    assert any('ml_prediction status=ok' in r.getMessage()
               and 'preprocessing_ms=' in r.getMessage()
               and 'forward_output_ms=' in r.getMessage()
               and 'total_ms=' in r.getMessage()
               and 'input_device=cpu' in r.getMessage() for r in caplog.records)


def test_efficientnet_forward_converts_log_mel_to_three_channels():
    torch = pytest.importorskip('torch')
    source = Path(__file__).resolve().parents[2] / 'ml-service/modules/model.py'
    module = ast.parse(source.read_text())
    class_node = next(node for node in module.body
                      if isinstance(node, ast.ClassDef) and node.name == 'RespiratoryClassifier')
    namespace = {'pl': SimpleNamespace(LightningModule=torch.nn.Module)}
    exec(compile(ast.Module(body=[class_node], type_ignores=[]), str(source), 'exec'), namespace)
    classifier_type = namespace['RespiratoryClassifier']
    classifier = classifier_type.__new__(classifier_type)
    torch.nn.Module.__init__(classifier)
    features = torch.arange(24, dtype=torch.float32).reshape(2, 4, 3)

    class TinyCNN(torch.nn.Module):
        def forward(self, inputs):
            assert inputs.shape == (2, 3, 3, 4)
            for channel in range(3):
                torch.testing.assert_close(inputs[:, channel], features.transpose(1, 2))
            return torch.tensor([[1., 2.], [3., 4.]])

    classifier.model = TinyCNN()
    torch.testing.assert_close(classifier(features), torch.tensor([[1., 2.], [3., 4.]]))
