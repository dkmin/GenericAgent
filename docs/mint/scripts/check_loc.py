#!/usr/bin/env python3
"""
LOC 검증 스크립트 — docs/mint/concepts/architecture.mdx의 줄수 표가 실제 코드와 일치하는지 확인.

CI 또는 pre-commit hook에서 호출:
    python docs/mint/scripts/check_loc.py

mismatch가 있으면 exit 1.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ARCH_MD = os.path.join(ROOT, 'docs', 'mint', 'concepts', 'architecture.mdx')

# (claimed_loc, file_path)
CLAIMS = [
    (268, 'agentmain.py'),
    (123, 'agent_loop.py'),
    (560, 'ga.py'),
    (982, 'llmcore.py'),
    (286, 'TMWebDriver.py'),
    (870, 'simphtml.py'),
    (144, 'launch.pyw'),
]

TOLERANCE = 5  # 줄수 차이 허용폭 (사소한 변경은 통과)

def actual_loc(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None
    with open(full, encoding='utf-8', errors='ignore') as f:
        return sum(1 for _ in f)

def main():
    failed = []
    for claimed, path in CLAIMS:
        actual = actual_loc(path)
        if actual is None:
            failed.append((path, 'MISSING', claimed))
            continue
        diff = abs(actual - claimed)
        status = 'OK' if diff <= TOLERANCE else 'STALE'
        print(f'  {status:5} {path:20} claimed={claimed:4} actual={actual:4} diff={diff}')
        if status == 'STALE':
            failed.append((path, actual, claimed))

    if failed:
        print(f'\n[FAIL] {len(failed)} file(s) drifted from architecture.mdx claims (>{TOLERANCE} lines):')
        for path, actual, claimed in failed:
            print(f'  - {path}: docs say {claimed}, actual {actual}')
        print(f'\nUpdate {ARCH_MD} or the source files.')
        sys.exit(1)

    print(f'\n[OK] all {len(CLAIMS)} files within ±{TOLERANCE} lines of doc claims.')

if __name__ == '__main__':
    main()
