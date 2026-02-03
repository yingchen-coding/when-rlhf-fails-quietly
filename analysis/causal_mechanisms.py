"""
Causal Mechanisms Analysis Module
=================================

Maps observed silent failures to their root causes in RLHF training dynamics.

This module does NOT:
- Run evaluations (that's eval-pipeline's job)
- Make release decisions (that's regression-suite's job)
- Generate attacks (that's stress-tests' job)

It ONLY provides causal analysis linking failure patterns to training artifacts.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import json


class RLHFArtifact(Enum):
    """RLHF training artifacts that cause silent failures."""

    REFUSAL_HARSHNESS_PENALTY = "over_penalize_refusal_harshness"
    LOCAL_REWARD_SHAPING = "local_reward_shaping"
    SAFETY_SPEC_AMBIGUITY = "safety_spec_ambiguity"
    DELEGATION_GAP = "delegation_gap"
    CREATIVE_COMPLIANCE_REWARD = "creative_compliance_reward"
    HELPFULNESS_PRESSURE = "helpfulness_pressure"


@dataclass
class CausalMechanism:
    """A causal link between failure type and RLHF artifact."""

    failure_type: str
    rlhf_artifact: RLHFArtifact
    explanation: str
    training_signal: str
    mitigation_layer: str


# Core causal mapping: Why each failure type occurs
CAUSAL_MECHANISMS: List[CausalMechanism] = [
    CausalMechanism(
        failure_type="hedging_leakage",
        rlhf_artifact=RLHFArtifact.REFUSAL_HARSHNESS_PENALTY,
        explanation="Model learns to soften refusals with hedging, inadvertently leaking information",
        training_signal="Preference data penalizes terse refusals; rewards nuanced responses",
        mitigation_layer="pre_action_intent_classifier"
    ),
    CausalMechanism(
        failure_type="decomposition_evasion",
        rlhf_artifact=RLHFArtifact.LOCAL_REWARD_SHAPING,
        explanation="Turn-by-turn reward optimization creates blind spots for multi-step composition",
        training_signal="RLHF evaluates single turns; no trajectory-level supervision",
        mitigation_layer="mid_trajectory_drift_monitor"
    ),
    CausalMechanism(
        failure_type="tool_handoff",
        rlhf_artifact=RLHFArtifact.DELEGATION_GAP,
        explanation="Tool calls exist in different output modality with weaker safety constraints",
        training_signal="Safety RLHF targets text generation; tool schemas not safety-tuned",
        mitigation_layer="post_action_tool_validator"
    ),
    CausalMechanism(
        failure_type="plausible_deniability",
        rlhf_artifact=RLHFArtifact.SAFETY_SPEC_AMBIGUITY,
        explanation="Model exploits gray areas in safety policy around dual-use information",
        training_signal="Ambiguous preference labels for borderline educational content",
        mitigation_layer="pre_action_intent_classifier"
    ),
    CausalMechanism(
        failure_type="compliance_framing",
        rlhf_artifact=RLHFArtifact.CREATIVE_COMPLIANCE_REWARD,
        explanation="Model rewarded for finding helpful framings even for borderline requests",
        training_signal="Preference for nuanced compliance over blunt refusal",
        mitigation_layer="mid_trajectory_drift_monitor"
    ),
]


def get_mechanism_for_failure(failure_type: str) -> Optional[CausalMechanism]:
    """Look up causal mechanism for a failure type."""
    for mechanism in CAUSAL_MECHANISMS:
        if mechanism.failure_type == failure_type:
            return mechanism
    return None


def generate_mechanism_report() -> Dict:
    """Generate a structured report of all causal mechanisms."""
    return {
        "title": "RLHF Silent Failure Causal Analysis",
        "summary": (
            "Many silent failures are not bugs, but incentives misaligned "
            "by RLHF reward shaping. This report maps failure types to their "
            "root causes in training dynamics."
        ),
        "mechanisms": [
            {
                "failure_type": m.failure_type,
                "rlhf_artifact": m.rlhf_artifact.value,
                "explanation": m.explanation,
                "training_signal": m.training_signal,
                "mitigation_layer": m.mitigation_layer
            }
            for m in CAUSAL_MECHANISMS
        ],
        "key_insight": (
            "RLHF optimizes for surface-level compliance signals. "
            "It does not robustly optimize against partial compliance, "
            "hedging leakage, or multi-step composition. "
            "As a result, many safety failures are silent, systematic, and predictable."
        )
    }


def map_failures_to_mitigations(failure_types: List[str]) -> Dict[str, List[str]]:
    """Map observed failures to recommended mitigation layers."""
    mitigation_map: Dict[str, List[str]] = {}

    for failure_type in failure_types:
        mechanism = get_mechanism_for_failure(failure_type)
        if mechanism:
            layer = mechanism.mitigation_layer
            if layer not in mitigation_map:
                mitigation_map[layer] = []
            mitigation_map[layer].append(failure_type)

    return mitigation_map


# Output schema for downstream consumption
OUTPUT_SCHEMA = {
    "description": "Causal mechanism analysis output format",
    "consumers": [
        "agentic-safeguards-simulator: Maps failures to safeguard hook placement",
        "safeguards-stress-tests: Converts failure types into attack templates",
        "agentic-safety-incident-lab: Root cause taxonomy for incident classification"
    ],
    "fields": {
        "failure_type": "Identifier from failure taxonomy",
        "rlhf_artifact": "Training artifact causing the failure",
        "explanation": "Human-readable causal explanation",
        "training_signal": "Specific training signal causing the issue",
        "mitigation_layer": "Recommended safeguard layer for mitigation"
    }
}


if __name__ == "__main__":
    report = generate_mechanism_report()
    print(json.dumps(report, indent=2))
