"""themegen.py — 기존 발행물을 재서 테마 뼈대를 만든다.

기관이 이미 펴낸 책을 건네면 거기서 판면·여백·본문 크기·색을 재서
`themes/<key>.py` 를 씁니다. 짐작이 아니라 **그 기관의 실제 판면**을 따라갑니다.

    python themegen.py 우리기관_가이드라인.pdf --key ourorg
    python themegen.py 책.pdf --key ourorg --label "우리 기관 표준" --force

재는 방법은 `references/publication-design.md` 와 같습니다 — 앞 12%(표지·목차)와
뒤 5%를 뺀 본문 구간에서, 글자 수가 긴 줄만 세어 본문 크기를 가늠하고, 여백은
글자가 실제로 놓인 영역의 바깥쪽 거리의 중앙값을 씁니다. 색은 면적이 넓고
무채색이 아닌 채움색을 면적으로 가중해 셉니다.

**뼈대일 뿐입니다.** 나온 값을 그대로 쓰지 말고 열어서 손보세요. 측정은 판면과
색을 짚어 주지만 배지 모양이나 표지 구성까지 알려 주지는 못합니다.

PyMuPDF 가 필요합니다.
"""

from __future__ import annotations

import argparse
import collections
import io
import os
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

PT = 25.4 / 72.0
HERE = os.path.dirname(os.path.abspath(__file__))


def chromatic(c) -> bool:
    r, g, b = c
    return max(c) - min(c) > 0.10 and max(c) > 0.12


def hexs(c) -> str:
    return '#%02x%02x%02x' % tuple(int(round(x * 255)) for x in c)


def lum(h: str) -> float:
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def mix(h: str, w: float) -> str:
    """흰색과 섞어 연한 색을 만든다. 측정에 연한 바탕이 안 잡힐 때 쓴다."""
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    f = lambda v: int(round(v + (255 - v) * w))
    return '#%02x%02x%02x' % (f(r), f(g), f(b))


def measure(path: str, sample: int = 26) -> dict:
    doc = fitz.open(path)
    n = doc.page_count
    lo = max(1, int(n * 0.12))
    hi = min(n - 1, max(lo + 1, int(n * 0.95)))
    sizes = collections.Counter()
    fonts = collections.Counter()
    colors = collections.Counter()
    seen = collections.defaultdict(set)   # 색이 나온 쪽. 주조색은 여러 쪽에 나온다
    headc = collections.Counter()         # 제목 글자 색
    headp = collections.defaultdict(set)
    L, R, T, B = [], [], [], []
    W = H = 0

    for i in range(lo, min(hi, lo + sample)):
        p = doc[i]
        W, H = p.rect.width, p.rect.height
        xs0, xs1, ys0, ys1 = [], [], [], []
        for b in p.get_text('dict')['blocks']:
            if b['type'] != 0:
                continue
            for l in b['lines']:
                txt = ''.join(s['text'] for s in l['spans']).strip()
                long = len(txt) >= 25
                for s in l['spans']:
                    if not s['text'].strip():
                        continue
                    if long:
                        sizes[round(s['size'], 1)] += len(s['text'])
                    fonts[s['font'].split('+')[-1]] += len(s['text'])
                    x0, y0, x1, y1 = s['bbox']
                    xs0.append(x0); xs1.append(x1); ys0.append(y0); ys1.append(y1)
        if xs0:
            L.append(min(xs0)); R.append(W - max(xs1))
            T.append(min(ys0)); B.append(H - max(ys1))
        for dr in p.get_drawings():
            c = dr.get('fill')
            if c and chromatic(c):
                a = abs(dr['rect'].width * dr['rect'].height)
                if a > 50:
                    k = hexs(c)
                    colors[k] += int(a)
                    seen[k].add(i)

    med = lambda v: sorted(v)[len(v) // 2] if v else 0
    body = sizes.most_common(1)[0][0] if sizes else 10.5

    # 제목 글자 색을 다시 돌며 센다. 본문 크기를 알아야 제목을 가릴 수 있다.
    for i in range(lo, min(hi, lo + sample)):
        for b in doc[i].get_text('dict')['blocks']:
            if b['type'] != 0:
                continue
            for l in b['lines']:
                for s in l['spans']:
                    txt = s['text'].strip()
                    if not txt or s['size'] < body * 1.08:
                        continue
                    v = s.get('color', 0)
                    rgb = ((v >> 16) & 255, (v >> 8) & 255, v & 255)
                    f = tuple(x / 255 for x in rgb)
                    # 거의 검정인 제목 색은 주조색이 아니다. 먹색으로 조판한
                    # 문서가 많아 그대로 두면 #0e172a 같은 값이 뽑힌다.
                    if not chromatic(f) or max(f) < 0.28:
                        continue
                    k = '#%02x%02x%02x' % rgb
                    headc[k] += len(txt)
                    headp[k].add(i)
    # 쪽 수를 먼저, 면적을 다음에 본다. 한두 쪽에 크게 깔린 포인트 색이
    # 주조색을 밀어내는 것을 막는다.
    cs = [c for c, _ in sorted(colors.items(),
                               key=lambda kv: (-len(seen[kv[0]]), -kv[1]))][:12]
    dark = [c for c in cs if lum(c) < 0.38]
    mid = [c for c in cs if 0.38 <= lum(c) < 0.70]
    pale = [c for c in cs if lum(c) >= 0.80]
    # 주조색 — 제목 글자 색을 먼저 본다. 없으면 도형 채움의 짙은 색으로 떨어진다.
    # 쪽 수를 먼저 보되, 쪽 수가 비슷하면 짙은 쪽을 고른다 — 제목은 짙게
    # 조판한다. 밝은 파랑이 짙은 남색을 밀어내는 것을 막는다.
    heads = sorted(headc.items(),
                   key=lambda kv: (-len(headp[kv[0]]), lum(kv[0]), -kv[1]))
    accent = heads[0][0] if heads else (dark[0] if dark else '#24408f')
    accent2 = mid[0] if mid else mix(accent, 0.35)
    if accent2 == accent:
        accent2 = mix(accent, 0.35)
    tint = pale[0] if pale else mix(accent, 0.88)
    return dict(
        file=os.path.basename(path), pages=n,
        page=(round(W * PT), round(H * PT)),
        margin=(round(med(L) * PT), round(med(R) * PT),
                round(med(T) * PT), round(med(B) * PT)),
        body=body,
        accent=accent, accent2=accent2, tint=tint,
        rule=mix(accent, 0.72), soft=mix(accent, 0.42),
        fonts=[f for f, _ in fonts.most_common(3)],
        colors=cs[:6],
        spread={c: len(seen[c]) for c in cs[:6]},
        heads=[(c, len(headp[c])) for c, _ in heads[:4]],
        sampled=min(hi, lo + sample) - lo,
    )


TPL = '''# -*- coding: utf-8 -*-
"""{label} — {src} 를 재서 만든 테마 뼈대.

`themegen.py` 가 잰 값입니다. **뼈대일 뿐이니 열어서 손보세요.** 측정은 판면과
색을 짚어 주지만 배지 모양이나 표지 구성까지 알려 주지는 못합니다.

측정 대상 : {src} ({pages}쪽 중 본문 {sampled}쪽)
주조색 후보 : {cands}
             아래 accent 가 마음에 들지 않으면 여기서 골라 한 줄만 바꾸세요.

측정한 색 : {colors}
             (괄호 안은 그 색이 나온 쪽 수 — 주조색은 여러 쪽에 되풀이됩니다)
쓰인 글꼴 : {fonts}
             (PDF 가 부분집합 글꼴을 쓰면 이름이 뭉개져 나옵니다. 본문은 고딕을
              쓰세요 — 발행본 20종 중 본문에 명조를 쓴 것은 없습니다.)

측정값이 아닌 것 — `rule` 과 `soft` 는 주조색을 흰색과 섞어 만들었고,
`badge` · `chapter` · `cover` 는 측정으로 알 수 없어 기본값을 두었습니다.
바꿀 때는 왜 그 값인지 여기에 적으세요.
"""

THEME = dict(
    key='{key}',
    label='{label}',
    note='{src} 를 재서 만든 테마. {w}x{h}mm, 본문 {body}pt.',

    # ── 측정값 ──
    page=({w}, {h}),              # mm
    margin=({ml}, {mr}, {mt}, {mb}),   # 좌 우 상 하 mm
    body={body},                      # pt
    accent='{accent}',            # 짙은 주조색
    accent2='{accent2}',          # 중간 보조색
    tint='{tint}',                # 연한 바탕

    # ── 주조색에서 만든 값 ──
    ink='#1a1a1a',
    rule='{rule}',
    soft='{soft}',

    # ── 측정으로 알 수 없어 기본값을 둔 것 ──
    badge='pill',                 # pill | tag | square
    chapter='page',               # page | inline
    cover='rule',                 # rule | band | side | tint
)

EXTRA_CSS = """
"""
'''


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source', help='기준으로 삼을 발행물 PDF')
    ap.add_argument('--key', required=True, help='테마 이름(영문·숫자)')
    ap.add_argument('--label', default=None, help='목록에 보일 이름')
    ap.add_argument('--out', default=None, help='쓸 파일. 기본 themes/<key>.py')
    ap.add_argument('--force', action='store_true', help='있는 파일을 덮어쓴다')
    ap.add_argument('--print', dest='show', action='store_true',
                    help='파일을 쓰지 않고 측정값만 보여 준다')
    a = ap.parse_args(argv)

    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    m = measure(a.source)
    w, h = m['page']
    ml, mr, mt, mb = m['margin']

    print('측정  %s  (%d쪽 중 본문 %d쪽)' % (m['file'], m['pages'], m['sampled']))
    print('  판면   %d x %d mm%s' % (w, h, '  ← A4' if abs(w - 210) < 3 else ''))
    print('  여백   좌 %d · 우 %d · 상 %d · 하 %d mm' % (ml, mr, mt, mb))
    print('  본문   %g pt' % m['body'])
    print('  색     %s / %s / %s' % (m['accent'], m['accent2'], m['tint']))
    print('  제목색 %s' % (' '.join('%s(%d쪽)' % (c, n) for c, n in m['heads'])
                           or '없음 — 도형 채움에서 가져왔습니다'))
    print('  채움색 %s' % ' '.join('%s(%d쪽)' % (c, m['spread'][c])
                                 for c in m['colors']))
    print('  글꼴   %s' % ', '.join(m['fonts']))
    if a.show:
        return 0

    out = a.out or os.path.join(HERE, 'themes', '%s.py' % a.key)
    if os.path.exists(out) and not a.force:
        print('\n이미 있는 파일입니다: %s\n--force 를 주면 덮어씁니다.' % out)
        return 2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    io.open(out, 'w', encoding='utf-8', newline='\n').write(TPL.format(
        key=a.key, label=a.label or ('%s 기준 테마' % a.key), src=m['file'],
        pages=m['pages'], sampled=m['sampled'],
        cands=' '.join('%s(%d쪽)' % (c, n) for c, n in
                       (m['heads'] + [(c, m['spread'][c]) for c in m['colors']])[:8]),
        colors=' '.join('%s(%d)' % (c, m['spread'][c]) for c in m['colors']),
        fonts=', '.join(m['fonts']),
        w=w, h=h, ml=ml, mr=mr, mt=mt, mb=mb, body=m['body'],
        accent=m['accent'], accent2=m['accent2'], tint=m['tint'],
        rule=m['rule'], soft=m['soft']))
    print('\n%s' % out)
    print('열어서 손보고  python render.py 원고.md --theme %s  로 써 보세요.' % a.key)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
