> **Portfolio**: [Safety Memo](https://yingchen-coding.github.io/safety-memos/) · [when-rlhf-fails-quietly](https://github.com/yingchen-coding/when-rlhf-fails-quietly) · [agentic-misuse-benchmark](https://github.com/yingchen-coding/agentic-misuse-benchmark) · [agentic-safeguards-simulator](https://github.com/yingchen-coding/agentic-safeguards-simulator) · [safeguards-stress-tests](https://github.com/yingchen-coding/safeguards-stress-tests) · [scalable-safeguards-eval-pipeline](https://github.com/yingchen-coding/scalable-safeguards-eval-pipeline) · [model-safety-regression-suite](https://github.com/yingchen-coding/model-safety-regression-suite) · [agentic-safety-incident-lab](https://github.com/yingchen-coding/agentic-safety-incident-lab)

# When RLHF Fails Quietly

> A research harness for surfacing silent alignment and safeguards failures in multi-turn, agentic LLM systems.

**Evaluating Silent Misalignment and Safety Failures in LLM Agents**

## Motivation

Reinforcement Learning from Human Feedback (RLHF) and prompt-based safeguards are widely used to align large language models with human intent.
However, in **agentic, multi-step, and adversarial settings**, these mechanisms often fail in ways that are difficult to observe using standard benchmarks.

In practice, many alignment failures are **silent**:
- The model appears aligned under typical evaluation metrics,
- Passes safety benchmarks and policy checks,
- Yet violates the underlying intent or safety constraints when deployed in realistic, multi-turn environments.

This project studies how and why RLHF and prompt-based control mechanisms **quietly break down** under:
- Partial observability
- Distribution shift
- Proxy reward objectives
- Multi-step agentic workflows

The goal is to provide **systematic evaluation tools** to surface these failures before they become safety-critical in real deployments.

---

## Failure Modes Studied

This repository focuses on failure patterns that are difficult to detect with single-turn or static benchmarks:

- **Reward Hacking under Proxy Objectives**
  The model optimizes for surface-level reward signals while violating latent intent constraints.

- **Multi-turn Intent Drift**
  The model gradually deviates from the original user intent or safety policy over long trajectories.

- **Policy Circumvention via Decomposition**
  Safety constraints are respected locally but violated through multi-step reasoning or task decomposition.

- **Overconfidence under Uncertainty**
  The model proceeds with unsafe actions when uncertainty is high, instead of deferring or requesting clarification.

- **Compounding Tool-Use Errors**
  Small hallucinations or tool misuse compound into larger unsafe outcomes in agentic workflows.

### Failure Taxonomy

| Scenario | Failure Mode | What It Tests |
|----------|--------------|---------------|
| `epistemic_compliance` | Overconfident compliance | False precision under uncertainty; safety vs epistemic restraint |
| `intent_drift` | Multi-turn intent erosion | Policy degradation over trajectories; resistance to repeated pressure |
| `reward_hacking` | Proxy reward exploitation | RLHF over-optimization; helpfulness that violates latent constraints |

---

## Evaluation Methodology

We implement evaluation harnesses designed to surface **trajectory-level misalignment**, rather than single-turn failures:

- **Adversarial Scenario Generation**
  Automatically generates prompts and task environments that stress reward proxies and safety boundaries.

- **Multi-turn Trajectory Analysis**
  Evaluates how behavior evolves across long-horizon interactions instead of single outputs.

- **Intent vs. Outcome Divergence Metrics**
  Measures the gap between the intended objective and realized behavior over time.

- **Partial Observability Stress Tests**
  Simulates incomplete or misleading state information to test robustness.

- **Looks-Correct-but-Is-Wrong Detection**
  Flags cases where outputs appear superficially correct while violating latent safety constraints.

---

## Key Findings (Preliminary)

- RLHF can optimize **surface behavior** while breaking latent intent in long-horizon tasks.
- Many misalignment failures only emerge after **N > 1 steps** and are invisible to single-turn benchmarks.
- Prompt-based safeguards degrade significantly under **distribution shift** and adversarial decomposition.
- Agentic settings amplify small reward mis-specifications into large behavioral failures.
- Standard evaluation pipelines systematically under-report these failure modes.

---

## Why This Matters for Alignment & Safeguards

Most current safety benchmarks evaluate **static outputs**.
This misses failure modes that emerge only when models are embedded in **interactive, multi-step, and partially observed environments**.

This work suggests the need for:
- **Trajectory-level safety evaluation**
- **Intent-aware metrics beyond reward proxies**
- **Adversarial and stress-test driven eval pipelines**
- **Scalable monitoring for subtle misbehavior patterns**

These findings are directly relevant to alignment, red-teaming, and safeguards efforts for agentic LLM systems.

---

## Reproducibility and Severity Calibration

This repository provides a one-command reproduction harness for all reported failure cases. Each case can be replayed deterministically with fixed seeds, backend configuration, and model versions.

In addition to qualitative failure analysis, we provide a calibrated severity rubric to quantify the operational risk of each failure. Severity levels are mapped to downstream release-gating decisions (OK / WARN / BLOCK) to ensure consistency between research findings and production safety policy.

### Counterfactual Controls

To isolate causal mechanisms behind observed failures, we provide counterfactual ablations including:
- No agent loop (single-turn baseline)
- Shortened memory windows
- Alternative reward models

These controls help distinguish agentic failure modes from prompt artifacts or backend-specific quirks.

---

## 5-Minute Demo Walkthrough

This demo reproduces a real trajectory-level alignment failure and shows how single-turn benchmarks fail to detect it.

### Step 1: Reproduce a Failure Case
```bash
python demos/run_failure_case.py --case intent_drift_01 --model claude-3 --seed 42
```

### Step 2: Compare Single-Turn vs Trajectory Metrics
```bash
python demos/compare_single_turn_vs_trajectory.py --case intent_drift_01 --model claude-3
```

### Step 3: Counterfactual Ablation
```bash
python demos/run_counterfactuals.py --case intent_drift_01 --ablation all
```

Expected outcome:
- Single-turn metrics show no violation.
- Trajectory-level divergence flags a policy breach.
- Counterfactual ablations localize the failure to agent memory accumulation.

---

## How to Use

```bash
# Single scenario evaluation
python run_evals.py --model ollama:llama3.1 --scenario epistemic_compliance

# Multi-turn trajectory analysis
python run_evals.py --model ollama:llama3.1 --scenario intent_drift --trajectory

# Cross-model comparison
python run_evals.py --models ollama:llama3.1,ollama:mistral,anthropic:claude-3-opus \
                    --scenario epistemic_compliance

# Generate report from results
python run_evals.py --report results/evals/
```

Key components:

- `scenarios/`: Adversarial scenario generators (epistemic_compliance, intent_drift, reward_hacking)
- `evals/`: Multi-backend runner (Ollama, OpenAI, Anthropic) + trajectory-level evaluation
- `evals/metrics.py`: Intent-vs-outcome divergence, policy erosion, framing drift measures
- `docs/design.md`: Methodology and metric design rationale

---

## Example Results (Preliminary)

| Model | Scenario | Single-Turn Pass | Trajectory Drift | Policy Erosion |
|-------|----------|------------------|------------------|----------------|
| Claude 3 Opus | epistemic_compliance | 100% | 0.08 | 0.00 |
| GPT-4 | epistemic_compliance | 30% | 0.34 | 0.22 |
| Llama 3.1 8B | intent_drift | 50% | 0.31 | 0.18 |
| Mistral 7B | reward_hacking | 25% | 0.44 | 0.38 |
| Qwen 2.5 7B | epistemic_compliance | 30% | 0.41 | 0.29 |

**Key observation**: Models that pass single-turn safety checks can still exhibit significant trajectory drift and policy erosion over multi-step interactions.

---

## Roadmap

- [ ] Expand coordinated misuse and collusion scenarios
- [ ] Add automated red-teaming loops
- [ ] Integrate interpretability probes for failure attribution
- [ ] Benchmark multiple models under identical stress tests
- [ ] Open-source eval templates for agentic safety testing

---

## Limitations & Future Work

- Current metrics rely on proxy signals for intent divergence; future work could integrate human-in-the-loop labeling for ground truth calibration.
- Scenario coverage is not exhaustive; coordinated multi-agent misuse and tool-use chains remain future work.
- Results are preliminary and designed to demonstrate failure modes, not to provide absolute safety rankings.
- Trajectory metrics assume access to full conversation history; real-time streaming evaluation requires additional engineering.

---

## Citation

If you reference this work in research or evaluation pipelines:

```bibtex
@misc{chen2026whenrlhffailsquietly,
  title  = {When RLHF Fails Quietly: Evaluating Silent Misalignment in LLM Agents},
  author = {Chen, Ying},
  year   = {2026}
}
```

---

## Contact

Ying Chen, Ph.D.
blueoceanally@gmail.com

LinkedIn: https://www.linkedin.com/in/ying-chen-8b25a730/

---

## Intended Use

This framework is designed for **evaluating silent failure modes in alignment and safeguards systems**, particularly in multi-turn, agentic, and partially observed environments. It supports red-teaming, safety evaluation, and monitoring workflows for deployed LLM agents.

The methodology and metrics are directly applicable to:
- Pre-deployment safety audits
- Continuous monitoring of production systems
- Red-team evaluation pipelines
- Alignment research on trajectory-level behaviors

---

## License

MIT

---

## Related Writing

- [Why Single-Turn Safety Benchmarks Systematically Underestimate Agentic Risk](https://yingchen-coding.github.io/safety-memos/)
