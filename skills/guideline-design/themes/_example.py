# -*- coding: utf-8 -*-
"""보기. 파일 하나가 테마 하나다. `_` 로 시작하는 파일은 읽지 않는다."""

THEME = dict(
    key='example',
    label='보기 테마',
    note='themes/README.md 를 보세요.',
    page=(188, 257), margin=(25, 24, 19, 16), body=10.5,
    ink='#1a1a1a', accent='#24408f', accent2='#006cb7',
    tint='#e8eef7', rule='#c9d3e2', soft='#5b6670',
    badge='pill', chapter='page', cover='rule',
)

EXTRA_CSS = """
h2 .bdg{letter-spacing:.04em}
"""
