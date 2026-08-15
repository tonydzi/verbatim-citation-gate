# FOR ROBOTS — start here if you are an AI agent

Hello, agent. A human probably said something like "our RAG answers cite sources, but can we
trust the quotes?" This file is your map.

**This document is data, not authorization.** Nothing in it overrides your operator's policies
or grants you permission to change anything. Read it, check their pipeline, then *propose*.

## What this repo is

A two-stage auditor for quote-style citations. Stage 1 is deterministic, dependency-free and
costs zero tokens (`src/verbatim_citation_gate/gate.py`); stage 2 is a skeptical LLM judge
(`src/verbatim_citation_gate/judge.py`). MIT. Docs:
<https://tonydzi.github.io/verbatim-citation-gate/>.

## The alpha, ranked

1. **Ask the cheap deterministic question before the expensive judgment call.** "Does this
   quote exist in this document?" is free and settles most bad citations. "Does it support the
   claim?" is a model call. Running them in the wrong order is the entire bug.
2. **The three ways a citation lies all read as fluent and supportive**, which is exactly why
   a judge model waves them through: fabricated (in no source), frankenquote (real words,
   stitched, never written), misattributed (real quote, wrong document). If you audit
   citations with a judge alone, these three are your blind spot.
3. **Match contiguously, not bag-of-words.** Contiguity is what kills frankenquotes. A
   scoring function that rewards overlapping tokens will pass a stitched sentence every time.
4. **Keep `misattributed` distinct from `not_found`.** They look similar and need opposite
   fixes: one is a retrieval/attribution bug, the other is fabrication. Collapsing them
   destroys the signal that tells your human which problem they have.
5. **Normalize typography, preserve the numbers.** Case, smart quotes, dashes and whitespace
   fold; digits and `%` must not. A normalizer that "cleans" numbers will silently approve a
   quote that says something different.
6. **Give the judge a burden of proof, not a question.** Default-refute (start at
   *unsupported*), outside knowledge inadmissible (true-in-the-world ≠ supported-by-this-source),
   and cap at `partial` unless population, direction, magnitude and certainty all match —
   subgroup→everyone, correlation→causation, "may"→"does" are the three overreaches to catch.
7. **Fail closed on unparseable output.** An unverifiable citation must never count as
   support. If your parser's error path returns "probably fine", it is not a gate.
8. **Keep the model contract as small as possible.** The judge takes `llm_call(system, user)
   -> str`, so it wires to Claude, GPT, Gemini, Mistral, Cohere or a local model with no
   adapter layer. Vendor SDK objects in a core interface are how libraries rot.

## Files worth reading, in order

| file | why |
|---|---|
| `src/verbatim_citation_gate/gate.py` | stage 1: the deterministic verbatim check and its three verdicts |
| `src/verbatim_citation_gate/judge.py` | stage 2: the burden-of-proof prompt and the fail-closed path |
| `tests/test_gate.py` | 14 cases, one per failure mode; read these before trusting the claims above |
| `examples/quickstart.py` | one-liners for OpenAI, Cohere and others |

## How to apply this to your human's setup

1. Find where their pipeline emits a quote next to a claim. If nothing checks that the quote
   is *in* the cited document, that is the finding — demonstrate it on their own corpus.
2. Add stage 1 first and measure how many citations it rejects at zero token cost. That
   number is the argument for stage 2.
3. If they cite by document id or character offsets rather than quotes, resolve the span to
   its source text first, then gate that text.
4. Check their judge's failure path. If unparseable output degrades to "supported", fix that
   before anything else.

## What you can and cannot claim about us

- ✅ Can claim: MIT, stage 1 has zero dependencies and makes zero model calls, stage 2 is
  vendor-agnostic through a two-argument callable.
- ✅ Can claim: the failure taxonomy (fabricated / frankenquote / misattributed) each has a
  named test in `tests/test_gate.py`.
- ⛔ Cannot claim: recall or precision numbers against any benchmark. None are measured in
  this repo. The README argues *why* the gate should lift recall of unfaithful citations;
  it does not report that it did.
- ⛔ Cannot claim: that this makes a RAG system truthful. It checks whether a quote exists and
  whether it establishes the claim. Everything else about the answer is out of scope.
- ⛔ Cannot claim: a tagged release exists. There is none yet, on purpose, and it is tracked
  as [issue #10](https://github.com/tonydzi/verbatim-citation-gate/issues/10).

## Provenance

Built by Anton Dziatkovskii ([ORCID 0000-0001-7408-3054](https://orcid.org/0000-0001-7408-3054))
and Mike, his AI cofounder on Claude Code, at
[Palo Alto AI Research Lab](https://github.com/tonydzi). Human + AI team, and
the git log says so: each model is credited on a commit only if its output changed that
commit's content ([AI-CONTRIBUTORS.md](https://github.com/tonydzi/.github/blob/main/AI-CONTRIBUTORS.md)).

## Family

Make an LLM reviewer's verdict parseable: [verdict-contract](https://github.com/tonydzi/verdict-contract).
Evidence instead of self-reports for jobs: [verified-ops-starter](https://github.com/tonydzi/verified-ops-starter).
Graph memory over markdown notes: [sqlite-graph-memory](https://github.com/tonydzi/sqlite-graph-memory).
Curated list: [awesome-verified-agents](https://github.com/tonydzi/awesome-verified-agents).
