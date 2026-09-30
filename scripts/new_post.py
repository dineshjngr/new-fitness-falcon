#!/usr/bin/env python3
"""
Create a new blog article for The Fitness Falcon.
Creates content/posts/<slug>.json, updates the search index, and compiles the post
using the single master template (components/post-template.html).
"""
import os, sys, re, json, argparse, html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / 'content' / 'posts'
SEARCH_JSON = ROOT / 'assets' / 'search_index.json'
SEARCH_JS = ROOT / 'assets' / 'js' / 'falcon-search-data.js'

AUTHOR_INFO = {
    'Dinesh': {
        'role': 'Senior Health & Fitness Editor',
        'bio': 'Senior contributor at The Fitness Falcon. Passionate about strength training, endurance performance, and evidence-based wellness strategies that empower everyday athletes.',
        'gradient': 'linear-gradient(135deg, #5541f8 0%, #3b82f6 100%)',
        'initial': 'D'
    },
    'Alex': {
        'role': 'Health Tech & Wearables Analyst',
        'bio': 'Fitness technology specialist and gear reviewer at The Fitness Falcon. Dedicated to demystifying biometric tracking, heart rate variability, and performance recovery tools.',
        'gradient': 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)',
        'initial': 'A'
    },
    'Riya Verma': {
        'role': 'Holistic Health & Nutrition Contributor',
        'bio': 'Nutrition and mindful living contributor at The Fitness Falcon. Specializes in whole-food recipes, gut health, stress resilience, and balanced daily wellness habits.',
        'gradient': 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
        'initial': 'R'
    }
}

def slugify(text):
    text = html.unescape(text).strip().lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def main():
    parser = argparse.ArgumentParser(description='Create a new blog article in content/posts/')
    parser.add_argument('--title', required=True, help='Article title / H1')
    parser.add_argument('--category', default='Fitness', help='Category name (e.g. Fitness, Nutrition, Health, Skincare)')
    parser.add_argument('--category-slug', default=None, help='Category slug (e.g. fitness, nutrition)')
    parser.add_argument('--author', default='Dinesh', choices=['Dinesh', 'Alex', 'Riya Verma'], help='Article author')
    parser.add_argument('--image', default='/assets/images/1-1.png', help='Featured image path')
    parser.add_argument('--tags', default='', help='Comma-separated tags (e.g. Fitness,Workout,Health)')
    parser.add_argument('--read-time', type=int, default=5, help='Reading time in minutes')
    parser.add_argument('--slug', default=None, help='Custom post slug')
    args = parser.parse_args()

    slug = args.slug or slugify(args.title)
    cat_slug = args.category_slug or slugify(args.category)
    now = datetime.now()
    date_str = now.strftime('%B %d, %Y')
    iso_date = now.strftime('%Y-%m-%d')
    author = args.author if args.author in AUTHOR_INFO else 'Dinesh'

    tags_list = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else [args.category]

    post_file = CONTENT_DIR / f'{slug}.json'
    if post_file.exists():
        print(f'Error: Post already exists at {post_file}', file=sys.stderr)
        sys.exit(1)

    post_data = {
        'slug': slug,
        'title': args.title,
        'meta_title': f"{args.title} - The Fitness Falcon",
        'description': f"Read {args.title} on The Fitness Falcon for expert fitness, nutrition, and wellness advice.",
        'canonical_url': f"https://thefitnessfalcon.com/blogs/{slug}/",
        'category': args.category,
        'category_url': f"/category/{cat_slug}/",
        'author': author,
        'author_role': AUTHOR_INFO[author]['role'],
        'author_bio': AUTHOR_INFO[author]['bio'],
        'author_initial': AUTHOR_INFO[author]['initial'],
        'author_gradient': AUTHOR_INFO[author]['gradient'],
        'published_date': date_str,
        'published_iso': iso_date,
        'modified_date': date_str,
        'modified_iso': iso_date,
        'read_time': args.read_time,
        'comments_count': 0,
        'featured_image': args.image,
        'featured_image_alt': args.title,
        'tags': tags_list,
        'content': f"<h2>Introduction</h2>\n<p>Welcome to {args.title}. In this article, we dive into key strategies and insights to help you reach your goals.</p>\n<h2>Key Takeaways</h2>\n<ul>\n    <li>Stay consistent and listen to your body.</li>\n    <li>Focus on evidence-based fitness and nutrition habits.</li>\n</ul>\n<h2>Conclusion</h2>\n<p>Start applying these principles today for long-term health and vitality.</p>"
    }

    post_file.write_text(json.dumps(post_data, indent=2, ensure_ascii=False))
    print(f'Created new post data: {post_file.relative_to(ROOT)}')

    # Update search index
    search_data = json.loads(SEARCH_JSON.read_text(encoding='utf-8'))
    thumb_name = Path(args.image).name
    search_entry = {
        'title': args.title,
        'slug': slug,
        'thumb': thumb_name,
        'date': date_str,
        'cat': args.category,
        'url': f'/blogs/{slug}/'
    }
    search_data.insert(0, search_entry)
    SEARCH_JSON.write_text(json.dumps(search_data, indent=2, ensure_ascii=False))
    SEARCH_JS.write_text(f'window.ALL_POSTS = {json.dumps(search_data, ensure_ascii=False)};\n')
    print('Updated search indexes.')

    # Rebuild site
    from scripts.build import main as build_site
    build_site()
    print(f'\nSuccess! New post is live at: /blogs/{slug}/')

if __name__ == '__main__':
    main()
