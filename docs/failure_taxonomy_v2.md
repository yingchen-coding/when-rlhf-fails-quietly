# Failure Taxonomy v2: Actionable Classification

## Overview

This document extends the phenomenological failure taxonomy (erosion, drift, hacking) with an actionable layer that maps failures to specific intervention points in the RLHF pipeline.

---

## Layer 1: Observable Phenomena

| Failure Type | Observable Behavior |
|--------------|---------------------|
| Policy Erosion | Gradual weakening of safety constraints over turns |
| Intent Drift | Shift from stated to hidden objectives |
| Reward Hacking | Optimizing proxy metrics while violating intent |
| Epistemic Failures | Overconfidence, false certainty, hallucination |

---

## Layer 2: Mechanistic Causes

### 2.1 Policy Misgeneralization

The model learned correct behavior on training distribution but fails to generalize to deployment scenarios.

**Root causes:**
- Training data lacks adversarial multi-turn examples
- Safety demonstrations are single-turn biased
- Distributional shift between eval and production

**Intervention:** Expand SFT data with trajectory-level adversarial examples.

### 2.2 Preference Model Blind Spots

The reward model (RM) has systematic gaps where it fails to distinguish safe from unsafe behavior.

**Root causes:**
- Human labelers didn't see certain attack patterns
- Comparative labeling masks absolute safety judgments
- RM trained on single-turn preferences

**Intervention:** Augment RM training with trajectory-level comparisons, add explicit safety classifiers as auxiliary reward.

### 2.3 Reward Shaping Side Effects

Auxiliary rewards (helpfulness, engagement) compete with safety objectives.

**Root causes:**
- Multi-objective optimization with implicit tradeoffs
- Safety reward too sparse (only penalizes extreme violations)
- Helpfulness reward is dense and dominates gradient

**Intervention:** Implement safety veto (hard constraint) rather than reward term, or use constrained RL.

### 2.4 Context Window Exploitation

Adversaries exploit the model's limited context handling to inject harmful context.

**Root causes:**
- Attention patterns favor recent tokens
- Safety context gets "pushed out" by adversarial padding
- No explicit context integrity verification

**Intervention:** Add context-level safeguards independent of model attention.

---

## Layer 3: Intervention Points Map

```
┌────────────────────────────────────────────────────────────────────┐
│                      RLHF PIPELINE                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PRETRAIN ─────────────────────────────────────────────────────┐   │
│      │                                                          │   │
│      │  Intervention: Safety-aware pretraining data curation   │   │
│      │  Effectiveness: LOW (too early, too diffuse)            │   │
│      ▼                                                          │   │
│  SFT (Supervised Fine-Tuning) ──────────────────────────────┐  │   │
│      │                                                       │  │   │
│      │  Intervention: Multi-turn safety demonstrations       │  │   │
│      │  Effectiveness: MEDIUM (shapes behavior directly)     │  │   │
│      ▼                                                       │  │   │
│  RLHF (Reward Model + PPO) ─────────────────────────────┐   │  │   │
│      │                                                   │   │  │   │
│      │  Intervention: Trajectory-level RM training       │   │  │   │
│      │  Intervention: Safety constraint in PPO           │   │  │   │
│      │  Effectiveness: HIGH (direct optimization target) │   │  │   │
│      ▼                                                   │   │  │   │
│  POST-HOC SAFEGUARDS ────────────────────────────────┐  │   │  │   │
│      │                                                │  │   │  │   │
│      │  Intervention: Output filtering, escalation   │  │   │  │   │
│      │  Effectiveness: HIGH (last line of defense)   │  │   │  │   │
│      │  BUT: Doesn't fix root cause                  │  │   │  │   │
│      ▼                                                │  │   │  │   │
│  [DEPLOYMENT]                                         │  │   │  │   │
│                                                       │  │   │  │   │
└───────────────────────────────────────────────────────┴──┴───┴───┘
```

---

## Why Failures Appear in Deployment but Not in Eval

| Factor | Offline Eval | Production |
|--------|--------------|------------|
| **Distribution** | Curated, static | Adversarial, evolving |
| **Turn depth** | Usually 1-3 turns | 10+ turns common |
| **Attacker sophistication** | Template-based | Adaptive, creative |
| **Context length** | Short, clean | Long, noisy |
| **Stakes** | Academic | Real harm potential |

### Key Insight

Offline eval optimizes for **average-case safety** on known distributions.
Production requires **worst-case safety** on unknown distributions.

This gap cannot be closed by scaling eval alone—it requires:
1. Adversarial eval that anticipates distribution shift
2. Runtime safeguards that don't assume benign inputs
3. Incident feedback loops that update both

---

## Recommended Intervention Priority

1. **Post-hoc safeguards** (immediate, defensive)
   - Pre-action intent classification
   - Trajectory monitoring
   - Escalation policies

2. **RLHF-level changes** (medium-term, root cause)
   - Trajectory-level reward modeling
   - Safety constraints in PPO objective
   - Adversarial RL training

3. **SFT augmentation** (medium-term, preventive)
   - Multi-turn safety demonstrations
   - Decomposition-aware examples
   - Recovery behavior training

4. **Pretraining changes** (long-term, foundational)
   - Safety-aware data curation
   - Constitutional AI integration
   - Debate/deliberation architectures

---

## Open Questions

- Can we prove safety guarantees without post-hoc safeguards?
- How do we balance helpfulness and safety in multi-objective RL?
- What's the minimal post-hoc safeguard set for deployment?
