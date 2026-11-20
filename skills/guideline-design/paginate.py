"""paginate.py — 인쇄한 PDF 에 쪽번호와 러닝 헤드를 넣는다.

브라우저 인쇄는 CSS `@page` 의 머리말·꼬리말 영역을 만들어 주지 않는다. 90쪽짜리
배포본에 쪽번호가 없으면 배포본이 아니므로, 인쇄한 PDF 를 후처리해서 넣는다.

    python paginate.py 배포본.pdf --title "공공기관 ROS 2 기반 … 가이드라인"
    python paginate.py 배포본.pdf --title "…" --style bottom --skip 1

위치는 발행본 20종에서 본 두 방식을 따른다.
  top    바깥쪽 위에 `12 | 문서명` (국가 망 보안체계 계열). 펼침면 기준으로
         좌우를 번갈아 놓는다.
  bottom 아래 바깥쪽에 쪽번호만 (우주시스템·전력망 계열).

PyMuPDF 가 필요하다. 한글은 내장 `korea` 글꼴로 찍으므로 글꼴 파일이 없어도 된다.
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    import fitz
except ImportError:
    print('PyMuPDF 가 필요하다:  pip install pymupdf')
    sys.exit(2)

# Windows 콘솔 기본 인코딩(cp949)은 ｢ ｣ 같은 글자를 쓰지 못한다.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PT = 72.0 / 25.4

# 설치된 한글 글꼴을 먼저 쓴다. 내장 `korea` 글꼴은 자간이 벌어져 머리말이
# 성기게 보이므로 마지막 수단으로 둔다.
FONT_CANDIDATES = [
    r'C:\Windows\Fonts\malgun.ttf',
    r'C:\Windows\Fonts\malgunsl.ttf',
    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
]


def pick_font(path=None):
    """쓸 수 있는 한글 글꼴을 고른다. (fontname, fontfile) 를 돌려준다."""
    for f in ([path] if path else []) + FONT_CANDIDATES:
        if f and os.path.exists(f):
            return 'kr', f
    return 'korea', None


def paginate(src, dst, title, style, skip, start, margin, gray, fontpath=None,
             end=0, head=False, sparse=0):
    doc = fitz.open(src)
    fname, ffile = pick_font(fontpath)
    measure = fitz.Font(fontfile=ffile) if ffile else fitz.Font('korea')
    col = (gray, gray, gray)
    rule = (0.78, 0.82, 0.88)
    m = margin * PT
    n = 0

    last = doc.page_count - end
    for i, page in enumerate(doc):
        if i < skip or i >= last:
            continue
        num = i - skip + start
        if sparse:
            # 전면 간지와 빈 쪽에는 쪽 장식을 넣지 않는다. 번호는 그대로 센다.
            import re as _re
            if len(_re.sub(r'\s+', '', page.get_text())) < sparse:
                continue
        w, h = page.rect.width, page.rect.height
        outer_left = (num % 2 == 0)  # 짝수 쪽은 왼쪽이 바깥이다
        if ffile:
            page.insert_font(fontname=fname, fontfile=ffile)

        if style == 'top':
            size, y = 7.5, m * 0.62
            label = '%d | %s' % (num, title) if outer_left else '%s | %d' % (title, num)
        else:
            size, y = 8.5, h - m * 0.45
            label = str(num)

        tw = measure.text_length(label, fontsize=size)
        x = m if outer_left else w - m - tw
        page.insert_text((x, y), label, fontname=fname, fontsize=size, color=col)
        if head and style == 'bottom' and title:
            hy = m * 0.62
            hw = measure.text_length(title, fontsize=7.5)
            hx = m if not outer_left else w - m - hw
            page.insert_text((hx, hy), title, fontname=fname, fontsize=7.5, color=col)
            page.draw_line(fitz.Point(m, hy + 3.2), fitz.Point(w - m, hy + 3.2),
                           color=rule, width=0.5)
        if style == 'top':
            page.draw_line(fitz.Point(m, y + 3.2), fitz.Point(w - m, y + 3.2),
                           color=rule, width=0.5)
        n += 1

    doc.save(dst, deflate=True, garbage=3)
    doc.close()
    return n


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source')
    ap.add_argument('--title', default='')
    ap.add_argument('--out', default=None)
    ap.add_argument('--style', default='top', choices=('top', 'bottom'))
    ap.add_argument('--skip', type=int, default=1,
                    help='번호를 넣지 않을 앞쪽 수. 기본 1(표지).')
    ap.add_argument('--start', type=int, default=1, help='첫 번호. 기본 1.')
    ap.add_argument('--margin', type=float, default=13.0, help='가장자리 여백 mm.')
    ap.add_argument('--gray', type=float, default=0.42, help='글자 밝기 0~1.')
    ap.add_argument('--font', default=None, help='한글 글꼴 파일 경로(.ttf/.otf).')
    ap.add_argument('--end', type=int, default=0,
                    help='번호를 넣지 않을 뒤쪽 수. 판권지가 있으면 1.')
    ap.add_argument('--sparse', type=int, default=0, metavar='글자수',
                    help='글자가 이보다 적은 쪽에는 번호·머리말을 넣지 않는다. '
                         '전면 간지와 빈 쪽에 쓴다. 70 쯤이 알맞다.')
    ap.add_argument('--head', action='store_true',
                    help='아래 번호와 함께 위쪽에 문서명을 적는다.')
    a = ap.parse_args(argv)

    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    out = a.out or a.source.replace('.pdf', '') + '-쪽번호.pdf'
    if os.path.abspath(out) == os.path.abspath(a.source):
        print('원본을 덮어쓰지 않는다. --out 으로 다른 이름을 준다.')
        return 2
    n = paginate(a.source, out, a.title, a.style, a.skip, a.start, a.margin,
                 a.gray, a.font, a.end, a.head, a.sparse)
    print('%s  (%d쪽에 번호)' % (out, n))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
