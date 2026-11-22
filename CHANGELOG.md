# Changelog

All notable changes to DorkCraft are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project intends to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) from its first tagged
release onwards.

> **Tagging starts at 0.1.0.** Everything below that heading was reconstructed from the
> commit history and is grouped by the date the work landed on `main`; all of it ships
> in 0.1.0. The API metadata in `backend/main.py` used to say `1.0.0` and
> `frontend/package.json` said `0.0.1`. Both now say `0.1.0`.

## [Unreleased]

### Added

- **A preview card for shared links.** `frontend/public/og.png` (1280×640, cropped from
  the live page) is set as `og:image` and `twitter:image`, so a link to the site on
  LinkedIn, X, Slack or Discord shows the tool instead of a bare URL. The same file
  works as the repository's social preview.
- **`sitemap.xml` and structured data for search engines.** The sitemap is what Bing
  Webmaster Tools and Google Search Console ask for, and a `WebApplication` block tells
  them the page is a free web tool.
- **Search engines hear about each deploy.** A third job in `deploy.yml` pings
  [IndexNow](https://www.indexnow.org/) once the site is live, so Bing, Yandex and the
  other engines that share it recrawl the page in hours rather than days. The key file in
  `frontend/public/` is public by design, the ping only warns if it fails, and forks skip
  it because they deploy to another host.

### Planned

- A test suite. There is none yet, which is why
  [`CONTRIBUTING.md`](CONTRIBUTING.md) asks a pull request to show the before-and-after
  output of the queries it changes.
- Rate limiting on the API. The backend ships without it; the nginx configuration in
  [`docs/self-hosting.md`](docs/self-hosting.md) is the current answer.
- One place to declare the version. It is written twice today, in `backend/main.py`
  and `frontend/package.json`, and a release has to change both.

## [0.1.0] - 2026-11-22

The first tagged release. It turns the demo into something usable: the generator
builds dorks from the wording of the request, a panel scores each one, and the live
site generates dorks again.

### Added

- **A search effectiveness panel beside the result.** Ten checks on how the generated
  dork is built, grouped as targeting, reach and coverage, with a score and the reason
  for every pass and fail. It catches the generator's own weak spots: phrases stitched
  together from words that were apart in the request, keywords that repeat an operator,
  terms from the request that went missing, and `filetype:ppt|pptx`, which Google does
  not read as a list. The score comes from the dork's text alone; no search is run.
- **A list of ten common dork patterns** beside the search box. Hovering or focusing a
  pattern shows what it does, and clicking copies it.
- **Shortcuts for the patterns you use.** Double-clicking a common pattern, or pressing
  Shift+Enter on it, pins it as a small button under the list. A shortcut copies on one
  click, explains itself on hover, and goes away on a double-click or Delete. Shortcuts
  are kept in the browser.
- **Save to history, and a Markdown download of it.** Each saved search records the date
  and time, the request, the dork and its score. Entries stay in the browser, up to 50.
- **The live site says when the API is waking up.** The demo API runs on a free
  instance that sleeps after 15 idle minutes and takes 40 to 50 seconds to wake. After
  three seconds without an answer the page now explains the wait instead of showing only
  a spinner.
- **`.github/workflows/keep-warm.yml` pings the API every ten minutes**, so most
  visitors never meet that wake-up at all.

### Changed

- **Dorks keep the request's wording.** The generator used to join the first four
  keywords into one quoted phrase, so *"PDF books about Linux malware"* became
  `intitle:"pdf books linux malware"`, a phrase no title contains. It now groups only
  words that were next to each other in the request, drops words an operator already
  covers (*pdf*, *books*, *profiles*, *github*), keeps two-letter terms such as *cv*,
  and reads *titled X* as `intitle:` and *mentions X* as `intext:`. Across the six example
  chips and ten other test requests, the average effectiveness score went from 66 to
  96, Strong ratings went from 1 of 16 to 12, and every chip except *Directories* now
  rates Strong. Directory
  listings have no site or file type to scope them to, so that one stays Fair.
- **A plainer look.** The indigo-to-pink gradients, glows and pill shapes are gone:
  neutral greys, one solid violet, tighter corners and the system UI font replace them.
  "Google" in the title is in Google's own colours, and the example chips lost their
  emoji. The primary button now has black text on violet, because white on that violet
  falls short of WCAG AA contrast.
- **History is saved on request, not automatically.** The page used to store the last
  ten searches by itself. It now stores a search only when *Save to history* is pressed,
  which matches the footer's statement that queries are not kept. Searches the old
  version stored are still listed, with a score worked out for each.
- **The page background is plain black easing to grey.** The tiled grid and the purple
  glow behind it are gone.
- **The green badge on a result reads "Valid syntax", not "Optimized".** It only ever
  meant the backend raised no syntax warning, and it now sits next to a panel that may
  rate the same dork as weak.
- **The client script moved out of `index.astro` into `src/scripts/app.ts`**, with the
  scoring, history and pattern list as separate modules under `src/lib/`.

### Fixed

- **File types and categories match whole words.** *docker* no longer selects
  `filetype:doc`, and `docx`, `xlsx` and `pptx` are reachable instead of being caught
  by their shorter prefixes ([#3](https://github.com/juandresrodca/DorkCraft/issues/3)).
  Presentations get `filetype:pptx` rather than `filetype:ppt|pptx`, which Google
  reads as `filetype:ppt` or the plain word *pptx*.

- **Copy buttons keep their icon.** The "Copied" confirmation used to replace the
  button's contents and restore only the text.
- **Motion respects `prefers-reduced-motion`**, and hover movement no longer sticks on
  touch screens.
- **The published site generates dorks.** The deployed build reads the API URL from the
  `VITE_API_URL` secret and the API answers CORS for the Pages origin, so the fault
  recorded in [#1](https://github.com/juandresrodca/DorkCraft/issues/1) no longer
  reproduces. A connectivity failure now reads as one, with a retry hint instead of a
  local port number.
- **Exported Markdown links to this repository** rather than to a `yourusername`
  placeholder.
- **The README examples show what the tool produces today.** The table showed idealised
  output; each row is now the live API's answer to that exact input.

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

<!-- Comparison links. Anchored by the rule in [EntraHuntKit/docs/changelog-anchors.md](https://github.com/juandresrodca/EntraHuntKit/blob/main/docs/changelog-anchors.md#the-anchor-rule),
     which is stated there once and cited here: v0.1.0 is the first tag, so under rule 5
     [Unreleased] compares from it and [0.1.0] points at its release. The dated headings
     above record when work landed on main before tagging began, so they are not
     versions and take no definition. -->
[Unreleased]: https://github.com/juandresrodca/DorkCraft/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/juandresrodca/DorkCraft/releases/tag/v0.1.0
