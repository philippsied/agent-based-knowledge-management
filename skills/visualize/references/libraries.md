# CDN Library Reference

Preferred CDN libraries and when to use them. Always use jsDelivr for consistent, fast loading.

## Table of Contents
- [Motion](#motion) ⭐ (animations — included in skeleton)
- [Chart.js](#chartjs)
- [D3.js](#d3js)
- [Three.js](#threejs)
- [Mermaid](#mermaid)
- [Reveal.js](#revealjs)
- [Leaflet](#leaflet)

---

## Motion

**Best for:** ALL animations. Spring physics, scroll-triggered reveals, staggered entrances, number counters, hover micro-interactions. Replaces raw CSS @keyframes and IntersectionObserver.

```html
<script src="https://cdn.jsdelivr.net/npm/motion@12/dist/motion.js"></script>
```

**Included in the mandatory skeleton.** Exposes global `Motion` object.

```javascript
// Spring-animated card entrance
Motion.animate('.card',
  { opacity: [0, 1], y: [40, 0], scale: [0.95, 1] },
  { delay: Motion.stagger(0.08), duration: 0.5, ease: Motion.spring({ stiffness: 200, damping: 22 }) }
);

// Scroll-triggered reveal
Motion.inView('.section', (info) => {
  Motion.animate(info.target, { opacity: 1, y: 0 }, { duration: 0.6 });
});
```

See [animations.md](animations.md) for complete API reference and recipes (~15KB gzipped).

---

## Chart.js

**Best for:** Standard charts with beautiful defaults. Bar, line, pie, doughnut, radar, polar area, scatter, bubble.

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
```

### When to Use
- Quick data visualization with minimal config
- Standard chart types (bar, line, pie, doughnut, radar)
- When you want great defaults without deep customization
- Responsive, animated charts out of the box

### Pattern
```html
<canvas id="myChart"></canvas>
<script>
new Chart(document.getElementById('myChart'), {
  type: 'bar', // line, pie, doughnut, radar, polarArea, scatter, bubble
  data: {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{
      label: 'Revenue',
      data: [12, 19, 3],
      backgroundColor: 'hsla(220, 80%, 55%, 0.7)',
      borderColor: 'hsl(220, 80%, 55%)',
      borderWidth: 2,
      borderRadius: 6,
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: 'bottom' },
      title: { display: true, text: 'Monthly Revenue' }
    },
    scales: { y: { beginAtZero: true } }
  }
});
</script>
```

### Tips
- Use `borderRadius` for rounded bar charts
- `tension: 0.4` on line datasets for smooth curves
- Combine chart types: `{ type: 'bar', datasets: [{ type: 'line', ... }, { ... }] }`

---

## D3.js

**Best for:** Custom, complex, or unconventional data visualizations. Force-directed graphs, geographic maps, treemaps, sunbursts.

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
```

### When to Use
- Custom visualizations Chart.js can't handle
- Force-directed network graphs
- Geographic/map visualizations (with topojson)
- Treemaps, sunbursts, chord diagrams
- When you need full SVG control

### Pattern
```html
<div id="viz"></div>
<script>
const data = [30, 86, 168, 281, 303, 365];
const width = 600, height = 400, margin = { top: 20, right: 20, bottom: 30, left: 40 };

const svg = d3.select('#viz').append('svg')
  .attr('viewBox', `0 0 ${width} ${height}`);

const x = d3.scaleBand()
  .domain(data.map((_, i) => i))
  .range([margin.left, width - margin.right])
  .padding(0.2);

const y = d3.scaleLinear()
  .domain([0, d3.max(data)])
  .range([height - margin.bottom, margin.top]);

svg.selectAll('rect').data(data).join('rect')
  .attr('x', (_, i) => x(i))
  .attr('y', d => y(d))
  .attr('width', x.bandwidth())
  .attr('height', d => y(0) - y(d))
  .attr('rx', 4)
  .attr('fill', 'hsl(220, 80%, 55%)');
</script>
```

---

## Three.js

**Best for:** 3D visualizations, immersive data displays, architectural/spatial representations.

```html
<script src="https://cdn.jsdelivr.net/npm/three@0.170/build/three.module.min.js" type="module"></script>
```

### When to Use
- 3D data visualization (3D scatter, terrain)
- Product/architectural visualization
- Immersive, impressive hero visuals
- When 2D isn't enough to convey the concept

---

## Mermaid

**Best for:** Diagrams from text definitions. Flowcharts, sequence diagrams, Gantt charts, ER diagrams, class diagrams.

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true, theme: 'neutral' });</script>
```

### When to Use
- Quick flowcharts and process diagrams
- Sequence diagrams for API/system interactions
- Gantt charts for project timelines
- When diagram accuracy matters more than custom styling

### Pattern
```html
<pre class="mermaid">
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
</pre>
```

### Tips
- Use `%%` for comments in Mermaid syntax
- Themes: `default`, `neutral`, `dark`, `forest`
- Custom styles: `style A fill:#f9f,stroke:#333`

---

## Reveal.js

**Best for:** Full-featured slide decks when you need more than the basic template.

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/theme/white.css">
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.js"></script>
```

### When to Use
- Complex presentations with nested slides (vertical + horizontal)
- Markdown-based slide content
- Built-in speaker notes, PDF export, overview mode
- When the basic slide template isn't enough

### Tips
- Themes: `white`, `black`, `league`, `beige`, `moon`, `night`, `serif`, `simple`, `solarized`
- Fragments for step-by-step reveals
- Code highlighting with highlight.js plugin

---

## Leaflet

**Best for:** Interactive maps with markers, polygons, heatmaps.

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1/dist/leaflet.js"></script>
```

### When to Use
- Location data visualization
- Geographic comparisons
- Travel/route visualization
- Any data with lat/lng coordinates

### Pattern
```html
<div id="map" style="height: 500px; border-radius: 12px;"></div>
<script>
const map = L.map('map').setView([37.5, -122.3], 10);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap'
}).addTo(map);
L.marker([37.5, -122.3]).addTo(map).bindPopup('Location');
</script>
```

---

## Chart.js Reliability Patterns (MANDATORY for every chart)

Charts are the most common failure. These production-grade patterns prevent "Canvas already in use" errors, blank white charts, and theme-toggle breakage. Use them instead of raw `new Chart()`.

**Global setup (immediately after the Chart.js CDN):**
- `Chart.defaults.animation = false;` — MUST be set before any chart creation (automatically checked by evaluation).
- Every chart function MUST start with `if (typeof Chart === 'undefined') { console.error('Chart.js not loaded'); return; }`.
- Every canvas needs `role="img"` and a descriptive `aria-label`; wrap in a container with explicit `height` >= 300px (360px+ for dashboards, 400px for slide charts).
- Chart config MUST set `maintainAspectRatio: false`, `responsive: true`, and `plugins: { tooltip: { enabled: true } }`. NEVER disable tooltips. NEVER use import/export syntax with the CDN — use `var` declarations only.

**Troubleshooting blank white charts:** verify (1) CDN before `</head>`, (2) `Chart.defaults.animation = false;` immediately after CDN, (3) init inside a DOMContentLoaded listener, (4) no module import/export anywhere, (5) `safeInit()`/reset pattern used, (6) canvas has `role="img"` + `aria-label`.

### ChartManager (bulletproof init/destroy/theme)

Use `ChartManager.safeInit()` instead of raw `new Chart()`:

```javascript
var ChartManager = {
  charts: new Map(),
  safeInit: function(canvasId, config) {
    if (typeof Chart === 'undefined') {
      console.error('Chart.js library not loaded - check CDN inclusion');
      return null;
    }
    try {
      if (this.charts.has(canvasId)) {
        this.charts.get(canvasId).destroy();
        this.charts.delete(canvasId);
      }
      var ctx = document.getElementById(canvasId);
      if (!ctx) {
        console.error('Canvas element not found: ' + canvasId);
        return null;
      }
      // Ensure no conflicting chart instances
      if (ctx.chart) {
        ctx.chart.destroy();
        delete ctx.chart;
      }
      // Set accessibility attributes
      ctx.setAttribute('role', 'img');
      if (!ctx.getAttribute('aria-label')) {
        ctx.setAttribute('aria-label', 'Chart visualization');
      }
      // Initialize with enhanced error handling
      var chart = new Chart(ctx, config);
      this.charts.set(canvasId, chart);
      return chart;
    } catch (error) {
      console.error('Chart initialization failed for ' + canvasId + ':', error);
      return null;
    }
  },
  updateTheme: function() {
    if (typeof Chart === 'undefined') return;
    this.charts.forEach(function(chart, canvasId) {
      try {
        chart.update();
      } catch (error) {
        console.error('Chart theme update failed for ' + canvasId + ':', error);
      }
    });
  },
  destroyAll: function() {
    this.charts.forEach(function(chart) {
      try {
        chart.destroy();
      } catch (error) {
        console.error('Chart destruction failed:', error);
      }
    });
    this.charts.clear();
  }
};
```

### Guard flag + canvas reset (chartsBuilt pattern)

```javascript
// REQUIRED: Chart destruction and canvas reset to prevent "Canvas already in use" errors
var chartsBuilt = false; // Guard flag

function buildCharts() {
  if (chartsBuilt) return; // Prevent double-initialization during theme detection
  
  // REQUIRED: Reset canvas before building
  function resetCanvas(id) {
    var old = document.getElementById(id);
    if (!old) return null;
    var parent = old.parentNode;
    var canvas = document.createElement('canvas');
    canvas.id = id;
    parent.replaceChild(canvas, old);
    return canvas;
  }
  
  // Example chart with required settings
  var ctx = resetCanvas('myChart');
  if (ctx) {
    new Chart(ctx, {
      type: 'bar',
      data: { /* your data */ },
      options: {
        responsive: true,
        maintainAspectRatio: false, // REQUIRED
        animation: false, // MANDATORY: Plus set Chart.defaults.animation = false globally
        plugins: {
          tooltip: {
            enabled: true, // NEVER disable tooltips
            padding: 12,
            cornerRadius: 8
          }
        },
        layout: { padding: 20 } // REQUIRED: breathing room
      }
    });
  }
  
  chartsBuilt = true; // Mark as built
}

// CRITICAL: Disable Chart.js default animations IMMEDIATELY after Chart.js loads
Chart.defaults.animation = false; // MUST be set before any chart creation

// REQUIRED: Build charts after DOM loads
document.addEventListener('DOMContentLoaded', buildCharts);

// REQUIRED: Rebuild charts on theme change
function onThemeChange() {
  chartsBuilt = false; // Reset flag
  setTimeout(buildCharts, 100); // Slight delay for CSS variable updates
}
```

### Chart styling defaults (apply beyond library defaults)

- **Hover tooltips enabled** — never disable:
  ```javascript
  options: {
    plugins: {
      tooltip: {
        enabled: true, // NEVER set to false
        mode: 'index',
        intersect: false
      }
    }
  }
  ```
- Min chart height 300px desktop / 250px mobile; container 12px border-radius, 40px internal padding, 360px min height for substantial presence.
- Axis tick labels ≥13px, axis titles 14px, chart titles ≥16px, legend 13px.
- `layout: { padding: { top: 20, right: 20, bottom: 20, left: 20 } }`; `maxRotation: 0` on ticks (keep labels horizontal), `maxTicksLimit` if labels overflow.
- Grid lines very faint: `rgba(255,255,255,0.04)` dark / `rgba(0,0,0,0.06)` light (or `var(--border)`).
- Tooltip styling: `padding: 12`, `cornerRadius: 8`, `titleFont: { size: 14 }`, `bodyFont: { size: 13 }`.
- Point radius 0 default, 6 on hover — cleaner line charts. `maintainAspectRatio: false`, control size via CSS container.
- Legend `'top'` for horizontal charts, `'right'` for vertical with space. Donut/pie: always label segment percentages.
- Use theme-aware colors read at render time; re-render on theme change. `Chart.defaults.color = getComputedStyle(root).getPropertyValue('--text-secondary').trim()`; grid line colors use `var(--border)`. High-contrast difference between data series for accessibility.
- Custom padding (`layout: { padding: 30 }`), remove excessive gridlines (opacity ≤ 0.04), rounded corners (`borderRadius: 4`), theme-matched palettes — avoid auto-generated library defaults.

### Theme-aware color reader + safe rebuild

```javascript
// Theme-aware Chart.js setup (include in every chart visualization)
function getChartColors() {
  var s = getComputedStyle(document.documentElement);
  return {
    text: s.getPropertyValue('--text').trim(),
    textSecondary: s.getPropertyValue('--text-secondary').trim(),
    border: s.getPropertyValue('--border').trim(),
    surface: s.getPropertyValue('--surface').trim(),
    accent: s.getPropertyValue('--accent').trim(),
  };
}

// REQUIRED: Reset canvas before rebuilding charts (prevents "Canvas already in use" errors)
function resetCanvas(id) {
  var old = document.getElementById(id);
  var parent = old.parentNode;
  var canvas = document.createElement('canvas');
  canvas.id = id;
  parent.replaceChild(canvas, old);
  return canvas;
}

// Usage in buildCharts():
//   try { if (window.myChart) window.myChart.destroy(); } catch(e) {}
//   window.myChart = new Chart(resetCanvas('myChart'), { ... });

// CRITICAL: Always check chart existence before destroy() to prevent console errors
function buildCharts() {
  var isDark = document.documentElement.classList.contains('theme-dark');
  var colors = getChartColors();
  
  // Safe chart destruction and rebuild pattern
  if (window.myChart) {
    try { window.myChart.destroy(); } catch(e) { /* ignore */ }
  }
  window.myChart = new Chart(resetCanvas('myChart'), {
    // chart config with theme-aware colors
    options: {
      scales: {
        x: { ticks: { color: colors.textSecondary }, grid: { color: colors.border } },
        y: { ticks: { color: colors.textSecondary }, grid: { color: colors.border } }
      }
    }
  });
}
```

### Full integration safety pattern (STEP 1–7)

MANDATORY for all Chart.js usage to prevent console errors:

```javascript
// STEP 1: Global variables - MUST use var, never let/const
var chartsBuilt = false;

// STEP 2: Chart building function with validation
function buildCharts() {
  // CRITICAL: Always validate Chart.js loaded first
  if (chartsBuilt || typeof Chart === 'undefined') return;
  
  // STEP 3: Destroy existing charts to prevent "Canvas already in use"
  if (window.myChart) window.myChart.destroy();
  
  // STEP 4: Reset canvas elements
  var canvas = document.getElementById('chartId');
  if (!canvas) return;
  
  // STEP 5: Get theme colors from CSS variables
  var isDark = document.documentElement.className.includes('theme-dark');
  var textColor = isDark ? '#EDEDED' : '#0f172a';
  var gridColor = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.06)';
  
  // STEP 6: Create chart with proper options
  try {
    window.myChart = new Chart(canvas.getContext('2d'), {
      // Your chart configuration here
      options: {
        responsive: true,
        maintainAspectRatio: false, // REQUIRED
        plugins: {
          tooltip: { enabled: true }, // REQUIRED - never disable
          legend: { 
            labels: { color: textColor, font: { family: 'Inter' } }
          }
        },
        scales: {
          x: { 
            ticks: { color: textColor },
            grid: { color: gridColor }
          },
          y: { 
            ticks: { color: textColor },
            grid: { color: gridColor }
          }
        }
      }
    });
    
    chartsBuilt = true;
  } catch (error) {
    console.error('Chart creation failed:', error);
  }
}

// STEP 7: Theme change handler
function onThemeChange() {
  if (chartsBuilt) {
    chartsBuilt = false;
    buildCharts();
  }
    var ctx = document.getElementById('myChart');
    if (!ctx) {
      console.error('Chart canvas #myChart not found');
      return;
    }
    // ... build chart
  } catch (error) {
    console.error('Chart building failed:', error);
  }
}
```
