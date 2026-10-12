<!--
Thanks for contributing to DorkCraft.

Two things worth knowing before you read the checklists:

1. There is no test suite yet, and the only workflow here deploys the frontend to
   Pages. A green tick means the site built — it does not mean the engine still
   works. That is why the sections below ask you to paste what you ran.
2. Most of this template is deletable. A typo fix, a broken link or a docs-only
   change needs **What this changes** and nothing else. Delete the rest.
-->

## What this changes

<!-- One or two sentences on why it matters rather than a restatement of the diff. -->

Closes #

## Adding a dork or a category?

<!-- Delete this whole section if you are not. -->

The six fields from [CONTRIBUTING](https://github.com/juandresrodca/DorkCraft/blob/main/CONTRIBUTING.md#submitting-a-dork), in the same
order the **Submit a dork** issue form asks for them. All six, because a maintainer
needs to be able to act on this without a conversation first.

- **Category:** <!-- an existing CATEGORIES key, or `new: <name>` with the one-line case -->
- **Operator string:** <!-- exactly as typed into Google, in a code fence, placeholders in <angle brackets> -->
- **Purpose:** <!-- one sentence: what a person is trying to find, and who that person is -->
- **Legal caveat:** <!-- what the searcher must own, be authorised for, or respect. "None — results are published by their subjects for this purpose" is a valid answer, written explicitly -->
- **Source:** <!-- your own work, an operator reference, a write-up. Link it -->
- **Verified on:** <!-- the date you actually ran it, and roughly what came back -->

- [ ] I ran this operator string myself on the date above. I have not copied it untested.
- [ ] It targets information published for public consumption — not credentials, keys, tokens, payment data, personal records, or a named private individual.
- [ ] It contains no real host, path or identifier belonging to an estate I do not own.
- [ ] The source above permits reuse. I have not lifted it from a restrictively licensed dork database.

If this adds a category, all three edits are in `backend/services/dork_generator.py`:
`CATEGORIES`, the `_build_*_dork()` function, and the entry in `builder_map`. The third
is the one people forget, and without it the category is detected and then falls through
to `general`.

- [ ] The category is registered in `builder_map`, not only declared in `CATEGORIES`
- [ ] The README examples table has a row for it

## Touching the engine, the API or the site?

<!-- Delete this whole section if you are not. -->

- [ ] **Before and after:** the query I typed and the JSON that came back, both ways, pasted below
- [ ] **The refusal still holds:** if I went near `is_safe_query()`, one blocked query still returning `400`, shown below
- [ ] **No new dependencies** under `backend/services/`, and no outbound call from the engine
- [ ] **README updated** if I changed behaviour a user can see

```
$ curl -s localhost:8000/generate -H 'Content-Type: application/json' \
       -d '{"query":"..."}' | python -m json.tool
```

## Scope

[Scope](https://github.com/juandresrodca/DorkCraft/blob/main/CONTRIBUTING.md#scope-what-belongs-in-dorkcraft) is the line this project
exists on the right-hand side of, and it is not a formality. Arguing that a dork sits
on the other side of the table, or that `BLOCKED_PATTERNS` over-refuses, is the normal
business of this repository — narrowing a pattern is a welcome pull request, provided
the description shows one phrasing that starts passing and one that still fails.
Widening the engine to generate what the right-hand column describes is not.

- [ ] This change stays on the publishing side of the scope table

## Anything a reviewer should know

<!--
Trade-offs, an operator reference that says something surprising, a decision you went
back and forth on. With no CI to lean on, this is the most useful part of the
description.

House style, for reference: British spelling in prose, four-space indentation and type
hints in Python, TypeScript rather than plain JavaScript in the frontend, and
Conventional Commit subjects in the imperative.
-->
