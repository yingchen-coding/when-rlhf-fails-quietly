"""
Scenario generators for evaluating silent alignment failures.

Each scenario targets a specific failure mode that is difficult to detect
with single-turn or static benchmarks.
"""

from .base import BaseScenario, ScenarioResult
from .epistemic_compliance import EpistemicComplianceScenario
from .intent_drift import IntentDriftScenario
from .reward_hacking import RewardHackingScenario

__all__ = [
    'BaseScenario',
    'ScenarioResult',
    'EpistemicComplianceScenario',
    'IntentDriftScenario',
    'RewardHackingScenario',
]

# Registry of available scenarios
SCENARIOS = {
    'epistemic_compliance': EpistemicComplianceScenario,
    'intent_drift': IntentDriftScenario,
    'reward_hacking': RewardHackingScenario,
}


def get_scenario(name: str) -> type:
    """Get scenario class by name."""
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[name]


def list_scenarios() -> list[str]:
    """List all available scenario names."""
    return list(SCENARIOS.keys())
