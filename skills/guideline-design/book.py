"""book.py — 인쇄한 PDF 를 책 구성에 맞춘다.

속표지·문서 정보·목차·본문은 저마다 **홀수 쪽**에서 시작해야 펼쳤을 때 오른쪽에
온다. 앞 내용이 한 쪽을 넘치면 뒤 차례가 밀리므로 **어느 쪽이 비어야 하는지는
인쇄해 봐야 안다.** 그래서 빈 쪽을 원고에 박지 않고 여기서 끼운다.

브라우저는 `break-before: recto` 를 무시한다(Chrome 에서 확인).

    python book.py 인쇄본.pdf --out 책.pdf
    python book.py 인쇄본.pdf --out 책.pdf --marks dist/nis-구성.json

`render.py` 가 같은 폴더에 써 둔 `<테마>-구성.json` 을 자동으로 찾는다. 없으면
`--recto` 로 직접 준다.

앞붙이가 몇 쪽인지 알려 준다. 그 값을 `toc.py --skip`, `paginate.py --skip` 에
그대로 넣으면 본문 첫 쪽이 1쪽이 된다.
"""

from __future__ import annotations

import argparse
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


def squeeze(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def page_matches(page, mark: str) -> bool:
    """그 쪽이 이 표지로 시작하는가.

    제목만 있는 속표지는 쪽 전체가 제목과 같고, 그 밖에는 제목 줄이 따로 있다.

    견줄 때 **공백을 모두 지운다.** 테마에 따라 장 번호를 `제 1 장` 처럼 자간을
    벌려 조판하는데, 글자 그대로 견주면 빗나가 본문 시작을 한참 뒤에서 찾는다.
    """
    text = page.get_text()
    want = squeeze(mark).replace(' ', '')
    if squeeze(text).replace(' ', '') == want:
        return True
    return any(squeeze(line).replace(' ', '') == want
               for line in text.split(chr(10)))


def find_marks(doc, marks: list, start: int = 1) -> list:
    """표지를 차례대로 짚어 쪽 번호(0부터)를 돌려준다. 못 찾으면 None."""
    out, at = [], start
    for mk in marks:
        hit = None
        for i in range(at, doc.page_count):
            if page_matches(doc[i], mk):
                hit = i
                break
        out.append(hit)
        if hit is not None:
            at = hit + 1
    return out


def find_body(doc, mark: str, start: int = 1, head: int = 44) -> int:
    """본문이 시작하는 쪽을 찾는다. 못 찾으면 -1.

    장 간지는 장 번호가 **쪽 맨 앞**에 온다. 본문 중간의 장 참조는 글 속에
    묻히므로 앞 `head` 글자만 본다. 테마가 번호와 제목의 순서를 바꾸거나
    (`개요 제1장`) 자간을 벌려도(`제 1 장`) 그 범위 안에 들어온다.
    """
    want = squeeze(mark).replace(' ', '')
    for i in range(start, doc.page_count):
        flat = squeeze(doc[i].get_text()).replace(' ', '')
        if want in flat[:head]:
            return i
    return -1


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source')
    ap.add_argument('--out', default=None)
    ap.add_argument('--marks', default=None,
                    help='render.py 가 쓴 <테마>-구성.json. 생략하면 옆에서 찾는다.')
    ap.add_argument('--recto', action='append', default=None,
                    help='홀수 쪽에서 시작해야 하는 자리의 표지. 여러 번 줄 수 있다.')
    ap.add_argument('--body', default=None,
                    help='본문 시작 표지. 기본은 표지 목록의 마지막.')
    a = ap.parse_args(argv)

    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    out = a.out or a.source.replace('.pdf', '') + '-책.pdf'
    if os.path.abspath(out) == os.path.abspath(a.source):
        print('원본을 덮어쓰지 않는다. --out 으로 다른 이름을 준다.')
        return 2

    marks = a.recto
    if not marks:
        mp = a.marks
        if not mp:
            # 같은 폴더에서 테마 이름이 같은 구성 파일을 먼저 찾는다. 여러 테마를
            # 한 폴더에 뽑으면 구성 파일도 여럿이라 아무거나 집으면 안 된다.
            base = os.path.dirname(os.path.abspath(a.source))
            stem = os.path.basename(a.source).rsplit('.', 1)[0]
            cand = [f for f in os.listdir(base) if f.endswith('-구성.json')]
            named = [f for f in cand
                     if stem.startswith(f[:-len('-구성.json')])]
            if named:
                mp = os.path.join(base, named[0])
            elif len(cand) == 1:
                mp = os.path.join(base, cand[0])
            else:
                mp = None
                if cand:
                    print('  구성 파일이 여럿이라 고를 수 없다. --marks 로 지정하세요.')
        if mp and os.path.exists(mp):
            marks = json.load(open(mp, encoding='utf-8')).get('recto', [])
        else:
            marks = ['제1장']
            print('구성 파일이 없어 본문 시작(제1장)만 맞춘다.')

    doc = fitz.open(a.source)
    added = 0
    # 앞에서부터 하나씩 맞춘다. 빈 쪽을 끼우면 뒤가 밀리므로 그때마다 다시 찾는다.
    for n in range(len(marks)):
        found = find_marks(doc, marks[:n + 1])
        p = found[n]
        if p is None:
            print('  ! 못 찾음: %s' % marks[n])
            continue
        if (p + 1) % 2 == 0:
            doc.new_page(pno=p, width=doc[p].rect.width, height=doc[p].rect.height)
            added += 1

    body_mark = a.body or (marks[-1] if marks else '제1장')
    # 앞붙이에도 `제1장` 이라는 글자가 나온다(발간 정보의 ※ 문장). 앞 표지들을
    # 차례대로 짚은 뒤 그 다음 쪽부터 본문을 찾는다.
    lead = find_marks(doc, marks[:-1]) if len(marks) > 1 else []
    after = max([p for p in lead if p is not None], default=0) + 1
    body = find_body(doc, body_mark, after)
    if body < 0:
        body = find_body(doc, body_mark, 1)
    if body is None:
        print('본문 시작을 못 찾았다. --body 로 직접 주세요.')
        return 2

    doc.save(out, deflate=True, garbage=3)
    n = doc.page_count
    doc.close()

    print('앞붙이 %d쪽 · 본문 시작 %d쪽(%s) · 전체 %d쪽 · 빈 쪽 %d장 끼움'
          % (body, body + 1, '홀수' if (body + 1) % 2 else '짝수', n, added))
    print('  다음 단계에 쓸 값:  --skip %d --start 1' % body)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
