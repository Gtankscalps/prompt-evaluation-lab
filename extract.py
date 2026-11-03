"""Run every prompt version against every document.

Live mode (OPENAI_API_KEY set): each prompt is sent to the model and the
raw responses are saved.

Offline demo mode (no key): the recorded sample responses in
sample_outputs.json are used instead, so the pipeline still runs
end-to-end and the scoring in evaluate.py is real scoring of real
response text.

Run:
    python extract.py
Writes:
    outputs/raw_outputs.json   {version: {doc_id: raw_response_text}}
"""

import json
from pathlib import Path

from llm_client import complete, llm_available
from prompts import PROMPT_VERSIONS

ROOT = Path(__file__).parent


def load_sample_outputs() -> dict:
    return json.loads((ROOT / "sample_outputs.json").read_text(encoding="utf-8"))


def main() -> None:
    documents = json.loads((ROOT / "data" / "documents.json").read_text(encoding="utf-8"))
    live = llm_available()
    samples = {} if live else load_sample_outputs()
    print("Mode:", "LIVE (API)" if live else "OFFLINE DEMO (recorded sample outputs)")

    raw_outputs: dict = {}
    for version, build_prompt in PROMPT_VERSIONS.items():
        raw_outputs[version] = {}
        for doc in documents:
            doc_id = doc["doc_id"]
            if live:
                raw = complete(build_prompt(doc["text"]))
            else:
                raw = samples[version][doc_id]
            raw_outputs[version][doc_id] = raw
        print(f"{version}: collected {len(raw_outputs[version])} responses")

    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "raw_outputs.json").write_text(
        json.dumps(raw_outputs, indent=2), encoding="utf-8"
    )
    print("Wrote outputs/raw_outputs.json — now run: python evaluate.py")


if __name__ == "__main__":
    main()
