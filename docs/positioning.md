# Positioning

The repository description and the homepage field are the only text GitHub shows
for DorkCraft in search results, on the profile grid, on a topic page and in the
sidebar of anyone who stars it. They are read far more often than the README.

DorkCraft's description is currently **`Google Dork helper`** — nineteen
characters, one of them a trailing space. It says what the tool is filed under,
not what it does or who should click. The homepage field is empty even though
[the site is live](https://juandresrodca.github.io/DorkCraft/). This page fixes the wording once so it is not
re-invented every time someone opens the repository settings.

---

## The canonical one-liner

```
Turn plain English into Google dork operators - an OSINT query builder with a safety blocklist.
```

95 characters. GitHub truncates a description at around 100 in search
results and on the profile grid, so it has to land inside that budget with the
benefit first.

What it is doing, clause by clause:

| Clause | Why it is there |
|---|---|
| *Turn plain English into Google dork operators* | The actual job, in the reader's words. No jargon that needs the README to decode. |
| *an OSINT query builder* | The category, so someone scanning a topic page knows which shelf it belongs on. |
| *with a safety blocklist* | The honest differentiator. Most dork tooling ships every operator it can think of; this refuses a set of them, and [`SECURITY.md`](../SECURITY.md) says exactly how far that guarantee goes. |

Two alternatives were written and rejected:

| Rejected | Why |
|---|---|
| `Google dork generator: describe what you are looking for, get the operators. OSINT, Astro + FastAPI.` | 100 characters — sitting on the truncation limit — and it spends a fifth of them on the stack. Astro and FastAPI belong in the topics, where someone filtering by them will actually look. |
| `Natural-language Google dork builder for OSINT and research, with a refusal list for harmful queries.` | 101 characters, over budget. *Refusal list* is also internal vocabulary; *blocklist* is what the rest of the repository calls it. |

Rules that fall out of this, for whoever writes the next one:

1. **Lead with the verb, not the noun.** *Turn plain English into…* beats *A tool
   that turns…*; the first three words are most of what a search result gets read for.
2. **No stack names.** The topics already carry `astro` and `fastapi`. A
   description that repeats them has less room for the benefit.
3. **No superlatives.** *Advanced*, *powerful* and *the best* are filler that
   survives no scrutiny and reads as noise next to a single-digit star count.
4. **ASCII only.** An em dash or an arrow renders fine on github.com and badly in
   several of the places that mirror a description.

---

## The homepage field

Set it to:

```
https://juandresrodca.github.io/DorkCraft/
```

The published frontend cannot currently generate a dork —
[#1](https://github.com/juandresrodca/DorkCraft/issues/1) is open on exactly that,
and [`CHANGELOG.md`](../CHANGELOG.md) records it as a known fault. The field is
still worth setting: GitHub renders it as a link in the sidebar, and a visitor who
wants the tool working follows [`docs/self-hosting.md`](self-hosting.md) rather
than the demo. Leaving it empty hides the demo from people who would forgive it;
setting it while the bug is open and documented in three places is the more honest
of the two states.

When #1 closes, nothing on this page changes. That is the point of writing it down.

---

## Applying it

Both fields live on the repository object, so one API call sets them:

```bash
gh repo edit juandresrodca/DorkCraft \
  --description "Turn plain English into Google dork operators - an OSINT query builder with a safety blocklist." \
  --homepage "https://juandresrodca.github.io/DorkCraft/"
```

Or without the CLI:

```bash
curl -X PATCH https://api.github.com/repos/juandresrodca/DorkCraft \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"description":"Turn plain English into Google dork operators - an OSINT query builder with a safety blocklist.","homepage":"https://juandresrodca.github.io/DorkCraft/"}'
```

Either call needs a token with **Administration: write** on the repository.
Contents and Issues are not enough: a token holding only those gets `403 Resource
not accessible by personal access token`. That is why this page exists rather than
the change having already been made — the automation that maintains these docs
deliberately holds no administration scope.

---

## Who DorkCraft is for

| Reader | What they want | Does DorkCraft serve them? |
|---|---|---|
| An analyst who already knows the operators | A faster way to assemble a query they could have written themselves | Partly. The `variations` are the useful part; the primary dork rarely beats what they would type. |
| Someone learning the operators | The syntax next to an explanation of it | Yes, and this is the strongest case. The `explanation` array is the feature. |
| A journalist or researcher | Public-record discovery without a syntax reference open in another tab | Yes. |
| A red team after credential or exploit dorks | Operators the blocklist refuses | No, deliberately. The refusal list is a design decision, not a gap to be filed. |
| A SOC that cannot send queries to a third party | A local deployment | Yes — [`docs/self-hosting.md`](self-hosting.md). The backend makes no outbound connections at all. |

## Where it sits among the alternatives

Stated plainly, because a description implying more than this would be overselling it:

- The [Google Hacking Database](https://www.exploit-db.com/google-hacking-database)
  is a curated corpus of dorks people have already written. It is a library;
  DorkCraft is a builder. They are complementary, and GHDB is the better starting
  point whenever an existing dork already matches the question.
- Form-based dork builders give you a field per operator and leave the intent to
  you. DorkCraft's difference is that it classifies the sentence first and picks
  the operators from that — worth something when you do not yet know which
  operator you want, and worth nothing when you do.
- Automated dork *runners* submit queries to a search engine and collect results.
  DorkCraft does not, and is not going to: the backend never makes an outbound
  request, which is the property that makes an offline deployment possible at all.

---

*Keep this page and the repository settings in step. If the description changes on
github.com, change it here in the same sitting — a positioning document that
disagrees with the live metadata is worse than no document.*
