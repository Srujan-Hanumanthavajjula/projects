from pathlib import Path

from app.detectors.model_format_detector import (
    detect_model_format
)


def test_detect_onnx_format(tmp_path: Path):

    model_file = tmp_path / "model.onnx"

    model_file.write_bytes(
        b"dummy onnx model"
    )

    result = detect_model_format(
        model_file
    )

    assert result["format"] == "ONNX"
    assert result["valid"] is False


def test_detect_pytorch_format(tmp_path: Path):

    model_file = tmp_path / "model.pt"

    model_file.write_bytes(
        b"dummy pytorch model"
    )

    result = detect_model_format(
        model_file
    )

    assert result["format"] == "PYTORCH"
    assert result["valid"] is False


def test_detect_pytorch_pth_format(tmp_path: Path):

    model_file = tmp_path / "model.pth"

    model_file.write_bytes(
        b"dummy pytorch model"
    )

    result = detect_model_format(
        model_file
    )

    assert result["format"] == "PYTORCH"
    assert result["valid"] is False


def test_detect_torchscript_format(tmp_path: Path):

    model_file = tmp_path / "model.torchscript"

    model_file.write_bytes(
        b"dummy torchscript model"
    )

    result = detect_model_format(
        model_file
    )

    assert result["format"] == "TORCHSCRIPT"
    assert result["valid"] is False


def test_detect_unknown_model_format(tmp_path: Path):

    model_file = tmp_path / "model.xyz"

    model_file.write_bytes(
        b"unknown model"
    )

    result = detect_model_format(
        model_file
    )

    assert result["format"] == "UNKNOWN"
    assert result["valid"] is False


def test_missing_model_file(tmp_path: Path):

    model_file = tmp_path / "missing.onnx"

    result = detect_model_format(
        model_file
    )

    assert result["format"] == "UNKNOWN"
    assert result["valid"] is False