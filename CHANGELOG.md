# Changelog

All notable changes to DorkCraft are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project intends to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) from its first tagged
release onwards.

> **There are no releases yet.** The repository carries no git tags, so everything below
> is reconstructed from the commit history and grouped by the date the work landed on
> `main`. The `version="1.0.0"` string in `backend/main.py` is the FastAPI app title
> metadata that appears in `/docs` — it is not a release, and `frontend/package.json`
> still says `0.0.1`. Reconciling the two is part of cutting `0.1.0`.

## [Unreleased]

### Known issues

- **The published site cannot generate a dork.** Three faults compound on
  <https://juandresrodca.github.io/DorkCraft/>: `PUBLIC_API_URL` is empty in the deployed
  build, the API's `ALLOWED_ORIGINS` is an exact-match list that does not include the
  Pages origin, and the frontend reports the resulting failure as a query problem rather
  than a connectivity one. Tracked in
  [#1](https://github.com/juandresrodca/DorkCraft/issues/1). Running both halves locally,
  or self-hosting them behind one origin as
  [`docs/self-hosting.md`](docs/self-hosting.md) describes, is unaffected.

### Planned before `0.1.0`

- A single declared version, shared by the API metadata and `package.json`.
- A test suite. There is none today, which is why
  [`CONTRIBUTING.md`](CONTRIBUTING.md) asks a pull request to show the before-and-after
  output of the queries it changes.
- Rate limiting on the API. The backend ships without it; the nginx configuration in
  [`docs/self-hosting.md`](docs/self-hosting.md) is the current answer.

---

## 2026-10-11

### Changed

- **Every dated figure in [`docs/comparison.md`](docs/comparison.md) now names the
  command that produced it.** A *Provenance of the dated figures* section carries the
  four calls behind the star counts, licences, operator coverage and release dates, so
  refreshing the page is a copy-paste rather than a reconstruction, and a reader can
  tell which call produced which cell. It also records what the GitHub API returns when
  a repository's licence cannot be identified, which is the distinction two of the
  claims on that page turn on.

## 2026-10-09

### Changed

- **[`docs/positioning.md`](docs/positioning.md) defers to the comparison page on the
  alternatives.** Both pages had asserted facts about GHDB, the form builders and the
  runners — two pages to keep in step, and the failure mode positioning.md closes by
  warning against. The three bullets stay as the short answer and now link to the
  matching comparison sections, and dated figures live in `comparison.md` alone, so
  there is exactly one page to refresh when a number moves.

## 2026-10-06

### Added

- **A comparison against the alternatives** ([`docs/comparison.md`](docs/comparison.md)):
  five tools grouped by what they actually are — a library, two runners, a form — on the
  grounds that the category decides most of the answer. Three of the five end with *use
  the other one*, including GHDB whenever a dork already exists for the question. It also
  states where DorkCraft is behind, and every figure in it was read from the GitHub API
  on the date the page gives.

## 2026-10-01

### Added

- **Code of conduct** ([`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), Contributor Covenant
  2.1), linked from the README and [`CONTRIBUTING.md`](CONTRIBUTING.md). DorkCraft is the
  repository most likely to attract a scope argument — `BLOCKED_PATTERNS` over-refuses by
  design and the scope table turns submissions away on purpose — and until now that
  argument had nowhere defined to go. A note under *Enforcement* separates a scope
  decision, which is a maintainer call, from a conduct problem, which is not.

## 2026-09-21

### Added

- **Self-hosting and deployment guide** ([`docs/self-hosting.md`](docs/self-hosting.md)):
  a Dockerfile and Compose file for the API plus the static build, the Render blueprint
  walkthrough, the two environment variables that matter, and an nginx reverse proxy that
  puts both halves on one origin — which removes CORS entirely and adds the rate limiting
  the API does not ship with. Documents the offline property explicitly: the backend makes
  no outbound connections, so a query never leaves the network it is typed on.

## 2026-09-11

### Added

- **Contributing guide** ([`CONTRIBUTING.md`](CONTRIBUTING.md)) with the six-field dork
  submission format — category, operator string, purpose, legal caveat, source, and the
  date the dork was last verified — a worked example, and an end-to-end walkthrough for
  adding an intent category. That walkthrough names the step that is easy to miss:
  registering the new category in `builder_map`, without which it is detected and then
  silently falls through to `general`.

## 2026-09-10

### Added

- **Security policy** ([`SECURITY.md`](SECURITY.md)): private vulnerability reporting, what
  is and is not in scope, the `ALLOWED_ORIGINS` change to make before deploying the API,
  and the responsible-use rules that come with the tool. States plainly what the safety
  blocklist guarantees — less than it appears to, being a keyword filter that also
  over-refuses.

## 2026-09-09

### Added

- MIT licence, and a README section explaining the choice: DorkCraft is meant to be
  vendored into other people's OSINT tooling, commercially included.

## 2026-05-16

### Added

- **Real-time dork validation and optimisation hints.** The generator now returns
  advisory notes alongside the query — an over-broad operator, a missing quote, a filter
  that will not narrow anything — surfaced per result in the UI.

## 2026-05-15

### Added

- Initial release of the rule-based dork engine (`backend/services/dork_generator.py`):
  natural-language intent detection, per-category query builders, and the
  `BLOCKED_PATTERNS` safety filter that refuses credential, PII, malware, exploit and
  unauthorised-access queries before any dork is generated.
- FastAPI backend with CORS handling and Pydantic request/response models.
- Astro + TypeScript frontend: search box, result cards, typed API client and the shared
  design system in `global.css`.
- GitHub Actions workflow deploying the frontend to GitHub Pages on every push to `main`.
- `render.yaml` blueprint for deploying the backend to Render.

### Changed

- The frontend moved from a git submodule into the repository, so a single clone gets a
  working checkout of both halves.
