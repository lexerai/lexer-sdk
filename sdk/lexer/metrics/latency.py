# Standard imports
import logging

# Third party imports
from numpy import float64
from pydantic.dataclasses import dataclass

# Lexer imports
from lexer.metrics.metrics import Metrics

logger = logging.getLogger(__name__)


@dataclass
class LatencyMetrics(Metrics):
    num_samples: int
    variance: float64
    mean_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    throughput_per_sec: float
