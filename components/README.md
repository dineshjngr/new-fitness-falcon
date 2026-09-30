# The Fitness Falcon - Global Component & Architecture System

This directory houses the shared global architecture for The Fitness Falcon.

The entire website uses:
- **1 shared global header** (`components/header.html`)
- **1 shared global footer** (`components/footer.html`)
- **1 global layout system** (`components/layout.html` + `assets/css/custom-style.css`)

Individual pages only provide their own page-specific content within `<main id="main-content" class="falcon-main-layout">` and page-specific `<head>` metadata.

## Available Architecture Components

- `header.html`: Global responsive header, top bar (breaking news ticker, date, social channels, theme switch), desktop navigation with dropdowns, mobile navigation drawer (`.slide-bar`), and live search modal with auto-complete.
- `footer.html`: Global responsive footer, brand intro, explore topic links, company pages links, reading recommendations, copyright, and back-to-top button.
- `layout.html`: Reference global layout architecture shell.
- `breadcrumbs.html`: Reusable breadcrumbs component pattern.
- `card.html`: Reusable article and content card component pattern.
- `cta-banner.html`: Reusable call-to-action newsletter/subscription banner pattern.

## Global Design System

All shared design tokens, layout primitives, and component styles live in `assets/css/custom-style.css`:
- **Containers**: `.falcon-container`, `.falcon-container-narrow`, `.falcon-container-article`
- **Spacing Scale**: CSS variables `--space-1` through `--space-20` (4px to 80px)
- **Typography**: Fluid type scale `--text-xs` through `--text-5xl`, line heights, font weights (`DM Sans`)
- **Buttons**: `.falcon-btn`, `.falcon-btn-primary`, `.falcon-btn-secondary`, `.falcon-btn-outline`, `.falcon-btn-sm`, `.falcon-btn-lg`
- **Cards**: `.post-card`, `.falcon-card`
- **Blog Components**: `.category-badge`, `.falcon-article-box`, `.falcon-post-meta`, `.entry-content`
- **CTA Components**: `.falcon-cta`, `.falcon-cta-eyebrow`, `.falcon-cta-title`, `.falcon-cta-description`, `.falcon-newsletter-form`

## Scripts Architecture

Shared scripts are loaded once globally rather than duplicated in page HTML:
- `assets/js/search-results.js`: Renders search result items cleanly.
- `assets/js/falcon-search-data.js`: Search index containing all 155 articles.
- `assets/js/falcon-core.js`: Live search filtering, modal open/close, dark/light theme persistence, mobile menu toggling, and breaking news carousel.

## Build and Verification

To compile and propagate changes across all pages:
```sh
python3 scripts/build.py
python3 scripts/check_site.py
```
