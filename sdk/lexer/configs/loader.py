# Standard imports
import logging
import os
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

# Third party imports
import tomlkit
from pydantic.dataclasses import dataclass

# Lexer imports
from lexer.configs.config import (
    AllConfig,
    BenchmarkConfig,
    DecoratorConfig,
    ExportConfig,
    OutputConfig,
)

DEFAULT_LEXER_CONFIG_FILENAME = ".lexer_config.toml"
DEFAULT_LEXER_CONFIG_PATH = Path.home()

logger = logging.getLogger(__name__)


def get_lexer_config_path() -> Path:
    """
    Returns the current LEXER_CONFIG_PATH env variable, if defined.
    Will return DEFAULT_LEXER_CONFIG_PATH otherwise.

    Returns
    -------
    LEXER_CONFIG_PATH: pathlib.Path
    """

    if os.getenv("LEXER_CONFIG_PATH") is None:
        warning_msg = "$LEXER_CONFIG_PATH not set, defaulting to {default_lexer_config_path} instead".format(  # noqa: E501
            default_lexer_config_path=DEFAULT_LEXER_CONFIG_PATH,
        )
        logger.warning(warning_msg)
        return DEFAULT_LEXER_CONFIG_PATH
    else:
        return Path(str(os.getenv("LEXER_CONFIG_PATH")))


@dataclass
class ConfigLoader:
    absolute_config_path: Path = get_lexer_config_path()
    lexer_config: AllConfig | None = None

    def parse_user_config(self) -> dict[str, Any]:
        """
        This method parses the user specified Lexer configs and returns
        them as a dictionary.
        """
        lexer_config_toml = None
        full_path = "{absolute_config_path}/{lexer_config_filename}".format(
            absolute_config_path=self.absolute_config_path,
            lexer_config_filename=DEFAULT_LEXER_CONFIG_FILENAME,
        )
        try:
            lexer_config_toml = tomlkit.loads(Path(full_path).read_text())
        except FileNotFoundError as e:
            warning_msg = "Could not find Lexer config file in {full_path}, defaulting to Lexer's default configurations".format(  # noqa: E501
                full_path=full_path
            )
            logger.warning(warning_msg)
            logger.debug(e)

        if lexer_config_toml is None:
            return dict()
        return lexer_config_toml

    def parse_lexer_internal_config(self) -> dict[str, Any]:
        """
        This method parses the internal Lexer configs and returns
        them as a dictionary.
        """
        lexer_config_toml = None

        full_path = os.path.join(
            os.path.dirname(__file__),
            "{lexer_config_filename}".format(
                lexer_config_filename=DEFAULT_LEXER_CONFIG_FILENAME,
            ),
        )
        try:
            lexer_config_toml = tomlkit.loads(Path(full_path).read_text())
        except FileNotFoundError as e:
            error_msg = "Could not find internal Lexer config file!"
            logger.error(error_msg)
            raise FileNotFoundError(e)

        return lexer_config_toml

    def parse_decorator_config(
        self, decorator_dict: dict[str, Any]
    ) -> AllConfig:
        if self.lexer_config is None:
            error_msg = "Internal: Expected type(lexer_config) attribute to be"
            error_msg += "AllConfig, got None instead"
            logger.error(error_msg)
            raise Exception(error_msg)

        result_dict = deepcopy(self.lexer_config)

        # Note that decorator_dict is "flat", ie. no TOML config file
        # "section" hierarchy.
        # This is why we can just update the internal dicts this way.

        # Update export_config
        result_dict.export_config.update(decorator_dict)

        # Update benchmark_config
        result_dict.benchmark_config.update(decorator_dict)

        # Update output_config
        result_dict.output_config.update(decorator_dict)

        # Create new instance of DecoratorConfig
        result_dict.decorator_config = DecoratorConfig(**decorator_dict)

        return result_dict

    def override_with_provided_config_dict(
        self, all_config: AllConfig, config_dict: dict[str, Any]
    ):
        """
        Internal helper method to override AllConfig instance with a provided
        dict[str, Any]
        """
        # Update export_config
        if "exports" in config_dict:
            user_export_config = config_dict["exports"]
            all_config.export_config.update(user_export_config)

        # Update benchmark_config
        if "benchmarks" in config_dict:
            user_benchmark_config = config_dict["benchmarks"]
            all_config.benchmark_config.update(user_benchmark_config)

        # Update output_config
        if "outputs" in config_dict:
            user_output_config = config_dict["outputs"]
            all_config.output_config.update(user_output_config)

        return all_config

    def override_internal_with_user_config(
        self, user_config_dict: dict[str, Any]
    ):
        """
        This method overrides the internal, in-memory config values
        with anything explicitly defined by the user_configs.
        """
        if self.lexer_config is None:
            error_msg = "Internal: Expected type(lexer_config) attribute"
            error_msg += "to be AllConfig, got None instead"
            logger.error(error_msg)
            raise Exception(error_msg)

        self.lexer_config = self.override_with_provided_config_dict(
            all_config=self.lexer_config, config_dict=user_config_dict
        )

    def parse(self):
        """
        This method parses the input configs based on the config path
        and maintains an in memory representation of it.
        """
        lexer_internal_config_dict = self.parse_lexer_internal_config()

        # We first initialize based on Lexer internal default configurations.
        self.lexer_config = AllConfig(
            export_config=ExportConfig(
                **lexer_internal_config_dict["exports"]
            ),
            benchmark_config=BenchmarkConfig(
                **lexer_internal_config_dict["benchmarks"]
            ),
            output_config=OutputConfig(
                **lexer_internal_config_dict["outputs"]
            ),
        )
        logger.debug("Lexer internal configs:")
        logger.debug(asdict(self.lexer_config))

        # Then now we parse user configs
        # then override internal configs with them.
        user_config_dict = self.parse_user_config()
        self.override_internal_with_user_config(
            user_config_dict=user_config_dict
        )

        logger.debug("Lexer configs after user config updates:")
        logger.debug(asdict(self.lexer_config))
