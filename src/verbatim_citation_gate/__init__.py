"""verbatim-citation-gate — catch fabricated RAG citations before they reach the user.

A two-stage, framework-agnostic auditor for quote-style citations:

* **Stage 1 — the verbatim gate** (:func:`quote_gate`): pure-stdlib, zero-token
  substring check that rejects fabrications, frankenquotes, and misattributed
  quotes for free.
* **Stage 2 — the skeptical judge** (:func:`judge_support`): a burden-of-proof
  prompt, wired to *any* model via an ``llm_call`` callable, that only lets a
  real quote count as ``supports`` when it establishes the claim at full
  strength.

Typical use::

    from verbatim_citation_gate import audit_citation

    verdict = audit_citation(claim, doc_id, quote, docs, llm_call=my_model)
    # -> "supports" | "partial" | "unrelated" | "contradicts"
    #    | "not_found" | "misattributed"
"""

from .gate import GateResult, normalize, quote_gate, resolve_span, span_gate
from .judge import JUDGE_SYSTEM, LLMCall, Verdict, audit_citation, judge_support

__version__ = "0.3.1"

__all__ = [
    "normalize",
    "quote_gate",
    "resolve_span",
    "span_gate",
    "GateResult",
    "JUDGE_SYSTEM",
    "Verdict",
    "LLMCall",
    "judge_support",
    "audit_citation",
    "__version__",
]
