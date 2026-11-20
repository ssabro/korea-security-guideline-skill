# -*- coding: utf-8 -*-
"""격식 있는 국가 간행물.

도서관 서가에 꽂힌 백서·연감의 격식을 따른다. 판면·여백·본문 크기·주조색은
발행본 20종 측정값(`references/publication-design.md`)에서 그대로 가져왔고,
격식은 색을 더 쓰는 대신 **괘선과 여백**으로 낸다 — 겹괘선(`double`) 테두리를
두른 표지, 쪽 전체를 쓰는 장 간지, 점선 이음줄 목차, 간기면 꼴의 판권지.

본문은 고딕이다. 측정 20종 중 본문에 명조를 쓴 것은 하나도 없다. 명조(`--serif`)는
표지·속표지·장 간지·판권지·목차 제목의 **큰 글자에만** 쓴다.
"""

THEME = dict(
    key='formal',
    label='국가 간행물형',
    note='백서·연감의 격식. 188×257mm, 본문 10.5pt. 짙은 남색 한 색에 황동 보조색, '
         '겹괘선 표지와 전면 장 간지, 점선 이음줄 목차, 간기면 판권지.',
    # 판면·여백·본문 크기는 측정 중앙값 그대로다(188×257mm · 25/24/19/16mm · 10.5pt).
    page=(188, 257), margin=(25, 24, 19, 16), body=10.5,
    # accent 는 측정 짙은 남색 그대로(#253c65). accent2 는 측정 보조색 주황
    # #fdb514 의 명도·채도를 내려 금속(황동) 느낌을 낸 값이다 — 측정값이 아니다.
    # tint·rule 은 측정 연한 하늘 #cedeee 를 바탕용으로 밝게, 괘선용으로 흐리게
    # 조정한 값이다 — 측정값이 아니다. ink 는 순검정보다 살짝 눌러 남색과
    # 부딪히지 않게 했다.
    ink='#15181d', accent='#253c65', accent2='#8a6a2f',
    tint='#e3e9f2', rule='#bfc8d6', soft='#5b6670',
    badge='square', chapter='page', cover='rule', mark='●',
)

EXTRA_CSS = """
/* ══ 토큰 ═══════════════════════════════════════════════════════════════ */
:root{
 /* 설치된 명조를 차례로 쓴다. 외부에서 받아오지 않는다. */
 --serif:'KoPubWorld바탕체','KoPubWorldBatang','나눔명조','NanumMyeongjo',
  '바탕','Batang','Noto Serif KR','AppleMyungjo',serif;
 --deep:#16213c;   /* accent 를 어둡게 내린 값. 표지 바탕 그라데이션에만 */
 --brass:#cdae72;  /* accent2 를 밝게 올린 값. 짙은 바탕 위 괘선·글자에만 */
 --gilt:#f0e2c4;   /* 같은 황동의 가장 밝은 단계. 짙은 바탕 위 작은 글자에만 */
 --zebra:#f5f7fa;  /* tint 를 밝게 내린 값. 통제항목표 교차 음영·예시 바탕 */
}
/* 색 바탕과 테두리가 인쇄에 남아야 한다. 도형은 ::before/::after 로 그린다. */
*,*::before,*::after{-webkit-print-color-adjust:exact;print-color-adjust:exact}

/* ══ 표지 ═══════════════════════════════════════════════════════════════
   짙은 남색 전면에 황동 겹괘선을 두 겹 두른다. 색을 종이 끝까지 보내는 것은
   기본 CSS 의 `@page cover{margin:0}` + `.cover{page:cover}` 가 한다 —
   음수 여백은 쓰지 않는다(글자가 잘린다). */
.cover.cv-rule{
 margin:0;border:0;padding:36mm 26mm 30mm;position:relative;overflow:hidden;
 justify-content:space-between;text-align:center;color:#fff;
 background:linear-gradient(168deg,#2a3f66 0%,var(--accent) 46%,var(--deep) 100%)}
/* 화면에서도 색이 쪽 가장자리에 닿게 한다. 인쇄는 위의 이름 붙은 페이지가
   맡으므로 음수 여백은 화면에만 준다 — 인쇄에 음수 여백을 주면 글자가 잘린다. */
@media screen{.cover.cv-rule{margin:-{{mt}}mm -{{mr}}mm 0 -{{ml}}mm;
 min-height:{{h}}mm}}
/* 바깥 얇은 테두리 */
.cover.cv-rule::before{content:"";position:absolute;inset:7mm;
 border:.75pt solid rgba(205,174,114,.5);pointer-events:none}
/* 안쪽 겹괘선 테두리 */
.cover.cv-rule::after{content:"";position:absolute;inset:10mm;
 border:2.25pt double var(--brass);pointer-events:none}

/* 문양 — 가로 괘선 가운데를 마름모로 끊는 고전 장치 */
.cover.cv-rule .cvtop{position:relative;padding-top:17mm}
.cover.cv-rule .cvtop::before{content:"";position:absolute;top:5mm;left:50%;
 width:48mm;margin-left:-24mm;border-top:.75pt solid rgba(205,174,114,.7)}
.cover.cv-rule .cvtop::after{content:"";position:absolute;top:3.4mm;left:50%;
 width:3.2mm;height:3.2mm;margin-left:-1.6mm;transform:rotate(45deg);
 border:.6mm solid var(--brass);background:#2a3f66}

/* 문서 종류 — 자간을 크게 벌리고 위아래를 겹괘선으로 막는다 */
.cover.cv-rule .ckind{color:var(--gilt);font-weight:700;font-size:.8em;
 letter-spacing:.45em;text-indent:.45em;margin:0 0 12mm;padding:3.6mm 0;
 border-top:2.25pt double rgba(205,174,114,.85);
 border-bottom:2.25pt double rgba(205,174,114,.85)}
.cover.cv-rule .ctitle{font-family:var(--serif);font-size:2.1em;font-weight:700;
 line-height:1.52;letter-spacing:-.01em;margin:0;
 text-shadow:0 0 .35mm rgba(0,0,0,.3)}

/* 발행 연월을 작은 틀에 담고, 기관명은 자간을 벌려 아래에 앉힌다 */
.cover.cv-rule .cvbot{margin:0;padding-top:4mm}
.cover.cv-rule .cdate{display:inline-block;margin:0 0 11mm;padding:2.5mm 8mm;
 border:.75pt solid rgba(205,174,114,.75);color:var(--gilt);font-size:.82em;
 letter-spacing:.26em;text-indent:.26em}
.cover.cv-rule .corg{font-family:var(--serif);font-size:1.3em;font-weight:700;
 letter-spacing:.5em;text-indent:.5em;margin:0;padding-top:5.5mm;
 border-top:.75pt solid rgba(255,255,255,.38)}
.cover.cv-rule .cver{color:var(--brass);font-size:.76em;letter-spacing:.1em;
 margin:4.5mm 0 0}

/* ══ 속표지 ═════════════════════════════════════════════════════════════ */
.halftitle{text-align:center}
.halftitle h1{font-family:var(--serif);font-size:1.85em;font-weight:700;
 line-height:1.56;letter-spacing:-.01em;color:var(--accent);padding:10mm 4mm;
 border-top:4.5pt double var(--accent);border-bottom:4.5pt double var(--accent)}

/* ══ 목차 ═══════════════════════════════════════════════════════════════ */
/* 제목은 명조 + 벌린 자간, 아래에 작은 CONTENTS. 측정 20종에서 흔한 꼴이다. */
.toch{display:block;text-align:center;font-family:var(--serif);font-size:1.75em;
 font-weight:700;color:var(--accent);letter-spacing:.5em;text-indent:.5em;
 margin:0 0 10mm;padding-bottom:4mm;border-bottom:4.5pt double var(--accent)}
.toch::after{content:"CONTENTS";display:block;font-family:var(--body);
 font-size:.29em;font-weight:700;letter-spacing:.42em;text-indent:.42em;
 color:var(--accent2);margin-top:4mm}

/* 점선 이음줄 — .tt 와 .tp 사이에 ::before 를 끼워 넣고 order 로 자리를 잡는다.
   베이스라인 정렬이라 글자 없는 칸의 아래 테두리가 글줄 기준선에 앉는다. */
.toc{display:flex;align-items:baseline;gap:0;margin:0 0 .55em;padding-left:8mm;
 font-size:.97em;color:var(--ink)}
.toc .tt{order:0;flex:0 1 auto}
.toc::before{content:"";order:1;flex:1 1 6mm;min-width:4mm;height:.6em;
 margin:0 2mm;border-bottom:.75pt dotted var(--rule)}
.toc .tp{order:2;margin-left:0;padding:0;color:var(--accent);font-weight:700;
 font-variant-numeric:tabular-nums}
/* 쪽번호를 넣지 않은 원고에서는 이음줄만 남아 떠 보이므로 지운다 */
.toc:not(:has(.tp))::before{border-bottom:0}
/* 장·부록은 굵게 띄우고 실선으로 가른다. 이음줄은 두지 않는다. */
.toc.tc{padding-left:0;margin:6mm 0 2mm;padding-bottom:1.6mm;font-size:1.1em;
 font-weight:800;color:var(--accent);letter-spacing:.01em;
 border-bottom:.75pt solid var(--accent)}
.toc.tc::before{border-bottom:0}
.toc.tc .tt::before{content:"";display:inline-block;width:2.4mm;height:2.4mm;
 margin:0 3mm .5mm 0;background:var(--accent2);vertical-align:middle}
.toc.tc .tp{font-size:.88em}

/* ══ 장 간지 — 쪽 전체를 쓴다 ═══════════════════════════════════════════ */
/* 아래쪽을 비워 글 덩어리를 쪽 가운데보다 살짝 위에 앉힌다(시각적 중심) */
.chapter{position:relative;min-height:{{coverp}}mm;margin:0;border:0;
 padding:0 0 28mm;display:flex;flex-direction:column;align-items:center;
 justify-content:center;text-align:center}
/* 판면 가장자리를 두르는 얇은 테두리 */
.chapter::before{content:"";position:absolute;inset:0;
 border:.75pt solid var(--rule);pointer-events:none}
/* 위를 막는 남색 띠. 아래에 황동 줄을 한 겹 깐다. */
.chapter::after{content:"";position:absolute;top:0;left:0;right:0;height:11mm;
 background:var(--accent);border-bottom:.8mm solid var(--accent2)}
/* 장 번호 — 흰 글자를 남색 명패에 앉히고 황동 테를 두른다 */
.chno{position:relative;margin:0;padding:3.6mm 12mm;background:var(--accent);
 color:#fff;font-size:1.62em;font-weight:700;letter-spacing:.36em;
 text-indent:.36em;box-shadow:0 0 0 .4mm #fff,0 0 0 .95mm var(--accent2)}
.chapter h1{display:inline-block;max-width:86%;margin:17mm 0 0;padding:0 6mm 8mm;
 font-family:var(--serif);font-size:2.6em;font-weight:700;line-height:1.42;
 letter-spacing:-.015em;color:var(--accent);
 border-bottom:4.5pt double var(--accent2)}
/* 번호와 제목 사이의 마름모 */
.chapter h1::before{content:"";display:block;width:3.6mm;height:3.6mm;
 margin:0 auto 11mm;transform:rotate(45deg);border:.5mm solid var(--accent2)}

/* ══ 절·항·목 ══════════════════════════════════════════════════════════ */
h2{display:flex;align-items:baseline;gap:.62em;margin:2.1em 0 .95em;
 padding-bottom:.34em;font-size:1.2em;font-weight:800;color:var(--accent);
 border-bottom:2.25pt double var(--accent)}
/* 배지에 흰 테를 두고 그 밖에 황동 선을 둘러 금속 명패처럼 보이게 한다 */
h2 .bdg{background:var(--accent);color:#fff;border-radius:0;padding:.26em .7em;
 font-size:.66em;font-weight:700;letter-spacing:.14em;text-indent:.14em;
 box-shadow:0 0 0 .3mm #fff,0 0 0 .6mm var(--accent2)}
h2 .ht{flex:1 1 auto}
h3{font-size:1.06em;font-weight:700;color:var(--accent);margin:1.7em 0 .5em;
 padding:0 0 .26em .55em;border-left:1.2mm solid var(--accent2);
 border-bottom:.75pt solid var(--rule)}
h4{font-size:1em;font-weight:700;color:var(--accent2);margin:1.35em 0 .4em}
.num .n{color:var(--accent2)}
ul{padding-left:1.25em}
li::marker{color:var(--accent2)}

/* ══ 캡션·표·삽도 ═══════════════════════════════════════════════════════ */
.cap{align-items:baseline;gap:.55em;margin:1.7em 0 .5em;padding-top:.32em;
 font-size:.93em;border-top:2.25pt double var(--accent)}
.capn{background:var(--accent);color:#fff;border-radius:0;padding:.15em .62em;
 font-weight:700;font-size:.86em;letter-spacing:.06em}
.capt{color:var(--accent);font-weight:700}
table{font-size:.9em}
table.tbl,table.ctl{border:1.5pt solid var(--accent)}
th,td{border:.75pt solid var(--rule);padding:.46em .5em}
/* 머리는 남색 바탕에 흰 글자. 쪽을 넘기면 머리를 다시 얹는다. */
.tbl thead th,.ctl thead th{background:var(--accent);color:#fff;
 border-color:var(--accent);font-weight:700;letter-spacing:.02em}
thead{display:table-header-group}
.ctl tbody tr:nth-child(even){background:var(--zebra)}
.ctl tbody td.g,.ctl tbody td.idc{color:var(--accent);font-weight:700}
figure{margin:0 0 1.2em;padding:3mm;border:.75pt solid var(--rule)}

/* ══ 보충 ═══════════════════════════════════════════════════════════════ */
.implhead{color:var(--accent);background:var(--tint);font-weight:700;
 margin:1.6em 0 .55em;padding:.34em .8em .34em .7em;
 border-left:1.6mm solid var(--accent)}
.note{margin:.3em 0 1em;padding-left:1.1em;text-indent:-1.1em;color:var(--soft)}
pre{background:var(--zebra);border:.75pt solid var(--rule);
 border-left:1.6mm solid var(--accent2)}

/* ══ 판권지 — 간기면 ════════════════════════════════════════════════════ */
.colophon{position:relative;justify-content:flex-end;padding-bottom:13mm;
 text-align:center}
.colt{font-family:var(--serif);font-size:1.45em;font-weight:700;line-height:1.5;
 color:var(--accent);margin:0;padding:7mm 4mm 5.5mm;
 border-top:4.5pt double var(--accent);border-bottom:.75pt solid var(--accent)}
.colt-t{margin:0;font-size:.9em;text-align:left;
 border:.75pt solid var(--rule);border-top:0}
.colt-t th{width:33mm;background:var(--tint);color:var(--accent);font-weight:700;
 text-align:center;vertical-align:middle;padding:.52em 1em;
 border-bottom:.75pt solid #fff}
.colt-t td{padding:.52em 1em;border-bottom:.75pt solid var(--rule)}
/* 맨 아래 문양 — 괘선 가운데에 마름모 */
.colophon::before{content:"";position:absolute;bottom:6mm;left:50%;width:40mm;
 margin-left:-20mm;border-top:.75pt solid var(--rule)}
.colophon::after{content:"";position:absolute;bottom:4.4mm;left:50%;width:3.2mm;
 height:3.2mm;margin-left:-1.6mm;transform:rotate(45deg);
 border:.5mm solid var(--accent2);background:#fff}

/* ══ 인쇄 ═══════════════════════════════════════════════════════════════ */
@media print{
 /* 크롬이 잡는 종이 높이가 {{h}}mm 보다 0.2mm 남짓 크다. 그 남는 띠는 레이아웃
    상자 밖이라 어떤 테마도 칠하지 못하지만(모든 테마가 같다), 상자 끝줄까지는
    그림자로 메운다. 색은 바탕 그라데이션의 끝 색이라 이은 자리가 보이지 않는다. */
 .cover.cv-rule{box-shadow:0 0 0 1mm var(--deep)}
 /* 간지가 꼭 한 쪽을 차지하게 높이를 못 박는다 */
 .chapter{height:{{coverp}}mm;min-height:{{coverp}}mm;
  break-before:page;break-after:page}
 .toc{break-inside:avoid}
 .cap,.implhead{break-after:avoid}
 .colt{break-after:avoid}
}
"""
