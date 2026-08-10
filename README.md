# verbatim-citation-gate

📖 **Docs: <https://palo-alto-ai-research-lab.github.io/verbatim-citation-gate/>** — the two stages, the API, the verdicts, and every known limit with its issue.

**Catch fabricated RAG citations before they reach the user.** A two-stage, framework-agnostic auditor for quote-style citations.
The deterministic half is `src/verbatim_citation_gate/gate.py`: zero dependencies, zero tokens.
The model half is `src/verbatim_citation_gate/judge.py`, and plugs into whatever LLM your pipeline already speaks.

RAG systems love to cite. The problem is *how they fail* — a quote that reads as authoritative and word-for-word can still be one of three things, each with its own case in `tests/test_gate.py`:

- **fabricated** — a plausible sentence that appears in no source (`test_fabrication_is_not_found`),
- a **frankenquote** — every word is real, but the sentence was stitched together and never actually written (`test_frankenquote_is_not_found`), or
- **misattributed** — a real quote lifted from a *different* document (`test_misattributed_real_quote_from_wrong_doc`).

A judge model, asked "does this quote support this claim?", waves all three through: they read as fluent and supportive.
The fix is to ask the cheaper, prior question first, deterministically — that is `src/verbatim_citation_gate/gate.py`.

## The two stages

```
                 ┌─────────────────────────┐
 claim + quote → │ 1. verbatim gate (free)  │ → not_found / misattributed   (rejected, 0 tokens)
   + doc id      └─────────────┬───────────┘
                               │ found
                               ▼
                 ┌─────────────────────────┐
                 │ 2. skeptical judge (LLM) │ → supports / partial / unrelated / contradicts
                 └─────────────────────────┘
```

**Stage 1 — the verbatim gate**, all of it in `src/verbatim_citation_gate/gate.py`.
Pure `re` + substring matching over a normalized form: case, smart quotes, dashes and whitespace folded, numbers and `%` preserved (`test_normalize_preserves_numbers_and_percent` in `tests/test_gate.py`).
It cannot be sweet-talked, and every fabrication it rejects costs zero model calls — proven by `test_audit_fabrication_never_calls_judge` in `tests/test_gate.py`.
Frankenquotes fail because the match is contiguous, not bag-of-words, and a real quote from the wrong document is surfaced as `misattributed` rather than collapsed into `not_found` — the two need different fixes upstream (`src/verbatim_citation_gate/gate.py`).

**Stage 2 — the skeptical judge**, all of it in `src/verbatim_citation_gate/judge.py`.
For quotes that *do* exist, a burden-of-proof prompt decides whether the passage actually establishes the claim. All three rules below live in that file's prompt:

1. **Default-refute** (`judge.py`) — the verdict starts at *unsupported*; the quote must
   earn `supports`, and ties break against the claim.
2. **Outside knowledge is inadmissible** (`judge.py`) — a claim can be true in the world
   and still unsupported by *this* source.
3. **Full-strength support** (`judge.py`) — same population, direction, magnitude and
   certainty, or the verdict caps at `partial`
   (subgroup→everyone, correlation→causation, "may"→"does").

If the judge's output does not parse it **fails closed** (`src/verbatim_citation_gate/judge.py`):
an unverifiable citation never counts as support.

## Install

Not on PyPI yet — install from the repository:

```bash
pip install "git+https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate"

# from a clone, with the test extra:
pip install -e ".[test]" && pytest -q
```

<!-- pypi-install-marker -->

Pure stdlib: the gate pulls in nothing, and the judge takes whatever `llm_call`
you already have.

## Use

```python
from verbatim_citation_gate import audit_citation

docs = {"veltranib-rct": "... Body weight was unchanged in both arms."}

# Stage 1 only — no model, no key, fully offline:
audit_citation("Body weight did not change.", "veltranib-rct",
               "Body weight was unchanged in both arms.", docs)   # -> "found"

# Both stages — supply any model as llm_call(system, user) -> str:
def llm_call(system, user):
    return client.messages.create(              # Anthropic shown; any vendor works
        model="claude-haiku-4-5", system=system, max_tokens=1024,
        messages=[{"role": "user", "content": user}],
    ).content[0].text

audit_citation("Body weight did not change.", "veltranib-rct",
               "Body weight was unchanged in both arms.", docs, llm_call=llm_call)
# -> "supports" | "partial" | "unrelated" | "contradicts" | "not_found" | "misattributed"
```

`llm_call` is deliberately the smallest possible contract — `(system, user) → text`
— so the judge wires to Claude, GPT, Gemini, Mistral, Cohere, or a local Qwen
without adapters. OpenAI, Cohere, and other one-liners are in
[`examples/quickstart.py`](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/blob/main/examples/quickstart.py).

## Why the gate goes first

The number you page on for a citation auditor is **recall of unfaithful
citations** — the fraction of bad citations you actually catch. The gate lifts
that recall for free on the three failure modes a judge is *worst* at
(fabricated, franken, misattributed), because those are exactly the ones that
look supportive. What reaches the model is only the genuinely ambiguous case:
a real quote whose *sufficiency* is a judgment call.

## Scope

The gate presumes **quote-style** citations. If your pipeline cites by document
id or character offsets, resolve the span to its source text first, then gate
that text. Contributions wiring this into specific frameworks (Haystack,
LlamaIndex, LangChain, Cohere, Qwen-Agent, …) are welcome.

## Roadmap

**Now — [v0.1.0](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/releases/tag/v0.1.0).**
The deterministic gate (`gate.py`) and the burden-of-proof judge (`judge.py`), 14 tests green,
install from git. Known limits are open issues, not footnotes — read them before you rely on it,
especially [#1](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues/1).

**Next**, in the order we would take them:

| What | Why it matters | Issue |
|---|---|---|
| Non-Latin normalization | today `normalize()` keeps only `[a-z0-9%.]`, so in Cyrillic/CJK the gate compares digits — a fabricated quote can pass as `found`. The tool's core promise is off in those scripts | [#1](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues/1) |
| Minimum-evidence rule | a one-word quote currently returns `found` | [#4](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues/4) |
| Normalize the corpus once | re-normalized per call: 2.4s per miss on 300 docs | [#2](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues/2) |
| `py.typed` marker | downstream type checkers see nothing today | [#3](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues/3) |
| Citations by doc id / offset | the gate presumes quote-style citations | [#9](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues/9) |
| PyPI package | so `pip install verbatim-citation-gate` is real | [#8](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues/8) |

Every noticeable change ships as a new release, so the
[release feed](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/releases)
is the honest record of how far along this is — not the commit graph.

## AI contributors

This project is built by a human + AI team, and the git log says so: Claude
writes most of the code, Codex and Grok review it, Gemini feeds the research.
Each is credited on a commit **only if its output changed that commit's
content** — no decorative credits. Lab-wide policy, one source for every repo:
[AI-CONTRIBUTORS.md](https://github.com/Palo-Alto-AI-Research-Lab/.github/blob/main/AI-CONTRIBUTORS.md).

## License

MIT © Palo Alto AI Research Lab

## Contact

Questions, war stories, or you want to run this on your own fleet:

- 💬 WhatsApp: **+1 341 222 9178**
- 🐦 X: [@Tony_Stef_](https://x.com/Tony_Stef_)
- 📣 Telegram: [@ClawRus](https://t.me/ClawRus) (RU) · [@ClawEng](https://t.me/ClawEng) (EN)
- 🌐 [palo-alto.ai](https://palo-alto.ai) · [Palo Alto AI Research Lab](https://github.com/Palo-Alto-AI-Research-Lab)

## Contributors welcome — and there is a queue

The queue is visible: **[verbatim-citation-gate — roadmap](https://github.com/users/Palo-Alto-AI-Research-Lab/projects/1)** — Now (an open PR exists), Next (scoped, free to take), Later (deferred, with the reason on the card), Shipped — and Shipped now starts with [v0.1.0](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/releases/tag/v0.1.0).

Issues labelled [`accepted`](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues?q=is%3Aissue+is%3Aopen+label%3Aaccepted)
are scoped, free to take, and nobody is on them. Comment **"claiming this"** — no permission needed —
and it is yours for 7 days. New here? Start with
[`good first issue`](https://github.com/Palo-Alto-AI-Research-Lab/verbatim-citation-gate/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

**You keep the copyright to your code.** No CLA, no assignment, ever — your contribution goes in
under this repo's existing license, the same terms as ours. We answer every issue and PR within
48 hours, including "no, and here is why"; our silence is our bug, so ping the thread.

Full deal: [CONTRIBUTING.md](https://github.com/Palo-Alto-AI-Research-Lab/.github/blob/main/CONTRIBUTING.md)

---

<!--ecosystem-map:start-->

## 🧩 One piece of a working system

This repository is one piece lifted out of a live operation: one non-technical founder, an AI
cofounder, and a fleet of machines that reach consensus with each other and wake the human only
for money or the irreversible. It was extracted after it survived production, not written as a
demo — and it runs on its own: nothing here phones home to the rest.

**See how the whole thing fits together → [SYSTEM.md](https://github.com/tonydzi/Palo-Alto-AI-Research-Lab/blob/main/SYSTEM.md)**

Its closest neighbours in the **gates** layer: [`verdict-contract`](https://github.com/tonydzi/verdict-contract) · [`claim-check`](https://github.com/tonydzi/claim-check) · [`verified-ops-starter`](https://github.com/tonydzi/verified-ops-starter)

<!--ecosystem-map:end-->
