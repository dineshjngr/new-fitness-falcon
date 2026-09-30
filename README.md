# The Fitness Falcon

Static website with grouped blog and landing pages.

## Layout

- `index.html`: homepage.
- `blogs/index.html`: all-articles archive.
- `blogs/<article-slug>/index.html`: 155 blog articles.
- `pages/<page-slug>/index.html`: Contact Us, Privacy Policy, Team, and Write For Us.
- `category/<category-slug>/index.html`: 19 category archives.
- `assets/`: shared images, design system styles (`custom-style.css`, `footer.css`), shared scripts (`falcon-core.js`, `falcon-search-data.js`, `search-results.js`), fonts, and the search index.
- `components/`: shared global header (`header.html`), footer (`footer.html`), layout shell (`layout.html`), and reusable component patterns (breadcrumbs, cards, CTA banners).
- `scripts/`: build, validation, architecture migration, and local preview commands.
- `audit/`: link validation, migration history, backup locations, and route mappings.
- `old-website/`: WordPress exports, archived flat pages/redirects, and retired import tools.

All 180 canonical pages share:
- 1 shared global header (`components/header.html`)
- 1 shared global footer (`components/footer.html`)
- 1 global layout system (`<main id="main-content" class="falcon-main-layout">`)
- Shared design system & tokens (`assets/css/custom-style.css`)
- Shared search index and core interactions (`assets/js/falcon-search-data.js`, `assets/js/falcon-core.js`)

Individual pages only provide their own page-specific content and `<head>` SEO metadata. The About Us page remains removed.

## Build, check, and preview

```sh
python3 scripts/build.py
python3 scripts/check_site.py
python3 scripts/serve.py --port 8000
```

The preview server handles compatibility redirects; a plain `python3 -m http.server` does not read hosting redirect files.

## URL compatibility

New article URLs use `/blogs/<article-slug>/`; landing pages use `/pages/<page-slug>/`. All site links and search results point directly to these routes.

Old `/article-slug/`, `/article-slug/index.html`, and `/article-slug.html` URLs redirect to their grouped route. The old `/blog/` archive redirects to `/blogs/`. Landing-page URLs have equivalent redirects.

Publish `.htaccess` for Apache hosting with mod_rewrite enabled, or `_redirects` for hosting that supports that format (such as Netlify). Other hosts need the mappings in `audit/routes.json` configured in their redirect system. Do not deploy only the HTML files and omit redirect configuration if old URL compatibility is required.

Migration scripts (`organize.py` and `group_pages.py`) are already applied and should not be rerun. Archived import tools can recreate obsolete pages; retain them for reference only.

Validation covers local page/resource references, CSS dependencies, redirect destinations, and search entries. It does not establish external-site availability or browser-rendered behavior. Original content and backup ZIP paths are retained in the audit reports.
