/**
 * DorkCraft: search effectiveness estimate
 * ----------------------------------------
 * Scores a generated dork against a fixed list of checks. Everything here is
 * derived from the dork's text and the user's request. Nothing is sent to
 * Google, so the score is an estimate of how well the query is built, not a
 * measured result count.
 */

export type Dimension = 'targeting' | 'reach' | 'coverage';
export type Impact = 'high' | 'medium' | 'low';
export type Level = 'strong' | 'fair' | 'weak';

export interface Check {
  id: string;
  dimension: Dimension;
  title: string;
  impact: Impact;
  passed: boolean;
  detail: string;
}

export interface Effectiveness {
  score: number;
  level: Level;
  label: string;
  summary: string;
  passed: number;
  total: number;
  checks: Check[];
}

export const DIMENSIONS: { id: Dimension; label: string }[] = [
  { id: 'targeting', label: 'Targeting' },
  { id: 'reach', label: 'Reach' },
  { id: 'coverage', label: 'Coverage' },
];

export const LEVEL_LABEL: Record<Level, string> = {
  strong: 'Strong',
  fair: 'Fair',
  weak: 'Weak',
};

const WEIGHT: Record<Impact, number> = { high: 4, medium: 2, low: 1 };

/** Phrases longer than this rarely match word for word. */
const MAX_FIELD_PHRASE_WORDS = 3;
const MAX_FREE_PHRASE_WORDS = 5;
/** Google ignores terms past the 32nd word. */
const MAX_QUERY_WORDS = 32;
const MAX_RESTRICTIONS = 5;

const OPERATORS = [
  'site', 'filetype', 'ext', 'intitle', 'allintitle', 'inurl', 'allinurl',
  'intext', 'allintext', 'before', 'after', 'related', 'cache', 'link',
  'info', 'inanchor',
];
const SCOPE_OPS = ['site', 'filetype', 'ext'];
const FIELD_OPS = ['intitle', 'allintitle', 'inurl', 'allinurl', 'intext', 'allintext'];

/** Where each field operator looks, for messages. */
const FIELD_PLACE: Record<string, string> = {
  intitle: 'title', allintitle: 'title',
  inurl: 'URL', allinurl: 'URL',
  intext: 'body text', allintext: 'body text',
};

/** Operators Google has retired, with what happened to each. */
const RETIRED: Record<string, string> = {
  cache: 'cache: was switched off by Google in 2024',
  link: 'link: stopped returning reliable results in 2017',
  info: 'info: was removed in 2017',
};

/** Words in the request that say how to search, not what to search for. */
const STOP_WORDS = new Set([
  'a', 'an', 'the', 'of', 'in', 'on', 'at', 'for', 'to', 'with', 'and', 'or',
  'about', 'from', 'by', 'some', 'any', 'this', 'that', 'these', 'those',
  'is', 'are', 'be', 'it', 'its', 'me', 'my', 'i', 'all', 'part', 'parts',
  'their', 'has', 'have', 'as', 'where', 'which', 'who', 'into', 'inside',
  'contain', 'contains', 'containing', 'mention', 'mentions', 'mentioning',
  'related', 'regarding', 'named', 'called', 'find', 'search', 'show', 'get',
  'give', 'list', 'look', 'looking', 'locate', 'want', 'need', 'please',
  'public', 'publicly', 'available', 'exposed', 'open',
  'file', 'files', 'document', 'documents', 'pdf', 'pdfs', 'doc', 'docs',
  'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'csv', 'txt', 'title', 'titled',
  'titles', 'text', 'body', 'url', 'urls', 'page', 'pages', 'site', 'sites',
  'website', 'websites', 'book', 'books', 'ebook', 'ebooks', 'profile',
  'profiles', 'repo', 'repos', 'repository', 'repositories', 'presentation',
  'presentations', 'slide', 'slides', 'directory', 'directories', 'listing',
  'listings', 'result', 'results',
]);

interface Phrase {
  text: string;
  words: string[];
  /** Operator the phrase is attached to, e.g. intitle, or null for a free phrase. */
  field: string | null;
}

interface Parsed {
  ops: { name: string; value: string; negated: boolean }[];
  phrases: Phrase[];
  /** Words the dork asks Google to match: phrases, field values and bare words. */
  keywords: string[];
  wordCount: number;
  restrictions: number;
}

const words = (text: string): string[] =>
  text.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];

const stem = (word: string): string => {
  if (word.length > 4 && word.endsWith('ies')) return word.slice(0, -3) + 'y';
  if (word.length > 4 && word.endsWith('es')) return word.slice(0, -2);
  if (word.length > 3 && word.endsWith('s')) return word.slice(0, -1);
  return word;
};

const quoteList = (items: string[]): string => items.map((w) => '"' + w + '"').join(', ');
const plural = (n: number, one: string, many: string): string => (n === 1 ? one : many);

function parse(dork: string): Parsed {
  const opRe = new RegExp('(-?)\\b(' + OPERATORS.join('|') + '):("[^"]*"|\\S+)?', 'gi');
  const ops: Parsed['ops'] = [];
  const phrases: Phrase[] = [];
  const keywords: string[] = [];

  let rest = dork.replace(opRe, (_m, neg: string, name: string, raw: string = '') => {
    const op = name.toLowerCase();
    const quoted = raw.startsWith('"');
    const value = raw.replace(/^"|"$/g, '');
    ops.push({ name: op, value, negated: neg === '-' });
    if (FIELD_OPS.includes(op) && neg !== '-') {
      keywords.push(...words(value));
      if (quoted) phrases.push({ text: value, words: words(value), field: op });
    }
    return ' ';
  });

  rest = rest.replace(/(-?)"([^"]*)"/g, (_m, neg: string, text: string) => {
    if (neg !== '-') {
      phrases.push({ text, words: words(text), field: null });
      keywords.push(...words(text));
    }
    return ' ';
  });

  for (const token of rest.split(/\s+/)) {
    if (!token || token.startsWith('-') || /^(OR|AND|\|)$/.test(token)) continue;
    keywords.push(...words(token));
  }

  const positiveOps = ops.filter((o) => !o.negated);
  const freePhrases = phrases.filter((p) => p.field === null).length;
  return {
    ops,
    phrases,
    keywords,
    wordCount: dork.trim().split(/\s+/).filter(Boolean).length,
    restrictions: positiveOps.length + freePhrases,
  };
}

/** Keywords that only repeat what an operator in the same dork already says. */
function redundantWords(parsed: Parsed): string[] {
  const redundant = new Set<string>();
  const add = (...list: string[]) => list.forEach((w) => redundant.add(w));
  const has = (...names: string[]) =>
    parsed.ops.some((o) => !o.negated && names.includes(o.name));

  if (has('filetype', 'ext')) {
    add('file', 'files', 'document', 'documents', 'book', 'books', 'ebook', 'ebooks');
    parsed.ops
      .filter((o) => o.name === 'filetype' || o.name === 'ext')
      .forEach((o) => words(o.value).forEach((w) => add(w, w + 's')));
  }
  if (has('intitle', 'allintitle')) add('title', 'titled', 'titles');
  if (has('intext', 'allintext')) add('text', 'body');
  if (has('inurl', 'allinurl')) add('url', 'urls');

  for (const op of parsed.ops) {
    if (op.name !== 'site' || op.negated) continue;
    add('site', 'website');
    const host = op.value.toLowerCase().replace(/^\./, '').split('/')[0];
    const labels = host.split('.');
    const name = labels.length > 1 ? labels[labels.length - 2] : '';
    if (name.length > 2) add(name);
    if (name === 'linkedin') add('profile', 'profiles');
    if (name === 'github') add('repo', 'repos', 'repository', 'repositories');
  }

  return [...new Set(parsed.keywords.filter((w) => redundant.has(w)))];
}

/** Terms from the request that the dork no longer contains in any form. */
function missingTerms(query: string, dork: string): string[] {
  const haystack = dork.toLowerCase();
  const wanted = [...new Set(words(query))].filter((w) => w.length > 1 && !STOP_WORDS.has(w));
  return wanted.filter((w) => !haystack.includes(w) && !haystack.includes(stem(w)));
}

/**
 * Quoted phrases built from words that were apart in the request. A phrase
 * with a word the request never used (a template such as "index of") is left
 * alone: it was chosen on purpose, not stitched together.
 */
function stitchedPhrases(query: string, phrases: Phrase[]): Phrase[] {
  const asked = words(query);
  return phrases.filter((p) => {
    if (p.words.length < 2 || !p.words.every((w) => asked.includes(w))) return false;
    for (let i = 0; i + p.words.length <= asked.length; i++) {
      if (p.words.every((w, j) => asked[i + j] === w)) return false;
    }
    return true;
  });
}

/** Operator values written as a|b, which Google does not read as a list. */
function pipedValues(parsed: Parsed): string[] {
  return parsed.ops
    .filter((o) => (o.name === 'filetype' || o.name === 'ext' || o.name === 'site') && o.value.includes('|'))
    .map((o) => o.name + ':' + o.value);
}

export function assessDork(query: string, dork: string): Effectiveness {
  const parsed = parse(dork);
  const positive = parsed.ops.filter((o) => !o.negated);
  const usedNames = (names: string[]) =>
    [...new Set(positive.filter((o) => names.includes(o.name)).map((o) => o.name + ':'))];

  const scopeOps = usedNames(SCOPE_OPS);
  const fieldOps = usedNames(FIELD_OPS);
  const tooLong = parsed.phrases.filter(
    (p) => p.words.length > (p.field ? MAX_FIELD_PHRASE_WORDS : MAX_FREE_PHRASE_WORDS),
  );
  const redundant = redundantWords(parsed);
  const retired = [...new Set(parsed.ops.map((o) => o.name).filter((n) => n in RETIRED))];
  const piped = pipedValues(parsed);
  const stitched = stitchedPhrases(query, parsed.phrases);
  const missing = missingTerms(query, dork);
  const overWords = parsed.wordCount > MAX_QUERY_WORDS;
  const overOps = parsed.restrictions > MAX_RESTRICTIONS;
  const longest = parsed.phrases.reduce((max, p) => Math.max(max, p.words.length), 0);

  let phraseDetail = 'No exact phrase that could fail to match.';
  if (tooLong.length) {
    const p = tooLong[0];
    const where = p.field ? ' in the ' + FIELD_PLACE[p.field] : '';
    phraseDetail =
      '"' + p.text + '" is ' + p.words.length + ' words. Few pages carry that exact wording' +
      where + '. Trim it to 2 or 3 words, or split it.';
  } else if (longest) {
    phraseDetail = 'The longest exact phrase is ' + longest + ' ' + plural(longest, 'word', 'words') + '.';
  }

  const syntaxProblems = retired.map((n) => RETIRED[n]);
  if (piped.length) {
    const first = piped[0];
    const [name, value] = [first.slice(0, first.indexOf(':')), first.slice(first.indexOf(':') + 1)];
    const parts = value.split('|');
    syntaxProblems.push(
      'Google reads | as OR between whole terms, so ' + first + ' means ' + name + ':' + parts[0] +
      ' or the plain word ' + parts[1] + '. Write ' + parts.map((v) => name + ':' + v).join(' OR ') + ' instead',
    );
  }

  let constraintDetail =
    parsed.restrictions + ' ' + plural(parsed.restrictions, 'restriction', 'restrictions') +
    ' across ' + parsed.wordCount + ' ' + plural(parsed.wordCount, 'word', 'words') + '.';
  if (overWords) {
    constraintDetail = parsed.wordCount + ' words. Google ignores everything after the 32nd.';
  } else if (overOps) {
    constraintDetail =
      parsed.restrictions + ' restrictions at once. Every one must match on the same page, so results dry up quickly.';
  }

  const checks: Check[] = [
    {
      id: 'scope',
      dimension: 'targeting',
      title: 'Scoped to a site or file type',
      impact: 'high',
      passed: scopeOps.length > 0,
      detail: scopeOps.length
        ? scopeOps.join(' and ') + ' ' + plural(scopeOps.length, 'cuts', 'cut') + ' the search down to one kind of result.'
        : 'No site: or filetype: operator, so Google searches the whole web. Add one to cut the noise.',
    },
    {
      id: 'field',
      dimension: 'targeting',
      title: 'Keyword pinned to a part of the page',
      impact: 'medium',
      passed: fieldOps.length > 0,
      detail: fieldOps.length
        ? fieldOps.join(' and ') + ' ' + plural(fieldOps.length, 'says', 'say') + ' where on the page the keyword must appear.'
        : 'No intitle:, inurl: or intext:, so the keyword can match anywhere on the page.',
    },
    {
      id: 'phrase',
      dimension: 'targeting',
      title: 'Exact phrase in quotes',
      impact: 'low',
      passed: parsed.phrases.length > 0,
      detail: parsed.phrases.length
        ? 'Quotes stop Google from reordering the words or swapping in synonyms.'
        : 'Nothing is quoted, so Google may reorder the words or swap in synonyms.',
    },
    {
      id: 'phrase-length',
      dimension: 'reach',
      title: 'Phrases short enough to match',
      impact: 'medium',
      passed: tooLong.length === 0,
      detail: phraseDetail,
    },
    {
      id: 'stitched',
      dimension: 'reach',
      title: 'Phrases read the way you wrote them',
      impact: 'high',
      passed: stitched.length === 0,
      detail: stitched.length
        ? '"' + stitched[0].text + '" joins words that were apart in your request. In quotes they must sit side by side on the page, which is rare.'
        : parsed.phrases.length
          ? 'No quoted phrase joins words that were apart in your request.'
          : 'No quoted phrase to check.',
    },
    {
      id: 'redundant',
      dimension: 'reach',
      title: 'No keyword repeats an operator',
      impact: 'high',
      passed: redundant.length === 0,
      detail: redundant.length
        ? quoteList(redundant) + ' ' + plural(redundant.length, 'repeats', 'repeat') +
          ' what an operator already says. Left in as ' + plural(redundant.length, 'a keyword', 'keywords') +
          ', ' + plural(redundant.length, 'it has', 'they have') + ' to appear on the page too, which filters out good results.'
        : 'Every keyword adds something the operators do not already cover.',
    },
    {
      id: 'syntax',
      dimension: 'reach',
      title: 'Syntax Google accepts',
      impact: 'medium',
      passed: syntaxProblems.length === 0,
      detail: syntaxProblems.length
        ? syntaxProblems.join('; ') + '.'
        : 'No retired operators or malformed values.',
    },
    {
      id: 'constraints',
      dimension: 'reach',
      title: 'Not over-constrained',
      impact: 'low',
      passed: !overWords && !overOps,
      detail: constraintDetail,
    },
    {
      id: 'terms',
      dimension: 'coverage',
      title: 'Keeps the terms you asked for',
      impact: 'high',
      passed: missing.length === 0,
      detail: missing.length
        ? 'Missing from the dork: ' + quoteList(missing) + '. Add ' + plural(missing.length, 'it', 'them') +
          ' by hand or rephrase the request.'
        : 'Every key term from your request is in the dork.',
    },
    {
      id: 'keywords',
      dimension: 'coverage',
      title: 'Has a keyword to match',
      impact: 'medium',
      passed: parsed.keywords.length > 0,
      detail: parsed.keywords.length
        ? parsed.keywords.length + ' ' + plural(parsed.keywords.length, 'keyword', 'keywords') + ' for Google to match.'
        : 'Operators only. Without a keyword the search returns everything in scope.',
    },
  ];

  const total = checks.reduce((sum, c) => sum + WEIGHT[c.impact], 0);
  const earned = checks.reduce((sum, c) => sum + (c.passed ? WEIGHT[c.impact] : 0), 0);
  const score = Math.round((earned / total) * 100);
  const failed = checks.filter((c) => !c.passed);
  const highFailed = failed.some((c) => c.impact === 'high');

  // A query with a high-impact failure is never called strong, whatever the total.
  const level: Level = score < 60 ? 'weak' : score >= 80 && !highFailed ? 'strong' : 'fair';

  const n = failed.length;
  let summary = 'Every check passed.';
  if (n > 0 && level === 'strong') {
    summary = 'Well built. ' + n + ' minor ' + plural(n, 'check', 'checks') + ' to look at.';
  } else if (level === 'fair') {
    summary = 'Should return results, but ' + n + ' ' + plural(n, 'check', 'checks') + ' could cost you some.';
  } else if (level === 'weak') {
    summary = 'Likely to miss. Fix the ' + n + ' failed ' + plural(n, 'check', 'checks') + ' first.';
  }

  return {
    score,
    level,
    label: LEVEL_LABEL[level],
    summary,
    passed: checks.length - n,
    total: checks.length,
    checks,
  };
}
