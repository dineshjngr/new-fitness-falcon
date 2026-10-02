#!/usr/bin/env python3
"""
Verify and restore publication and modified dates for all 155 blog posts
against the authoritative WordPress export XML.
"""
import glob, json, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
XML_PATH = ROOT / 'old-website' / 'thefitnessfalcon.WordPress.2026-09-30.xml'
CONTENT_DIR = ROOT / 'content' / 'posts'

NAMESPACES = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'dc': 'http://purl.org/dc/elements/1.1/'
}

def load_wp_posts():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    wp_items = [
        i for i in root.findall('.//item')
        if i.find('wp:post_type', NAMESPACES) is not None
        and i.find('wp:post_type', NAMESPACES).text == 'post'
        and i.find('wp:status', NAMESPACES).text == 'publish'
    ]
    
    wp_map = {}
    for p in wp_items:
        slug = p.find('wp:post_name', NAMESPACES).text.strip()
        post_id = int(p.find('wp:post_id', NAMESPACES).text.strip())
        pdate = p.find('wp:post_date', NAMESPACES).text.strip()
        pdate_gmt = p.find('wp:post_date_gmt', NAMESPACES).text.strip()
        mdate = p.find('wp:post_modified', NAMESPACES).text.strip()
        mdate_gmt = p.find('wp:post_modified_gmt', NAMESPACES).text.strip()
        title = (p.find('title').text or '').strip()
        link = (p.find('link').text or '').strip()
        
        wp_map[slug] = {
            'post_id': post_id,
            'slug': slug,
            'title': title,
            'link': link,
            'pdate': pdate,
            'pdate_gmt': pdate_gmt,
            'mdate': mdate,
            'mdate_gmt': mdate_gmt
        }
    return wp_map

def restore_dates():
    wp_map = load_wp_posts()
    json_files = sorted(CONTENT_DIR.glob('*.json'))
    
    total_posts = len(json_files)
    correct_pub_already = []
    corrected_pub = []
    correct_mod_already = []
    corrected_mod = []
    unmatched = []
    
    for jf in json_files:
        data = json.loads(jf.read_text(encoding='utf-8'))
        slug = data.get('slug')
        
        # Match by slug
        wp_rec = wp_map.get(slug)
        if not wp_rec:
            # Fallback match by title
            title_lower = data.get('title', '').strip().lower()
            for cand in wp_map.values():
                if cand['title'].lower() == title_lower:
                    wp_rec = cand
                    break
        
        if not wp_rec:
            unmatched.append(slug)
            continue
            
        wp_pub_dt = datetime.strptime(wp_rec['pdate'], '%Y-%m-%d %H:%M:%S')
        wp_mod_dt = datetime.strptime(wp_rec['mdate'], '%Y-%m-%d %H:%M:%S')
        
        new_pub_date = wp_pub_dt.strftime('%B %d, %Y')
        new_pub_iso = wp_pub_dt.strftime('%Y-%m-%d')
        new_pub_time = wp_pub_dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        new_mod_date = wp_mod_dt.strftime('%B %d, %Y')
        new_mod_iso = wp_mod_dt.strftime('%Y-%m-%d')
        new_mod_time = wp_mod_dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        old_pub_iso = data.get('published_iso')
        old_pub_date = data.get('published_date')
        old_mod_iso = data.get('modified_iso')
        old_mod_date = data.get('modified_date')
        
        pub_was_correct = (old_pub_iso == new_pub_iso and old_pub_date == new_pub_date)
        mod_was_correct = (old_mod_iso == new_mod_iso and old_mod_date == new_mod_date)
        
        if pub_was_correct:
            correct_pub_already.append(slug)
        else:
            corrected_pub.append({
                'slug': slug,
                'old_date': old_pub_date,
                'new_date': new_pub_date,
                'old_iso': old_pub_iso,
                'new_iso': new_pub_iso
            })
            
        if mod_was_correct:
            correct_mod_already.append(slug)
        else:
            corrected_mod.append({
                'slug': slug,
                'old_date': old_mod_date,
                'new_date': new_mod_date,
                'old_iso': old_mod_iso,
                'new_iso': new_mod_iso
            })
            
        # Update JSON record while strictly preserving all other content & metadata
        data['published_date'] = new_pub_date
        data['published_iso'] = new_pub_iso
        data['published_time'] = new_pub_time
        data['modified_date'] = new_mod_date
        data['modified_iso'] = new_mod_iso
        data['modified_time'] = new_mod_time
        data['wp_id'] = wp_rec['post_id']
        
        jf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        
    print(f'=== RESTORATION SUMMARY ===')
    print(f'Total posts checked: {total_posts}')
    print(f'Posts with publication date correct already: {len(correct_pub_already)}')
    print(f'Posts whose publication date was corrected: {len(corrected_pub)}')
    print(f'Posts with modified date correct already: {len(correct_mod_already)}')
    print(f'Posts whose modified date was corrected: {len(corrected_mod)}')
    print(f'Posts that could not be matched confidently: {len(unmatched)}')
    
    return {
        'total': total_posts,
        'correct_pub_already': correct_pub_already,
        'corrected_pub': corrected_pub,
        'correct_mod_already': correct_mod_already,
        'corrected_mod': corrected_mod,
        'unmatched': unmatched
    }

if __name__ == '__main__':
    restore_dates()
