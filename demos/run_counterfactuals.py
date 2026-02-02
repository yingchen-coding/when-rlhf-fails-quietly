#!/usr/bin/env python3
"""
Run counterfactual ablations to isolate failure causes.

Usage:
    python demos/run_counterfactuals.py --case intent_drift_01 --ablation no_memory
    python demos/run_counterfactuals.py --case intent_drift_01 --ablation all
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from repro import FAILURE_CASES
from counterfactuals.baseline_comparison import (
    CounterfactualAnalyzer,
    BaselineType
)


# Ablation configurations
ABLATIONS = {
    "no_memory": {
        "baseline_type": BaselineType.SINGLE_TURN,
        "description": "No conversation memory (single-turn)"
    },
    "window_1": {
        "baseline_type": BaselineType.WINDOW_1,
        "description": "Memory window of 1 turn"
    },
    "window_3": {
        "baseline_type": BaselineType.WINDOW_3,
        "description": "Memory window of 3 turns"
    },
    "window_5": {
        "baseline_type": BaselineType.WINDOW_5,
        "description": "Memory window of 5 turns"
    },
    "no_tools": {
        "baseline_type": BaselineType.NO_TOOLS,
        "description": "No tool access"
    },
    "full": {
        "baseline_type": BaselineType.FULL_CONTEXT,
        "description": "Full context (control)"
    }
}


def mock_model_fn(turns, config):
    """Mock model function with ablation-aware behavior."""
    import random

    memory_window = config.get("memory_window")
    tools_enabled = config.get("tools_enabled", True)

    # Base failure rate varies with memory window
    if memory_window == 0:
        base_rate = 0.10
    elif memory_window == 1:
        base_rate = 0.25
    elif memory_window == 3:
        base_rate = 0.45
    elif memory_window == 5:
        base_rate = 0.58
    else:
        base_rate = 0.68

    # Tools add additional risk
    if not tools_enabled:
        base_rate *= 0.8

    violated = random.random() < base_rate

    return {
        "policy_violated": violated,
        "violation_turn": len(config.get("turns_to_use", [])) if violated else None
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run counterfactual ablations"
    )
    parser.add_argument(
        "--case",
        required=True,
        help="Failure case ID"
    )
    parser.add_argument(
        "--ablation",
        required=True,
        choices=list(ABLATIONS.keys()) + ["all"],
        help="Ablation to run"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=50,
        help="Samples per condition"
    )

    args = parser.parse_args()

    if args.case not in FAILURE_CASES:
        print(f"Error: Unknown case '{args.case}'")
        sys.exit(1)

    case = FAILURE_CASES[args.case]
    turns = case["turns"]

    print(f"=" * 60)
    print(f"COUNTERFACTUAL ABLATION STUDY")
    print(f"Case: {args.case}")
    print(f"Ablation: {args.ablation}")
    print(f"=" * 60)

    analyzer = CounterfactualAnalyzer()

    # Determine which ablations to run
    if args.ablation == "all":
        ablations_to_run = list(ABLATIONS.keys())
    else:
        ablations_to_run = [args.ablation]

    results = {}

    for ablation_name in ablations_to_run:
        ablation = ABLATIONS[ablation_name]
        print(f"\n[Running] {ablation_name}: {ablation['description']}")

        result = analyzer.run_baseline(
            scenario_id=args.case,
            scenario_turns=turns,
            model_fn=mock_model_fn,
            baseline_type=ablation["baseline_type"],
            n_samples=args.samples
        )

        results[ablation_name] = {
            "failure_rate": result.failure_rate,
            "avg_failure_turn": result.avg_failure_turn,
            "description": ablation["description"]
        }

        print(f"  Failure Rate: {result.failure_rate:.1%}")

    # Display comparison
    print(f"\n{'=' * 60}")
    print("ABLATION COMPARISON")
    print(f"{'=' * 60}")
    print(f"\n{'Ablation':<15} {'Failure Rate':>15} {'Description'}")
    print("-" * 60)

    for name, data in sorted(results.items(), key=lambda x: x[1]["failure_rate"]):
        print(f"{name:<15} {data['failure_rate']:>14.1%}  {data['description']}")

    # Analysis
    if len(results) > 1:
        rates = [r["failure_rate"] for r in results.values()]
        max_rate = max(rates)
        min_rate = min(rates)
        spread = max_rate - min_rate

        print(f"\n{'=' * 60}")
        print("ANALYSIS")
        print(f"{'=' * 60}")
        print(f"Failure Rate Range: {min_rate:.1%} - {max_rate:.1%}")
        print(f"Spread: {spread:.1%}")

        if spread > 0.3:
            print("\nLARGE SPREAD detected.")
            print("Memory accumulation is a significant factor in this failure.")

            # Find the critical transition
            sorted_results = sorted(results.items(), key=lambda x: x[1]["failure_rate"])
            for i in range(len(sorted_results) - 1):
                name1, data1 = sorted_results[i]
                name2, data2 = sorted_results[i + 1]
                delta = data2["failure_rate"] - data1["failure_rate"]
                if delta > 0.15:
                    print(f"\nCritical transition: {name1} -> {name2} (+{delta:.1%})")

        else:
            print("\nSMALL SPREAD detected.")
            print("This failure is relatively stable across ablations.")
            print("Consider investigating other factors (prompt design, model behavior).")


if __name__ == "__main__":
    main()
