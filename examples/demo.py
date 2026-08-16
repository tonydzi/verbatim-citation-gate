"""The 20-second demo: three bad citations, two rejected before the model wakes up.

Runs offline. The ``llm_call`` here counts its own invocations, so the
"model calls" line at the end is a measured number, not a claim.

    python examples/demo.py
"""

from verbatim_citation_gate import audit_citation

DOCS = {
    "veltranib-rct": (
        "In the veltranib randomized controlled trial, fasting plasma glucose "
        "fell by 28 mg/dL in the veltranib arm. Body weight was unchanged in both arms."
    ),
    "restatin-meta": (
        "Restatin reduced the relative risk of non-fatal myocardial infarction by 25%. "
        "In the low-risk subgroup the reduction was not statistically significant."
    ),
}

CALLS = 0


def llm_call(system: str, user: str) -> str:
    """Stand-in for your model. Counts calls so the demo cannot overstate itself."""
    global CALLS
    CALLS += 1
    return '{"reasoning": "the quote states it directly", "verdict": "supports", "confidence": 0.9}'


CITATIONS = [
    ("Veltranib caused rapid weight loss.", "veltranib-rct",
     "Veltranib produced dramatic weight loss.",
     "fabricated - no such sentence exists"),
    ("Restatin cut heart attacks even in low-risk patients.", "restatin-meta",
     "Restatin reduced the relative risk of non-fatal myocardial infarction by 25% "
     "in the low-risk subgroup.",
     "frankenquote - every word real, sentence never written"),
    ("Veltranib prevents heart attacks.", "veltranib-rct",
     "Restatin reduced the relative risk of non-fatal myocardial infarction by 25%.",
     "real quote, wrong paper"),
    ("Body weight did not change on veltranib.", "veltranib-rct",
     "Body weight was unchanged in both arms.",
     "real quote, real document"),
]

if __name__ == "__main__":
    for claim, doc_id, quote, note in CITATIONS:
        before = CALLS
        verdict = audit_citation(claim, doc_id, quote, DOCS, llm_call=llm_call)
        cost = "1 model call" if CALLS > before else "0 tokens"
        print(f'  claim: "{claim}"')
        print(f'  quote: "{quote[:58]}{"..." if len(quote) > 58 else ""}"')
        print(f"  -> {verdict:<14} {note}  ({cost})")
        print()

    print(f"  {len(CITATIONS)} citations audited - "
          f"{len(CITATIONS) - CALLS} rejected for free, {CALLS} reached the model")
