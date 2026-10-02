# Website source audit

Audited the current local website: 192 canonical pages, shared components, content JSON, scripts, hosting rules, and WordPress exports. No browser was used for this audit. No website fixes were applied. Counts represent the source snapshot reviewed; other workspace changes may continue independently.

## High priority

| Issue | Evidence | Impact and recommended fix |
|---|---|---|
| Newsletter reports success without submitting | `components/newsletter-block.html:6` calls `preventDefault()` and `alert('Subscribed successfully!')`. Present on 174 pages. | Emails are not saved or subscribed. Connect a real subscription endpoint and show success only after it accepts the request. |
| Contact form is missing | `pages/contact-us/index.html:240` contains the literal `[contact-form-7 id="1032" title="Contact form 1"]` shortcode. | A static HTML server cannot turn this into a form. Replace it with a working form and an actual submission endpoint. |
| Publication dates were overwritten during import | `scripts/extract_posts.py:74` searches the entire page for the first calendar icon; the shared top bar comes before article metadata. All 155 posts have `published_iso: 2026-09-30`; 150 disagree with the WordPress export. | Article dates, structured data, archive ordering, and recent-post selection are misleading. Restore original dates from the export and scope extraction to article metadata. Keep genuine update dates separate. |
| Team page links to theme demo profiles | `pages/team/index.html:250` and surrounding cards link to `itcroctheme.com/wp/demos/themes/benqu/benqu_team/...`. | Readers leave the site for theme-demo profiles. Replace demo content with verified contributor profiles, or remove the demo cards. |
| WhatsApp contact URL is malformed | `pages/write-for-us/index.html:261` uses `href="http://+91 8561092679"`. | This is not a valid WhatsApp contact link. Use the intended WhatsApp URL or a `tel:` link, and confirm which action the text should describe. |

## Medium priority

| Issue | Evidence | Impact and recommended fix |
|---|---|---|
| Invalid/missing canonical URLs | Homepage canonical is `javascript:void(0)`; all four landing pages lack canonical tags. | Supply one absolute canonical URL per page. Blog/category canonical tags passed this check. |
| Homepage contains an undefined analytics call | `index.html:304` calls `fbq('track', 'PageView')`; no definition or Meta Pixel loader exists in the reviewed source. | That inline script throws a ReferenceError unless an external environment injects `fbq`. Remove obsolete tracking or load and initialize it correctly. Other script elements can still run after this error. |
| Keyboard controls and modal behavior are incomplete | `components/header.html:8` uses an unfocusable `<i>` as the search-close control. The theme control has `role="button"` and `tabindex="0"`, but `assets/js/falcon-core.js:149` binds only click. Search/mobile drawers lack a focus trap and focus restoration. | Use native buttons, keyboard activation, appropriate dialog semantics, and predictable focus management. |
| Global initialization assumes localStorage is available | `assets/js/falcon-core.js:118` reads storage without a guard. | If storage access throws, initialization stops before subsequent mobile/menu/ticker handlers register. Use a guarded storage helper with a fallback. This is a conditional failure, not reproduced in a browser. |
| Duplicate IDs and multiple H1s | Duplicate IDs on `best-lifestyle-habits-for-longevity-and-healthy-aging` (`final-thoughts`, `sources`) and `chia-seeds-health-benefits-sources-and-supplements`. Two H1s on `top-6-gyms-in-miami`, `what-is-zumba-workout-pros-cons-and-how-it-works`, and Privacy Policy. | IDs must be unique so anchor navigation is unambiguous. Keep a single main page heading and downgrade embedded article/page headings. The TOC compiler only deduplicates generated H2 IDs; it does not account for existing section IDs. |
| Large image asset and missing dimensions | `assets/images/2024-New-Year-Resolutions-for-Your-Gym-1.svg` is 8,340,862 bytes. 1,835 image elements across 188 pages omit width/height. | Optimize the oversized SVG and reserve image space. Missing dimensions can contribute to layout shifts, though some current CSS already sets aspect ratios. Actual performance/CLS was not measured. |
| Import/archive files are inside the served project root | `old-website/` is about 56 MB, including WordPress XML exports, full legacy pages, and retired tools. `.htaccess` does not deny access to this folder. | If the whole project is deployed as the document root, these files can be fetched directly and legacy pages remain accessible. Exclude archives, audit files, content sources, and build tools from deployment or deny web access to nonpublic files. Actual production exposure was not tested. |

## Lower priority and maintenance

- `robots.txt` and a sitemap are absent. This does not prevent indexing, but a generated sitemap would help discovery of the 192 routes and pagination.
- One image on `blogs/top-5-gyms-in-new-york-city-2026/index.html` has no alt attribute. Give it useful alt text, or an explicit empty alt if decorative.
- The homepage loads both legacy `assets/js/scripts.js` and `falcon-core.js`; both manage mobile navigation, sticky headers, and themes. Consolidate ownership to avoid conflicting event handlers. The legacy theme loader also dereferences `toggleSwitch.checked` without a null guard when a saved dark theme exists.
- The top-bar styles and core script are versioned, but most other shared assets are unversioned. Apply a consistent asset-versioning policy rather than requiring visitors to clear caches after changes.
- README still says 180 canonical pages; the current build has 192 after archive pagination. Keep generated counts out of static documentation or refresh them during builds.
- The existing checker verifies file destinations and structural counts, but does not detect nonfunctional forms, malformed external links, canonical errors, duplicate IDs, incorrect dates, or runtime behavior. Extend checks to cover the confirmed failures above.

## Checks that passed

- 26,535 local references and redirect destinations resolve to files.
- All 640 compatibility mappings have existing destination pages. These are source checks; actual HTTP redirect behavior depends on hosting configuration.
- All 155 search entries have existing article pages and thumbnail files; titles agree with current content JSON.
- No missing local fragment targets were found. Duplicate IDs still make some targets ambiguous.
- Syntax checks passed for nine external JavaScript files and seven executable inline scripts. Syntax validation does not establish runtime correctness.
- Every canonical page has one site header and one site footer.
- The deleted About Us page and removed sidebar drawer remain absent.

## Recommended order

1. Restore original article dates and correct the import logic.
2. Implement real contact/newsletter submission and repair the WhatsApp link.
3. Remove theme-demo profiles and obsolete analytics.
4. Correct landing/homepage canonical tags, heading structure, and duplicate IDs.
5. Complete keyboard/modal behavior and resilient storage handling.
6. Optimize images and define a deployment allowlist plus consistent asset versioning.

Machine-readable findings: `audit/site-audit.json`. Basic route validation: `audit/validation.json`.
