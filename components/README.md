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
- `post-template.html`: Single master reusable blog post template for the entire website. Renders all 155 existing articles and future articles with zero duplicated layout code.
- `layout.html`: Reference global layout architecture shell.
- `breadcrumbs.html`: Reusable breadcrumbs component pattern.
- `card.html`: Reusable article and content card component pattern.
- `cta-banner.html`: Reusable call-to-action newsletter/subscription banner pattern.

## Blog Post Architecture & Content Storage

To eliminate layout duplication across articles:
- **Master Template**: `components/post-template.html` defines the layout, dynamic SEO tags, schema structured data, reading progress bar, table of contents, article meta row, author box, social sharing bar, post pagination (prev/next), related articles grid, and sticky sidebar.
- **Content Store**: Post data and body HTML are stored cleanly in `content/posts/<slug>.json`.
- **Dynamic SEO per Article**:
  - Meta title, description, robots directives
  - Canonical URL (`https://thefitnessfalcon.com/blogs/<slug>/`)
  - Open Graph tags (`og:type="article"`, `og:title`, `og:description`, `og:url`, `og:image`, `article:published_time`, `article:modified_time`, `article:author`, `article:section`)
  - Twitter card tags (`twitter:card="summary_large_image"`)
  - Schema.org JSON-LD structured data (`BlogPosting` and `BreadcrumbList`)
- **Rich Elements Support**:
  - Automatic Table of Contents (`.falcon-toc`) for articles with 3+ headings
  - Responsive tables wrapped in `.falcon-table-wrapper` with mobile horizontal scroll
  - Styled quotes (`blockquote`), video embeds (`.falcon-video-wrapper`), and captions
  - Social sharing toolbar with instant clipboard copy for article URL
  - Contextual Related Articles (3 cards by category) & Chronological Previous/Next post pagination
  - Sticky sidebar with recent posts, category counts, and newsletter subscription

## Build and Post Management

To compile and propagate changes across all pages and blog posts:
```sh
# 1. Compile all posts and propagate global header/footer
python3 scripts/build.py

# 2. Verify all routes, references, and search entries (must be 0 errors)
python3 scripts/check_site.py

# 3. Create a new future blog article
python3 scripts/new_post.py --title "New Health Guide" --category "Health" --author "Dinesh"
```

