# Standard imports
import logging
import time
from dataclasses import asdict
from functools import partial

# Third party imports
import click

# Lexer imports
from lexer.artifact.lexer_artifact_manager import LexerArtifactManager
from lexer.configs.loader import ConfigLoader
from lexer.onnx.benchmark import ONNXRuntimeBenchmark
from lexer.onnx.runtime import ONNXRuntime
from lexer.pytorch.benchmark import PyTorchBenchmark
from lexer.pytorch.export import PytorchExport
from lexer.utils.benchmark_results import BenchmarkResult
from lexer.utils.csv_utils import (
    generate_output_csv_name,
    generate_output_csv_stream,
)
from lexer.utils.numpy import to_numpy
from lexer.validation.validation import Validation

logger = logging.getLogger(__name__)


class _Lexer:
    def __init__(self, original_class_name, **kwargs):
        self.class_name = original_class_name
        self.decorator_based_dict = kwargs
        self.onnx_runtime = ONNXRuntime()

    # Not using this method yet.
    # def __call__(self, *args, **kwargs):
    #     pass

    def export_model(
        self,
        config_loader: ConfigLoader,
        artifact_manager: LexerArtifactManager,
        torch_model,
        input,
        **export_args,
    ):
        """
        This method exports the PyTorch model.
        """
        # Parse and "overwrite" the config for this nn.Module by merging any
        # decorator based args with the export_model function args
        # (the decorator and "this" set of function
        # arguments two take precedence).
        export_model_config = config_loader.parse_decorator_config(
            decorator_dict=self.decorator_based_dict | export_args
        )
        artifact_manager.update_artifact_metadata_section(
            key="export", model_config=export_model_config
        )
        # Workaround for ONNX output files for now.
        export_model_config.output_config_internal.onnx_output_filename = (
            self.class_name + ".onnx"
        )
        self.pytorch_export = PytorchExport(
            model_config=export_model_config, artifact_manager=artifact_manager
        )

        start_time = time.perf_counter()
        export_output = self.pytorch_export.export(
            torch_model=torch_model,
            input=input,
        )
        end_time = time.perf_counter()
        run_time = end_time - start_time
        click.secho(
            "Finished model export in {run_time:.4f} secs".format(
                run_time=run_time
            ),
            fg="green",
            bold=True,
        )
        if export_model_config.export_config.enable_export_validation:
            msg = "enable_export_validation is set to True, "
            msg += "running functional validation for torch model..."
            click.secho(
                msg,
                fg="yellow",
                bold=True,
            )
            ort_outputs = self.onnx_runtime.run(
                onnx_file=export_output.onnx.onnx_file,
                input=to_numpy(pytorch_tensor=input),
            )
            torch_out = torch_model(input)
            validation = Validation()
            validation.compare_numpy(
                expected_outputs=to_numpy(pytorch_tensor=torch_out),
                actual_outputs=ort_outputs[0],
            )
        return export_output

    def benchmark_model(
        self,
        config_loader: ConfigLoader,
        artifact_manager: LexerArtifactManager,
        torch_model,
        input,
        **benchmark_args,
    ):
        """
        This method benchmarks the given PyTorch model
        """
        # Parse and "overwrite" the config for this nn.Module by merging any
        # decorator based args with the benchmark_model function args
        # (the decorator and "this" set of function arguments two
        # take precedence).
        benchmark_model_config = config_loader.parse_decorator_config(
            decorator_dict=self.decorator_based_dict | benchmark_args
        )
        artifact_manager.update_artifact_metadata_section(
            key="benchmark", model_config=benchmark_model_config
        )
        # Workaround for ONNX output files for now.
        benchmark_model_config.output_config_internal.onnx_output_filename = (
            self.class_name + ".onnx"
        )
        self.pytorch_export = PytorchExport(
            model_config=benchmark_model_config,
            artifact_manager=artifact_manager,
        )

        all_results: list[BenchmarkResult] = []
        if benchmark_model_config.benchmark_config.enable_onnxruntime:
            logger.info(
                "enable_onnxruntime option enabled, running benchmarks for ONNXRuntime..."  # noqa: E501
            )
            # Export the model first.
            export_output = self.export_model(
                config_loader=config_loader,
                artifact_manager=artifact_manager,
                torch_model=torch_model,
                input=input,
            )
            onnxruntime_benchmark = ONNXRuntimeBenchmark(
                batch_size=benchmark_model_config.export_config.batch_size
            )
            onnxruntime_results = onnxruntime_benchmark.benchmark(
                onnx_file=export_output.onnx.onnx_file,
                input=to_numpy(input),
                num_iterations=benchmark_model_config.benchmark_config.num_iterations,  # noqa: E501
            )
            all_results.extend(onnxruntime_results)

        if benchmark_model_config.benchmark_config.enable_pytorch:
            logger.info(
                "enable_pytorch option enabled, running benchmarks for PyTorch..."  # noqa: E501
            )
            pytorch_benchmark = PyTorchBenchmark(
                batch_size=benchmark_model_config.export_config.batch_size
            )
            pytorch_results = pytorch_benchmark.benchmark(
                torch_model=torch_model,
                input=input,
                num_iterations=benchmark_model_config.benchmark_config.num_iterations,  # noqa: E501
            )
            all_results.extend(pytorch_results)

        result_list_dict = [asdict(x) for x in all_results]
        result_list_dict_total = []
        for result_dict in result_list_dict:
            temp_dict = result_dict["latency_metrics"]
            temp_dict.update(**result_dict)
            temp_dict.pop("latency_metrics")
            result_list_dict_total.append(temp_dict)

        if benchmark_model_config.output_config.enable_csv:
            logger.info(
                "enable_csv option enabled, exporting benchmarks as CSV..."
            )
            output_file_name = generate_output_csv_name(
                name=torch_model.__class__.__name__
            )

            # Generate the output CSV in a /tmp directory then append it to
            # artifact_manager list.
            tmp_output_file = generate_output_csv_stream(
                output_file_name=output_file_name,
                input_list=result_list_dict_total,
            )
            artifact_manager.append(file=tmp_output_file)

        if benchmark_model_config.output_config.enable_stdout:
            logger.info("enable_stdout option enabled, flushing to stdout...")
            click.secho("Generated results:", fg="yellow", bold=True)
            click.secho("-------------------", fg="yellow", bold=True)
            click.secho(result_list_dict_total)


def Lexer(
    original_class=None,
    **lexer_decorator_args,
):
    if original_class is None:
        return partial(Lexer, **lexer_decorator_args)

    orig_init = original_class.__init__

    def __init__(self, *args, **kws):
        self.lexer = _Lexer(original_class.__name__, **lexer_decorator_args)
        orig_init(self, *args, **kws)  # Call the original __init__

    original_class.__init__ = (
        __init__  # Set the class' __init__ to the new one
    )
    return original_class
