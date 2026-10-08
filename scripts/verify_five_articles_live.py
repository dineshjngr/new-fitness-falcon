"""Verify the five October 8 articles and their discovery surfaces over HTTPS."""
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ['minimum-effective-strength-training-beginners', 'creatine-for-women-benefits-water-weight-safety', '7000-vs-10000-steps-daily-walking-goal', 'pre-workout-caffeine-sleep-dose-timing', 'should-you-work-out-when-sore-doms']
paths = ['index.html', 'blogs/index.html', 'sitemap.xml', 'post-sitemap.xml', 'assets/search_index.json', 'robots.txt']
for slug in SLUGS:
    post = json.loads((ROOT/'content/posts'/f'{slug}.json').read_text())
    paths.extend([f'blogs/{slug}/index.html', post['featured_image'].lstrip('/')])
paths.extend(f'blogs/{slug}/index.html' for slug in ['progressive-overload-for-beginners-increase-weight-reps-sets', 'the-ultimate-guide-to-plant-protein-for-womens-health', '10000-steps-walking-pad-how-long', 'how-to-sleep-better-at-night-naturally', 'returning-to-the-gym-after-a-long-break-first-four-weeks', 'walking-pad-beginner-routine'])
out = Path('/private/tmp/falcon-five-live')
out.mkdir(exist_ok=True)

def check(path):
    url = 'https://thefitnessfalcon.com/' + path.removesuffix('index.html')
    dest = out/path
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(['curl', '-sS', '-L', '--max-time', '45', '-w', '%{http_code}', '-o', str(dest), url], capture_output=True, text=True)
    match = not result.returncode and dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest() == hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    image_valid = False
    if not result.returncode and dest.is_file() and path.endswith('.jpg'):
        dimensions = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', str(dest)], capture_output=True, text=True)
        image_valid = dimensions.returncode == 0 and 'pixelWidth: 1600' in dimensions.stdout and 'pixelHeight: 900' in dimensions.stdout
    # Hostinger's CDN recompresses JPEGs; HTML and discovery files must match exactly.
    return dict(path=path, url=url, status=result.stdout, exact_match=bool(match), image_dimensions_valid=image_valid, ok=result.stdout=='200' and bool(match or image_valid), error=result.stderr if result.returncode else None)

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(check, paths))
(ROOT/'audit/five-articles-live-publication-2026-10-08.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
passed = all(item['ok'] for item in results)
print('ALL PASS', passed)
raise SystemExit(0 if passed else 1)
