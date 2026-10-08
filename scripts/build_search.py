"""Refresh search data directly from the source article inventory."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def generate_search():
    posts = [json.loads(p.read_text()) for p in (ROOT / 'content/posts').glob('*.json')]
    posts.sort(key=lambda p: (p.get('published_time') or p['published_iso'], p['slug']), reverse=True)
    entries = [{'title': p['title'], 'slug': p['slug'], 'thumb': Path(p['featured_image']).name, 'date': p['published_date'], 'cat': p['category'], 'url': f'/blogs/{p["slug"]}/'} for p in posts]
    (ROOT / 'assets/search_index.json').write_text(json.dumps(entries, indent=2, ensure_ascii=False) + '\n')
    (ROOT / 'assets/js/falcon-search-data.js').write_text('window.ALL_POSTS = ' + json.dumps(entries, ensure_ascii=False) + ';\n')

