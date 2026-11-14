/**
 * DorkCraft client script
 * -----------------------
 * Handles: form submission, API calls, copy, share, export, the effectiveness
 * panel, the common-dorks list, saved history, cheat-sheet toggle, chip clicks.
 */

import { API_BASE_URL, type DorkResponse } from '../lib/api';
import { assessDork, DIMENSIONS, type Check, type Effectiveness } from '../lib/effectiveness';
import {
  buildMarkdown,
  clearHistory,
  formatTimestamp,
  loadHistory,
  saveEntry,
  type HistoryEntry,
} from '../lib/history';

const $ = <T extends HTMLElement = HTMLElement>(id: string): T =>
  document.getElementById(id) as T;

// ── DOM refs ──────────────────────────────────────────────────────────
const input = $<HTMLTextAreaElement>('dc-query-input');
const generateBtn = $<HTMLButtonElement>('dc-generate-btn');
const charCount = $('dc-char-count');
const resultCard = $('dc-result-card');
const errorCard = $('dc-error-card');
const errorMsg = $('dc-error-message');
const wakeNotice = $('dc-wake-notice');
const dorkOutput = $('dc-dork-output');
const badge = $('dc-category-badge');
const explList = $('dc-explanation-list');
const varList = $('dc-variations-list');
const copyBtn = $('dc-copy-btn');
const openBtn = $('dc-open-btn');
const saveBtn = $<HTMLButtonElement>('dc-save-btn');
const exportBtn = $('dc-export-btn');
const shareBtn = $('dc-share-btn');
const cheatToggle = $('dc-cheat-toggle');
const cheatBody = $('dc-cheat-body');
const chips = document.querySelectorAll<HTMLElement>('.dc-chip');

const validIndicator = $('dc-valid-indicator');
const warningsBox = $('dc-warnings-box');
const warningsList = $('dc-warnings-list');

const effPanel = $('dc-eff');
const effCount = $('dc-eff-count');
const effScore = $('dc-eff-score');
const effRingValue = document.getElementById('dc-eff-ring-value') as unknown as SVGCircleElement;
const effHeadline = $('dc-eff-headline');
const effSub = $('dc-eff-sub');
const effBar = $('dc-eff-bar');
const effBarLabel = $('dc-eff-bar-label');
const effBarMax = $('dc-eff-bar-max');
const effGroups = $('dc-eff-groups');

const histList = $('dc-history-list');
const histCount = $('dc-hist-count');
const histEmpty = $('dc-hist-empty');
const histActions = $('dc-hist-actions');
const histDownload = $('dc-hist-download');
const histClear = $('dc-clear-history');

const commonList = document.querySelector<HTMLElement>('.dc-common__list');
const commonNoteName = $('dc-common-note-name');
const commonNoteText = $('dc-common-note-text');

/** The last successful API result, kept for save/export/share. */
let currentResult: DorkResponse | null = null;
let currentQuery = '';
let currentAssessment: Effectiveness | null = null;

const GENERATE_LABEL = generateBtn.innerHTML;
const SAVE_LABEL = saveBtn.innerHTML;
const RING_LENGTH = 2 * Math.PI * 42;

// ── Utilities ─────────────────────────────────────────────────────────
function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className = '',
  text = '',
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function download(filename: string, text: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Swaps an element's content for a short confirmation, then puts it back. */
function flash(target: HTMLElement, message: string, ms = 1600): void {
  if (target.dataset.flashing) return;
  const original = target.innerHTML;
  target.dataset.flashing = '1';
  target.textContent = message;
  setTimeout(() => {
    target.innerHTML = original;
    delete target.dataset.flashing;
  }, ms);
}

async function copyText(text: string, feedbackEl?: HTMLElement | null): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // Fallback for older browsers and non-HTTPS pages
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }
  if (feedbackEl) flash(feedbackEl, 'Copied');
}

// ── Search input ──────────────────────────────────────────────────────
input.addEventListener('input', () => {
  charCount.textContent = input.value.length + ' / 500 characters';
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 160) + 'px';
});

// Ctrl/Cmd+Enter to generate
input.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    handleGenerate();
  }
});

chips.forEach((chip) => {
  chip.addEventListener('click', () => {
    setQuery(chip.dataset.chip ?? '');
    input.focus();
  });
});

function setQuery(text: string): void {
  input.value = text;
  input.dispatchEvent(new Event('input'));
}

// ── Generate ──────────────────────────────────────────────────────────
generateBtn.addEventListener('click', handleGenerate);

async function handleGenerate(): Promise<void> {
  const query = input.value.trim();
  if (!query) {
    input.focus();
    return;
  }

  generateBtn.disabled = true;
  generateBtn.classList.add('dc-btn--loading');
  generateBtn.textContent = ''; // spinner comes from the ::before pseudo-element
  hideResults();
  const wakeTimer = setTimeout(() => { wakeNotice.hidden = false; }, 3000);

  try {
    const res = await fetch(API_BASE_URL + '/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    const json = await res.json();

    if (!res.ok || json.error) {
      showError(json.error ?? 'An unexpected error occurred.');
      return;
    }

    currentResult = json as DorkResponse;
    currentQuery = query;
    currentAssessment = assessDork(query, currentResult.dork);
    renderResult(currentResult);
    renderEffectiveness(currentAssessment);
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch {
    showError('Could not reach the DorkCraft backend. Please try again in a minute.');
  } finally {
    clearTimeout(wakeTimer);
    wakeNotice.hidden = true;
    generateBtn.disabled = false;
    generateBtn.classList.remove('dc-btn--loading');
    generateBtn.innerHTML = GENERATE_LABEL;
  }
}

// ── Render result ─────────────────────────────────────────────────────
function renderResult(data: DorkResponse): void {
  badge.textContent = data.category ?? 'general';
  dorkOutput.textContent = data.dork;

  validIndicator.classList.toggle('dc-card__valid--hidden', !data.is_valid);

  const warnings = data.warnings ?? [];
  warningsBox.classList.toggle('dc-card--hidden', warnings.length === 0);
  warningsList.replaceChildren(...warnings.map((w) => el('li', '', w)));

  explList.replaceChildren(...(data.explanation ?? []).map((point) => el('li', '', point)));

  varList.replaceChildren(
    ...(data.variations ?? []).map((v) => {
      const li = el('li');
      const hint = el('span', 'dc-card__var-copy', 'copy');
      li.append(el('code', '', v), hint);
      li.addEventListener('click', () => copyText(v, hint));
      return li;
    }),
  );

  saveBtn.disabled = false;
  saveBtn.innerHTML = SAVE_LABEL;

  resultCard.classList.remove('dc-card--hidden');
  errorCard.classList.add('dc-card--hidden');
}

function showError(message: string): void {
  errorMsg.textContent = message;
  errorCard.classList.remove('dc-card--hidden');
  resultCard.classList.add('dc-card--hidden');
  effPanel.classList.add('dc-card--hidden');
}

function hideResults(): void {
  resultCard.classList.add('dc-card--hidden');
  errorCard.classList.add('dc-card--hidden');
  effPanel.classList.add('dc-card--hidden');
}

// ── Effectiveness panel ───────────────────────────────────────────────
function checkItem(check: Check): HTMLLIElement {
  const li = el('li', 'dc-check ' + (check.passed ? 'dc-check--pass' : 'dc-check--fail'));

  const box = el('span', 'dc-check__box');
  box.setAttribute('aria-hidden', 'true');
  if (check.passed) {
    box.innerHTML =
      '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
  }

  const body = el('div', 'dc-check__body');
  const head = el('div', 'dc-check__head');
  const title = el('span', 'dc-check__title');
  title.append(el('span', 'dc-sr-only', check.passed ? 'Passed: ' : 'Failed: '), check.title);
  head.append(title, el('span', 'dc-tag dc-tag--' + check.impact, check.impact + ' impact'));
  body.append(head, el('p', 'dc-check__detail', check.detail));

  li.append(box, body);
  return li;
}

function renderEffectiveness(a: Effectiveness): void {
  effPanel.dataset.level = a.level;
  effCount.textContent = a.passed + ' / ' + a.total + ' passed';
  effScore.textContent = a.score + '%';
  effRingValue.style.strokeDasharray = String(RING_LENGTH);
  effRingValue.style.strokeDashoffset = String(RING_LENGTH * (1 - a.score / 100));
  effHeadline.textContent = a.label + ' search' + (a.level === 'strong' ? ' ✓' : '');
  effSub.textContent = a.summary;
  effBarLabel.textContent = a.passed + ' of ' + a.total + ' checks passed';
  effBarMax.textContent = String(a.total);

  effGroups.replaceChildren(
    ...DIMENSIONS.map((dimension) => {
      const checks = a.checks.filter((c) => c.dimension === dimension.id);
      const group = el('section', 'dc-eff__group');
      const head = el('h3', 'dc-eff__group-head');
      const marker = el('span', '', '▸');
      marker.setAttribute('aria-hidden', 'true');
      head.append(marker, ' ' + dimension.label);
      const tally = el(
        'span',
        'dc-eff__group-count',
        checks.filter((c) => c.passed).length + '/' + checks.length,
      );
      const top = el('div', 'dc-eff__group-top');
      top.append(head, tally);
      const list = el('ul', 'dc-eff__checks');
      list.setAttribute('role', 'list');
      list.append(...checks.map(checkItem));
      group.append(top, list);
      return group;
    }),
  );

  // Grow the bar from empty so the change of state is visible.
  effBar.style.transform = 'scaleX(0)';
  effPanel.classList.remove('dc-card--hidden');
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      effBar.style.transform = 'scaleX(' + a.passed / a.total + ')';
    });
  });
}

// ── Result actions ────────────────────────────────────────────────────
copyBtn.addEventListener('click', () => {
  if (dorkOutput.textContent) copyText(dorkOutput.textContent, copyBtn);
});

openBtn.addEventListener('click', () => {
  const dork = dorkOutput.textContent;
  if (!dork) return;
  window.open(
    'https://www.google.com/search?q=' + encodeURIComponent(dork),
    '_blank',
    'noopener,noreferrer',
  );
});

exportBtn.addEventListener('click', () => {
  if (!currentResult) return;
  const lines = [
    '# DorkCraft: ' + currentQuery,
    '',
    '## Generated Dork',
    '```',
    currentResult.dork,
    '```',
    '',
    ...(currentAssessment
      ? ['**Success score:** ' + currentAssessment.score + '/100 (' + currentAssessment.label + ')', '']
      : []),
    '## How it works',
    ...(currentResult.explanation ?? []).map((e) => '- ' + e),
    '',
    '## Variations',
    ...(currentResult.variations ?? []).map((v) => '- `' + v + '`'),
    '',
    '---',
    '*Generated by [DorkCraft](https://github.com/juandresrodca/DorkCraft)*',
  ];
  download('dorkcraft-result.md', lines.join('\n'));
});

shareBtn.addEventListener('click', async () => {
  if (!currentQuery) return;
  const url = location.origin + location.pathname + '?q=' + encodeURIComponent(currentQuery);
  if (navigator.share) {
    try {
      await navigator.share({ title: 'DorkCraft Result', url });
    } catch {
      // Share sheet dismissed: nothing to do.
    }
  } else {
    copyText(url, shareBtn);
  }
});

// ── Saved history ─────────────────────────────────────────────────────
saveBtn.addEventListener('click', () => {
  if (!currentResult || !currentAssessment) return;
  const entries = saveEntry(localStorage, {
    ts: Date.now(),
    query: currentQuery,
    dork: currentResult.dork,
    score: currentAssessment.score,
    level: currentAssessment.level,
  });
  renderHistory(entries);
  saveBtn.disabled = true;
  saveBtn.textContent = 'Saved to history';
});

function historyItem(entry: HistoryEntry): HTMLLIElement {
  const li = el('li');
  const button = el('button', 'dc-hist__item');
  button.type = 'button';
  button.title = 'Run this search again';

  const time = el('time', 'dc-hist__time', formatTimestamp(entry.ts));
  time.dateTime = new Date(entry.ts).toISOString();

  const body = el('span', 'dc-hist__body');
  body.append(el('span', 'dc-hist__query', entry.query), el('code', 'dc-hist__dork', entry.dork));

  const score = el('span', 'dc-score dc-score--' + entry.level, entry.score + '%');
  score.title = 'Success score';

  button.append(time, body, score);
  button.addEventListener('click', () => {
    setQuery(entry.query);
    handleGenerate();
  });
  li.append(button);
  return li;
}

function renderHistory(entries: HistoryEntry[] = loadHistory(localStorage)): void {
  histCount.textContent = entries.length + ' saved';
  histEmpty.hidden = entries.length > 0;
  histActions.hidden = entries.length === 0;
  histList.replaceChildren(...entries.map(historyItem));
}

histDownload.addEventListener('click', () => {
  const entries = loadHistory(localStorage);
  if (!entries.length) return;
  const stamp = formatTimestamp(Date.now()).slice(0, 10);
  download('dorkcraft-history-' + stamp + '.md', buildMarkdown(entries));
});

// Clearing takes two clicks: saved searches cannot be recovered.
let clearArmed: ReturnType<typeof setTimeout> | null = null;
histClear.addEventListener('click', () => {
  if (clearArmed) {
    clearTimeout(clearArmed);
    clearArmed = null;
    histClear.textContent = 'Clear history';
    clearHistory(localStorage);
    renderHistory();
    return;
  }
  histClear.textContent = 'Click again to clear';
  clearArmed = setTimeout(() => {
    clearArmed = null;
    histClear.textContent = 'Clear history';
  }, 3000);
});

renderHistory();

// ── Common dorks ──────────────────────────────────────────────────────
if (commonList) {
  const defaultText = commonNoteText.dataset.default ?? '';
  const describe = (item: HTMLElement | null): void => {
    commonNoteName.textContent = item?.dataset.name ?? 'What it does';
    commonNoteText.textContent = item?.dataset.explanation ?? defaultText;
  };
  const itemFrom = (target: EventTarget | null): HTMLElement | null =>
    target instanceof Element ? target.closest<HTMLElement>('.dc-common__item') : null;

  commonList.addEventListener('mouseover', (e) => {
    const item = itemFrom(e.target);
    if (item) describe(item);
  });
  commonList.addEventListener('focusin', (e) => describe(itemFrom(e.target)));
  commonList.addEventListener('mouseleave', () => describe(itemFrom(document.activeElement)));
  commonList.addEventListener('focusout', (e) => {
    if (!commonList.contains(e.relatedTarget as Node | null)) describe(null);
  });
  commonList.addEventListener('click', (e) => {
    const item = itemFrom(e.target);
    if (!item) return;
    copyText(item.dataset.dork ?? '');
    commonNoteName.textContent = 'Copied to clipboard';
    setTimeout(() => {
      if (commonNoteName.textContent === 'Copied to clipboard') {
        commonNoteName.textContent = item.dataset.name ?? 'What it does';
      }
    }, 1600);
  });
}

// ── Cheat sheet toggle ────────────────────────────────────────────────
cheatToggle.addEventListener('click', () => {
  const expanded = cheatToggle.getAttribute('aria-expanded') === 'true';
  cheatToggle.setAttribute('aria-expanded', String(!expanded));
  cheatBody.classList.toggle('dc-cheat__body--open', !expanded);
});

// ── Pre-fill from a shared link ───────────────────────────────────────
const sharedQuery = new URLSearchParams(location.search).get('q');
if (sharedQuery) {
  setQuery(sharedQuery);
  handleGenerate();
}
