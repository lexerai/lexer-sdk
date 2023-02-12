# Third party imports
from pydantic.dataclasses import dataclass

# Lexer imports
from lexer.artifact.lexer_artifact_manager import LexerArtifactManager
from lexer.configs.config import AllConfig


@dataclass
class Export:
    model_config: AllConfig
    artifact_manager: LexerArtifactManager
