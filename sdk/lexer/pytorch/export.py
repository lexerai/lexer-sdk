# Standard imports
import logging
from pathlib import Path

# Third party imports
import torch
from pydantic.dataclasses import dataclass

# Lexer imports
from lexer.base.export import Export
from lexer.onnx.checker import ONNXChecker
from lexer.onnx.loader import ONNXLoader
from lexer.output.output import ExportOutput, ONNXOutput

logger = logging.getLogger(__name__)


@dataclass
class PytorchExport(Export):
    @staticmethod
    def generate_absolute_tmp_directory(output_file_name: str) -> Path:
        """
        This function takes in an output filename, appends a /tmp directory to
        it then return the full path.
        """
        return Path("/tmp").joinpath(output_file_name)

    def export(
        self,
        torch_model,
        input,
    ) -> ExportOutput:
        """
        This method exports the model in various formats and returns the list
        of outputs accordingly.

        Params
        ------
        torch_model (nn.Module): The PyTorch model.
        input: Input tensors to the PyTorch model.
        """
        onnx_export = self.export_onnx(
            torch_model=torch_model,
            input=input,
        )
        return ExportOutput(onnx=onnx_export)

    def export_onnx(
        self,
        torch_model,
        input,
    ) -> ONNXOutput:
        """
        This method exports the current PyTorch model to ONNX.

        Params
        ------
        torch_model (nn.Module): The PyTorch model.
        input: Input tensors to the PyTorch model.
        """
        if self.model_config.decorator_config is None:
            error_msg = "Expected type(decorator_config) to be DecoratorConfig, but got None instead"  # noqa: E501
            logger.error(error_msg)
            raise Exception(error_msg)

        # Generate the output ONNX file in a /tmp directory first.
        tmp_output_onnx_file = self.generate_absolute_tmp_directory(
            output_file_name=self.model_config.output_config_internal.onnx_output_filename,  # noqa: E501
        )

        # Export the model
        torch.onnx.export(
            torch_model,
            input,  # model input or tuple
            str(tmp_output_onnx_file),
            export_params=True,
            opset_version=10,
            do_constant_folding=True,
            input_names=self.model_config.decorator_config.input_names,
            output_names=self.model_config.decorator_config.output_names,
            dynamic_axes={
                "input": {0: "batch_size"},  # variable length axes
                "output": {0: "batch_size"},
            },
        )
        # then append it to the artifact_manager list later.
        self.artifact_manager.append(file=tmp_output_onnx_file)

        if self.model_config.export_config.enable_onnx_checks:
            logger.info("Running checks on exported artifacts...")
            loader = ONNXLoader()
            onnx_model = loader.load(tmp_output_onnx_file)

            checker = ONNXChecker()
            checker.check(onnx_model)

        return ONNXOutput(onnx_file=tmp_output_onnx_file)
