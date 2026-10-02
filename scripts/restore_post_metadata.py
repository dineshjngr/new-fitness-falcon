#!/usr/bin/env python3
"""
Verify and restore WordPress metadata parity for all 155 blog posts
against the authoritative WordPress export XML (thefitnessfalcon.WordPress.2026-09-30 (10).xml).
"""
import xml.etree.ElementTree as ET
import json, re, html, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
XML_PATH = ROOT / 'old-website' / 'thefitnessfalcon.WordPress.2026-09-30 (10).xml'
CONTENT_DIR = ROOT / 'content' / 'posts'

NS = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'excerpt': 'http://purl.org/rss/1.0/modules/excerpt/'
}

def safe_find(el, path):
    child = el.find(path, NS)
    return child.text.strip() if (child is not None and child.text) else ''

def sync_wordpress_parity():
    print(f"Reading authoritative WordPress export: {XML_PATH.name}...")
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    # 1. Attachment alt texts
    attachments_alt = {}
    for it in root.findall('.//item'):
        if safe_find(it, 'wp:post_type') == 'attachment':
            aid = safe_find(it, 'wp:post_id')
            alt = ''
            for m in it.findall('wp:postmeta', NS):
                if safe_find(m, 'wp:meta_key') == '_wp_attachment_image_alt':
                    alt = safe_find(m, 'wp:meta_value')
            if aid and alt:
                attachments_alt[aid] = alt

    # 2. Process all published posts
    posts_updated = 0
    total_posts = 0
    updated_posts_list = []

    for it in root.findall('.//item'):
        if safe_find(it, 'wp:post_type') == 'post' and safe_find(it, 'wp:status') == 'publish':
            total_posts += 1
            slug = safe_find(it, 'wp:post_name')
            pdate = safe_find(it, 'wp:post_date')
            mdate = safe_find(it, 'wp:post_modified')
            creator = safe_find(it, 'dc:creator')
            
            # Find thumbnail ID
            tid = None
            for m in it.findall('wp:postmeta', NS):
                if safe_find(m, 'wp:meta_key') == '_thumbnail_id':
                    tid = safe_find(m, 'wp:meta_value')
                    break

            jfile = CONTENT_DIR / f"{slug}.json"
            if not jfile.exists():
                print(f"WARNING: Post JSON missing on disk for slug: {slug}", file=sys.stderr)
                continue

            jdata = json.loads(jfile.read_text(encoding='utf-8'))
            changed = False

            # Check and update alt text from original WP attachment
            if tid and tid in attachments_alt and attachments_alt[tid]:
                wp_alt = attachments_alt[tid]
                if jdata.get('featured_image_alt') != wp_alt:
                    jdata['featured_image_alt'] = wp_alt
                    changed = True

            # Double-check publication date
            wp_pdt = datetime.strptime(pdate, '%Y-%m-%d %H:%M:%S')
            wp_pub_iso = wp_pdt.strftime('%Y-%m-%d')
            wp_pub_date = wp_pdt.strftime('%B %d, %Y')
            if jdata.get('published_iso') != wp_pub_iso or jdata.get('published_date') != wp_pub_date:
                jdata['published_iso'] = wp_pub_iso
                jdata['published_date'] = wp_pub_date
                changed = True

            # Double-check modified date
            wp_mdt = datetime.strptime(mdate, '%Y-%m-%d %H:%M:%S')
            wp_mod_iso = wp_mdt.strftime('%Y-%m-%d')
            wp_mod_date = wp_mdt.strftime('%B %d, %Y')
            if jdata.get('modified_iso') != wp_mod_iso or jdata.get('modified_date') != wp_mod_date:
                jdata['modified_iso'] = wp_mod_iso
                jdata['modified_date'] = wp_mod_date
                changed = True

            if changed:
                jfile.write_text(json.dumps(jdata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
                posts_updated += 1
                updated_posts_list.append(slug)

    print(f"Sync complete. Total posts verified: {total_posts}")
    print(f"Total post files updated: {posts_updated}")
    return total_posts, posts_updated, updated_posts_list

if __name__ == '__main__':
    sync_wordpress_parity()
