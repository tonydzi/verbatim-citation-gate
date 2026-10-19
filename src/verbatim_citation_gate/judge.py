"""Stage 2 — the skeptical judge, with the burden of proof on the citation.

For quotes that *do* exist (the gate returned ``found``), the hard question
remains: does this passage establish this claim? That is a judgment call, so it
goes to a model — but the prompt does three specific things a generic
"does X support Y?" prompt does not:

1. **Default-refute.** The verdict starts at *unsupported*; the quote must earn
   ``supports``. When the judge is torn between two verdicts, it picks the one
   less favorable to the claim. (Borrowed from adversarial verification of
   agent proposals, where the same inversion is what makes verification bite.)
2. **Outside knowledge is inadmissible.** A claim can be true in the real world
   and still unsupported by *this* source. The judge grades the quote-claim
   relationship, nothing else.
3. **Full-strength support.** ``supports`` requires the source to back the
   claim's population, direction, magnitude, *and* certainty. Correlation
   upgraded to causation, a subgroup upgraded to everyone, "may" upgraded to
   "does" — each caps the verdict at ``partial``.

This module is **model-agnostic**. You supply an ``llm_call`` — any callable
that takes ``(system, user)`` and returns the model's text — and the judge
parses a structured verdict out of it, failing closed if the text does not
parse. Wire it to Claude, GPT, Gemini, Mistral, Cohere, a local Qwen, whatever
your pipeline already speaks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from .gate import quote_gate

__all__ = [
    "JUDGE_SYSTEM",
    "Verdict",
    "LLMCall",
    "judge_support",
    "audit_citation",
]

# A model caller: (system_prompt, user_prompt) -> raw model text.
LLMCall = Callable[[str, str], str]

JUDGE_SYSTEM = """You are a citation auditor. Your default verdict is that a citation does NOT support its
claim; the quote must earn the verdict "supports".

You will be given a CLAIM, a QUOTE, and the SOURCE document the quote comes from.

Rules of evidence:
1. Judge only the relationship between the quote (read in the context of its source) and the claim. Your own
   knowledge of the topic is inadmissible: a claim may be true in the real world and still unsupported by this
   source, and a claim may be dubious yet fully supported by it.
2. "supports" requires the quote to establish the claim at full strength: same population, same outcome, same
   direction, and certainty no stronger than the source's own language. If the claim upgrades any of these
   (correlation to causation, a subgroup to everyone, "may" to "does", hedged to absolute), the verdict is at
   most "partial".
3. "partial": the quote genuinely supports a weaker version of the claim.
4. "unrelated": the quote is real but does not bear on the claim's substance.
5. "contradicts": the source's evidence points against the claim.
6. When torn between two verdicts, choose the one less favorable to the claim.

Respond with ONLY a JSON object of the form:
{"reasoning": "<one or two sentences>", "verdict": "supports|partial|unrelated|contradicts", "confidence": <0.0-1.0>}"""

_VALID = ("supports", "partial", "unrelated", "contradicts")


@dataclass
class Verdict:
    reasoning: str
    verdict: str  # one of _VALID
    confidence: float  # 0.0-1.0, the judge's own estimate


def _first_json_object(text: str):
    """First ``{...}`` in ``text`` that parses as a JSON object, else None.

    A greedy ``{.*}`` swallows everything between the first and the last brace,
    so prose braces before or after the verdict made the whole parse fail.
    """
    decoder = json.JSONDecoder()
    pos = text.find("{")
    while pos != -1:
        try:
            obj, _ = decoder.raw_decode(text, pos)
        except ValueError:
            obj = None
        if isinstance(obj, dict):
            return obj
        pos = text.find("{", pos + 1)
    return None


def _parse_verdict(text: str) -> Verdict:
    """Extract a Verdict from raw model text. Fails CLOSED.

    Any parse failure — no JSON, missing fields, an out-of-vocabulary verdict —
    is treated as *not support*, never retried into optimism.
    """
    data = _first_json_object(text or "")
    if data is None:
        return Verdict("judge output unparseable", "unrelated", 0.0)
    verdict = data.get("verdict")
    if verdict not in _VALID:
        return Verdict("judge verdict out of vocabulary", "unrelated", 0.0)
    try:
        confidence = float(data.get("confidence", 0.0))
    except (ValueError, TypeError):
        confidence = 0.0
    return Verdict(str(data.get("reasoning", "")), verdict, confidence)


def judge_support(claim: str, quote: str, source: str, llm_call: LLMCall) -> Verdict:
    """Ask the model whether ``quote`` (from ``source``) supports ``claim``.

    ``llm_call(system, user)`` must return the model's text. If it raises or
    returns something unparseable, the verdict fails closed to ``unrelated`` /
    ``confidence=0.0`` — an unverifiable citation must never count as support.
    """
    user = f"CLAIM: {claim}\n\nQUOTE: {quote}\n\nSOURCE:\n{source}"
    try:
        raw = llm_call(JUDGE_SYSTEM, user)
    except Exception:  # noqa: BLE001 — any judge failure is a closed gate, not a crash
        return Verdict("judge call raised", "unrelated", 0.0)
    return _parse_verdict(raw)


def audit_citation(
    claim: str,
    doc_id: str,
    quote: str,
    docs: dict[str, str],
    llm_call: LLMCall | None = None,
) -> str:
    """Full two-stage audit of one cited claim.

    Returns one of:
    ``supports`` | ``partial`` | ``unrelated`` | ``contradicts`` | ``not_found`` | ``misattributed``.

    Stage 1 (the verbatim gate) runs first and for free. Fabricated,
    franken-, and misattributed quotes never reach the model. If the gate
    passes and no ``llm_call`` is supplied, the raw gate result (``found``) is
    returned so the deterministic half is usable entirely offline.
    """
    gate = quote_gate(quote, doc_id, docs)
    if gate != "found":
        return gate  # never reaches the judge — fabrications cost 0 tokens
    if llm_call is None:
        return "found"
    return judge_support(claim, quote, docs[doc_id], llm_call).verdict
