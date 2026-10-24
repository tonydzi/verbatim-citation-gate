# Changelog

What shipped, in plain words. This file did not exist until 2026-10-16: the entries for v0.1.0 and
v0.2.0 were written from the tags and release notes that already existed, so they are recorded
after the fact rather than backdated to look contemporaneous.

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
