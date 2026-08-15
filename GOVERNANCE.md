# Governance

Small project, honest rules. Written down so that a future sponsor, employer, or foundation
can read in two minutes exactly what they'd be dealing with — no verbal lore.

## Roles

- **Maintainer:** Anton Dziatkovskii ([@tonydzi](https://github.com/tonydzi)), Palo Alto AI Research Lab.
  Final say on merges, releases, and the fail-closed invariant.
- **AI agents** (Claude and others) do a large share of the implementation work under the maintainer's
  review. Every such commit is labelled; the policy and the ledger live in
  [AI-CONTRIBUTORS.md](https://github.com/tonydzi/.github/blob/main/AI-CONTRIBUTORS.md).
  The maintainer — a named human — carries responsibility for everything merged.
- **Contributors:** anyone via issues/PRs. Path to trust is boring on purpose: repeated good PRs →
  triage rights → review rights. No inner circle, the label workflow in
  [CONTRIBUTING](https://github.com/tonydzi/.github/blob/main/CONTRIBUTING.md) is the whole process.

## Licensing of contributions

- License: **MIT** ([LICENSE](LICENSE)). Inbound = outbound: by submitting a PR you license your
  contribution under the same MIT terms. **No CLA, no DCO sign-off, no copyright assignment** —
  the org-wide policy is explicit about this and it is part of the deal we offer contributors.
- Third-party code may enter only under MIT-compatible terms, stated in the PR.

## Releases

- Releases are tagged by the maintainer; notes are auto-generated per [release.yml](.github/release.yml) —
  nothing merged falls out of the notes silently.
- Roadmap is public: [project board](https://github.com/users/tonydzi/projects/1) (Now / Next / Later /
  Shipped, with reasons on deferred cards).

## If the project outgrows one maintainer

Stated in advance, because unclear succession is how single-maintainer projects die:

- **Name and namespace.** "verbatim-citation-gate" is a descriptive name; no trademark is claimed.
  If the project moves to a foundation or a new steward, the repository transfers with its full
  history and the PyPI name (once registered) transfers with it. The maintainer commits to not
  holding the namespace hostage.
- **Steward deal-breakers.** Any transfer or sponsorship must preserve: (1) the license stays MIT,
  (2) the fail-closed invariant stays non-negotiable, (3) the AI-contribution ledger keeps being
  honest. A steward who needs any of these relaxed is the wrong steward.
- **Bus factor.** If the maintainer is unreachable for 90 days, the most active trusted contributor
  may fork under the same name-with-suffix and this file counts as the maintainer's public blessing.
