# External Validity & Generalization

*Applies to entire portfolio*

## Cross-Domain Generalization

### Domains Tested

| Domain | Coverage | Confidence |
|--------|----------|------------|
| General chat | High | High |
| Code generation | Medium | Medium |
| Medical/health | Low | Low |
| Financial | Low | Low |
| Legal | Minimal | Low |

### Domain-Specific Findings

| Finding | General | Code | Medical |
|---------|---------|------|---------|
| Policy erosion rate | 15% | 12% | 22% |
| Avg erosion turn | 4.2 | 5.1 | 3.8 |
| Detection accuracy | 78% | 82% | 71% |

**Key insight:** Medical/health domain shows faster erosion and lower detection accuracy. Domain-specific tuning needed.

## Distribution Shift Analysis

### Tested Shifts

| Shift Type | Impact on Results |
|------------|-------------------|
| English → Multilingual | Detection drops 15-25% |
| Direct harm → Dual-use | Detection drops 20-30% |
| Single-user → Multi-user | Not tested |
| Synthetic → Real traffic | Unknown |

### Language Generalization

| Language | Detection Rate | vs English |
|----------|----------------|------------|
| English | 78% | Baseline |
| Spanish | 71% | -7% |
| Chinese | 65% | -13% |
| Arabic | 62% | -16% |

**Limitation:** Most scenarios are English-first. Multilingual coverage is a gap.

### Dual-Use Content Challenge

Dual-use content (legitimate + potentially harmful) is systematically harder:

| Content Type | False Negative Rate | False Positive Rate |
|--------------|--------------------|--------------------|
| Direct harm | 8% | 5% |
| Dual-use | 28% | 12% |

**Implication:** Benchmark may underestimate real-world risk for dual-use scenarios.

## Known Generalization Failures

### Where Our Results Don't Transfer

1. **Novel attack vectors**
   - Our benchmarks test known patterns
   - Zero-day attacks will have different characteristics

2. **Different model architectures**
   - Results calibrated on transformer LLMs
   - May not apply to future architectures

3. **Production scale**
   - Tested on 1000s of trajectories
   - Production sees millions—rare failures matter more

4. **Adversarial adaptation**
   - Static benchmarks vs adaptive attackers
   - Real attackers learn and evolve

## Honest Limitations

### What We Cannot Claim

- ❌ Results generalize to all domains
- ❌ Results generalize to all languages
- ❌ Results predict production failure rates
- ❌ Results are stable under distribution shift

### What We Can Claim

- ✅ Results establish baseline on tested distribution
- ✅ Methodology is transferable to new domains
- ✅ Framework identifies what to measure
- ✅ Negative results highlight gaps

## Recommendations for Users

1. **Validate on your domain** before trusting our numbers
2. **Test multilingual** if deploying globally
3. **Monitor production** for distribution shift
4. **Re-evaluate periodically** as attacks evolve
