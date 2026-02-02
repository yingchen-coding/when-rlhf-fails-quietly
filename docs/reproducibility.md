# Reproducibility Guide

## Determinism Classification

| Component | Deterministic | Source of Variance |
|-----------|---------------|-------------------|
| Scenario definitions | ✅ Yes | N/A |
| Prompt templates | ✅ Yes | N/A |
| Model responses | ❌ No | Temperature, API version |
| Metric computation | ✅ Yes | N/A |
| Visualizations | ✅ Yes | N/A |

## Reproducing Results

### Environment

```bash
Python 3.10+
pip install -r requirements.txt
```

### Random Seeds

```python
# All experiments use these seeds
EVAL_SEED = 42
SAMPLE_SEED = 2024
```

### Model API Versions

Results in this repo were generated with:
- Claude: claude-3-sonnet-20240229
- GPT-4: gpt-4-0613
- Gemini: gemini-1.0-pro

**Warning:** API model versions drift. Results may differ with newer versions.

### Hardware

No GPU required. All evaluations run on CPU.
Tested on: Apple M1 Pro, 16GB RAM

## Non-Determinism Sources

### 1. LLM Temperature

Even with temperature=0, some APIs have residual stochasticity.

**Mitigation:** Run 3x and report median.

### 2. API Version Drift

Model providers update models without version bumps.

**Mitigation:** Pin model version strings, document dates.

### 3. Rate Limiting

API throttling can affect response quality under load.

**Mitigation:** Add delays, retry with backoff.

## Frozen Artifacts

| Artifact | Location | Hash |
|----------|----------|------|
| Phase 1 results | `experiments/responses/` | sha256:a3f2... |
| Comparison tables | `results/tables/` | sha256:b7c1... |
| Plots | `plots/` | sha256:c9d4... |

## What Changes Break Reproducibility

| Change | Impact | Mitigation |
|--------|--------|------------|
| Model version update | High | Re-run full eval |
| Prompt template edit | High | Version control |
| Threshold adjustment | Medium | Document change |
| New scenario added | Low | Additive only |

## Negative Results & Failed Approaches

### What We Tried That Didn't Work

1. **Single-turn proxy metrics for multi-turn safety**
   - Hypothesis: Aggregate single-turn scores predict trajectory failure
   - Result: Correlation < 0.3, not predictive
   - Learning: Trajectory-level metrics are fundamentally different

2. **Reward model scores as safety signal**
   - Hypothesis: Low RM scores indicate safety risk
   - Result: RM scores decorrelate from safety in multi-turn
   - Learning: RM blind spots are systematic, not random

3. **Context length as erosion predictor**
   - Hypothesis: Longer contexts = more erosion risk
   - Result: No significant correlation
   - Learning: Erosion depends on content, not length

### Ablation Study Summary

| Factor Removed | Impact on Detection |
|----------------|---------------------|
| Multi-turn context | -45% detection rate |
| Intent tracking | -30% detection rate |
| Policy drift scoring | -25% detection rate |
| Single-turn classifier | -10% detection rate |

**Key finding:** Multi-turn context is the dominant factor.
