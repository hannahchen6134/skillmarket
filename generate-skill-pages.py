#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate-skill-pages.py
═══════════════════════════════════════════════════════════════════
從 Google Sheet 抓「上架清單」L 欄已核准的服務，產生兩件東西：

1. skill/<slug>.html × N 個 — 每個服務的 OG 預覽頁
   讓 LINE / FB / IG / Threads 分享單一服務時顯示專屬預覽。

2. data/skills.json — 給 index.html 直接讀取的快取
   訪客打開網站時不再直接打 Google Sheets，省下 API 配額、
   而且 GitHub 的 CDN 比 gviz 快很多。

GitHub Action 每 5 分鐘自動跑這個腳本。
"""

import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ════════════════════════════════════════════════════════════════
# 設定
# ════════════════════════════════════════════════════════════════
SHEET_ID = '1RHTyeA9kfmU7nxQjmnZoDSbNP1eSssYPis2bJm9utrk'
TAB_NAME = '上架清單'
SITE_BASE = 'https://hannahchen6134.github.io/skillmarket'
ROOT_DIR = Path(__file__).parent
OUTPUT_DIR = ROOT_DIR / 'skill'   # 每個服務的 OG 預覽頁
DATA_DIR = ROOT_DIR / 'data'      # 給網站讀的快取 JSON
OG_IMAGE_URL = f'{SITE_BASE}/starry-hall.jpg'

# 分類中文 → 短代碼（須與 index.html 的 CATEGORY_MAP 完全一致）
CATEGORY_MAP = {
    '設計與創意': 'design',
    '心靈成長': 'wellness',
    '語言文化': 'language',
    '職涯發展': 'career',
    '文創技能': 'creative',
    '個人成長': 'growth',
    '生活風格': 'lifestyle',
    '運動健身': 'fitness',
    '其他技能': 'other',
    '其他': 'other',
}

# L 欄（index 11）支援的「已核准」值
APPROVED_VALUES = {
    'TRUE', 'true', '是', '✅', '1', '上架', '已核准', '核准',
    'YES', 'yes', 'Y', True, 1,
}


# ════════════════════════════════════════════════════════════════
# Slug 函數 — 須與 index.html 內 JS 版本完全一致
# ════════════════════════════════════════════════════════════════
def slugify(title):
    """把服務名稱轉成檔名安全的 slug（保留中文，過濾路徑/控制字元）"""
    if not title:
        return 'untitled'
    s = re.sub('[\\s/\\\\:?*<>|"\\x00-\\x1f]+', '-', title)
    s = re.sub(r'-+', '-', s).strip('-')
    s = s[:80]
    return s or 'untitled'


# ════════════════════════════════════════════════════════════════
# 抓 Google Sheet（gviz JSON API）
# ════════════════════════════════════════════════════════════════
def fetch_sheet():
    url = (
        f'https://docs.google.com/spreadsheets/d/{SHEET_ID}'
        f'/gviz/tq?tqx=out:json&headers=1&sheet={urllib.parse.quote(TAB_NAME)}'
    )
    print(f'→ fetch {url}')
    req = urllib.request.Request(url, headers={'User-Agent': 'skillmarket-bot/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')

    m = re.search(r'setResponse\((.+)\);?\s*$', raw, re.DOTALL)
    if not m:
        raise RuntimeError('Invalid gviz response — sheet must be public')
    data = json.loads(m.group(1))
    return data.get('table', {}).get('rows', [])


def is_approved(cell):
    if not cell:
        return False
    v = cell.get('v')
    if v in (None, ''):
        return False
    if v is True:
        return True
    return str(v).strip() in APPROVED_VALUES


def get_cell(row_cells, idx):
    if idx >= len(row_cells) or not row_cells[idx]:
        return ''
    v = row_cells[idx].get('v')
    return str(v).strip() if v not in (None, '') else ''


# ════════════════════════════════════════════════════════════════
# OG description 組合
# ════════════════════════════════════════════════════════════════
def truncate(s, n):
    s = (s or '').strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def build_description(data):
    head_parts = []
    if data['provider']:
        head_parts.append(f'by {data["provider"]}')
    if data['category']:
        head_parts.append(data['category'])
    if data['mode']:
        head_parts.append(data['mode'])
    if data['duration']:
        head_parts.append(data['duration'])
    if data['capacity']:
        head_parts.append(data['capacity'])
    header = ' · '.join(head_parts)
    body = truncate(data['desc'] or data['bio'] or '', 110)
    if header and body:
        return f'{header}｜{body}'
    return header or body or '初星群 · 技能交換公會'


# ════════════════════════════════════════════════════════════════
# HTML 模板（每個服務的 OG 預覽頁）
# ════════════════════════════════════════════════════════════════
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 初星群技能交換公會</title>
<meta name="description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:locale" content="zh_TW">
<meta property="og:site_name" content="初星群 · 技能交換公會">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:secure_url" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_title}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">
<meta name="twitter:image:alt" content="{og_title}">
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0; url={redirect}">
<script>
  (function () {{
    try {{ location.replace({redirect_json}); }} catch (e) {{}}
  }})();
</script>
<style>
  body {{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         background:#0a0805; color:rgba(232,181,77,0.85);
         font-family:'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
         font-size:14px; letter-spacing:0.05em; }}
  a {{ color: rgba(232,181,77,0.95); }}
</style>
</head>
<body>
<noscript><p>請點擊：<a href="{redirect}">{title}</a></p></noscript>
<p>正在前往 <strong>{title}</strong>…</p>
</body>
</html>
'''


def html_escape(s):
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('"', '&quot;')
             .replace("'", '&#39;'))


# ════════════════════════════════════════════════════════════════
# 主程式
# ════════════════════════════════════════════════════════════════
def main():
    rows = fetch_sheet()
    print(f'→ got {len(rows)} rows')

    OUTPUT_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    existing = {p.name for p in OUTPUT_DIR.glob('*.html')}
    written = set()
    manifest = []
    skills_data = []

    has_approval_col = any(
        len(r.get('c') or []) > 11 and r['c'][11] and r['c'][11].get('v') not in (None, '')
        for r in rows
    )

    used_slugs = {}
    for row in rows:
        c = row.get('c') or []
        if not c or not c[0] or c[0].get('v') in (None, ''):
            continue
        if has_approval_col and not is_approved(c[11] if len(c) > 11 else None):
            continue

        data = {
            'title':        get_cell(c, 0),
            'provider':     get_cell(c, 1),
            'social':       get_cell(c, 2),
            'category':     get_cell(c, 3),
            'duration':     get_cell(c, 4),
            'mode':         get_cell(c, 5),
            'capacity':     get_cell(c, 6),
            'availability': get_cell(c, 7),
            'desc':         get_cell(c, 8),
            'bio':          get_cell(c, 9),
            'wants':        get_cell(c, 10),
        }
        title = data['title']
        if not title:
            continue

        if data['mode'] in ('都可', '線上線下都可'):
            data['mode'] = '線上／線下'

        slug = slugify(title)
        if slug in used_slugs:
            short_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:6]
            slug = f'{slug}-{short_hash}'
        used_slugs[slug] = title

        filename = f'{slug}.html'
        canonical = f'{SITE_BASE}/skill/{urllib.parse.quote(slug)}.html'
        redirect = f'{SITE_BASE}/#s/{urllib.parse.quote(title)}'

        og_title = title + (f' · by {data["provider"]}' if data['provider'] else '')
        description = build_description(data)

        html = HTML_TEMPLATE.format(
            title=html_escape(title),
            og_title=html_escape(og_title),
            description=html_escape(description),
            og_image=OG_IMAGE_URL,
            canonical=canonical,
            redirect=html_escape(redirect),
            redirect_json=json.dumps(redirect),
        )

        (OUTPUT_DIR / filename).write_text(html, encoding='utf-8', newline='\n')
        written.add(filename)

        manifest.append({
            'title': title,
            'provider': data['provider'],
            'category': data['category'],
            'slug': slug,
            'url': f'skill/{urllib.parse.quote(slug)}.html',
        })

        skills_data.append({
            'title':         title,
            'provider':      data['provider'],
            'social':        data['social'],
            'category':      CATEGORY_MAP.get(data['category'], 'other'),
            'categoryLabel': data['category'] or '其他',
            'duration':      data['duration'],
            'mode':          data['mode'],
            'capacity':      data['capacity'],
            'availability':  data['availability'],
            'desc':          data['desc'],
            'bio':           data['bio'],
            'wants':         data['wants'],
            'isExample':     False,
        })

        print(f'✓ {filename}  ←  {title}')

    removed = []
    for orphan in existing - written - {'manifest.json'}:
        (OUTPUT_DIR / orphan).unlink()
        removed.append(orphan)
        print(f'✗ removed: {orphan}')

    (OUTPUT_DIR / 'manifest.json').write_text(
        json.dumps({'version': 1, 'skills': manifest}, ensure_ascii=False, indent=2),
        encoding='utf-8', newline='\n')

    (DATA_DIR / 'skills.json').write_text(
        json.dumps({
            'version': 1,
            'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'skills': skills_data,
        }, ensure_ascii=False, indent=2),
        encoding='utf-8', newline='\n')

    print(f'\n— done. wrote {len(written)} pages, {len(skills_data)} skills cached, removed {len(removed)} stale.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
