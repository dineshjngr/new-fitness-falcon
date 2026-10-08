"""Keep the homepage's Latest tab aligned with publication dates."""
import html,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def generate_home_latest():
    posts=[json.loads(p.read_text()) for p in (ROOT/'content/posts').glob('*.json')]
    posts.sort(key=lambda p:(p.get('published_time') or p['published_iso'],p['slug']),reverse=True)
    cards=[]
    for p in posts[:4]:
        url=f'/blogs/{p["slug"]}/'
        cards.append(f'''                <div class="pfy-post-item pfy-scale">
                    <div class="pfy-post-thumb">
                        <a href="{url}"><img width="72" height="72" loading="lazy" src="{html.escape(p['featured_image'],quote=True)}" alt="{html.escape(p.get('featured_image_alt',p['title']),quote=True)}" /></a>
                    </div>
                    <div class="pfy-post-content">
                        <h4 class="pfy-post-title"><a href="{url}">{html.escape(p['title'])}</a></h4>
                    </div>
                </div>''')
    path=ROOT/'index.html';source=path.read_text()
    pattern=r'(<!-- Tab 1: Latest -->.*?<div class="pfy-post-grid-wrap grid-style-tb">).*?(\n            </div>\n        </div>\n        <!-- Tab 2: Popular -->)'
    updated,n=re.subn(pattern,lambda m:m[1]+'\n'+'\n'.join(cards)+m[2],source,count=1,flags=re.S)
    if n!=1:raise ValueError('Homepage Latest section not found')
    if updated!=source:path.write_text(updated)
