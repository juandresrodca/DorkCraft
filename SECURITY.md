# Security Policy

DorkCraft builds search queries. It never runs them, never fetches a result page
and never stores what you typed. That keeps the attack surface small, but a tool
in this category still owes its users a stated policy rather than an assumption,
so here it is.

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Report privately through GitHub:
[Security → Report a vulnerability](https://github.com/juandresrodca/DorkCraft/security/advisories/new).
If private reporting is unavailable to you, email **juandresrodca@gmail.com**
with `DorkCraft security` in the subject.

Please include:

- which surface is affected — the API (`backend/`), the site (`frontend/`), or a
  deployment of your own,
- the request you sent and the response you got, verbatim,
- what you expected instead, and why it matters,
- any redacted output. Never paste a third party's data into an issue or an
  email to demonstrate a finding.

What to expect:

| Stage | Target |
|---|---|
| Acknowledgement | 72 hours |
| Initial assessment | 7 days |
| Fix or documented mitigation | 90 days, sooner where the severity warrants |

Credit is offered in the release notes unless you would rather stay anonymous.

## Supported versions

DorkCraft is developed on `main`, and the deployed site tracks it. Fixes land on
`main`; there are no maintained release branches. If you vendored
`DorkGenerator` into your own project, the safety blocklist became yours to
maintain at that point — the [licence note in the README](README.md#licence) says
so deliberately.

## In scope

- Injection or command execution through the `/generate` request body.
- A crafted query that escapes the operator builder and produces output the
  category templates were never meant to emit.
- Denial of service against the API that a small number of requests can trigger.
- Anything in `frontend/` that turns generated text into executed script in a
  visitor's browser.
- A dependency advisory affecting `backend/requirements.txt` or
  `frontend/package.json`.

## Out of scope

- **A dork that finds something sensitive.** That is the tool working. Search
  operators are documented Google syntax; DorkCraft composes them, it does not
  discover anything Google does not already index. If a public site exposes data
  it should not, report it to that site's owner.
- **Bypassing the query blocklist.** See below — it is a guard rail, not a
  security boundary, and reports that it can be worded around are not findings.
- Missing hardening on a deployment you control (rate limiting, WAF, an origin
  policy you configured). See *Deploying safely*.
- Findings produced only by automated scanners, with no working request behind
  them.

## What the blocklist is, and is not

`BLOCKED_PATTERNS` in
[`backend/services/dork_generator.py`](backend/services/dork_generator.py) refuses
queries mentioning credential and key theft, payment data and national
identifiers, malware and exploitation, and child abuse material. A refused query
returns `400` with `{"error": "Unsafe or disallowed query."}` and no dork.

Two honest caveats, because a guard rail described as a wall is worse than no
guard rail at all:

- **It is a keyword filter over the user's plain English, not over the generated
  operators.** Rewording gets past it. It exists to stop the obvious and the
  accidental, and to make the project's intent explicit — not to make misuse
  impossible.
- **It over-refuses.** `\bvulnerabilit(y|ies)\b` and `\bhack(ing|ed)?\b` block
  legitimate research phrasing such as *"find vulnerability disclosure policies"*
  or *"articles about the hacking of X"*. That trade is intentional for now.
  Narrowing the patterns without opening the category is a welcome pull request.

Neither is a vulnerability report. Both are ordinary issues.

## Deploying safely

The bundled backend is configured for a public demo, not for your production:

- `ALLOWED_ORIGINS` in [`backend/main.py`](backend/main.py) ends with `"*"`.
  Replace it with your own origins before you deploy. Credentials are already
  disabled (`allow_credentials=False`), so this is not a session-theft risk, but
  it does mean anyone's page can call your instance and spend your quota.
- There is **no rate limiting**. Put the API behind one — a reverse proxy, your
  platform's edge, or an API gateway — before exposing it.
- The API needs no secrets, no database and no outbound network access. If your
  deployment gives it any of those, something has been added that this policy
  does not cover.

## Responsible use

DorkCraft is built for OSINT practitioners, academic research and public
information discovery. Using it means accepting the following.

- **Authorised targets only.** Reconnaissance against systems you do not own or
  have not been explicitly permitted to test is illegal in most jurisdictions —
  the Criminal Justice (Offences Relating to Information Systems) Act 2017 in
  Ireland, the Computer Misuse Act 1990 in the United Kingdom, the Computer Fraud
  and Abuse Act in the United States, and equivalent legislation elsewhere. A
  signed scope document is what makes a test authorised; a screenshot of a public
  page is not.
- **No automated mass scraping.** DorkCraft generates one query for a person to
  run. Feeding its output into a bulk scraper breaks the terms of service of
  every search engine it targets, and is not a use this project supports.
- **Respect `robots.txt`, rate limits and terms of service** on anything you
  visit as a result of a query.
- **People are not targets.** Operators such as `site:linkedin.com/in` are in
  here for legitimate research and recruitment work. Aggregating them into a
  profile of a private individual is harassment, and depending on where you and
  they live, it is also a data-protection offence.
- **Handle what you find carefully.** If a query surfaces exposed personal data,
  the responsible action is to stop, not to enumerate. Disclose to the owner and
  delete your copy.

Using DorkCraft to break the law is your decision and your liability. The
[MIT licence](LICENSE) disclaims warranty; this section states intent.

## Reporting misuse

If you find a deployment of DorkCraft being used to harass someone or to attack
systems, open an issue naming the deployment — not the victim — or email the
address above.
