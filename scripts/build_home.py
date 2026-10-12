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


def home_main(posts):
    by_slug = {p['slug']: p for p in posts}
    lead, side = posts[0], posts[1:5]
    used = {p['slug'] for p in posts[:5]}
    latest = [p for p in posts[5:] if p['slug'] not in used][:6]
    used |= {p['slug'] for p in latest}

    def in_cat(urls, n):
        out = [p for p in posts if p.get('category_url') in urls and p['slug'] not in used][:n]
        used.update(p['slug'] for p in out)
        return out

    side_items = '\n'.join(f'''      <a class="ff-lead-item" href="{url(p)}">
        <img src="{esc(p['featured_image'])}" alt="{esc(p.get('featured_image_alt', p['title']))}" width="160" height="90" loading="lazy">
        <span class="ff-lead-item-text"><span class="ff-kicker">{esc(p['category'])}</span><span class="ff-lead-item-title">{html.escape(p['title'])}</span><span class="ff-lead-item-meta">{esc(p['published_date'])} &middot; {p.get('read_time', 5)} min read</span></span>
      </a>''' for p in side)
    hero = f'''<section class="ff-home-hero">
  <div class="container">
    <h1 class="falcon-visually-hidden">The Fitness Falcon: Fitness, Nutrition and Wellness Guides</h1>
    <div class="ff-lead">
      <a class="ff-lead-main" href="{url(lead)}">
        <img src="{esc(lead['featured_image'])}" alt="{esc(lead.get('featured_image_alt', lead['title']))}" width="1200" height="675" fetchpriority="high">
        <span class="ff-lead-main-text">
          <span class="ff-kicker">{esc(lead['category'])}</span>
          <span class="ff-lead-title">{html.escape(lead['title'])}</span>
          <span class="ff-lead-dek">{esc(lead.get('description', ''))}</span>
          <span class="ff-lead-meta">{esc(lead['author'])} &middot; {esc(lead['published_date'])} &middot; {lead.get('read_time', 5)} min read</span>
        </span>
      </a>
      <div class="ff-lead-side">
        <p class="ff-lead-side-title">Latest</p>
{side_items}
      </div>
    </div>
  </div>
</section>'''

    tiles = '\n'.join(f'''      <a class="ff-topic" href="/category/{slug}/"><img src="/assets/images/{img}" alt="" loading="lazy"><span>{name}</span></a>''' for name, slug, img in CATEGORY_TILES)
    topics = section('Browse by topic', '/blogs/', 'All articles', f'    <div class="ff-topics">\n{tiles}\n    </div>', 'ff-home-topics')

    guides = [by_slug[s] for s in ESSENTIAL_GUIDES if s in by_slug and s not in used][:6]
    used.update(p['slug'] for p in guides)
    fitness = in_cat({'/category/fitness/', '/category/workout/', '/category/gym/'}, 3)
    nutrition = in_cat({'/category/nutrition/', '/category/food-and-recipes/', '/category/recipes/'}, 3)
    tech = in_cat({'/category/wearables-fitness-technology/'}, 3)

    parts = [hero,
             section('Latest articles', '/blogs/', 'View all', card_grid(latest)),
             topics,
             section('Essential guides', '/blogs/', 'Browse the library', card_grid(guides), 'ff-home-alt'),
             section('Fitness &amp; workouts', '/category/fitness/', 'More fitness', card_grid(fitness)),
             section('Nutrition &amp; recipes', '/category/nutrition/', 'More nutrition', card_grid(nutrition), 'ff-home-alt'),
             section('Wearables &amp; tech', '/category/wearables-fitness-technology/', 'More wearables', card_grid(tech))]
    return '<main id="main-content" class="falcon-main-layout home-main ff-home">\n' + '\n\n'.join(parts) + '\n</main>'


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
