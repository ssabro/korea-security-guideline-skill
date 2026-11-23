# -*- coding: utf-8 -*-
"""호박색 강조형 — ｢지능형 전력망 사이버보안 가이드라인｣ 을 재서 만들었다.

다른 테마가 모두 파랑 계열인데 이 발행본은 **남색 본문에 호박색을 점색**
으로 쓴다. 표가 많은 문서에서 눈이 쉴 자리를 만드는 방식이라, 통제 항목이
많은 가이드라인에 맞는다.

**잰 값**

    색     #24408f 남색 · #7183b6 연남색 · #fee6d6 살구
    점색   #fdb514 호박 (13 쪽에서 나왔다 — 표 머리와 강조에 쓴다)

｢지능형 전력망｣ 의 글꼴 이름은 PDF 가 부분집합으로 묻어 둬 읽을 수 없었다
(YDVYGO32 따위). 본문은 발행본 관례대로 고딕을 쓴다.

표지 그림은 **제목에서 고른다**(`motif='subject'`).
"""

THEME = dict(
    key='wide',
    label='호박색 강조형',
    note='｢지능형 전력망 사이버보안 가이드라인｣ 계열. 남색 본문에 호박색 점색.',
    page=(183, 256),
    margin=(23, 22, 18, 20),
    body=10.2,
    ink='#1a1a1a',
    accent='#24408f',
    accent2='#c8860a',
    tint='#fdf0e2',
    rule='#d6cfc2',
    soft='#5d6472',
    badge='tag',
    chapter='page',
    cover='art',
    cover_art=True,
    motif='subject',
    cover_bg='white',
    art_accent2='#1d4e8f',  # 간지 그러데이션은 남색으로 — 호박색은 점색일 뿐
    quiet=0.34,
)

EXTRA_CSS = """
/* ── 표지 — 흰 바탕에 호박색 띠 ──────────────────────────
   그림은 인쇄 뒤에 깔리므로 바탕을 투명하게 둔다. */
.cover{background:none;position:relative}
.cover::before{content:"";position:absolute;left:0;top:0;bottom:0;
 width:7mm;background:var(--accent2);z-index:1}
.cover .cvtop{position:absolute;left:0;right:0;top:30mm;
 padding:0 18mm 0 24mm;text-align:left;z-index:2}
.cover .ckind{margin:0 0 6mm;color:var(--accent2);
 font-size:8.4pt;font-weight:700;letter-spacing:.34em}
.cover .ctitle{margin:0;color:var(--accent);font-size:24pt;font-weight:800;
 line-height:1.34;letter-spacing:-.025em}
.cover .cvtop::after{content:"";display:block;width:30mm;height:1.1mm;
 margin:8mm 0 0;background:var(--accent2)}
.cover .cvbot{position:absolute;left:0;right:0;bottom:14mm;
 padding:0 18mm 0 24mm;text-align:left;z-index:2}
.cover .cdate{margin:0 0 5mm;color:var(--ink);font-size:10.5pt;font-weight:600}
.cover .corg{margin:0;color:var(--accent);font-size:11.5pt;font-weight:700}
.cover .cver{margin:3mm 0 0;color:var(--soft);font-size:7.6pt}

/* ── 장 간지 ────────────────────────────────────────────── */
.chapter{display:flex;flex-direction:column;justify-content:center;
 height:{{coverp}}mm;border:0;margin:0;padding:0 14mm;
 background:none;color:#fff;text-align:left}
.chapter .chno{margin:0 0 5mm;color:#ffd98a;font-size:1.2em;
 font-weight:700;letter-spacing:.26em}
.chapter h1{margin:0;color:#fff;font-size:2.35em;font-weight:800;
 letter-spacing:-.03em;line-height:1.26}
.chapter .chsec{margin-top:12mm;max-width:112mm}
.chapter .chsec li{margin:0 0 3mm;font-size:.92em}
.chapter .chsec .sno{display:inline-block;min-width:13mm;text-align:center;
 background:#ffd98a;color:#4a3000;border-radius:0;
 padding:.8mm 2mm;font-size:.84em;font-weight:700}
.chapter .chsec .stt{color:#fff;font-weight:600}
@media screen{
 .chapter{background:linear-gradient(158deg,#16275c,var(--accent))}
}
@media print{
 .chapter{break-after:page}
}

/* ── 본문 — 호박색은 점으로만 ───────────────────────────── */
h2{color:var(--accent);border-bottom:1.1mm solid var(--accent2);
 padding-bottom:2.2mm}
h3{color:var(--accent)}
h4{color:#8a5c08}
.bdg{background:var(--accent2);color:#ffffff;border-radius:0;
 padding:1mm 3mm;font-weight:700}

table{border-color:var(--rule)}
thead th{background:var(--tint);color:#6b4604;font-weight:700;
 border-color:var(--rule)}
tbody td{border-color:var(--rule)}
.cid,.idc{color:var(--accent);font-weight:700}

/* `.law` 는 ｢법령｣ 을 감싸는 **인라인** 이름표다. 배경이나 테두리를
   주면 글 속에 색 덩어리가 줄줄이 생긴다. 색으로만 구분한다. */
.law{color:var(--accent)}
.note{color:var(--soft)}
.cap,.capt{color:var(--accent)}
.capn{color:#8a5c08;font-weight:700}

.colophon .colt-t{color:var(--accent)}
.colophon::before{background:var(--accent2)}
"""
