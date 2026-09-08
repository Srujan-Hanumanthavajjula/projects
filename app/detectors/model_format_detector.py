from pathlib import Path


def _unknown_result(reason: str) -> dict:
    """
    Create a standard result for an unknown or invalid model.
    """

    return {
        "format": "UNKNOWN",
        "confidence": 0.0,
        "valid": False,
        "reason": reason
    }


def detect_model_format(model_path: Path) -> dict:
    """
    Detect and perform basic validation of common
    computer-vision model formats.

    Supported formats:
    - ONNX
    - PyTorch
    - TorchScript
    - Unknown

    The detector uses the file extension to determine
    the expected format and then performs basic structural
    validation where the required library is available.
    """

    # --------------------------------------------------
    # File existence
    # --------------------------------------------------

    if not model_path.exists():

        return _unknown_result(
            "Model file does not exist"
        )

    if not model_path.is_file():

        return _unknown_result(
            "Model path is not a file"
        )

    extension = model_path.suffix.lower()

    # --------------------------------------------------
    # ONNX
    # --------------------------------------------------

    if extension == ".onnx":

        try:
            import onnx

            model = onnx.load(
                str(model_path)
            )

            onnx.checker.check_model(
                model
            )

            return {
                "format": "ONNX",
                "confidence": 1.0,
                "valid": True,
                "reason": (
                    "Valid ONNX model structure detected"
                )
            }

        except ImportError:

            return {
                "format": "ONNX",
                "confidence": 0.90,
                "valid": False,
                "reason": (
                    "ONNX extension detected, but "
                    "onnx validation package is unavailable"
                )
            }

        except Exception as error:

            return {
                "format": "ONNX",
                "confidence": 1.0,
                "valid": False,
                "reason": (
                    f"ONNX validation failed: {error}"
                )
            }

    # --------------------------------------------------
    # PyTorch
    # --------------------------------------------------

    if extension in {".pt", ".pth"}:

        try:
            import torch

            torch.load(
                str(model_path),
                map_location="cpu",
                weights_only=True
            )

            return {
                "format": "PYTORCH",
                "confidence": 1.0,
                "valid": True,
                "reason": (
                    "PyTorch model/checkpoint "
                    "loaded successfully"
                )
            }

        except ImportError:

            return {
                "format": "PYTORCH",
                "confidence": 0.90,
                "valid": False,
                "reason": (
                    "PyTorch extension detected, but "
                    "PyTorch validation package is unavailable"
                )
            }

        except Exception as error:

            return {
                "format": "PYTORCH",
                "confidence": 1.0,
                "valid": False,
                "reason": (
                    f"PyTorch validation failed: {error}"
                )
            }

    # --------------------------------------------------
    # TorchScript
    # --------------------------------------------------

    if extension in {
        ".torchscript",
        ".ts"
    }:

        try:
            import torch

            torch.jit.load(
                str(model_path),
                map_location="cpu"
            )

            return {
                "format": "TORCHSCRIPT",
                "confidence": 1.0,
                "valid": True,
                "reason": (
                    "Valid TorchScript model "
                    "loaded successfully"
                )
            }

        except ImportError:

            return {
                "format": "TORCHSCRIPT",
                "confidence": 0.90,
                "valid": False,
                "reason": (
                    "TorchScript extension detected, but "
                    "PyTorch validation package is unavailable"
                )
            }

        except Exception as error:

            return {
                "format": "TORCHSCRIPT",
                "confidence": 1.0,
                "valid": False,
                "reason": (
                    f"TorchScript validation failed: {error}"
                )
            }

    # --------------------------------------------------
    # Unknown format
    # --------------------------------------------------

    return _unknown_result(
        "Unsupported model format"
    )