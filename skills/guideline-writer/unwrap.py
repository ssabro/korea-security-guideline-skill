"""unwrap.py — 원고의 강제 줄바꿈을 걷어 한 문단을 한 줄로 만든다.

가이드라인 원고는 Markdown 파일 자체가 작성의 원본이다. 문단을 폭에 맞춰
감아 두면 두 가지가 번거로워진다.

1. **문장을 고칠 때마다 문단을 다시 감아야 한다.** 한 단어를 넣으면 그 아래
   줄들이 전부 밀린다.
2. **`guideline-lint` 의 검사는 줄 단위다.** 용어 혼용, 주기 누락, 위치 표현
   같은 검사가 "같은 줄"을 본다. 문단을 감아 두면 `정기적으로` 와
   `반기 1회 이상` 이 다른 줄에 떨어져 주기를 적었는데도 지적을 받는다.
   문단을 한 줄로 쓰면 "같은 줄"이 곧 "같은 문단"이 된다.

YAML 머리말, 표 행, 코드 블록, 제목은 건드리지 않는다. 목록 항목은 들여써서 이어지는 줄을
항목 본문에 붙여 한 줄로 만든다. 공백 외의 글자가 바뀌지 않았는지 검증한 뒤에
파일을 덮어쓴다.

    python unwrap.py 원고.md
    python unwrap.py 원고.md 요약본.md      # 여러 파일
    python unwrap.py 원고.md --check        # 고치지 않고 바뀔 줄 수만 본다

표준 라이브러리만 쓴다. 두 번 돌려도 결과가 같다.
"""

from __future__ import annotations

import io
import re
import sys

# 목록 항목의 머리 — 불릿, 숫자, 한글 번호, 보충 기호, 인용
LIST_HEAD = re.compile(
    r"^(\s*)(?:[-*+]\s+|\d{1,3}\.\s+|[가-힣]\.\s+|\d{1,3}\)\s+|※\s*|■\s*|>\s+)"
)


def unwrap(text: str) -> str:
    out = []
    buf = []
    fence = False
    lines = text.split(chr(10))
    # YAML 머리말(`---` 로 열고 닫는 첫 블록)은 건드리지 않는다. 한 줄로
    # 뭉개면 `--- name: … description: … ---` 이 되어 스킬 정의가 깨지고
    # Claude Code 가 그 스킬을 읽지 못한다.
    front = bool(lines) and lines[0].rstrip() == "---"

    def flush() -> None:
        if buf:
            out.append(" ".join(buf))
            buf.clear()

    for i, raw in enumerate(lines):
        if front:
            out.append(raw)
            if i > 0 and raw.rstrip() == "---":
                front = False
            continue
        if raw.lstrip().startswith("```"):
            flush()
            out.append(raw)
            fence = not fence
            continue
        if fence:
            out.append(raw)
            continue

        stripped = raw.strip()
        if not stripped:                                  # 문단 경계
            flush()
            out.append("")
            continue
        if raw.lstrip().startswith("|") or raw.startswith("#"):
            flush()
            out.append(raw)                               # 표 행·제목은 그대로
            continue
        if LIST_HEAD.match(raw):                          # 새 목록 항목
            flush()
            buf.append(stripped)
            continue
        buf.append(stripped)                              # 문단 또는 이어지는 줄
    flush()

    # 문단 사이 빈 줄은 하나만 남긴다
    res: list[str] = []
    blank = False
    for line in out:
        if line == "":
            if blank:
                continue
            blank = True
        else:
            blank = False
        res.append(line)
    return "\n".join(res).rstrip("\n") + "\n"


def _squeeze(s: str) -> str:
    """공백을 모두 지운 문자열. 내용 보존을 검증할 때 쓴다."""
    return re.sub(r"\s+", "", s)


def main(argv: list[str]) -> int:
    paths = [a for a in argv if not a.startswith("-")]
    check = "--check" in argv
    if not paths:
        print(__doc__)
        return 2
    for path in paths:
        try:
            src = io.open(path, encoding="utf-8").read()
        except OSError as e:
            print("읽을 수 없습니다: %s (%s)" % (path, e))
            return 2
        dst = unwrap(src)
        if _squeeze(src) != _squeeze(dst):
            print("내용이 바뀌어 중단합니다: %s" % path)
            return 2
        before, after = len(src.split("\n")), len(dst.split("\n"))
        if check:
            state = "바뀔 것 없음" if before == after else "%d줄 -> %d줄" % (before, after)
            print("%s  %s" % (path, state))
            continue
        if before == after:
            print("%s  바뀐 것 없음" % path)
            continue
        io.open(path, "w", encoding="utf-8", newline="\n").write(dst)
        print("%s  %d줄 -> %d줄" % (path, before, after))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
