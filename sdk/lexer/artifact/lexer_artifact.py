# Standard imports
import logging
from datetime import datetime
from pathlib import Path

# Third party imports
from pydantic.dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Metadata:
    title: str
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


@dataclass
class LexerArtifact:
    """
    This class encapsulates all Lexer zip artifact modules
    """

    file_paths: list[Path]
    metadata: Metadata = Metadata(title="")
