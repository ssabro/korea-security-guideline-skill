"""coverart.py — 인쇄한 PDF 의 표지에 아트워크를 깔아 준다.

표지 그래픽을 CSS 로 종이 끝까지 채우려 했으나 되지 않았다. `@page cover
{margin:0}` 과 `height:257mm` 를 줘도 인쇄에서 상자가 232.8mm 로 잘린다 —
쪽 조각화가 걸려 쪽 내용 영역에 맞춰진다. 아래 24mm 가 희게 남는다.

그래서 쪽번호와 같은 방식을 쓴다. **인쇄한 뒤에 입힌다.**

    python coverart.py 책.pdf --theme art --title "문서명" --out 최종.pdf

아트워크를 쪽 크기 그대로 그려 **글자 아래에** 깐다(`overlay=False`). 표지의
제목과 발행 정보는 그대로 위에 남는다.

그림은 Chrome 으로 PDF 를 만들어 옮긴다. PyMuPDF 로 SVG 를 직접 그리면
그라데이션이 검게 나오기 때문이다.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    import fitz
except ImportError:
    print('PyMuPDF 가 필요하다:  pip install pymupdf')
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CHROME = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
]


def find_chrome(path=None) -> str:
    for c in ([path] if path else []) + CHROME:
        if c and os.path.exists(c):
            return c
    return ''


MOTIFS = ('crystal', 'network', 'wave', 'grid')


def art_pdf(theme: str, seeds: list, w: float, h: float, chrome: str,
            motif: str = None, quiet: float = None, motifs: list = None) -> str:
    """아트워크를 담은 PDF 를 만들어 경로를 돌려준다.

    `seeds` 하나마다 한 쪽이다. 한 번의 인쇄로 여러 쪽을 만들어, 표지와 장
    간지를 각각 따로 인쇄하지 않는다.
    """
    import render
    import figures
    render.load_themes()
    t = dict(render.DEFAULTS, **render.THEMES.get(theme, {}))
    pal = figures.theme_palette_from(t)
    # 간지 그러데이션에 쓸 보조색을 테마가 따로 고를 수 있다. 점색(호박색
    # 따위)을 주조색과 섞으면 간지가 요란해진다.
    if t.get('art_accent2'):
        pal = dict(pal, accent2=t['art_accent2'])
    pages = []
    for i, sd in enumerate(seeds):
        # `motifs` 가 있으면 그 쪽의 무늬를 그대로 쓴다. 표지·간지·뒤표지가
        # 한 번의 인쇄 안에서 저마다 다른 무늬를 쓸 수 있어야 한다.
        mo = (motifs[i] if motifs and i < len(motifs) and motifs[i] else None)
        mo = mo or motif or (t.get('motif', 'crystal') if i == 0
                             else MOTIFS[i % len(MOTIFS)])
        back = mo == 'pill'
        svg = figures.build(dict(
            type='cover', width=w * 4, height=h * 4, motif=mo,
            quiet=0.0 if back else
                 (t.get('quiet', 0.62) if quiet is None else quiet),
            # 표지만 테마가 고른 바탕을 쓴다. 장 간지는 흰 글자를 올리므로
            # 늘 색 바탕이어야 한다.
            bg=t.get('cover_bg', '') if (i == 0 or back) else '',
            # 주제 그림은 **표지에만** 둔다. 간지마다 같은 그림이 되풀이되면
            # 장을 구분해 주지 못하고, 제목이 없는 간지에서는 주제를 고를
            # 근거도 없어 방패만 찍힌다.
            subject='' if (i == 0 or back) else 'none',
            seed=sd), pal)
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = svg.replace('<svg ', '<svg preserveAspectRatio="none" ', 1)
        pages.append('<div class="pg">%s</div>' % svg)

    d = tempfile.mkdtemp(prefix='coverart-')
    html = os.path.join(d, 'a.html')
    io.open(html, 'w', encoding='utf-8', newline='\n').write(
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        '@page{size:%gmm %gmm;margin:0}'
        'html,body{margin:0;padding:0}'
        '.pg{break-after:page}'
        'svg{display:block;width:%gmm;height:%gmm}'
        '*{-webkit-print-color-adjust:exact;print-color-adjust:exact}'
        '</style></head><body>%s</body></html>'
        % (w, h, w, h, ''.join(pages)))
    out = os.path.join(d, 'a.pdf')
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-sandbox',
                    '--no-pdf-header-footer', '--print-to-pdf=%s' % out,
                    '--virtual-time-budget=6000', 'file:///' + html.replace('\\', '/')],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out if os.path.exists(out) else ''


def find_chapters(doc, skip: int, maxchars: int = 420) -> list:
    """전면 장 간지 쪽을 찾는다. (쪽 번호, 씨앗) 목록.

    장 번호가 쪽 맨 앞에 오고 **그 쪽의 글자가 적은** 쪽만 고른다.
    목차 쪽도 "제1장 개요 1 제1절 …" 으로 시작하므로 `목차`·`CONTENTS` 가
    들어간 쪽은 뺀다.

    간지가 그 장의 절 목록을 함께 실으면서 글자 수가 70 자를 넘게 되었다.
    발행본을 따라 절 목록을 넣은 뒤로 70 자 기준이 간지를 하나도 찾지
    못했다. 재어 보니 절 목록을 단 간지는 150~300 자이고 목차 쪽은 1,000
    자가 넘는다. 그 사이인 420 자를 기준으로 둔다.

    전면 간지를 쓰지 않는 테마에서는 아무것도 찾지 못한다. 그때는 간지에
    그림을 깔 자리가 없다는 뜻이므로 그대로 두면 된다.
    """
    out = []
    for i in range(skip, doc.page_count):
        flat = re.sub(r'\s+', '', doc[i].get_text())
        if not flat or len(flat) > maxchars:
            continue
        if '목차' in flat or 'CONTENTS' in flat.upper():
            continue
        # 목차는 이어지는 쪽에 `목차` 라는 말이 없다. 대신 **항목마다 끝에
        # 쪽번호**가 붙는다. 간지의 절 목록에는 쪽번호가 없다.
        #   목차   …목적 2 제2절 적용 범위 2 제3절…
        #   간지   …목적 제2절 적용 범위 제3절…
        # 다음 항목 바로 앞에 숫자가 있으면 목차다.
        if len(re.findall(r'\d(?=제\d+절|부록\s*\d)', flat)) >= 2:
            continue
        # 간지는 제목만 담겨 온점이 없다. 마침표가 있으면 문장이 있다는
        # 뜻이므로 본문이다. `부록 3 보안등급 판정 워크시트` 처럼 장이나
        # 부록으로 **시작하는 본문 쪽**이 여기서 걸러진다.
        if '.' in flat:
            continue
        # 장 번호가 쪽 맨 앞에 오면 의심할 것이 없다.
        m = re.match(r'^(?:제(\d+)장|(부록))', flat)
        if m:
            out.append((i, '제%s장' % m.group(1) if m.group(1) else '부록'))
            continue
        # 테마에 따라 글자가 `개요 제1절 … 제1장` 순으로 추출되어 장 번호가
        # 맨 뒤로 밀릴 수 있다. 그때는 **절 목록을 가진 짧은 쪽**만 받는다.
        # 장을 가리키는 본문도 짧을 수 있지만 그쪽에는 문장이 있고,
        # 간지는 제목만 담겨 온점이 없다.
        if len(re.findall(r'제\d+절|부록\s*\d+', flat)) < 2:
            continue
        m = re.search(r'제(\d+)장', flat)
        if m:
            out.append((i, '제%s장' % m.group(1)))
        elif '부록' in flat:
            out.append((i, '부록'))
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source', help='인쇄한 책 PDF')
    ap.add_argument('--theme', default='art')
    ap.add_argument('--title', default='가이드라인', help='무늬를 흩뜨리는 씨앗')
    ap.add_argument('--motif', default=None, help='crystal | network | wave | grid')
    ap.add_argument('--page', type=int, default=1, help='표지 쪽 번호. 기본 1')
    ap.add_argument('--chapters', action='store_true',
                    help='장 간지에도 깐다. 장마다 다른 무늬를 쓴다.')
    ap.add_argument('--chapter-quiet', type=float, default=0.30,
                    help='장 간지에서 무늬를 비울 위쪽 비율. 기본 0.30')
    ap.add_argument('--out', default=None)
    ap.add_argument('--chrome', default=None)
    a = ap.parse_args(argv)

    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    chrome = find_chrome(a.chrome)
    if not chrome:
        print('Chrome 을 찾지 못했다. --chrome 으로 경로를 주세요.')
        return 2
    out = a.out or a.source.replace('.pdf', '') + '-표지.pdf'
    if os.path.abspath(out) == os.path.abspath(a.source):
        print('원본을 덮어쓰지 않는다. --out 으로 다른 이름을 준다.')
        return 2

    doc = fitz.open(a.source)
    r = doc[a.page - 1].rect
    w, h = r.width * 25.4 / 72, r.height * 25.4 / 72

    targets = [(a.page - 1, a.title)]
    if a.chapters:
        targets += find_chapters(doc, a.page)
    ap_ = art_pdf(a.theme, [s for _, s in targets], w, h, chrome, a.motif)
    if not ap_:
        print('아트워크 PDF 를 만들지 못했다.')
        return 2
    art = fitz.open(ap_)
    # 글자 아래에 깐다. overlay=False 가 그 뜻이다.
    for i, (pno, _) in enumerate(targets):
        if i < art.page_count:
            doc[pno].show_pdf_page(doc[pno].rect, art, i, overlay=False)
    art.close()
    doc.save(out, deflate=True, garbage=3)
    doc.close()
    shutil.rmtree(os.path.dirname(ap_), ignore_errors=True)
    print('%s  (%d곳에 아트워크를 깔았습니다 — 표지와 간지 %d쪽)'
          % (out, len(targets), len(targets) - 1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
