"""
Evaluation modules for silent alignment failure testing.
"""

from .runner import EvalRunner, EvalConfig, get_backend
from .metrics import (
    EpistemicMetrics,
    FramingMetrics,
    TrajectoryMetrics,
    FabricationMetrics,
    compute_all_metrics,
    compute_comparison_metrics,
    compute_trajectory_metrics,
)

__all__ = [
    'EvalRunner',
    'EvalConfig',
    'get_backend',
    'EpistemicMetrics',
    'FramingMetrics',
    'TrajectoryMetrics',
    'FabricationMetrics',
    'compute_all_metrics',
    'compute_comparison_metrics',
    'compute_trajectory_metrics',
]
