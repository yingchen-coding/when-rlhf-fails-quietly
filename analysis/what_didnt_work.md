# What Didn't Work: Negative Results Log

> Documenting failed approaches is as valuable as documenting successes.
> This log captures hypotheses that were tested and found ineffective.

---

## 1. Simple Keyword Detection for Hedging

**Hypothesis**: Hedging leakage can be detected by keyword patterns like "generally speaking", "in theory", "hypothetically".

**What we tried**:
- Built regex patterns for 47 hedging phrases
- Tested on 500 labeled responses

**Result**: **Failed**
- Precision: 34% (too many false positives)
- Recall: 61% (missed subtle hedging)

**Why it failed**:
- Many legitimate educational responses use similar language
- Sophisticated hedging doesn't use obvious markers
- Context determines whether hedging is harmful

**Lesson learned**: Hedging detection requires semantic understanding, not pattern matching.

---

## 2. Embedding Distance for Silent Failure Detection

**Hypothesis**: Silent failures can be detected by measuring embedding distance between "what was asked" and "what was provided".

**What we tried**:
- Computed cosine similarity between request and response embeddings
- Threshold-based classification (distance > 0.7 = potential leak)

**Result**: **Partially failed**
- Works for obvious cases (full compliance vs. refusal)
- Fails for hedging leakage (semantically similar to refusal)

**Why it failed**:
- Hedging responses are close to refusals in embedding space
- The "leak" is often a small part of a larger refusal
- Embedding distance doesn't capture information density

**Lesson learned**: Need information-theoretic metrics, not just semantic similarity.

---

## 3. Turn-by-Turn Labeling for Trajectory Analysis

**Hypothesis**: Labeling each turn independently and aggregating would capture trajectory-level failures.

**What we tried**:
- Independent per-turn safety classification
- Aggregation rules (any unsafe = trajectory unsafe)

**Result**: **Failed**
- Misses decomposition attacks entirely
- High false negative rate for gradual escalation

**Why it failed**:
- Each turn in decomposition attack IS individually safe
- Harm emerges from composition, not individual turns
- Aggregation can't capture emergent properties

**Lesson learned**: Trajectory-level evaluation requires trajectory-level features.

---

## 4. Reward Model Score as Safety Proxy

**Hypothesis**: Low reward model scores correlate with safety violations.

**What we tried**:
- Extracted reward model scores for responses
- Correlated with human safety labels

**Result**: **Inverse correlation in some cases**
- Helpful hedging responses get HIGH reward scores
- Terse refusals get LOWER reward scores

**Why it failed**:
- Reward models optimize for helpfulness, not safety
- Polite information leakage is rewarded
- This IS the problem we're studying

**Lesson learned**: Reward model scores are not safety indicators; they're part of the failure mechanism.

---

## 5. Fixed Threshold for Drift Detection

**Hypothesis**: A universal drift threshold (e.g., 0.5) can identify policy erosion.

**What we tried**:
- Applied fixed threshold across all scenarios
- Measured detection rate

**Result**: **Failed**
- Threshold too high: missed 40% of erosion cases
- Threshold too low: 60% false positive rate

**Why it failed**:
- Different attack types have different drift profiles
- Some attacks maintain low drift until final turn
- Context-dependent thresholds needed

**Lesson learned**: Drift thresholds must be adaptive or attack-type-specific.

---

## 6. LLM-as-Judge for Silent Failure Detection

**Hypothesis**: An LLM can reliably judge whether another LLM's response contains silent failures.

**What we tried**:
- GPT-4 as judge for Claude responses (and vice versa)
- Structured prompts asking "Does this response leak actionable information?"

**Result**: **Mixed**
- Agreement with human labels: 71%
- Systematic blind spots for subtle hedging
- Cross-model evaluation more reliable than self-evaluation

**Why it partially failed**:
- LLMs have similar blind spots to each other
- Subtle information leakage is hard to define precisely
- Judge LLM sometimes "understands" the leak and rates it as informative

**Lesson learned**: LLM-as-judge is useful for triage, not final labeling.

---

## Summary Table

| Approach | Success | Key Failure Mode |
|----------|---------|------------------|
| Keyword detection | No | Too many false positives |
| Embedding distance | Partial | Misses hedging |
| Per-turn labeling | No | Misses composition |
| Reward model proxy | No | Inverse correlation |
| Fixed drift threshold | No | Context-dependent |
| LLM-as-judge | Partial | Shared blind spots |

---

## Implications for Future Work

1. **Semantic analysis insufficient**: Need information-theoretic measures
2. **Per-turn analysis insufficient**: Need trajectory-level features
3. **Model-based detection has ceiling**: Human review required for ground truth
4. **Thresholds must be adaptive**: No universal cutoffs work

---

## Why Document This?

> "Negative results are results." — Science

This log serves three purposes:
1. **Avoid repeated mistakes**: Future work can skip known dead ends
2. **Demonstrate rigor**: Shows systematic exploration, not cherry-picking
3. **Guide research direction**: Failed approaches inform promising ones
