"""Keep the homepage and shared header/footer story lists aligned with publication dates.

Regenerates, from content/posts/*.json (newest first):
- homepage hero (newest post) and the three side cards (next three posts)
- homepage Latest tab
- header "Latest" ticker (components/header.html)
- footer "One more good read" list (components/footer.html)
and removes legacy WordPress leftovers from index.html (idempotent).
URLs are never changed: every link uses /blogs/<slug>/.
"""
import html,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def esc(s):
    return html.escape(s,quote=True)

def load_posts():
    posts=[json.loads(p.read_text()) for p in (ROOT/'content/posts').glob('*.json')]
    posts.sort(key=lambda p:(p.get('published_time') or p['published_iso'],p['slug']),reverse=True)
    return posts

def url(p):
    return f'/blogs/{p["slug"]}/'

def remove_div_containing(source,marker):
    """Remove the <div> whose opening tag contains marker, including all nested divs."""
    i=source.find(marker)
    if i<0:return source
    start=source.rfind('<div',0,i)
    depth=0
    for m in re.finditer(r'<div\b|</div>',source[start:]):
        depth+=1 if m.group(0)=='<div' else -1
        if depth==0:
            end=start+m.end()
            return source[:start]+source[end:]
    raise ValueError(f'Unbalanced div for {marker}')

def hero_html(posts):
    main,side=posts[0],posts[1:4]
    side_cards='\n'.join(f'''                    <a class="falcon-side-card" href="{url(p)}">
                        <div class="falcon-side-thumb">
                            <img width="120" height="120" src="{esc(p['featured_image'])}" alt="{esc(p.get('featured_image_alt',p['title']))}" />
                        </div>
                        <div class="falcon-side-content">
                            <span class="falcon-side-badge">{esc(p['category'])}</span>
                            <h3 class="falcon-side-title">{esc(p['title'])}</h3>
                        </div>
                    </a>''' for p in side)
    return f'''<section class="elementor-section elementor-top-section falcon-hero-section elementor-section-boxed my-4" data-id="a32e7b8">
    <div class="container">
        <h1 class="falcon-visually-hidden">The Fitness Falcon: Fitness, Nutrition and Wellness Guides</h1>
        <div class="falcon-hero-row">
            <div class="falcon-hero-col-main">
                <a class="falcon-hero-card" href="{url(main)}">
                    <img fetchpriority="high" width="{main.get('featured_image_width',1200)}" height="{main.get('featured_image_height',675)}" src="{esc(main['featured_image'])}" alt="{esc(main.get('featured_image_alt',main['title']))}" />
                    <div class="falcon-hero-card-overlay"></div>
                    <div class="falcon-hero-card-content">
                        <span class="falcon-hero-badge">{esc(main['category'])}</span>
                        <h2 class="falcon-hero-card-title">{esc(main['title'])}</h2>
                        <div class="falcon-hero-card-meta">
                            <span><i class="fal fa-user"></i> {esc(main['author'])}</span>
                            <span><i class="fal fa-calendar-alt"></i> {esc(main['published_date'])}</span>
                            <span><i class="fal fa-clock"></i> {main.get('read_time',5)} min read</span>
                        </div>
                    </div>
                </a>
            </div>
            <div class="falcon-hero-col-side">
                <div class="falcon-hero-side-list">
{side_cards}
                </div>
            </div>
        </div>
    </div>
</section>'''

def generate_home_latest():
    posts=load_posts()
    path=ROOT/'index.html';source=path.read_text()
    updated=source

    # Hero + side cards
    updated,n=re.subn(r'<section class="elementor-section elementor-top-section falcon-hero-section.*?</section>',
                      lambda m:hero_html(posts),updated,count=1,flags=re.S)
    if n!=1:raise ValueError('Homepage hero section not found')

    # Latest tab
    cards=[]
    for p in posts[:4]:
        cards.append(f'''                <div class="pfy-post-item pfy-scale">
                    <div class="pfy-post-thumb">
                        <a href="{url(p)}"><img width="72" height="72" loading="lazy" src="{esc(p['featured_image'])}" alt="{esc(p.get('featured_image_alt',p['title']))}" /></a>
                    </div>
                    <div class="pfy-post-content">
                        <h4 class="pfy-post-title"><a href="{url(p)}">{html.escape(p['title'])}</a></h4>
                    </div>
                </div>''')
    pattern=r'(<!-- Tab 1: Latest -->.*?<div class="pfy-post-grid-wrap grid-style-tb">).*?(\n            </div>\n        </div>\n        <!-- Tab 2: Popular -->)'
    updated,n=re.subn(pattern,lambda m:m[1]+'\n'+'\n'.join(cards)+m[2],updated,count=1,flags=re.S)
    if n!=1:raise ValueError('Homepage Latest section not found')

    # Legacy WordPress leftovers: bogus ez-toc navigation schema and Elementor generator tag
    updated=re.sub(r'<script type="application/ld\+json" class="ez-toc-schema-markup-output">.*?</script>','',updated,flags=re.S)
    updated=re.sub(r'<meta name="generator" content="Elementor[^"]*">','',updated)
    # Fake engagement counters (no comment system or view tracking exists)
    updated=re.sub(r'\s*<li><i class="far fa-comments"></i>\s*\d+ Comments\s*</li>','',updated)
    updated=re.sub(r'\s*<span><i class="far fa-(?:comments|eye)"></i> \d+ (?:Comments|Views)</span>','',updated)
    # Newsletter widget has no delivery integration; hide it until one is connected
    updated=remove_div_containing(updated,'elementor-element-9f16dba')
    # The second "Trending Stories" heading labels the social follow widget
    updated=re.sub(r'(<div class="benqu-section-title-wrap text-left">\s*<h2>)Trending Stories(</h2>\s*<span></span>\s*</div>\s*</div>\s*</div>\s*<div[^>]*benqu-social)',
                   r'\1Follow Us\2',updated,flags=re.S)

    # Stylesheet was linked twice by the original migration
    dup='<link rel="stylesheet" href="/assets/css/homepage.css">\n'
    while updated.count(dup)>1:
        i=updated.rfind(dup);updated=updated[:i]+updated[i+len(dup):]

    if updated!=source:path.write_text(updated)

    # Header ticker: newest four posts
    header=ROOT/'components/header.html';h=header.read_text()
    items='\n'.join(f'                                    <li><a href="{url(p)}">{html.escape(p["title"])}</a></li>' for p in posts[:4])
    h2=re.sub(r'(<ul class="falcon-breaking-headlines" aria-label="Latest headlines">\n).*?(\n\s*</ul>)',lambda m:m[1]+items+m[2],h,count=1,flags=re.S)
    h2=h2.replace('<i class="far fa-fire-alt"></i> Breaking News','<i class="far fa-fire-alt"></i> Latest')
    if h2!=h:header.write_text(h2)

    # Footer reads: newest three posts
    footer=ROOT/'components/footer.html';f=footer.read_text()
    stories='\n'.join(f'''        <a class="falcon-footer-story" href="{url(p)}">
          <img src="{esc(p['featured_image'])}" width="72" height="56" alt="" loading="lazy">
          <span>{html.escape(p['title'])}</span>
          <span class="falcon-story-arrow" aria-hidden="true">↗</span>
        </a>''' for p in posts[:3])
    f2=re.sub(r'(<h3>One more good read</h3>\n).*?(\n      </div>)',lambda m:m[1]+stories+m[2],f,count=1,flags=re.S)
    if f2!=f:footer.write_text(f2)
