# Standard imports
import logging
from pathlib import Path

# Third party imports
from pydantic.dataclasses import dataclass

# Lexer imports
from lexer.artifact.lexer_artifact_manager import LexerArtifactManager
from lexer.configs.loader import ConfigLoader

logger = logging.getLogger(__name__)

DEFAULT_TARGET_DIRECTORY = Path.cwd()


@dataclass
class LexerContext:
    config_loader = ConfigLoader()
    artifact_manager = LexerArtifactManager()

    def __init__(self):
        logger.info("Initializing Lexer context...")
        logger.info("Loading Lexer configs...")
        self.load_config()
        logger.info("Initializing Lexer artifact manager...")
        self.artifact_manager.init()

    def load_config(self):
        """
        Internal!
        Loads the Lexer configs
        """
        # Initialize and parse workspace level configs.
        self.config_loader.parse()

    def export(self, torch_model, input, **export_args):
        """
        This method exports the given PyTorch model and input. Please refer
        to our documentation for full set of options.

        Params
        ------
        torch_model (nn.Module): The PyTorch model.
        input: Input tensors to the PyTorch model.
        export_args: Other (both required and optional) arguments specific to
        the underlying export workflow. Please read our documentation for full
        details.
        """
        torch_model.lexer.export_model(
            config_loader=self.config_loader,
            artifact_manager=self.artifact_manager,
            torch_model=torch_model,
            input=input,
            **export_args,
        )

    def benchmark(self, torch_model, input, **benchmark_args):
        """
        This method benchmarks the given PyTorch model and input. Please refer
        to our documentation for full set of options.

        Params
        ------
        torch_model (nn.Module): The PyTorch model.
        input: Input tensors to the PyTorch model.
        benchmark_args: Other (both required and optional) arguments specific
        to the underlying benchmarking workflow. Please read our documentation
        for full details.
        """
        torch_model.lexer.benchmark_model(
            config_loader=self.config_loader,
            artifact_manager=self.artifact_manager,
            torch_model=torch_model,
            input=input,
            **benchmark_args,
        )

    def flush(
        self, name: str, target_directory: str = str(DEFAULT_TARGET_DIRECTORY)
    ):
        """
        This method takes in a name for the Lexer output artifact and target
        directory for where to place it.

        Params
        ------
        name: str - The name of the Lexer artifact.
        For example, "my_benchmarks" to export a "my_benchmarks.lexer"
        target_directory: str - The target directory for where to place this
        generated ".lexer" artifact. Current directory by default.
        """
        self.artifact_manager.export(
            name=name,
            target_directory=target_directory,
        )
