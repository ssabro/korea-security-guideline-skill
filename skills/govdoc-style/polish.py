"""polish.py — 뜻을 바꾸지 않는 범위에서만 표현을 고친다.

가이드라인 원고는 표현을 다듬다가 **요구 수준이 달라지면 안 됩니다.** 그래서
이 도구는 바꿀 수 있는 것을 좁게 정해 두고, 바꾸면 안 되는 것은 아예 건드리지
못하게 막아 둡니다.

    python polish.py 원고.md --check     # 무엇이 바뀌는지만 본다
    python polish.py 원고.md             # <이름>-교정.md 와 변경 보고서를 쓴다

## 바꾸는 것

발행본 20종에 **한 번도 나오지 않는** 비유적·구어적 표현만 바꿉니다. 짝은
`skills/guideline-lint/lint.py` 의 `FIGURATIVE` 와 같은 근거에서 왔습니다.

## 건드리지 않는 것

- 코드 블록과 인라인 코드
- 법령 인용 `｢ ｣` 안
- 캡션 `[표 N-M]` · `[그림 N-M]`
- 보안통제 ID `PRS-MW-3(1)`
- **종결어미** — `한다` 와 `해야 한다` 사이를 오가지 않습니다. 의무 수준이
  달라지기 때문입니다.

바꾼 뒤에는 위 다섯 가지의 **개수가 그대로인지 확인**하고, 하나라도 어긋나면
파일을 쓰지 않습니다.

## 바꾸지 않는 것(일부러)

긴 대시로 이은 문장은 **세지만 고치지 않습니다.** 문장을 나누는 일은 뜻을
건드리므로 사람이 해야 합니다. 어디에 있는지만 알려 줍니다.

뜻이 문맥에 따라 갈리는 말도 넣지 않았습니다. `걸린다` 는 '시간이 걸린다'
(소요된다)와 '보안이 걸린다'(적용된다)가 달라 사람이 봐야 합니다.

## 표기도 고칩니다

조사 띄어쓰기(`PDF 까지` → `PDF까지`), 금액 단위(`5천만원` → `5천만 원`),
가운뎃점 뒤 공백 — 셋 다 코퍼스가 뒷받침하고 **공백만 바뀌므로** 뜻이 달라질
여지가 없습니다.

## 지켜 주지 못하는 것

**법령 조문을 표의 칸에 옮겨 적은 자리는 지켜 주지 못합니다.** `｢ ｣` 안은
막지만, 꺾쇠 밖에 조문을 그대로 옮긴 칸은 다른 글과 구별할 수 없습니다.
보고서에 전후가 모두 적히니 **반드시 읽고 확인하세요.**
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ── 바꿀 짝 ──────────────────────────────────────────────────────────────
# 왼쪽은 코퍼스 20종에 한 번도 나오지 않는 표현이다. 활용형을 그대로 적어
# 어미가 어긋나지 않게 한다.
PAIRS = [
    ('메운다', '보완한다'),
    ('메우는', '보완하는'),
    ('흔들리면', '저하되면'),
    ('흔들린다', '저하된다'),
    ('번진다', '확산된다'),
    ('번지는', '확산되는'),
    ('박혀 있다', '하드코딩되어 있다'),
    ('박혀 있', '하드코딩되어 있'),
    ('멀쩡해도', '정상 동작하더라도'),
    ('값싼', '비용이 적게 드는'),
    ('울타리', '관리구역 경계'),
    ('갈래로 모인다', '유형으로 구분된다'),
    ('갈래', '유형'),
    ('통째로', '전부'),
    ('무너진다', '훼손된다'),
    ('몰려 있다', '집중되어 있다'),
    ('몰려 있', '집중되어 있'),
    ('발판으로', '경유지로'),
    ('찍는다', '표시한다'),
    ('찍힌', '표시된'),
    ('다녀도', '운용되더라도'),
    ('넘어간다', '탈취될 수 있다'),
    ('낳는다', '가진다'),
    ('잠그면', '해제할 수 없도록 설정하면'),
    ('켜지 않으면', '활성화하지 않으면'),
    ('켜지 않은', '활성화하지 않은'),
    ('켜면', '활성화하면'),
    ('먼저 드러난다', '먼저 확인된다'),
    ('드러난다', '확인된다'),
    # `걸린다` 는 넣지 않는다. '시간이 걸린다'(소요된다)와 '보안이 걸린다'
    # (적용된다)가 뜻이 달라 문맥을 봐야 한다. 사람 몫으로 남긴다.
]

# 지켜야 하는 것 — 바꾼 뒤 개수가 그대로여야 한다
GUARDS = [
    ('보안통제 ID', re.compile(r'[A-Z][A-Z0-9]{1,7}-[A-Z]{2}-M?\d{1,3}(?:\(\d{1,2}\))?')),
    ('법령 인용', re.compile(r'｢[^｣]{2,80}｣')),
    ('캡션', re.compile(r'\[(?:표|그림)\s?[\d\-–.]+\]')),
    # 의무 수준을 가르는 것만 지킨다. 맨 `한다` 는 낱말을 바꾸면 자연히
    # 늘고 줄므로(메운다 → 보완한다) 세어도 뜻이 없다.
    ('~해야 한다', re.compile(r'해야 한다')),
    ('~하여야 한다', re.compile(r'하여야 한다')),
    ('등급 표시 ●', re.compile(r'●')),
]

# 표기 — 공백만 바뀐다. 코퍼스가 모두 뒷받침한다.
SPACING = [
    # 조사는 앞말에 붙여 쓴다 — `PDF 까지` → `PDF까지`
    (re.compile(r"([A-Za-z0-9\)\]`])[ \t]+"
                r"((?:은|는|이|가|을|를|의|에|와|과|로|으로|까지|부터|만|도"
                r"|에서|에는|에도)(?=[\s,.·)\]]|$))"), r"\1\2"),
    # 금액 단위는 띄어 쓴다 — `5천만원` → `5천만 원`
    (re.compile(r"(?<=[0-9억만천백])원"), " 원"),
    # 가운뎃점 뒤에는 공백을 두지 않는다
    (re.compile(r"([가-힣A-Za-z0-9])·[ \t]+(?=[가-힣A-Za-z0-9])"), r"\1·"),
]

RX_INLINE = re.compile(r'`[^`]*`')
RX_LAW = re.compile(r'｢[^｣]*｣')
RX_CAP = re.compile(r'\[(?:표|그림)\s?[\d\-–.]+\]')
RX_ID = re.compile(r'[A-Z][A-Z0-9]{1,7}-[A-Z]{2}-M?\d{1,3}(?:\(\d{1,2}\))?')
RX_EM = re.compile('—')


def protect(line: str) -> tuple:
    """건드리면 안 되는 토막을 자리표시자로 빼 둔다."""
    keep = []

    def stash(m):
        keep.append(m.group(0))
        return '\x00%d\x00' % (len(keep) - 1)

    for rx in (RX_INLINE, RX_LAW, RX_CAP, RX_ID):
        line = rx.sub(stash, line)
    return line, keep


def restore(line: str, keep: list) -> str:
    for i, s in enumerate(keep):
        line = line.replace('\x00%d\x00' % i, s)
    return line


def polish(text: str) -> tuple:
    """고친 글과 (줄번호, 전, 후, 바꾼 짝) 목록."""
    out, changes = [], []
    fence = False
    for n, line in enumerate(text.split('\n'), 1):
        if line.lstrip().startswith('```'):
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        body, keep = protect(line)
        before = body
        used = []
        for a, b in PAIRS:
            if a in body:
                body = body.replace(a, b)
                used.append('%s → %s' % (a, b))
        body = restore(body, keep)
        # 표기는 자리표시자를 되돌린 **뒤에** 고친다. 조사를 띄우는 일이
        # 인라인 코드 바로 뒤에서 가장 자주 일어나는데, 자리표시자 상태로는
        # 그 자리를 볼 수 없다.
        for rx, to in SPACING:
            body, k = rx.subn(to, body)
            if k:
                used.append('표기 %d곳' % k)
        if used:
            changes.append((n, restore(before, keep), body, used))
        out.append(body)
    return '\n'.join(out), changes


def counts(text: str) -> dict:
    return {name: len(rx.findall(text)) for name, rx in GUARDS}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('source')
    ap.add_argument('--out', default=None)
    ap.add_argument('--report', default=None)
    ap.add_argument('--check', action='store_true', help='고치지 않고 보여만 준다')
    a = ap.parse_args(argv)

    if not os.path.exists(a.source):
        print('없는 파일: %s' % a.source)
        return 2
    src = io.open(a.source, encoding='utf-8').read()
    dst, changes = polish(src)

    print('바꿀 곳 %d줄' % len(changes))
    for n, b, c, used in changes[:12]:
        print('  %4d  %s' % (n, ' · '.join(used)))
    if len(changes) > 12:
        print('  … %d줄 더' % (len(changes) - 12))

    # 지켜야 하는 것이 그대로인지
    before, after = counts(src), counts(dst)
    bad = [k for k in before if before[k] != after[k]]
    print()
    for k in before:
        mark = '  ← 달라졌습니다' if k in bad else ''
        print('  %-12s %5d → %5d%s' % (k, before[k], after[k], mark))
    if bad:
        print('\n지켜야 할 것이 달라졌습니다. 파일을 쓰지 않습니다.')
        return 1

    em = [n for n, l in enumerate(src.split('\n'), 1) if RX_EM.search(l)]
    if em:
        print('\n긴 대시로 이은 줄 %d개 — 세기만 하고 고치지 않습니다.' % len(em))
        print('  문장을 나누는 일은 뜻을 건드리므로 사람이 합니다.')

    if a.check:
        return 0
    if not changes:
        print('\n바꿀 것이 없습니다.')
        return 0

    base, ext = os.path.splitext(a.source)
    out = a.out or (base + '-교정' + ext)
    io.open(out, 'w', encoding='utf-8', newline='\n').write(dst)
    rpt = a.report or (base + '-교정보고서.md')
    with io.open(rpt, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 교정 보고서\n\n원본 `%s` · 결과 `%s`\n\n'
                % (os.path.basename(a.source), os.path.basename(out)))
        f.write('바꾼 줄 %d개. 보안통제 ID·법령 인용·캡션·종결어미는 '
                '개수가 그대로입니다.\n\n' % len(changes))
        for n, b, c, used in changes:
            f.write('## %d줄 — %s\n\n' % (n, ', '.join(used)))
            f.write('전\n\n> %s\n\n후\n\n> %s\n\n' % (b.strip(), c.strip()))
        if em:
            f.write('## 사람이 봐야 할 것\n\n긴 대시로 이은 줄 %d개입니다. '
                    '문장을 나누는 일은 뜻을 건드리므로 고치지 않았습니다.\n\n'
                    % len(em))
            f.write('줄 번호: %s\n' % ', '.join(str(x) for x in em[:60]))
    print('\n%s\n%s' % (out, rpt))
    print('원본은 그대로 둡니다. 보고서로 전후를 대조한 뒤 올리세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
