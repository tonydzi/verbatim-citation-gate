"""Offline tests. The gate is fully deterministic and needs no model or network.

The judge is exercised through a fake ``llm_call`` so the two-stage control
flow — and the fail-closed behavior — is covered without an API key.
"""

from verbatim_citation_gate import (
    Verdict,
    audit_citation,
    judge_support,
    normalize,
    quote_gate,
)

# Three tiny documents. The frankenquote trap stitches real fragments from
# RESTATIN across a sentence boundary that was never written.
DOCS = {
    "veltranib-rct": (
        "In the veltranib randomized controlled trial, fasting plasma glucose "
        "fell by 28 mg/dL in the veltranib arm. Body weight was unchanged in both arms."
    ),
    "restatin-meta": (
        "Restatin reduced the relative risk of non-fatal myocardial infarction by 25%. "
        "In the low-risk subgroup the reduction was not statistically significant."
    ),
    "coffee-cohort": (
        "Higher coffee consumption was associated with lower all-cause mortality "
        "in this observational cohort."
    ),
}


# --- Stage 1: the verbatim gate --------------------------------------------

def test_real_quote_is_found():
    assert quote_gate("Body weight was unchanged in both arms.", "veltranib-rct", DOCS) == "found"


def test_typography_and_case_insensitive():
    # smart quotes, em dash, odd casing, extra whitespace all normalize away
    assert quote_gate("  body   WEIGHT was unchanged in both arms.  ", "veltranib-rct", DOCS) == "found"


def test_frankenquote_is_not_found():
    # every word is real, but this sentence was never written in restatin-meta
    franken = "Restatin reduced the relative risk of non-fatal myocardial infarction by 25% in the low-risk subgroup."
    assert quote_gate(franken, "restatin-meta", DOCS) == "not_found"


def test_fabrication_is_not_found():
    assert quote_gate("Fasting plasma glucose fell by 28 mg/dL in the veltranib arm.", "restatin-meta", DOCS) == "misattributed"
    assert quote_gate("Veltranib cured the disease in every patient.", "veltranib-rct", DOCS) == "not_found"


def test_misattributed_real_quote_from_wrong_doc():
    q = "Body weight was unchanged in both arms."
    assert quote_gate(q, "restatin-meta", DOCS) == "misattributed"


def test_empty_quote_fails_closed():
    assert quote_gate("", "veltranib-rct", DOCS) == "not_found"
    assert quote_gate("   ", "veltranib-rct", DOCS) == "not_found"


def test_unknown_doc_id_fails_closed_not_raises():
    # a real quote attributed to a doc id we do not have -> misattributed, no KeyError
    assert quote_gate("Body weight was unchanged in both arms.", "does-not-exist", DOCS) == "misattributed"
    # a fabricated quote attributed to an unknown doc -> not_found, no KeyError
    assert quote_gate("nothing like this anywhere", "does-not-exist", DOCS) == "not_found"


def test_changed_document_text_does_not_reuse_stale_normalization():
    docs = {"changing": "The original quote."}

    assert quote_gate("The original quote.", "changing", docs) == "found"

    docs["changing"] = "The replacement quote."

    assert quote_gate("The replacement quote.", "changing", docs) == "found"
    assert quote_gate("The original quote.", "changing", docs) == "not_found"


def test_normalize_preserves_numbers_and_percent():
    assert "25%" in normalize("...by 25% in...")
    assert "28" in normalize("fell by 28 mg/dL")


def test_cyrillic_quotes_keep_words_when_matching():
    docs = {"report": "Отчёт показал: модель провалила 3 из 5 тестов безопасности."}

    assert quote_gate("модель провалила 3 из 5 тестов", "report", docs) == "found"
    assert quote_gate("модель успешно прошла 3 из 5 тестов", "report", docs) == "not_found"
    assert quote_gate("компания уволила 3 сотрудников за 5 минут", "report", docs) == "not_found"


def test_cjk_fabrication_with_shared_digits_is_not_found():
    docs = {"report": "模型在 3 个测试中失败了"}

    assert quote_gate("模型在 3 个测试中失败了", "report", docs) == "found"
    assert quote_gate("模型通过了所有 3 个测试", "report", docs) == "not_found"


def test_accented_latin_and_combining_marks_normalize_consistently():
    docs = {"letter": "Grüße aus München"}

    assert normalize("Straße") == "strasse"
    assert quote_gate("GRÜSSE aus Mu\u0308nchen", "letter", docs) == "found"


# --- Stage 2 + the two-stage audit -----------------------------------------

def _fake_supports(system, user):
    return '{"reasoning": "matches", "verdict": "supports", "confidence": 0.9}'


def _fake_garbage(system, user):
    return "the model rambled and returned no json at all"


def _fake_raises(system, user):
    raise RuntimeError("model exploded")


def test_audit_fabrication_never_calls_judge():
    calls = []

    def spy(system, user):
        calls.append(1)
        return _fake_supports(system, user)

    # a fabricated quote should be rejected by the gate for zero model calls
    result = audit_citation("some claim", "restatin-meta", "totally made up quote", DOCS, llm_call=spy)
    assert result == "not_found"
    assert calls == []  # judge was never reached


def test_audit_found_quote_reaches_judge():
    result = audit_citation(
        "Body weight did not change.", "veltranib-rct",
        "Body weight was unchanged in both arms.", DOCS, llm_call=_fake_supports,
    )
    assert result == "supports"


def test_audit_without_llm_returns_found():
    result = audit_citation(
        "Body weight did not change.", "veltranib-rct",
        "Body weight was unchanged in both arms.", DOCS, llm_call=None,
    )
    assert result == "found"


def test_judge_fails_closed_on_garbage():
    v = judge_support("c", "q", "s", _fake_garbage)
    assert isinstance(v, Verdict)
    assert v.verdict == "unrelated"
    assert v.confidence == 0.0


def test_judge_fails_closed_when_call_raises():
    v = judge_support("c", "q", "s", _fake_raises)
    assert v.verdict == "unrelated"
    assert v.confidence == 0.0


def test_judge_rejects_out_of_vocabulary_verdict():
    def sneaky(system, user):
        return '{"reasoning": "x", "verdict": "definitely_supports", "confidence": 1.0}'

    v = judge_support("c", "q", "s", sneaky)
    assert v.verdict == "unrelated"  # unknown label -> fail closed


# --- transit damage: honest quotes that arrive mangled -----------------------
#
# Measured on 295 arXiv abstracts (bench/): before these three were handled the
# gate rejected 42.5% of honest quotes; after, 17.2%. Each test below is a
# regression guard for one of the three classes that closed that 25-point gap.


def test_soft_hyphen_inside_word_still_matches():
    """PDF hyphenation leaves U+00AD inside words; it is invisible to a reader."""
    assert quote_gate("fasting pla\u00adsma glu\u00adcose", "veltranib-rct", DOCS) == "found"


def test_line_break_hyphen_is_rejoined():
    """`pla-\nsma` is one word broken by a typesetter, not two words."""
    assert quote_gate("fasting pla-\nsma glucose", "veltranib-rct", DOCS) == "found"


def test_real_hyphenated_word_keeps_its_boundary():
    """Only hyphens AT a line break are removed — `mg/dL`-style compounds stay intact."""
    # A hyphen with no line break after it must not glue the two halves together,
    # otherwise `re-cover` would start matching `recover`.
    assert normalize("re-cover") != normalize("recover")


def test_cyrillic_homoglyphs_still_match():
    """Text round-tripped through a glyph-swapping tool: identical to the eye."""
    assert quote_gate("f\u0430sting plasma gluc\u043ese", "veltranib-rct", DOCS) == "found"


def test_homoglyph_folding_does_not_invent_matches():
    """Folding look-alikes must not make genuinely different letters equal."""
    # Cyrillic "в" is NOT folded to "b": they are different letters, and
    # collapsing them would manufacture matches that do not exist.
    assert normalize("\u0432") != normalize("b")


def test_transit_damage_does_not_rescue_a_fabrication():
    """The repairs must not turn a fabrication into a match.

    This is the load-bearing test: every normalization that makes matching more
    forgiving risks waving through the thing the gate exists to catch.
    """
    fabricated = "fasting pla\u00adsma glucose r\u043ese by 28 mg/dL"
    assert quote_gate(fabricated, "veltranib-rct", DOCS) == "not_found"
