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


def art_pdf(theme: str, title: str, w: float, h: float, chrome: str,
            motif: str = None) -> str:
    """아트워크만 담은 한 쪽짜리 PDF 를 만들어 경로를 돌려준다."""
    import render
    import figures
    render.load_themes()
    t = dict(render.DEFAULTS, **render.THEMES.get(theme, {}))
    svg = figures.build(dict(
        type='cover', width=w * 4, height=h * 4,
        motif=motif or t.get('motif', 'crystal'),
        quiet=t.get('quiet', 0.62), seed=title),
        figures.theme_palette_from(t))
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    svg = svg.replace('<svg ', '<svg preserveAspectRatio="none" ', 1)

    d = tempfile.mkdtemp(prefix='coverart-')
    html = os.path.join(d, 'a.html')
    io.open(html, 'w', encoding='utf-8', newline='\n').write(
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        '@page{size:%gmm %gmm;margin:0}'
        'html,body{margin:0;padding:0}'
        'svg{display:block;width:%gmm;height:%gmm}'
        '*{-webkit-print-color-adjust:exact;print-color-adjust:exact}'
        '</style></head><body>%s</body></html>' % (w, h, w, h, svg))
    out = os.path.join(d, 'a.pdf')
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-sandbox',
                    '--no-pdf-header-footer', '--print-to-pdf=%s' % out,
                    '--virtual-time-budget=6000', 'file:///' + html.replace('\\', '/')],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out if os.path.exists(out) else ''


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source', help='인쇄한 책 PDF')
    ap.add_argument('--theme', default='art')
    ap.add_argument('--title', default='가이드라인', help='무늬를 흩뜨리는 씨앗')
    ap.add_argument('--motif', default=None, help='crystal | network | wave | grid')
    ap.add_argument('--page', type=int, default=1, help='표지 쪽 번호. 기본 1')
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
    pg = doc[a.page - 1]
    r = pg.rect
    w, h = r.width * 25.4 / 72, r.height * 25.4 / 72
    ap_ = art_pdf(a.theme, a.title, w, h, chrome, a.motif)
    if not ap_:
        print('아트워크 PDF 를 만들지 못했다.')
        return 2
    art = fitz.open(ap_)
    # 글자 아래에 깐다. overlay=False 가 그 뜻이다.
    pg.show_pdf_page(r, art, 0, overlay=False)
    art.close()
    doc.save(out, deflate=True, garbage=3)
    doc.close()
    shutil.rmtree(os.path.dirname(ap_), ignore_errors=True)
    print('%s  (표지 %d쪽에 아트워크를 깔았습니다)' % (out, a.page))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
