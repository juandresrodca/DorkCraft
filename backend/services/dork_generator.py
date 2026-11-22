"""
DorkCraft — Core Google Dork Generation Engine
================================================
This module contains the rule-based DorkGenerator class.
It is intentionally free of external AI dependencies so that:
  - it runs instantly with zero latency
  - a coding agent (Gemini CLI, Claude Code, etc.) can drop an AI provider in
    by replacing / extending the `generate()` method

Architecture:
  1. Safety check   — refuse harmful queries
  2. Intent detect  — classify the query into a category
  3. Term extract   — split the request into subject, title, body and extra terms
  4. Operator map   — build the dork from operator templates
  5. Variations     — produce 2-3 alternative phrasings
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ---------------------------------------------------------------------------
# Safety guardrails — patterns that trigger an immediate refusal
# ---------------------------------------------------------------------------
BLOCKED_PATTERNS: List[str] = [
    # credential / access theft
    r"\bpassword(s)?\b", r"\bpasswd\b", r"\bssh[\s_-]?key\b",
    r"\bprivate[\s_-]?key\b", r"\bapi[\s_-]?secret\b",
    r"\bauth[\s_-]?token\b", r"\baccess[\s_-]?token\b",
    # payment / PII
    r"\bcredit[\s_-]?card\b", r"\bssn\b", r"\bsocial[\s_-]?security\b",
    r"\bbank[\s_-]?account\b",
    # malware / hacking
    r"\bexploit\b", r"\bshellcode\b", r"\bransomware\b",
    r"\brat\b", r"\bkeylogger\b", r"\bbackdoor\b",
    r"\bunauthorized[\s_-]?access\b", r"\bhack(ing|ed)?\b",
    r"\bsql[\s_-]?inject\b", r"\bxss\b", r"\bremote[\s_-]?code[\s_-]?exec\b",
    r"\bvulnerabilit(y|ies)\b",
    # child safety
    r"\bchild[\s_-]?(porn|abuse|exploit)\b",
]

# ---------------------------------------------------------------------------
# Intent categories
#   triggers    — whole words or phrases that vote for the category (a plural
#                 "s" is allowed, so "report" also matches "reports")
#   absorbs     — words an operator in this category already says, so they are
#                 dropped from the keywords (site:github.com covers "github")
#   explanation — one line per operator; a line that starts with an operator
#                 the dork does not use is left out of the response
# ---------------------------------------------------------------------------
CATEGORIES = {
    "documents": {
        "triggers": [
            "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "csv",
            "document", "report", "whitepaper", "presentation", "slide",
            "spreadsheet", "excel", "manual", "guide", "ebook", "book",
            "resume", "cv",
        ],
        "absorbs": ["file", "files", "document", "documents", "book", "books"],
        "explanation": [
            "filetype: returns only files in the format you asked for, PDF if you named none",
            "intitle: requires the subject, or the words after \"titled\", in the file's title",
            "intext: requires the words after \"mentions\" or \"containing\" in the file's text",
        ],
    },
    "people": {
        "triggers": [
            "person", "people", "who is", "information about", "public info",
            "find someone", "biography",
        ],
        "absorbs": ["person", "people", "someone", "biography", "bio", "profile", "profiles"],
        "explanation": [
            "intitle: requires the name in the page title, where profile pages put it",
            "site: limits results to profile sites, joined with OR so either may match",
            "Quotes keep the name together, so first and last name are not matched apart",
        ],
    },
    "linkedin": {
        "triggers": [
            "linkedin", "professional", "job title", "analyst", "engineer",
            "manager", "director", "recruiter", "soc", "ciso", "developer",
        ],
        "absorbs": ["linkedin", "profile", "profiles", "professional", "professionals"],
        "explanation": [
            "site:linkedin.com/in limits results to public LinkedIn profiles",
            "intitle: requires the role in the profile's headline, which LinkedIn puts in the title",
            "A quoted place name narrows the profiles to one location",
        ],
    },
    "github": {
        "triggers": [
            "github", "code", "script", "repository", "repositories", "repo",
            "source code", "open source", "project",
        ],
        "absorbs": ["github", "repo", "repos", "repository", "repositories"],
        "explanation": [
            "site:github.com limits results to GitHub",
            "intitle: requires the topic in the repository's title, which carries its description",
            "inurl: in a variation matches repositories named after the topic",
        ],
    },
    "academic": {
        "triggers": [
            "research", "academic", "thesis", "dissertation", "journal",
            "arxiv", "scholar", "conference", "paper", "study", "ieee",
        ],
        "absorbs": ["arxiv"],
        "explanation": [
            "site:arxiv.org limits results to arXiv preprints",
            "filetype: returns the paper itself rather than a page about it",
            "intitle: requires the topic in the paper's title",
        ],
    },
    "directories": {
        "triggers": [
            "directory listing", "open directory", "index of", "exposed",
            "directories", "file listing", "apache", "nginx", "ftp", "public files",
        ],
        "absorbs": ["directory", "directories", "listing", "listings", "index", "folder", "folders", "open"],
        "explanation": [
            "intitle:\"index of\" matches the title Apache and Nginx give an open directory listing",
            "The other words must appear in the listing, usually as file or folder names",
            "-htm -html drops ordinary web pages so the listings are left",
        ],
    },
    "social_media": {
        "triggers": [
            "twitter", "instagram", "facebook", "tiktok", "reddit",
            "social media", "social profile", "post", "tweet",
        ],
        "absorbs": [
            "twitter", "instagram", "facebook", "tiktok", "reddit", "social", "media",
            "post", "posts", "tweet", "tweets", "account", "accounts", "profile", "profiles",
        ],
        "explanation": [
            "site: limits results to the platform you named",
            "intitle: requires the topic in the post's title, which holds its opening words",
            "inurl: in a variation matches posts whose address carries the topic",
        ],
    },
    "company": {
        "triggers": [
            "company", "organization", "organisation", "corporate",
            "business", "startup", "firm", "enterprise", "brand",
        ],
        "absorbs": [
            "company", "companies", "organization", "organisation", "corporate",
            "business", "firm", "enterprise", "brand", "startup",
        ],
        "explanation": [
            "intitle: requires the company name in the title",
            "filetype:pdf returns documents the company published",
            "The OR group accepts an annual report or a press release",
        ],
    },
    "general": {
        "triggers": [],  # fallback
        "absorbs": [],
        "explanation": [
            "intitle: requires the subject in the page title",
            "intext: requires the words after \"mentions\" or \"containing\" in the page text",
            "Other words are plain keywords, which Google may match anywhere on the page",
        ],
    },
}

# ---------------------------------------------------------------------------
# Word lists for term extraction
# ---------------------------------------------------------------------------

# Words that say how to search rather than what to search for.
STOP_WORDS = {
    "a", "an", "the", "for", "in", "on", "at", "to", "of", "and", "or", "by",
    "with", "from", "into", "inside", "about", "regarding", "concerning",
    "covering", "related", "relating",
    "find", "search", "get", "show", "me", "my", "i", "we", "our", "look",
    "looking", "locate", "please", "want", "need", "help", "using", "use",
    "give", "list", "some", "any", "all", "this", "that", "these", "those",
    "which", "who", "whose", "where", "what", "is", "are", "was", "were", "be",
    "it", "its", "their", "there", "public", "publicly", "available", "exposed",
    "online", "web", "internet", "google", "dork", "dorks", "query",
    "result", "results", "information", "info", "details",
}

# "titled X" puts X in intitle:, "mentions X" puts X in intext:.
TITLE_MARKERS = {"titled", "named", "called", "title"}
TEXT_MARKERS = {
    "mentions", "mentioning", "mention", "mentioned", "containing",
    "contains", "contain", "including", "includes", "include",
}
# Words skipped between a marker and its value: "containing the word BROU".
SLOT_FILLER = {"the", "a", "an", "word", "words", "phrase", "term", "terms", "text"}
# A run of words right after one of these is the subject: "books about <subject>".
TOPIC_MARKERS = {"about", "on", "regarding", "concerning", "covering", "for", "to"}

# Format words, read only by the categories in FORMAT_CATEGORIES.
FILETYPE_WORDS = {
    "pdf": "pdf", "pdfs": "pdf", "ebook": "pdf", "ebooks": "pdf",
    "doc": "doc", "docs": "doc", "docx": "docx",
    "ppt": "ppt", "pptx": "pptx", "presentation": "pptx", "presentations": "pptx",
    "slide": "pptx", "slides": "pptx",
    "xls": "xls", "xlsx": "xlsx", "excel": "xlsx", "spreadsheet": "xlsx", "spreadsheets": "xlsx",
    "csv": "csv", "txt": "txt",
}
FORMAT_CATEGORIES = {"documents", "academic"}
ALT_FILETYPE = {
    "pdf": "docx", "doc": "docx", "docx": "doc", "ppt": "pptx", "pptx": "ppt",
    "xls": "xlsx", "xlsx": "xls", "csv": "xlsx", "txt": "pdf",
}
RESUME_WORDS = {"resume", "resumes", "cv", "cvs"}

SOCIAL_SITES = {
    "twitter": "twitter.com",
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "tiktok": "tiktok.com",
    "reddit": "reddit.com",
}

# Google matches a quoted phrase in a title or URL word for word, so field
# values are kept to three words.
MAX_FIELD_WORDS = 3

TOKEN_RE = re.compile(r"[^\W_][\w+#.-]*")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

@dataclass
class Terms:
    """The parts of a request a builder turns into operators."""
    topic: List[str] = field(default_factory=list)   # the subject, as typed
    extras: List[str] = field(default_factory=list)  # other words worth keeping
    title: List[str] = field(default_factory=list)   # words after "titled"
    text: List[str] = field(default_factory=list)    # words after "mentions"
    location: Optional[str] = None                   # "in Ireland"
    filetype: Optional[str] = None                   # from a format word

    def subject(self) -> Tuple[List[str], List[str]]:
        """The words for intitle:, and the extras left after taking them."""
        if self.title:
            return self.title, self.topic + self.extras
        if self.topic:
            return self.topic, self.extras
        return self.extras[:MAX_FIELD_WORDS], self.extras[MAX_FIELD_WORDS:]

    def found(self) -> bool:
        return bool(self.topic or self.extras or self.title or self.text or self.location)


def _quote(phrase: str) -> str:
    """Wrap multi-word phrases in quotes; single words need no quotes."""
    return f'"{phrase}"' if " " in phrase else phrase


def _field(op: str, words: List[str]) -> str:
    """An operator with a quoted value, so Google does not swap in synonyms."""
    return f'{op}:"{" ".join(words)}"' if words else ""


def _join(*parts: str) -> str:
    return " ".join(p for p in parts if p)


def _bare(words: List[str], location: Optional[str] = None) -> List[str]:
    """Extra words as plain keywords, plus a quoted place name if there is one."""
    return words + ([f'"{location}"'] if location else [])


def _intext(t: Terms) -> str:
    return _field("intext", t.text)


def _singular(word: str) -> str:
    """Rough singular for job titles: "analysts" to "analyst"."""
    lower = word.lower()
    if len(lower) > 4 and lower.endswith("ies"):
        return word[:-3] + "y"
    if len(lower) > 3 and lower.endswith("s") and not lower.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def _singular_last(words: List[str]) -> List[str]:
    return words[:-1] + [_singular(words[-1])] if words else words


def _clean_query(text: str) -> str:
    """Lowercase and remove punctuation, keeping hyphens."""
    return re.sub(r"[^\w\s-]", "", text.lower()).strip()


def _tokenise(query: str) -> List[str]:
    """Words in the order typed, original case kept, trailing dots dropped."""
    return [t for t in (w.rstrip(".-") for w in TOKEN_RE.findall(query)) if t]


def _has_word(query_lower: str, word: str) -> bool:
    """Whole-word match, so "doc" does not fire on "docker"."""
    return re.search(rf"\b{re.escape(word)}s?\b", query_lower) is not None


def _detect_category(query_lower: str) -> Tuple[str, dict]:
    """
    Score each category by how many of its triggers appear as whole words.
    Returns the category name and its config dict. On a tie the category
    declared first in CATEGORIES wins.
    """
    scores: dict = {}
    for name, cfg in CATEGORIES.items():
        if name == "general":
            continue
        score = sum(1 for t in cfg["triggers"] if _has_word(query_lower, t))
        if score:
            scores[name] = score

    if not scores:
        return "general", CATEGORIES["general"]

    best = max(scores, key=scores.get)
    return best, CATEGORIES[best]


def _extract_terms(query: str, category: str) -> Terms:
    """
    Split the request into the parts the builders use. Words are kept in the
    order they were typed, and only words that sat next to each other in the
    request are ever grouped into one phrase.
    """
    tokens = _tokenise(query)
    lower = [t.lower() for t in tokens]
    n = len(tokens)
    absorbs = set(CATEGORIES[category].get("absorbs", []))
    reads_formats = category in FORMAT_CATEGORIES
    used = [False] * n
    terms = Terms()

    def is_content(i: int) -> bool:
        w = lower[i]
        if w in STOP_WORDS or w in absorbs or w in TITLE_MARKERS or w in TEXT_MARKERS:
            return False
        if reads_formats and w in FILETYPE_WORDS:
            return False
        return len(w) > 1 or w.isdigit()

    if reads_formats:
        terms.filetype = next((FILETYPE_WORDS[w] for w in lower if w in FILETYPE_WORDS), None)

    # "in Ireland", "in New York": capitalised words after "in".
    for i in range(n - 1):
        if lower[i] != "in":
            continue
        place = []
        j = i + 1
        while j < n and len(place) < 2 and tokens[j][0].isupper() and is_content(j):
            place.append(tokens[j])
            j += 1
        if place:
            terms.location = " ".join(place)
            for k in range(i + 1, j):
                used[k] = True
            break

    # "titled X" and "mentions X".
    for i in range(n):
        if lower[i] in TITLE_MARKERS:
            slot = terms.title
        elif lower[i] in TEXT_MARKERS:
            slot = terms.text
        else:
            continue
        if slot:
            continue
        j = i + 1
        while j < n and lower[j] in SLOT_FILLER:
            j += 1
        while j < n and len(slot) < MAX_FIELD_WORDS and not used[j] and is_content(j):
            slot.append(tokens[j])
            used[j] = True
            j += 1

    # Runs of adjacent content words.
    runs: List[Tuple[int, List[str]]] = []
    for i in range(n):
        if is_content(i) and not used[i]:
            if runs and runs[-1][0] + len(runs[-1][1]) == i:
                runs[-1][1].append(tokens[i])
            else:
                runs.append((i, [tokens[i]]))

    if runs:
        topic_run = next(
            (r for r in runs if r[0] > 0 and lower[r[0] - 1] in TOPIC_MARKERS),
            max(runs, key=lambda r: len(r[1])),
        )
        for run in runs:
            if run is topic_run:
                terms.topic = run[1][:MAX_FIELD_WORDS]
                terms.extras += run[1][MAX_FIELD_WORDS:]
            else:
                terms.extras += run[1]

    return terms


def _explain(cfg: dict, dork: str) -> List[str]:
    """Explanation lines for the operators this dork actually uses."""
    lines = []
    for line in cfg["explanation"]:
        head = line.split(" ", 1)[0]
        op = head.split(":", 1)[0] + ":" if ":" in head else None
        if op is None or op in dork:
            lines.append(line)
    return lines


def _unique(dork: str, variations: List[str]) -> List[str]:
    """Drop empty, repeated and primary-equal variations, keeping order."""
    seen = {dork}
    out = []
    for v in variations:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


# ---------------------------------------------------------------------------
# Safety checker
# ---------------------------------------------------------------------------

def is_safe_query(query: str) -> bool:
    """
    Return False if the query matches any blocked pattern.
    Uses case-insensitive regex matching for robustness.
    """
    q = query.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, q):
            return False
    return True


# ---------------------------------------------------------------------------
# Per-category dork builders
#   Each takes the extracted Terms and the cleaned query, and returns
#   (dork, variations).
# ---------------------------------------------------------------------------

def _build_document_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    ft = t.filetype or "pdf"
    title, phrase, extras = list(t.title), list(t.topic), list(t.extras)
    resume = next((w for w in extras if w.lower() in RESUME_WORDS), None)
    if not title and resume:
        # "resumes for SOC analysts": the title says resume, the body says the role.
        extras.remove(resume)
        title, phrase = [_singular(resume.lower())], _singular_last(phrase)
    elif not title:
        title, phrase = phrase, []

    body = [_intext(t), _quote(" ".join(phrase)) if phrase else "", *_bare(extras, t.location)]
    dork = _join(f"filetype:{ft}", _field("intitle", title), *body)
    anywhere = _join(
        f"filetype:{ft}",
        *(f'"{" ".join(p)}"' for p in (title, t.text, phrase) if p),
        *_bare(extras, t.location),
    )
    variations = [
        anywhere,
        _join(f"filetype:{ALT_FILETYPE.get(ft, 'pdf')}", _field("intitle", title), *body),
        _join(dork, "-site:scribd.com -site:issuu.com"),
    ]
    return dork, variations


def _build_linkedin_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    role, extras = t.subject()
    role = _singular_last(role)
    place = [f'"{t.location}"'] if t.location else []

    dork = _join("site:linkedin.com/in", _field("intitle", role), _intext(t), *place, *extras)
    variations = [
        _join("site:linkedin.com/in", f'"{" ".join(role)}"' if role else "", *place, *extras),
        _join("site:linkedin.com/in", _field("intitle", role), *extras) if place
        else _join("site:linkedin.com/in", _field("intitle", role), "(senior OR lead)", *extras),
    ]
    return dork, variations


def _build_github_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    topic, extras = t.subject()
    rest = _bare(extras, t.location)
    dork = _join("site:github.com", _field("intitle", topic), _intext(t), *rest)
    variations = [
        _join("site:github.com", _quote(" ".join(topic)), *rest),
        _join("site:github.com", "inurl:" + "-".join(w.lower() for w in topic) if topic else "", *rest),
        _join("site:gitlab.com", _field("intitle", topic), *rest),
    ]
    return dork, variations


def _build_academic_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    topic, extras = t.subject()
    # A paper rarely says "papers", but almost every one says "paper".
    rest = _bare(["paper" if w.lower() == "papers" else w for w in extras], t.location)
    ft = t.filetype or "pdf"
    on_arxiv = _has_word(query_lower, "arxiv")
    scope = "site:arxiv.org" if on_arxiv else f"filetype:{ft}"

    dork = _join(scope, _field("intitle", topic), _intext(t), *rest)
    variations = [
        _join(f"filetype:{ft}", _field("intitle", topic), "site:edu", *rest) if on_arxiv
        else _join("site:arxiv.org", _field("intitle", topic), *rest),
        _join(f"filetype:{ft}", _quote(" ".join(topic)), "abstract", *rest),
        _join("site:researchgate.net", _field("intitle", topic), *rest),
    ]
    return dork, variations


def _build_directory_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    topic, extras = t.subject()
    # File and folder names rarely sit side by side, so nothing here is quoted.
    words = _bare(t.title + t.text + topic + extras, t.location) or ["logs"]
    dork = _join('intitle:"index of"', *words, "-htm -html")
    variations = [
        _join('intitle:"index of" "parent directory"', *words),
        _join('intitle:"index of"', "inurl:" + words[0].lower(), *words[1:]),
    ]
    return dork, variations


def _build_social_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    platform = next(
        (v for k, v in SOCIAL_SITES.items() if _has_word(query_lower, k)), "twitter.com"
    )
    topic, extras = t.subject()
    rest = _bare(extras, t.location)
    dork = _join(f"site:{platform}", _field("intitle", topic), _intext(t), *rest)
    alternative = (
        _join("site:x.com", _field("intitle", topic), *rest) if platform == "twitter.com"
        else _join(f"site:{platform}", "inurl:" + "-".join(w.lower() for w in topic) if topic else "", *rest)
    )
    variations = [
        _join(f"site:{platform}", _quote(" ".join(topic)), *rest),
        alternative,
    ]
    return dork, variations


def _build_people_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    name, extras = t.subject()
    rest = _bare(extras, t.location)
    quoted = f'"{" ".join(name)}"' if name else ""
    dork = _join(_field("intitle", name), "(site:linkedin.com/in OR site:about.me)", _intext(t), *rest)
    variations = [
        _join(quoted, '(biography OR "about me" OR profile)', *rest),
        _join(quoted, "filetype:pdf (resume OR cv)", *rest),
        _join(quoted, "site:linkedin.com OR site:twitter.com", *rest),
    ]
    return dork, variations


def _build_company_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    company, extras = t.subject()
    rest = _bare(extras, t.location)
    quoted = f'"{" ".join(company)}"' if company else ""
    dork = _join(_field("intitle", company), 'filetype:pdf ("annual report" OR "press release")', *rest)
    variations = [
        _join(quoted, "inurl:about", *rest),
        _join(_field("intitle", company), "(careers OR jobs)", *rest),
        _join(quoted, "filetype:pdf", *rest),
    ]
    return dork, variations


def _build_general_dork(t: Terms, query_lower: str) -> Tuple[str, List[str]]:
    topic, extras = t.subject()
    rest = _bare(extras, t.location)
    dork = _join(_field("intitle", topic), _intext(t), *rest)
    variations = [
        _join(_quote(" ".join(topic)), _intext(t), *rest),
        _join(_field("intext", topic), *rest),
        _join(_quote(" ".join(topic)), "(site:edu OR site:gov)", *rest),
    ]
    return dork, variations


# ---------------------------------------------------------------------------
# Main DorkGenerator class
# ---------------------------------------------------------------------------

class DorkGenerator:
    """
    Rule-based Google dork generator.

    This class is designed to be easily extended:
      - Override `generate()` to plug in an LLM (Gemini, OpenAI, Claude)
      - Add new entries to CATEGORIES for new intent types
      - Extend BLOCKED_PATTERNS for tighter safety controls
    """

    def generate(self, query: str) -> dict:
        """
        Generate a Google dork from a natural language query.

        Parameters
        ----------
        query : str
            The user's plain English request.

        Returns
        -------
        dict
            Keys: dork, explanation, variations, category
            OR:   error (if query is refused)
        """
        # 1. Safety check
        if not is_safe_query(query):
            return {"error": "Unsafe or disallowed query."}

        # 2. Normalise and classify
        query_lower = _clean_query(query)
        category, cfg = _detect_category(query_lower)
        terms = _extract_terms(query, category)

        if not terms.found():
            return {"error": "Could not extract meaningful keywords from your query."}

        # 3. Route to per-category builder
        builder_map = {
            "documents": _build_document_dork,
            "linkedin": _build_linkedin_dork,
            "github": _build_github_dork,
            "academic": _build_academic_dork,
            "directories": _build_directory_dork,
            "social_media": _build_social_dork,
            "people": _build_people_dork,
            "company": _build_company_dork,
            "general": _build_general_dork,
        }

        build_fn = builder_map.get(category, builder_map["general"])
        dork, variations = build_fn(terms, query_lower)
        variations = _unique(dork, variations)

        # 4. Real-time validation
        warnings = []
        is_valid = True

        # Check word limit (Google limit is approx 32 words)
        word_count = len(dork.split())
        if word_count > 32:
            warnings.append(f"Query is very long ({word_count} words). Google may ignore terms beyond the 32nd word.")
            is_valid = False

        # Check for deprecated or sensitive operators
        if "link:" in dork:
            warnings.append("The 'link:' operator is largely deprecated and may not return accurate results.")
        if "info:" in dork:
            warnings.append("The 'info:' operator is deprecated.")
        if "inanchor:" in dork:
            warnings.append("The 'inanchor:' operator is often unreliable in modern Google searches.")

        # Check for potentially heavy queries
        if dork.count("OR") > 10:
            warnings.append("High number of OR operators detected. This may trigger a CAPTCHA.")

        return {
            "dork": dork,
            "explanation": _explain(cfg, dork),
            "variations": variations,
            "category": category,
            "warnings": warnings,
            "is_valid": is_valid,
        }
