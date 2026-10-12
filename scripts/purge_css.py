#!/usr/bin/env python3
"""Trim unused rules from vendor stylesheets with PurgeCSS.

Originals: old-website/css-full/ (never edited). Output: assets/css/ (same
file names, so stylesheet URLs do not change). Re-run after adding new
templates or icons:  python3 scripts/purge_css.py
Font Awesome's upstream file has malformed @font-face blocks that browsers
recover from; those blocks are copied verbatim and only icon rules are purged.
"""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FULL = ROOT / 'old-website/css-full'
OUT = ROOT / 'assets/css'


def split_font_awesome():
    s = (FULL / 'all.min.css').read_text()
    a_end = s.index('@font-face')
    brands_end = s.index('}', a_end) + 1
    duo_start = s.index('@font-face', brands_end)
    duo_ff_end = s.index('}', duo_start) + 1
    tail_start = s.index('@font-face', duo_ff_end)
    (FULL / 'fa-icons.css').write_text(s[:a_end])
    (FULL / 'fa-duotone.css').write_text(s[duo_ff_end:tail_start])
    return s[a_end:duo_start], s[duo_start:duo_ff_end], s[tail_start:]


def main():
    brands_ff, duo_ff, tail = split_font_awesome()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['npx', '--yes', 'purgecss@6.0.0', '--config', 'scripts/purge.config.cjs', '--output', tmp],
                       cwd=ROOT, check=True)
        tmp = Path(tmp)
        icons = (tmp / 'fa-icons.css').read_text()
        duotone = (tmp / 'fa-duotone.css').read_text()
        (OUT / 'all.min.css').write_text(icons + brands_ff + duo_ff + duotone + tail)
        for name in ('bootstrap.min.css', 'benqu-style.css', 'responsive.css'):
            (OUT / name).write_text((tmp / name).read_text())
    for name in ('all.min.css', 'bootstrap.min.css', 'benqu-style.css', 'responsive.css'):
        print(f'{name}: {(FULL / name).stat().st_size:,} -> {(OUT / name).stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
