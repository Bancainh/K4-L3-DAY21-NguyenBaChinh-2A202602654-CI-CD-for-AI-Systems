import importlib.util
from pathlib import Path
from unittest.mock import Mock

import boto3
import joblib
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def serving(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACT_BUCKET", "test-income-bucket")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    s3 = Mock()
    model = Mock()
    model.predict.return_value = [1]
    create_client = Mock(return_value=s3)
    monkeypatch.setattr(boto3, "client", create_client)
    monkeypatch.setattr(joblib, "load", Mock(return_value=model))
    source = Path(__file__).resolve().parents[1] / "src" / "serve.py"
    spec = importlib.util.spec_from_file_location("income_test_serve", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with TestClient(module.app) as client:
        yield client, module, model, s3, create_client


def test_startup_downloads_current_model(serving):
    _, module, _, s3, create_client = serving
    assert Path(module.MODEL_PATH).parent.is_dir()
    create_client.assert_called_once_with("s3")
    s3.download_file.assert_called_once_with(
        "test-income-bucket", "artifacts/current/model.joblib", module.MODEL_PATH
    )
    joblib.load.assert_called_once_with(module.MODEL_PATH)


def test_healthz(serving):
    client, *_ = serving
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("prediction,label", [(0, "thu_nhap_thap"), (1, "thu_nhap_cao")])
def test_score(serving, prediction, label):
    client, _, model, *_ = serving
    model.predict.return_value = [prediction]
    features = [28, 2, 14, 2, 11, 0, 1, 0, 0, 45]
    response = client.post("/score", json={"features": features})
    assert response.status_code == 200
    assert response.json() == {"prediction": prediction, "label": label}
    model.predict.assert_called_once_with([features])


@pytest.mark.parametrize("count", [0, 9, 11])
def test_score_requires_ten_features(serving, count):
    client, _, model, *_ = serving
    response = client.post("/score", json={"features": [0.0] * count})
    assert response.status_code == 400
    model.predict.assert_not_called()
