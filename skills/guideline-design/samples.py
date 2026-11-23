# -*- coding: utf-8 -*-
"""테마별 배포판 샘플을 **작업 디렉터리에** 만든다.

디자인을 고르려면 눈으로 봐야 한다. 그런데 PDF 를 여러 개 열어 같은 쪽을
찾아 비교하는 일은 번거롭다. 이 도구는 테마마다 배포판을 뽑고, 쪽 종류별
(표지 · 목차 · 장 간지 · 본문 · 판권지) 그림을 떠서 한 자리에 모은다.

    python samples.py 원고.md
    python samples.py 원고.md --out 샘플 --themes art,kisa

산출물은 `--out` 이 가리키는 **작업 디렉터리 안의 폴더**다. 임시 폴더에
두지 않는다. 사용자가 탐색기에서 열어 볼 수 있어야 한다.

    샘플/index.html        테마별 그림을 한 쪽에 늘어놓은 비교표
    샘플/<테마>.pdf        그 테마로 뽑은 배포판 전체
    샘플/<테마>-<쪽>.png   쪽 종류별 그림
"""
import argparse
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ['표지', '발간정보', '목차', '장간지', '본문', '판권지']


def themes_available():
    out = []
    for f in sorted(os.listdir(os.path.join(HERE, 'themes'))):
        if f.endswith('.py') and not f.startswith('_'):
            out.append(f[:-3])
    return out


def pick_pages(doc):
    """쪽 종류별로 대표 쪽 번호를 고른다. 없으면 건너뛴다."""
    import fitz  # noqa: F401  (호출자가 이미 들여왔다)
    pick = {'표지': 0, '판권지': doc.page_count - 1}
    for i in range(doc.page_count):
        sq = ''.join(doc[i].get_text().split())
        if not sq:
            continue
        # 목차 — 테마에 따라 `목차` 를 숨기고 바로 항목부터 내기도 한다.
        if '목차' not in pick:
            if (sq.startswith('목차') or 'CONTENTS' in sq[:40].upper()
                    or (re.match(r'^제1장', sq)
                        and len(re.findall(r'제\d+절', sq)) >= 5
                        and '.' not in sq[:120])):
                pick['목차'] = i
        # 발간정보 — 문서 종류·발행기관을 담은 표가 있는 쪽
        if '발간정보' not in pick and '발행기관' in sq and '문서종류' in sq:
            pick['발간정보'] = i
        # 장간지 — 간지가 그 장의 절 목록을 함께 실으므로 글자가 수백 자다.
        # 문장이 있으면 본문이니 마침표로 가른다(coverart.find_chapters 와 같은 셈).
        # 목차는 항목 끝마다 쪽번호가 붙고 간지의 절 목록에는 없다.
        toc_like = len(re.findall(r'\d(?=제\d+절|부록\s*\d)', sq)) >= 2
        if ('장간지' not in pick and len(sq) < 620 and '.' not in sq
                and '목차' not in sq and not toc_like
                and (re.search(r'제\d+장', sq) or sq.startswith('부록'))
                and len(re.findall(r'제\d+절|부록\s*\d+', sq)) >= 2):
            pick['장간지'] = i
        if '본문' not in pick and i > 12 and doc[i].get_text().count('PRS-') >= 6:
            pick['본문'] = i
    return pick


def shoot(doc, pno, path, width=900):
    import fitz
    p = doc[pno]
    z = width / p.rect.width
    pix = p.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
    pix.save(path)


def main():
    ap = argparse.ArgumentParser(description='테마별 배포판 샘플을 만든다')
    ap.add_argument('source', help='원고 .md')
    ap.add_argument('--out', default='샘플', help='산출 폴더 (기본: 샘플)')
    ap.add_argument('--themes', default='', help='쉼표로 나눈 테마 이름 (기본: 전부)')
    ap.add_argument('--keep-pdf', action='store_true', help='PDF 도 남긴다 (기본: 남김)')
    a = ap.parse_args()

    try:
        import fitz
    except ImportError:
        raise SystemExit('PyMuPDF 가 필요합니다:  pip install pymupdf')

    names = [x.strip() for x in a.themes.split(',') if x.strip()] or themes_available()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    made = []
    for th in names:
        pdf = os.path.join(out, th + '.pdf')
        print('%-9s 뽑는 중...' % th, end='', flush=True)
        r = subprocess.run(
            [sys.executable, '-I', os.path.join(HERE, 'publish.py'),
             a.source, '--theme', th, '--out', pdf],
            capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode or not os.path.exists(pdf):
            tail = (r.stdout or '') + (r.stderr or '')
            print('  실패 — %s' % tail.strip().split('\n')[-1][:70])
            continue
        d = fitz.open(pdf)
        pick = pick_pages(d)
        shots = []
        for k in KINDS:
            if k not in pick:
                continue
            png = '%s-%s.png' % (th, k)
            shoot(d, pick[k], os.path.join(out, png))
            shots.append((k, png, pick[k] + 1))
        made.append((th, d.page_count, shots))
        d.close()
        print('  %d쪽 · 그림 %d장' % (made[-1][1], len(shots)))

    # 이번에 뽑지 않은 테마라도 폴더에 남아 있으면 비교표에 함께 올린다.
    # `--themes` 로 하나만 다시 뽑았다고 나머지가 사라지면 비교를 못 한다.
    seen = {th for th, _, _ in made}
    for f in sorted(os.listdir(out)):
        if not f.endswith('.pdf'):
            continue
        th = f[:-4]
        if th in seen:
            continue
        shots = []
        for k in KINDS:
            png = '%s-%s.png' % (th, k)
            if os.path.exists(os.path.join(out, png)):
                shots.append((k, png, 0))
        if not shots:
            continue
        try:
            d = fitz.open(os.path.join(out, f))
            n = d.page_count
            d.close()
        except Exception:
            n = 0
        made.append((th, n, shots))
    made.sort(key=lambda x: x[0])

    if not made:
        raise SystemExit('만들어진 샘플이 없습니다.')

    rows = []
    for th, pages, shots in made:
        cells = ''.join(
            '<figure><img src="%s" alt="%s %s"><figcaption>%s%s</figcaption>'
            '</figure>' % (png, th, k, k, ' · %d쪽' % pno if pno else '')
            for k, png, pno in shots)
        rows.append('<section><h2>%s <small>%d쪽</small> '
                    '<a href="%s.pdf">PDF 열기</a></h2><div class="r">%s</div>'
                    '</section>' % (th, pages, th, cells))

    html = '''<!doctype html><html lang="ko"><meta charset="utf-8">
<title>배포판 디자인 샘플</title>
<style>
:root{color-scheme:light dark;--bg:#f6f6f8;--fg:#1a1a1f;--card:#fff;--line:#d8d8de}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
 --bg:#17171b;--fg:#e8e8ee;--card:#202026;--line:#34343c}}
*{box-sizing:border-box}
body{margin:0;padding:24px 16px 48px;background:var(--bg);color:var(--fg);
 font:15px/1.6 "Malgun Gothic","맑은 고딕",system-ui,sans-serif}
h1{margin:0 0 6px;font-size:20px}
p.lead{margin:0 0 26px;color:#7a7a86}
section{margin:0 0 30px}
h2{margin:0 0 10px;font-size:16px;display:flex;align-items:baseline;gap:10px}
h2 small{font-weight:400;color:#8a8a96}
h2 a{margin-left:auto;font-size:13px}
.r{display:flex;gap:14px;overflow-x:auto;padding-bottom:6px}
figure{margin:0;flex:0 0 auto}
img{display:block;width:230px;border:1px solid var(--line);background:var(--card)}
figcaption{margin-top:5px;font-size:12px;color:#8a8a96;text-align:center}
@media (max-width:640px){img{width:160px}}
</style>
<h1>배포판 디자인 샘플</h1>
<p class="lead">테마 %d종 · 원고 %s · 쪽 그림을 눌러 키우거나 PDF 를 열어
전체를 보세요.</p>
%s
</html>''' % (len(made), os.path.basename(a.source), '\n'.join(rows))

    idx = os.path.join(out, 'index.html')
    io.open(idx, 'w', encoding='utf-8', newline='\n').write(html)
    print()
    print(idx)
    print('테마 %d종 · 그림 %d장. 이 파일을 브라우저로 열어 고르세요.'
          % (len(made), sum(len(s) for _, _, s in made)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main()
