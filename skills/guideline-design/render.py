"""render.py — 가이드라인 원고(Markdown)를 배포용 HTML 로 바꾼다.

판면·여백·글자 크기·색은 국내 발행본 20종을 측정해 정한 값이다
(`references/publication-design.md`). 테마만 바꿔 같은 원고를 여러 판면으로
뽑을 수 있다.

    python render.py 원고.md                      # 기본 테마(nis)
    python render.py 원고.md --theme field        # 테마 지정
    python render.py 원고.md --all                # 모든 테마 + 비교용 index.html
    python render.py --themes                     # 테마 목록

표준 라이브러리만 쓴다. 외부 글꼴·스크립트를 받아오지 않는다. 삽도 SVG 는
파일 안에 넣어 HTML 하나로 열린다. 브라우저에서 인쇄하면 측정한 판면으로
PDF 가 나온다.
"""

from __future__ import annotations

import argparse
import html
import json
import io
import os
import re
import sys

# ── 테마 — 수치는 모두 측정값이다 ──────────────────────────────────────────
THEMES = {
    'nis': dict(
        label='국정원 표준형',
        note='｢국가 망 보안체계 보안 가이드라인｣·｢AI 보안 가이드북｣ 계열. '
             '188×257mm, 본문 10.5pt, 남색 주조에 하늘색 보조.',
        page=(188, 257), margin=(25, 24, 19, 16), body=10.5,
        ink='#1a1a1a', accent='#24408f', accent2='#006cb7', tint='#e8eef7',
        rule='#c9d3e2', soft='#5b6670', serif=False, badge='pill', chapter='page',
        cover='rule'),
    'field': dict(
        label='분야별 가이드라인형',
        note='｢지능형 전력망｣·｢병원정보시스템｣ 계열. 183×256mm, 본문 11pt, '
             '청록 보조색과 포인트 주황.',
        page=(183, 256), margin=(33, 32, 37, 17), body=11.0,
        ink='#16202b', accent='#0f4c81', accent2='#11ada9', tint='#e6f3f6',
        rule='#cdd8e0', soft='#5f6c76', serif=False, badge='tag', chapter='page',
        cover='band'),
    'control': dict(
        label='통제항목 해설서형',
        note='｢보안통제 항목 해설서｣ 계열. 194×263mm. 표가 지면의 대부분을 차지하므로 '
             '글자를 줄이고 격자를 세운다. 측정값은 8.2pt 이나 화면 가독을 위해 8.6pt 로 둔다.',
        page=(194, 263), margin=(28, 28, 19, 28), body=8.6,
        ink='#111827', accent='#003e7e', accent2='#42b2d2', tint='#eef4fa',
        rule='#b9c4d2', soft='#64748b', serif=False, badge='square', chapter='inline',
        cover='side'),
    'manual': dict(
        label='실무 안내서형',
        note='｢SIEM·SOAR 지침｣ 계열. A4 210×297mm, 하늘색 주조. 짧은 경어체 문서에 쓴다. '
             '측정값은 9pt 이나 화면 가독을 위해 9.5pt 로 둔다.',
        page=(210, 297), margin=(20, 20, 18, 14), body=9.5,
        ink='#0f172a', accent='#006cb7', accent2='#89cada', tint='#cce7f9',
        rule='#c3d9e8', soft='#5b6670', serif=False, badge='pill', chapter='inline',
        cover='tint'),
    'print': dict(
        label='흑백 인쇄형',
        note='1색 인쇄와 복사를 전제한다. 색 대신 괘선과 굵기로 구분하고 '
             '등급 표시를 ■ 로 바꾼다.',
        page=(188, 257), margin=(25, 24, 19, 16), body=10.5,
        ink='#000000', accent='#000000', accent2='#000000', tint='#ededed',
        rule='#000000', soft='#333333', serif=False, badge='square', chapter='page',
        cover='rule'),
}

GOTHIC = ("'Malgun Gothic','맑은 고딕','KoPubWorld돋움체','Noto Sans KR',"
          "'Apple SD Gothic Neo',sans-serif")
MONO = "'D2Coding','Consolas','Menlo',monospace"

# Windows 콘솔 기본 인코딩(cp949)은 ｢ ｣ 같은 글자를 쓰지 못한다.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 캡션은 `[표 2-3] 제목` 꼴이다. `[표 2-3]은 …` 처럼 조사가 바로 붙으면 캡션이
# 아니라 그 표를 가리키는 문단이므로, 닫는 괄호 뒤의 **공백을 반드시 요구한다.**
# 공백을 선택으로 두면 문단 첫머리가 캡션 배지로 먹힌다.
RX_CAP = re.compile(r'^\[(표|그림)\s*([\d\-–.]+)\](?:\s+(\S.*))?$')
RX_IMG = re.compile(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$')
RX_H = re.compile(r'^(#{1,6})\s+(.+)$')
RX_LI = re.compile(r'^(\s*)-\s+(.+)$')
RX_OL = re.compile(r'^(\s*)(\d{1,3})\.\s+(.+)$')
RX_CTL = re.compile(r'\b([A-Z][A-Z0-9]{1,7}-[A-Z]{2}-M?\d{1,3}(?:\(\d{1,2}\))?)')


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def inline(s: str) -> str:
    s = esc(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(｢[^｣]{2,80}｣)', r'<span class="law">\1</span>', s)
    s = RX_CTL.sub(r'<span class="cid">\1</span>', s)
    return s


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip('|').split('|')]


def is_sep(line: str) -> bool:
    return bool(re.fullmatch(r'\|[\s:|-]+\|', line.strip()))


def render_table(rows: list[list[str]], mark: str) -> str:
    head, body = rows[0], rows[1:]
    grade = [i for i, h in enumerate(head) if h in ('C', 'S', 'O')]
    out = ['<table class="%s">' % ('ctl' if grade else 'tbl'), '<thead><tr>']
    for i, h in enumerate(head):
        out.append('<th%s>%s</th>' % (' class="g"' if i in grade else '', inline(h)))
    out.append('</tr></thead><tbody>')
    for r in body:
        out.append('<tr>')
        for i, c in enumerate(r):
            cls = ''
            if i in grade:
                cls = ' class="g"'
                c = mark if c.strip() == '●' else c
            elif i == 0 and RX_CTL.fullmatch(c):
                cls = ' class="idc"'
            out.append('<td%s>%s</td>' % (cls, inline(c)))
        out.append('</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


def embed_svg(path: str, base: str) -> str | None:
    p = os.path.normpath(os.path.join(base, path))
    if not (p.lower().endswith('.svg') and os.path.exists(p)):
        return None
    s = io.open(p, encoding='utf-8').read()
    s = re.sub(r'<\?xml[^>]*\?>', '', s)
    s = re.sub(r'\swidth="\d+"\s+height="\d+"', ' width="100%"', s, count=1)
    return s


def split_front(md: str) -> tuple:
    """원고 머리에서 제목과 발간 정보를 떼어 표지에 쓸 값을 모은다."""
    lines = md.split(chr(10))
    title = ''
    start = 0
    for i, l in enumerate(lines):
        if l.startswith('# '):
            title = l[2:].strip()
            start = i + 1
            break
    meta = {}
    for l in lines[start:start + 60]:
        s = l.strip()
        if s.startswith('|') and s.count('|') >= 3:
            c = split_row(s)
            if len(c) == 2 and c[0] not in ('항목', '---'):
                meta[c[0]] = re.sub(r'[*`]+', '', c[1]).strip()
    return title, meta, chr(10).join(lines[start:])


def split_sections(rest: str) -> tuple:
    """발간 정보 · 목차 · 본문으로 가른다.

    앞의 둘은 앞붙이 쪽에 따로 앉히고, 본문만 흐름에 태운다.
    """
    lines = rest.split(chr(10))
    toc_at = next((i for i, l in enumerate(lines)
                   if re.match(r'^#+\s*목차\s*$', l)), None)
    body_at = next((i for i, l in enumerate(lines) if l.startswith('# ')), None)
    if toc_at is None or body_at is None:
        return '', '', rest
    info = chr(10).join(lines[:toc_at])
    toc = chr(10).join(lines[toc_at:body_at])
    body = chr(10).join(lines[body_at:])
    return info, toc, body


def front_matter(title: str, meta: dict, kind_css: str,
                 info_html: str, toc_html: str) -> str:
    """책 앞붙이. 쪽 차례는 발행본 관행을 따른다.

    표지 · 속표지 · 문서 정보 · 목차 차례로 각각 새 쪽에서 시작한다.

    빈 쪽은 여기서 넣지 않는다. 문서 정보가 한 쪽을 넘치면 뒤 차례가 밀리므로,
    **어느 쪽이 비어야 하는지는 인쇄해 봐야 안다.** `book.py` 가 인쇄한 뒤에
    각 앞붙이를 홀수 쪽으로 맞추며 필요한 만큼만 끼운다.
    """
    return (cover(title, meta, kind_css)
            + '<section class="halftitle"><h1>%s</h1></section>' % inline(title)
            + '<section class="docinfo">%s</section>' % info_html
            + '<section class="tocpage">%s</section>' % toc_html)


def colophon(title: str, meta: dict) -> str:
    """판권지. 책 마지막 쪽에 제목과 발행 정보를 둔다."""
    rows = [(k, meta[k]) for k in
            ('문서 종류', '발행기관', '발간등록번호', '원고 버전', '작성 기준일', '문의처')
            if meta.get(k)]
    cells = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (esc(k), inline(v))
                    for k, v in rows)
    return ('<section class="colophon">'
            '<p class="colt">%s</p>'
            '<table class="colt-t"><tbody>%s</tbody></table>'
            '</section>' % (inline(title), cells))


def cover(title: str, meta: dict, kind_css: str = 'rule') -> str:
    """발행본 표지. 기관이 채울 칸은 원고의 값을 그대로 보여 준다."""
    kind = meta.get('문서 종류', '')
    org = meta.get('발행기관', '')
    date = meta.get('작성 기준일', '')
    m = re.match(r'\s*(\d{4})\.\s*(\d{1,2})\.', date)
    ym = '%s. %s.' % (m.group(1), m.group(2)) if m else date
    ver = meta.get('원고 버전', '')
    return ('<section class="cover cv-%s">' % kind_css
            + '<div class="cvtop">'
            + ('<p class="ckind">%s</p>' % inline(kind) if kind else '')
            + '<h1 class="ctitle">%s</h1>' % inline(title)
            + '</div><div class="cvbot">'
            + '<p class="cdate">%s</p>' % esc(ym)
            + '<p class="corg">%s</p>' % inline(org)
            + ('<p class="cver">%s</p>' % inline(ver) if ver else '')
            + '</div></section>')


def convert(md: str, base: str, mark: str, pages: dict = None) -> str:
    lines = md.split('\n')
    out: list[str] = []
    i, n = 0, len(lines)
    pages = pages or {}
    ul_open = 0
    toc = False
    pending_cap = None

    def close_lists():
        nonlocal ul_open
        while ul_open:
            out.append('</ul>')
            ul_open -= 1

    while i < n:
        line = lines[i]
        s = line.strip()

        if s.startswith('```'):
            close_lists()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith('```'):
                buf.append(esc(lines[i]))
                i += 1
            i += 1
            out.append('<pre>%s</pre>' % '\n'.join(buf))
            continue

        if not s:
            close_lists()
            i += 1
            continue

        m = RX_H.match(line)
        if m:
            close_lists()
            lv, txt = len(m.group(1)), m.group(2).strip()
            if lv == 1 and txt == '부록':
                out.append('<section class="chapter"><h1>부록</h1></section>')
                i += 1
                continue
            mm = re.match(r'^부록\s*(\d+)\s+(.+)$', txt)
            if lv == 2 and mm:
                out.append('<h2 class="apx"><span class="bdg">부록 %s</span>'
                           '<span class="ht">%s</span></h2>'
                           % (mm.group(1), inline(mm.group(2))))
                i += 1
                continue
            mm = re.match(r'^제(\d+)장\s+(.+)$', txt)
            if lv == 1 and mm:
                out.append('<section class="chapter"><p class="chno">제%s장</p>'
                           '<h1>%s</h1></section>' % (mm.group(1), inline(mm.group(2))))
                i += 1
                continue
            mm = re.match(r'^제(\d+)절\s+(.+)$', txt)
            if lv == 2 and mm:
                out.append('<h2><span class="bdg">제%s절</span><span class="ht">%s</span></h2>'
                           % (mm.group(1), inline(mm.group(2))))
                i += 1
                continue
            toc = txt == '목차'
            out.append('<h%d%s>%s</h%d>' % (min(lv, 6), ' class="toch"' if toc else '',
                                            inline(txt), min(lv, 6)))
            i += 1
            continue

        m = RX_CAP.match(s)
        if m and (m.group(3) or '').rstrip().endswith('다.'):
            m = None  # 문장이다. 캡션은 마침표로 끝나지 않는다
        if m:
            close_lists()
            kind = 'fig' if m.group(1) == '그림' else 'tbl'
            pending_cap = ('<p class="cap cap-%s"><span class="capn">%s %s</span>'
                           '<span class="capt">%s</span></p>'
                           % (kind, m.group(1), m.group(2), inline(m.group(3) or '')))
            out.append(pending_cap)
            i += 1
            continue

        m = RX_IMG.match(s)
        if m:
            close_lists()
            svg = embed_svg(m.group(2), base)
            out.append('<figure>%s</figure>' %
                       (svg if svg else '<img src="%s" alt="%s">' % (esc(m.group(2)), esc(m.group(1)))))
            i += 1
            continue

        if s.startswith('|') and i + 1 < n and is_sep(lines[i + 1]):
            close_lists()
            rows = [split_row(line)]
            i += 2
            while i < n and lines[i].strip().startswith('|'):
                rows.append(split_row(lines[i]))
                i += 1
            out.append(render_table(rows, mark))
            continue

        if s.startswith('※'):
            close_lists()
            out.append('<p class="note">%s</p>' % inline(s))
            i += 1
            continue

        if s.startswith('■'):
            close_lists()
            out.append('<p class="implhead">%s</p>' % inline(s.lstrip('■ ').strip()))
            i += 1
            continue

        m = RX_LI.match(line)
        if m:
            if toc:
                txt = m.group(2).strip()
                ch = bool(re.match(r'^(제\d+장|부록)', txt))
                pg = pages.get(txt)
                out.append('<p class="toc%s"><span class="tt">%s</span>%s</p>'
                           % (' tc' if ch else '', inline(txt),
                              '<span class="tp">%d</span>' % pg if pg else ''))
                i += 1
                continue
            depth = 1 + (len(m.group(1)) >= 2)
            while ul_open < depth:
                out.append('<ul>')
                ul_open += 1
            while ul_open > depth:
                out.append('</ul>')
                ul_open -= 1
            out.append('<li>%s</li>' % inline(m.group(2)))
            i += 1
            continue

        m = RX_OL.match(line)
        if m:
            close_lists()
            out.append('<p class="num"><span class="n">%s.</span>%s</p>'
                       % (m.group(2), inline(m.group(3))))
            i += 1
            continue

        close_lists()
        out.append('<p>%s</p>' % inline(s))
        i += 1

    close_lists()
    return '\n'.join(out)


def css(t: dict) -> str:
    w, h = t['page']
    ml, mr, mt, mb = t['margin']
    badge = t['badge']
    radius = {'pill': '999px', 'tag': '3px', 'square': '0'}[badge]
    return """
:root{--ink:%(ink)s;--accent:%(accent)s;--accent2:%(accent2)s;--tint:%(tint)s;
 --rule:%(rule)s;--soft:%(soft)s;--body:%(font)s;--mono:%(mono)s}
*{box-sizing:border-box}
body{margin:0;background:#edeef0;color:var(--ink);font-family:var(--body);
 font-size:%(body)spt;line-height:1.72;word-break:keep-all;-webkit-text-size-adjust:100%%}
.sheet{width:%(w)smm;min-height:%(h)smm;margin:10mm auto;background:#fff;
 padding:%(mt)smm %(mr)smm %(mb)smm %(ml)smm;box-shadow:0 1px 6px rgba(0,0,0,.15);
 position:relative;counter-increment:pg}
h1,h2,h3,h4{line-height:1.38;margin:0}
p{margin:0 0 .8em}
ul{margin:0 0 .8em;padding-left:1.15em}li{margin:.18em 0}
code{font-family:var(--mono);font-size:.92em}
.cid{font-family:var(--mono);font-size:.92em;white-space:nowrap}
.law{white-space:nowrap}
.num{margin:0 0 .45em;padding-left:1.5em;text-indent:-1.5em}
.num .n{display:inline-block;width:1.5em;text-indent:0;color:var(--accent);font-weight:700}
.chapter{margin:0 0 9mm;padding:7mm 0;border-top:3px solid var(--accent);
 border-bottom:1px solid var(--rule)}
.chno{margin:0 0 .35em;color:var(--accent);font-weight:700;letter-spacing:.12em;font-size:.92em}
.chapter h1{font-size:1.75em;font-weight:800;letter-spacing:-.02em}
h2{display:flex;align-items:center;gap:.5em;margin:1.9em 0 .9em;font-size:1.3em;font-weight:800}
h2 .bdg{background:var(--accent);color:#fff;border-radius:%(radius)s;padding:.12em .7em;
 font-size:.72em;font-weight:700;letter-spacing:.02em;white-space:nowrap}
h3{font-size:1.08em;font-weight:700;margin:1.6em 0 .55em;padding-left:.45em;
 border-left:3px solid var(--accent2)}
h4{font-size:1em;font-weight:700;margin:1.3em 0 .45em;color:var(--accent)}
.cover{page:cover;display:flex;flex-direction:column;justify-content:center;
 min-height:%(coverh)smm;text-align:center;padding:%(mt)smm %(mr)smm %(mb)smm %(ml)smm;
 margin:-%(mt)smm -%(mr)smm 0 -%(ml)smm}
.cvtop,.cvbot{width:100%%}
.ckind{color:var(--accent);font-weight:700;letter-spacing:.3em;font-size:.86em;margin:0 0 1.5em}
.ctitle{font-size:2.05em;font-weight:800;line-height:1.36;letter-spacing:-.03em;margin:0}
.cdate{font-size:1.05em;color:var(--soft);margin:0 0 .3em}
.corg{font-size:1.15em;font-weight:700;margin:0 0 .2em}
.cver{font-size:.85em;color:var(--soft);margin:.9em 0 0}
.cvbot{margin-top:3.4em}

/* 괘선형 — 흰 바탕에 상하 굵은 선. ｢국가 망 보안체계 보안 가이드라인｣ 계열 */
.cv-rule .cvtop{border-top:6px solid var(--accent);padding-top:0}
.cv-rule{border-top:6px solid var(--accent);border-bottom:6px solid var(--accent);
 margin:0;padding:8%% %(mr)smm 8%% %(ml)smm}
.cv-rule .cvtop{border:0}

/* 색면형 — 위쪽을 색으로 덮고 아래에 기관을 둔다. ｢지능형 전력망｣·｢AI 보안 가이드북｣ 계열 */
.cv-band{justify-content:space-between;padding:0}
.cv-band .cvtop{background:linear-gradient(165deg,var(--accent),var(--accent2));
 color:#fff;padding:32%% 14mm 13%%;margin:0}
.cv-band .ckind{color:#fff;opacity:.88}
.cv-band .cvbot{padding:0 14mm 18mm;margin:0}

/* 측면형 — 왼쪽에 색 바를 세우고 왼쪽으로 맞춘다. 부속 해설서 계열 */
.cv-side{text-align:left;padding:%(mt)smm %(mr)smm %(mb)smm 0;
 border-left:10mm solid var(--accent)}
.cv-side .cvtop,.cv-side .cvbot{padding-left:12mm}

/* 바탕형 — 연한 색을 전면에 깐다. ｢SIEM·SOAR 지침｣ 계열 */
.cv-tint{background:var(--tint);border-top:4mm solid var(--accent);padding:0 14mm}

.halftitle{break-before:page;break-after:page;display:flex;align-items:center;justify-content:center;
 min-height:%(coverh)smm;text-align:center}
.halftitle h1{font-size:1.5em;font-weight:800;line-height:1.4;letter-spacing:-.02em}
.docinfo{break-before:page;break-after:page}
.tocpage{break-before:page;break-after:page}
.colophon{break-before:page;display:flex;flex-direction:column;justify-content:flex-end;
 min-height:%(coverh)smm}
.colt{font-size:1.15em;font-weight:800;line-height:1.45;margin:0 0 1.1em;
 padding-bottom:.7em;border-bottom:3px solid var(--accent)}
.colt-t{width:100%%;border-collapse:collapse;font-size:.92em}
.colt-t th{width:30mm;text-align:left;font-weight:700;border:0;padding:.35em .4em .35em 0;
 background:none;color:var(--soft)}
.colt-t td{border:0;padding:.35em 0}
h2.apx{break-before:page}
.toch{margin-bottom:.7em}
.toc{margin:0 0 .25em;padding-left:1.4em;color:var(--soft);font-size:.95em;
 display:flex;align-items:baseline;gap:.4em}
.toc .tt{flex:0 1 auto}
.toc .tp{margin-left:auto;font-variant-numeric:tabular-nums;color:var(--soft);
 padding-left:.6em}
.toc:has(.tp) .tt:after{content:"";display:inline-block;width:0}
.toc .tt+.tp:before{content:"";display:block}
.toc.tc{padding-left:0;margin-top:.85em;color:var(--ink);font-weight:700;font-size:1em;
 border-bottom:1px solid var(--rule);padding-bottom:.25em}
.toc.tc .tp{color:var(--accent)}
.ctl th:first-child,.ctl td:first-child{width:21mm}
.ctl th:nth-child(2),.ctl td:nth-child(2){width:23mm}
.ctl th:first-child{white-space:nowrap}
.cap{margin:1.5em 0 .45em;display:flex;align-items:center;gap:.5em;font-size:.94em}
.capn{background:var(--tint);color:var(--accent);border-radius:%(radius)s;
 padding:.1em .6em;font-weight:700;font-size:.9em;white-space:nowrap}
.capt{font-weight:700}
table{border-collapse:collapse;width:100%%;margin:0 0 1.1em;font-size:.92em}
th,td{vertical-align:top;padding:.5em .45em;border:1px solid var(--rule)}
th{background:var(--tint);font-weight:700;text-align:left}
.ctl th.g,.ctl td.g{width:7mm;text-align:center}
.ctl td.idc{font-family:var(--mono);font-size:.9em;white-space:nowrap}
.tbl th{background:var(--tint)}
figure{margin:0 0 1.1em}figure svg,figure img{display:block;width:100%%;height:auto}
.note{font-size:.92em;color:var(--soft);margin:.2em 0 1em}
.implhead{font-weight:700;margin:1.2em 0 .4em;color:var(--accent)}
pre{background:var(--tint);padding:.8em 1em;overflow:auto;font-family:var(--mono);
 font-size:.86em;line-height:1.5;margin:0 0 1em;border-left:3px solid var(--accent2)}
.rh{position:absolute;top:%(rh)smm;left:%(ml)smm;right:%(mr)smm;display:flex;
 font-size:8pt;color:var(--soft);border-bottom:1px solid var(--rule);padding-bottom:1.5mm}
.rh .doc{margin-left:auto}
@page{size:%(w)smm %(h)smm;margin:%(mt)smm %(mr)smm %(mb)smm %(ml)smm}
@page cover{size:%(w)smm %(h)smm;margin:0}
@media print{body{background:#fff}
 .cover{min-height:%(h)smm;height:%(h)smm;margin:0;break-after:page;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
 .halftitle,.colophon{min-height:%(coverp)smm;height:%(coverp)smm}
 .sheet{width:auto;min-height:0;margin:0;padding:0;box-shadow:none}
 .rh{display:none}
 .chapter{%(brk)s}
 tr,figure,.cap{break-inside:avoid}h2,h3,h4{break-after:avoid}}
""" % dict(ink=t['ink'], accent=t['accent'], accent2=t['accent2'], tint=t['tint'],
           rule=t['rule'], soft=t['soft'], font=GOTHIC, mono=MONO, body=t['body'],
           w=w, h=h, ml=ml, mr=mr, mt=mt, mb=mb, radius=radius,
           rh=max(5, mt - 11), brk='break-before:page' if t['chapter'] == 'page' else '',
           coverh=h - mt - mb - 20, coverp=h - mt - mb - 4,
           coverb=h - mb - 4)


def recto_marks(md: str, title: str) -> list:
    """홀수 쪽에서 시작해야 하는 자리의 표지를 차례대로 돌려준다.

    인쇄본에서 이 글자를 찾아 그 쪽이 짝수면 앞에 빈 쪽을 끼운다. 표지는 늘
    1쪽이므로 넣지 않는다.
    """
    _, _, rest = split_front(md)
    info_md, toc_md, body_md = split_sections(rest)
    marks = [title]
    for block in (info_md, toc_md):
        h = next((l for l in block.split(chr(10)) if l.startswith('#')), '')
        h = h.lstrip('#').strip()
        if h:
            marks.append(h)
    first = next((l for l in body_md.split(chr(10)) if l.startswith('# ')), '')
    m = re.match(r'^#\s*(제\d+장)', first)
    if m:
        marks.append(m.group(1))
    return marks


def build(md: str, base: str, key: str, title: str, pages: dict = None) -> str:
    t = THEMES[key]
    mark = '■' if key == 'print' else '●'
    doctitle, meta, rest = split_front(md)
    name = doctitle or title
    info_md, toc_md, body_md = split_sections(rest)
    body = (front_matter(name, meta, t.get('cover', 'rule'),
                         convert(info_md, base, mark, pages),
                         convert(toc_md, base, mark, pages))
            + convert(body_md, base, mark, pages)
            + colophon(name, meta))
    return """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>%s</style></head>
<body><main class="sheet">
<div class="rh"><span>%s</span><span class="doc">%s</span></div>
%s
</main></body></html>
""" % (esc(title), css(t), esc(t['label']), esc(title), body)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source', nargs='?')
    ap.add_argument('--theme', default='nis')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--themes', action='store_true')
    ap.add_argument('--out', default=None)
    ap.add_argument('--toc', default=None,
                    help='toc.py 가 만든 쪽번호 json. 목차에 넣는다.')
    a = ap.parse_args(argv)

    if a.themes or not a.source:
        print('테마')
        for k, t in THEMES.items():
            print('  %-9s %-16s %dx%dmm  본문 %gpt' % (k, t['label'], t['page'][0], t['page'][1], t['body']))
            print('            %s' % t['note'])
        return 0 if a.themes else 2

    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    md = io.open(a.source, encoding='utf-8').read()
    base = os.path.dirname(os.path.abspath(a.source))
    out = a.out or os.path.join(base, 'dist')
    os.makedirs(out, exist_ok=True)
    title = next((l[2:].strip() for l in md.split('\n') if l.startswith('# ')), '가이드라인')
    pages = {}
    if a.toc:
        if not os.path.exists(a.toc):
            print('없는 파일: %s' % a.toc)
            return 2
        pages = json.load(io.open(a.toc, encoding='utf-8'))
        print('목차 쪽번호 %d개를 넣는다' % len(pages))

    keys = list(THEMES) if a.all else [a.theme]
    for k in keys:
        if k not in THEMES:
            print('없는 테마: %s' % k)
            return 2
        p = os.path.join(out, '%s.html' % k)
        io.open(p, 'w', encoding='utf-8', newline='\n').write(build(md, base, k, title, pages))
        mp = os.path.join(out, '%s-구성.json' % k)
        io.open(mp, 'w', encoding='utf-8', newline='\n').write(
            json.dumps({'recto': recto_marks(md, title)}, ensure_ascii=False, indent=1) + '\n')
        print('%s  (%s)' % (p, THEMES[k]['label']))

    if a.all:
        cards = '\n'.join(
            '<a class="s" href="%s.html"><strong>%s</strong>'
            '<em>%dx%dmm · 본문 %gpt</em><span>%s</span></a>'
            % (k, THEMES[k]['label'], THEMES[k]['page'][0], THEMES[k]['page'][1],
               THEMES[k]['body'], THEMES[k]['note']) for k in THEMES)
        io.open(os.path.join(out, 'index.html'), 'w', encoding='utf-8', newline='\n').write(
            """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>배포본 디자인</title><style>
body{margin:0;background:#f5f6f8;color:#16181d;font-family:FONT;line-height:1.7;word-break:keep-all}
main{max-width:820px;margin:0 auto;padding:44px 20px 60px}
h1{font-size:21px;margin:0 0 6px}p.l{color:#5b6670;margin:0 0 26px}
.s{display:block;border:1px solid #e1e4e8;border-radius:10px;background:#fff;
 padding:15px 17px;text-decoration:none;color:inherit;margin-bottom:11px}
.s:hover{border-color:#24408f}.s strong{display:block;font-size:16px}
.s em{font-style:normal;color:#24408f;font-size:13px}
.s span{display:block;color:#5b6670;font-size:13.5px;margin-top:3px}
</style></head><body><main><h1>배포본 디자인</h1>
<p class="l">같은 원고를 테마만 바꿔 뽑은 것입니다. 판면·여백·본문 크기는 국내 발행본
20종을 측정해 정했습니다. 브라우저에서 인쇄하면 그 판면으로 PDF 가 나옵니다.</p>
CARDS</main></body></html>""".replace('FONT', GOTHIC).replace('CARDS', cards))
        print(os.path.join(out, 'index.html'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
