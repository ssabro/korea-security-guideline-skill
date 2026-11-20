# -*- coding: utf-8 -*-
"""장별 색 구분과 측면 탭 — 책을 덮고 옆에서 봐도 장이 구분되는 판.

｢지능형 전력망 사이버보안 가이드라인｣ 계열이 쓰는 **사이드 탭**(쪽 바깥쪽에
장 이름을 세로로 적은 색 띠)을 중심에 둔다. 장마다 색을 달리하고 탭의 세로
위치를 한 칸씩 내려, 책배(책의 옆면)에 계단이 생기게 한다. 장 간지는 전면으로
쓰고, 통제항목 표의 등급 칸까지 그 장의 색을 따르게 해 쪽마다 지금 몇 장을
읽는지 색으로 알게 한다.

판면·여백·본문 크기는 측정값 그대로다(188×257mm, 25/24/19/16mm, 10.5pt —
`references/publication-design.md` 1·2·3절의 중앙값). 간지와 표지의 색면 치수
(150mm 색면, 24mm 탭, 40mm 탭 간격)는 측정값에 없는 값이므로 아래에 근거를
주석으로 적는다.

장 색을 어떻게 고르는가 — 조판기는 장 번호를 class 로 내주지 않는다. 그래서
`.chapter` 의 **형제 사슬**로 센다. `.chapter ~ table` 은 1장 이후의 모든 표,
`.chapter ~ .chapter ~ table` 은 2장 이후의 모든 표를 고른다. 뒤쪽 사슬이 class
선택자를 하나 더 가지므로 명시도가 높아 **뒤 장이 앞 장을 덮는다.** 결과적으로
각 장의 사이에 있는 요소만 그 장의 색을 받는다. 본문 요소가 모두 `.sheet` 안의
평평한 형제여서 가능한 방법이다.

할 수 없는 것 — 사이드 탭은 **장 간지 쪽에만** 선다. 조판기가 장의 본문을 하나로
묶어 주지 않아 어느 쪽이 몇 장인지 CSS 가 알 수 없고, 쪽마다 반복되는 요소를 놓을
자리도 없다(`position:fixed` 는 Chrome 인쇄에서 모든 쪽에 똑같이 찍혀 장을 구분하지
못한다). 그래서 쪽마다 따라오는 것은 **장 색**이다 — 절 배지, 절 제목 밑줄, 표 머리,
등급 칸, 캡션 띠가 모두 그 장의 색을 쓴다.
"""

# ── 판면 ──────────────────────────────────────────────────────────────────
W, H = 188, 257          # 측정 중앙값(188×257mm). 신국판에 가깝다
ML, MR, MT, MB = 25, 24, 19, 16   # 측정 중앙값. 좌우가 상하보다 넓다

# ── 장 색 여섯 — 한 계열 안에서 명도·채도만 달리한다 ──────────────────────
# 측정값의 주조색 구간(짙은 남색 #24408f·#003e7e → 중간 파랑 #006cb7)을 청록
# 쪽으로 늘려 여섯 칸으로 끊었다. 모두 파랑-청록 한 계열이라 함께 놓아도
# 산만하지 않고, 흰 글자를 얹을 수 있는 명도(대비 4.3:1 이상)로 맞췄다.
# 부록만 채도를 빼 회청색으로 두어 "장이 아님"을 알린다.
CH = ['#13325a',   # 1장 — 짙은 남색
      '#194b84',   # 2장
      '#0f618c',   # 3장
      '#0a7290',   # 4장
      '#0a7c7a',   # 5장 — 청록
      '#4f6373']   # 부록 — 채도를 뺀 회청


def mix(hexcolor: str, ratio: float) -> str:
    """색을 흰색과 섞는다. 표 머리·등급 칸의 연한 바탕을 장 색에서 만든다."""
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    f = lambda v: int(round(v + (255 - v) * ratio))
    return '#%02x%02x%02x' % (f(r), f(g), f(b))


THEME = dict(
    key='tab',
    label='장별 색 구분·측면 탭형',
    note='｢지능형 전력망｣ 계열의 사이드 탭을 살린 판. 188×257mm, 본문 10.5pt. '
         '장마다 색이 바뀌고 탭이 한 칸씩 내려가 책배에 계단이 생긴다. '
         '장 간지는 전면 색면.',
    page=(W, H), margin=(ML, MR, MT, MB), body=10.5,
    ink='#16202b', accent=CH[0], accent2=CH[2], tint=mix(CH[0], 0.90),
    rule='#c6d0dd', soft='#5b6670',
    badge='tag', chapter='page', cover='band', mark='●',
)

# ── 간지·표지 치수 (측정값에 없는 값 — 근거를 적는다) ─────────────────────
FIELD_W, FIELD_H = 150, 168   # 색면. 폭은 판면의 80%로, 오른쪽에 탭이 들어설
                              # 38mm 폭의 흰 띠를 남긴다. 높이는 판면의 65%로
                              # 제목을 눈높이보다 위에 둔다
TAB_W, TAB_H = 24, 32         # 탭 한 칸. 세로로 '제4장' 네 글자가 8.5pt로 들어가는
                              # 최소 크기(글자 3mm × 4 + 여유)에서 올렸다
TAB_TOP, TAB_STEP = 8, 40     # 첫 탭의 위치와 장마다 내려가는 간격.
                              # 6칸 × 40mm = 240mm 로 판면 높이 257mm 안에 들어간다
RAIL_W = 9                    # 흐린 탭 자리의 폭. 이번 장의 탭(24mm)보다 좁게 두어
                              # 지금 몇 번째 장인지가 폭으로도 읽히게 한다
TICK_PAD, TICK_H = 6, 20      # 흐린 탭 자리는 탭 칸(32mm) 안에 20mm 로 넣어 위아래를
                              # 6mm 씩 띄운다. 탭과 자리의 모서리가 겹치면 인쇄에서
                              # 1px 밝은 선이 생긴다 — 실제로 나와서 고쳤다
RAIL_H = TAB_STEP * 5 + TICK_PAD + TICK_H


def chain(n: int) -> str:
    """n번째 장을 고르는 형제 사슬. 뒤 장이 명시도로 앞 장을 덮는다."""
    return ' ~ '.join(['.chapter'] * n)


def rules() -> str:
    out = []
    for i, c in enumerate(CH):
        n = i + 1
        pre = chain(n)            # 이 장의 간지
        sib = pre + ' ~ '         # 이 장 뒤에 오는 본문 요소
        t12 = mix(c, 0.88)        # 표 머리 바탕
        t18 = mix(c, 0.82)        # 등급 칸 바탕
        t82 = mix(c, 0.89)        # 간지의 흐린 탭 자리 — 이번 장의 탭이 묻히지
                                  # 않도록 아주 연하게 둔다
        top = TAB_TOP + i * TAB_STEP
        out.append("""
/* ── %(n)s번째 장 — %(c)s ────────────────────────────────── */
%(pre)s{background-image:linear-gradient(%(c)s,%(c)s)}
%(pre)s .chno{top:%(top)smm;background:%(c)s}
%(pre)s::before{top:%(top)smm;background:%(c)s}
%(pre)s::after{background-image:repeating-linear-gradient(180deg,
 transparent 0 %(tpad)smm,%(t82)s %(tpad)smm %(tend)smm,
 transparent %(tend)smm %(step)smm)}
%(sib)sh2{border-bottom-color:%(c)s}
%(sib)sh2 .bdg{background:%(c)s}
%(sib)sh2.apx .bdg{background:%(c)s}
%(sib)sh3{border-left-color:%(c)s}
%(sib)sh4{color:%(c)s}
%(sib)s.num .n{color:%(c)s}
%(sib)s.implhead{color:%(c)s}
%(sib)s.implhead:before{background:%(c)s}
%(sib)spre{border-left-color:%(c)s}
%(sib)s.capn{background:%(t18)s;color:%(c)s}
%(sib)stable th{background:%(t12)s}
%(sib)stable.ctl th.g{background:%(c)s;color:#fff;border-color:%(c)s}
%(sib)stable.ctl td.g{background:%(t18)s;color:%(c)s}
%(sib)stable.ctl td.idc{color:%(c)s}
%(sib)s.cap{border-left-color:%(c)s}
""" % dict(n=n, c=c, pre=pre, sib=sib, t12=t12, t18=t18, t82=t82,
           top=top, tabh=TAB_H, step=TAB_STEP,
           tpad=TICK_PAD, tend=TICK_PAD + TICK_H))

    # 목차의 장 줄 — 같은 사슬 수법을 `.tc` 로 쓴다. 장 색을 왼쪽 탭으로 보여
    # 주어 목차 자체가 색인 범례가 된다.
    for i, c in enumerate(CH):
        sel = ' ~ '.join(['.tc'] * (i + 1))
        out.append('.tocpage %s{--tc:%s}\n' % (sel, c))
    return ''.join(out)


# ── 여섯 색 탭을 한 상자에 그리는 그라디언트 (표지의 색인 범례) ───────────
def cover_rail() -> str:
    stops = []
    for i, c in enumerate(CH):
        a = i * TAB_STEP
        stops.append('%s %smm %smm' % (c, a, a + TAB_H))
        stops.append('transparent %smm %smm' % (a + TAB_H, a + TAB_STEP))
    return 'linear-gradient(180deg,' + ','.join(stops) + ')'


EXTRA_CSS = ("""
/* ═══ 장별 색 구분과 측면 탭 ═══════════════════════════════════════════════
   색 바탕은 모두 print-color-adjust:exact 를 받는다. 없으면 인쇄에서 사라진다. */
*{-webkit-print-color-adjust:exact;print-color-adjust:exact}

/* ── 전면 장 간지 ────────────────────────────────────────────────────────
   이름 붙은 페이지로 여백을 0 으로 만들어 종이 끝까지 색을 보낸다.
   음수 여백을 쓰지 않는다(인쇄 영역 밖은 잘린다). */
@page chap{size:{{w}}mm {{h}}mm;margin:0}
.chapter{page:chap;position:relative;display:block;margin:0;padding:0;
 border:0;height:{{h}}mm;overflow:hidden;
 background-color:#fff;background-repeat:no-repeat;background-position:left top;
 background-size:FIELDWmm FIELDHmm;break-after:page}

/* 장 이름 자리 — 조판기가 내는 `.chno`('제4장')를 그대로 세로 탭으로 쓴다.
   글자를 새로 만들지 않으므로 원고의 장 번호와 어긋날 일이 없다. */
.chapter .chno{position:absolute;right:0;z-index:2;width:TABWmm;height:TABHmm;margin:0;
 display:flex;align-items:center;justify-content:center;
 writing-mode:vertical-rl;text-orientation:upright;
 color:#fff;font-weight:700;font-size:8.5pt;letter-spacing:.14em}

/* 부록 간지에는 `.chno` 가 없다. 탭을 ::before 로 세운다. */
.chapter::before{content:"";position:absolute;right:0;z-index:2;
 width:TABWmm;height:TABHmm;display:none}
.chapter:not(:has(.chno))::before{display:flex;align-items:center;
 justify-content:center;content:"부록";writing-mode:vertical-rl;
 text-orientation:upright;color:#fff;font-weight:700;font-size:8.5pt;
 letter-spacing:.14em}

/* 탭 자리 여섯을 흐리게 깔아 이 장이 몇 번째인지 보이게 한다 */
.chapter::after{content:"";position:absolute;right:0;top:TABTOPmm;z-index:1;
 width:RAILWmm;height:RAILHmm;background-repeat:no-repeat}

.chapter h1{position:absolute;left:{{ml}}mm;right:54mm;bottom:BOTTOMmm;
 color:#fff;font-size:2.35em;font-weight:800;line-height:1.3;letter-spacing:-.035em}
.chapter h1:before{content:"";position:absolute;left:0;top:-14mm;
 width:26mm;height:1.2mm;background:#fff;opacity:.75}

/* ── 표지 — 간지와 같은 색면 치수에, 오른쪽에는 여섯 장 색을 범례로 세운다 ── */
.cover.cv-band{display:block;position:relative;margin:0;padding:0;
 height:{{h}}mm;text-align:left;background-color:#fff;
 background-image:linear-gradient(CH0,CH0);background-repeat:no-repeat;
 background-position:left top;background-size:FIELDWmm FIELDHmm}
.cv-band::after{content:"";position:absolute;right:0;top:TABTOPmm;
 width:TABWmm;height:RAILHmm;background-image:COVERRAIL;background-repeat:no-repeat}
.cv-band .cvtop{position:absolute;left:{{ml}}mm;right:54mm;bottom:BOTTOMmm;
 width:auto;background:none;color:#fff;padding:0;margin:0}
.cv-band .ckind{color:#fff;opacity:.85;letter-spacing:.3em;font-size:.8em;
 margin:0 0 1.1em}
.cv-band .ctitle{font-size:2.1em;line-height:1.32;letter-spacing:-.035em}
.cv-band .cvbot{position:absolute;left:{{ml}}mm;right:54mm;bottom:24mm;
 width:auto;padding:0;margin:0}
.cv-band .cdate{font-size:.98em;color:var(--soft);margin:0 0 .45em}
.cv-band .corg{font-size:1.1em;font-weight:800;color:var(--ink);margin:0}
.cv-band .cver{font-size:.82em;color:var(--soft);margin:.5em 0 0}

/* ── 속표지·판권지 ──────────────────────────────────────────────────────── */
.halftitle h1{padding-top:1.2em;border-top:1.2mm solid var(--accent)}

/* ── 목차 — 장 줄이 색인 범례가 된다 ───────────────────────────────────── */
.toch{letter-spacing:-.02em}
.toch:after{content:"CONTENTS";display:block;margin-top:.35em;
 font-size:.42em;letter-spacing:.34em;color:var(--soft);font-weight:700}
.tocpage .toc.tc{--tc:var(--accent);position:relative;padding-left:9mm;
 border-bottom:0;margin-top:1.15em;padding-bottom:.3em;
 box-shadow:inset 0 -.6mm 0 0 var(--tc)}
.tocpage .toc.tc:before{content:"";position:absolute;left:0;top:.28em;
 width:6mm;height:2.6mm;background:var(--tc)}
.tocpage .toc.tc .tp{color:var(--tc);font-weight:700}
.tocpage .toc:not(.tc){padding-left:9mm}

/* ── 본문 — 장 색이 쪽마다 따라온다 ────────────────────────────────────── */
h2{align-items:baseline;border-bottom:.6mm solid var(--rule);padding-bottom:.3em}
h2 .bdg{padding:.16em .62em;font-size:.68em;letter-spacing:.06em}
h3{border-left-width:4px;padding-left:.5em}
.implhead{position:relative;padding-left:4.2mm}
.implhead:before{content:"";position:absolute;left:0;top:.52em;
 width:2.6mm;height:2.6mm}
.cap{border-left:.9mm solid var(--accent);padding-left:2.2mm}
.capn{border-radius:2px}

/* 표 — 등급 칸(C·S·O)이 그 장의 색을 따른다.
   소항목 칸이 23mm 면 '참여자 인증서 발급 체계' 가 세 줄로 쪼개진다. 29mm 로
   넓히고 ID 칸을 22mm 로 줄여 본문 설명 칸의 폭을 지킨다. */
table{font-size:.9em}
th,td{padding:.46em .45em}
.ctl th:first-child,.ctl td:first-child{width:22mm}
.ctl th:nth-child(2),.ctl td:nth-child(2){width:29mm}
.ctl th{letter-spacing:-.02em}
.ctl th.g{font-weight:800}
.ctl td.g{text-align:center;font-weight:700}
.ctl td.idc{font-weight:700}

/* ── 인쇄 ───────────────────────────────────────────────────────────────── */
@media print{
 .chapter{height:{{h}}mm;min-height:{{h}}mm}
 .cover.cv-band{height:{{h}}mm;min-height:{{h}}mm}
 tr,figure,.cap,.implhead{break-inside:avoid}
 .cap,.implhead{break-after:avoid}
}

/* ── 화면 — 간지가 쪽 전체를 쓰는 모습을 미리 본다 ───────────────────────── */
@media screen{
 .chapter{margin:6mm -{{mr}}mm 6mm -{{ml}}mm;width:{{w}}mm}
 .cover.cv-band{margin:0 -{{mr}}mm 0 -{{ml}}mm;width:{{w}}mm}
}
"""
    .replace('FIELDW', str(FIELD_W)).replace('FIELDH', str(FIELD_H))
    .replace('TABWW', '').replace('TABW', str(TAB_W)).replace('TABH', str(TAB_H))
    .replace('TABTOP', str(TAB_TOP)).replace('RAILH', str(RAIL_H))
    .replace('RAILW', str(RAIL_W))
    .replace('BOTTOM', str(H - FIELD_H + 20))
    .replace('COVERRAIL', cover_rail()).replace('CH0', CH[0])
    + rules())
