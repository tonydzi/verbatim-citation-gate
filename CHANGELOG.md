# Changelog

What shipped, in plain words. This file did not exist until 2026-10-16: the entries for v0.1.0 and
v0.2.0 were written from the tags and release notes that already existed, so they are recorded
after the fact rather than backdated to look contemporaneous.

## Unreleased - 2026-11-06

**Four ways the gate said "found" (or crashed) on a citation that should fail, closed.** A breaker
panel run against the public demo found each one; each now has a test that fails on v0.3.1.

- A number inside a longer number no longer matches. `28` was "found" in `dose 28.5 mg`, `3` in
  `3.14`, `rate 28` in `rate 28%`: normalization keeps `.` and `%`, and the word-boundary check
  treated them as boundaries. A decimal point between digits and a `%` after a digit now count as
  part of the number. A sentence-final period still ends a word, so `fell by 28` matches
  `fell by 28.`.
- A quote with no letter or digit in it (`.`, `%`, `. .`) is `not_found`. It used to be "found" in
  almost any document, since a period survives normalization.
- Line-break hyphen repair only joins two letters. `range 25-\n30 mg` was normalized to
  `range 2530 mg`, so the invented quote `2530 mg` was "found". `Proc-\nedural` still rejoins.
- `resolve_span` returns `(None, "not_text")` when the document is not a string, instead of
  raising `TypeError`; `span_gate` returns `not_found`. `quote_gate` skips non-string documents and
  a non-string quote is `not_found`, so it keeps its "raises nothing" promise too.

A second breaker panel (six models) then attacked the fix itself and found more of the same class,
each confirmed by a reproduction and now covered by a test that fails without the change:

- `5` was "found" in `.5`, `000` and `of 1` in `1,000`, `rate 28` in `rate 28 %`. A leading-dot
  decimal, a comma between digits and a space before `%` are now part of the number.
- `risk < 5%` was "found" in `risk > 5%`, and `by 5%` in `by -5%`. Comparison operators (`< > ≤ ≥ = ±`)
  and a sign written right before a digit now survive normalization. A hyphen inside a word or a
  range (`COVID-19`, `25-30`) is still a separator.
- `quote_gate` no longer raises on an unhashable `cited_doc_id` or a `docs` that is not a dict;
  `resolve_span` reports a `None` document as `not_text`; `span_gate` rejects a span with no letter
  or digit in it.
- A zero-width character between a line-break hyphen and the break no longer stops the rejoin.

A third panel run on that fix (2026-11-13) found three smaller gaps, fixed with tests:

- An unhashable `cited_doc_id` now gives `misattributed` when the quote is real elsewhere, as the
  docstring always promised, instead of `not_found`.
- Line-break hyphen repair also sees Unicode line breaks (U+0085, U+2028, U+2029).
- A `str` subclass without a hash no longer crashes the gate through its normalization cache.

Known limits, by design: punctuation other than `.` `%` `,` and the operators is dropped, so
`Stop now` matches `Stop? Now.`; a hyphen with spaces on both sides is a dash, not a minus.

Benchmark unchanged: detection 1.0000 over 1 221 bad citations, false positive rate 0.1721 over
3 371 honest quotes, byte-identical output to v0.3.1.

## v0.3.1 - 2026-10-24

**Three gate fixes, each with a test that fails without it.** The quote match is now whole-word, so a
quote of "cat" no longer passes because the source says "category". The judge's verdict parser takes the
first balanced JSON object instead of the first closing brace, so a verdict containing nested braces
is no longer cut in half. `pytest` now finds `src` without an editable install.
Install: `pip install "git+https://github.com/tonydzi/verbatim-citation-gate@v0.3.1"`.

## v0.3.0 - 2026-10-16

**Citations by character offset now get the same fail-closed gate.** `span_gate(doc_id, start, end,
docs, quote=None, chunk=None)` resolves an offset span against the source text and rejects anything it
cannot resolve: unknown document, offsets outside the text, a span outside the retrieved chunk (it is
rejected, never silently clipped), a malformed interval, or an optional `quote` that does not appear
inside the span. Offsets are Python string indices over the half-open interval `[start, end)`.

This is a community contribution: written by [adity982](https://github.com/adity982) in
[#12](https://github.com/tonydzi/verbatim-citation-gate/pull/12), closing
[#9](https://github.com/tonydzi/verbatim-citation-gate/issues/9). It is the first outside change
merged here.

Two things fixed on our side while cutting the release:

- `__version__` in the package still said `0.1.0` while v0.2.0 was already tagged. It now says `0.3.0`.
- **Not on PyPI yet.** The v0.2.0 notes said it was; it was not, and the PyPI project does not exist.
  The publish job needs a Trusted Publisher registered on pypi.org by the owner. Until then the publish
  job is skipped (repo variable `PYPI_READY`), so a release no longer ends in a red build.
  Install with `pip install "git+https://github.com/tonydzi/verbatim-citation-gate"`.

## v0.2.0 - 2026-08-25

Recorded after the fact. Added CI, the Trusted Publishing workflow, and false-positive numbers for the
quote gate. The release notes claimed "on PyPI"; that was wrong (see v0.3.0).

## v0.1.0 - 2026-08-04

Recorded after the fact. First release: the deterministic quote gate and the model-judge stage.
