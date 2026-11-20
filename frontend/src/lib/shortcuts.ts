/**
 * DorkCraft: pinned common-dork shortcuts
 * ---------------------------------------
 * The user pins a pattern from the common dorks list by double-clicking it.
 * Pins are stored as the pattern text in localStorage and never leave the
 * browser. Only patterns that still exist in the list are kept, so a pattern
 * removed from the list in a later release drops out of saved shortcuts.
 */

export const SHORTCUTS_KEY = 'dc_shortcuts';

type Store = Pick<Storage, 'getItem' | 'setItem'>;

/** Saved shortcuts, in pin order, limited to patterns in `known`. */
export function loadShortcuts(store: Store, known: readonly string[]): string[] {
  try {
    const raw: unknown = JSON.parse(store.getItem(SHORTCUTS_KEY) ?? '[]');
    if (!Array.isArray(raw)) return [];
    const kept = raw.filter((d): d is string => typeof d === 'string' && known.includes(d));
    return [...new Set(kept)];
  } catch {
    return [];
  }
}

export function saveShortcuts(store: Store, dorks: readonly string[]): void {
  try {
    store.setItem(SHORTCUTS_KEY, JSON.stringify(dorks));
  } catch {
    // Storage blocked or full: the shortcuts still work until the page is closed.
  }
}
