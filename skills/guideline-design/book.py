"""book.py — 인쇄한 PDF 를 책 구성에 맞춘다.

본문이 **홀수 쪽**에서 시작해야 펼쳤을 때 오른쪽에 온다. 브라우저는
`break-before: recto` 를 무시하므로(Chrome 에서 확인) 인쇄한 뒤에 맞춘다.

    python book.py 인쇄본.pdf --out 책.pdf

앞붙이가 몇 쪽인지 알려 줍니다. 그 값을 `toc.py --skip`, `paginate.py --skip`
에 그대로 넣으면 본문 첫 쪽이 1쪽이 됩니다.

본문 시작은 장 간지의 `제1장` 줄로 찾습니다. 목차에는 `제1장 개요` 처럼 제목이
붙어 있어 `제1장` 하나만 있는 줄과 구별됩니다.
"""

from __future__ import annotations

import argparse
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


def find_body(doc, marker: str) -> int:
    """본문이 시작하는 쪽을 0부터 센 번호로 돌려준다. 못 찾으면 -1."""
    rx = re.compile(r'^%s$' % re.escape(marker))
    for i, page in enumerate(doc):
        for line in page.get_text().split('\n'):
            if rx.match(line.strip()):
                return i
    return -1


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source')
    ap.add_argument('--out', default=None)
    ap.add_argument('--marker', default='제1장',
                    help='본문 시작을 알리는 장 간지 줄. 기본 "제1장"')
    ap.add_argument('--front', type=int, default=None,
                    help='앞붙이 쪽수를 직접 지정한다. 기본은 찾아서 쓴다.')
    a = ap.parse_args(argv)

    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    out = a.out or a.source.replace('.pdf', '') + '-책.pdf'
    if os.path.abspath(out) == os.path.abspath(a.source):
        print('원본을 덮어쓰지 않는다. --out 으로 다른 이름을 준다.')
        return 2

    doc = fitz.open(a.source)
    body = a.front if a.front is not None else find_body(doc, a.marker)
    if body < 0:
        print('본문 시작을 못 찾았다. --marker 를 확인하거나 --front 로 직접 주세요.')
        return 2

    added = 0
    if (body + 1) % 2 == 0:  # 1부터 센 쪽 번호가 짝수면 빈 쪽을 끼운다
        doc.new_page(pno=body, width=doc[body].rect.width,
                     height=doc[body].rect.height)
        body += 1
        added = 1

    doc.save(out, deflate=True, garbage=3)
    n = doc.page_count
    doc.close()

    print('앞붙이 %d쪽 · 본문 시작 %d쪽(홀수) · 전체 %d쪽%s'
          % (body, body + 1, n, ' · 빈 쪽 1장 끼움' if added else ''))
    print('  다음 단계에 쓸 값:  --skip %d --start 1' % body)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
