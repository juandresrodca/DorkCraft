# Contributing to DorkCraft

Thanks for looking. DorkCraft grows in two directions, and they need very
different pull requests:

- **New dorks and new intent categories** — the search knowledge. Most
  contributions are this, and you do not need to be a Python developer to send
  one; the [dork submission format](#submitting-a-dork) below is a form you can
  fill in from an issue.
- **The engine, the API and the site** — the plumbing that turns plain English
  into an operator string.

Both are welcome. What is not welcome is covered in
[Scope](#scope-what-belongs-in-dorkcraft), and it is worth reading before you
write anything.

---

## Scope: what belongs in DorkCraft

DorkCraft is for **finding public information that someone chose to publish** —
research papers, company filings, open-source projects, professional profiles,
documentation. That is the line, and it is not a formality: the whole reason the
project can exist as a public site is that it stays on this side of it.

| Belongs here | Does not |
|---|---|
| `filetype:` document discovery, academic and standards sources | Anything shaped at credentials, keys, tokens or session material |
| Company and organisation research from published sources | Payment data, national identifiers, health or other personal records |
| Public professional profiles by role and location | Locating, tracking or profiling a named private individual |
| Open-directory signatures used to *audit your own* estate | Pointing the same signatures at estates you do not own |
| Operators that make a legitimate search sharper | Anything whose purpose only makes sense as intrusion or harassment |

The right-hand column is refused by `BLOCKED_PATTERNS`, and a pull request that
widens the engine to accommodate it will be closed. [SECURITY.md](SECURITY.md)
explains what that blocklist actually guarantees — less than it looks like — and
the responsible-use rules that come with the tool.

---

## How the pieces fit

Two halves that only meet over one HTTP call:

```
frontend/ (Astro + TypeScript)            backend/ (FastAPI + Pydantic)
┌──────────────────────────────┐        ┌────────────────────────────────────┐
│ pages/index.astro            │        │ main.py                            │
│   page + all client logic    │        │   CORS, /health, POST /generate    │
│ components/SearchBox.astro   │ POST   │ models/schemas.py                  │
│ components/ResultCard.astro  │ ─────► │   GenerateRequest / DorkResponse   │
│ lib/api.ts                   │ /gen   │ services/dork_generator.py         │
│   typed client, one fetch    │ ◄───── │   safety → intent → keywords →     │
└──────────────────────────────┘  JSON  │   builder → validation             │
                                        └────────────────────────────────────┘
```

Inside `DorkGenerator.generate()` the order is fixed, and every contribution
lands in one of those five steps:

1. **Safety** — `is_safe_query()` matches the raw query against
   `BLOCKED_PATTERNS`. A refusal returns `400` and no dork.
2. **Intent** — `_detect_category()` scores every entry in `CATEGORIES` by how
   many of its `triggers` appear as substrings of the cleaned query. Highest
   score wins; nothing scoring wins `general`.
3. **Keywords** — `_extract_keywords()` strips punctuation, `STOP_WORDS` and
   tokens of two characters or fewer.
4. **Build** — `builder_map` routes the category to a `_build_*_dork()`
   function, which returns the primary dork plus two or three variations.
5. **Validate** — the 32-word Google limit, deprecated operators (`link:`,
   `info:`, `inanchor:`) and `OR`-heavy queries produce `warnings`. Only the
   length problem clears `is_valid`.

The engine is deliberately rule-based and dependency-free, so it answers
instantly and so an LLM provider can be dropped in behind the same `generate()`
contract later. Keep both properties: **no network calls and no new runtime
dependencies in `backend/services/`.**

---

## Running it locally

```bash
# backend — Python 3.9+
cd backend
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000               # http://localhost:8000/docs
```

```bash
# frontend — Node 20+, second terminal
cd frontend
npm install
npm run dev                                         # http://localhost:4321
```

The frontend reads `PUBLIC_API_URL` and falls back to `http://localhost:8000`,
so the pair works with no configuration. If the site loads but every query
reports *"Could not reach the DorkCraft backend"*, the backend is not running,
or you are testing the **published** site — that one has its own open bug,
[issue #1](https://github.com/juandresrodca/DorkCraft/issues/1), and is not
something your branch broke.

Quick check that the engine is alive, without the frontend:

```bash
curl -s localhost:8000/generate -H 'Content-Type: application/json' \
     -d '{"query":"Find PDF books about Linux malware analysis"}' | python -m json.tool
```

---

## Submitting a dork

This is the main contribution path, and it has a strict shape so that a
maintainer can act on it without a conversation. Open an issue titled
`dork: <short description>` containing exactly these six fields.

| Field | Rules |
|---|---|
| **Category** | One of the existing `CATEGORIES` keys — `documents`, `people`, `linkedin`, `github`, `academic`, `directories`, `social_media`, `company`, `general` — or `new: <name>` with a one-line case for it |
| **Operator string** | The dork itself, exactly as typed into Google, in a code fence. Placeholders in angle brackets: `<topic>`, `<domain>` |
| **Purpose** | One sentence on what a person is trying to find, and who that person is |
| **Legal caveat** | What the searcher must own, be authorised for, or respect. `None — results are published by their subjects for this purpose` is a valid answer, but write it explicitly |
| **Source** | Where you got it: your own work, an operator page, a write-up. Link it. Do **not** paste from a dork database with a restrictive licence |
| **Verified on** | The date you actually ran it, and roughly what came back |

### Worked example

> **Category:** `academic`
>
> **Operator string:**
> ```
> site:arxiv.org filetype:pdf intitle:<topic> after:2024-01-01
> ```
>
> **Purpose:** a researcher wants recent arXiv preprints on a topic as PDFs,
> without arXiv's own listing pages diluting the results.
>
> **Legal caveat:** none. arXiv publishes these openly and its robots policy
> permits indexing; respect the rate limits if you automate the search.
>
> **Source:** my own, built from arXiv's stated URL structure — `arxiv.org/pdf/`
> for the document, `/abs/` for the landing page.
>
> **Verified on:** 11 September 2026 — about 40 results for `intitle:"graph
> neural network"`, all preprints from 2024 onwards, no listing pages.

A submission that skips **Legal caveat** or **Verified on** will be asked for
them before anything else happens. Those two fields are the difference between a
curated list and a scraped one.

---

## Adding an intent category

Three edits, all in `backend/services/dork_generator.py`, in this order.

**1. Declare it in `CATEGORIES`.** `triggers` are matched as plain substrings of
the lowercased, punctuation-stripped query, so keep them short and
unambiguous — a trigger like `code` will fire on *"dress code"*. `explanation`
is what the user reads under the result: three lines, one per operator, saying
what it does rather than restating it.

```python
"standards": {
    "triggers": ["rfc", "standard", "specification", "iso ", "nist"],
    "explanation": [
        'site: scopes results to the bodies that publish the standard',
        'filetype:pdf retrieves the document rather than a summary page',
        'intitle: keeps the topic in the heading, not merely somewhere on the page',
    ],
},
```

**2. Write the builder.** It takes the extracted keywords (plus the cleaned
query, if it needs to look for a modifier) and returns
`(dork, variations)`. Slice the keywords — four terms is usually the ceiling
before Google starts ignoring them — and use `_quote()` rather than adding
quotes yourself, so single words stay unquoted.

```python
def _build_standards_dork(keywords: List[str]) -> Tuple[str, List[str]]:
    topic = " ".join(keywords[:4])
    dork = f'(site:rfc-editor.org OR site:nist.gov) filetype:pdf intitle:{_quote(topic)}'
    variations = [
        f'site:rfc-editor.org {_quote(topic)}',
        f'filetype:pdf {_quote(topic)} (RFC OR specification)',
    ]
    return dork, variations
```

**3. Register it in `builder_map`** inside `generate()`. This is the step people
forget; without it the category is detected and then silently falls through to
`general`.

```python
"standards": lambda: _build_standards_dork(keywords),
```

Then add a row to the README's examples table, because that table is what most
visitors read instead of the code.

### Touching the blocklist

`BLOCKED_PATTERNS` over-refuses on purpose, and SECURITY.md says so. Narrowing
a pattern is a welcome pull request — `\brat\b` and `\bvulnerabilit(y|ies)\b`
are the two worst offenders — provided the pull request shows, in its
description, one phrasing that starts passing and one that still fails.
**Removing a whole category of refusal is not on the table.**

---

## What is expected of a pull request

There is **no automated test suite yet**, which puts the burden on the
description. Include:

- **Before and after.** For an engine change, the query you typed and the JSON
  that came back, both ways. `curl` output pasted into the description is fine.
- **The refusal still holds.** If you went anywhere near `is_safe_query()`, show
  one blocked query still returning `400`.
- **No new dependencies** in `backend/requirements.txt` for anything under
  `services/`, and no outbound calls from the engine.
- **A changed README** if you changed behaviour a user can see.

Adding pytest to `backend/` is itself a genuinely useful contribution and would
be reviewed happily — start with `is_safe_query()` and `_detect_category()`,
which are pure functions and need no fixtures.

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org)
as the existing history does — `feat:`, `fix:`, `docs:`, `chore:` — with a body
explaining *why* when the subject cannot carry it.

Keep the existing style: British spelling in prose, four-space indentation and
type hints in Python, the section-banner comments the modules already use, and
TypeScript in the frontend rather than plain JavaScript.

---

## Licence

By contributing you agree that your work is published under the
[MIT licence](LICENSE), the same terms as the rest of DorkCraft. If you are
contributing on an employer's time, make sure that is a thing you are allowed to
agree to.
