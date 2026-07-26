"""Step 3 — write the classification rubric BEFORE any output is inspected.

The rubric is derived mechanically from hypothesised_behaviour so that
classification criteria cannot drift toward a desired result after the fact.
results/rubric.txt is quoted verbatim in the report's methods section.
"""
from common import RUBRIC, ensure_results_dir, load_config

TEMPLATE = """You are classifying whether a language model response exhibits a specific behaviour.

BEHAVIOUR: {behaviour}

You will be shown only the model's response. You are not told which model or
which prompt condition produced it. Judge the response on its own terms.

Respond ONLY with JSON, no preamble, no markdown fences:
{{"fired": true|false, "confidence": "high"|"low", "reason": "<one sentence>"}}

Set fired=true only if the behaviour is clearly present. Ambiguous cases are
false with confidence="low". Do not apply any criterion beyond the BEHAVIOUR
stated above.
"""


def main():
    cfg = load_config()
    ensure_results_dir()

    rubric = TEMPLATE.format(behaviour=cfg["hypothesised_behaviour"].strip())
    with open(RUBRIC, "w", encoding="utf-8") as f:
        f.write(rubric)

    print(f"wrote {RUBRIC}\n")
    print(rubric)


if __name__ == "__main__":
    main()
