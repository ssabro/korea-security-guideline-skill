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
def theme_palette_from(t: dict) -> dict:
    """이미 읽어 둔 테마 사전에서 바로 팔레트를 만든다. render.py 가 쓴다."""
    mono = t.get('mark') == '■' or t.get('label', '').startswith('흑백')
    return dict(
        ink=t.get('ink', '#1a1a1a'), accent=t.get('accent', '#24408f'),
        accent2=t.get('accent2', '#006cb7'), tint=t.get('tint', '#e8eef7'),
        rule=t.get('rule', '#c9d3e2'), soft=t.get('soft', '#5b6670'),
        mono=mono, fill='#ffffff' if mono else t.get('tint', '#e8eef7'),
        stroke=t.get('ink', '#1a1a1a') if mono else t.get('rule', '#c9d3e2'),
        hot=t.get('ink', '#1a1a1a') if mono else '#c0392b')


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


# ── 표지 주제 ────────────────────────────────────────────────────────
# 제목에 나오는 낱말로 무엇을 그릴지 정한다. 앞에 오는 것이 먼저 걸린다.
SUBJECTS = [
    ('robot',  ('로봇', 'ROS', '자율주행', '무인이동체')),
    ('drone',  ('드론', '무인기', 'UAV', '비행')),
    ('ship',   ('선박', '해양', '항만', '자율운항')),
    ('power',  ('전력', '전력망', '송전', '스마트그리드', '에너지')),
    ('medical', ('의료', '병원', '환자', '보건')),
    ('ai',     ('AI', '인공지능', '생성형', '머신러닝', '학습모델')),
    ('cloud',  ('클라우드', 'SaaS', '가상화', '컨테이너')),
    ('chip',   ('암호', '양자', '반도체', '키관리', '인증서')),
    ('supply', ('공급망', 'SBOM', '소프트웨어자재', '조달')),
    ('net',    ('망', '네트워크', '통신', '분리')),
    ('data',   ('데이터', '정보', '로그', '개인정보')),
]


def subject_of(title: str) -> str:
    """제목에서 표지에 그릴 주제를 고른다. 못 고르면 'shield'."""
    s = re.sub(r'\s+', '', title or '')
    up = s.upper()
    for name, keys in SUBJECTS:
        for k in keys:
            if k.upper() in up:
                return name
    return 'shield'


def draw_subject(c, kind, cx, cy, s, ink, op, sw):
    """주제 모양을 (cx, cy) 를 가운데로 크기 `s` 만큼 그린다.

    선과 면으로만 그린다. 사진처럼 보이게 하지 않는다 — 지어낸 사진은
    문서가 말하지 않는 것을 말하게 된다.
    """
    import math as m

    def rect(x, y, w, h, r=0, fill='none', o=None):
        c.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" '
              'stroke="%s" stroke-width="%g" opacity="%g"/>'
              % (x, y, w, h, r, fill, 'none' if fill != 'none' else ink,
                 sw, op if o is None else o))

    def out(x, y, w, h, r=0, o=None):
        c.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="none" '
              'stroke="%s" stroke-width="%g" opacity="%g"/>'
              % (x, y, w, h, r, ink, sw, op if o is None else o))

    def dot(x, y, r, o=None):
        c.add('<circle cx="%g" cy="%g" r="%g" fill="%s" opacity="%g"/>'
              % (x, y, r, ink, op if o is None else o))

    def ring(x, y, r, o=None, w=None):
        c.add('<circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" '
              'stroke-width="%g" opacity="%g"/>'
              % (x, y, r, ink, w or sw, op if o is None else o))

    def ln(x1, y1, x2, y2, o=None, w=None):
        c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
              'stroke-width="%g" stroke-linecap="round" opacity="%g"/>'
              % (x1, y1, x2, y2, ink, w or sw, op if o is None else o))

    def path(d, o=None, w=None, fill='none'):
        c.add('<path d="%s" fill="%s" stroke="%s" stroke-width="%g" '
              'stroke-linecap="round" opacity="%g"/>'
              % (d, fill, ink, w or sw, op if o is None else o))

    if kind == 'robot':
        out(cx - s * .62, cy - s * .50, s * 1.24, s * .50, s * .10)
        out(cx - s * .28, cy - s * .76, s * .56, s * .26, s * .06)
        for g in (-1, 1):
            dot(cx + g * s * .13, cy - s * .63, s * .045)
        rect(cx - s * .14, cy - s * .91, s * .28, s * .15, s * .04, ink)
        for k in range(3):
            a = m.radians(208 + k * 22)
            ln(cx, cy - s * .88, cx + s * .86 * m.cos(a),
               cy - s * .88 + s * .86 * m.sin(a), op * .34, sw * .6)
        for g in (-1, 1):
            ring(cx + g * s * .36, cy + s * .12, s * .14)
        ln(cx - s * .36, cy + s * .12, cx + s * .36, cy + s * .12, op * .5, sw * .7)
    elif kind == 'drone':
        for gx in (-1, 1):
            for gy in (-1, 1):
                ring(cx + gx * s * .62, cy + gy * s * .34, s * .26, op * .8)
                ln(cx + gx * s * .20, cy + gy * s * .12,
                   cx + gx * s * .50, cy + gy * s * .28)
        out(cx - s * .24, cy - s * .16, s * .48, s * .32, s * .07)
        dot(cx, cy, s * .07)
    elif kind == 'ship':
        path('M %g %g L %g %g L %g %g L %g %g Z'
             % (cx - s * .70, cy + s * .10, cx + s * .70, cy + s * .10,
                cx + s * .48, cy + s * .46, cx - s * .48, cy + s * .46))
        out(cx - s * .34, cy - s * .22, s * .62, s * .32, s * .04)
        ln(cx + s * .44, cy + s * .10, cx + s * .44, cy - s * .62)
        for k in range(3):
            ln(cx - s * .72, cy + s * .62 + k * s * .14,
               cx + s * .72, cy + s * .62 + k * s * .14, op * .35, sw * .7)
    elif kind == 'power':
        path('M %g %g L %g %g L %g %g L %g %g L %g %g L %g %g Z'
             % (cx + s * .16, cy - s * .76, cx - s * .34, cy + s * .04,
                cx - s * .02, cy + s * .04, cx - s * .16, cy + s * .76,
                cx + s * .36, cy - s * .06, cx + s * .02, cy - s * .06))
        ring(cx, cy, s * .92, op * .30)
    elif kind == 'medical':
        ring(cx, cy, s * .72, op * .8)
        ln(cx - s * .34, cy, cx + s * .34, cy)
        ln(cx, cy - s * .34, cx, cy + s * .34)
    elif kind == 'ai':
        for k in range(3):
            for j in range(3):
                dot(cx + (j - 1) * s * .56, cy + (k - 1) * s * .46, s * .07,
                    op * (.6 + .14 * j))
        for k in range(3):
            for j in range(2):
                ln(cx + (j - 1) * s * .56, cy + (k - 1) * s * .46,
                   cx + j * s * .56, cy + ((k + 1) % 3 - 1) * s * .46,
                   op * .34, sw * .7)
    elif kind == 'cloud':
        path('M %g %g A %g %g 0 0 1 %g %g A %g %g 0 0 1 %g %g '
             'A %g %g 0 0 1 %g %g Z'
             % (cx - s * .62, cy + s * .22, s * .30, s * .30,
                cx - s * .30, cy - s * .10, s * .36, s * .36,
                cx + s * .34, cy - s * .12, s * .30, s * .30,
                cx + s * .62, cy + s * .22))
        ln(cx - s * .62, cy + s * .22, cx + s * .62, cy + s * .22)
    elif kind == 'chip':
        out(cx - s * .46, cy - s * .46, s * .92, s * .92, s * .08)
        out(cx - s * .20, cy - s * .20, s * .40, s * .40, s * .04, op * .7)
        for k in range(4):
            q = -s * .30 + k * s * .20
            ln(cx + q, cy - s * .46, cx + q, cy - s * .76, op * .7)
            ln(cx + q, cy + s * .46, cx + q, cy + s * .76, op * .7)
            ln(cx - s * .46, cy + q, cx - s * .76, cy + q, op * .7)
            ln(cx + s * .46, cy + q, cx + s * .76, cy + q, op * .7)
    elif kind == 'supply':
        for k in range(3):
            x = cx + (k - 1) * s * .62
            out(x - s * .22, cy - s * .22, s * .44, s * .44, s * .05)
            if k < 2:
                ln(x + s * .22, cy, x + s * .40, cy, op * .6)
        dot(cx, cy, s * .06)
    elif kind == 'net':
        pts = [(cx, cy - s * .70), (cx - s * .66, cy - s * .10),
               (cx + s * .66, cy - s * .10), (cx - s * .40, cy + s * .62),
               (cx + s * .40, cy + s * .62)]
        for i, p in enumerate(pts):
            for q in pts[i + 1:]:
                ln(p[0], p[1], q[0], q[1], op * .34, sw * .7)
        for p in pts:
            dot(p[0], p[1], s * .09)
    elif kind == 'data':
        for k in range(3):
            y = cy - s * .40 + k * s * .40
            c.add('<ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="none" '
                  'stroke="%s" stroke-width="%g" opacity="%g"/>'
                  % (cx, y, s * .56, s * .18, ink, sw, op * (1 - k * .18)))
        ln(cx - s * .56, cy - s * .40, cx - s * .56, cy + s * .40, op * .7)
        ln(cx + s * .56, cy - s * .40, cx + s * .56, cy + s * .40, op * .7)
    else:  # shield — 어느 가이드라인에나 맞는 바탕
        path('M %g %g L %g %g L %g %g Q %g %g %g %g Q %g %g %g %g Z'
             % (cx - s * .58, cy - s * .62, cx + s * .58, cy - s * .62,
                cx + s * .58, cy + s * .04, cx + s * .58, cy + s * .50,
                cx, cy + s * .74, cx - s * .58, cy + s * .50,
                cx - s * .58, cy + s * .04))
        rect(cx - s * .17, cy - s * .06, s * .34, s * .34, s * .05, ink)
        path('M %g %g A %g %g 0 0 1 %g %g'
             % (cx - s * .11, cy - s * .06, s * .11, s * .11,
                cx + s * .11, cy - s * .06), None, sw * 1.6)


def draw_cover(spec: dict, pal: dict) -> Canvas:
    """표지 아트워크. 판면을 꽉 채우는 기하 구성을 그린다.

    `motif` 로 꼴을 고른다.

      crystal  모난 다각형이 겹치는 결정 구조. 가장 무난하다
      network  점과 선으로 짠 망. 통신·연계를 다루는 문서에
      wave     동심원 호. 넓은 범위·전파를 다루는 문서에
      grid     아이소메트릭 격자. 체계·구조를 다루는 문서에
      pill     뒤표지용. 둥근 기둥에 보안 아이콘을 쌓는다. 제목은
               조판기가 옆에 둔다.
      subject  비스듬한 띠 위에 **제목에서 고른 주제 그림**과 노드 망,
               마디의 자물쇠. 로봇·선박·전력·의료·AI·클라우드·암호·
               공급망·망·데이터를 알아보고, 못 고르면 방패를 그린다.
               `robot`·`auto` 도 같은 무늬를 가리킨다.

    **글자가 앉을 자리(`quiet`)는 비워 둔다.** 작은 글자 뒤에 무늬가 깔리면
    읽히지 않는다. `quiet` 는 위에서부터의 비율이다(기본 0.62).
    """
    import math as _m
    W = spec.get('width', 760)
    H = spec.get('height', 1040)
    c = Canvas(W, H, pal)
    seed = sum(ord(x) for x in str(spec.get('seed', 'guideline')))
    motif = spec.get('motif', 'crystal')
    quiet = float(spec.get('quiet', 0.62))
    qy = H * quiet
    mono = pal['mono']

    # 바탕을 고른다. 발행본의 표지는 전면 색과 흰 바탕이 반반이다.
    #   gradient  주조색 그러데이션 위에 흰 무늬 (기본)
    #   white     흰 바탕에 주조색 무늬 — 글자를 검게 앉히는 표지에 쓴다
    white_bg = spec.get('bg') == 'white'
    base = grad(c, 'cvbg', pal['accent'], pal['accent2'], 155)
    if mono or white_bg:
        c.rect(0, 0, W, H, '#ffffff', 'none', 0, 0)
    else:
        c.rect(0, 0, W, H, base, 'none', 0, 0)

    if mono:
        line, soft = pal['ink'], 0.22
    elif white_bg:
        line, soft = pal['accent2'], 0.30
    else:
        line, soft = '#ffffff', 0.10

    def poly(pts, fill, op):
        c.add('<polygon points="%s" fill="%s" opacity="%g"/>'
              % (' '.join('%g,%g' % p for p in pts), fill, op))

    if motif == 'crystal':
        # 모난 다각형을 겹쳐 결정처럼 쌓는다. 아래쪽에 모은다.
        for i in range(7):
            k = (seed + i * 37) % 100 / 100.0
            cx = W * (0.18 + 0.68 * ((seed + i * 53) % 100) / 100.0)
            cy = qy + (H - qy) * (0.10 + 0.72 * k)
            r = W * (0.10 + 0.17 * ((seed + i * 71) % 100) / 100.0)
            pts = []
            for j in range(6):
                a = _m.radians(60 * j + (seed + i * 11) % 30)
                pts.append((cx + r * _m.cos(a), cy + r * _m.sin(a) * 0.86))
            poly(pts, line, soft + 0.06 * (i % 3))
    elif motif == 'network':
        pts = []
        for i in range(14):
            x = W * (0.08 + 0.84 * ((seed + i * 97) % 100) / 100.0)
            y = qy + (H - qy) * (0.06 + 0.84 * ((seed + i * 59) % 100) / 100.0)
            pts.append((x, y))
        for i, p in enumerate(pts):
            for q in pts[i + 1:]:
                d = _m.hypot(p[0] - q[0], p[1] - q[1])
                if d < W * 0.30:
                    c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
                          'stroke-width="0.8" opacity="%g"/>'
                          % (p[0], p[1], q[0], q[1], line, soft * 1.6))
        for p in pts:
            c.add('<circle cx="%g" cy="%g" r="3.4" fill="%s" opacity="%g"/>'
                  % (p[0], p[1], line, soft * 3.2))
    elif motif == 'wave':
        cx, cy = W * 0.78, qy + (H - qy) * 0.42
        for i in range(11):
            r = W * (0.08 + i * 0.058)
            c.add('<circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" '
                  'stroke-width="%g" opacity="%g"/>'
                  % (cx, cy, r, line, 1.4 if i % 3 == 0 else 0.7,
                     soft * (2.4 - i * 0.14)))
    elif motif in ('subject', 'robot', 'auto'):
        # ── 대각 띠 두 장 ──────────────────────────────
        # 흰 바탕이면 띠가 짙어야 하고, 색 바탕이면 띠가 밝아야 한다.
        dark = pal['accent'] if (white_bg or mono) else '#ffffff'
        lite = pal['accent2'] if (white_bg or mono) else '#ffffff'
        d_op = 1.0 if white_bg else 0.18
        l_op = 0.22 if white_bg else 0.12

        # 맨 아래는 비워 둔다. 날짜·기관·로고가 앉는 자리라 무늬가 깔리면
        # 글자가 읽히지 않는다. 원본도 아래 한 뼘은 희다.
        #
        # 발행 정보는 쪽 아래 25% 안에 들어온다(날짜·기관·버전·로고).
        # 띠가 기울어 있어 아래 모서리가 안쪽으로 들어오므로, 끝나는
        # 높이를 넉넉히 잡지 않으면 날짜와 닿는다.
        foot = H * 0.70
        A = foot - qy                    # 무늬가 쓸 수 있는 높이
        bx, bw2_, sk = W * 0.07, W * 0.26, W * 0.13
        poly([(bx, qy), (bx + bw2_, qy),
              (bx + bw2_ + sk, foot), (bx + sk, foot)], dark, d_op)
        poly([(W * -0.04, qy + A * 0.62), (W * 0.56, qy + A * 0.16),
              (W * 1.02, qy + A * 0.38), (W * 0.42, foot)],
             lite, l_op)

        ink = '#ffffff' if white_bg else pal['accent']
        iop = 0.95 if white_bg else 0.88
        sw = W * 0.0052

        # ── 주제 그림 ─────────────────────────────────
        # 무엇을 그릴지는 **제목에서 고른다**. 로봇 가이드라인에는 로봇을,
        # 선박 가이드라인에는 배를 그린다. 아무 무늬나 깔면 겉돈다.
        kind = spec.get('subject') or subject_of(str(spec.get('seed', '')))
        rf = 0.60                           # 띠를 따라 내려온 비율
        rx = bx + bw2_ * 0.5 + sk * rf
        ry = qy + A * rf
        draw_subject(c, kind, rx, ry, W * 0.088, ink, iop, sw)
        bw2 = W * 0.072

        # ── 노드 망 — 주제 그림에서 오른쪽 위로 뻗는다 ──────
        # 통신 구간을 점과 선으로 보이고, 마디 몇 곳에 자물쇠를 단다.
        net = pal['accent'] if (white_bg or mono) else '#ffffff'
        nop = 0.30 if white_bg else 0.30
        hub = (rx + bw2 * 1.5, ry - W * 0.046)
        nodes = [hub]
        for i in range(7):
            a = _m.radians(-78 + ((seed * 11 + i * 47) % 86) + i * 9)
            rr = W * (0.14 + 0.055 * ((seed + i * 37) % 100) / 100.0) * (1 + i * 0.22)
            nodes.append((hub[0] + rr * _m.cos(a) * 1.06,
                          hub[1] + rr * _m.sin(a) * 0.74))
        for i, p in enumerate(nodes):
            for q in nodes[i + 1:]:
                if _m.hypot(p[0] - q[0], p[1] - q[1]) < W * 0.30:
                    c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
                          'stroke-width="0.9" opacity="%g"/>'
                          % (p[0], p[1], q[0], q[1], net, nop * 0.62))
        # 마디 — 두 곳에 자물쇠를 달아 통신 구간을 지킨다는 뜻을 둔다
        for i, p in enumerate(nodes[1:], 1):
            if i % 3:
                c.add('<circle cx="%g" cy="%g" r="%g" fill="%s" '
                      'opacity="%g"/>' % (p[0], p[1], W * 0.0062, net, nop))
                continue
            s = W * 0.026
            c.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" '
                  'fill="none" stroke="%s" stroke-width="%g" opacity="%g"/>'
                  % (p[0] - s, p[1] - s, s * 2, s * 2, s * 0.28,
                     net, W * 0.0026, nop * 1.5))
            c.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" '
                  'fill="%s" opacity="%g"/>'
                  % (p[0] - s * 0.34, p[1] - s * 0.02, s * 0.68, s * 0.50,
                     s * 0.08, net, nop * 1.4))
            c.add('<path d="M %g %g A %g %g 0 0 1 %g %g" fill="none" '
                  'stroke="%s" stroke-width="%g" opacity="%g"/>'
                  % (p[0] - s * 0.20, p[1] - s * 0.02, s * 0.20, s * 0.20,
                     p[0] + s * 0.20, p[1] - s * 0.02,
                     net, W * 0.0026, nop * 1.4))
        c.add('<circle cx="%g" cy="%g" r="%g" fill="%s" opacity="%g"/>'
              % (hub[0], hub[1], W * 0.0085, ink, iop * 0.8))

    elif motif == 'pill':
        # ── 뒤표지 — 둥근 기둥에 쌓은 아이콘 ───────────
        # 쪽 가운데 왼쪽에 기둥을 세우고 옆에 제목을 둔다. 글자는 조판기가
        # 내므로 여기서는 기둥과 아이콘만 그린다.
        ink = pal['accent'] if (white_bg or mono) else '#ffffff'
        op = 0.95 if (white_bg or mono) else 0.9
        kind = spec.get('subject') or subject_of(str(spec.get('seed', '')))
        stack = [kind] + [k for k in ('net', 'chip', 'shield', 'cloud', 'data')
                          if k != kind][:4]

        px = W * 0.155                    # 기둥 가운데 x
        pw = W * 0.105                    # 기둥 너비
        n = len(stack)
        gap = W * 0.096                   # 아이콘 사이
        ph = gap * n + W * 0.030
        pyc = H * 0.50
        c.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" '
              'fill="none" stroke="%s" stroke-width="%g" opacity="%g"/>'
              % (px - pw / 2, pyc - ph / 2, pw, ph, pw / 2,
                 ink, W * 0.0030, op * 0.45))
        for i, k in enumerate(stack):
            iy = pyc - ph / 2 + W * 0.015 + gap * (i + 0.5)
            draw_subject(c, k, px, iy, W * 0.030, ink, op, W * 0.0028)

    else:  # grid
        step = W * 0.052
        for i in range(-6, 40):
            x = i * step
            c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
                  'stroke-width="0.7" opacity="%g"/>'
                  % (x, qy, x - (H - qy) * 0.58, H, line, soft * 1.3))
            c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
                  'stroke-width="0.7" opacity="%g"/>'
                  % (x, qy, x + (H - qy) * 0.58, H, line, soft * 0.9))

    # ── 주제 그림 ───────────────────────────────────────
    # `subject` 무늬는 제 자리에 이미 그렸다. 나머지 무늬는 바탕일 뿐이므로
    # 그 위에 **문서의 주제**를 하나 얹는다. 무늬는 테마마다 달라도 표지가
    # 무엇을 다루는 문서인지는 어느 테마에서나 보여야 한다.
    # `pill` 은 기둥 안에 이미 아이콘을 쌓았으므로 따로 얹지 않는다.
    if (motif not in ('subject', 'robot', 'auto', 'pill')
            and spec.get('subject', '') != 'none'):
        kind = spec.get('subject') or subject_of(str(spec.get('seed', '')))
        # 그림은 **글자 자리와 발행 정보 사이의 띠** 안에 들어가야 한다.
        # 위로는 `quiet` 아래, 아래로는 날짜·기관·로고 위다. 그 띠가 좁은
        # 테마(제목이 긴 타이포형 따위)에서는 그림을 줄여 맞춘다. 자리를
        # 고정하면 제목이나 날짜를 덮는다.
        gfoot = H * 0.74
        band = max(gfoot - qy, H * 0.05)
        gs = min(W * 0.098, max(W * 0.044, band * 0.30))
        gx, gy = W * 0.50, qy + band * 0.5
        gink = pal['accent'] if (mono or white_bg) else '#ffffff'
        c.add('<circle cx="%g" cy="%g" r="%g" fill="%s" opacity="%g"/>'
              % (gx, gy, gs * 1.52, gink, 0.07 if not white_bg else 0.05))
        draw_subject(c, kind, gx, gy, gs, gink,
                     0.80 if not white_bg else 0.86, max(gs * 0.052, 0.9))

    # 글자 자리와 무늬를 가르는 가는 선. 뒤표지에는 가를 글자가 없다.
    if motif != 'pill':
        c.add('<line x1="0" y1="%g" x2="%g" y2="%g" stroke="%s" '
              'stroke-width="1" opacity="%g"/>' % (qy, W, qy, line, soft * 2.2))
    return c


DRAW = {
    'cover': draw_cover,

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
    'cover': '표지 아트워크. 판면을 채우는 기하 구성. 글자 자리는 비워 둔다',
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
