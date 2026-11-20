"""figures.py — 삽도를 SVG 로 그린다.

명세(JSON)를 받아 그림을 그립니다. 색과 글꼴은 **조판 테마를 그대로 따르므로**
`nis` 로 조판한 문서의 삽도는 남색 계열이고 `print` 로 조판하면 흑백이 됩니다.

    python figures.py 명세.json --out figures/ --theme nis
    python figures.py --types                  # 그릴 수 있는 꼴

글자는 글자로 남습니다. 조판 단계에서 글꼴과 크기를 바꿀 수 있고, 인쇄에서
선명하며, 본문 검색에 걸립니다. 래스터 이미지로 굽지 않습니다.

화살표 머리는 `<marker>` 대신 삼각형으로 직접 그립니다. 변환기가 marker 를
무시하면 화살표가 선만 남기 때문입니다.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


# ── 테마에서 색을 가져온다 ────────────────────────────────────────────────
def theme_palette(key: str = 'nis') -> dict:
    """조판 테마의 색을 삽도에 쓴다. 문서와 삽도가 따로 놀지 않게 한다."""
    try:
        sys.path.insert(0, HERE)
        import render  # noqa
        render.load_themes()
        t = dict(render.DEFAULTS, **render.THEMES.get(key, {}))
    except Exception:
        t = dict(ink='#1a1a1a', accent='#24408f', accent2='#006cb7',
                 tint='#e8eef7', rule='#c9d3e2', soft='#5b6670')
    mono = key == 'print'
    return dict(
        ink=t['ink'], accent=t['accent'], accent2=t['accent2'],
        tint=t['tint'], rule=t['rule'], soft=t['soft'],
        mono=mono,
        fill='#ffffff' if mono else t['tint'],
        stroke=t['ink'] if mono else t['rule'],
        hot=t['ink'] if mono else '#c0392b',
    )


# ── 글자 폭 어림 ──────────────────────────────────────────────────────────
def char_w(ch: str, size: float) -> float:
    o = ord(ch)
    if o < 128:
        return size * (0.30 if ch == ' ' else 0.52)
    if 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF:
        return size * 0.62          # 구두점·반각
    return size * 1.0               # 한글·한자


def text_w(s: str, size: float) -> float:
    return sum(char_w(c, size) for c in s)


def wrap(s: str, width: float, size: float, maxlines: int = 4) -> list:
    """폭에 맞춰 줄을 나눈다. 한국어는 낱말 단위로 끊는다."""
    words, lines, cur = s.split(' '), [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if text_w(trial, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        lines[-1] = lines[-1][:-1] + '…'
    return lines


def fit(s: str, width: float, height: float, size: float,
        lh: float = 1.32, minsize: float = 6.5) -> tuple:
    """상자 안에 들어갈 때까지 글자를 줄인다. (줄 목록, 크기)"""
    while size >= minsize:
        lines = wrap(s, width, size)
        if len(lines) * size * lh <= height:
            return lines, size
        size -= 0.5
    return wrap(s, width, minsize), minsize


def esc(s) -> str:
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


# ── 작도 ──────────────────────────────────────────────────────────────────
class Canvas:
    def __init__(self, w: float, h: float, pal: dict):
        self.w, self.h, self.p = w, h, pal
        self.el: list = []
        self.defs: list = []

    def add(self, s: str):
        self.el.append(s)

    # 기본 도형
    def rect(self, x, y, w, h, fill='none', stroke=None, rx=3, sw=1, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        st = self.p['stroke'] if stroke is None else stroke
        self.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" '
                 'stroke="%s" stroke-width="%g"%s/>'
                 % (x, y, w, h, rx, fill, st, sw, d))

    def line(self, x1, y1, x2, y2, stroke=None, sw=1, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        st = self.p['stroke'] if stroke is None else stroke
        self.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
                 'stroke-width="%g"%s/>' % (x1, y1, x2, y2, st, sw, d))

    def text(self, x, y, s, size=9, fill=None, anchor='middle', weight=None,
             mono=False, opacity=None):
        f = self.p['ink'] if fill is None else fill
        w = ' font-weight="%s"' % weight if weight else ''
        o = ' opacity="%g"' % opacity if opacity is not None else ''
        fam = ('font-family="D2Coding,Consolas,monospace"' if mono
               else 'font-family="Malgun Gothic,맑은 고딕,Noto Sans KR,sans-serif"')
        self.add('<text x="%g" y="%g" %s font-size="%g" fill="%s" '
                 'text-anchor="%s"%s%s>%s</text>'
                 % (x, y, fam, size, f, anchor, w, o, esc(s)))

    def block(self, x, y, w, h, s, size=9, fill=None, anchor='middle',
              weight=None, lh=1.32, mono=False, pad=4, sub=0.86):
        """상자 안에 여러 줄로 앉힌다. 넘치면 글자를 줄인다.

        명세에 적은 줄바꿈("\n")을 지킨다. 지키지 않으면 "참여자 인증" 과
        "PRS-MW-2" 가 한 덩어리로 붙어 읽히지 않는다. 둘째 줄부터는 조금
        작게, 고정폭으로 앉힌다 — 통제 ID 나 부연이 오는 자리이기 때문이다.
        """
        parts = [p.strip() for p in str(s).split("\n") if p.strip()]
        if len(parts) < 2:
            lines, size = fit(s, w - pad * 2, h - pad, size, lh)
            total = len(lines) * size * lh
            y0 = y + (h - total) / 2 + size * 0.95
            ax = {'middle': x + w / 2, 'start': x + pad, 'end': x + w - pad}[anchor]
            for i, ln in enumerate(lines):
                self.text(ax, y0 + i * size * lh, ln, size, fill, anchor, weight, mono)
            return size

        while size >= 6.0:
            rows = []
            for pi, p in enumerate(parts):
                sz = size if pi == 0 else size * sub
                for ln in wrap(p, w - pad * 2, sz):
                    rows.append((ln, sz, pi))
            if sum(r[1] for r in rows) * lh <= h - pad:
                break
            size -= 0.5
        total = sum(r[1] for r in rows) * lh
        y0 = y + (h - total) / 2 + rows[0][1] * 0.95
        ax = {'middle': x + w / 2, 'start': x + pad, 'end': x + w - pad}[anchor]
        yy = y0
        for ln, sz, pi in rows:
            self.text(ax, yy, ln, sz, fill, anchor,
                      weight if pi == 0 else None, mono or pi > 0)
            yy += sz * lh
        return size

    def arrow(self, x1, y1, x2, y2, color=None, sw=1.3, dash=None, size=7):
        """화살표. 머리를 삼각형으로 직접 그린다 — marker 는 변환에서 사라진다."""
        c = self.p['soft'] if color is None else color
        a = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - size * math.cos(a), y2 - size * math.sin(a)
        self.line(x1, y1, bx, by, c, sw, dash)
        wd = size * 0.5
        p1 = (bx - wd * math.sin(a), by + wd * math.cos(a))
        p2 = (bx + wd * math.sin(a), by - wd * math.cos(a))
        self.add('<polygon points="%g,%g %g,%g %g,%g" fill="%s"/>'
                 % (x2, y2, p1[0], p1[1], p2[0], p2[1], c))

    def chip(self, x, y, s, size=7.5, fill=None, fg='#ffffff', pad=5, h=13):
        """번호·꼬리표용 작은 배지."""
        f = self.p['accent'] if fill is None else fill
        w = text_w(s, size) + pad * 2
        self.rect(x, y, w, h, f, f, h / 2 if not self.p['mono'] else 2, 0.8)
        self.text(x + w / 2, y + h * 0.72, s, size, fg, 'middle', '700')
        return w

    def caption(self, s):
        """그림 아래에 두는 보충 설명."""
        self.text(self.w / 2, self.h - 6, s, 7.6, self.p['soft'], 'middle')

    def render(self) -> str:
        d = ('<defs>%s</defs>' % ''.join(self.defs)) if self.defs else ''
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" width="%g" height="%g" '
                'viewBox="0 0 %g %g">%s'
                '<rect width="%g" height="%g" fill="#ffffff"/>%s</svg>\n'
                % (self.w, self.h, self.w, self.h, d, self.w, self.h,
                   ''.join(self.el)))


def grad(c: Canvas, name: str, a: str, b: str, angle: int = 160) -> str:
    """절제된 그라데이션. 흑백 테마에서는 쓰지 않는다."""
    if c.p['mono']:
        return a
    rad = math.radians(angle)
    c.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="%g" y2="%g">'
                  '<stop offset="0" stop-color="%s"/>'
                  '<stop offset="1" stop-color="%s"/></linearGradient>'
                  % (name, abs(math.cos(rad)), abs(math.sin(rad)), a, b))
    return 'url(#%s)' % name


# ── 그림 꼴 ───────────────────────────────────────────────────────────────
def draw_architecture(spec: dict, pal: dict) -> Canvas:
    """계층·구역 구성. layers[].items[] 를 위에서 아래로 쌓는다."""
    layers = spec['layers']
    W = spec.get('width', 760)
    pad, gap, lh = 16, 12, spec.get('layer_height', 58)
    H = pad * 2 + len(layers) * lh + (len(layers) - 1) * gap + 26
    c = Canvas(W, H, pal)
    y = pad + 14
    for li, L in enumerate(layers):
        c.rect(pad, y, W - pad * 2, lh, pal['fill'] if li % 2 == 0 else '#ffffff',
               pal['rule'], 4, 1, '4 3' if L.get('dashed') else None)
        if L.get('label'):
            c.chip(pad + 8, y - 7, L['label'])
        items = L.get('items', [])
        if items:
            iw = (W - pad * 2 - 20 - gap * (len(items) - 1)) / len(items)
            for i, it in enumerate(items):
                ix = pad + 10 + i * (iw + gap)
                name = it if isinstance(it, str) else it.get('text', '')
                hot = isinstance(it, dict) and it.get('mark')
                c.rect(ix, y + 12, iw, lh - 24, '#ffffff',
                       pal['hot'] if hot else pal['accent2'], 3, 1.1)
                c.block(ix, y + 12, iw, lh - 24, name, 8.4,
                        pal['hot'] if hot else pal['ink'], weight='600')
        y += lh + gap
    if spec.get('note'):
        c.caption(spec['note'])
    return c


def draw_flow(spec: dict, pal: dict) -> Canvas:
    """데이터·통신 흐름. nodes 를 가로로 놓고 edges 로 잇는다."""
    nodes, edges = spec['nodes'], spec.get('edges', [])
    W = spec.get('width', 760)
    bh, pad = 46, 18
    H = spec.get('height', 150 + (26 if spec.get('note') else 0))
    c = Canvas(W, H, pal)
    n = len(nodes)
    bw = (W - pad * 2 - 26 * (n - 1)) / n
    y = (H - bh) / 2 - 8
    pos = {}
    for i, nd in enumerate(nodes):
        x = pad + i * (bw + 26)
        name = nd if isinstance(nd, str) else nd.get('text', '')
        sub = '' if isinstance(nd, str) else nd.get('sub', '')
        c.rect(x, y, bw, bh, '#ffffff', pal['accent'], 4, 1.2)
        c.block(x, y + (4 if sub else 0), bw, bh - (14 if sub else 0), name, 9,
                pal['ink'], weight='700')
        if sub:
            c.text(x + bw / 2, y + bh - 7, sub, 7.4, pal['soft'])
        pos[i] = (x, x + bw, y + bh / 2)
    for e in edges:
        a, b = e['from'], e['to']
        lab = e.get('label', '')
        x1, y1 = pos[a][1], pos[a][2]
        x2 = pos[b][0]
        c.arrow(x1 + 3, y1, x2 - 3, y1, pal['accent2'] if not e.get('mark') else pal['hot'],
                1.4, '4 3' if e.get('dashed') else None)
        if lab:
            c.text((x1 + x2) / 2, y1 - 7, lab, 7.4, pal['soft'])
    if spec.get('note'):
        c.caption(spec['note'])
    return c


def draw_process(spec: dict, pal: dict) -> Canvas:
    """절차. steps 를 번호와 함께 나란히 둔다."""
    steps = spec['steps']
    W = spec.get('width', 760)
    pad = 16
    n = len(steps)
    bw = (W - pad * 2 - 22 * (n - 1)) / n
    bh = spec.get('step_height', 78)
    H = bh + 50 + (18 if spec.get('note') else 0)
    c = Canvas(W, H, pal)
    y = 30
    for i, st in enumerate(steps):
        x = pad + i * (bw + 22)
        title = st if isinstance(st, str) else st.get('text', '')
        desc = '' if isinstance(st, str) else st.get('desc', '')
        c.rect(x, y, bw, bh, pal['fill'], pal['rule'], 4, 1)
        c.chip(x + 8, y - 8, str(i + 1))
        c.block(x, y + 8, bw, 24, title, 9, pal['ink'], weight='700')
        if desc:
            c.block(x, y + 32, bw, bh - 38, desc, 7.8, pal['soft'])
        if i < n - 1:
            c.arrow(x + bw + 3, y + bh / 2, x + bw + 19, y + bh / 2, pal['accent2'], 1.4)
    if spec.get('note'):
        c.caption(spec['note'])
    return c


def draw_compare(spec: dict, pal: dict) -> Canvas:
    """비교. columns 머리와 rows 의 값을 격자로 둔다."""
    cols, rows = spec['columns'], spec['rows']
    W = spec.get('width', 760)
    pad = 16
    labw = spec.get('label_width', 150)
    cw = (W - pad * 2 - labw) / len(cols)
    rh = spec.get('row_height', 42)
    H = 34 + len(rows) * rh + 20 + (16 if spec.get('note') else 0)
    c = Canvas(W, H, pal)
    y = 16
    c.rect(pad + labw, y, cw * len(cols), 26, pal['fill'], pal['rule'], 3, 1)
    for i, col in enumerate(cols):
        c.block(pad + labw + i * cw, y, cw, 26, col, 8.8, pal['accent'], weight='700')
    y += 26
    for r in rows:
        c.line(pad, y, W - pad, y, pal['rule'], 0.8)
        c.block(pad, y, labw, rh, r['label'], 8.4, pal['ink'], 'start', '700', pad=6)
        for i, v in enumerate(r['values']):
            c.block(pad + labw + i * cw, y, cw, rh, v, 8, pal['soft'])
        y += rh
    c.line(pad, y, W - pad, y, pal['rule'], 0.8)
    for i in range(len(cols) + 1):
        x = pad + labw + i * cw
        c.line(x, 16, x, y, pal['rule'], 0.6)
    if spec.get('note'):
        c.caption(spec['note'])
    return c


def draw_threat(spec: dict, pal: dict) -> Canvas:
    """공격 경로. 구역 위에 공격 단계를 번호로 얹고 대응 통제를 붙인다."""
    zones = spec['zones']
    steps = spec.get('steps', [])
    W = spec.get('width', 760)
    pad = 16
    zw = (W - pad * 2 - 16 * (len(zones) - 1)) / len(zones)
    zh = 66
    H = zh + 40 + len(steps) * 17 + 18
    c = Canvas(W, H, pal)
    y = 26
    cx = []
    for i, z in enumerate(zones):
        x = pad + i * (zw + 16)
        c.rect(x, y, zw, zh, '#ffffff', pal['rule'], 4, 1)
        c.chip(x + 8, y - 8, z.get('label', '구역 %d' % (i + 1)), fill=pal['soft'])
        c.block(x, y + 10, zw, zh - 16, z.get('text', ''), 8.4, pal['ink'], weight='600')
        cx.append((x, x + zw, y + zh / 2))
    for i in range(len(zones) - 1):
        c.arrow(cx[i][1] + 2, cx[i][2], cx[i + 1][0] - 2, cx[i + 1][2], pal['hot'], 1.6)
    y += zh + 16
    for i, s in enumerate(steps):
        c.chip(pad, y - 9, '%d' % (i + 1), 7, pal['hot'])
        txt = s if isinstance(s, str) else s.get('text', '')
        ctl = '' if isinstance(s, str) else s.get('control', '')
        c.text(pad + 24, y, txt, 8, pal['ink'], 'start')
        if ctl:
            c.text(W - pad, y, ctl, 7.6, pal['accent'], 'end', mono=True)
        y += 17
    if spec.get('note'):
        c.caption(spec['note'])
    return c


def draw_matrix(spec: dict, pal: dict) -> Canvas:
    """행렬. 등급·대응 관계처럼 ● 로 채우는 표."""
    cols, rows = spec['columns'], spec['rows']
    W = spec.get('width', 620)
    pad, labw = 16, spec.get('label_width', 230)
    cw = (W - pad * 2 - labw) / len(cols)
    rh = spec.get('row_height', 24)
    H = 30 + len(rows) * rh + 18
    c = Canvas(W, H, pal)
    y = 16
    for i, col in enumerate(cols):
        c.text(pad + labw + i * cw + cw / 2, y + 14, col, 8.6, pal['accent'],
               weight='700')
    y += 22
    mark = '■' if pal['mono'] else '●'
    for r in rows:
        c.line(pad, y, W - pad, y, pal['rule'], 0.7)
        c.block(pad, y, labw, rh, r['label'], 8.2, pal['ink'], 'start', pad=4)
        for i, v in enumerate(r['values']):
            if v:
                c.text(pad + labw + i * cw + cw / 2, y + rh * 0.68, mark, 8.6,
                       pal['accent'])
        y += rh
    c.line(pad, y, W - pad, y, pal['rule'], 0.7)
    if spec.get('note'):
        c.caption(spec['note'])
    return c


def draw_concept(spec: dict, pal: dict) -> Canvas:
    """개념도. 가운데 핵심을 두고 둘레에 요소를 돌린다."""
    items = spec['items']
    W = spec.get('width', 620)
    H = spec.get('height', 330)
    c = Canvas(W, H, pal)
    cx, cy = W / 2, H / 2 - 6
    R = min(W, H) * 0.33
    g = grad(c, 'cg', pal['accent'], pal['accent2'])
    c.add('<circle cx="%g" cy="%g" r="%g" fill="%s" opacity="%g"/>'
          % (cx, cy, R * 0.52, g, 1 if not pal['mono'] else 0))
    if pal['mono']:
        c.add('<circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="1.4"/>'
              % (cx, cy, R * 0.52, pal['ink']))
    c.block(cx - R * 0.45, cy - 16, R * 0.9, 32, spec.get('center', ''), 10,
            pal['ink'] if pal['mono'] else '#ffffff', weight='700')
    n = len(items)
    for i, it in enumerate(items):
        a = -math.pi / 2 + i * 2 * math.pi / n
        bx, by = cx + R * 1.52 * math.cos(a), cy + R * 1.08 * math.sin(a)
        bw, bh = 126, 40
        c.rect(bx - bw / 2, by - bh / 2, bw, bh, '#ffffff', pal['rule'], 4, 1)
        name = it if isinstance(it, str) else it.get('text', '')
        c.block(bx - bw / 2, by - bh / 2, bw, bh, name, 8.2, pal['ink'], weight='600')
        ex, ey = cx + R * 0.56 * math.cos(a), cy + R * 0.56 * math.sin(a)
        tx, ty = bx - (bw / 2 + 3) * math.cos(a), by - (bh / 2 + 3) * math.sin(a)
        c.line(ex, ey, tx, ty, pal['rule'], 1)
    if spec.get('note'):
        c.caption(spec['note'])
    return c


def draw_hero(spec: dict, pal: dict) -> Canvas:
    """장 시작 그래픽. 장 번호와 제목을 기하 구성 위에 앉힌다."""
    W = spec.get('width', 760)
    H = spec.get('height', 200)
    c = Canvas(W, H, pal)
    g = grad(c, 'hg', pal['accent'], pal['accent2'], 150)
    if pal['mono']:
        c.rect(0, 0, W, H, '#ffffff', pal['ink'], 0, 1.4)
    else:
        c.rect(0, 0, W, H, g, 'none', 0, 0)
    # 기하 문양 — 절제된 사선과 원호
    for i in range(6):
        x = W * 0.58 + i * 26
        c.add('<line x1="%g" y1="0" x2="%g" y2="%g" stroke="%s" stroke-width="1" '
              'opacity="0.35"/>' % (x, x - H * 0.5, H, '#ffffff' if not pal['mono'] else pal['rule']))
    c.add('<circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="1.2" '
          'opacity="0.4"/>' % (W * 0.82, H * 0.3, H * 0.42,
                               '#ffffff' if not pal['mono'] else pal['rule']))
    fg = pal['ink'] if pal['mono'] else '#ffffff'
    c.text(44, H * 0.42, spec.get('kicker', ''), 9.5, fg, 'start', '700')
    c.text(44, H * 0.68, spec.get('title', ''), 23, fg, 'start', '800')
    return c


DRAW = {
    'architecture': draw_architecture,
    'flow': draw_flow,
    'process': draw_process,
    'compare': draw_compare,
    'threat': draw_threat,
    'matrix': draw_matrix,
    'concept': draw_concept,
    'hero': draw_hero,
}

TYPE_NOTE = {
    'architecture': '계층·구역 구성. 무엇이 무엇 안에 있는지 보일 때',
    'flow': '데이터·통신 흐름. 무엇이 어디로 가는지 보일 때',
    'process': '절차 단계. 순서가 있는 일을 보일 때',
    'compare': '비교. 둘 이상을 같은 잣대로 놓을 때',
    'threat': '공격 경로와 대응 통제. 위협 시나리오에 쓴다',
    'matrix': '행렬. 등급·대응 관계처럼 교차표가 필요할 때',
    'concept': '개념도. 하나를 둘러싼 요소들을 보일 때',
    'hero': '장 시작 그래픽. 장 간지를 크게 쓸 때',
}


def build(spec: dict, pal: dict) -> str:
    kind = spec.get('type')
    if kind not in DRAW:
        raise SystemExit('모르는 꼴: %s  (쓸 수 있는 것: %s)'
                         % (kind, ', '.join(DRAW)))
    return DRAW[kind](spec, pal).render()


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('spec', nargs='?', help='명세 json (하나 또는 목록)')
    ap.add_argument('--out', default='figures')
    ap.add_argument('--theme', default='nis')
    ap.add_argument('--types', action='store_true')
    a = ap.parse_args(argv)

    if a.types or not a.spec:
        print('그릴 수 있는 꼴')
        for k, v in TYPE_NOTE.items():
            print('  %-13s %s' % (k, v))
        return 0 if a.types else 2

    pal = theme_palette(a.theme)
    data = json.load(io.open(a.spec, encoding='utf-8'))
    items = data['figures'] if isinstance(data, dict) and 'figures' in data else data
    if isinstance(items, dict):
        items = [items]
    os.makedirs(a.out, exist_ok=True)
    for s in items:
        # figplan.py 의 계획 파일은 명세를 `spec` 아래 둔다. 두 꼴을 다 받는다.
        if isinstance(s.get('spec'), dict):
            s = dict(s['spec'], file=s.get('file'), number=s.get('number'),
                     render=s.get('render'))
        if s.get('render') == 'image':
            print('건너뜀(이미지 생성 필요): %s' % s.get('file', s.get('number', '?')))
            continue
        name = s.get('file') or ('fig-%s.svg' % s.get('number', 'x'))
        p = os.path.join(a.out, name)
        io.open(p, 'w', encoding='utf-8', newline='\n').write(build(s, pal))
        print('%s  (%s)' % (p, s.get('type')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
