---
name: visualize
description: >
  Create beautiful, self-contained HTML visualizations from any content or idea.
  Use for: slide decks, presentations, infographics, dashboards, flowcharts, diagrams,
  timelines, comparison tables, data visualizations, landing pages, one-pagers, org charts,
  mind maps, process flows, kanban boards, report summaries, or any visual that helps
  humans digest information faster. Trigger on requests like "visualize this," "make a deck,"
  "create a slide," "build an infographic," "show me a dashboard," "make this visual,"
  or any request to present information in a visual HTML format. For internal Obsidian
  reference boards use the `canvas` skill instead; `visualize` produces external, shareable HTML.
license: MIT
allowed-tools: Read Write Edit Glob Grep
metadata:
  author: careerhackeralex
  version: 0.3.0
  category: document-creation
  tags: [visualization, html, slides, dashboard, infographic]
---

# Visualize

Turn any idea, data, or content into a stunning single-file HTML visualization. HTML is a visualization tool, not a "website." Invoked **mid-conversation** — use the full conversation context (discussion, links, pasted data) as source material. When given a URL, crawl and extract its content.

**vs `canvas`:** `visualize` = external, shareable HTML (decks, infographics, dashboards) to send or present; `canvas` = an internal Obsidian board for in-vault visual organization.

## Workflow (every time)

1. **Understand** — what's the message? Who's the audience? What format fits? (See the type table below.)
2. **Copy the skeleton** — start from the ENTIRE template in [references/skeleton.md](references/skeleton.md). NEVER write HTML from scratch; it wires up the menu, theme system, required CSS properties, semantic HTML, and accessibility.
3. **Structure** — outline sections BEFORE filling the skeleton's `<!-- YOUR CONTENT HERE -->`.
4. **Build** — add content, charts, styles. Keep ALL colors as CSS vars. Load the reference(s) below for the pieces you need.
5. **Verify** the non-negotiables (below), then open the file.

## After Creating a File

Default output is the vault's `wiki/visualizations/` directory (override with any user-specified path). Write BOTH:

1. **The artifact** — `wiki/visualizations/<slug>.html`, descriptive kebab-case slug (e.g. `q4-revenue-dashboard.html`).
2. **A companion stub** — `wiki/visualizations/<slug>.md`, so the artifact is graph-visible and lint-classified:

   ```
   ---
   type: visualization
   created: <YYYY-MM-DD>
   ---
   [Open the visualization](<slug>.html)

   ![[<slug>.html]]
   ```

Then **always do BOTH:** (1) auto-open — `open <file>.html` (macOS) / `xdg-open <file>.html` (Linux); (2) return the path as a clickable `file://<absolute-path>` URL. Both files live under `wiki/visualizations/` (git-ignored — regenerable — and `wiki-lint`-excluded).

## Core Principles

1. **Single-file HTML** — one `.html` file with inline CSS/JS. Opens in any browser, works offline, emails easily.
2. **Light theme optimized** — prioritize light-mode quality. Dark theme available via toggle.
3. **Beautiful by default** — first output looks professional with zero iteration.
4. **Content-first** — the visualization serves the message; never sacrifice clarity for aesthetics.
5. **Responsive** — desktop, tablet, mobile, unless explicitly fixed-dimension (e.g. 16:9 slides, posters).
6. **Visual restraint** — no floating gradient orbs, rainbow/gradient borders, gradient text on headings, scale transforms, glow effects, or ornamental animations.

Always use real content — never "Lorem ipsum" or fake data when real context exists.

## Non-Negotiables (EVALUATION FAILURE GUARANTEED WITHOUT THESE)

Every file MUST include, all provided by the skeleton:

1. **CSS Custom Properties — exact names only:** `--bg, --surface, --surface-hover, --border, --text, --text-secondary, --accent, --accent-secondary, --positive, --negative, --warning`. NO other names (not `--bg-primary`, not `--text-primary`).
2. **Class-based themes:** define BOTH `.theme-light` and `.theme-dark` with full custom-property sets. Toggle changes the html class (`document.documentElement.className = 'theme-' + newTheme`). NEVER rely only on `:root` / `@media (prefers-color-scheme)`, and NEVER use `data-theme` — the evaluation checks for class-based themes.
3. **Utility menu system:** `.viz-menu` with `.viz-menu-toggle`, `.viz-menu-dropdown`, download-PNG button (`onclick="downloadImage()"`), print button (`onclick="window.print()"`), plus the html-to-image CDN (`<script src="https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js"></script>`).
4. **Semantic HTML:** `<main id="main-content">`, multiple `<section>` elements for major content blocks, skip-to-content link, landmark roles, chart accessibility (`role="img"` + `aria-label`).
5. **Chart.js (when charts are used):** `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>` before `</head>`, immediately followed by `<script>Chart.defaults.animation = false;</script>`. Every chart function starts with `if (typeof Chart === 'undefined') { console.error('Chart.js not loaded'); return; }`. Set `maintainAspectRatio: false`, `responsive: true`, `plugins: { tooltip: { enabled: true } }` — never disable tooltips. Container height ≥300px (≥360px dashboards). See [references/libraries.md](references/libraries.md) for the mandatory ChartManager / reliability patterns.
6. **Responsive:** section spacing ≥48px; NO horizontal overflow at 375px (add `@media (max-width: 375px) { body { overflow-x: hidden; } }`). Font hierarchy: h1 ≥2.5rem (≥3rem title slides), h2 ≥2rem, h3 ≥1.5rem, body 1rem — each heading level visibly smaller (≥0.5rem step).
7. **Print & reduced motion:** `@media print` styles and `@media (prefers-reduced-motion: reduce)` with animations disabled.
8. **Entrance animations:** `.animate` classes, `data-reveal` attributes, or CSS `@keyframes` — presence is auto-detected and required. Above-fold content uses `.animate` (never `data-reveal`); use `data-reveal` sparingly (max 3-4 below-fold sections).
9. **JavaScript:** top-level variables use `var` (not `let`/`const`, avoids TDZ with hoisting). Functions `cycleTheme()`, `toggleMenu()` (with outside-click + Escape close), and `function onThemeChange() {}` for chart re-render on theme change.

**Interactivity (mandatory):** every file needs ≥1 meaningful interaction beyond theme toggle + menu (filter, search, sort, drill-down, expand/collapse, carousel, slide nav). Static pages score low.

## Visualization Types

Choose the right format; see [references/types.md](references/types.md) for per-type structure and patterns.

- **Slide Deck** — 16:9, keyboard nav, transitions · **Infographic** — long scroll, big numbers · **Dashboard** — grid of KPI cards + charts · **Flowchart** — Mermaid/SVG · **Timeline** — alternating left/right, scroll-triggered · **Comparison** — feature matrix, pros/cons · **Data Viz** — Chart.js/D3 · **One-Pager** — single viewport, print-friendly · **Mind Map** — radial SVG · **Kanban** — column cards.
- **Data Story** — scrollytelling · **Process Guide** — numbered steps + icons · **Status Report** — KPIs + progress bars, one page · **Org Chart** — hierarchical tree + avatars · **Product Card** — hero + feature pills + CTA.
- **Fixed-dimension** (posters, carousel cards 1080×1080, event posters, quote cards, banners 1200×630, resume/CV): a single-viewport canvas with `overflow: hidden` + flex column + `justify-content: space-between`, NOT a scrolling page. No hamburger menu. Typography dominates; one idea per card. Sizing and font scales in [references/css-techniques.md](references/css-techniques.md).

## When to Load Each Reference

Load only what the current task needs — do not read all references reflexively.

| Reference | Load it when you need… |
|-----------|------------------------|
| [references/skeleton.md](references/skeleton.md) | ALWAYS first — the complete copy-paste HTML template (themes, menu, CSS props, print, Inter font, animations, popover/details). Copy it, replace `YOUR CONTENT HERE`, save. |
| [references/design-system.md](references/design-system.md) | Typography, color system, spacing, card system, background atmosphere, visual polish, accessibility checklist, icons, theme-aware slide gradients, slide-deck chart container, slide-deck light mode. |
| [references/css-techniques.md](references/css-techniques.md) | Advanced CSS: glassmorphism, gradient/fluid text (`clamp()`), scroll-snap, conic-gradient charts, container queries, `:has()`, subgrid, print CSS, CSS-only charts, single-screen poster sizing, mobile-first grid, design tokens. |
| [references/libraries.md](references/libraries.md) | CDN choice + patterns for Chart.js (incl. mandatory ChartManager / reliability / theme-aware / safety patterns), D3, Three.js, Mermaid, Reveal.js, Leaflet. Load for ANY chart work. |
| [references/menu.md](references/menu.md) | The hamburger menu (HTML/CSS/JS), theme cycling, PNG download, print styles, slide-deck download handling, and the Reveal.js custom bottom nav bar (`prevSlide`/`nextSlide`). |
| [references/animations.md](references/animations.md) | Entrance animations, hover effects, scroll-triggered reveals, number counters (+ debug pattern), CSS slide transitions, and when to reach for Motion.js. |
| [references/types.md](references/types.md) | Structure and best-practice patterns for a specific visualization type (deck, infographic, dashboard, flowchart, timeline, comparison, data-viz, one-pager, mind map, kanban). |

**Libraries encouraged** — best tool for the job: Tailwind (`https://cdn.tailwindcss.com`), Chart.js, D3 (`d3@7`), Mermaid, Three.js, Reveal.js (numeric `width`/`height`, `controls: false`, custom nav), Leaflet (required for geographic data — never hand-draw SVG maps). SVG for icons/simple graphics; no external image URLs unless the user provides them. Prefer CSS animations over JS.

## Anti-Patterns

- ❌ Walls of text (if it reads like a document, it's not a visualization) · tiny fonts (min 14px body, 20px+ presentation headings) · rainbow colors (2-3 palette colors + neutrals) · placeholder/fake content.
- ❌ Over-engineering (simplest approach that looks stunning) · cramped layouts (add whitespace) · generic/templated feel (vary grid structure, section rhythm, focal point) · missing menu · broken print · text colored near the background.

## Verify Before Opening

Confirm every item in **Non-Negotiables** above, plus: OS-preference detected on first visit and persisted in localStorage; correct font loaded (Inter default, Noto Sans KR / appropriate CJK/RTL for non-Latin); min sizing followed (cards 280px+, text 16px+); at least one meaningful interaction; **zero console errors on load**.

The quality bar: **"good, period"** — not "good for AI-generated."
