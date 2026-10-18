#!/usr/bin/env python3
"""Set each post's modified date to the last time its visible content changed.

The 6 October 2026 cleanup stamped that day's date on 174 imported posts, so
sitemap lastmod and dateModified stopped tracking real edits. Search engines
only trust these dates when they do. This script derives the date from
evidence instead of a build run:

- Walk the git history of content/posts/<slug>.json and find the oldest commit
  whose visible text (title, description, body, takeaways, FAQ and similar
  fields) is identical to the current file. Markup-only cleanups, thumbnail
  swaps and template changes do not count as modifications.
- If the text has not changed since the file was first committed, use the
  WordPress export's modified date for imported posts, or the publication time
  for articles first written on this site.
- A modified date is never earlier than the publication date.

Run before scripts/build.py so pages, schema, feed and sitemaps agree.
"""
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.restore_post_dates import load_wp_posts  # noqa: E402

POSTS = ROOT / 'content/posts'
METADATA_KEYS = {'slug', 'canonical_url', 'category', 'category_url', 'tags', 'read_time', 'comments_count',
                 'wp_id', 'cluster_id', 'cluster_role', 'author', 'author_role', 'author_bio', 'author_initial',
                 'author_gradient', 'featured_image', 'featured_image_alt', 'featured_image_width',
                 'featured_image_height', 'featured_image_caption', 'meta_title'}
METADATA_SUFFIXES = ('_time', '_iso', '_date', '_image', '_url')


def visible_text(value):
    if isinstance(value, str):
        text = re.sub(r'<[^>]+>', ' ', value)
        return re.sub(r'\s+', ' ', text).strip()
    if isinstance(value, list):
        return [visible_text(v) for v in value]
    if isinstance(value, dict):
        return {k: visible_text(v) for k, v in sorted(value.items())}
    return value


def signature(post):
    fields = {k: visible_text(v) for k, v in post.items()
              if k not in METADATA_KEYS and not k.endswith(METADATA_SUFFIXES)}
    return json.dumps(fields, sort_keys=True, ensure_ascii=False)


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def history(path):
    """Commits touching the file, newest first, as (hash, author date)."""
    out = git('log', '--format=%H%x09%aI', '--follow', '--', str(path.relative_to(ROOT)))
    return [tuple(line.split('\t')) for line in out.splitlines() if line]


def to_utc(iso):
    return datetime.fromisoformat(iso).astimezone(timezone.utc)


def fmt(dt):
    return {
        'modified_time': dt.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
        'modified_iso': dt.strftime('%Y-%m-%d'),
        'modified_date': f'{dt:%B} {dt.day}, {dt.year}',
    }


def last_content_change(path, current):
    """Return (datetime, reason) for the oldest commit that already had the current text."""
    commits = history(path)
    if not commits:
        return None, 'uncommitted'
    current_sig = signature(current)
    oldest_same = None
    for commit, date in commits:
        try:
            past = json.loads(git('show', f'{commit}:{path.relative_to(ROOT).as_posix()}'))
        except subprocess.CalledProcessError:
            break  # file was renamed/added here; earlier history is not this file
        if signature(past) != current_sig:
            break
        oldest_same = (commit, date)
    if oldest_same is None:
        # Working tree differs from HEAD: the change is happening now.
        return datetime.now(timezone.utc), 'working tree edit'
    if oldest_same[0] == commits[-1][0]:
        return None, 'unchanged since first commit'
    return to_utc(oldest_same[1]), f'commit {oldest_same[0][:8]}'


def restore(write=True):
    wp = load_wp_posts()
    changes, reasons = [], Counter()
    for path in sorted(POSTS.glob('*.json')):
        post = json.loads(path.read_text())
        published = to_utc(post.get('published_time') or post['published_iso'] + 'T00:00:00+00:00')
        when, reason = last_content_change(path, post)
        if when is None:
            record = wp.get(post['slug']) if post.get('wp_id') else None
            if record:
                when = datetime.strptime(record['mdate_gmt'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                reason = 'WordPress export modified date'
            else:
                when, reason = published, 'publication time'
        if when < published:
            when, reason = published, reason + ' (clamped to publication)'
        new = fmt(when)
        reasons[reason.split(' (')[0].split(' ')[0]] += 1
        old = {k: post.get(k) for k in new}
        if old != new:
            changes.append({'slug': post['slug'], 'from': old['modified_iso'], 'to': new['modified_iso'], 'reason': reason})
            if write:
                post.update(new)
                path.write_text(json.dumps(post, indent=2, ensure_ascii=False) + '\n')
    report = {'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'), 'posts': len(list(POSTS.glob('*.json'))),
              'changed': len(changes), 'sources': dict(reasons), 'changes': changes}
    (ROOT / 'audit' / f'modified-dates-{report["date"]}.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'{report["posts"]} posts; {len(changes)} modified dates corrected; sources: {dict(reasons)}')
    return report


if __name__ == '__main__':
    restore(write='--dry-run' not in sys.argv)
