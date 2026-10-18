#!/usr/bin/env python3
"""Submit new or changed URLs to IndexNow (Bing, Yandex, Seznam, Naver).

Usage:
    python3 scripts/indexnow.py                 # every URL in sitemap.xml
    python3 scripts/indexnow.py /blogs/slug/ …  # specific paths or full URLs

Run after a deployment: the key file <key>.txt in the site root must be live
first, and the script checks that before submitting. Google does not read
IndexNow; request indexing for priority URLs in Search Console instead.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = 'thefitnessfalcon.com'
ENDPOINT = 'https://api.indexnow.org/indexnow'


def key_file():
    files = [p for p in ROOT.glob('*.txt') if re.fullmatch(r'[0-9a-f]{32}', p.stem)]
    if len(files) != 1:
        raise SystemExit('Expected exactly one 32-hex-character key file in the site root.')
    return files[0]


def sitemap_urls():
    return re.findall(r'<loc>(https://%s/[^<]*)</loc>' % re.escape(HOST), (ROOT / 'sitemap.xml').read_text())


def main(args):
    key_path = key_file()
    key = key_path.read_text().strip()
    key_location = f'https://{HOST}/{key_path.name}'
    with urllib.request.urlopen(key_location, timeout=30) as response:
        if response.read().decode().strip() != key:
            raise SystemExit(f'{key_location} does not serve the key; deploy first.')
    urls = [a if a.startswith('http') else f'https://{HOST}{a}' for a in args] or sitemap_urls()
    urls = sorted(set(urls))[:10000]
    body = json.dumps({'host': HOST, 'key': key, 'keyLocation': key_location, 'urlList': urls}).encode()
    request = urllib.request.Request(ENDPOINT, data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    print(f'IndexNow: submitted {len(urls)} URLs, HTTP {status} ({"accepted" if status in (200, 202) else "rejected"})')
    return 0 if status in (200, 202) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
