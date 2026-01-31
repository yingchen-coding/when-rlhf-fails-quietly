"""
Evaluation Runner for Silent Alignment Failure Tests.

Supports multiple model backends:
- Ollama (local open-weight models)
- OpenAI API (GPT-4, etc.)
- Anthropic API (Claude)
- Google AI (Gemini)

Usage:
    python -m evals.runner --model ollama:llama3.1 --scenario epistemic_compliance
    python -m evals.runner --model openai:gpt-4 --scenario intent_drift
    python -m evals.runner --model anthropic:claude-3-opus --scenario reward_hacking
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scenarios import get_scenario, list_scenarios, ScenarioResult
from scenarios.base import Severity, Turn, Prompt


class ModelBackend(Protocol):
    """Protocol for model backends."""

    def generate(self, prompt: str, context: Optional[list[dict]] = None) -> str:
        """Generate a response to the given prompt."""
        ...

    @property
    def name(self) -> str:
        """Return model name for logging."""
        ...


@dataclass
class EvalConfig:
    """Configuration for evaluation run."""
    model_spec: str  # e.g., "ollama:llama3.1"
    scenario_name: str
    output_dir: Path
    verbose: bool = False
    timeout: int = 120


class OllamaBackend:
    """Backend for Ollama local models."""

    def __init__(self, model_name: str, timeout: int = 120):
        self.model_name = model_name
        self.timeout = timeout

    @property
    def name(self) -> str:
        return f"ollama:{self.model_name}"

    def generate(self, prompt: str, context: Optional[list[dict]] = None) -> str:
        """Generate response using Ollama CLI."""
        # Build conversation if context provided
        if context:
            full_prompt = self._build_conversation(context, prompt)
        else:
            full_prompt = prompt

        try:
            result = subprocess.run(
                ["ollama", "run", self.model_name, full_prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "[TIMEOUT]"
        except FileNotFoundError:
            return "[ERROR: Ollama not found. Install from https://ollama.ai]"
        except Exception as e:
            return f"[ERROR: {str(e)}]"

    def _build_conversation(self, context: list[dict], current_prompt: str) -> str:
        """Build conversation string from context."""
        parts = []
        for msg in context:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                parts.append(f"User: {content}")
            else:
                parts.append(f"Assistant: {content}")
        parts.append(f"User: {current_prompt}")
        return "\n\n".join(parts)


class OpenAIBackend:
    """Backend for OpenAI API models."""

    def __init__(self, model_name: str = "gpt-4", timeout: int = 120):
        self.model_name = model_name
        self.timeout = timeout
        self._client = None

    @property
    def name(self) -> str:
        return f"openai:{self.model_name}"

    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI()
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        return self._client

    def generate(self, prompt: str, context: Optional[list[dict]] = None) -> str:
        """Generate response using OpenAI API."""
        messages = context or []
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                timeout=self.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[ERROR: {str(e)}]"


class AnthropicBackend:
    """Backend for Anthropic API models."""

    def __init__(self, model_name: str = "claude-3-opus-20240229", timeout: int = 120):
        self.model_name = model_name
        self.timeout = timeout
        self._client = None

    @property
    def name(self) -> str:
        return f"anthropic:{self.model_name}"

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic()
            except ImportError:
                raise ImportError("anthropic package required. Install with: pip install anthropic")
        return self._client

    def generate(self, prompt: str, context: Optional[list[dict]] = None) -> str:
        """Generate response using Anthropic API."""
        messages = context or []
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2048,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            return f"[ERROR: {str(e)}]"


def get_backend(model_spec: str, timeout: int = 120) -> ModelBackend:
    """
    Create model backend from specification.

    Args:
        model_spec: Model specification in format "provider:model_name"
                   e.g., "ollama:llama3.1", "openai:gpt-4", "anthropic:claude-3-opus"

    Returns:
        ModelBackend instance
    """
    if ":" not in model_spec:
        # Default to ollama for bare model names
        model_spec = f"ollama:{model_spec}"

    provider, model_name = model_spec.split(":", 1)

    backends = {
        "ollama": OllamaBackend,
        "openai": OpenAIBackend,
        "anthropic": AnthropicBackend,
    }

    if provider not in backends:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(backends.keys())}")

    return backends[provider](model_name, timeout=timeout)


class EvalRunner:
    """
    Main evaluation runner.

    Coordinates scenario generation, model queries, and result collection.
    """

    def __init__(self, config: EvalConfig):
        self.config = config
        self.backend = get_backend(config.model_spec, config.timeout)
        self.scenario_class = get_scenario(config.scenario_name)
        self.scenario = self.scenario_class()
        self.results: list[dict] = []

    def run(self) -> dict[str, Any]:
        """
        Run the full evaluation.

        Returns:
            Dictionary with evaluation results and metrics
        """
        print(f"\n{'='*60}")
        print(f"Running: {self.scenario.name}")
        print(f"Model: {self.backend.name}")
        print(f"{'='*60}\n")

        prompts = self.scenario.generate_prompts()
        total = len(prompts)

        for i, prompt in enumerate(prompts, 1):
            print(f"[{i}/{total}] {prompt.id}: {prompt.category}")

            if self.config.verbose:
                print(f"  Prompt: {prompt.content[:80]}...")

            # Generate response
            response = self.backend.generate(prompt.content)

            if self.config.verbose:
                print(f"  Response: {response[:200]}...")

            # Evaluate response
            eval_result = self.scenario.evaluate_response(prompt, response)

            result = {
                'prompt_id': prompt.id,
                'prompt_category': prompt.category,
                'prompt_content': prompt.content,
                'response': response,
                'severity': eval_result['severity'].value,
                'metrics': eval_result['metrics'],
                'indicators': eval_result.get('indicators', [])
            }
            self.results.append(result)

            # Print status
            severity_emoji = {
                'pass': '✅',
                'warning': '⚠️',
                'fail': '❌',
                'critical': '❌❌'
            }
            emoji = severity_emoji.get(eval_result['severity'].value, '?')
            print(f"  Result: {emoji} {eval_result['severity'].value.upper()}")

            if eval_result.get('indicators'):
                print(f"  Indicators: {', '.join(eval_result['indicators'][:3])}")
            print()

        return self._compile_results()

    def run_trajectory(self) -> dict[str, Any]:
        """
        Run multi-turn trajectory evaluation.

        For scenarios that test behavior across multiple turns.
        """
        print(f"\n{'='*60}")
        print(f"Running Trajectory: {self.scenario.name}")
        print(f"Model: {self.backend.name}")
        print(f"{'='*60}\n")

        # Check if scenario supports trajectory generation
        if not hasattr(self.scenario, 'generate_trajectory'):
            print("Scenario does not support trajectory evaluation")
            return self.run()

        trajectory = self.scenario.generate_trajectory()
        context = []

        for i, turn in enumerate(trajectory):
            if turn.role == 'user':
                print(f"[Turn {i//2 + 1}] User: {turn.content[:60]}...")

                # Generate response
                response = self.backend.generate(turn.content, context)
                print(f"  Assistant: {response[:100]}...")

                # Update the placeholder turn with actual response
                if i + 1 < len(trajectory):
                    trajectory[i + 1] = Turn(
                        role='assistant',
                        content=response,
                        metadata=trajectory[i + 1].metadata
                    )

                # Update context for next turn
                context.append({"role": "user", "content": turn.content})
                context.append({"role": "assistant", "content": response})
                print()

        # Evaluate full trajectory
        trajectory_result = self.scenario.evaluate_trajectory(trajectory)

        print(f"\n{'='*60}")
        print("Trajectory Evaluation Complete")
        severity_emoji = {
            'pass': '✅',
            'warning': '⚠️',
            'fail': '❌',
            'critical': '❌❌'
        }
        emoji = severity_emoji.get(trajectory_result['severity'].value, '?')
        print(f"Overall: {emoji} {trajectory_result['severity'].value.upper()}")
        print(f"{'='*60}\n")

        return {
            'scenario': self.scenario.name,
            'model': self.backend.name,
            'mode': 'trajectory',
            'trajectory_result': {
                'severity': trajectory_result['severity'].value,
                'metrics': trajectory_result['metrics'],
                'indicators': trajectory_result.get('indicators', [])
            }
        }

    def _compile_results(self) -> dict[str, Any]:
        """Compile results into summary format."""
        # Count severities
        severity_counts = {}
        for r in self.results:
            sev = r['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Calculate pass rate
        total = len(self.results)
        passes = severity_counts.get('pass', 0)
        pass_rate = passes / total if total > 0 else 0

        return {
            'scenario': self.scenario.name,
            'model': self.backend.name,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_prompts': total,
                'pass_rate': pass_rate,
                'severity_counts': severity_counts
            },
            'results': self.results
        }

    def save_results(self, results: dict[str, Any]) -> Path:
        """Save results to output directory."""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_safe = self.backend.name.replace(":", "_").replace("/", "_")
        filename = f"{self.scenario.name}_{model_safe}_{timestamp}.json"

        output_path = self.config.output_dir / filename

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Run silent alignment failure evaluations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m evals.runner --model ollama:llama3.1 --scenario epistemic_compliance
  python -m evals.runner --model openai:gpt-4 --scenario intent_drift --trajectory
  python -m evals.runner --model anthropic:claude-3-opus --scenario reward_hacking -v

Available scenarios:
""" + "\n".join(f"  - {s}" for s in list_scenarios())
    )

    parser.add_argument(
        "--model", "-m",
        required=True,
        help="Model specification (e.g., ollama:llama3.1, openai:gpt-4)"
    )
    parser.add_argument(
        "--scenario", "-s",
        required=True,
        choices=list_scenarios(),
        help="Scenario to run"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("results/evals"),
        help="Output directory for results"
    )
    parser.add_argument(
        "--trajectory", "-t",
        action="store_true",
        help="Run multi-turn trajectory evaluation"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout for model queries (seconds)"
    )

    args = parser.parse_args()

    config = EvalConfig(
        model_spec=args.model,
        scenario_name=args.scenario,
        output_dir=args.output,
        verbose=args.verbose,
        timeout=args.timeout
    )

    runner = EvalRunner(config)

    if args.trajectory:
        results = runner.run_trajectory()
    else:
        results = runner.run()

    runner.save_results(results)

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if 'summary' in results:
        print(f"Pass Rate: {results['summary']['pass_rate']*100:.1f}%")
        print(f"Severities: {results['summary']['severity_counts']}")


if __name__ == "__main__":
    main()
