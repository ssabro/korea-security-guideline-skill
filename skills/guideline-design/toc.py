"""toc.py — 인쇄한 PDF 에서 장·절이 시작하는 쪽을 찾아 목차 쪽번호를 만든다.

조판하기 전에는 쪽을 알 수 없으므로 두 번 인쇄합니다.

    1) render.py 원고.md                       쪽번호 없는 목차
    2) 인쇄 → 1차.pdf
    3) toc.py 1차.pdf --source 원고.md --out toc.json
    4) render.py 원고.md --toc toc.json        목차에 쪽번호가 들어간다
    5) 인쇄 → 2차.pdf  ·  paginate.py 로 쪽번호

쪽번호를 **원고에 쓰지 않습니다.** 원고가 바뀌면 곧바로 틀린 값이 되기 때문입니다.
`toc.json` 은 그 인쇄본에서만 맞는 파생물이므로 원고와 함께 두지 말고 버리세요.

목차 항목은 원고의 `## 목차` 목록에서 가져오고, PDF 에서는 **차례대로** 찾습니다.
`제1절` 처럼 장마다 되풀이되는 이름이 있어 순서를 지켜야 맞게 짚습니다.
"""

from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    import fitz
except ImportError:
    print('PyMuPDF 가 필요하다:  pip install pymupdf')
    sys.exit(2)

RX_MARK = re.compile(r'^(제\s?\d+\s?[장절]|부록\s*\d*)')


def toc_entries(md_path: str) -> list:
    """원고의 `## 목차` 목록을 (표시줄, 표지) 짝으로 읽는다."""
    text = io.open(md_path, encoding='utf-8').read()
    lines = text.split('\n')
    try:
        s = next(i for i, l in enumerate(lines) if re.match(r'^#+\s*목차\s*$', l))
    except StopIteration:
        print('원고에 `## 목차` 가 없다.')
        return []
    out = []
    for l in lines[s + 1:]:
        if l.startswith('#'):
            break
        m = re.match(r'^\s*-\s+(.+?)\s*$', l)
        if not m:
            continue
        txt = m.group(1).strip()
        mk = RX_MARK.match(txt)
        mark = mk.group(1).strip() if mk else ''
        head = txt[len(mk.group(1)):].strip() if mk else txt
        out.append(dict(text=txt, mark=mark, head=head or mark or txt))
    return out


def headings(doc, lead: float) -> list:
    """쪽마다 제목으로 볼 만한 줄을 추린다. (쪽, 줄) 목록.

    제목 한 줄이 여러 글자 조각으로 쪼개져 있으므로 줄 단위로 이어 붙인다.
    번호 배지는 본문보다 작게 조판되므로 줄에서 **가장 큰** 조각을 기준으로 본다.
    """
    out = []
    for i, page in enumerate(doc):
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0:
                continue
            for l in b['lines']:
                txt = ''.join(sp['text'] for sp in l['spans']).strip()
                if not txt:
                    continue
                big = max(sp['size'] for sp in l['spans'])
                if big >= lead:
                    out.append((i, txt))
    return out


def body_size(doc, sample: int = 40) -> float:
    """본문 글자 크기를 가늠한다.

    통제항목 ID 처럼 짧은 글자가 수천 개 들어간 문서에서는 단순히 가장 흔한
    크기를 고르면 본문이 아니라 ID 크기가 잡힌다. 글자 수가 긴 줄만 세고,
    문서 전체에 고루 퍼진 쪽을 본다.
    """
    c = collections.Counter()
    step = max(1, doc.page_count // sample)
    for i in range(0, doc.page_count, step):
        for b in doc[i].get_text('dict')['blocks']:
            if b['type'] != 0:
                continue
            for l in b['lines']:
                txt = ''.join(sp['text'] for sp in l['spans']).strip()
                if len(txt) < 25:
                    continue
                for sp in l['spans']:
                    if sp['text'].strip():
                        c[round(sp['size'], 1)] += len(sp['text'])
    return c.most_common(1)[0][0] if c else 10.0


def locate(doc, entries: list, skip: int, start: int, lead_ratio: float) -> dict:
    """항목을 차례대로 짚어 시작 쪽을 찾는다.

    목차 쪽은 항목을 한꺼번에 담고 있어 그대로 두면 거기서 다 맞아 버린다. 목차
    줄은 본문과 같은 크기로 조판되므로 보통은 제목 걸러내기에서 빠지지만, 그래도
    목차 제목이 있는 쪽과 한 쪽에서 여덟 항목 넘게 맞는 쪽은 건너뛴다. 본문에도
    제목 서넛이 한 쪽에 오는 일이 흔하므로 문턱을 낮게 두면 안 된다.
    """
    lead = body_size(doc) * lead_ratio
    per_page = collections.defaultdict(list)
    for page, txt in headings(doc, lead):
        per_page[page].append(txt)

    def hit(entry, txt):
        want = entry['head'].replace(' ', '')
        got = txt.replace(' ', '')
        return bool(want) and (got.startswith(want) or want in got)

    found, idx = {}, 0
    for page in range(doc.page_count):
        lines = per_page.get(page, [])
        if idx >= len(entries):
            break
        if any(x.strip() in ('목차', 'CONTENTS', 'Contents') for x in lines):
            continue  # 목차 쪽
        ahead = entries[idx:idx + 20]
        if sum(1 for e in ahead if any(hit(e, x) for x in lines)) >= 8:
            continue  # 목차 쪽
        for txt in lines:
            if idx < len(entries) and hit(entries[idx], txt):
                found[entries[idx]['text']] = max(1, page - skip + start)
                idx += 1
    return found


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('pdf', help='1차 인쇄본')
    ap.add_argument('--source', required=True, help='원고 .md')
    ap.add_argument('--out', default=None, help='쓸 json. 기본 toc.json')
    ap.add_argument('--skip', type=int, default=1, help='쪽번호를 매기지 않는 앞쪽 수')
    ap.add_argument('--start', type=int, default=1, help='첫 쪽번호')
    ap.add_argument('--lead', type=float, default=1.05,
                    help='제목으로 볼 글자 크기 배수. 기본 1.05')
    ap.add_argument('--verify', default=None,
                    help='2차 인쇄본. 쪽이 밀렸는지 확인만 한다')
    a = ap.parse_args(argv)

    for p in (a.pdf, a.source):
        if not os.path.exists(p):
            print('없는 파일: %s' % p)
            return 2

    entries = toc_entries(a.source)
    if not entries:
        return 2
    doc = fitz.open(a.pdf)
    found = locate(doc, entries, a.skip, a.start, a.lead)
    miss = [e['text'] for e in entries if e['text'] not in found]

    print('목차 %d항목 · 찾음 %d · 못 찾음 %d' % (len(entries), len(found), len(miss)))
    for m in miss[:10]:
        print('  못 찾음: %s' % m)
    if miss:
        print('  → --lead 를 낮추거나(제목 글자가 작을 때) 원고 목차와 본문 제목이'
              ' 같은지 보세요.')

    if a.verify:
        doc2 = fitz.open(a.verify)
        again = locate(doc2, entries, a.skip, a.start, a.lead)
        moved = [(k, found[k], again[k]) for k in found if k in again and found[k] != again[k]]
        if moved:
            print('\n쪽이 밀린 항목 %d개 — 목차 쪽번호가 틀립니다.' % len(moved))
            for k, b, c in moved[:10]:
                print('  %s  %d → %d' % (k, b, c))
            print('  → toc.json 을 2차 인쇄본으로 다시 만들고 한 번 더 인쇄하세요.')
            return 1
        print('\n쪽이 밀린 항목 없음. 목차 쪽번호가 맞습니다.')
        return 0

    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.source)), 'toc.json')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(found, ensure_ascii=False, indent=1) + '\n')
    print('%s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
