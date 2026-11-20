# -*- coding: utf-8 -*-
"""타이포그래피 주도형 — 색과 장식을 걷어내고 크기·굵기·여백·괘선으로만 위계를 세운다.

## 수치 근거

- 판면 188×257mm — 측정 중앙값(references/publication-design.md 1절). 그대로 쓴다.
- 여백 좌 20 · 우 26 · 상 22 · 하 18mm
  측정 중앙값은 25·24·19·16 이다. 여기서 바꾼 이유는 둘이다.
  (1) **판면 안쪽에 방주칼럼 28mm 를 따로 둔다.** 본문은 좌 20mm + 28mm = 쪽
      왼쪽에서 48mm 지점에서 시작한다. 절 번호·표 번호·항 표지·구현 예시 표지가
      그 28mm 안에 들어간다. 좌우 여백을 중앙값대로 두고 방주칼럼까지 더하면 한
      줄이 너무 짧아지므로 좌 여백을 20mm 로 줄였다.
  (2) 오른쪽을 26mm 로 왼쪽보다 넓게 두어 **판면을 비대칭**으로 만든다. 펼침면
      기준으로 홀수 쪽 바깥쪽(오른쪽)이 넓다. Chrome 은 `@page :left/:right` 를
      무시해 짝수 쪽에서 좌우를 뒤집을 수 없으므로, 방주칼럼은 모든 쪽에서
      왼쪽에 고정된다. 뒤집기는 포기하고 한쪽으로 통일한 결과다.
  좌우 합 46mm(측정 49mm), 상하 합 40mm(측정 35mm). 여백 총량은 측정 범위와
  비슷하게 두고 배분만 바꾼 것이다.
- 본문 9.4pt
  측정값은 두 무리에 걸친다 — 표가 지면 대부분을 차지하는 문서 8.1~9.2pt, 본체
  가이드라인 10.3~11.6pt(2절). 이 원고는 통제항목 표가 지면을 많이 차지하므로
  앞 무리에 가깝지만, 화면 가독을 위해 9.4pt 로 조금 올렸다(`control` 테마가
  8.2→8.6 으로 올린 것과 같은 이유). 글줄 길이로 따지면 측정 문서들과 거의
  같다 — 측정 문서는 판면 139mm / 10.5pt 로 한 줄 약 37자, 이 테마는 본문칼럼
  114mm / 9.4pt 로 약 34자다.
- 색 먹색 하나 + 주조색 하나
  주조색 `#003e7e` 는 측정된 짙은 남색(5절) 중 하나를 그대로 썼다. 보조색과
  연한 하늘색은 쓰지 않는다. 회색 괘선은 무채색이라 색으로 세지 않는다. 바탕을
  색으로 채우는 곳은 **표지 맨 위 띠 하나와 코드 블록**뿐이다.

## 설계 의도

표 머리 바탕색·알약 배지·캡션 배지를 모두 걷어냈다. 그 자리를 괘선의 굵기가
대신한다 — 장 2.2mm, 표 상하 0.55mm, 절 0.45mm, 표 머리 아래 0.3mm, 행 사이
0.12mm. 네 단계 굵기가 네 단계 위계다.

표는 세로 괘선을 전부 걷고 가로선만 남겼다. 다만 등급 칸(C·S·O)은 ● 하나가
어느 칸인지 가로선만으로는 읽히지 않아, **설명 칸과 등급 칸 사이에만 세로
머리카락선 하나**를 남겼다. 등급 칸 머리글은 가운데 맞춤이고 폭을 넉넉히 줬다.

캡션은 배지를 쓰지 않는다. 측정 문서에서는 배지형이 많았고(7절), 맨 글씨 캡션은
"발행본처럼 보이지 않는 짓"에 올라 있다(8절). 그래서 맨 글씨로 두는 대신 번호를
**방주칼럼에 따로 앉혀** 표의 왼쪽 끝선에 맞췄다. 번호는 주조색 굵은 글씨로
자리값이 분명하다.
"""

THEME = dict(
    key='typo',
    label='타이포그래피 주도형',
    note='색과 장식 대신 크기·굵기·여백·괘선으로 위계를 세운다. 188×257mm, 본문 9.4pt, '
         '먹색과 남색 둘만 쓴다. 판면 안쪽 왼쪽에 방주칼럼 28mm 를 두고 절 번호·표 '
         '번호를 거기 앉힌다. 표는 가로 괘선만 남긴다.',
    page=(188, 257),
    margin=(20, 26, 22, 18),
    body=9.4,
    ink='#121417',
    accent='#003e7e',
    accent2='#003e7e',   # 보조색을 쓰지 않는다. 기본 CSS 가 쓰는 자리는 모두 덮는다
    tint='#f1f1ee',      # 무채색. 코드 블록 바탕에만 쓴다
    rule='#c6c6c0',
    soft='#6e6e6a',
    badge='square',
    chapter='page',
    cover='rule',
    mark='●',
)

EXTRA_CSS = """
/* ── 격자 ─────────────────────────────────────────────────────────────────
   판면 안쪽을 두 칼럼으로 나눈다. --gut 은 방주칼럼, 그 오른쪽이 본문칼럼이다.
   음수 여백으로 인쇄 영역을 넘지 않는다. 방주칼럼은 판면 안에 있으므로 거기
   놓인 글자는 잘리지 않는다. */
:root{--gut:28mm;--hair:.12mm;--thin:.3mm;--med:.45mm;--thick:.55mm}

body{line-height:1.76;letter-spacing:-.005em}

/* 본문 흐름은 본문칼럼에서 시작한다. 표·삽도·장·절·캡션은 판면 전체를 쓴다.
   `.sheet` 의 직계 자식만 밀어, 표지·목차·판권지 안쪽 글은 건드리지 않는다. */
.sheet>p,.sheet>ul,.sheet>h3,.sheet>h4{margin-left:var(--gut)}
.sheet>ul ul{margin-left:0}
p{margin:0 0 .85em}

/* 글머리는 점 대신 짧은 줄표를 방주 쪽으로 반 칸 내민다 */
.sheet>ul{list-style:none;padding-left:4.6mm}
.sheet>ul>li{margin:.3em 0}
.sheet>ul>li:before{content:"—";display:inline-block;width:4.6mm;
 margin-left:-4.6mm;color:var(--accent);font-weight:700}
.sheet>ul ul{padding-left:4.6mm;margin-top:.3em}

.sheet>.num{margin-left:var(--gut);padding-left:1.7em;text-indent:-1.7em}
.num .n{width:1.7em;font-weight:800}

/* ── 장 ───────────────────────────────────────────────────────────────────
   가장 굵은 괘선 하나 + 가장 큰 글자. 장 번호는 방주칼럼에 앉힌다. */
.chapter{display:grid;grid-template-columns:var(--gut) 1fr;
 margin:0 0 14mm;padding:9mm 0 0;border-top:2.2mm solid var(--accent);
 border-bottom:0}
.chno{margin:0;padding-top:4.2mm;color:var(--accent);font-size:1.5em;
 font-weight:800;letter-spacing:-.01em}
.chapter h1{font-size:3em;font-weight:800;line-height:1.14;letter-spacing:-.045em}

/* ── 절 ───────────────────────────────────────────────────────────────────
   배지를 걷고 번호를 방주칼럼에 세운다. 본문의 1.95배. */
h2:has(.bdg){display:grid;grid-template-columns:var(--gut) 1fr;align-items:start;
 gap:0;margin:15mm 0 5.5mm;padding-top:3.2mm;border-top:var(--med) solid var(--ink)}
h2 .bdg{background:none;color:var(--accent);border-radius:0;padding:0;
 font-size:.95em;font-weight:800;letter-spacing:.02em;line-height:1.5;
 padding-top:.95em}
h2 .ht{font-size:1.95em;font-weight:800;line-height:1.24;letter-spacing:-.04em}
h2.apx{break-before:page}

/* 앞붙이 제목(발간 정보·목차)은 번호가 없다. 격자 대신 전폭으로 두고 굵은 밑줄 */
.docinfo>h2,.tocpage>h2{display:block;font-size:2.4em;font-weight:800;
 letter-spacing:-.045em;margin:0 0 7mm;padding-bottom:3.5mm;
 border-bottom:var(--thick) solid var(--ink)}

/* ── 항·목 ──────────────────────────────────────────────────────────────
   색 막대를 걷고, 방주칼럼에 짧은 굵은 줄 하나를 둔다. */
.sheet>h3{position:relative;font-size:1.14em;font-weight:800;letter-spacing:-.02em;
 margin:11mm 0 3mm var(--gut);padding-left:0;border-left:0}
.sheet>h3:before{content:"";position:absolute;left:calc(-1 * var(--gut));top:.72em;
 width:14mm;height:.7mm;background:var(--ink);print-color-adjust:exact;
 -webkit-print-color-adjust:exact}
.sheet>h4{font-size:1em;font-weight:800;color:var(--ink);letter-spacing:.01em;
 margin:7mm 0 2mm var(--gut)}

/* ── 캡션 ─────────────────────────────────────────────────────────────────
   배지 대신 번호를 방주칼럼에 앉혀 표·삽도의 왼쪽 끝선에 맞춘다. */
.sheet>.cap{display:grid;grid-template-columns:var(--gut) 1fr;gap:0;
 margin:10mm 0 2.5mm;margin-left:0;align-items:baseline;font-size:.95em}
.capn{background:none;color:var(--accent);border-radius:0;padding:0;
 font-weight:800;font-size:1em;letter-spacing:.01em}
.capt{font-weight:800;letter-spacing:-.015em}

/* ── 표 ───────────────────────────────────────────────────────────────────
   세로 괘선을 전부 걷고 가로선만 남긴다. 머리 바탕색도 쓰지 않는다. */
table{width:100%;margin:0 0 9mm;font-size:.92em;line-height:1.56}
table.tbl,table.ctl{border-top:var(--thick) solid var(--ink);
 border-bottom:var(--thick) solid var(--ink)}
th,td{border:0;padding:.52em .9em .52em 0;vertical-align:top}
th:last-child,td:last-child{padding-right:0}
/* 머리글에 위 굵은 선을 직접 준다. 표가 쪽을 넘어가면 다음 쪽 머리글에도
   같은 선이 다시 그려진다 — table 의 border-top 은 첫 쪽에만 그려진다. */
thead th{background:none;font-weight:800;letter-spacing:.01em;
 border-top:var(--thick) solid var(--ink);
 border-bottom:var(--thin) solid var(--ink);padding-top:.5em;padding-bottom:.5em}
tbody tr+tr th,tbody tr+tr td{border-top:var(--hair) solid var(--rule)}
.tbl th{background:none}
/* 판권지는 괘선 없이 조용히 둔다 */
.colt-t tr+tr th,.colt-t tr+tr td{border-top:0}

/* 등급 칸 — 가로선만으로는 ● 가 어느 칸인지 읽히지 않는다. 설명 칸과 등급 칸
   사이에만 세로 머리카락선 하나를 남긴다. */
.ctl th:first-child,.ctl td:first-child{width:22mm}
.ctl th:nth-child(2),.ctl td:nth-child(2){width:25mm}
.ctl th.g,.ctl td.g{width:8mm;text-align:center;padding-left:0;padding-right:0}
.ctl th:not(.g)+th.g,.ctl td:not(.g)+td.g{border-left:var(--hair) solid var(--rule);
 padding-left:2mm}
.ctl td.g{color:var(--accent);font-size:.9em}
.ctl td.idc{font-size:.92em}

/* 발간 정보·판권지의 두 칸 표 */
.docinfo .tbl th:first-child,.docinfo .tbl td:first-child{width:34mm}
.docinfo .tbl th{color:var(--soft);font-weight:700}
.colt-t th{color:var(--soft);width:30mm}

/* ── 보충 ─────────────────────────────────────────────────────────────── */
.sheet>.implhead{display:grid;grid-template-columns:var(--gut) 1fr;gap:0;
 margin-left:0;margin:12mm 0 3mm;color:var(--ink);font-weight:800;
 font-size:1em;letter-spacing:.02em;align-items:baseline}
.sheet>.implhead:before{content:"■";color:var(--accent);font-size:.62em}
.sheet>.note{margin-left:var(--gut);font-size:.9em;color:var(--soft);
 padding-left:1.3em;text-indent:-1.3em;margin-bottom:.6em}
pre{background:var(--tint);border-left:var(--med) solid var(--ink);
 margin-left:var(--gut);padding:.9em 1.1em;font-size:.88em;
 print-color-adjust:exact;-webkit-print-color-adjust:exact}
code{letter-spacing:0}
.implhead+p,.implhead+ul{margin-top:0}

/* ── 삽도 ───────────────────────────────────────────────────────────────── */
figure{margin:0 0 9mm;padding-top:2.5mm;border-top:var(--hair) solid var(--rule)}

/* ── 표지 ─────────────────────────────────────────────────────────────────
   색면은 맨 위 띠 하나뿐이다. 제목은 본문칼럼 왼쪽 끝선에 맞춰 왼쪽으로 몰고,
   28mm 굵은 줄 하나가 방주칼럼의 폭을 미리 보여 준다. */
.cover.cv-rule{margin:0;padding:0;border:0;
 border-top:3.2mm solid var(--accent);text-align:left;
 display:flex;flex-direction:column;justify-content:space-between}
.cv-rule .cvtop{width:auto;border:0;padding:96mm 26mm 0 20mm;margin:0}
.cv-rule .cvtop:before{content:"";display:block;width:var(--gut);height:1.6mm;
 background:var(--accent);margin:0 0 5.5mm;
 print-color-adjust:exact;-webkit-print-color-adjust:exact}
.cv-rule .ckind{color:var(--ink);font-size:.86em;font-weight:700;
 letter-spacing:.26em;margin:0 0 9mm}
.cv-rule .ctitle{font-size:3.3em;font-weight:800;line-height:1.16;
 letter-spacing:-.05em;margin:0}
.cv-rule .cvbot{width:auto;margin:0 26mm 0 20mm;padding:5mm 0 20mm;
 border-top:var(--thin) solid var(--ink)}
.cv-rule .cdate{font-size:1em;color:var(--ink);margin:0 0 1.2em;
 letter-spacing:.06em}
.cv-rule .corg{font-size:1.5em;font-weight:800;letter-spacing:-.03em;margin:0}
.cv-rule .cver{font-size:.86em;color:var(--soft);margin:.7em 0 0;
 letter-spacing:.04em}

/* ── 속표지·판권지 ──────────────────────────────────────────────────────── */
.halftitle{justify-content:flex-start;text-align:left;
 padding-left:calc(20mm + var(--gut) - {{ml}}mm)}
.halftitle h1{font-size:2em;font-weight:800;line-height:1.26;letter-spacing:-.04em}
.halftitle h1:before{content:"";display:block;width:var(--gut);height:1.6mm;
 background:var(--accent);margin:0 0 5mm;
 print-color-adjust:exact;-webkit-print-color-adjust:exact}
.colt{font-size:1.5em;font-weight:800;letter-spacing:-.035em;
 padding-bottom:3.5mm;border-bottom:var(--thick) solid var(--ink);margin:0 0 5mm}

/* ── 목차 ─────────────────────────────────────────────────────────────────
   점선 안내선을 쓰지 않는다. 장은 굵게 눕히고 절은 본문칼럼으로 들여 쓴다. */
.toch:after{content:"CONTENTS";display:block;font-size:.3em;font-weight:700;
 letter-spacing:.34em;color:var(--accent);margin-top:2.2mm}
.toc{margin-left:0;padding-left:var(--gut);font-size:.95em;color:var(--ink)}
.toc.tc{padding-left:0;margin:0;padding-top:3.2mm;padding-bottom:3.2mm;
 font-size:1.22em;font-weight:800;letter-spacing:-.025em;
 border-bottom:var(--hair) solid var(--rule)}
.toc .tp{color:var(--ink);font-weight:700}
.toc.tc .tp{color:var(--accent)}

/* ── 인쇄 ───────────────────────────────────────────────────────────────── */
@media print{
 tr,figure,.cap{break-inside:avoid}
 .cap{break-after:avoid}
 h2,h3,h4,.implhead,.chapter{break-after:avoid}
 thead{display:table-header-group}
}
"""
