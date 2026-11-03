# Evaluation results

20 synthetic trade documents x 8 fields = 160 field checks per version.

| Prompt | JSON valid | Field accuracy | Perfect docs | Hallucinated fields |
|--------|-----------:|---------------:|-------------:|--------------------:|
| v1 | 85.0% | 74.4% | 5/20 | 9 |
| v2 | 100.0% | 96.2% | 14/20 | 4 |
| v3 | 100.0% | 99.4% | 19/20 | 0 |

**v1** — Naive single instruction, no output contract. Prose answers, broken JSON, and invented values for fields the document never stated.

**v2** — Few-shot example + step-by-step reasoning. Accuracy jumps and JSON is consistent, but the model still guesses missing fields instead of admitting they are absent.

**v3** — Explicit output contract: schema, formatting rules, 'null if not stated', and the document wrapped in delimiters. Hallucinated fields drop to zero.
