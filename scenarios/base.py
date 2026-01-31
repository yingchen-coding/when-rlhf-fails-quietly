"""
Base classes for scenario generation and evaluation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import json


class FailureMode(Enum):
    """Categories of silent alignment failures."""
    EPISTEMIC_COMPLIANCE = "epistemic_compliance"
    INTENT_DRIFT = "intent_drift"
    REWARD_HACKING = "reward_hacking"
    POLICY_CIRCUMVENTION = "policy_circumvention"
    OVERCONFIDENCE = "overconfidence"
    FRAMING_SENSITIVITY = "framing_sensitivity"


class Severity(Enum):
    """Failure severity levels."""
    PASS = "pass"           # Correct behavior
    WARNING = "warning"     # Minor deviation
    FAIL = "fail"           # Clear failure
    CRITICAL = "critical"   # Severe failure with potential harm


@dataclass
class Turn:
    """A single turn in a multi-turn interaction."""
    role: str  # 'user' or 'assistant'
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """Result of running a scenario against a model."""
    scenario_name: str
    model_name: str
    turns: list[Turn]
    metrics: dict[str, float]
    severity: Severity
    failure_mode: Optional[FailureMode] = None
    notes: str = ""
    raw_outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'scenario_name': self.scenario_name,
            'model_name': self.model_name,
            'turns': [{'role': t.role, 'content': t.content, 'metadata': t.metadata} for t in self.turns],
            'metrics': self.metrics,
            'severity': self.severity.value,
            'failure_mode': self.failure_mode.value if self.failure_mode else None,
            'notes': self.notes,
        }

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class Prompt:
    """A prompt with metadata for evaluation."""
    id: str
    content: str
    phase: int
    category: str
    expected_behavior: str
    failure_indicators: list[str] = field(default_factory=list)
    context: Optional[str] = None  # Prior context if multi-turn


class BaseScenario(ABC):
    """
    Base class for scenario generators.

    Each scenario defines:
    1. What prompts to generate
    2. How to evaluate responses
    3. What metrics to compute
    """

    name: str = "base"
    description: str = "Base scenario"
    failure_mode: FailureMode = FailureMode.EPISTEMIC_COMPLIANCE

    @abstractmethod
    def generate_prompts(self) -> list[Prompt]:
        """
        Generate prompts for this scenario.

        Returns:
            List of Prompt objects to evaluate
        """
        pass

    @abstractmethod
    def evaluate_response(self, prompt: Prompt, response: str) -> dict[str, Any]:
        """
        Evaluate a single response.

        Args:
            prompt: The prompt that was sent
            response: The model's response

        Returns:
            Dictionary with evaluation results including:
            - severity: Severity level
            - metrics: Dict of metric name -> value
            - indicators: List of detected failure indicators
        """
        pass

    def evaluate_trajectory(self, turns: list[Turn]) -> dict[str, Any]:
        """
        Evaluate a multi-turn trajectory.

        Override this for scenarios that need trajectory-level analysis.
        Default implementation evaluates each turn independently.

        Args:
            turns: List of Turn objects representing the conversation

        Returns:
            Dictionary with trajectory-level evaluation results
        """
        results = []
        for i, turn in enumerate(turns):
            if turn.role == 'assistant':
                # Find corresponding user prompt
                if i > 0 and turns[i-1].role == 'user':
                    prompt = Prompt(
                        id=f"turn_{i}",
                        content=turns[i-1].content,
                        phase=0,
                        category="trajectory",
                        expected_behavior="maintain_alignment"
                    )
                    results.append(self.evaluate_response(prompt, turn.content))

        # Aggregate results
        if not results:
            return {'severity': Severity.PASS, 'metrics': {}, 'indicators': []}

        # Return worst severity
        severities = [r['severity'] for r in results]
        worst = max(severities, key=lambda s: list(Severity).index(s))

        return {
            'severity': worst,
            'metrics': self._aggregate_metrics([r['metrics'] for r in results]),
            'indicators': [ind for r in results for ind in r.get('indicators', [])],
            'turn_results': results
        }

    def _aggregate_metrics(self, metrics_list: list[dict]) -> dict:
        """Aggregate metrics across turns."""
        if not metrics_list:
            return {}

        aggregated = {}
        all_keys = set(k for m in metrics_list for k in m.keys())

        for key in all_keys:
            values = [m.get(key, 0) for m in metrics_list if key in m]
            if values:
                aggregated[f"{key}_mean"] = sum(values) / len(values)
                aggregated[f"{key}_max"] = max(values)
                aggregated[f"{key}_min"] = min(values)

        return aggregated
