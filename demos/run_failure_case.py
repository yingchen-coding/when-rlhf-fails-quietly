#!/usr/bin/env python3
"""
Run a documented failure case and display results.

Usage:
    python demos/run_failure_case.py --case intent_drift --model claude-3 --seed 42
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from repro import FAILURE_CASES, ReproRunner


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce a documented RLHF failure case"
    )
    parser.add_argument(
        "--case",
        required=True,
        help="Failure case ID (e.g., intent_drift_01, policy_erosion_02)"
    )
    parser.add_argument(
        "--model",
        default="mock",
        help="Model to use (default: mock for demonstration)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for results (JSON)"
    )

    args = parser.parse_args()

    # Validate case exists
    if args.case not in FAILURE_CASES:
        print(f"Error: Unknown case '{args.case}'")
        print(f"Available cases: {', '.join(FAILURE_CASES.keys())}")
        sys.exit(1)

    print(f"=" * 60)
    print(f"REPRODUCING FAILURE CASE: {args.case}")
    print(f"Model: {args.model}")
    print(f"Seed: {args.seed}")
    print(f"=" * 60)

    # Run reproduction
    runner = ReproRunner(model=args.model)
    result = runner.run_case(args.case, verbose=True)

    # Summary
    print(f"\n{'=' * 60}")
    print("REPRODUCTION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Case: {result['case_id']}")
    print(f"Category: {result['category']}")
    print(f"Severity: {result['severity']}")
    print(f"Failure Reproduced: {'YES' if result['reproduced'] else 'NO'}")

    if result['reproduced']:
        print(f"Failure Turn: {result['failure_turn']} (expected: {result['expected_failure_turn']})")
        match_status = "MATCH" if result['match_expected'] else "MISMATCH"
        print(f"Expected Turn Match: {match_status}")

    # Save results if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
