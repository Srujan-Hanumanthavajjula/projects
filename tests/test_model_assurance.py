from pathlib import Path

from app.services.model_assurance import run_model_assurance


def test_unknown_model_format(tmp_path: Path):

    model_file = tmp_path / "model.xyz"

    model_file.write_bytes(
        b"unknown model"
    )

    result = run_model_assurance(
        model_file
    )

    assert result["model_format"] == "UNKNOWN"
    assert result["model_risk"] == 70
    assert len(result["findings"]) == 1


def test_invalid_onnx_model(tmp_path: Path):

    model_file = tmp_path / "model.onnx"

    model_file.write_bytes(
        b"dummy onnx model"
    )

    result = run_model_assurance(
        model_file
    )

    assert result["model_format"] == "ONNX"
    assert result["format_valid"] is False
    assert result["model_risk"] == 100
    assert len(result["findings"]) == 1


def test_invalid_pytorch_model(tmp_path: Path):

    model_file = tmp_path / "model.pt"

    model_file.write_bytes(
        b"dummy pytorch model"
    )

    result = run_model_assurance(
        model_file
    )

    assert result["model_format"] == "PYTORCH"
    assert result["format_valid"] is False
    assert result["model_risk"] == 100
    assert len(result["findings"]) == 1


def test_invalid_torchscript_model(tmp_path: Path):

    model_file = tmp_path / "model.torchscript"

    model_file.write_bytes(
        b"dummy torchscript model"
    )

    result = run_model_assurance(
        model_file
    )

    assert result["model_format"] == "TORCHSCRIPT"
    assert result["format_valid"] is False
    assert result["model_risk"] == 100
    assert len(result["findings"]) == 1


def test_missing_model(tmp_path: Path):

    model_file = tmp_path / "missing.onnx"

    result = run_model_assurance(
        model_file
    )

    assert result["model_format"] == "UNKNOWN"
    assert result["model_risk"] == 70
    assert len(result["findings"]) == 1