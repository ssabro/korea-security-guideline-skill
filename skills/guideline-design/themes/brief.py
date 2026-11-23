# -*- coding: utf-8 -*-
"""진한 표지형 — ｢국가·공공기관 AI보안 가이드북｣ 을 재서 만들었다.

발행본 24종 가운데 표지 색 면적이 100% 인 둘 중 하나다. 짙은 바탕을 종이
끝까지 깔고 제목을 위에 올린다. 본문은 밝게 두어 간지에서 한 번 쉬고
본문에서 읽는 리듬을 만든다.

**잰 값**

    색     #384087 남보라 · #78afd6 하늘 · #a7dce0 청록
    글꼴   KoPubWorldDotum PL / PB / PM

빨강(#ed1c24)이 14 쪽에서 나왔으나 쓰지 않았다. 재어 보니 머리글 장식과
경고 표시에만 쓰인 점색이라 주조색으로 삼으면 문서가 요란해진다.

표지 그림은 **제목에서 고른다**(`motif='subject'`). 로봇 가이드라인이면
로봇을, 선박 가이드라인이면 배를 그린다.
"""

THEME = dict(
    key='brief',
    label='진한 표지형',
    note='｢국가·공공기관 AI보안 가이드북｣ 계열. 짙은 전면 표지와 밝은 본문.',
    page=(188, 257),
    margin=(24, 23, 18, 20),
    body=10.2,
    ink='#1b1b22',
    accent='#384087',
    accent2='#2f9fb4',
    tint='#e9edf6',
    rule='#c6cde0',
    soft='#5f6678',
    badge='pill',
    chapter='page',
    cover='art',
    cover_art=True,
    motif='subject',
    quiet=0.46,
)

EXTRA_CSS = """
/* ── 표지 — 종이 끝까지 짙게 ─────────────────────────────
   그림은 인쇄 뒤에 깔리므로 바탕을 투명하게 둔다. */
.cover{background:none;position:relative;color:#fff}
.cover .cvtop{position:absolute;left:0;right:0;top:30mm;
 padding:0 20mm;text-align:center;z-index:2}
.cover .ckind{margin:0 0 7mm;color:#bcd6e6;
 font-size:8.6pt;font-weight:700;letter-spacing:.38em}
.cover .ctitle{margin:0;color:#fff;font-size:25pt;font-weight:800;
 line-height:1.32;letter-spacing:-.025em}
.cover .cvtop::after{content:"";display:block;width:34mm;height:.8mm;
 margin:9mm auto 0;background:var(--accent2)}
.cover .cvbot{position:absolute;left:0;right:0;bottom:15mm;
 padding:0 18mm;text-align:center;z-index:2}
.cover .cdate{margin:0 0 6mm;color:#dbe6f0;font-size:10.5pt;font-weight:600}
.cover .corg{margin:0;color:#fff;font-size:11.5pt;font-weight:700}
.cover .cver{margin:3mm 0 0;color:#aebfd2;font-size:7.6pt}

/* ── 장 간지 — 표지와 같은 결 ───────────────────────────── */
.chapter{display:flex;flex-direction:column;justify-content:center;
 height:{{coverp}}mm;border:0;margin:0;padding:0 14mm;
 background:none;color:#fff;text-align:left}
.chapter .chno{margin:0 0 5mm;color:var(--accent2);font-size:1.2em;
 font-weight:700;letter-spacing:.26em}
.chapter h1{margin:0;color:#fff;font-size:2.4em;font-weight:800;
 letter-spacing:-.03em;line-height:1.26}
.chapter .chsec{margin-top:12mm;max-width:112mm}
.chapter .chsec li{margin:0 0 3mm;font-size:.92em}
.chapter .chsec .sno{display:inline-block;min-width:13mm;text-align:center;
 background:var(--accent2);color:#06262d;border-radius:2.2mm;
 padding:.8mm 2mm;font-size:.84em;font-weight:700}
.chapter .chsec .stt{color:#fff;font-weight:600}
@media screen{
 .chapter{background:linear-gradient(158deg,#1d2358,var(--accent))}
}
@media print{
 .chapter{break-after:page}
}

/* ── 본문 ───────────────────────────────────────────────── */
h2{color:var(--accent);border-bottom:.5mm solid var(--accent2);
 padding-bottom:2.2mm}
h3{color:var(--accent)}
h4{color:#2f6f87}
.bdg{background:var(--accent);color:#fff;border-radius:2.4mm;
 padding:1mm 3mm;font-weight:700}

table{border-color:var(--rule)}
thead th{background:var(--accent);color:#fff;font-weight:700;
 border-color:var(--accent)}
tbody td{border-color:var(--rule)}
tbody tr:nth-child(2n) td{background:#f7f9fc}
.cid,.idc{color:var(--accent);font-weight:700}

/* `.law` 는 ｢법령｣ 을 감싸는 **인라인** 이름표다. 배경이나 테두리를
   주면 글 속에 색 덩어리가 줄줄이 생긴다. 색으로만 구분한다. */
.law{color:var(--accent)}
.note{color:var(--soft)}
.cap,.capt{color:var(--accent)}
.capn{color:var(--accent2);font-weight:700}

.colophon .colt-t{color:var(--accent)}
.colophon::before{background:var(--accent2)}
"""
