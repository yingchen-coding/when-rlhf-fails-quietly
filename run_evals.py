#!/usr/bin/env python3
"""
When RLHF Fails Quietly - Evaluation Harness

Main entry point for running silent alignment failure evaluations.

Usage:
    # Run single scenario
    python run_evals.py --model ollama:llama3.1 --scenario epistemic_compliance

    # Run all scenarios
    python run_evals.py --model ollama:llama3.1 --all

    # Run multi-turn trajectory evaluation
    python run_evals.py --model ollama:llama3.1 --scenario intent_drift --trajectory

    # Compare multiple models
    python run_evals.py --models ollama:llama3.1,ollama:mistral,ollama:qwen2.5 --scenario epistemic_compliance

    # Generate report
    python run_evals.py --report results/evals/
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from scenarios import list_scenarios, get_scenario
from evals.runner import EvalRunner, EvalConfig, get_backend


def run_single(
    model_spec: str,
    scenario_name: str,
    output_dir: Path,
    trajectory: bool = False,
    verbose: bool = False
) -> dict:
    """Run single model/scenario evaluation."""
    config = EvalConfig(
        model_spec=model_spec,
        scenario_name=scenario_name,
        output_dir=output_dir,
        verbose=verbose
    )

    runner = EvalRunner(config)

    if trajectory:
        results = runner.run_trajectory()
    else:
        results = runner.run()

    runner.save_results(results)
    return results


def run_all_scenarios(
    model_spec: str,
    output_dir: Path,
    verbose: bool = False
) -> dict:
    """Run all scenarios for a single model."""
    all_results = {}

    for scenario_name in list_scenarios():
        print(f"\n{'#'*60}")
        print(f"# Scenario: {scenario_name}")
        print(f"{'#'*60}")

        results = run_single(model_spec, scenario_name, output_dir, verbose=verbose)
        all_results[scenario_name] = results

    return all_results


def run_comparison(
    model_specs: list[str],
    scenario_name: str,
    output_dir: Path,
    verbose: bool = False
) -> dict:
    """Run same scenario across multiple models for comparison."""
    comparison_results = {
        'scenario': scenario_name,
        'timestamp': datetime.now().isoformat(),
        'models': {}
    }

    for model_spec in model_specs:
        print(f"\n{'#'*60}")
        print(f"# Model: {model_spec}")
        print(f"{'#'*60}")

        results = run_single(model_spec, scenario_name, output_dir, verbose=verbose)
        comparison_results['models'][model_spec] = results

    # Generate comparison summary
    comparison_results['summary'] = generate_comparison_summary(comparison_results['models'])

    # Save comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_path = output_dir / f"comparison_{scenario_name}_{timestamp}.json"
    with open(comparison_path, 'w') as f:
        json.dump(comparison_results, f, indent=2)

    print(f"\nComparison saved to: {comparison_path}")
    return comparison_results


def generate_comparison_summary(model_results: dict) -> dict:
    """Generate summary comparing model performance."""
    summary = {
        'rankings': [],
        'pass_rates': {},
        'critical_failures': {}
    }

    for model, results in model_results.items():
        if 'summary' in results:
            pass_rate = results['summary'].get('pass_rate', 0)
            severity_counts = results['summary'].get('severity_counts', {})

            summary['pass_rates'][model] = pass_rate
            summary['critical_failures'][model] = severity_counts.get('critical', 0)

    # Rank by pass rate
    summary['rankings'] = sorted(
        summary['pass_rates'].keys(),
        key=lambda m: summary['pass_rates'][m],
        reverse=True
    )

    return summary


def generate_report(results_dir: Path) -> str:
    """Generate markdown report from results directory."""
    results_files = list(results_dir.glob("*.json"))

    if not results_files:
        return "No results found."

    report_lines = [
        "# Silent Alignment Failure Evaluation Report",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"\nResults analyzed: {len(results_files)} files",
        "\n---\n"
    ]

    # Group by scenario
    by_scenario = {}
    for file_path in results_files:
        with open(file_path) as f:
            data = json.load(f)
        scenario = data.get('scenario', 'unknown')
        if scenario not in by_scenario:
            by_scenario[scenario] = []
        by_scenario[scenario].append((file_path.name, data))

    for scenario, results in by_scenario.items():
        report_lines.append(f"## {scenario.replace('_', ' ').title()}\n")

        for filename, data in results:
            model = data.get('model', 'unknown')
            summary = data.get('summary', {})

            report_lines.append(f"### {model}\n")
            report_lines.append(f"- Pass Rate: {summary.get('pass_rate', 0)*100:.1f}%")
            report_lines.append(f"- Severities: {summary.get('severity_counts', {})}")
            report_lines.append("")

    return "\n".join(report_lines)


def print_banner():
    """Print startup banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     When RLHF Fails Quietly - Evaluation Harness              ║
║                                                               ║
║     Detecting Silent Alignment Failures in LLMs               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description="Run silent alignment failure evaluations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--model", "-m",
        help="Single model specification (e.g., ollama:llama3.1)"
    )
    parser.add_argument(
        "--models",
        help="Comma-separated list of models for comparison"
    )
    parser.add_argument(
        "--scenario", "-s",
        choices=list_scenarios(),
        help="Scenario to run"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all scenarios"
    )
    parser.add_argument(
        "--trajectory", "-t",
        action="store_true",
        help="Run multi-turn trajectory evaluation"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("results/evals"),
        help="Output directory"
    )
    parser.add_argument(
        "--report", "-r",
        type=Path,
        help="Generate report from results directory"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios"
    )

    args = parser.parse_args()

    # Handle special actions
    if args.list_scenarios:
        print("Available scenarios:")
        for name in list_scenarios():
            scenario_class = get_scenario(name)
            print(f"  - {name}: {scenario_class.description}")
        return

    if args.report:
        report = generate_report(args.report)
        print(report)
        return

    print_banner()

    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)

    # Run evaluations
    if args.models:
        # Multi-model comparison
        if not args.scenario:
            parser.error("--scenario required for model comparison")
        model_list = [m.strip() for m in args.models.split(",")]
        run_comparison(model_list, args.scenario, args.output, args.verbose)

    elif args.model:
        if args.all:
            # All scenarios for one model
            run_all_scenarios(args.model, args.output, args.verbose)
        elif args.scenario:
            # Single scenario
            run_single(
                args.model,
                args.scenario,
                args.output,
                args.trajectory,
                args.verbose
            )
        else:
            parser.error("Either --scenario or --all required")
    else:
        parser.error("Either --model or --models required")


if __name__ == "__main__":
    main()
