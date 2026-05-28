---
type: template
title: "Hand-Labeling Rubric Template"
created: 2026-05-27
updated: 2026-05-27
tags:
  - template
  - evals
  - labeling
  - iaa
status: stable
related:
  - "[[Inter-Annotator-Agreement]]"
  - "[[Judge-Calibration-Pilot-wiki-ingest]]"
  - "[[Research-Judge-Calibration-2026]]"
---

# Hand-Labeling Rubric Template

Copy this file into `wiki/eval/rubrics/<skill>-rubric.md` (or per-batch into `<skill>-rubric-<date>.md`). Fill every section. Empty sections produce labeler disagreement.

> [!key-insight] Design principle
> A short, concrete rubric applied consistently beats a long, hedged rubric applied subjectively. Target: a new labeler can score 20 items in 30 minutes after reading the rubric once. If they can't, the rubric is too long or too vague.

---

## 1. Task definition

**One sentence** describing what the labeler is judging.

> Example: "Score whether this `wiki-ingest` output correctly extracted the primary entities and key claims from the source document."

## 2. Input the labeler sees

List exactly what is shown for each item:

- [ ] Source document (full text or first 2000 tokens)
- [ ] Judge output to score
- [ ] Reference / gold answer (if applicable)
- [ ] Anything else the labeler needs (URL, metadata, prior context)

**Anti-pattern**: showing the labeler the model's chain-of-thought. The labeler scores the *output*, not the reasoning narrative — same logic as [[Judges-Must-Not-See-CoT]].

## 3. Primary label (the thing IAA is computed on)

Pick **one**:

- [ ] Binary: `PASS` / `FAIL`
- [ ] Ordinal: `1` (broken) — `5` (excellent)
- [ ] Categorical: `{correct, partially-correct, incorrect, off-topic}`

Recommended for the first rubric version: **binary**. Ordinal looks more informative but doubles the rubric work because labelers must agree on every gradation.

## 4. Dimensions (sub-scores, optional)

If the task has multiple aspects, list them. **Each dimension gets its own gold label**; the primary label is a function of the dimensions (e.g. PASS = all dimensions ≥ 4).

| Dimension | Description | Scale | Weight |
|---|---|---|---|
| Clarity | Output is unambiguous and well-structured | 1–5 | 0.2 |
| Completeness | Primary entities and claims are present | 1–5 | 0.4 |
| Faithfulness | No hallucinated facts | 1–5 | 0.3 |
| Source quality | Citations to authoritative sources | 1–5 | 0.1 |

**Default**: one dimension only for the first rubric version. Add dimensions when a failure pattern repeats across batches.

## 5. Concrete examples (3+ per label class)

For each value of the primary label, give 3 worked examples drawn from real prior outputs. **This is the single highest-leverage section of the rubric** — it kills 80% of would-be disagreements.

### Example: `PASS`

```
Source: <2-sentence summary of the source doc>
Output: <the judged output>
Why PASS: Names X, Y, Z entities. Claims A, B, C are faithful to the source.
```

### Example: `FAIL`

```
Source: <...>
Output: <...>
Why FAIL: Missed entity Y. Claim A is unsupported by the source.
```

## 6. Edge cases and "skip" criteria

When can a labeler abstain or mark as out-of-scope?

- [ ] Source document is corrupted or unreadable → mark `SKIP`, do not score
- [ ] Output is non-English when source is English → mark `SKIP`
- [ ] [Other domain-specific skip rule]

Track skip rate in pilot weekly summary; if skip rate > 5%, the input distribution is broken, not the rubric.

## 7. Adjudication protocol

When two labelers disagree:

1. Both labelers re-read the item and the rubric **without** seeing each other's label.
2. If still disagreeing, the adjudicator (named upfront, typically Philipp) makes the call with a **one-line rationale** appended to the item record.
3. Adjudicated label = **gold label** for that item.
4. If the same dimension drives ≥ 3 adjudications in a batch of 50, rewrite that dimension's description before the next batch.

## 8. Inter-annotator agreement target

- **Cohen's κ ≥ 0.80** on the primary label before the rubric ships to the judge as ground truth.
- **Co-report raw agreement and class prevalence** to detect the kappa paradox (see [[Inter-Annotator-Agreement]]).
- If κ < 0.70 after one rubric rewrite, the task is genuinely subjective or the rubric needs a third labeler — escalate.

## 9. Logistics

| | |
|---|---|
| Batch size | 50 items per session, hard cap |
| Session duration | 60 min max (fatigue → drift) |
| Calibration session | First 10 items per labeler are scored together, side-by-side, before independent labeling starts |
| Re-calibration | Every 4 weeks: 20 items co-labeled, compute κ, fix rubric drift |
| Tool | Markdown table in `wiki/eval/fixtures/<skill>-<date>.md`, git-tracked, one row per item |

## 10. Record schema (one row per item)

```yaml
case_id: <ulid>
source_path: ".raw/articles/<file>.md"
source_excerpt: "first 200 chars or summary"
judge_output_path: "wiki/eval/runs/<run_id>/<case_id>.json"
labels:
  - labeler: "labeler_A"
    primary: "PASS"
    dimensions: {clarity: 4, completeness: 5, faithfulness: 5}
    notes: "Strong on entity extraction."
    timestamp: "2026-05-27T10:15:00Z"
  - labeler: "labeler_B"
    primary: "PASS"
    dimensions: {clarity: 4, completeness: 4, faithfulness: 5}
    notes: ""
    timestamp: "2026-05-27T11:02:00Z"
adjudication:
  needed: false
  gold_label: "PASS"
  adjudicator: ""
  rationale: ""
```

## 11. Pilot adoption checklist

Before any judge is deployed against a rubric for the first time:

- [ ] Rubric written following this template, including ≥ 3 examples per label class.
- [ ] Calibration session held (first 10 items co-labeled).
- [ ] N ≥ 30 items independently double-labeled.
- [ ] Cohen's κ computed and ≥ 0.80.
- [ ] Kappa paradox check: raw agreement + class prevalence reported.
- [ ] Adjudicator named.
- [ ] Gold-label fixture committed to `wiki/eval/fixtures/`.
- [ ] Re-calibration date scheduled (4 weeks out).

Only then does the judge run against the fixture.

## Sources

- [Scale AI — Data Labeling: The Authoritative Guide](https://scale.com/guides/data-labeling-annotation-guide).
- [Dataannotationhub — The Annotator's Compass: Mastering Rubrics (Oct 2025)](https://dataannotationhub.com/2025/10/30/the-annotators-compass-mastering-rubrics-for-high-quality-ml-data/).
- [CVAT — Annotation Quality Assurance: Multi-Layered Approach](https://www.cvat.ai/resources/blog/annotation-quality-assurance).
- [Label Studio — Scale AI Evaluation with Rubrics and Calibration](https://labelstud.io/blog/how-to-scale-evaluation-for-rag-and-agent-workflows/).
- [LLM-Rubric arXiv:2501.00274](https://arxiv.org/pdf/2501.00274) — multidimensional calibrated rubric evaluation, motivates dimension weighting.
- [RULERS arXiv:2601.08654](https://arxiv.org/pdf/2601.08654) — locked-rubric, evidence-anchored scoring against drift.
