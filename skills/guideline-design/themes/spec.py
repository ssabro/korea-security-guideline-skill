# -*- coding: utf-8 -*-
"""기술 규격서형 — 156개 보안통제 항목을 찾아 쓰는 책으로 짠다.

이 문서의 알맹이는 읽어 내려가는 글이 아니라 **찾아 들어가는 항목**이다.
그래서 조판을 색인에 맞춘다.

  1. 쪽 왼쪽에 26mm 방주 칸을 비워 둔다. 절 번호(`제2절`), 표·그림 번호,
     구현 예시 표지(■)가 모두 이 칸에 걸린다. 본문은 그 오른쪽에서만 흐르므로
     글줄을 가로막지 않는다.
  2. 표는 방주 칸까지 끌어내 쪽 전체 폭을 쓴다. 이때 **통제항목 ID 칸의 폭을
     방주 칸과 똑같이 26mm 로 맞춘다.** 그러면 ID 가 위의 절 번호·표 번호와
     같은 세로줄에 서고, 쪽을 넘기며 바깥쪽만 훑어도 항목을 찾을 수 있다.
  3. C·S·O 등급 칸은 설명 칸과 굵은 괘선으로 끊어 데이터시트 특성표처럼 묶는다.

수치 근거 — `references/publication-design.md`
  · 판면 188×257mm: 측정 중앙값.
  · 본문 8.8pt: 통제항목 해설서 무리(8.1~9.2pt, 6종)의 가운데. 화면 가독을
    위해 중앙값보다 조금 키웠다.
  · 여백 좌 18 · 우 14 · 상 16 · 하 15mm: 측정 중앙값(25/24/19/16)에서 좌우를
    줄였다. 방주 칸 26mm 를 더하면 본문이 실제로 시작하는 자리는 왼쪽
    44mm 로 측정값보다 넓고, 글줄 길이는 130mm(8.8pt 로 약 41자)가 되어
    측정 판면의 글줄(139mm)보다 짧다. 좌우를 줄인 것은 여백을 아끼려는 것이
    아니라 그 여백을 방주 칸으로 옮긴 것이다.
  · 색 넷: 짙은 남색 #062d56, 중간 파랑 #0099d2, 연한 바탕 #e9f0f8,
    괘선 회청 #9fadbd. 앞의 둘은 측정된 색이다. 연한 바탕은 측정색
    #d7eaf9 를 옅게 한 값인데, 8.8pt 격자에서 #d7eaf9 는 번갈아 칠한 줄이
    ID 칸보다 세게 보여 글자를 덮었다.

알려진 한계 — 방주 칸은 왼쪽에 고정이다. 펼침면 바깥쪽(홀수 쪽 오른쪽,
짝수 쪽 왼쪽)으로 번갈아 두는 것이 책의 관행이지만, 조판기는 원고를 한 줄기
흐름으로 흘리므로 쪽의 홀짝을 알 수 없다. `@page :left/:right` 로 판면
여백만 바꾸면 방주가 인쇄 영역 밖으로 나가 잘린다. PDF 로 읽는 것을 전제로
왼쪽 고정을 택했다.
"""

THEME = dict(
    key='spec',
    label='기술 규격서형',
    note='통제항목을 찾아 쓰는 규격서로 짠다. 188×257mm, 본문 8.8pt. '
         '왼쪽 26mm 방주 칸에 절 번호·표 번호·통제항목 ID 가 한 세로줄로 선다. '
         'C·S·O 등급은 데이터시트 특성표 꼴.',
    page=(188, 257), margin=(18, 14, 16, 15), body=8.8,
    ink='#111318', accent='#062d56', accent2='#0099d2',
    tint='#e9f0f8', rule='#9fadbd', soft='#5c6773',
    badge='square', chapter='page', cover='side',
    mark='●',
)

EXTRA_CSS = """
/* --gut: 방주 칸. 통제항목 ID 칸 폭과 같은 값이어야 세로줄이 맞는다. */
:root{--gut:26mm;--hair:#d5dde6}

body{line-height:1.56;font-variant-numeric:tabular-nums;
 font-feature-settings:"tnum" 1}
p{margin:0 0 .55em}
ul{margin:0 0 .6em;padding-left:1.05em;list-style:none}
li{margin:.12em 0;position:relative;padding-left:.15em}
li:before{content:"–";position:absolute;left:-.95em;color:var(--accent2);
 font-weight:700}
strong{color:var(--accent)}

/* ── 방주 칸 ───────────────────────────────────────────────────────────
   화면에서는 .sheet 의 왼쪽 패딩에 방주 칸을 더한다. 인쇄에서는 판면 여백을
   @page 가 맡으므로 패딩이 곧 방주 칸이다. */
.sheet{padding-left:calc({{ml}}mm + var(--gut))}

/* 판면 왼쪽 가장자리를 따라 내려가는 세로 괘선. 방주 칸의 바깥 테두리이자
   표·삽도가 왼쪽으로 뻗는 한계선이어서, 쪽을 넘겨도 판면의 왼쪽이 한자리에
   선다. 흐름이 여러 쪽으로 쪼개져도 쪽마다 그려지도록 테두리가 아니라
   배경으로 넣는다. 화면과 인쇄 모두 종이 왼쪽에서 {{ml}}mm 자리다. */
.sheet{background-image:linear-gradient(var(--hair),var(--hair));
 background-size:.2mm 100%;background-repeat:repeat-y;
 background-position:{{ml}}mm 0;
 -webkit-print-color-adjust:exact;print-color-adjust:exact}

/* 방주 칸에 걸리는 것들의 공통 자리 */
h2,h2.apx,.cap,.implhead{position:relative}
.cap .capn,.implhead:before{position:absolute;
 left:calc(-1 * var(--gut));width:calc(var(--gut) - 3.2mm);
 text-align:right;white-space:nowrap}
/* h2 는 방주 칸까지 끌어내 괘선을 뻗으므로, 배지는 제 왼쪽 패딩 안에 둔다.
   여기에 -gut 을 주면 판면 밖으로 나가 잘린다. */
h2 .bdg{position:absolute;left:0;width:calc(var(--gut) - 3.2mm);
 text-align:right;white-space:nowrap}

/* ── 제목 ─────────────────────────────────────────────────────────── */
h2{display:block;margin:2.1em 0 .8em;font-size:1.34em;font-weight:800;
 letter-spacing:-.015em;padding-bottom:.3em;
 border-bottom:.5mm solid var(--accent)}
h2 .bdg{top:.18em;background:none;color:var(--accent);border-radius:0;
 padding:0;font-size:.63em;font-weight:800;letter-spacing:.06em;
 font-family:var(--mono)}
h2 .ht{display:block}

/* 절 제목은 방주 칸까지 괘선을 뻗어 쪽을 가로지르는 띠가 되게 한다. */
h2,h2.apx{margin-left:calc(-1 * var(--gut));padding-left:var(--gut)}
h2.apx{break-before:page}

h3{font-size:1.04em;font-weight:800;margin:1.5em 0 .5em;padding:.3em 0 0;
 border-left:0;border-top:.25mm solid var(--rule);
 margin-left:calc(-1 * var(--gut));padding-left:var(--gut);
 letter-spacing:-.01em}
h4{font-size:.98em;font-weight:800;margin:1.15em 0 .35em;color:var(--accent);
 letter-spacing:.01em}

/* 구현 방법 예시 — 원고의 ■ 는 조판기가 떼므로 방주 칸에 다시 세운다. */
.implhead{font-weight:800;color:var(--accent);margin:1.3em 0 .4em;
 font-size:.97em;letter-spacing:.02em}
.implhead:before{content:"■";color:var(--accent2);font-size:.82em;top:.1em}

.note{font-size:.92em;color:var(--soft);margin:.3em 0 .85em;
 padding-left:1.05em;text-indent:-1.05em;line-height:1.5}
.num{margin:0 0 .35em;padding-left:1.6em;text-indent:-1.6em}
.num .n{width:1.6em;font-family:var(--mono);font-weight:700}

/* ── 통제항목 ID — 1등 시민 ──────────────────────────────────────────
   본문 안에서도 눈에 걸리게 한다. 고정폭에 연한 바탕, 아래로 보조색 선. */
.cid{font-family:var(--mono);font-size:.9em;font-weight:700;
 color:var(--accent);background:var(--tint);padding:.04em .3em;
 border-bottom:.25mm solid var(--accent2);letter-spacing:-.01em;
 -webkit-print-color-adjust:exact;print-color-adjust:exact}
.law{color:var(--accent)}

/* ── 표 — 촘촘한 격자 ────────────────────────────────────────────── */
/* 표는 방주 칸까지 끌어내 쪽 전체 폭을 쓴다. 음수 여백이 판면 안쪽으로만
   들어가므로 인쇄에서 잘리지 않는다. */
table{margin-left:calc(-1 * var(--gut));width:calc(100% + var(--gut));
 font-size:.93em;margin-bottom:1em;table-layout:fixed}

/* 칸 너비를 고정한다. 브라우저가 알아서 재는 방식(auto)과 견주어 보니,
   같은 원고가 76쪽에서 60쪽으로 줄고 표마다 달라지던 세로줄이 책 전체에서
   한자리에 섰다. 대신 긴 문장 칸이 짧은 칸과 같은 폭을 갖는다 — 부록 1의
   점검 문항 칸이 그래서 좁다. 격자를 택한 값이다.
   다만 통제항목 ID 만 든 칸은 넓을 까닭이 없으므로 따로 좁힌다. 어느 칸인지는
   첫 줄의 내용으로 가려낸다. */
.tbl:has(tbody tr:first-child td:nth-child(1)>.cid:only-child) th:nth-child(1),
.tbl:has(tbody tr:first-child td:nth-child(2)>.cid:only-child) th:nth-child(2),
.tbl:has(tbody tr:first-child td:nth-child(3)>.cid:only-child) th:nth-child(3),
.tbl:has(tbody tr:first-child td:nth-child(4)>.cid:only-child) th:nth-child(4)
 {width:23mm}
th,td{padding:.3em .45em;border:.2mm solid var(--hair);line-height:1.42;
 word-break:keep-all;overflow-wrap:break-word}
th{background:var(--accent);color:#fff;font-weight:700;text-align:left;
 letter-spacing:.01em;border-color:var(--accent);
 -webkit-print-color-adjust:exact;print-color-adjust:exact}
table{border-top:.5mm solid var(--accent);border-bottom:.5mm solid var(--accent)}
/* 기본 CSS 의 `.tbl th{background:var(--tint)}` 가 요소 선택자보다 세므로
   같은 선택자로 다시 칠한다. 빠뜨리면 흰 글자가 연한 바탕에 깔려 사라진다. */
.tbl th,.ctl th{background:var(--accent);color:#fff;border-color:var(--accent);
 font-size:.95em;padding-top:.35em;padding-bottom:.35em}

/* 번갈아 칠한 줄 — 여섯 칸을 가로로 훑을 때 줄을 놓치지 않게 한다.
   ID 칸은 칠하지 않는다. 방주 칸의 연장으로 읽혀야 한다. */
tbody tr:nth-child(even) td:not(:first-child){background:var(--tint);
 -webkit-print-color-adjust:exact;print-color-adjust:exact}

/* 통제항목표 — ID 칸 폭을 방주 칸과 똑같이 맞춘다 */
.ctl th:first-child,.ctl td:first-child{width:var(--gut)}
.ctl th:nth-child(2),.ctl td:nth-child(2){width:25mm}
.ctl th:first-child{white-space:normal;font-size:.86em;letter-spacing:-.02em}
.ctl td.idc,.ctl td:first-child{font-family:var(--mono);font-size:.92em;
 font-weight:700;color:var(--accent);background:none;
 border-right:.5mm solid var(--accent);padding-right:.6em;
 letter-spacing:-.02em;white-space:nowrap}
.ctl td:first-child .cid{background:none;border-bottom:0;padding:0;
 font-size:1em;font-weight:700}

/* C·S·O 등급 칸 — 데이터시트 특성표. 설명 칸과 굵은 선으로 끊고,
   등급끼리는 실선으로 가른다. */
.ctl th.g,.ctl td.g{width:7.2mm;text-align:center;vertical-align:middle;
 padding-left:0;padding-right:0;font-family:var(--mono)}
.ctl .g{border-left:.5mm solid var(--accent)}
.ctl .g+.g{border-left:.2mm solid var(--hair)}
.ctl th.g{font-size:1.02em;font-weight:800;letter-spacing:0}
.ctl td.g{color:var(--accent2);font-size:1.02em;line-height:1.3}

/* ── 캡션 — 번호는 방주 칸으로 ──────────────────────────────────── */
.cap{display:block;margin:1.4em 0 .3em;font-size:.95em;font-weight:800;
 color:var(--ink);letter-spacing:-.01em}
.cap .capn{top:.1em;background:none;color:var(--accent);border-radius:0;
 padding:0;font-family:var(--mono);font-size:.86em;font-weight:700}
.cap .capt{font-weight:800}

figure{margin:0 0 1.1em calc(-1 * var(--gut))}
pre{margin-left:calc(-1 * var(--gut));background:var(--tint);
 border-left:1.2mm solid var(--accent2);padding:.6em .8em;font-size:.88em;
 line-height:1.45;-webkit-print-color-adjust:exact;print-color-adjust:exact}

/* ── 장 간지 ─────────────────────────────────────────────────────── */
.chapter{margin:0 0 8mm calc(-1 * var(--gut));padding:5mm 0 4mm var(--gut);
 border-top:1.6mm solid var(--accent);border-bottom:.25mm solid var(--rule)}
.chno{font-family:var(--mono);font-size:1em;font-weight:700;
 letter-spacing:.18em;color:var(--accent2);margin:0 0 .5em}
.chapter h1{font-size:1.85em;font-weight:800;letter-spacing:-.025em}

/* ── 앞붙이 ─────────────────────────────────────────────────────── */
.toch{font-size:1.5em;font-weight:800;letter-spacing:-.02em;
 margin:0 0 .9em calc(-1 * var(--gut));padding:0 0 .35em var(--gut);
 border-bottom:1.2mm solid var(--accent)}
.toc{display:flex;align-items:baseline;gap:0;margin:0 0 .22em;
 padding-left:1.2em;font-size:.97em;color:var(--ink)}
.toc .tt{order:1;flex:0 1 auto}
.toc:has(.tp):after{content:"";order:2;flex:1 1 auto;
 border-bottom:.22mm dotted var(--rule);margin:0 .5em .33em}
.toc .tp{order:3;margin-left:0;font-family:var(--mono);font-weight:700;
 color:var(--accent);padding-left:0}
.toc.tc{margin:.8em 0 .3em calc(-1 * var(--gut));padding:0 0 .2em var(--gut);
 font-weight:800;font-size:1.04em;border-bottom:.25mm solid var(--rule)}
.toc.tc:has(.tp):after{border-bottom-style:none}

.docinfo h2,.docinfo .toch{margin-left:calc(-1 * var(--gut))}
.docinfo table{font-size:.98em}
.docinfo th{width:32mm}

.halftitle h1{font-size:1.45em;font-weight:800;letter-spacing:-.02em}
.colt{font-size:1.15em;font-weight:800;border-bottom:1.2mm solid var(--accent);
 margin-left:calc(-1 * var(--gut));padding-left:var(--gut)}
.colt-t{margin-left:0;width:100%;border:0}
.colt-t th{background:none;color:var(--soft);border:0;width:30mm;
 font-family:var(--body)}
.colt-t td{border:0}
.colt-t tbody tr:nth-child(even) td:not(:first-child){background:none}

/* ── 표지 — 규격서 표제지 ───────────────────────────────────────────
   왼쪽에 색 바를 세우고(이름 붙은 cover 쪽이라 종이 끝까지 닿는다) 제목을
   왼쪽으로 맞춘다. 아래는 괘선으로 끊은 발행 정보 블록. */
.cover.cv-side{justify-content:space-between;text-align:left;padding:0;
 border-left:9mm solid var(--accent);background:#fff}
.cv-side .cvtop{padding:44mm 16mm 0 15mm}
.cv-side .cvbot{padding:0 16mm 20mm 15mm;margin:0;
 border-top:.6mm solid var(--ink)}
.cv-side .ckind{font-family:var(--mono);font-size:.82em;font-weight:700;
 letter-spacing:.22em;color:var(--accent2);margin:0 0 2.2em;
 padding-bottom:.5em;border-bottom:.25mm solid var(--rule)}
.cv-side .ctitle{font-size:2.15em;font-weight:800;line-height:1.3;
 letter-spacing:-.035em;margin:0}
.cv-side .cdate{font-family:var(--mono);font-size:1em;font-weight:700;
 color:var(--accent);letter-spacing:.04em;margin:1.4em 0 .5em}
.cv-side .corg{font-size:1.25em;font-weight:800;margin:0 0 .3em}
.cv-side .cver{font-size:.85em;color:var(--soft);margin:.7em 0 0;
 padding-top:.6em;border-top:.25mm solid var(--rule)}
.cover .cid{background:none;border:0}

/* ── 인쇄 ───────────────────────────────────────────────────────── */
@media print{
 /* 판면 여백은 @page 가 맡는다. 패딩에 남는 것은 방주 칸뿐이다. */
 .sheet{padding:0 0 0 var(--gut);background-position:-.1mm 0}
 /* 표 머리를 쪽마다 되풀이하고, 통제항목 한 줄이 쪽을 넘어 잘리지 않게 한다. */
 thead{display:table-header-group}
 .ctl thead,.tbl thead{break-after:avoid}
 tr,tbody tr{break-inside:avoid}
 .cap{break-after:avoid;break-inside:avoid}
 .implhead{break-after:avoid}
 h2,h3,h4{break-after:avoid}
 figure,pre{break-inside:avoid}
}
"""
