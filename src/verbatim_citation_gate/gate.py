"""Stage 1 — the deterministic verbatim gate.

Zero dependencies, zero tokens. Before any model is asked whether a quote
*supports* a claim, this stage asks the cheaper, prior question: **does the
quote exist, verbatim, in the document it is attributed to?**

A bag-of-words comparison would pass frankenquotes — stitched "quotes" whose
every word appears in the source but whose sentence was never written. So the
gate matches the normalized quote as a contiguous substring. A real quote that
lives in a *different* document is flagged ``misattributed`` rather than
silently failing, which keeps that failure mode visible instead of collapsing
it into ``not_found``.

Because it is pure string work, the gate cannot be sweet-talked by a persuasive
citation, and every fabrication it rejects costs zero model calls.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

__all__ = ["normalize", "quote_gate", "GateResult"]

# The three outcomes the gate can return.
GateResult = str  # Literal["found", "misattributed", "not_found"]

# A word broken across a line by a typesetter, as it survives copy-paste out of
# a PDF: a hyphen (or its Unicode variants) immediately before the break. The
# hyphen is an artifact of the layout, not of the word, so it is removed along
# with the break — otherwise ``Proc-\nedural`` and ``Procedural`` never match.
# A hyphen NOT followed by a line break is left alone and later becomes a space,
# so ``state-of-the-art`` keeps its internal boundaries.
_LINEBREAK_HYPHEN = re.compile(r"[-‐‑‒–]\s*[\r\n]\s*")

# Characters that are visually identical to ASCII letters but encode as
# different codepoints. They arrive when text round-trips through a tool that
# swaps glyphs, or when a document mixes scripts. Only pairs that are
# indistinguishable when rendered are listed: a reader cannot tell them apart,
# so the matcher should not either. Deliberately conservative — near-lookalikes
# (Greek epsilon vs "e", Cyrillic "в" vs "b") are NOT folded, because collapsing
# genuinely different letters would invent matches that do not exist.
_HOMOGLYPHS = str.maketrans(
    {
        # Cyrillic → Latin
        "а": "a", "с": "c", "е": "e", "о": "o", "р": "p",
        "х": "x", "у": "y", "і": "i", "ј": "j", "ѕ": "s",
        # Greek → Latin
        "ο": "o", "α": "a", "ρ": "p", "ι": "i", "κ": "k",
        "ν": "v", "χ": "x",
    }
)


def normalize(text: str) -> str:
    """Case/typography/whitespace-insensitive form for verbatim matching.

    Applies Unicode compatibility normalization and case folding, folds
    visually identical glyphs onto ASCII, repairs line-break hyphenation, drops
    punctuation that does not carry meaning, and collapses runs of whitespace.
    Percent signs and decimal points survive because ``25%`` and ``0.5`` are
    load-bearing in the kind of quantitative claims citations usually support.

    The ordering matters. Hyphenation is repaired while the line breaks are
    still present; zero-width and soft-hyphen formatting characters are
    *deleted* rather than turned into spaces, since a soft hyphen sits inside a
    word and a space there would split it; and glyph folding runs after case
    folding so only lowercase mappings are needed.
    """
    text = unicodedata.normalize("NFKC", text)
    text = _LINEBREAK_HYPHEN.sub("", text)
    # Format characters (soft hyphen, zero-width space/joiners, bidi marks) are
    # invisible *inside* words. Dropping them keeps the word whole; replacing
    # them with a space would break it in two.
    text = "".join(char for char in text if unicodedata.category(char) != "Cf")
    text = text.casefold()
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_HOMOGLYPHS)
    text = "".join(
        char if char in "%." or unicodedata.category(char)[0] in "LNM" else " "
        for char in text
    )
    return " ".join(text.split())


@lru_cache(maxsize=4096)
def _normalized(text: str) -> str:
    """Normalize repeated text once, retaining up to 4,096 raw inputs."""
    return normalize(text)


def quote_gate(quote: str, cited_doc_id: str, docs: dict[str, str]) -> GateResult:
    """Check a quote against the document it is attributed to.

    Returns one of:

    * ``"found"``        — the quote appears verbatim in ``docs[cited_doc_id]``.
    * ``"misattributed"``— the quote appears verbatim in some *other* document.
    * ``"not_found"``    — the quote appears in no document (fabricated /
      frankenquote), or the quote / citation is empty.

    Fails closed: an empty quote, or a ``cited_doc_id`` that is not in ``docs``,
    can never come back ``"found"``. It raises nothing — an empty quote is
    ``"not_found"``, and an unknown doc id is judged on the quote alone, so a
    real quote with a bad citation is reported as ``"misattributed"`` (which is
    what it is) rather than being collapsed into ``"not_found"``.
    """
    q = _normalized(quote)
    if not q:
        return "not_found"
    cited = docs.get(cited_doc_id)
    if cited is not None and q in _normalized(cited):
        return "found"
    if any(
        q in _normalized(text)
        for doc_id, text in docs.items()
        if doc_id != cited_doc_id
    ):
        return "misattributed"
    return "not_found"
