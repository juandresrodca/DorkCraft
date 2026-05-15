// @ts-check
import { defineConfig } from 'astro/config';

/**
 * Astro configuration for DorkCraft.
 *
 * GitHub Pages deployment:
 *   - Set `base` to your repo name (e.g. '/google-dorksHelper')
 *   - `output: 'static'` produces a fully pre-rendered site
 *   - `trailingSlash: 'always'` avoids 404s on GitHub Pages
 *
 * Local dev: base is ignored, so you can leave it as-is.
 */
export default defineConfig({
  output: 'static',
  // Update this to match your GitHub repo name when deploying:
  base: '/DorkCraft',
  trailingSlash: 'always',
  site: 'https://juandresrodca.github.io',
});
