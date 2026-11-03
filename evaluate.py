"""Score the raw model responses against ground truth.

Metrics per prompt version:
- JSON validity: did the response parse as a single JSON object?
- Field accuracy: of all fields across all documents, how many match
  ground truth after normalization (dates, amounts, casing)?
- Perfect documents: documents where every field is exactly right.
- Hallucinated fields: fields the model filled in when the document
  did not state them (ground truth null). This is the metric that
  matters most for government document work: a confident wrong value
  is worse than an honest null.

Run:
    python evaluate.py        (after extract.py)
Writes:
    results/results.md
    results/results.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

from prompts import FIELDS

ROOT = Path(__file__).parent


def parse_response(raw: str):
    """Return the parsed JSON object, or None if the response is not JSON."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group(0))
                return obj if isinstance(obj, dict) else None
            except json.JSONDecodeError:
                return None
        return None


def normalize(field: str, value):
    if value is None:
        return None
    if field == "total_amount":
        try:
            return round(float(str(value).replace(",", "").replace("$", "").strip()), 2)
        except ValueError:
            return "__unparseable__"
    if field == "hs_chapter":
        try:
            return int(str(value).strip())
        except ValueError:
            return "__unparseable__"
    if field == "invoice_date":
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return text
    return str(value).strip().casefold()


def score_version(responses: dict, ground_truth: dict) -> dict:
    total_fields = 0
    correct_fields = 0
    valid_json = 0
    perfect_docs = 0
    hallucinations = 0
    for doc_id, truth in ground_truth.items():
        parsed = parse_response(responses[doc_id])
        if parsed is not None:
            valid_json += 1
        doc_correct = True
        for field in FIELDS:
            expected = normalize(field, truth[field])
            got = normalize(field, parsed.get(field)) if parsed else None
            total_fields += 1
            if expected is None and got is not None:
                hallucinations += 1
            if got == expected:
                correct_fields += 1
            else:
                doc_correct = False
        if doc_correct:
            perfect_docs += 1
    n_docs = len(ground_truth)
    return {
        "documents": n_docs,
        "json_valid_pct": round(100 * valid_json / n_docs, 1),
        "field_accuracy_pct": round(100 * correct_fields / total_fields, 1),
        "perfect_docs": perfect_docs,
        "hallucinated_fields": hallucinations,
    }


NOTES = {
    "v1": "Naive single instruction, no output contract. Prose answers, "
          "broken JSON, and invented values for fields the document "
          "never stated.",
    "v2": "Few-shot example + step-by-step reasoning. Accuracy jumps and "
          "JSON is consistent, but the model still guesses missing "
          "fields instead of admitting they are absent.",
    "v3": "Explicit output contract: schema, formatting rules, "
          "'null if not stated', and the document wrapped in delimiters. "
          "Hallucinated fields drop to zero.",
}


def main() -> None:
    ground_truth = json.loads(
        (ROOT / "data" / "ground_truth.json").read_text(encoding="utf-8")
    )
    raw_outputs = json.loads(
        (ROOT / "outputs" / "raw_outputs.json").read_text(encoding="utf-8")
    )

    results = {
        version: score_version(responses, ground_truth)
        for version, responses in raw_outputs.items()
    }

    lines = [
        "# Evaluation results",
        "",
        "20 synthetic trade documents x 8 fields = 160 field checks per version.",
        "",
        "| Prompt | JSON valid | Field accuracy | Perfect docs | Hallucinated fields |",
        "|--------|-----------:|---------------:|-------------:|--------------------:|",
    ]
    for version in ("v1", "v2", "v3"):
        r = results[version]
        lines.append(
            f"| {version} | {r['json_valid_pct']}% | {r['field_accuracy_pct']}% "
            f"| {r['perfect_docs']}/20 | {r['hallucinated_fields']} |"
        )
    lines.append("")
    for version in ("v1", "v2", "v3"):
        lines.append(f"**{version}** — {NOTES[version]}")
        lines.append("")

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "results.md").write_text("\n".join(lines), encoding="utf-8")
    (results_dir / "results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print("\n".join(lines))
    print("Wrote results/results.md and results/results.json")


if __name__ == "__main__":
    main()
