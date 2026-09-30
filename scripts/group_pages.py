#!/usr/bin/env python3
"""One-time migration of existing posts and landing pages into grouped folders."""
import json, re, shutil, zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parent.parent
EXCLUDED={'old-website','components','.git','node_modules'}

def main():
    if (ROOT/'blogs').exists():
        raise SystemExit('Grouping is already complete. Edit grouped pages directly; do not rerun a migration.')
    posts=json.loads((ROOT/'assets/search_index.json').read_text())
    mapping={f"/{p['slug']}/":f"/blogs/{p['slug']}/" for p in posts}
    landing=('contact-us','privacy-policy','team','write-for-us')
    mapping.update({f'/{name}/':f'/pages/{name}/' for name in landing})
    mapping['/blog/']='/blogs/'
    files=[p for p in ROOT.rglob('*.html') if not EXCLUDED.intersection(p.relative_to(ROOT).parts)]
    backup=Path('/private/tmp')/f"falcon-before-grouping-{datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files: z.write(p,p.relative_to(ROOT))
        for folder in ('components','scripts'):
            for p in (ROOT/folder).glob('*'):
                if p.is_file(): z.write(p,p.relative_to(ROOT))
        z.write(ROOT/'assets/search_index.json','assets/search_index.json')
    def transform_url(page,url):
        part=urlsplit(url)
        if not part.path or part.scheme or part.netloc:return url
        path=unquote(part.path)
        target=(ROOT/path.lstrip('/') if path.startswith('/') else page.parent/path).resolve()
        try:rel=target.relative_to(ROOT).as_posix()
        except ValueError:return url
        if rel.endswith('index.html'):rel=rel[:-10]
        elif rel.endswith('.html') and '/'+rel[:-5]+'/' in mapping:rel=rel[:-5]+'/'
        elif target.is_dir():rel=rel.rstrip('/')+'/'
        new=mapping.get('/'+rel,'/'+rel)
        return new+('?' + part.query if part.query else '')+('#'+part.fragment if part.fragment else '')
    for page in files:
        if page.parent==ROOT and page.name!='index.html':continue
        source=page.read_text()
        def chunk(text):
            return re.sub(r'\b(href|src|action|poster)=(["\'])(.*?)\2',lambda m:f'{m[1]}={m[2]}{transform_url(page,m[3])}{m[2]}',text)
        pieces=re.split(r'(<script\b[^>]*>.*?</script>)',source,flags=re.S|re.I)
        for i,piece in enumerate(pieces):
            if re.match(r'<script\b',piece,re.I):
                # Only rewrite the script element's src, never JavaScript string markup.
                end=piece.index('>')+1
                piece=chunk(piece[:end])+piece[end:]
                piece=re.sub(r'matches\.forEach\(function\(p\)\s*\{.*?\}\);', 'html = window.FalconSearch.render(matches);',piece,flags=re.S)
                piece=piece.replace("resultsBox.innerHTML = '<div style=\"padding: 16px; text-align: center; color: #64748b;\">No articles found matching \"' + query + '\"</div>';", "resultsBox.textContent = 'No articles found matching \"' + query + '\"';")
                pieces[i]=piece
            else:pieces[i]=chunk(piece)
        source=''.join(pieces)
        source=source.replace('</body>','<script src="/assets/js/search-results.js"></script>\n</body>')
        # Canonical metadata follows the new public route.
        old='/' + page.relative_to(ROOT).as_posix()
        if old.endswith('index.html'):old=old[:-10]
        new=mapping.get(old,old)
        if new!=old:source=source.replace('https://thefitnessfalcon.com'+old,'https://thefitnessfalcon.com'+new)
        page.write_text(source)
    for old,new in mapping.items():
        src=ROOT/old.strip('/'); dst=ROOT/new.strip('/')
        if old=='/blog/':
            dst.mkdir(exist_ok=True); shutil.move(src/'index.html',dst/'index.html'); src.rmdir()
        else:
            dst.parent.mkdir(exist_ok=True);shutil.move(src,dst)
    # Archive old flat redirect files instead of leaving them scattered in the root.
    redirects=ROOT/'old-website/legacy-redirects';redirects.mkdir(exist_ok=True)
    for p in ROOT.glob('*.html'):
        if p.name!='index.html':shutil.move(p,redirects/p.name)
    for entry in posts:entry['url']=f"/blogs/{entry['slug']}/"
    (ROOT/'assets/search_index.json').write_text(json.dumps(posts,ensure_ascii=False))
    for component in (ROOT/'components').glob('*.html'):
        component.write_text(chunk(component.read_text()))
    aliases={}
    for old,new in mapping.items():
        slug=old.strip('/')
        for alias in (old,old.rstrip('/'),old+'index.html','/'+slug+'.html'):aliases[alias]=new
    (ROOT/'audit/routes.json').write_text(json.dumps({'backup':str(backup),'redirects':aliases},indent=2))
    rules=['# Canonical blog and landing-page routes','DirectoryIndex index.html','<IfModule mod_rewrite.c>','RewriteEngine On']
    for old,new in mapping.items():
        slug=re.escape(old.strip('/'))
        rules.append(f'RewriteRule ^{slug}(?:/index\\.html|\\.html|/)?$ {new} [R=301,L,NE]')
    rules.append('</IfModule>')
    (ROOT/'.htaccess').write_text('\n'.join(rules)+'\n')
    (ROOT/'_redirects').write_text(''.join(f'{old} {new} 301\n' for old,new in sorted(aliases.items())))
    print(f'Moved {len(posts)} articles into blogs/, 4 landing pages into pages/, and the blog archive into blogs/index.html. Backup: {backup}')
if __name__=='__main__':main()
