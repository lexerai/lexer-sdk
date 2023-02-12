# Standard imports
from pathlib import Path

# Third party imports
from pydantic.dataclasses import dataclass


@dataclass
class Output:
    pass


@dataclass
class ONNXOutput(Output):
    onnx_file: Path


@dataclass
class ExportOutput(Output):
    onnx: ONNXOutput
