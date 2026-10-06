# How DorkCraft compares

Anyone who already uses a dork tool arrives with the same question: *why not the
one I have?* This page answers it before the reader leaves, and it answers it
honestly — three of the five comparisons below end with "use the other one".

The alternatives are grouped by what they actually are, because the category
decides most of the answer. A library, a builder and a runner are not competing
products; they are three different steps of the same job.

| | DorkCraft | [GHDB](https://www.exploit-db.com/google-hacking-database) | [pagodo](https://github.com/opsdisk/pagodo) | [sitedorks](https://github.com/Zarcolio/sitedorks) | Google Advanced Search |
|---|---|---|---|---|---|
| Category | Builder | Library | Runner | Runner | Form |
| Input | A sentence | A keyword search over existing dorks | A GHDB dork file | A search term plus a site list | One field per operator |
| Operators it emits | 5 (`site:`, `filetype:`, `intitle:`, `intext:`, `inurl:`) | Whatever the corpus contains | Whatever the corpus contains | `site:` plus your term | ~8, including date and language |
| Explains the operators | Yes — an `explanation` array per result | No | No | No | Partly, as field labels |
| Submits the query for you | Never | n/a | Yes | Yes | Yes |
| Self-hostable | Yes — [`self-hosting.md`](self-hosting.md) | No | Yes | Yes | No |
| Works fully offline | Yes, for query generation | No | No, needs a search engine | No, needs a search engine | No |
| Refuses harmful queries | Yes, a keyword blocklist | No, by design | No | No | No |
| Licence | MIT | Site terms; not a redistributable corpus | GPL-3.0 | GPL-3.0 | Proprietary |

Star counts, licences and descriptions above were read from the GitHub API on
6 October 2026. The two runners are the ones most people mean by "a dork tool":
pagodo at 3,400 stars and sitedorks at 1,056.

---

## Against the Google Hacking Database

GHDB is a curated corpus of dorks that people have already written, tested and
submitted — thousands of them, maintained by OffSec. DorkCraft holds none.

**Use GHDB when an existing dork already matches the question.** That covers more
cases than this page would like to admit. If you want exposed Jenkins consoles or
a known camera-feed signature, somebody has written that dork better than a
sentence classifier will assemble it, and GHDB will hand it to you with a date and
an author.

DorkCraft is for the other case: a question nobody has filed, where you do not yet
know which operator you want. The classifier picks the operators from the intent,
and the `explanation` array says why it picked them — which is the part a corpus
cannot do, because a corpus has no reason to explain a query it is only storing.

The two are complementary, and the honest reading is that GHDB is the better first
stop. Searching it costs one page load.

## Against the runners — pagodo and sitedorks

pagodo (3,400 stars, GPL-3.0, Python) scrapes GHDB and then runs the dorks against
Google with proxy support and jitter. sitedorks (1,056 stars, GPL-3.0, Python)
takes a term and sweeps it across a default list of sites over several engines.
Both are more useful than DorkCraft for the thing they do, and neither overlaps
with it: they consume dorks, they do not compose them.

**Use a runner when you want results rather than a query.** That is the whole
gap. DorkCraft hands you a string to paste; a runner hands you hits.

The reason DorkCraft does not and will not submit anything is stated in
[`positioning.md`](positioning.md) and it is not modesty: the backend makes no
outbound request at all, which is the single property that makes an air-gapped
deployment possible. Adding a runner would cost that, and the SOC readers in
[`self-hosting.md`](self-hosting.md) are the ones who would pay. A runner also
inherits a rate-limiting and terms-of-service problem that a generator simply
does not have.

If automated collection is what you need, run pagodo. It is the mature tool for it.

## Against form-based builders

Google's own Advanced Search, and the various web dork builders that copy its
shape, give you a field per operator and leave the intent to you. They cover more
operators than DorkCraft's five — date ranges, language and region filters, exact
numeric ranges — and they need no installation.

**Use a form when you already know which operator you want.** Filling in
`filetype:` yourself is faster than describing a document in prose and hoping the
classifier agrees with you.

DorkCraft's difference is the step before that: it classifies the sentence into one
of nine intent categories and chooses the operators from the classification. That
is worth something while you are still learning the syntax, and worth nothing once
you know it. [`positioning.md`](positioning.md) says the same thing in the table of
who the tool is for, and reaches the same conclusion: the strongest case is
somebody learning the operators, not the analyst who has them memorised.

## Against the shell-script scanners

[Fast-Google-Dorks-Scan](https://github.com/IvanGlinkin/Fast-Google-Dorks-Scan)
(1,743 stars) and [uDork](https://github.com/m3n0sd0n4ld/uDork) (866 stars) take a
domain and sweep a fixed battery of dorks across it. Both are Bash, both are
widely used in recon workflows, and neither publishes a licence file — which
matters if you intend to vendor one into commercial work. DorkCraft is MIT
precisely so it can be vendored; see the licence note in the README.

These scanners answer "what is exposed on this domain?". DorkCraft answers "how do
I phrase this search?". There is no sensible comparison beyond that, and a reader
who wants the first question answered should take the scanner.

---

## Where DorkCraft is genuinely ahead

Four things, and the list is short deliberately.

1. **It explains itself.** Every result ships an `explanation` array naming each
   operator it used and why. Nothing else in this table does that, because nothing
   else in this table is trying to teach.
2. **It refuses a set of queries.** `BLOCKED_PATTERNS` turns away credential,
   payment-data, malware and exploit phrasings before generation.
   [`SECURITY.md`](../SECURITY.md) is candid about how far that guarantee goes — it
   is a keyword filter, it over-refuses, and it is not a safety boundary you should
   rely on. No other tool here attempts it at all.
3. **It is genuinely offline-capable.** The backend makes no outbound request, so
   a generated query never leaves your network. Every runner in this table needs a
   search engine to be useful.
4. **MIT, and meant to be vendored.** The `DorkGenerator` class is designed as a
   drop-in extension point. Two of the four GitHub alternatives are GPL-3.0 and two
   publish no licence at all.

## Where it is behind

1. **Five operators.** No date ranges, no `AROUND()`, no `numrange:`, no language or
   region filters. A form beats it on coverage.
2. **No corpus.** GHDB's thousands of tested dorks are a real asset and DorkCraft
   has nothing equivalent. The submission workflow in
   [`CONTRIBUTING.md`](../CONTRIBUTING.md) is the beginning of one — six fields,
   four confirmations, and a requirement that you ran the operator yourself on a
   stated date — but a workflow is not yet a library.
3. **The classifier is keyword-scored, not semantic.** It matches trigger words, so
   a sentence that uses none of them falls through to `general`. Issue
   [#3](https://github.com/juandresrodca/DorkCraft/issues/3) is open on a real
   instance of this: `_detect_filetype` matches substrings, so *docker* selects
   `filetype:doc`.
4. **The published demo is broken.** [#1](https://github.com/juandresrodca/DorkCraft/issues/1)
   is open on it. Running both halves locally is unaffected, and
   [`self-hosting.md`](self-hosting.md) is the route a serious reader takes anyway —
   but a comparison page that omitted this would not be worth reading.

---

*Keep this page truthful as the alternatives move. Star counts and licences were
read on 6 October 2026; the categories are structural and will not drift, but a
tool that adds a licence or an operator set makes a row here wrong. If a claim in
the table cannot be checked in one page load, it does not belong in the table.*
