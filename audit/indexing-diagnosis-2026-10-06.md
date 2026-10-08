# Indexing investigation — 6 October 2026

## Conclusion

The main historical problem is indexing selection, not a sitewide crawl block. Google has fetched affected articles successfully but has not indexed them. The current site is technically accessible. Content usefulness, credibility, and overlapping archive pages need attention. These are plausible contributors, not a confirmed algorithmic diagnosis. The report does not establish that every excluded URL was previously indexed.

## Search Console evidence

Property: https://thefitnessfalcon.com/. Page Indexing report last updated 21 September 2026, before the 30 September URL migration.

| Status | URLs |
|---|---:|
| Indexed | 102 |
| Crawled — currently not indexed | 129 |
| Excluded by noindex | 29 |
| Not found (404) | 9 |
| Discovered — currently not indexed | 5 |
| Page with redirect | 2 |
| Soft 404 | 1 |
| Blocked by robots.txt | 0 |
| Redirect error | 0 |

The 129 crawled exclusions include 83 root article URL variants, 37 tag URLs (including feeds), and other archive/feed URLs. Exclusions are not all lost articles. The noindex list consists of 27 feeds and 2 date archive URLs; no main article URL appears in that list.

Inspected example: `/brain-boosting-nutrition-best-foods-to-improve-focus-and-memory/`.

- Status: Crawled — currently not indexed.
- Last crawl: 4 August 2026, 00:26:11, Googlebot smartphone.
- Crawl allowed: Yes. Fetch: Successful. Indexing allowed: Yes.
- User-declared canonical: inspected root article URL.
- Google-selected canonical: Inspected URL.
- No referring sitemap or referring page detected in this inspection. This does not prove that no links exist.

Manual Actions and Security Issues reports: No issues detected.

## Current live crawl

Full response evidence: `indexing-live-2026-10-06.json`.

- All 324 sitemap URLs returned 200, stayed on their submitted URLs, declared matching canonical URLs, and had no detected meta/header noindex.
- Sitemap contains 160 articles, the blog archive, 136 tag archives, 19 categories, 3 authors, 4 static pages, and the homepage.
- robots.txt permits article crawling; only search and the custom 404 page are disallowed.
- Existing legacy article paths tested against current articles reach their `/blogs/<slug>/` destinations. The five root paths without redirects belong to recently added articles; their grouped destinations work, and root versions may never have existed.
- Sample old article response is a 301 to its grouped article destination.
- Unknown URLs return genuine 404 responses.
- www homepage and explicit `/index.html` URLs return 200 copies with non-www, clean canonicals. Add permanent redirects to consolidate these variants; their existence alone does not prove the cause of exclusions.
- `/about-us/` returns 404; the repository documents its removal.
- Search Console example `/10-common-panic-attack-symptoms-you-should-never-ignore/` now returns 404. Review the old content inventory to determine whether valuable articles were omitted or intentionally retired.
- Old `/blog/page/2/` returns 404. Legacy archive pagination was not fully mapped during the migration.

## Sitemap issue

Search Console lists the old WordPress sitemap setup:

- `/sitemap.xml`: last recorded read 1 March 2026; shown as a sitemap index with 215 discovered pages. The current file is a URL set with 324 entries.
- `/sitemap_index.xml`: last read 20 January 2026; currently returns 404.
- `/post-sitemap.xml`: last read 7 March 2026; currently returns 404.
- `/page-sitemap.xml`: Couldn't fetch, last read 24 September 2026; currently 404.
- `/category-sitemap.xml`: Couldn't fetch, last read 25 September 2026; currently 404.

The stale/failed sitemap reports are a discovery issue, but cannot alone explain articles that Google demonstrably crawled successfully. Re-submit the working current sitemap once, then monitor the last-read date and discovered URLs. Restore appropriate compatibility for obsolete sitemap endpoints or clean up obsolete submissions after the working replacement is confirmed.

## Content observations and hypotheses

- The inspected brain nutrition article gives broad health advice but its body lacks external citations. Its author is Alex, whose displayed bio describes a fitness technology and wearables specialist. Add relevant, truthful expertise and named qualified review where appropriate for health topics.
- Article HTML retains copied conversation markup (`data-message-author-role="assistant"`, `data-message-model-slug`). This shows copied editor markup; it is not evidence of an automatic penalty. Assess factual accuracy, original value, and sourcing rather than treating AI markup as an indexing blocker.
- The Team page repeats Florence Boyle, Joseph Mackey, Wendy McHugh, and Will Hernandez across eight profiles with differing roles. Verify and replace template-like profiles with accurate people, biographies, and credentials. Do not invent qualifications.
- An About page, ownership information, and an editorial/review policy would improve transparency. The missing About page is not itself a crawl block.
- 136 tag archives overlap the 160 articles. Search Console already excludes many tag URLs. Review archives for distinct value; consider noindex for low-value redundant archives and omit those from the sitemap while retaining useful article discovery links. Do not indiscriminately delete or block all tags.
- Sitemap generator stamps archive/static lastmod values with each build's date. Use actual significant modification dates or omit dates that cannot be maintained accurately.

## Recommended order

1. Reconcile the current article inventory against old Search Console/WordPress URLs; restore useful omitted articles or redirect only to close replacements. Keep deliberate removals as 404/410.
2. Re-submit `/sitemap.xml`, confirm successful fresh processing, and resolve obsolete sitemap submissions/endpoints.
3. Consolidate www and index.html variants with permanent redirects; complete relevant legacy route mappings. Keep stable URLs thereafter.
4. Improve a small priority group of excluded articles with original practical value, reliable references, accurate authorship, and appropriate expert review. Correct Team/About/editorial transparency.
5. Review thin/overlapping tag archives and sitemap lastmod accuracy.
6. Inspect the new grouped URLs, run live tests, and request indexing for materially improved priority pages. Monitor actual indexing and impressions rather than expecting all feeds/archives to be indexed.

No production files, Search Console submissions, indexing requests, or site settings were changed in this investigation.

## References

- https://support.google.com/webmasters/answer/7440203
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
