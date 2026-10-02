#!/usr/bin/env python3
"""Check all static routes, local resources, CSS dependencies and search entries."""
import json, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parent.parent
EXCLUDED={'old-website','components','.git','node_modules','scratch'}
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.counts={}; self.shell={'header':0,'footer':0}
    def handle_starttag(self,tag,attrs):
        self.counts[tag]=self.counts.get(tag,0)+1
        if tag in self.shell and any(key=='class' and ('benqu-main-header' in value or 'benqu-footer' in value or 'falcon-footer' in value) for key,value in attrs): self.shell[tag]+=1
        for key,value in attrs:
            if not value: continue
            if key in ('href','src','poster','action'): self.refs.append(value)
            elif key=='srcset': self.refs.extend(item.strip().split()[0] for item in value.split(',') if item.strip())
def resolve(page,url):
    part=urlsplit(url)
    if part.scheme or part.netloc or not part.path: return None
    target=(ROOT/unquote(part.path).lstrip('/') if part.path.startswith('/') else page.parent/unquote(part.path)).resolve()
    if target.is_dir(): target/='index.html'
    return target

def main():
    errors=[]; checked=0
    pages=sorted(p for p in ROOT.rglob('*.html') if not EXCLUDED.intersection(p.relative_to(ROOT).parts))
    canonical=[]
    for page in pages:
        parser=Parser(); parser.feed(page.read_text())
        if page.name=='index.html':
            canonical.append(page)
            for tag in ('html','head','body'):
                if parser.counts.get(tag)!=1: errors.append(f'{page.relative_to(ROOT)}: expected one {tag}, found {parser.counts.get(tag,0)}')
        if page.name=='index.html':
            for tag,count in parser.shell.items():
                if count!=1: errors.append(f'{page.relative_to(ROOT)}: expected one site {tag}, found {count}')
        for url in parser.refs:
            target=resolve(page,url)
            if target is not None:
                checked+=1
                if not target.is_file(): errors.append(f'{page.relative_to(ROOT)}: missing {url}')
    for css in (ROOT/'assets/css').glob('*.css'):
        for url in re.findall(r'url\(\s*["\']?([^\)"\']+)',css.read_text()):
            target=resolve(css,url.strip())
            if target is not None:
                checked+=1
                if not target.is_file(): errors.append(f'{css.relative_to(ROOT)}: missing {url}')
    data=json.loads((ROOT/'assets/search_index.json').read_text())
    for entry in data:
        for path in (ROOT/entry.get('url', '/blogs/'+entry['slug']+'/').strip('/')/'index.html',ROOT/'assets/images'/entry['thumb']):
            checked+=1
            if not path.is_file(): errors.append(f'search index: missing {path.relative_to(ROOT)}')
    if (ROOT/'about-us').exists() or (ROOT/'about-us.html').exists() or (ROOT/'pages/about-us').exists(): errors.append('Deleted About Us page was restored')
    routes=json.loads((ROOT/'audit/routes.json').read_text())['redirects'] if (ROOT/'audit/routes.json').exists() else {}
    for old,new in routes.items():
        checked+=1
        if not (ROOT/new.strip('/')/'index.html').is_file(): errors.append(f'redirect {old}: missing target {new}')
    result={'compatibility_redirects':len(routes),'canonical_pages':len(canonical),'legacy_redirects':len(pages)-len(canonical),'local_references_checked':checked,'search_entries':len(data),'errors':sorted(set(errors))}
    (ROOT/'audit/validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return bool(errors)
if __name__=='__main__': sys.exit(main())
