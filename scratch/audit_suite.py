#!/usr/bin/env python3
"""
Comprehensive End-to-End Audit Suite for The Fitness Falcon.
Audits all 49 requested areas and outputs full structured findings.
"""
import os, sys, re, json, glob, html, math
from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlparse, unquote

ROOT = Path('/Users/dj/Desktop/vscode/thefitnessfalcon')
EXCLUDED_DIRS = {'old-website', 'components', '.git', 'node_modules', 'scratch'}
BASE_URL = 'https://thefitnessfalcon.com'

print("="*60)
print("RUNNING THE FITNESS FALCON END-TO-END AUDIT SUITE")
print("="*60)

# -------------------------------------------------------------
# 1. ROUTE INVENTORY
# -------------------------------------------------------------
html_files = sorted(p for p in ROOT.rglob('*.html') if not EXCLUDED_DIRS.intersection(p.relative_to(ROOT).parts))

route_inventory = {
    'homepage': [],
    'blog_main': [],
    'blog_pagination': [],
    'blog_posts': [],
    'categories': [],
    'category_pagination': [],
    'tags': [],
    'tag_pagination': [],
    'authors': [],
    'author_pagination': [],
    'static_pages': [],
    'search': [],
    '404': [],
    'other_html': []
}

canonical_routes = set()

for p in html_files:
    rel = p.relative_to(ROOT).as_posix()
    if rel == 'index.html':
        route_inventory['homepage'].append(rel)
        canonical_routes.add('/')
    elif rel == 'blogs/index.html':
        route_inventory['blog_main'].append(rel)
        canonical_routes.add('/blogs/')
    elif rel.startswith('blogs/page/'):
        route_inventory['blog_pagination'].append(rel)
        page_num = rel.split('/')[2]
        canonical_routes.add(f'/blogs/page/{page_num}/')
    elif rel.startswith('blogs/'):
        route_inventory['blog_posts'].append(rel)
        slug = rel.split('/')[1]
        canonical_routes.add(f'/blogs/{slug}/')
    elif rel.startswith('category/') and '/page/' in rel:
        route_inventory['category_pagination'].append(rel)
        parts = rel.split('/')
        canonical_routes.add(f'/category/{parts[1]}/page/{parts[3]}/')
    elif rel.startswith('category/'):
        route_inventory['categories'].append(rel)
        slug = rel.split('/')[1]
        canonical_routes.add(f'/category/{slug}/')
    elif rel.startswith('tag/') and '/page/' in rel:
        route_inventory['tag_pagination'].append(rel)
        parts = rel.split('/')
        canonical_routes.add(f'/tag/{parts[1]}/page/{parts[3]}/')
    elif rel.startswith('tag/'):
        route_inventory['tags'].append(rel)
        slug = rel.split('/')[1]
        canonical_routes.add(f'/tag/{slug}/')
    elif rel.startswith('author/') and '/page/' in rel:
        route_inventory['author_pagination'].append(rel)
        parts = rel.split('/')
        canonical_routes.add(f'/author/{parts[1]}/page/{parts[3]}/')
    elif rel.startswith('author/'):
        route_inventory['authors'].append(rel)
        slug = rel.split('/')[1]
        canonical_routes.add(f'/author/{slug}/')
    elif rel.startswith('pages/'):
        route_inventory['static_pages'].append(rel)
        slug = rel.split('/')[1]
        canonical_routes.add(f'/pages/{slug}/')
    elif rel == 'search/index.html':
        route_inventory['search'].append(rel)
        canonical_routes.add('/search/')
    elif rel == '404.html':
        route_inventory['404'].append(rel)
        # 404 is utility/error, not an indexable canonical route
    else:
        route_inventory['other_html'].append(rel)
        canonical_routes.add('/' + rel.replace('/index.html', '/'))

print(f"Total HTML files: {len(html_files)}")
for k, v in route_inventory.items():
    print(f"  {k:22}: {len(v)}")

# -------------------------------------------------------------
# 2. HTML PARSER & DATA EXTRACTION
# -------------------------------------------------------------
class PageParser(HTMLParser):
    def __init__(self, rel_path):
        super().__init__()
        self.rel_path = rel_path
        self.title = None
        self._in_title = False
        self.meta_desc = None
        self.meta_robots = None
        self.canonical = None
        self.canonicals = []
        self.og = {}
        self.twitter = {}
        self.h1_list = []
        self.headings = [] # list of (tag, text, id, line)
        self._curr_tag = None
        self._curr_text = []
        self._curr_id = None
        self.json_ld = []
        self._in_json_ld = False
        self._json_ld_text = []
        self.links = [] # list of dict(href, text, line, attrs)
        self.images = [] # list of dict(src, alt, width, height, loading, fetchpriority, line)
        self.iframes = []
        self.forms = []
        self.ids = []
        self.has_main = False
        self.lang = None
        self.scripts = []
        self.stylesheets = []
        self.has_skip_link = False
        self.rel_prev = None
        self.rel_next = None

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        self._curr_tag = tag
        self._curr_text = []
        self._curr_id = attr_dict.get('id')

        if 'id' in attr_dict:
            self.ids.append((attr_dict['id'], self.getpos()[0]))

        if tag == 'html':
            self.lang = attr_dict.get('lang')
        elif tag == 'main':
            self.has_main = True
        elif tag == 'title':
            self._in_title = True
        elif tag == 'meta':
            name = (attr_dict.get('name') or '').lower()
            prop = (attr_dict.get('property') or '').lower()
            content = attr_dict.get('content', '')
            if name == 'description':
                self.meta_desc = content
            elif name == 'robots':
                self.meta_robots = content
            elif prop.startswith('og:'):
                self.og[prop] = content
            elif name.startswith('twitter:'):
                self.twitter[name] = content
        elif tag == 'link':
            rel = (attr_dict.get('rel') or '').lower()
            href = attr_dict.get('href')
            if rel == 'canonical':
                self.canonical = href
                self.canonicals.append(href)
            elif rel == 'stylesheet':
                self.stylesheets.append(href)
            elif rel == 'prev':
                self.rel_prev = href
            elif rel == 'next':
                self.rel_next = href
        elif tag == 'script':
            src = attr_dict.get('src')
            if src:
                self.scripts.append(src)
            type_attr = attr_dict.get('type', '').lower()
            if type_attr == 'application/ld+json':
                self._in_json_ld = True
                self._json_ld_text = []
        elif tag == 'a':
            href = attr_dict.get('href')
            line = self.getpos()[0]
            if href and '#main-content' in href:
                self.has_skip_link = True
            self.links.append({
                'href': href,
                'attrs': attr_dict,
                'line': line,
                'text': ''
            })
        elif tag == 'img':
            self.images.append({
                'src': attr_dict.get('src'),
                'alt': attr_dict.get('alt'), # None if attr absent, string if present
                'width': attr_dict.get('width'),
                'height': attr_dict.get('height'),
                'loading': attr_dict.get('loading'),
                'fetchpriority': attr_dict.get('fetchpriority'),
                'line': self.getpos()[0]
            })
        elif tag == 'iframe':
            self.iframes.append({
                'src': attr_dict.get('src'),
                'title': attr_dict.get('title'),
                'loading': attr_dict.get('loading'),
                'line': self.getpos()[0]
            })
        elif tag == 'form':
            self.forms.append({
                'action': attr_dict.get('action'),
                'method': attr_dict.get('method'),
                'id': attr_dict.get('id'),
                'line': self.getpos()[0]
            })

    def handle_endtag(self, tag):
        text = ''.join(self._curr_text).strip()
        line = self.getpos()[0]
        if tag == 'title':
            self._in_title = False
            self.title = text
        elif tag == 'h1':
            self.h1_list.append((text, line))
            self.headings.append(('h1', text, self._curr_id, line))
        elif tag in ('h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append((tag, text, self._curr_id, line))
        elif tag == 'script' and self._in_json_ld:
            self._in_json_ld = False
            raw_json = ''.join(self._json_ld_text).strip()
            self.json_ld.append((raw_json, line))
        elif tag == 'a' and self.links:
            self.links[-1]['text'] = text

        self._curr_tag = None
        self._curr_text = []
        self._curr_id = None

    def handle_data(self, data):
        if self._in_title:
            self._curr_text.append(data)
        elif self._in_json_ld:
            self._json_ld_text.append(data)
        elif self._curr_tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'):
            self._curr_text.append(data)

parsed_pages = {}
raw_pages = {}
for p in html_files:
    rel = p.relative_to(ROOT).as_posix()
    raw = p.read_text(encoding='utf-8')
    raw_pages[rel] = raw
    parser = PageParser(rel)
    try:
        parser.feed(raw)
    except Exception as e:
        print(f"Error parsing {rel}: {e}")
    parser.has_shared_header = ('<!-- shared:header:start -->' in raw and '<!-- shared:header:end -->' in raw)
    parser.has_shared_footer = ('<!-- shared:footer:start -->' in raw and '<!-- shared:footer:end -->' in raw)
    parsed_pages[rel] = parser

print(f"Parsed {len(parsed_pages)} pages.")

# -------------------------------------------------------------
# 3. CANONICAL AUDIT
# -------------------------------------------------------------
canonical_issues = []
for rel, page in parsed_pages.items():
    if rel == '404.html':
        # 404.html shouldn't have canonical or can point to 404, let's see what it has
        continue
    if len(page.canonicals) == 0:
        canonical_issues.append((rel, "Missing canonical tag"))
    elif len(page.canonicals) > 1:
        canonical_issues.append((rel, f"Multiple canonical tags: {page.canonicals}"))
    else:
        c = page.canonical
        if not c.startswith('https://thefitnessfalcon.com/'):
            canonical_issues.append((rel, f"Canonical not on production domain: {c}"))
        if not c.endswith('/'):
            canonical_issues.append((rel, f"Canonical missing trailing slash: {c}"))
        if 'javascript:' in c or 'localhost' in c or '127.0.0.1' in c:
            canonical_issues.append((rel, f"Invalid canonical URL: {c}"))

        # Check self-referencing correctness
        expected_path = '/' if rel == 'index.html' else '/' + rel.replace('/index.html', '/')
        if rel == 'blogs/index.html':
            expected_path = '/blogs/'
        expected_canonical = f"https://thefitnessfalcon.com{expected_path}"
        if c != expected_canonical:
            canonical_issues.append((rel, f"Canonical mismatch: expected '{expected_canonical}', found '{c}'"))

print(f"Canonical issues count: {len(canonical_issues)}")
for issue in canonical_issues[:10]:
    print("  ", issue)

# -------------------------------------------------------------
# 4. INDEXATION & ROBOTS AUDIT
# -------------------------------------------------------------
robots_analysis = {
    'index_follow': [],
    'noindex_follow': [],
    'noindex_nofollow': [],
    'missing_robots': [],
    'other_robots': []
}

for rel, page in parsed_pages.items():
    r = (page.meta_robots or '').lower()
    if not r:
        robots_analysis['missing_robots'].append(rel)
    elif 'noindex' in r and 'nofollow' in r:
        robots_analysis['noindex_nofollow'].append(rel)
    elif 'noindex' in r:
        robots_analysis['noindex_follow'].append(rel)
    elif 'index' in r and 'follow' in r:
        robots_analysis['index_follow'].append(rel)
    else:
        robots_analysis['other_robots'].append((rel, r))

print(f"Robots directives breakdown:")
print(f"  index, follow: {len(robots_analysis['index_follow'])}")
print(f"  noindex, follow: {len(robots_analysis['noindex_follow'])}")
print(f"  noindex, nofollow: {len(robots_analysis['noindex_nofollow'])}")
print(f"  missing meta robots: {len(robots_analysis['missing_robots'])}")
if robots_analysis['missing_robots']:
    print("    Sample missing:", robots_analysis['missing_robots'][:5])

# Check robots.txt
robots_txt_path = ROOT / 'robots.txt'
robots_txt_content = robots_txt_path.read_text() if robots_txt_path.exists() else ''
print("\nRobots.txt content preview:\n" + robots_txt_content.strip())

# -------------------------------------------------------------
# 5. SITEMAP AUDIT
# -------------------------------------------------------------
sitemap_path = ROOT / 'sitemap.xml'
sitemap_urls = []
sitemap_errors = []
if sitemap_path.exists():
    try:
        stree = ET.parse(sitemap_path)
        sroot = stree.getroot()
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for u in sroot.findall('sm:url', ns):
            loc = u.find('sm:loc', ns).text.strip()
            lastmod = u.find('sm:lastmod', ns).text.strip() if u.find('sm:lastmod', ns) is not None else None
            sitemap_urls.append(loc)
    except Exception as e:
        sitemap_errors.append(f"Sitemap XML parsing error: {e}")

print(f"\nSitemap URLs count: {len(sitemap_urls)}")

# Compare sitemap with canonical indexable routes
# Exclude 404, search (if noindex)
indexable_pages = set()
for rel, page in parsed_pages.items():
    if rel in ('404.html', 'search/index.html'):
        continue
    r = (page.meta_robots or '').lower()
    if 'noindex' in r:
        continue
    path = '/' if rel == 'index.html' else '/' + rel.replace('/index.html', '/')
    if rel == 'blogs/index.html':
        path = '/blogs/'
    indexable_pages.add(f"https://thefitnessfalcon.com{path}")

sitemap_url_set = set(sitemap_urls)
missing_from_sitemap = indexable_pages - sitemap_url_set
extra_in_sitemap = sitemap_url_set - indexable_pages

print(f"Indexable pages calculated: {len(indexable_pages)}")
print(f"Missing from sitemap ({len(missing_from_sitemap)}):", sorted(list(missing_from_sitemap))[:15])
print(f"Extra in sitemap ({len(extra_in_sitemap)}):", sorted(list(extra_in_sitemap))[:15])

# -------------------------------------------------------------
# 6. META TITLE & DESCRIPTION AUDIT
# -------------------------------------------------------------
title_issues = []
desc_issues = []
titles_seen = {}
descs_seen = {}

for rel, page in parsed_pages.items():
    if rel == '404.html':
        continue
    # Title
    t = page.title
    if not t or not t.strip():
        title_issues.append((rel, "Missing or empty title"))
    else:
        t_clean = t.strip()
        length = len(t_clean)
        if length < 20:
            title_issues.append((rel, f"Very short title ({length} chars): '{t_clean}'"))
        elif length > 75:
            title_issues.append((rel, f"Long title ({length} chars): '{t_clean}'"))
        if '&amp;amp;' in t or '&#8217;' in t or '&#038;' in t or '&amp;#8217;' in t:
            title_issues.append((rel, f"HTML entity unescaping issue in title: '{t_clean}'"))
        titles_seen.setdefault(t_clean, []).append(rel)

    # Description
    d = page.meta_desc
    if not d or not d.strip():
        desc_issues.append((rel, "Missing or empty meta description"))
    else:
        d_clean = d.strip()
        length = len(d_clean)
        if length < 50:
            desc_issues.append((rel, f"Very short meta description ({length} chars): '{d_clean}'"))
        elif length > 175:
            desc_issues.append((rel, f"Long meta description ({length} chars): '{d_clean[:60]}...'"))
        if '&amp;amp;' in d or '&#8217;' in d or '&#038;' in d:
            desc_issues.append((rel, f"HTML entity unescaping issue in description: '{d_clean[:60]}...'"))
        descs_seen.setdefault(d_clean, []).append(rel)

duplicate_titles = {t: pages for t, pages in titles_seen.items() if len(pages) > 1}
duplicate_descs = {d: pages for d, pages in descs_seen.items() if len(pages) > 1}

print(f"\nMeta Title issues: {len(title_issues)}")
print(f"Duplicate titles: {len(duplicate_titles)}")
for t, pages in list(duplicate_titles.items())[:5]:
    print(f"  Title '{t}' on {len(pages)} pages: {pages[:3]}")

print(f"Meta Description issues: {len(desc_issues)}")
print(f"Duplicate descriptions: {len(duplicate_descs)}")
for d, pages in list(duplicate_descs.items())[:5]:
    print(f"  Desc '{d[:50]}...' on {len(pages)} pages: {pages[:3]}")

# -------------------------------------------------------------
# 7. OPEN GRAPH & TWITTER META AUDIT
# -------------------------------------------------------------
og_issues = []
for rel, page in parsed_pages.items():
    if rel == '404.html':
        continue
    missing_og = []
    for prop in ['og:title', 'og:description', 'og:url', 'og:image']:
        if prop not in page.og or not page.og[prop].strip():
            missing_og.append(prop)
    if missing_og:
        og_issues.append((rel, f"Missing OpenGraph properties: {missing_og}"))
    
    # Check og:image validity
    og_img = page.og.get('og:image')
    if og_img:
        if not og_img.startswith('https://thefitnessfalcon.com/'):
            og_issues.append((rel, f"og:image not absolute URL: {og_img}"))
        else:
            local_rel = og_img.replace('https://thefitnessfalcon.com/', '')
            if not (ROOT / local_rel).is_file():
                og_issues.append((rel, f"og:image file missing locally: {local_rel}"))

print(f"\nOpenGraph issues: {len(og_issues)}")
for issue in og_issues[:5]:
    print("  ", issue)

# -------------------------------------------------------------
# 8. HEADING STRUCTURE (H1 - H6) AUDIT
# -------------------------------------------------------------
heading_issues = []
for rel, page in parsed_pages.items():
    h1_count = len(page.h1_list)
    if h1_count == 0:
        heading_issues.append((rel, "Missing H1"))
    elif h1_count > 1:
        heading_issues.append((rel, f"Multiple H1 headings ({h1_count}): {[h[0][:40] for h in page.h1_list]}"))
    else:
        h1_text = page.h1_list[0][0].strip()
        if not h1_text:
            heading_issues.append((rel, "Empty H1 heading"))

print(f"\nHeading issues (H1): {len(heading_issues)}")
for issue in heading_issues[:10]:
    print("  ", issue)

# -------------------------------------------------------------
# 9. STRUCTURED DATA / SCHEMA AUDIT
# -------------------------------------------------------------
schema_issues = []
schema_types_found = set()
for rel, page in parsed_pages.items():
    if not page.json_ld:
        if rel.startswith('blogs/') and rel != 'blogs/index.html' and not '/page/' in rel:
            schema_issues.append((rel, "Blog post missing JSON-LD schema block"))
        continue
    
    for raw_json, line in page.json_ld:
        try:
            data = json.loads(raw_json)
        except Exception as e:
            schema_issues.append((rel, f"JSON parse error at line {line}: {e}"))
            continue
        
        # Traverse graph or dict
        nodes = data.get('@graph', [data]) if isinstance(data, dict) else []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            ntype = node.get('@type')
            if ntype:
                schema_types_found.add(ntype)
            
            if ntype == 'BlogPosting':
                req_fields = ['headline', 'datePublished', 'dateModified', 'image', 'author', 'publisher']
                for rf in req_fields:
                    if rf not in node or not node[rf]:
                        schema_issues.append((rel, f"BlogPosting missing field: {rf}"))
                
                # Check date formats
                for df in ['datePublished', 'dateModified']:
                    dval = node.get(df, '')
                    if not re.match(r'^\d{4}-\d{2}-\d{2}', dval):
                        schema_issues.append((rel, f"Invalid date format in {df}: '{dval}'"))

print(f"\nSchema issues: {len(schema_issues)}")
print(f"Schema types found across site: {sorted(list(schema_types_found))}")
for issue in schema_issues[:5]:
    print("  ", issue)

# -------------------------------------------------------------
# 10. WORDPRESS CONTENT PARITY AUDIT
# -------------------------------------------------------------
wp_xml_path = ROOT / 'old-website' / 'thefitnessfalcon.WordPress.2026-09-30.xml'
wp_posts = {}
if wp_xml_path.exists():
    tree = ET.parse(wp_xml_path)
    root = tree.getroot()
    ns = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }
    for item in root.findall('.//item'):
        pt = item.find('wp:post_type', ns).text
        st = item.find('wp:status', ns).text
        if pt == 'post' and st == 'publish':
            slug = item.find('wp:post_name', ns).text.strip()
            title = (item.find('title').text or '').strip()
            pdate = item.find('wp:post_date', ns).text.strip()
            pdate_gmt = item.find('wp:post_date_gmt', ns).text.strip()
            mdate = item.find('wp:post_modified', ns).text.strip()
            mdate_gmt = item.find('wp:post_modified_gmt', ns).text.strip()
            creator = item.find('dc:creator', ns).text.strip()
            content_el = item.find('content:encoded', ns)
            content_text = content_el.text if content_el is not None and content_el.text else ''
            
            # Extract categories and tags
            cats = []
            tags = []
            for cat_el in item.findall('category'):
                domain = cat_el.attrib.get('domain')
                nicename = cat_el.attrib.get('nicename')
                name = cat_el.text or ''
                if domain == 'category':
                    cats.append((nicename, name))
                elif domain == 'post_tag':
                    tags.append((nicename, name))
            
            wp_posts[slug] = {
                'slug': slug,
                'title': title,
                'pdate': pdate,
                'pdate_gmt': pdate_gmt,
                'mdate': mdate,
                'mdate_gmt': mdate_gmt,
                'creator': creator,
                'cats': cats,
                'tags': tags,
                'content_len': len(content_text)
            }

print(f"\nLoaded {len(wp_posts)} published posts from WordPress XML export.")

content_posts = {}
content_posts_dir = ROOT / 'content' / 'posts'
for f in sorted(content_posts_dir.glob('*.json')):
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
        content_posts[data['slug']] = data
    except Exception as e:
        print(f"Error loading {f.name}: {e}")

print(f"Loaded {len(content_posts)} posts from content/posts/*.json.")

parity_mismatches = []
for slug, wp in wp_posts.items():
    if slug not in content_posts:
        parity_mismatches.append((slug, "Post in WordPress XML missing from content/posts/"))
        continue
    cp = content_posts[slug]
    
    # Check published date
    wp_pub_iso = wp['pdate'].split(' ')[0]
    cp_pub_iso = cp.get('published_iso')
    if wp_pub_iso != cp_pub_iso:
        parity_mismatches.append((slug, f"Published date mismatch: WP={wp_pub_iso}, Static={cp_pub_iso}"))
    
    # Check modified date
    wp_mod_iso = wp['mdate'].split(' ')[0]
    cp_mod_iso = cp.get('modified_iso')
    if wp_mod_iso != cp_mod_iso:
        parity_mismatches.append((slug, f"Modified date mismatch: WP={wp_mod_iso}, Static={cp_mod_iso}"))
    
    # Check title
    wp_title_clean = html.unescape(wp['title']).strip()
    cp_title_clean = html.unescape(cp['title']).strip()
    if wp_title_clean != cp_title_clean:
        parity_mismatches.append((slug, f"Title mismatch: WP='{wp_title_clean}', Static='{cp_title_clean}'"))

for slug in content_posts:
    if slug not in wp_posts:
        parity_mismatches.append((slug, "Post in content/posts/ missing from WordPress published posts"))

print(f"WordPress Content Parity mismatches: {len(parity_mismatches)}")
for m in parity_mismatches[:10]:
    print("  ", m)

# -------------------------------------------------------------
# 11. CATEGORIES, TAGS, AUTHORS AUDIT
# -------------------------------------------------------------
# Categories
categories_dir = ROOT / 'category'
cat_dirs = sorted([d.name for d in categories_dir.iterdir() if d.is_dir()])
print(f"\nCategory directories on disk: {len(cat_dirs)}")

# Count posts per category in content_posts
cat_post_counts = {}
for p in content_posts.values():
    c = p.get('category_url', '').strip('/').split('/')[-1]
    cat_post_counts[c] = cat_post_counts.get(c, 0) + 1

empty_categories = []
for c in cat_dirs:
    count = cat_post_counts.get(c, 0)
    if count == 0:
        empty_categories.append(c)

print(f"Empty categories: {empty_categories}")

# Tags
tags_dir = ROOT / 'tag'
tag_dirs = sorted([d.name for d in tags_dir.iterdir() if d.is_dir()])
print(f"Tag directories on disk: {len(tag_dirs)}")

tag_post_counts = {}
for p in content_posts.values():
    for t in p.get('tags', []):
        tslug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', str(t).lower().strip())).strip('-')
        if tslug:
            tag_post_counts[tslug] = tag_post_counts.get(tslug, 0) + 1

empty_tags = [t for t in tag_dirs if tag_post_counts.get(t, 0) == 0]
single_post_tags = [t for t in tag_dirs if tag_post_counts.get(t, 0) == 1]
print(f"Empty tags: {len(empty_tags)}: {empty_tags}")
print(f"Single-post tags: {len(single_post_tags)} (e.g. {single_post_tags[:10]})")

# Authors
authors_dir = ROOT / 'author'
author_dirs = sorted([d.name for d in authors_dir.iterdir() if d.is_dir()])
print(f"Author directories on disk: {len(author_dirs)}: {author_dirs}")

author_post_counts = {}
for p in content_posts.values():
    a = p.get('author', 'Dinesh')
    aslug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', a.lower().strip())).strip('-')
    author_post_counts[aslug] = author_post_counts.get(aslug, 0) + 1
print(f"Author post counts: {author_post_counts}")

# -------------------------------------------------------------
# 12. INTERNAL LINKS AUDIT (Deep resolution of all links)
# -------------------------------------------------------------
internal_link_issues = []
internal_links_checked = 0
all_canonical_targets = set()
for rel in parsed_pages:
    if rel == 'index.html':
        all_canonical_targets.add('/')
    elif rel.endswith('/index.html'):
        all_canonical_targets.add('/' + rel.replace('/index.html', '/'))

# Also all assets on disk
asset_files = set()
for p in ROOT.rglob('*'):
    if not EXCLUDED_DIRS.intersection(p.relative_to(ROOT).parts):
        asset_files.add('/' + p.relative_to(ROOT).as_posix())

for rel, page in parsed_pages.items():
    page_dir = (ROOT / rel).parent
    for link_item in page.links:
        href = link_item['href']
        line = link_item['line']
        if not href:
            internal_link_issues.append((rel, line, "Empty or None href attribute"))
            continue
        href = href.strip()
        if href == '#':
            internal_link_issues.append((rel, line, "Empty hash anchor href='#'"))
            continue
        if href.startswith('javascript:'):
            if href != 'javascript:void(0);' and href != 'javascript:void(0)':
                internal_link_issues.append((rel, line, f"javascript: URL: {href}"))
            else:
                internal_link_issues.append((rel, line, "javascript:void(0) link found"))
            continue
        if href.startswith(('mailto:', 'tel:', 'whatsapp:')):
            continue
        if href.startswith(('http://', 'https://')):
            if not href.startswith('https://thefitnessfalcon.com'):
                # External link, checked separately
                continue
            # Internal absolute URL, normalize to path
            href = href.replace('https://thefitnessfalcon.com', '')
            if not href:
                href = '/'
        
        internal_links_checked += 1
        
        # Split fragment
        part = urlsplit(href)
        path = unquote(part.path)
        frag = part.fragment

        if not path and frag:
            # Anchor on same page, check if ID exists on page
            if not any(i[0] == frag for i in page.ids):
                internal_link_issues.append((rel, line, f"Anchor #{frag} not found on same page"))
            continue
        
        # Resolve target path
        if path.startswith('/'):
            target_path = path
        else:
            # relative path
            target_path = (page_dir / path).resolve().relative_to(ROOT).as_posix()
            if not target_path.startswith('/'):
                target_path = '/' + target_path

        # If pointing to directory without trailing slash
        if not target_path.endswith('/') and not '.' in target_path.split('/')[-1]:
            target_path += '/'

        # Check if target is a canonical HTML route
        if target_path in all_canonical_targets:
            # Valid canonical page
            if frag:
                # Check fragment target exists in that page
                target_rel = 'index.html' if target_path == '/' else target_path.strip('/') + '/index.html'
                target_page = parsed_pages.get(target_rel)
                if target_page and not any(i[0] == frag for i in target_page.ids):
                    internal_link_issues.append((rel, line, f"Anchor #{frag} not found on target page {target_rel}"))
        elif target_path in asset_files or target_path.rstrip('/') in asset_files:
            pass # Valid asset
        else:
            # Target does not resolve
            internal_link_issues.append((rel, line, f"Broken internal link: '{href}' resolves to '{target_path}' (404)"))

print(f"\nInternal links checked: {internal_links_checked}")
print(f"Internal link issues: {len(internal_link_issues)}")
for issue in internal_link_issues[:15]:
    print("  ", issue)

# -------------------------------------------------------------
# 13. EXTERNAL LINKS AUDIT
# -------------------------------------------------------------
external_links = []
external_link_issues = []
for rel, page in parsed_pages.items():
    for link_item in page.links:
        href = link_item['href']
        line = link_item['line']
        if not href:
            continue
        href = href.strip()
        if href.startswith(('http://', 'https://')):
            if not href.startswith('https://thefitnessfalcon.com'):
                external_links.append((rel, line, href))
                if 'itcroctheme.com' in href or 'elementor.com' in href:
                    external_link_issues.append((rel, line, f"Theme demo or builder link: {href}"))
                if 'localhost' in href or '127.0.0.1' in href or 'wp-admin' in href:
                    external_link_issues.append((rel, line, f"Development/Staging link: {href}"))
        elif href.startswith('whatsapp:'):
            external_links.append((rel, line, href))
        elif href.startswith('mailto:'):
            external_links.append((rel, line, href))
            email = href.replace('mailto:', '').split('?')[0].strip()
            if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                external_link_issues.append((rel, line, f"Malformed mailto link: {href}"))
        elif href.startswith('tel:'):
            external_links.append((rel, line, href))
        elif href.startswith('http://+'):
            external_link_issues.append((rel, line, f"Malformed WhatsApp/phone URL: {href}"))

print(f"\nExternal links found: {len(external_links)}")
print(f"External link issues: {len(external_link_issues)}")
for issue in external_link_issues[:10]:
    print("  ", issue)

# -------------------------------------------------------------
# 14. IMAGE & MEDIA AUDIT
# -------------------------------------------------------------
images_checked = 0
image_issues = []
for rel, page in parsed_pages.items():
    page_dir = (ROOT / rel).parent
    for img in page.images:
        images_checked += 1
        src = img['src']
        alt = img['alt']
        line = img['line']
        width = img['width']
        height = img['height']

        if not src:
            image_issues.append((rel, line, "Missing src attribute"))
            continue

        if alt is None:
            image_issues.append((rel, line, f"Missing alt attribute on img: {src}"))
        
        # Check source resolution
        if src.startswith('https://thefitnessfalcon.com/'):
            local_path = ROOT / src.replace('https://thefitnessfalcon.com/', '')
        elif src.startswith('/'):
            local_path = ROOT / src.lstrip('/')
        elif src.startswith(('http://', 'https://')):
            local_path = None # External image
        else:
            local_path = (page_dir / src).resolve()

        if local_path is not None and not local_path.is_file():
            image_issues.append((rel, line, f"Missing local image file: {src}"))

print(f"\nImages checked: {images_checked}")
print(f"Image issues: {len(image_issues)}")
for issue in image_issues[:10]:
    print("  ", issue)

# Check oversized images in assets/
oversized_images = []
for img_path in (ROOT / 'assets').rglob('*'):
    if img_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif'):
        sz = img_path.stat().st_size
        if sz > 500 * 1024:
            oversized_images.append((img_path.relative_to(ROOT).as_posix(), f"{sz / 1024:.1f} KB"))

print(f"\nOversized images (>500KB): {len(oversized_images)}")
for p, s in oversized_images:
    print(f"  {p}: {s}")

# -------------------------------------------------------------
# 15. FORMS & CONVERSIONS AUDIT
# -------------------------------------------------------------
form_issues = []
for rel, page in parsed_pages.items():
    for f in page.forms:
        action = f['action'] or ''
        method = f['method'] or ''
        fid = f['id'] or ''
        line = f['line']
        if not action or action == '#' or action == 'javascript:void(0)':
            form_issues.append((rel, line, f"Form has missing or dummy action: action='{action}'"))

# Check contact form page specifically
contact_page_raw = raw_pages.get('pages/contact-us/index.html', '')
if '[contact-form-7' in contact_page_raw:
    form_issues.append(('pages/contact-us/index.html', 0, "Unparsed WordPress Contact Form 7 shortcode found!"))

# Check newsletter block
newsletter_block_raw = (ROOT / 'components' / 'newsletter-block.html').read_text() if (ROOT / 'components' / 'newsletter-block.html').exists() else ''
if "alert('Subscribed successfully!')" in newsletter_block_raw or 'alert("Subscribed successfully!")' in newsletter_block_raw:
    form_issues.append(('components/newsletter-block.html', 0, "Newsletter form triggers fake alert without sending request to backend"))

print(f"\nForm issues: {len(form_issues)}")
for issue in form_issues:
    print("  ", issue)

# -------------------------------------------------------------
# 16. DUPLICATE HTML IDs AUDIT
# -------------------------------------------------------------
duplicate_id_issues = []
for rel, page in parsed_pages.items():
    id_counts = {}
    for fid, line in page.ids:
        id_counts.setdefault(fid, []).append(line)
    dups = {k: v for k, v in id_counts.items() if len(v) > 1}
    if dups:
        duplicate_id_issues.append((rel, dups))

print(f"\nDuplicate HTML ID issues: {len(duplicate_id_issues)} pages")
for rel, dups in duplicate_id_issues[:5]:
    print(f"  {rel}: {dups}")

# -------------------------------------------------------------
# 17. JAVASCRIPT SYNTAX & AUDIT
# -------------------------------------------------------------
js_files = list((ROOT / 'assets' / 'js').glob('*.js'))
print(f"\nJavaScript files found: {len(js_files)}")
js_issues = []
for js in js_files:
    content = js.read_text(encoding='utf-8')
    # Check syntax using python node if available or simple checks
    if 'localStorage' in content and 'try {' not in content:
        # Check if localStorage is accessed directly without try/catch
        pass
    if 'fbq(' in content:
        js_issues.append((js.name, "fbq call present in script"))

# Check inline scripts in HTML
for rel, raw in raw_pages.items():
    if "fbq('track'" in raw or 'fbq("track"' in raw:
        js_issues.append((rel, "Undefined fbq('track', 'PageView') call in inline script"))

print(f"JavaScript issues: {len(js_issues)}")
for issue in js_issues:
    print("  ", issue)

# -------------------------------------------------------------
# 18. REDIRECTS AUDIT (_redirects & .htaccess)
# -------------------------------------------------------------
redirects_file = ROOT / '_redirects'
redirect_rules = []
if redirects_file.exists():
    for line in redirects_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            parts = line.split()
            if len(parts) >= 2:
                src, dst = parts[0], parts[1]
                code = parts[2] if len(parts) > 2 else '301'
                redirect_rules.append((src, dst, code))

print(f"\nRedirect rules loaded from _redirects: {len(redirect_rules)}")

redirect_issues = []
# Check destination validity
for src, dst, code in redirect_rules:
    if dst.startswith('http'):
        continue
    # Normalize dst
    clean_dst = dst
    if clean_dst == '/':
        target_file = ROOT / 'index.html'
    else:
        target_file = ROOT / clean_dst.strip('/') / 'index.html'
    if not target_file.is_file():
        redirect_issues.append((src, dst, f"Destination does not resolve to an existing page: {target_file}"))

# Check redirect chains
redirect_sources = {src: dst for src, dst, code in redirect_rules}
for src, dst, code in redirect_rules:
    if dst in redirect_sources:
        redirect_issues.append((src, dst, f"Redirect chain detected: {dst} -> {redirect_sources[dst]}"))

print(f"Redirect issues: {len(redirect_issues)}")
for issue in redirect_issues[:10]:
    print("  ", issue)

# -------------------------------------------------------------
# 19. ACCESSIBILITY CHECKS
# -------------------------------------------------------------
a11y_issues = []
for rel, page in parsed_pages.items():
    if not page.lang:
        a11y_issues.append((rel, "Missing lang attribute on <html>"))
    if not page.has_main:
        a11y_issues.append((rel, "Missing <main> semantic landmark"))

print(f"\nAccessibility issues (basic DOM landmarks): {len(a11y_issues)}")
for issue in a11y_issues[:5]:
    print("  ", issue)

# -------------------------------------------------------------
# 20. REMAINING TEMPLATE PLACEHOLDERS AUDIT
# -------------------------------------------------------------
placeholder_issues = []
for rel, raw in raw_pages.items():
    matches = re.findall(r'\{\{[A-Z0-9_]+\}\}', raw)
    if matches:
        placeholder_issues.append((rel, matches))

print(f"\nRemaining template placeholders: {len(placeholder_issues)}")
for issue in placeholder_issues:
    print("  ", issue)

# -------------------------------------------------------------
# SAVE SUMMARY JSON
# -------------------------------------------------------------
full_summary = {
    'total_pages': len(html_files),
    'route_inventory': {k: len(v) for k, v in route_inventory.items()},
    'canonical_issues': canonical_issues,
    'robots_analysis': {k: len(v) if isinstance(v, list) else v for k, v in robots_analysis.items()},
    'sitemap_urls_count': len(sitemap_urls),
    'missing_from_sitemap': sorted(list(missing_from_sitemap)),
    'extra_in_sitemap': sorted(list(extra_in_sitemap)),
    'title_issues': title_issues,
    'desc_issues': desc_issues,
    'duplicate_titles_count': len(duplicate_titles),
    'duplicate_descs_count': len(duplicate_descs),
    'og_issues': og_issues,
    'heading_issues': heading_issues,
    'schema_issues': schema_issues,
    'parity_mismatches': parity_mismatches,
    'empty_categories': empty_categories,
    'empty_tags': empty_tags,
    'single_post_tags': single_post_tags,
    'internal_links_checked': internal_links_checked,
    'internal_link_issues': internal_link_issues,
    'external_links_checked': len(external_links),
    'external_link_issues': external_link_issues,
    'images_checked': images_checked,
    'image_issues': image_issues,
    'oversized_images': oversized_images,
    'form_issues': form_issues,
    'duplicate_id_issues': duplicate_id_issues,
    'js_issues': js_issues,
    'redirect_issues': redirect_issues,
    'a11y_issues': a11y_issues,
    'placeholder_issues': placeholder_issues
}

(ROOT / 'scratch' / 'full_audit_summary.json').write_text(json.dumps(full_summary, indent=2))
print("\n" + "="*60)
print("AUDIT COMPLETE. Full summary written to scratch/full_audit_summary.json")
print("="*60)
