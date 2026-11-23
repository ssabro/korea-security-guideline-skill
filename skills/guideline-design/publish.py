"""publish.py — 원고 하나에서 배포본 PDF 까지 한 번에 간다.

조판·인쇄·책 구성·목차 쪽번호·쪽번호·표지 아트워크를 차례로 돌립니다. 손으로
하면 명령이 열둘이고 `--skip` 값을 옮겨 적어야 하는데, 그 값을 도구끼리 주고
받습니다.

    python publish.py 원고.md
    python publish.py 원고.md --theme art --cover-art
    python publish.py 원고.md --theme nis --out 배포본.pdf

## 하는 일

    1 조판        원고 → HTML
    2 인쇄        HTML → PDF            (브라우저)
    3 책 구성     빈 쪽을 끼워 본문을 홀수 쪽에서 시작시킨다
    4 목차 쪽번호 인쇄본에서 장·절이 시작하는 쪽을 읽는다
    5 재조판·재인쇄·재구성
    6 검증        쪽이 밀리지 않았는지 대조한다
    7 쪽번호      본문 첫 쪽이 1
    8 표지 아트워크 (--cover-art)

목차 쪽번호 때문에 **두 번 인쇄합니다.** 조판하기 전에는 쪽을 알 수 없습니다.

## 필요한 것

Chrome 이나 Edge, 그리고 PyMuPDF. 브라우저를 못 찾으면 `--chrome` 으로
경로를 주세요.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    import fitz
except ImportError:
    print('PyMuPDF 가 필요합니다:  pip install pymupdf')
    sys.exit(2)

import book
import coverart
import paginate as pg
import render
import toc as toclib


def step(n: int, total: int, msg: str):
    print('[%d/%d] %s' % (n, total, msg))


def print_pdf(chrome: str, html: str, pdf: str, budget: int = 25000) -> bool:
    url = 'file:///' + os.path.abspath(html).replace('\\', '/')
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-sandbox',
                    '--no-pdf-header-footer', '--print-to-pdf=%s' % pdf,
                    '--virtual-time-budget=%d' % budget, url],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(pdf)


# 발행본 24종의 앞붙이(표지·발간 정보·목차)는 최대 여덟 쪽이었다.
FRONT_MAX = 8


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source', help='원고 .md')
    ap.add_argument('--theme', default='nis')
    ap.add_argument('--out', default=None, help='배포본 PDF 경로')
    ap.add_argument('--work', default=None, help='중간 산출물 폴더. 기본 <원고폴더>/dist')
    ap.add_argument('--title', default=None, help='머리말에 쓸 문서명. 기본 원고 제목')
    ap.add_argument('--style', default='bottom', choices=('top', 'bottom'),
                    help='쪽번호 자리. 기본 아래 바깥쪽')
    ap.add_argument('--cover-art', action='store_true',
                    help='표지와 장 간지에 아트워크를 깐다(art 테마에서 기본값)')
    ap.add_argument('--no-cover-art', action='store_true')
    ap.add_argument('--keep', action='store_true', help='중간 산출물을 지우지 않는다')
    ap.add_argument('--theme-set', dest='sets', action='append', default=None,
                    metavar='이름=값',
                    help='테마 값을 덮어쓴다. 예: --theme-set accent=#1b3a6b')
    ap.add_argument('--chrome', default=None)
    a = ap.parse_args(argv)

    t0 = time.time()
    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    chrome = coverart.find_chrome(a.chrome)
    if not chrome:
        print('Chrome 이나 Edge 를 찾지 못했습니다. --chrome 으로 경로를 주세요.')
        return 2

    render.load_themes()
    if a.theme not in render.THEMES:
        print('없는 테마: %s   (python render.py --themes 로 목록을 봅니다)' % a.theme)
        return 2
    th = dict(render.DEFAULTS, **render.THEMES[a.theme])
    if a.sets:
        th = render.apply_sets(th, a.sets)
        render.THEMES[a.theme] = th
    # `cover` 는 표지 **짜임**의 이름이고 CSS 선택자(`cv-side` 등)와 묶여
    # 있다. 아트워크를 쓸지는 `cover_art` 로 따로 정한다 — 둘을 한 열쇠로
    # 묶으면 아트워크를 켜는 순간 그 테마의 표지 CSS 가 통째로 꺼진다.
    # `cover` 는 표지 **짜임**의 이름이고 CSS 선택자(`cv-side` 등)와 묶여
    # 있다. 아트워크를 쓸지는 `cover_art` 로 따로 정한다 — 둘을 한 열쇠로
    # 묶으면 아트워크를 켜는 순간 그 테마의 표지 CSS 가 통째로 꺼진다.
    want_art = (a.cover_art or th.get('cover') == 'art'
                or th.get('cover_art'))
    art = want_art and not a.no_cover_art

    base = os.path.dirname(os.path.abspath(a.source))
    md = io.open(a.source, encoding='utf-8').read()
    title = a.title or next(
        (l[2:].strip() for l in md.split('\n') if l.startswith('# ')), '가이드라인')
    work = a.work or os.path.join(base, 'dist')
    os.makedirs(work, exist_ok=True)
    out = a.out or os.path.join(base, '%s.pdf' % title)
    total = 8 if art else 7

    marks = render.recto_marks(md, title)
    html = os.path.join(work, '%s.html' % a.theme)
    p1 = os.path.join(work, '_1.pdf')
    p2 = os.path.join(work, '_2.pdf')
    b1 = os.path.join(work, '_b1.pdf')
    b2 = os.path.join(work, '_b2.pdf')
    tj = os.path.join(work, 'toc.json')

    step(1, total, '조판 — %s' % th.get('label', a.theme))
    extra = []
    for s in (a.sets or []):
        extra += ['--set', s]
    if render.main([a.source, '--theme', a.theme, '--out', work] + extra) != 0:
        return 2

    step(2, total, '인쇄 (1차)')
    if not print_pdf(chrome, html, p1):
        print('  인쇄에 실패했습니다.')
        return 2

    step(3, total, '책 구성')
    front, added, pages = book.apply(p1, b1, marks)
    print('  앞붙이 %d쪽 · 본문 %d쪽부터 · 빈 쪽 %d장' % (front, front + 1, added))

    # 앞붙이가 터무니없으면 멈춘다. 발행본 24종의 앞붙이는 표지·발간 정보·
    # 목차를 합쳐 **여덟 쪽을 넘지 않는다.** 그보다 크면 본문 시작을 잘못
    # 짚은 것이고, 그대로 두면 쪽번호와 목차 쪽번호가 전부 밀린다.
    #
    # 실제로 장 간지에 절 목록을 싣자 간지의 글자 수가 70자에서 300자로
    # 늘어 book.py 가 장 번호를 놓쳤고, 앞붙이가 8쪽에서 24쪽·92쪽이
    # 되었다. 출력 한 줄을 눈으로 보고서야 알았다. 사람이 보지 않아도
    # 걸리게 한다.
    if not 1 <= front <= FRONT_MAX:
        print('  ! 앞붙이가 %d쪽입니다. 발행본은 여덟 쪽을 넘지 않습니다.'
              % front)
        print('    본문 시작을 잘못 짚었습니다 — 장 간지에서 장 번호를 찾지')
        print('    못한 것입니다. --keep 으로 중간 산출물을 남겨 1차 인쇄본을')
        print('    확인하고, 간지의 글자가 다르면 book.py 의 --marks 로')
        print('    지정하세요.')
        return 2

    step(4, total, '목차 쪽번호')
    doc = fitz.open(b1)
    entries = toclib.toc_entries(a.source)
    found = toclib.locate(doc, entries, front, 1, 1.05)
    doc.close()
    print('  %d항목 중 %d개를 찾았습니다' % (len(entries), len(found)))
    if len(found) < len(entries):
        for e in entries:
            if e['text'] not in found:
                print('    못 찾음: %s' % e['text'])
    io.open(tj, 'w', encoding='utf-8', newline='\n').write(
        __import__('json').dumps(found, ensure_ascii=False, indent=1))

    step(5, total, '재조판·재인쇄')
    if render.main([a.source, '--theme', a.theme, '--out', work,
                    '--toc', tj] + extra) != 0:
        return 2
    if not print_pdf(chrome, html, p2):
        print('  인쇄에 실패했습니다.')
        return 2
    front2, _, pages2 = book.apply(p2, b2, marks)

    step(6, total, '검증')
    if front2 != front:
        print('  ! 앞붙이 쪽수가 %d → %d 로 바뀌었습니다. 다시 돌리세요.' % (front, front2))
        return 1
    doc = fitz.open(b2)
    again = toclib.locate(doc, entries, front2, 1, 1.05)
    doc.close()
    moved = [k for k in found if k in again and found[k] != again[k]]
    if moved:
        print('  ! 쪽이 밀린 항목 %d개 — 목차 쪽번호가 틀립니다.' % len(moved))
        return 1
    print('  쪽이 밀린 항목 없음')

    step(7, total, '쪽번호')
    stamped = pg.paginate(b2, out, title, a.style, front2, 1, 13.0, 0.42,
                          None, 1, True, 70)
    print('  %d쪽에 번호' % stamped)

    if art:
        step(8, total, '표지 아트워크')
        doc = fitz.open(out)
        r = doc[0].rect
        w, h = r.width * 25.4 / 72, r.height * 25.4 / 72
        # 간지 아트워크는 테마가 끌 수 있다. 간지를 희게 두거나 전면
        # 쪽으로 쓰지 않는 테마에서는 그림이 글자를 덮기만 한다.
        targets = [(0, title)]
        if th.get('chapter_art', True):
            targets += coverart.find_chapters(doc, 1)
        # 뒤표지 — 발행본은 마지막 쪽을 조용히 둔다. 테마가 원하면 둥근
        # 기둥에 보안 아이콘을 쌓은 무늬를 깐다.
        motifs = [None] * len(targets)
        if th.get('back_art'):
            targets.append((doc.page_count - 1, title))
            motifs.append('pill')
        ap_ = coverart.art_pdf(a.theme, [s for _, s in targets], w, h, chrome,
                               motifs=motifs)
        if ap_:
            src = fitz.open(ap_)
            for i, (pno, _) in enumerate(targets):
                if i < src.page_count:
                    doc[pno].show_pdf_page(doc[pno].rect, src, i, overlay=False)
            src.close()
            tmp = out + '.tmp'
            doc.save(tmp, deflate=True, garbage=3)
            doc.close()
            shutil.move(tmp, out)
            shutil.rmtree(os.path.dirname(ap_), ignore_errors=True)
            print('  그림 %d쪽 (표지·간지%s)'
                  % (len(targets), '·뒤표지' if th.get('back_art') else ''))
        else:
            doc.close()
            print('  ! 아트워크를 만들지 못했습니다. 그림 없이 두었습니다.')

    if not a.keep:
        for f in (p1, p2, b1, b2):
            if os.path.exists(f):
                os.remove(f)

    d = fitz.open(out)
    print('\n%s' % out)
    print('%d쪽 · %.0fx%.0fmm · %.1fMB · %.0f초'
          % (d.page_count, d[0].rect.width * 25.4 / 72, d[0].rect.height * 25.4 / 72,
             os.path.getsize(out) / 1048576, time.time() - t0))
    ids = set(re.findall(r'[A-Z][A-Z0-9]{1,7}-[A-Z]{2}-M?\d{1,3}(?:\(\d{1,2}\))?',
                         ''.join(p.get_text() for p in d)))
    mdids = set(re.findall(r'[A-Z][A-Z0-9]{1,7}-[A-Z]{2}-M?\d{1,3}(?:\(\d{1,2}\))?', md))
    d.close()
    if mdids:
        print('통제항목 %d / %d%s' % (len(ids), len(mdids),
                                   '' if ids >= mdids else '   ← 빠진 항목이 있습니다'))
    if not a.keep:
        print('중간 산출물은 지웠습니다. 남기려면 --keep 을 주세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
