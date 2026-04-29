#!/usr/bin/env python3
"""
Mintlify docs sanity checks. Bundles three checks:

  1. Nav consistency — every docs.json path has a .mdx file, every .mdx is in nav
  2. JSX-fake detection — bare `<NUM>` or `<token>` patterns that MDX parses as tags
  3. Frontmatter completeness — every page has title + description

Usage:
    python docs/mint/scripts/check_docs.py
"""
import json, os, re, sys, subprocess

def _git_root():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--show-toplevel'],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

ROOT = _git_root()
DOCS = os.path.join(ROOT, 'docs', 'mint')
NAV  = os.path.join(DOCS, 'docs.json')

def collect_nav_pages():
    pages = []
    def walk(o):
        if isinstance(o, dict):
            if 'pages' in o: pages.extend(p for p in o['pages'] if isinstance(p, str))
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(json.load(open(NAV)))
    return pages

SKIP_DIRS = {'snippets', 'scripts'}

def _iter_mdx(skip_dirs=True):
    """Yield (path, rel_no_ext) for every .mdx (skipping snippets/scripts when requested)."""
    for r, _, fs in os.walk(DOCS):
        rel_root = os.path.relpath(r, DOCS)
        if skip_dirs and any(p in SKIP_DIRS for p in rel_root.split(os.sep)): continue
        for f in fs:
            if f.endswith('.mdx'):
                path = os.path.join(r, f)
                rel = os.path.relpath(path, DOCS).replace('.mdx', '')
                yield path, rel

def collect_mdx_files():
    return [rel for _, rel in _iter_mdx()]

def check_nav():
    nav = collect_nav_pages()
    files = set(collect_mdx_files())
    missing = [p for p in nav if p not in files]
    orphan = [f for f in files if f not in nav]
    return missing, orphan

# Bare angle-bracket numbers/tokens that MDX parses as JSX:
#   <30, <200줄, <foo  (only inside prose, not in `code`, not in <...> attrs)
_JSX_FAKE_RE = re.compile(r'(?<![\w`])<[0-9a-z][0-9a-z가-힣]*(?:[^a-z\s>][^>]*)?>', re.IGNORECASE)

def check_jsx_fakes():
    issues = []
    for path, _ in _iter_mdx():
        in_code = False
        in_frontmatter = False
        for ln, line in enumerate(open(path, encoding='utf-8'), 1):
            if ln == 1 and line.strip() == '---': in_frontmatter = True; continue
            if in_frontmatter:
                if line.strip() == '---': in_frontmatter = False
                continue
            if line.startswith('```'): in_code = not in_code; continue
            if in_code: continue
            # Strip inline `backtick` spans (so `<30K` inside code is ignored)
            stripped = re.sub(r'`[^`]*`', '', line)
            # Strip valid JSX components like <Card title="...">
            stripped = re.sub(r'<(?:/?[A-Z]\w*|/?[a-z]+\s+\w+=|/[A-Za-z]\w*)\s*[^>]*>', '', stripped)
            m = _JSX_FAKE_RE.search(stripped)
            if m:
                snippet = line.strip()[:80]
                issues.append(f'  {os.path.relpath(path, ROOT)}:{ln}: {snippet}')
    return issues

def check_frontmatter():
    issues = []
    fm_re = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
    for path, _ in _iter_mdx():
        content = open(path, encoding='utf-8').read()
        m = fm_re.match(content)
        if not m:
            issues.append(f'  {os.path.relpath(path, ROOT)}: no frontmatter')
            continue
        fm = m.group(1)
        if 'title:' not in fm:
            issues.append(f'  {os.path.relpath(path, ROOT)}: missing title')
        if 'description:' not in fm:
            issues.append(f'  {os.path.relpath(path, ROOT)}: missing description')
    return issues

def main():
    fail = False

    print('[1/3] Nav consistency...')
    missing, orphan = check_nav()
    if missing or orphan:
        fail = True
        if missing:
            print(f'  MISSING (in nav, no file): {missing}')
        if orphan:
            print(f'  ORPHAN (file, not in nav): {orphan}')
    else:
        print('  OK — all nav paths resolve, no orphan files')

    print('[2/3] JSX-fake patterns (e.g. <30K, <200줄)...')
    jsx = check_jsx_fakes()
    if jsx:
        fail = True
        print(f'  Found {len(jsx)} suspicious patterns (wrap with backticks):')
        for line in jsx[:20]: print(line)
        if len(jsx) > 20: print(f'  ... and {len(jsx)-20} more')
    else:
        print('  OK — no bare <NUM> or <token> in prose')

    print('[3/3] Frontmatter completeness...')
    fm = check_frontmatter()
    if fm:
        fail = True
        print(f'  Found {len(fm)} pages with incomplete frontmatter:')
        for line in fm: print(line)
    else:
        print('  OK — all pages have title + description')

    if fail:
        print('\n[FAIL] docs sanity checks did not pass.')
        sys.exit(1)
    print('\n[OK] all docs checks passed.')

if __name__ == '__main__':
    main()
