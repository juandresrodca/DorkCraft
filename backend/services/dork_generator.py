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
  3. Keyword extract — pull meaningful terms
  4. Operator map  — build the dork from operator templates
  5. Variations    — produce 2-3 alternative phrasings
"""

import re
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
# Intent categories with keyword triggers and operator templates
# ---------------------------------------------------------------------------
CATEGORIES = {
    "documents": {
        "triggers": [
            "pdf", "document", "doc", "report", "paper", "whitepaper",
            "presentation", "slide", "pptx", "xlsx", "spreadsheet",
            "manual", "guide", "ebook", "book"
        ],
        "filetype_map": {
            "pdf": "pdf",
            "doc": "doc",
            "docx": "docx",
            "ppt": "ppt",
            "pptx": "pptx",
            "xls": "xls",
            "xlsx": "xlsx",
            "presentation": "ppt|pptx",
            "book": "pdf",
            "ebook": "pdf",
            "manual": "pdf",
            "whitepaper": "pdf",
        },
        "explanation": [
            "filetype: restricts results to specific file formats",
            "intitle: ensures the topic appears in the page title",
            "Combining filetype + intitle gives precise document discovery",
        ],
    },
    "people": {
        "triggers": [
            "person", "people", "profile", "who is", "information about",
            "public info", "find person", "find someone", "biography"
        ],
        "explanation": [
            'site: targets specific platforms for people-search',
            'intext: scans the page body for the name',
            'intitle: further filters pages where the name appears in headings',
        ],
    },
    "linkedin": {
        "triggers": [
            "linkedin", "professional", "resume", "cv", "job title",
            "analyst", "engineer", "manager", "director", "recruiter",
            "soc", "ciso", "developer"
        ],
        "explanation": [
            'site:linkedin.com/in restricts to LinkedIn public profiles',
            'intitle: finds profiles with the role in the page title',
            'Adding a location narrows results geographically',
        ],
    },
    "github": {
        "triggers": [
            "github", "code", "script", "repository", "repo", "source code",
            "open source", "project"
        ],
        "explanation": [
            'site:github.com scopes results to GitHub',
            'intitle: narrows to repository pages with the topic in the title',
            '"language:" in GitHub search syntax can further filter by code type',
        ],
    },
    "academic": {
        "triggers": [
            "research", "academic", "thesis", "dissertation", "journal",
            "arxiv", "scholar", "conference", "paper", "study", "ieee"
        ],
        "explanation": [
            'site:arxiv.org or site:scholar.google.com targets academic databases',
            'filetype:pdf retrieves the actual paper documents',
            'intitle: scopes results to relevant topics',
        ],
    },
    "directories": {
        "triggers": [
            "directory listing", "open directory", "index of", "exposed",
            "file listing", "apache", "nginx", "ftp", "public files"
        ],
        "explanation": [
            '"Index of /" is the classic Apache/Nginx open-directory signature',
            'intitle: combined with "index of" surfaces exposed file trees',
            '-htm -html excludes regular web pages to surface raw directories',
        ],
    },
    "social_media": {
        "triggers": [
            "twitter", "instagram", "facebook", "tiktok", "reddit",
            "social media", "social profile", "post", "tweet"
        ],
        "explanation": [
            'site: targets the exact social platform',
            'inurl: can further scope to a user path (e.g., /user/)',
            'Adding keywords finds public content about specific topics',
        ],
    },
    "company": {
        "triggers": [
            "company", "organization", "organisation", "corporate",
            "business", "startup", "firm", "enterprise", "brand"
        ],
        "explanation": [
            'site: narrows results to official company domains',
            'intitle: picks up company names from page headings',
            'filetype:pdf finds annual reports and press releases',
        ],
    },
    "general": {
        "triggers": [],  # fallback
        "explanation": [
            'intitle: filters pages where all keywords appear in the heading',
            'Quoting phrases with "" forces exact-match on multi-word terms',
            'Adding site: can scope to a trusted source type',
        ],
    },
}

# ---------------------------------------------------------------------------
# Stop-words to strip before keyword extraction
# ---------------------------------------------------------------------------
STOP_WORDS = {
    "a", "an", "the", "for", "in", "on", "at", "to", "of", "and", "or",
    "find", "search", "get", "show", "me", "public", "look", "please",
    "information", "info", "about", "related", "with", "from", "some",
    "any", "all", "give", "want", "need", "help", "using", "use",
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _quote(phrase: str) -> str:
    """Wrap multi-word phrases in quotes; single words need no quotes."""
    return f'"{phrase}"' if " " in phrase else phrase


def _clean_query(text: str) -> str:
    """Lowercase and remove punctuation, keeping hyphens."""
    return re.sub(r"[^\w\s-]", "", text.lower()).strip()


def _extract_keywords(text: str, stop_words: set = STOP_WORDS) -> List[str]:
    """
    Remove stop-words and short tokens, return meaningful keywords.
    Preserves multi-word collocations where possible.
    """
    words = _clean_query(text).split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords


def _detect_category(query_lower: str) -> Tuple[str, dict]:
    """
    Walk through CATEGORIES and score each by trigger matches.
    Returns the category name and its config dict.
    """
    scores: dict[str, int] = {}
    for name, cfg in CATEGORIES.items():
        if name == "general":
            continue
        score = sum(1 for t in cfg["triggers"] if t in query_lower)
        if score:
            scores[name] = score

    if not scores:
        return "general", CATEGORIES["general"]

    best = max(scores, key=scores.get)
    return best, CATEGORIES[best]


def _detect_location(query: str) -> Optional[str]:
    """
    Naive location extractor — looks for 'in <place>' pattern.
    A real AI service would do proper NER; this handles the common case.
    """
    match = re.search(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", query)
    if match:
        return match.group(1)
    return None


def _detect_filetype(query_lower: str, filetype_map: dict) -> Optional[str]:
    """Return the first matching filetype keyword, if any."""
    for keyword, ft in filetype_map.items():
        if keyword in query_lower:
            return ft
    return None


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
# ---------------------------------------------------------------------------

def _build_document_dork(keywords: List[str], cfg: dict, query_lower: str) -> Tuple[str, List[str]]:
    filetype = _detect_filetype(query_lower, cfg.get("filetype_map", {})) or "pdf"
    topic = " ".join(keywords[:4])
    dork = f'filetype:{filetype} intitle:{_quote(topic)}'
    variations = [
        f'filetype:{filetype} {_quote(topic)}',
        f'inurl:{filetype} {_quote(topic)} -site:scribd.com',
        f'filetype:{filetype} "{keywords[0]}" site:edu' if keywords else dork,
    ]
    return dork, variations


def _build_linkedin_dork(keywords: List[str], query: str) -> Tuple[str, List[str]]:
    # Strip generic trigger words to isolate the role
    role_words = [k for k in keywords if k not in {"linkedin", "profile", "resume", "cv"}]
    role = " ".join(role_words[:3])
    location = _detect_location(query)

    dork = f'site:linkedin.com/in intitle:{_quote(role)}'
    if location:
        dork += f' "{location}"'

    variations = [
        f'site:linkedin.com intitle:{_quote(role)}',
        f'site:linkedin.com/in "{role}"',
    ]
    if location:
        variations.append(f'site:linkedin.com/in "{role}" "{location}"')

    return dork, variations


def _build_github_dork(keywords: List[str]) -> Tuple[str, List[str]]:
    topic = " ".join(keywords[:3])
    dork = f'site:github.com intitle:{_quote(topic)}'
    variations = [
        f'site:github.com "{topic}"',
        f'site:github.com inurl:/{keywords[0]}' if keywords else dork,
    ]
    return dork, variations


def _build_academic_dork(keywords: List[str], query_lower: str) -> Tuple[str, List[str]]:
    topic = " ".join(keywords[:4])
    target = "arxiv.org" if "arxiv" in query_lower else "scholar.google.com"
    dork = f'site:{target} {_quote(topic)}'
    variations = [
        f'filetype:pdf {_quote(topic)} site:edu',
        f'intitle:{_quote(topic)} filetype:pdf',
        f'"{topic}" inurl:pdf',
    ]
    return dork, variations


def _build_directory_dork(keywords: List[str]) -> Tuple[str, List[str]]:
    topic = " ".join(keywords[:2]) if keywords else "logs"
    dork = f'intitle:"index of" {_quote(topic)} -htm -html'
    variations = [
        f'"Index of /" {_quote(topic)}',
        f'intitle:"index of" inurl:{keywords[0]}' if keywords else dork,
    ]
    return dork, variations


def _build_social_dork(keywords: List[str], query_lower: str) -> Tuple[str, List[str]]:
    platforms = {
        "twitter": "twitter.com",
        "instagram": "instagram.com",
        "facebook": "facebook.com",
        "tiktok": "tiktok.com",
        "reddit": "reddit.com",
    }
    platform_site = next(
        (v for k, v in platforms.items() if k in query_lower), "twitter.com"
    )
    role_words = [k for k in keywords if k not in set(platforms.keys())]
    topic = " ".join(role_words[:3])
    dork = f'site:{platform_site} {_quote(topic)}'
    variations = [
        f'site:{platform_site} intitle:{_quote(topic)}',
        f'site:{platform_site} inurl:/{role_words[0]}' if role_words else dork,
    ]
    return dork, variations


def _build_people_dork(keywords: List[str]) -> Tuple[str, List[str]]:
    name = " ".join(keywords[:3])
    dork = f'intitle:{_quote(name)} intext:{_quote(name)}'
    variations = [
        f'"{name}" site:about.me',
        f'"{name}" (resume OR biography OR profile)',
        f'"{name}" site:linkedin.com OR site:twitter.com',
    ]
    return dork, variations


def _build_company_dork(keywords: List[str]) -> Tuple[str, List[str]]:
    company = " ".join(keywords[:2])
    dork = f'intitle:{_quote(company)} (annual report OR press release OR careers)'
    variations = [
        f'site:{keywords[0].lower()}.com' if keywords else dork,
        f'"{company}" filetype:pdf',
        f'intitle:{_quote(company)} inurl:about',
    ]
    return dork, variations


def _build_general_dork(keywords: List[str]) -> Tuple[str, List[str]]:
    topic = " ".join(keywords[:4])
    dork = f'intitle:{_quote(topic)}'
    variations = [
        f'{_quote(topic)}',
        f'intext:{_quote(topic)}',
        f'{_quote(topic)} site:edu OR site:gov',
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
        keywords = _extract_keywords(query)

        if not keywords:
            return {"error": "Could not extract meaningful keywords from your query."}

        # 3. Route to per-category builder
        builder_map = {
            "documents": lambda: _build_document_dork(keywords, cfg, query_lower),
            "linkedin": lambda: _build_linkedin_dork(keywords, query),
            "github": lambda: _build_github_dork(keywords),
            "academic": lambda: _build_academic_dork(keywords, query_lower),
            "directories": lambda: _build_directory_dork(keywords),
            "social_media": lambda: _build_social_dork(keywords, query_lower),
            "people": lambda: _build_people_dork(keywords),
            "company": lambda: _build_company_dork(keywords),
            "general": lambda: _build_general_dork(keywords),
        }

        build_fn = builder_map.get(category, builder_map["general"])
        dork, variations = build_fn()

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
            "explanation": cfg["explanation"],
            "variations": variations,
            "category": category,
            "warnings": warnings,
            "is_valid": is_valid,
        }
