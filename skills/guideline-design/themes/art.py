# -*- coding: utf-8 -*-
"""아트워크 표지형 — 전면 기하 구성 위에 제목을 앉히고 기관 로고를 단다.

실제 발행본의 표지는 글자만 있지 않다. ｢국가 망 보안체계 보안 가이드라인｣,
｢AI 보안 가이드북｣ 모두 전면 그래픽과 기관 로고를 쓴다. 이미지 생성 모델
없이 SVG 작도로 같은 성격을 낸다.

장 간지도 전면 아트워크로 쓴다. 본문은 밝고 읽기 쉽게 그대로 둔다 — 간지에서
한 번 쉬고 본문에서 읽는 리듬이다.

판면·여백·본문 크기는 측정 중앙값 그대로다(188×257mm, 25/24/19/16, 10.5pt).
표지와 간지만 다르다.

그림은 **인쇄한 뒤** `coverart.py` 가 깐다. CSS 로는 종이 끝까지 채우지
못한다 — 쪽 조각화로 상자가 232.8mm 에서 잘린다.

로고는 원고 폴더의 `logos/` 에 기관이 넣은 파일을 쓴다. 없으면 그리지 않는다.


`text-shadow` 는 쓰지 않는다. Chrome 인쇄에서 글자가 PDF 글자층에
**두 번 찍혀** 본문을 뽑으면 "개요개요" 처럼 겹친다. 검색과 추출이
망가지므로 그림자 대신 어두운 그림 위에 흰 글자를 그냥 올린다.
"""

THEME = dict(
    key='art',
    label='아트워크 표지형',
    note='전면 기하 구성 표지와 장 간지. 판면과 본문은 ｢국가 망 보안체계｣ 계열과 같다.',
    page=(188, 257), margin=(25, 24, 19, 16), body=10.5,
    ink='#1a1a1a', accent='#24408f', accent2='#0a7ea4',
    tint='#e8eef7', rule='#c9d3e2', soft='#5b6670',
    badge='pill', chapter='page',
    cover='art',
    motif='crystal',   # crystal | network | wave | grid
    quiet=0.60,        # 표지에서 무늬를 비울 위쪽 비율 — 글자 자리
)

EXTRA_CSS = """
/* 장 간지를 전면으로 쓴다. 그림은 인쇄 뒤에 깔리므로 여기서는 글자만 둔다.
   바탕을 투명하게 두어야 밑에 깐 그림이 보인다. */
.chapter{display:flex;flex-direction:column;justify-content:flex-end;
 height:{{coverp}}mm;border:0;margin:0 0 0;padding:0 0 22mm;
 background:none;color:#fff;text-align:left}
.chapter .chno{color:#fff;opacity:.9;letter-spacing:.34em;font-size:1em;
 margin:0 0 .5em;font-weight:700}
.chapter h1{color:#fff;font-size:2.5em;font-weight:800;letter-spacing:-.03em;
 line-height:1.25}

/* 화면에서는 그림이 없으므로 간지가 허옇게 보인다. 주조색을 깔아 둔다. */
@media screen{
 .chapter{background:linear-gradient(160deg,var(--accent),var(--accent2));
  padding:0 14mm 22mm}
}
@media print{
 .chapter{break-after:page}
}
"""
