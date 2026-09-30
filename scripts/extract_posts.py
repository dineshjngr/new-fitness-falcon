#!/usr/bin/env python3
"""
Extract existing blog posts data from blogs/*/index.html into content/posts/<slug>.json.
Preserves all original article content, images, headings, tables, and metadata cleanly.
"""
import os, sys, re, json, html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
BLOGS_DIR = ROOT / 'blogs'
CONTENT_DIR = ROOT / 'content' / 'posts'

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

def extract_post(post_file):
    txt = post_file.read_text(encoding='utf-8')
    slug = post_file.parent.name
    
    # 1. Title & H1
    title_m = re.search(r'<title>(.*?)(?:\s*-\s*The Fitness Falcon)?</title>', txt, re.I)
    raw_title = title_m.group(1).strip() if title_m else slug.replace('-', ' ').title()
    raw_title = re.sub(r'\s*-\s*The Fitness Falcon$', '', raw_title).strip()
    raw_title = html.unescape(raw_title)
    
    h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', txt, re.DOTALL)
    h1_title = h1_m.group(1).strip() if h1_m else raw_title
    h1_title = html.unescape(h1_title)
    
    # 2. Description
    desc_m = re.search(r'<meta\s+name=[\"\']description[\"\']\s+content=[\"\'](.*?)[\"\']', txt, re.I)
    desc = desc_m.group(1).strip() if desc_m else ''
    desc = html.unescape(desc)
    
    # 3. Category & Category URL
    cat_m = re.search(r'<a[^>]+class=[\"\'][^\"\']*category-badge[^\"\']*[\"\'][^>]*>(.*?)</a>', txt)
    cat_name = cat_m.group(1).strip() if cat_m else 'Fitness'
    cat_name = html.unescape(cat_name)
    
    cat_url_m = re.search(r'<a[^>]+href=[\"\'](/category/[^/\"\']+/?)[\"\'][^>]*class=[\"\'][^\"\']*category-badge', txt) or \
                re.search(r'<a[^>]+class=[\"\'][^\"\']*category-badge[^\"\']*[\"\'][^>]+href=[\"\'](/category/[^/\"\']+/?)[\"\']', txt)
    cat_url = cat_url_m.group(1).strip() if cat_url_m else '/category/fitness/'
    if not cat_url.endswith('/'):
        cat_url += '/'
    
    # 4. Author
    author_m = re.search(r'By\s+([^<]+)</span>', txt)
    author = author_m.group(1).strip() if author_m else 'Dinesh'
    if 'by ' in author.lower():
        author = re.sub(r'(?i)by\s+', '', author).strip()
    if author not in AUTHOR_INFO:
        author = 'Dinesh'
        
    # 5. Published Date
    date_m = re.search(r'fa-calendar-alt[^>]*></i>\s*([^<]+)</span>', txt)
    date_str = date_m.group(1).strip() if date_m else 'September 30, 2026'
    try:
        dt = datetime.strptime(date_str, '%B %d, %Y')
        iso_date = dt.strftime('%Y-%m-%d')
    except Exception:
        iso_date = '2026-09-30'
        
    # 6. Read Time
    read_m = re.search(r'fa-clock[^>]*></i>\s*(\d+)\s*min read', txt)
    read_time = int(read_m.group(1)) if read_m else 4
    
    # 7. Comments count
    comm_m = re.search(r'fa-comments[^>]*></i>\s*(\d+)\s*Comments?', txt)
    comments_count = int(comm_m.group(1)) if comm_m else 0
    
    # 8. Featured image & alt
    img_m = re.search(r'<article[^>]*>.*?<img\s+src=[\"\']([^\"]+)[\"\']\s+alt=[\"\'](.*?)[\"\']', txt, re.DOTALL)
    if img_m:
        featured_img = img_m.group(1).strip()
        img_alt = img_m.group(2).strip()
    else:
        featured_img = '/assets/images/1-1.png'
        img_alt = h1_title
        
    # Normalize featured image to root-relative /assets/images/...
    if featured_img.startswith('../../assets/'):
        featured_img = '/' + featured_img.replace('../../', '')
    elif featured_img.startswith('../assets/'):
        featured_img = '/' + featured_img.replace('../', '')
    elif not featured_img.startswith('/assets/'):
        featured_img = '/assets/images/' + featured_img.lstrip('/')
        
    # 9. Entry content
    m_content = re.search(r'<div class=[\"\']entry-content[\"\']>(.*?)</div>\s*(?:<div style=[\"\']margin-top: 40px;|<div class=[\"\']falcon-tags|<div style=[\"\']background: #f8fafc;|<article|</main)', txt, re.DOTALL)
    if m_content:
        content = m_content.group(1).strip()
    else:
        raise ValueError(f'Could not find entry-content in {slug}')
        
    # 10. Tags: accurately extract from the Tags block only
    tags = []
    tags_block = re.search(r'Tags:</strong>(.*?)(?:</div>)', txt, re.DOTALL)
    if tags_block:
        tags = [t.strip() for t in re.findall(r'>\s*#([^<]+)</span>', tags_block.group(1)) if t.strip()]
        
    return {
        'slug': slug,
        'title': h1_title,
        'meta_title': f'{h1_title} - The Fitness Falcon',
        'description': desc,
        'canonical_url': f'https://thefitnessfalcon.com/blogs/{slug}/',
        'category': cat_name,
        'category_url': cat_url,
        'author': author,
        'author_role': AUTHOR_INFO[author]['role'],
        'author_bio': AUTHOR_INFO[author]['bio'],
        'author_initial': AUTHOR_INFO[author]['initial'],
        'author_gradient': AUTHOR_INFO[author]['gradient'],
        'published_date': date_str,
        'published_iso': iso_date,
        'modified_date': date_str,
        'modified_iso': iso_date,
        'read_time': read_time,
        'comments_count': comments_count,
        'featured_image': featured_img,
        'featured_image_alt': img_alt if img_alt else h1_title,
        'tags': tags,
        'content': content
    }

def main():
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    post_files = sorted(BLOGS_DIR.glob('*/index.html'))
    print(f'Extracting clean data for {len(post_files)} posts...')
    
    extracted = []
    for pf in post_files:
        data = extract_post(pf)
        out_file = CONTENT_DIR / f"{data['slug']}.json"
        out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        extracted.append(data)
        
    # Also write a combined data/posts.json
    data_dir = ROOT / 'data'
    data_dir.mkdir(exist_ok=True)
    (data_dir / 'posts.json').write_text(json.dumps(extracted, indent=2, ensure_ascii=False))
    
    print(f'Successfully wrote {len(extracted)} post files to {CONTENT_DIR.relative_to(ROOT)} and data/posts.json.')

if __name__ == '__main__':
    main()
