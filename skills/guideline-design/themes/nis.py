# -*- coding: utf-8 -*-
"""국가정보원 계열 — ｢국가 망 보안체계 보안 가이드라인 1.0｣ 을 따른다.

같은 기관이 내는 가이드라인끼리 통일감이 있어야 하므로, 그 발행본의 짜임을
거의 그대로 가져왔다. `themegen.py` 로 재고 지면을 하나씩 보며 맞췄다.

**잰 값**

    판면   188 x 257 mm   (우리 기본값과 같다)
    여백   좌 25 · 우 24 · 상 16 · 하 28 mm
    본문   10.5 pt
    주조색 #2a4098 남보라
    배지색 #73c4ce 청록       (본문의 `제N절` 배지에서 뜸)
    바탕   #edf4fc 연하늘     (목차·문서이력 면)
    선     #9fc1e8

**지면에서 가져온 것**

    표지     흰 바탕. 버전을 네모 테두리에 넣어 오른쪽 위에,
             제목은 오른쪽 맞춤으로 위쪽 1/3 에, 연월은 그 아래.
             가운데 아래는 기하 구성, 맨 아래 기관 로고.
    문서이력  쪽 전체를 연하늘로 깔고 표 머리를 파랑으로.
    목차     연하늘 면을 안쪽에 두고 장은 배지, 절은 점선과 쪽번호.
    장 간지  전면 어두운 그림 위에 장 번호 · 가로선 · 장 제목 ·
             그 장의 절 목록을 흰 글자로.
    본문     `제N절` 을 청록 배지에 넣고 절 제목 아래 밑줄.

**그림에 대하여** — 원본의 표지와 간지에는 사진을 기하 도형 안에 합성해
넣었다. 사진은 저작권이 있는 자산이라 가져올 수 없고 지어낼 수도 없다.
대신 `figures.py` 가 같은 성격의 **기하 구성을 SVG 로 작도**하고
`coverart.py` 가 인쇄한 뒤에 깐다. 사진이 필요하면 기관이 파일을 주면
된다. 로고도 `drafts/logos/` 에 넣은 것만 쓰고 그리지 않는다.


`text-shadow` 는 쓰지 않는다. Chrome 인쇄에서 글자가 PDF 글자층에
**두 번 찍혀** 본문을 뽑으면 "개요개요" 처럼 겹친다. 검색과 추출이
망가지므로 그림자 대신 어두운 그림 위에 흰 글자를 그냥 올린다.
"""

THEME = dict(
    key='nis',
    label='국가정보원 계열',
    note='｢국가 망 보안체계 보안 가이드라인 1.0｣ 의 짜임을 따름. 188x257mm.',
    page=(188, 257),
    margin=(25, 24, 16, 28),
    body=10.5,
    ink='#1a1a1a',
    accent='#2a4098',
    accent2='#73c4ce',
    tint='#edf4fc',
    rule='#9fc1e8',
    soft='#5b6670',
    badge='pill',
    chapter='page',
    cover='art',
    motif='subject',   # 그림은 제목에서 고른다 — 로봇·선박·전력 등
    cover_bg='white',  # 원본 표지는 흰 바탕이다
    quiet=0.34,        # 표지 위쪽 34% 는 그림을 비운다 — 제목 자리
    back_art=True,     # 뒤표지에 둥근 기둥과 보안 아이콘을 깐다
)

EXTRA_CSS = """
/* ── 표지 ──────────────────────────────────────────────
   원본은 흰 바탕에 제목을 **오른쪽 맞춤**으로 위쪽 1/3 에 앉히고,
   버전을 네모 테두리에 넣어 오른쪽 위 모서리에 둔다. 그림은 가운데
   아래를 채우고 기관 로고가 맨 아래에 온다.
   그림은 인쇄 뒤에 깔리므로 바탕을 투명하게 두어야 한다. */
.cover{background:none;position:relative}
/* 바탕이 희므로 글자는 주조색으로 둔다(`cover_bg='white'`). */
.cover .cvtop{position:absolute;left:0;right:0;top:26mm;
 padding:0 22mm 0 30mm;text-align:right;z-index:2}
.cover .ckind{margin:0 0 6mm;color:var(--soft);
 font-size:8.4pt;font-weight:600;letter-spacing:.34em}
.cover .ctitle{margin:0;color:var(--accent);
 font-size:25pt;font-weight:800;line-height:1.34;letter-spacing:-.025em}

.cover .cvbot{position:absolute;left:0;right:0;bottom:16mm;
 padding:0 22mm;text-align:center;z-index:2}
.cover .cdate{margin:0 0 9mm;color:var(--ink);
 font-size:11pt;font-weight:600;letter-spacing:.04em}
.cover .corg{margin:0;color:var(--accent);font-size:11.5pt;font-weight:700}
.cover .cvlogo{margin-top:6mm}

/* 버전은 오른쪽 위 네모 안에 — 원본의 `1.0` 자리 */
.cover .cver{position:absolute;right:22mm;top:14mm;margin:0;z-index:3;
 border:.45mm solid var(--accent);color:var(--accent);
 padding:1.4mm 3.4mm;font-size:9pt;font-weight:700;letter-spacing:.02em}

/* ── 문서 정보 ────────────────────────────────────────
   원본은 이 쪽 전체를 연하늘로 깔고 표 머리를 파랑으로 둔다. */
/* 발간 정보도 흰 바탕에 둔다. 쪽 전체를 덮는 색은 인쇄비가 오르고,
   앞붙이가 연이어 색면이면 책이 무거워 보인다. */
.docinfo{background:none;padding:0}
.docinfo h2,.docinfo h1{color:var(--accent)}
.docinfo thead th{background:var(--rule);color:#15306b;font-weight:700}
.docinfo table{background:#fff}

/* ── 목차 ─────────────────────────────────────────────
   원본은 연하늘 면을 안쪽에 두고 장을 배지로 끊는다. */
/* 목차는 흰 바탕에 둔다. 원본은 연하늘 면을 깔지만, 쪽 전체를 덮는 색은
   통제 항목이 많은 문서에서 눈을 지치게 하고 인쇄비도 올린다. */
.tocpage{background:none;padding:0}
.tocpage .toch{color:var(--accent);letter-spacing:.3em}
.tocpage a,.tocpage li{color:#20264a}

/* ── 장 간지 ──────────────────────────────────────────
   전면 그림 위에 장 번호 · 가로선 · 제목 · 절 목록을 흰 글자로.
   원본은 가로선 오른쪽 끝에 점을 하나 찍는다. */
.chapter{display:flex;flex-direction:column;justify-content:center;
 height:{{coverp}}mm;border:0;margin:0;padding:0 16mm 0 14mm;
 background:none;color:#fff;text-align:left}
.chapter .chno{margin:0 0 6mm;color:#fff;opacity:.95;
 font-size:1.3em;font-weight:700;letter-spacing:.1em}
.chapter h1{margin:0;color:#fff;font-size:2.3em;font-weight:800;
 letter-spacing:-.03em;line-height:1.26}

/* 장 번호와 제목 사이의 가로선 + 오른쪽 끝 점 */
.chapter .chno::after{content:"";display:block;position:relative;
 width:72mm;height:.4mm;margin:5mm 0 0;background:rgba(255,255,255,.85)}

.chapter .chsec{margin-top:13mm;max-width:118mm}
.chapter .chsec li{margin:0 0 3.2mm;font-size:.92em}
.chapter .chsec .sno{display:inline-block;min-width:13mm;text-align:center;
 background:var(--accent2);color:#15306b;border-radius:2.4mm;
 padding:.8mm 2mm;font-size:.84em;font-weight:700}
.chapter .chsec .stt{color:#fff;font-weight:600}

/* 화면에서는 그림이 없어 간지가 허옇다. 주조색을 깔아 둔다. */
@media screen{
 .chapter{background:linear-gradient(155deg,#15306b,var(--accent))}
}
@media print{
 .chapter{break-after:page}
}

/* ── 본문 ─────────────────────────────────────────────
   원본은 `제N절` 을 청록 배지에 넣고 절 제목 아래에 밑줄을 둔다. */
.bdg{background:var(--accent2);color:#15306b;border-radius:2.6mm;
 padding:1mm 3mm;font-weight:700;letter-spacing:.02em}
h2{color:var(--accent);border-bottom:.5mm solid var(--accent);
 padding-bottom:2.4mm}
h3{color:var(--accent)}
h4{color:#3b5bb5}

/* ── 표 ──────────────────────────────────────────────── */
table{border-color:var(--rule)}
thead th{background:var(--tint);color:var(--accent);font-weight:700;
 border-color:var(--rule)}
tbody td{border-color:var(--rule)}
.cid,.idc{color:var(--accent);font-weight:700}

/* ── 인용과 주석 ──────────────────────────────────────── */
/* `.law` 는 ｢법령｣ 을 감싸는 **인라인** 이름표다. 배경이나 테두리를
   주면 글 속에 색 덩어리가 줄줄이 생긴다. 색으로만 구분한다. */
.law{color:var(--accent)}
.note{color:var(--soft)}
.cap,.capt{color:var(--accent)}
.capn{color:#3b5bb5;font-weight:700}

/* ── 뒤표지 ─────────────────────────────────────────────
   원본은 둥근 기둥에 보안 아이콘을 쌓고 그 옆에 제목을 둔다. 기둥은
   인쇄 뒤에 깔리므로(`back_art`) 여기서는 글자 자리만 잡는다. */
.colophon{position:relative;height:{{coverp}}mm;background:none;
 display:block;padding:0}
.colbox{position:absolute;left:30mm;top:50%;transform:translateY(-50%);
 max-width:98mm}
.colkind{margin:0 0 2.5mm;color:var(--soft);font-size:7.6pt;
 font-weight:700;letter-spacing:.24em}
.colt{margin:0;color:var(--accent);font-size:13pt;font-weight:800;
 line-height:1.44;letter-spacing:-.02em}
.colorg{margin:4mm 0 0;color:var(--ink);font-size:9.4pt;font-weight:600}
"""
