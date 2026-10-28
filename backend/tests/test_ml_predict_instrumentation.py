"""Run the actual predict method with a tiny CPU model, without AST dependencies.

Extracting the class avoids importing unavailable librosa/transformers/Lightning.
This verifies output preservation and instrumentation, not AST capacity.
"""
import ast
import logging
import math
from pathlib import Path
from time import monotonic

import pytest


def test_predict_output_preserved_and_preprocessing_forward_times_logged(caplog):
    torch = pytest.importorskip('torch')
    source = Path(__file__).resolve().parents[2] / 'ml-service/modules/model.py'
    module = ast.parse(source.read_text())
    class_node = next(node for node in module.body
                      if isinstance(node, ast.ClassDef) and node.name == 'LungSoundClassifier')
    isolated = ast.Module(body=[class_node], type_ignores=[])
    namespace = {'torch':torch, 'logger':logging.getLogger('isolated_ml_predict'),
                 'monotonic':monotonic}
    exec(compile(isolated, str(source), 'exec'), namespace)
    classifier = namespace['LungSoundClassifier'].__new__(namespace['LungSoundClassifier'])
    class TinyCPUModel(torch.nn.Module):
        def forward(self, inputs):
            return torch.tensor([[-2., 1.]])
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
