# Indexing fixes — 6 October 2026

## Evidence and scope

Search Console's 21 September report predates the recent URL migration. It showed 129 crawled but not indexed URLs, including old article routes and tag archives; 29 noindex exclusions were predominantly feeds. The inspected brain nutrition article had a successful historical crawl and no crawl/indexing prohibition. No manual action or security issue was reported by Search Console. These facts do not establish a single algorithmic cause for every excluded page.

## Changes

- Generated 997 permanent compatibility redirects for old articles, static pages, author routes, blog pagination, and sitemap aliases. Normalized the www host and explicit index.html variants.
- Rebuilt the main sitemap with 202 indexable canonical URLs, including all 160 current articles. Restored the four previously submitted WordPress sitemap paths.
- Kept tag archives accessible to crawlers with noindex,follow; excluded them from the sitemap. Excluded author pagination from indexing.
- Added accurate About and editorial policy pages. Used the confirmed owner name Dinesh Jeengar; replaced unconfirmed personal contributor profiles with a publication byline and removed invented credential badges.
- Rewrote six articles containing unsupported health/fitness promises and added source/context notes to nine others. Removed copied editor interface markup while preserving semantic article content and navigation. This was not a clinical review of the entire article collection.
- Rebuilt the search index and updated shared navigation/footer links.

## Verification

- Nine unit tests passed.
- Site checks passed: 377 canonical pages, 160 search entries, no local link errors.
- All 997 generated redirects passed against Apache; www normalization was also checked.
- Backup before local changes: `/private/tmp/falcon-before-indexing-fixes-20261006.zip`.
- Live .htaccess backup: `/private/tmp/falcon-remote-htaccess-before-fixes.txt`.

## Recovery expectations

Google must recrawl the changed URLs and reassess their content. A successful deployment or sitemap submission does not guarantee indexing. Legitimately retired URLs remain 404 rather than redirecting visitors to unrelated content. Search Console's historical exclusion totals will not immediately reflect these changes.

Deployment completed: 572 public files uploaded without failures. All 202 sitemap URLs returned HTTP 200 with correct canonical URLs and no indexing prohibition. Legacy routes reached their intended destinations; unknown URLs still returned 404. All restored compatibility sitemap files returned HTTP 200. Google Search Console confirmed the main sitemap submission and accepted the corrected brain nutrition article and new About page into its priority crawl queue. Full response metadata is recorded in `indexing-live-after-fixes-2026-10-06.json`.
