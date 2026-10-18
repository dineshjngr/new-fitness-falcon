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
from datetime import datetime, timedelta, timezone
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

ESSENTIAL_GUIDES = [
    'how-much-water-should-you-really-drink-each-day',
    'what-is-hiit-high-intensity-interval-training-types-benefits',
    'intermittent-fasting-and-fat-loss',
    'running-for-mental-health-stress-anxiety-and-mood-benefits',
    '10-effective-tips-for-managing-stress',
    'aging-well-10-secrets-to-a-vibrant-life',
]

CATEGORY_TILES = [
    ('Fitness', 'fitness', 'Fitness.png'), ('Nutrition', 'nutrition', 'Nutrition.png'),
    ('Health', 'health', 'Health.png'), ('Gym', 'gym', 'Gym.png'),
    ('Food &amp; Recipes', 'food-and-recipes', 'Food-Recipes.png'), ('Cycling', 'cycling', 'Cycling.png'),
    ('Skincare', 'skincare', 'Skincare.png'), ('Lifestyle', 'lifestyle', 'Lifestyle.png'),
]


def section(title, link, link_text, body, cls=''):
    more = f'<a class="ff-home-more" href="{link}">{link_text} <span aria-hidden="true">&rarr;</span></a>' if link else ''
    return f'''<section class="ff-home-section {cls}">
  <div class="container">
    <div class="ff-home-head"><h2>{title}</h2>{more}</div>
{body}
  </div>
</section>'''


def card_grid(posts, cols='col-md-6 col-lg-4 mb-4'):
    from scripts import components
    return '<div class="row">' + '\n'.join(components.render_article_card(p, col_class=cols) for p in posts) + '</div>'


def mini_card(p, hidden=False):
    attrs = ' aria-hidden="true" tabindex="-1"' if hidden else ''
    return f'''<a class="ff-mini-card" href="{url(p)}"{attrs}>
  <img src="{esc(p['featured_image'])}" alt="{'' if hidden else esc(p.get('featured_image_alt', p['title']))}" width="320" height="180" loading="lazy">
  <span class="ff-mini-body"><span class="ff-kicker">{esc(p['category'])}</span><span class="ff-mini-title">{html.escape(p['title'])}</span><span class="ff-mini-meta">{esc(p['published_date'])} &middot; {p.get('read_time', 5)} min read</span></span>
</a>'''


def marquee_section(title, link, link_text, items, reverse=False, cls=''):
    """Full-bleed auto-scrolling row. The item list is repeated so one copy is
    wider than large screens, then duplicated for a seamless loop."""
    if not items:
        return ''
    loop = list(items)
    while len(loop) < 12:
        loop += items
    first = '\n'.join(mini_card(p) for p in loop[:len(items)]) + '\n' + '\n'.join(mini_card(p, True) for p in loop[len(items):])
    copy = '\n'.join(mini_card(p, True) for p in loop)
    direction = ' ff-marquee--reverse' if reverse else ''
    seconds = max(40, len(loop) * 5)
    more = f'<a class="ff-home-more" href="{link}">{link_text} <span aria-hidden="true">&rarr;</span></a>'
    return f'''<section class="ff-home-section ff-home-marquee {cls}">
  <div class="container"><div class="ff-home-head"><h2>{title}</h2>{more}</div></div>
  <div class="ff-marquee{direction}" style="--ff-marquee-duration:{seconds}s">
    <div class="ff-marquee-track">
{first}
{copy}
    </div>
  </div>
</section>'''


def overlay_card(p, cls, eager=False):
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    dek = f'<span class="ff-cover-dek">{esc(p.get("description", ""))}</span>' if cls == 'ff-cover-main' else ''
    return f'''<a class="ff-cover-card {cls}" href="{url(p)}">
  <img src="{esc(p['featured_image'])}" alt="{esc(p.get('featured_image_alt', p['title']))}" {load}>
  <span class="ff-cover-text">
    <span class="ff-cover-kicker">{esc(p['category'])}</span>
    <span class="ff-cover-title">{html.escape(p['title'])}</span>
    {dek}
    <span class="ff-cover-meta">{esc(p['published_date'])} &middot; {p.get('read_time', 5)} min read</span>
  </span>
</a>'''


def home_main(posts):
    by_slug = {p['slug']: p for p in posts}
    used = set()

    def take(items):
        used.update(p['slug'] for p in items)
        return items

    # 1. Cover
    lead, second, third = take(posts[:3])
    cover = f'''<section class="ff-cover">
  <div class="container">
    <h1 class="falcon-visually-hidden">The Fitness Falcon: Fitness, Nutrition and Wellness Guides</h1>
    <div class="ff-cover-grid">
{overlay_card(lead, 'ff-cover-main', eager=True)}
      <div class="ff-cover-side">
{overlay_card(second, 'ff-cover-small')}
{overlay_card(third, 'ff-cover-small')}
      </div>
    </div>
  </div>
</section>'''

    # 2. Just published: numbered text strip
    fresh = take([p for p in posts if p['slug'] not in used][:4])
    fresh_items = '\n'.join(f'''      <a class="ff-fresh-item" href="{url(p)}"><span class="ff-fresh-num">{i:02d}</span><span class="ff-kicker">{esc(p['category'])}</span><span class="ff-fresh-title">{html.escape(p['title'])}</span><span class="ff-fresh-meta">{esc(p['published_date'])}</span></a>''' for i, p in enumerate(fresh, 1))
    just = f'''<section class="ff-fresh">
  <div class="container">
    <div class="ff-fresh-head"><span class="ff-dot" aria-hidden="true"></span><h2>Just published</h2><a class="ff-home-more" href="/blogs/">All articles <span aria-hidden="true">&rarr;</span></a></div>
    <div class="ff-fresh-grid">
{fresh_items}
    </div>
  </div>
</section>'''

    # 3. Explore topics: round images
    topics_html = '\n'.join(f'''      <a class="ff-round-topic" href="/category/{slug}/"><img src="/assets/images/{img}" alt="" loading="lazy"><span>{name}</span></a>''' for name, slug, img in CATEGORY_TILES)
    topics = f'''<section class="ff-topics-band">
  <div class="container">
    <h2 class="ff-band-title">Explore topics</h2>
    <div class="ff-round-topics">
{topics_html}
    </div>
  </div>
</section>'''

    # 4. Editor's pick: newest unused post with key takeaways
    pick = next((p for p in posts if p['slug'] not in used and p.get('key_takeaways')), None)
    pick_html = ''
    if pick:
        take([pick])
        lis = '\n'.join(f'          <li>{html.escape(t)}</li>' for t in pick['key_takeaways'][:3])
        pick_html = f'''<section class="ff-pick">
  <div class="container">
    <div class="ff-pick-grid">
      <a class="ff-pick-media" href="{url(pick)}"><img src="{esc(pick['featured_image'])}" alt="{esc(pick.get('featured_image_alt', pick['title']))}" loading="lazy"></a>
      <div class="ff-pick-body">
        <span class="ff-pick-label">Editor&rsquo;s pick</span>
        <span class="ff-kicker">{esc(pick['category'])}</span>
        <h2 class="ff-pick-title"><a href="{url(pick)}">{html.escape(pick['title'])}</a></h2>
        <ul class="ff-pick-points">
{lis}
        </ul>
        <a class="ff-pick-cta" href="{url(pick)}">Read the guide <span aria-hidden="true">&rarr;</span></a>
      </div>
    </div>
  </div>
</section>'''

    # 5. Essential guides: numbered two-column reading list
    guides = take([by_slug[s] for s in ESSENTIAL_GUIDES if s in by_slug and s not in used][:6])
    guide_items = '\n'.join(f'''      <a class="ff-guide" href="{url(p)}"><span class="ff-guide-num">{i}</span><span class="ff-guide-text"><span class="ff-kicker">{esc(p['category'])}</span><span class="ff-guide-title">{html.escape(p['title'])}</span><span class="ff-guide-meta">{p.get('read_time', 5)} min read</span></span><img src="{esc(p['featured_image'])}" alt="" loading="lazy"></a>''' for i, p in enumerate(guides, 1))
    guides_html = section('Essential guides', '/blogs/', 'Browse the library', f'    <div class="ff-guides">\n{guide_items}\n    </div>', 'ff-home-guides')

    # Sliders
    lead_slugs = {p['slug'] for p in posts[:3]}

    def row(urls, n=10):
        return [p for p in posts if p.get('category_url') in urls and p['slug'] not in lead_slugs][:n]

    fitness = row({'/category/fitness/', '/category/workout/', '/category/gym/'})
    nutrition = row({'/category/nutrition/', '/category/food-and-recipes/', '/category/recipes/'})
    tech = row({'/category/wearables-fitness-technology/'})

    # 5b. New this month: every article from the last 45 days that no section
    # above links. Googlebot crawls the homepage far more often than the
    # paginated archive, so each new URL gets a link from the strongest page.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=45)).strftime('%Y-%m-%d')
    linked = used | {p['slug'] for group in (fitness, nutrition, tech) for p in group}
    recent = take([p for p in posts if p['slug'] not in linked and p['published_iso'] >= cutoff][:24])
    recent_html = ''
    if recent:
        recent_items = '\n'.join(f'''      <a class="ff-recent-item" href="{url(p)}"><span class="ff-kicker">{esc(p['category'])}</span><span class="ff-recent-title">{html.escape(p['title'])}</span><span class="ff-recent-meta">{esc(p['published_date'])}</span></a>''' for p in recent)
        recent_html = section('New this month', '/blogs/', 'All articles', f'    <div class="ff-recent">\n{recent_items}\n    </div>', 'ff-home-recent')

    # 6. How we work
    trust = '''<section class="ff-trust" aria-labelledby="ff-trust-title">
  <div class="container">
    <div class="ff-trust-panel">
      <div class="ff-trust-intro">
        <span class="ff-trust-eyebrow">How we work</span>
        <h2 id="ff-trust-title">Fitness information you can check</h2>
        <p>The Fitness Falcon is an independent publication. This is how we research, date and correct what we publish.</p>
        <div class="ff-trust-actions">
          <a class="ff-trust-btn ff-trust-btn--solid" href="/pages/editorial-policy/">Editorial policy</a>
          <a class="ff-trust-btn" href="/pages/team/">Who we are</a>
          <a class="ff-trust-btn" href="/pages/contact-us/">Report a correction</a>
        </div>
      </div>
      <ul class="ff-trust-list">
        <li><span class="ff-trust-icon" aria-hidden="true"><i class="fal fa-search"></i></span><div><h3>Built on reliable sources</h3><p>We research articles from public health agencies, peer-reviewed studies and official product specs, and our current guides link the sources they use.</p></div></li>
        <li><span class="ff-trust-icon" aria-hidden="true"><i class="fal fa-calendar-check"></i></span><div><h3>Dated and kept current</h3><p>Time-sensitive details such as prices, features and guidelines show when we checked them, and we update articles when they change.</p></div></li>
        <li><span class="ff-trust-icon" aria-hidden="true"><i class="fal fa-shield-check"></i></span><div><h3>Clear about limits</h3><p>Reviews say when they are research-based rather than hands-on. Health content is general information, not medical advice.</p></div></li>
      </ul>
    </div>
  </div>
</section>'''

    parts = [cover, just, topics,
             marquee_section('Fitness &amp; Workouts', '/category/fitness/', 'More fitness', fitness),
             pick_html,
             marquee_section('Nutrition &amp; Recipes', '/category/nutrition/', 'More nutrition', nutrition, reverse=True, cls='ff-home-alt'),
             guides_html,
             marquee_section('Wearables &amp; Tech', '/category/wearables-fitness-technology/', 'More wearables', tech),
             recent_html,
             trust]
    return '<main id="main-content" class="falcon-main-layout home-main ff-home">\n' + '\n\n'.join(x for x in parts if x) + '\n</main>'


def generate_home_latest():
    posts=load_posts()
    path=ROOT/'index.html';source=path.read_text()
    updated=re.sub(r'<main id="main-content".*?</main>',lambda m:home_main(posts),source,count=1,flags=re.S)
    # Legacy WordPress leftovers in <head>
    updated=re.sub(r'<script type="application/ld\+json" class="ez-toc-schema-markup-output">.*?</script>','',updated,flags=re.S)
    updated=re.sub(r'<meta name="generator" content="Elementor[^"]*">','',updated)
    dup='<link rel="stylesheet" href="/assets/css/homepage.css">\n'
    while updated.count(dup)>1:
        i=updated.rfind(dup);updated=updated[:i]+updated[i+len(dup):]
    if '/assets/css/home-clean.css' not in updated:
        updated=updated.replace('</head>','<link rel="stylesheet" href="/assets/css/home-clean.css">\n</head>',1)
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
