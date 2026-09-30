#!/usr/bin/env python3
"""Normalize existing static pages without regenerating their content."""
import json, re, shutil, zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {'components', 'old-website', '.git', 'node_modules'}

def pages():
    return sorted(p for p in ROOT.rglob('*.html') if not EXCLUDED.intersection(p.relative_to(ROOT).parts))

def destination(page, url):
    part = urlsplit(url)
    if part.scheme or part.netloc or not part.path:
        return None
    path = unquote(part.path)
    target = (ROOT / path.lstrip('/') if path.startswith('/') else page.parent / path).resolve()
    if target.is_dir(): target /= 'index.html'
    return target

def route(target):
    path = target.relative_to(ROOT).as_posix()
    return '/' + (path[:-10] if path.endswith('index.html') else path)

def main():
    if (ROOT/'blogs').exists():
        raise SystemExit('Grouping is already complete. Edit grouped pages directly; do not rerun a migration.')
    originals = pages()
    backup = Path('/private/tmp') / ('falcon-before-organization-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip')
    with zipfile.ZipFile(backup, 'w', zipfile.ZIP_DEFLATED) as archive:
        for page in originals: archive.write(page, page.relative_to(ROOT))
        for page in ROOT.glob('*.py'): archive.write(page, page.relative_to(ROOT))
        for page in (ROOT/'components').glob('*'):
            if page.is_file(): archive.write(page, page.relative_to(ROOT))
    legacy = ROOT/'old-website'/'legacy-pages'
    legacy.mkdir(exist_ok=True)
    changes = {'backup':str(backup), 'aliases':[], 'disabled_links':[], 'fixed_assets':[]}
    # Preserve historical flat URLs, but keep content in the folder route only.
    for page in ROOT.glob('*.html'):
        if page.name == 'index.html': continue
        canonical = ROOT/page.stem/'index.html'
        if not canonical.exists() and page.stem != 'about-us':
            canonical.parent.mkdir(exist_ok=True)
            text = page.read_text()
            text = re.sub(r'((?:src|href|action)=["\'])(?![a-z]+:|/|#)([^"\']+)', lambda m:m[1]+'../'+m[2], text)
            canonical.write_text(text)
        if not (legacy/page.name).exists(): shutil.copy2(page, legacy/page.name)
        if page.stem == 'about-us':
            page.unlink()
            continue
        url = route(canonical)
        page.write_text(f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Page moved - The Fitness Falcon</title><link rel="canonical" href="https://thefitnessfalcon.com{url}"><meta http-equiv="refresh" content="0;url={url}"></head><body><p>This page has moved. <a href="{url}">Continue to the page</a>.</p><script>location.replace({json.dumps(url)} + location.search + location.hash);</script></body></html>\n')
        changes['aliases'].append({'from':'/'+page.name,'to':url})
    for page in pages():
        if page.parent == ROOT and page.name != 'index.html': continue
        source = page.read_text()
        def anchor(match):
            attrs, content = match.group(1), match.group(2)
            href = re.search(r'\bhref=(["\'])(.*?)\1',attrs,re.S)
            if not href: return match[0]
            url = href[2]; target = destination(page,url)
            if target is None: return match[0]
            if target.name.endswith('.html') and target.name != 'index.html' and (ROOT/target.stem/'index.html').exists(): target = ROOT/target.stem/'index.html'
            if target.exists():
                new_url = route(target)
                part = urlsplit(url)
                if part.query: new_url += '?'+part.query
                if part.fragment: new_url += '#'+part.fragment
                return '<a'+attrs[:href.start()]+f'href="{new_url}"'+attrs[href.end():]+'>'+content+'</a>'
            if unquote(url).rstrip('/').endswith('swimming'):
                return '<a'+attrs[:href.start()]+'href="/category/swimming/"'+attrs[href.end():]+'>'+content+'</a>'
            # Keep content text, but do not send readers to a missing page.
            if '/uploads/' in str(target):
                asset = ROOT/'assets/images'/target.parent.name
                if asset.exists(): return '<a'+attrs[:href.start()]+f'href="{route(asset)}"'+attrs[href.end():]+'>'+content+'</a>'
            changes['disabled_links'].append({'page':str(page.relative_to(ROOT)),'url':url})
            safe = re.sub(r'\s*(?:href|target|rel|onclick)=(["\']).*?\1', '', attrs, flags=re.S)
            return '<span'+safe+'>'+content+'</span>'
        source = re.sub(r'<a\b([^>]*)>(.*?)</a>',anchor,source,flags=re.S|re.I)
        def asset(match):
            attr, quote, url = match.groups()
            target = destination(page,url)
            if target is None or target.exists(): return match[0]
            if 'assets/images' not in str(target): return match[0]
            filename = target.name
            candidate = re.sub(r'-\d+x\d+(?=\.[^.]+$)', '',filename)
            if filename == 'AdobeStock_126977674-scaled.jpeg': candidate = 'Acne-101-Understanding-Different-Types-Causes-and-Effective-Treatments.png'
            replacement = ROOT/'assets/images'/candidate
            if not replacement.exists(): return match[0]
            changes['fixed_assets'].append({'page':str(page.relative_to(ROOT)),'from':url,'to':route(replacement)})
            return f'{attr}={quote}{route(replacement)}{quote}'
        source = re.sub(r'\b(src|poster)=(["\'])(.*?)\2',asset,source)
        page.write_text(source)
    # Ensure shared includes cannot reintroduce deleted About Us links.
    for component in (ROOT/'components').glob('*.html'):
        source=component.read_text()
        source=re.sub(r'<a\b[^>]*href=["\'][^"\']*about-us[^"\']*["\'][^>]*>(.*?)</a>',r'<span>\1</span>',source,flags=re.S)
        component.write_text(source)
    (ROOT/'audit'/'organization.json').write_text(json.dumps(changes,indent=2))
    print(f"Preserved {len(changes['aliases'])} legacy URLs; corrected {len(changes['fixed_assets'])} images; unlinked {len(changes['disabled_links'])} unavailable destinations.")
    print(f'Backup: {backup}')
if __name__ == '__main__': main()
