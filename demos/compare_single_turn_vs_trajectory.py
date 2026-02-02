#!/usr/bin/env python3
"""
Compare single-turn vs trajectory-level metrics for a failure case.

This demonstrates why single-turn safety benchmarks miss trajectory-level failures.

Usage:
    python demos/compare_single_turn_vs_trajectory.py --case intent_drift_01 --model claude-3
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from repro import FAILURE_CASES
from counterfactuals.baseline_comparison import (
    CounterfactualAnalyzer,
    CounterfactualResult,
    BaselineType
)


def mock_model_fn(turns, config):
    """Mock model function for demonstration."""
    import random

    n_turns = len(config.get("turns_to_use", turns))
    memory_window = config.get("memory_window")

    # Single-turn baseline: low failure rate
    if memory_window == 0 or n_turns == 1:
        violated = random.random() < 0.12
    # Limited memory: moderate failure rate
    elif memory_window and memory_window < 5:
        violated = random.random() < 0.35
    # Full context: high failure rate
    else:
        violated = random.random() < 0.68

    return {
        "policy_violated": violated,
        "violation_turn": n_turns if violated else None
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare single-turn vs trajectory-level evaluation"
    )
    parser.add_argument(
        "--case",
        required=True,
        help="Failure case ID"
    )
    parser.add_argument(
        "--model",
        default="mock",
        help="Model to use"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=50,
        help="Number of samples per condition"
    )

    args = parser.parse_args()

    if args.case not in FAILURE_CASES:
        print(f"Error: Unknown case '{args.case}'")
        sys.exit(1)

    case = FAILURE_CASES[args.case]
    turns = case["turns"]

    print(f"=" * 60)
    print(f"COMPARING SINGLE-TURN VS TRAJECTORY METRICS")
    print(f"Case: {args.case}")
    print(f"Turns: {len(turns)}")
    print(f"Samples: {args.samples} per condition")
    print(f"=" * 60)

    analyzer = CounterfactualAnalyzer()

    # Run single-turn baseline
    print("\n[1/2] Running single-turn baseline...")
    single_result = analyzer.run_baseline(
        scenario_id=args.case,
        scenario_turns=turns,
        model_fn=mock_model_fn,
        baseline_type=BaselineType.SINGLE_TURN,
        n_samples=args.samples
    )

    # Run full trajectory
    print("[2/2] Running full trajectory evaluation...")
    trajectory_result = analyzer.run_baseline(
        scenario_id=args.case,
        scenario_turns=turns,
        model_fn=mock_model_fn,
        baseline_type=BaselineType.FULL_CONTEXT,
        n_samples=args.samples
    )

    # Compute attribution
    attribution = analyzer.compute_attribution(args.case)

    # Display results
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")

    print(f"\n--- Single-Turn Baseline ---")
    print(f"Failure Rate: {single_result.failure_rate:.1%}")
    print(f"Sample Size: {single_result.sample_size}")

    print(f"\n--- Full Trajectory ---")
    print(f"Failure Rate: {trajectory_result.failure_rate:.1%}")
    print(f"Avg Failure Turn: {trajectory_result.avg_failure_turn or 'N/A'}")
    print(f"Sample Size: {trajectory_result.sample_size}")

    print(f"\n--- Attribution Analysis ---")
    print(f"Delta: {trajectory_result.failure_rate - single_result.failure_rate:+.1%}")
    print(f"Attribution to Agentic Dynamics: {attribution.get('attribution_to_agentic', 0):.1%}")
    print(f"Interpretation: {attribution.get('interpretation', 'N/A')}")

    print(f"\n{'=' * 60}")
    print("KEY INSIGHT")
    print(f"{'=' * 60}")

    if attribution.get('attribution_to_agentic', 0) > 0.5:
        print("""
Single-turn metrics would show this scenario as LOW RISK.
Trajectory-level evaluation reveals the TRUE failure rate.

This demonstrates why evaluating only on single-turn benchmarks
creates a false sense of safety for multi-turn agentic systems.
        """)
    else:
        print("""
This scenario shows similar failure rates in both conditions.
The failure is primarily due to prompt difficulty, not
multi-turn dynamics.
        """)


if __name__ == "__main__":
    main()
