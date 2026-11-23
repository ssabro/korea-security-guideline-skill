# -*- coding: utf-8 -*-
"""KISA 로봇 보안 발행물형 — 흰 바탕 표지와 하늘색 표.

｢로봇 보안모델(고도화)｣(과학기술정보통신부·한국인터넷진흥원, 2026. 2.)과
｢로봇 보안취약점 점검 체크리스트 해설서｣ 를 `themegen.py` 로 재고, 실제
지면을 보고 손봤습니다. 두 자료의 색이 같아 하나로 합쳤습니다.

**측정값**

  색     #3b4555(슬레이트) · #57aad8(하늘) · #c5e9f7(연파랑)
  글꼴   KoPubWorldDotum Light / Bold, KIMM Bold
  판면   216 x 303 mm · 본문 9 pt

**측정이 아니라 지면을 보고 정한 것**

  표지   다른 발행본과 달리 **흰 바탕**이다. 가운데에 굵은 제목을 크게
         앉히고 그 아래 가는 선과 연월을 두며, 기관 표시는 맨 아래로
         내린다. 남색 바탕 표지 넷과 나란히 놓으면 이 점이 가장 다르다.
  표     머리 칸을 연파랑으로 채우고 글자는 슬레이트로 쓴다. 선은 가늘다.
  쪽     본문 아래에 하늘색 가는 선을 하나 긋는다.
  장     장 간지에 번호를 크게 두고 하늘색 띠를 세운다.

**판면은 216x303 을 쓰지 않았다.** 그 값은 KISA 자료의 것이고, 이 가이드
라인은 발행본 20종의 중앙값인 188x257 을 쓴다. 한 책 안에서 테마를 바꿔도
쪽수가 크게 달라지지 않아야 비교할 수 있다. 색과 글자 짜임만 가져왔다.
"""

THEME = dict(
    key='kisa',
    label='KISA 로봇 보안 발행물형',
    note='KISA 로봇 보안 자료 2종의 색과 지면을 따름. 흰 바탕 표지.',
    page=(188, 257),
    margin=(25, 24, 19, 16),
    body=9.6,
    accent='#3b4555',
    accent2='#57aad8',
    tint='#c5e9f7',
    ink='#1a1a1a',
    rule='#ccd2d8',
    soft='#8d939c',
    badge='square',
    chapter='page',
    cover='art',
    chapter_art=False,  # 간지는 흰 바탕이 제 디자인이다
    motif='wave',      # 바탕 무늬
    cover_bg='white',   # 표지 바탕
    quiet=0.36,
)

EXTRA_CSS = """
/* 색은 CSS 변수를 쓴다. `extra_css()` 는 치수 토큰({{w}} 따위)만 치환한다. */

/* ── 표지 ──────────────────────────────────────────────
   발행본 24종의 표지를 재어 보니 색 면적이 9%에서 100%까지 갈리는데
   짜임은 거의 같다. **제목은 위쪽 1/3, 그림은 가운데, 기관 표시는 맨
   아래**다. 세로 가운데에 제목만 놓는 표지는 하나도 없었다.
   KISA 로봇 자료는 그중에서도 바탕이 희다(색 면적 17~21%).

   가운데 그림 자리에는 원본이 아이소메트릭 삽화를 쓴다. 삽화를 지어낼
   수 없으므로, ｢SIEM 실무자 지침｣ 이 쓰는 방식대로 **엷은 선 도형**을
   둔다. `.cvart` 는 `--cover-art` 를 줄 때만 생기므로 쓰지 않는다. */
@page cover{size:{{w}}mm {{h}}mm;margin:0}
.cover{page:cover;position:relative;width:{{w}}mm;height:{{h}}mm;
 margin:0;padding:0;overflow:hidden;
 background:none}

/* 가운데 그림 자리는 비워 둔다. 원본은 아이소메트릭 삽화를 쓰는데,
   삽화를 지어내면 문서가 말하지 않는 것을 말하게 된다. 발행본 중에도
   ｢SIEM 경영진 지침｣ 처럼 삽화 없이 흰 바탕을 쓰는 것이 있다.
   기관 로고는 `drafts/logos/` 에 넣으면 아래 띠에 함께 앉는다. */

.cover::before{content:"";position:absolute;left:0;right:0;top:0;
 height:3.4mm;background:var(--accent)}
.cover::after{content:"";position:absolute;left:0;right:0;bottom:0;
 height:42mm;background:var(--tint)}

.cover .cvtop{position:absolute;left:0;right:0;top:32mm;
 padding:0 18mm;text-align:center;z-index:2}
.cover .ckind{margin:0 0 7mm;color:var(--accent2);
 font-size:8.4pt;font-weight:700;letter-spacing:.42em}
.cover .ctitle{margin:0;color:var(--accent);
 font-size:24pt;font-weight:800;line-height:1.36;letter-spacing:-.02em}
.cover .cvtop::after{content:"";display:block;width:40mm;height:.7mm;
 margin:9mm auto 0;background:var(--accent2)}

.cover .cvbot{position:absolute;left:0;right:0;bottom:12mm;
 padding:0 18mm;text-align:center;z-index:2}
.cover .cdate{margin:0 0 5mm;color:var(--accent);
 font-size:10.5pt;font-weight:600;letter-spacing:.06em}
.cover .corg{margin:0;color:var(--accent);font-size:11.5pt;font-weight:700}
.cover .cver{margin:3mm 0 0;color:var(--soft);font-size:7.4pt}
.cover .cvlogo{margin-top:5mm}

/* ── 속표지 ──────────────────────────────────────────── */
.halftitle h1{color:var(--accent);border-bottom:.4mm solid var(--accent2);
 padding-bottom:5mm}

/* ── 장 간지 ──────────────────────────────────────────
   ｢AI보안 가이드북｣ 과 ｢국가 망 보안체계 보안 가이드라인｣ 은 장 간지에
   **그 장의 절 목록**을 싣는다. 펼쳤을 때 무엇이 들어 있는지 먼저 본다. */
.chapter{position:relative;display:flex;flex-direction:column;
 justify-content:center;height:{{coverp}}mm;margin:0;padding:0 20mm 0 0;
 border:0;background:#fff;text-align:left}
.chapter::before{content:"";position:absolute;right:0;top:0;bottom:0;
 width:13mm;background:var(--tint)}
.chapter::after{content:"";position:absolute;right:13mm;top:0;bottom:0;
 width:1.2mm;background:var(--accent2)}
.chapter .chno{margin:0 0 3mm;color:var(--accent2);font-size:1.05em;
 font-weight:700;letter-spacing:.3em}
.chapter h1{margin:0;color:var(--accent);font-size:2.3em;font-weight:800;
 letter-spacing:-.03em;line-height:1.24}
.chapter .chsec{margin-top:14mm;max-width:108mm}
.chapter .chsec li{margin:0 0 3.4mm;font-size:.95em}
.chapter .chsec .sno{display:inline-block;min-width:14mm;
 background:var(--accent);color:#fff;text-align:center;font-size:.8em;
 padding:.8mm 1.8mm;font-weight:700;letter-spacing:.02em}
.chapter .chsec .stt{color:var(--accent);font-weight:600}

/* ── 본문 ────────────────────────────────────────────── */
h2{color:var(--accent);border-bottom:.4mm solid var(--accent2);padding-bottom:2mm}
h3{color:var(--accent)}
h4{color:var(--accent2)}
.bdg{background:var(--accent);color:#fff;border-radius:0;
 padding:.9mm 2.6mm;font-weight:700;letter-spacing:.04em}

/* ── 표 ───────────────────────────────────────────────
   원본의 표는 머리 칸이 연파랑이고 선이 가늘며 칸 안 여백이 넉넉하다. */
table{border-color:var(--rule)}
thead th{background:var(--tint);color:var(--accent);font-weight:700;
 border-color:var(--rule)}
tbody td{border-color:var(--rule);padding-top:1.5mm;padding-bottom:1.5mm}
tbody tr:nth-child(2n) td{background:#fafcfe}
.cid,.idc{color:var(--accent);font-weight:700}

/* ── 인용과 주석 ──────────────────────────────────────── */
/* `.law` 는 ｢법령｣ 을 감싸는 **인라인** 이름표다. 배경이나 테두리를
   주면 글 속에 색 덩어리가 줄줄이 생긴다. 색으로만 구분한다. */
.law{color:var(--accent)}
.note{color:var(--soft)}
.cap,.capt{color:var(--accent)}
.capn{color:var(--accent2);font-weight:700}

/* ── 판권지 ───────────────────────────────────────────
   발행본의 판권지는 쪽 **아래 절반**에 가로선으로 묶여 있다. */
.colophon{background:#fff}
.colophon .colt-t{color:var(--accent)}
.colophon::before{background:var(--accent2)}
"""
