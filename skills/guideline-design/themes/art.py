# -*- coding: utf-8 -*-
"""아트워크 표지형 — 전면 기하 구성 위에 제목을 앉히고 기관 로고를 단다.

실제 발행본의 표지는 글자만 있지 않다. ｢국가 망 보안체계 보안 가이드라인｣,
｢AI 보안 가이드북｣ 모두 전면 그래픽과 기관 로고를 쓴다. 이미지 생성 모델
없이 SVG 작도로 같은 성격을 낸다.

판면·여백·본문 크기는 측정 중앙값 그대로다. 표지만 다르다.

로고는 원고 폴더의 `logos/` 에 기관이 넣은 파일을 쓴다. 없으면 그리지 않는다.
"""

THEME = dict(
    key='art',
    label='아트워크 표지형',
    note='전면 기하 구성 표지에 기관 로고. 판면과 본문은 ｢국가 망 보안체계｣ 계열과 같다.',
    page=(188, 257), margin=(25, 24, 19, 16), body=10.5,
    ink='#1a1a1a', accent='#24408f', accent2='#0a7ea4',
    tint='#e8eef7', rule='#c9d3e2', soft='#5b6670',
    badge='pill', chapter='page',
    cover='art',
    motif='crystal',   # crystal | network | wave | grid
    quiet=0.60,        # 위에서부터 이 비율까지는 무늬를 비워 글자 자리로 둔다
)

EXTRA_CSS = """
"""
