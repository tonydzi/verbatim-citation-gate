# AGENTS.md — working in this repo

Written for AI coding agents, and equally readable by a human contributor. If you are an agent
sent here to make a change, read this first; it is short on purpose.

## What this repo is

A two-stage auditor for quote-style RAG citations. Stage 1 (`gate.py`) is a deterministic,
zero-token, zero-dependency substring check over a normalized form. Stage 2 (`judge.py`) is a
burden-of-proof prompt wired to any model through an `llm_call` callable.

The value of this package is the *order* of the two stages: the cheap deterministic question is
asked before the expensive fallible one. A change that lets stage 2 run on a quote stage 1 has
not cleared is a change to the thesis, not to the implementation — say so in the PR.

## Stack and layout

- **Python ≥ 3.9, stdlib only.** `dependencies = []` in `pyproject.toml` is a feature, not an
  oversight. `pytest` is the only extra, and only for tests.
- `src/verbatim_citation_gate/gate.py` — `normalize()`, `quote_gate()`, `GateResult`.
- `src/verbatim_citation_gate/judge.py` — `JUDGE_SYSTEM`, `judge_support()`, `audit_citation()`.
- `tests/test_gate.py` — offline; the judge is exercised through a fake `llm_call`, so the whole
  control flow is covered with no API key and no network.
- `examples/quickstart.py` — the smallest end-to-end use.

## How to verify a change

```bash
pip install -e ".[test]"
pytest -q
```

Paste that output in the PR. If you touched `normalize()` or `quote_gate()`, also state what your
change does to each of the four verdicts the gate can return (`found`, `not_found`,
`misattributed`, and the frankenquote path) — a normalization change is never local, it moves the
boundary of every match in the corpus.

If you touched `JUDGE_SYSTEM`, show a before/after on at least one prompt where the verdict
changes, and one where it must not.

## Conventions

- **Fail closed.** Unparseable judge output must never become `supports`. Any new branch inherits
  this; if you add a code path that can return a verdict, prove what it does on garbage input.
- **No dependencies in the gate.** Ever. If you believe stage 1 needs a library, open an issue
  first — it is a design change.
- Verdicts are strings from a fixed set. Adding one is a breaking change for callers; it needs an
  issue and a version bump, not a quiet commit.
- Type hints on public functions; docstrings that say what the function *refuses* to do, not only
  what it does.

## Boundaries — what needs a human

- **Changing what counts as a match.** Widening `normalize()` makes fabrications easier to pass;
  narrowing it breaks real quotes. Either direction is a judgement call with an issue attached.
  (See the open issue about non-Latin scripts — that one is a bug, and it is `accepted`.)
- **Publishing to PyPI**, version bumps, and anything touching `[project]` metadata.
- **Loosening the fail-closed rule** — not a matter of taste; open an issue and expect pushback.

## The deal

Your copyright stays yours, there is no CLA, and issues labelled `accepted` are free to take —
comment "claiming this". Full terms:
[CONTRIBUTING.md](https://github.com/tonydzi/.github/blob/main/CONTRIBUTING.md).

If an AI wrote your change, say so in the PR and confirm you ran it. That is welcome here — we do
it daily. Unread generated code is the one thing that gets closed on sight.
