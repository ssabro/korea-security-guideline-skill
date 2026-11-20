"""
lint.py — 사이버보안 가이드라인 원고를 analysis/ 의 증류 규칙으로 검사한다.

기계적으로 판정할 수 있는 항목만 본다. 구조가 설득력 있는지, 위협과 대책이
맞물리는지 같은 판단은 사람(또는 guideline-writer 스킬)의 몫이다.

    python lint.py 원고.md
    python lint.py 원고.md --genre guideline      # 장르 명시
    python lint.py docs/*.md --format json
    python lint.py 원고.md --only ENDING-MIX,GRADE-GAP

장르: guideline(분야별 가이드라인, 기본) | control(통제항목 체계)
      ordinance(법령형 지침) | manual(실무 안내서, 경어체)

같은 성격의 지적은 하나로 묶어 횟수와 예시 줄번호만 보여준다.
문서 전체에 걸친 일관성 문제를 줄마다 반복해 출력하면 읽을 수 없게 된다.

종료 코드: 0 = error 없음, 1 = error 있음, 2 = 실행 실패
요구 사항: 표준 라이브러리만.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SAMPLE_LIMIT = 5

# ── 진단 ──────────────────────────────────────────────────────────────────────


@dataclass
class Finding:
    code: str
    severity: str  # error | warn | info
    line: int
    message: str
    hint: str = ""
    count: int = 1
    samples: list[int] = field(default_factory=list)


@dataclass
class Doc:
    path: Path
    lines: list[str]
    genre: str
    text: str = ""
    findings: list[Finding] = field(default_factory=list)

    def add(self, code: str, sev: str, line: int, msg: str, hint: str = "") -> None:
        """한 곳을 지적한다."""
        self.findings.append(Finding(code, sev, line, msg, hint))

    def add_agg(self, code: str, sev: str, lines: list[int], msg: str,
                hint: str = "") -> None:
        """여러 곳에 걸친 같은 문제를 하나로 묶어 지적한다."""
        if not lines:
            return
        uniq = sorted(set(lines))
        self.findings.append(Finding(
            code, sev, uniq[0], msg, hint,
            count=len(uniq), samples=uniq[:SAMPLE_LIMIT],
        ))


# ── 공통 패턴 ─────────────────────────────────────────────────────────────────

RX_HAYEOYA = re.compile(r"(?:하|되)여야\s*한다")
RX_HAEYA = re.compile(r"[가-힣]야\s*한다(?![가-힣])")
RX_HONORIFIC = re.compile(r"(?:습니다|입니다)(?![가-힣])|(?:하세요|하십시오|바랍니다)")
RX_PLAIN = re.compile(r"(?:[가-힣]{2,}한다|된다|이다)(?![가-힣])")
RX_LAW_QUOTE = re.compile(r"[｢「][^｣」]{2,60}[｣」]")

# 통제항목 ID: <접두사>-<도메인 2글자>-<번호>[(강화)] 또는 -M<번호>
RX_ID_OK = re.compile(
    r"\b([A-Z][A-Z0-9]{1,7})-([A-Z]{2})-(M?\d{1,3})(?:\((\d{1,2})\))?(?![\w(])"
)
# ID처럼 보이지만 문법에서 벗어난 것
RX_ID_LOOSE = re.compile(
    r"\b([A-Z][A-Z0-9]{1,7})-([A-Za-z]{1,4})-([A-Za-z]?\d{1,3})(?:\((\d{1,2})\))?(?![\w(])"
)
# 오탐 제외: 널리 쓰이는 외부 식별자
ID_IGNORE_PREFIX = {
    "CVE", "CWE", "CAPEC", "SHA", "AES", "RSA", "LSH", "HMAC", "TTAK", "TTAS",
    "ISO", "IEC", "NIST", "SP", "FIPS", "RFC", "ITSG", "GPT", "TLS", "SSL",
    "ECDSA", "ECDH", "KCMVP", "UTF", "ASCII", "KS", "X", "ML", "SLH", "FN",
    "ID", "URL", "API", "PDF", "HTTP", "HTTPS",
}

# 식별자처럼 생긴 토큰. 약어 검사에서 지워 오탐을 막는다.
# 통제항목 ID(PRS-MW-1), 외부 점검항목(IA-01), 권고·취약점 번호(ICSA-21-315-02,
# CVE-2021-38425)가 모두 여기 걸린다.
RX_IDLIKE = re.compile(
    r"\b[A-Z][A-Z0-9]{1,7}-[A-Za-z]{1,4}-[A-Za-z]?\d{1,3}(?:\(\d{1,2}\))?"
    r"|\b[A-Z]{2,6}-\d{1,4}(?:-\d{1,4})*"
)

CYCLE_NEAR = re.compile(
    r"(?:연|월|주|일|분기|반기|년)\s?\d+\s?회|\d+\s?(?:일|주|개월|년|시간|분)\s?"
    r"(?:마다|이내|이상|이하|단위|주기)|매\s?(?:일|주|월|분기|반기|년)|"
    r"\d+\s?회\s?이상|실시간|상시"
)
RX_VAGUE_CYCLE = re.compile(r"정기적[으로인]|주기적[으로인]|수시로")

RX_MIDDOT_BAD = re.compile(r"ㆍ")  # ㆍ 한글 호환 자모

# 패턴을 **가리켜 설명하는** 자리는 지적하지 않는다. 규칙 문서가 "`ㆍ` 를 쓰지
# 마세요" 라고 적으면 그 줄이 자기 규칙에 걸리고, 쓰는 사람이 나쁜 보기를
# 인용할 때도 같은 일이 난다.
RX_INLINE_CODE = re.compile(r"`[^`]*`")
RX_QUOTED = re.compile(r"[\"\'\u201c\u201d\u2018\u2019]"
                       r"[^\"\'\u201c\u201d\u2018\u2019]{0,40}"
                       r"[\"\'\u201c\u201d\u2018\u2019]")


def unquoted(line: str) -> str:
    """인라인 코드와 따옴표 안을 지운 줄.

    **표면 패턴을 보는 검사는 모두 이걸 거친다** — MIDDOT, MIDDOT-SPACE,
    LOCATION-REF, FIGURATIVE, MONEY-SPACE. 규칙을 적은 문서는 나쁜 보기를
    적어야 하는데 그 자리까지 지적하면 자기 규칙에 걸린다.

    PARTICLE-SPACE 는 예외다. 조사를 띄우는 일이 바로 인라인 코드 **뒤**에서
    가장 자주 일어나므로 거기를 봐야 한다.
    """
    return RX_QUOTED.sub(" ", RX_INLINE_CODE.sub(" ", line))

RX_LOCATION_REF = re.compile(r"(?:아래|위|다음|상기|하기)\s*(?:의\s*)?(?:표|그림|도표|그래프)")
# 조사는 앞말에 붙여 쓴다(한글 맞춤법). 영문·숫자·닫는 괄호·인라인 코드
# 뒤에서 자주 깨진다 — `PDF 까지`, `A4 는`. 조사 뒤에 다른 글자가 이어지면
# 조사가 아니므로(`SVG 로드`, `API 가능`) 경계를 본다.
RX_PARTICLE_SPACE = re.compile(
    r"[A-Za-z0-9\)\]`]\s+"
    r"(?:은|는|이|가|을|를|의|에|와|과|로|으로|까지|부터|만|도|에서|에는|에도)"
    r"(?=[\s,.·)\]]|$)")

# 비유적·구어적 표현과 권장 표현. 코퍼스 20종에서 **한 번도 나오지 않는**
# 말만 골랐다(`고리` 처럼 다른 낱말의 일부가 되는 것은 뺐다).
FIGURATIVE = [
    (r"메운다|메우는|메울", "보완한다"),
    (r"흔들리|흔들린", "영향을 받는다"),
    (r"번진다|번지는|번질", "확산된다"),
    (r"박혀 있|박힌", "하드코딩되어 있다"),
    (r"멀쩡", "정상 동작한다"),
    (r"값싼|값싸", "비용이 적게 드는"),
    (r"울타리", "관리구역 경계"),
    (r"갈래", "유형"),
    (r"통째로", "전부"),
    (r"무너지|무너뜨", "훼손된다"),
    (r"켜지 않|켜면|켜고|꺼진", "활성화·비활성화"),
    (r"찍는다|찍어", "표시한다"),
]
RX_FIGURATIVE = [(re.compile(p), s) for p, s in FIGURATIVE]

# 금액 단위 — `원` 은 앞말과 띄어 쓴다. 코퍼스는 띄움 3 · 붙임 0.
RX_MONEY = re.compile(r"(?<=[0-9억만천백])원")  # 5천만원 → 5천만 원

# `N 가지` 를 선언하고 그보다 큰 서수를 쓴 곳
RX_COUNT_DECL = re.compile(r"(두|세|네|다섯|2|3|4|5)\s*가지")
ORD_WORD = {"첫": 1, "둘": 2, "두": 2, "셋": 3, "세": 3, "넷": 4, "네": 4,
            "다섯": 5}
RX_ORDINAL = re.compile(r"(첫|둘|두|셋|세|넷|네|다섯)\s*(?:째|번째)")
COUNT_WORD = {"두": 2, "세": 3, "네": 4, "다섯": 5, "2": 2, "3": 3, "4": 4, "5": 5}

# 가운뎃점 뒤의 공백
RX_MIDDOT_SPACE = re.compile(r"[가-힣A-Za-z0-9]·[ \t]+[가-힣A-Za-z0-9]")

RX_CAPTION_SQ = re.compile(r"\[(?:표|그림)\s?[\d\-–.]+\]")
RX_CAPTION_AN = re.compile(r"<(?:표|그림)\s?[\d\-–.]+>")

# 용어 혼용 — analysis/07-terminology.md
TERM_PAIRS = [
    ("사용자", ["이용자"]),
    ("기관", ["조직"]),
    ("정보시스템", ["정보 시스템"]),
    ("취약점", ["취약성"]),
    ("침해사고", ["보안사고"]),
    ("이상행위", ["비정상 행위", "비정상행위"]),
    ("접근통제", ["접근 제어", "접근제어", "접근 통제"]),
    ("모니터링", ["감시"]),
    ("권고", ["권장"]),
]

HEADING_RX = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_ROW = re.compile(r"^\s*\|")
DOT = "●"


def is_code_fence(line: str) -> bool:
    return line.lstrip().startswith("```")


def body_lines(doc: Doc) -> list[tuple[int, str]]:
    """코드 블록을 제외한 (1-기반 줄번호, 줄) 목록."""
    out, fence = [], False
    for i, l in enumerate(doc.lines, 1):
        if is_code_fence(l):
            fence = not fence
            continue
        if not fence:
            out.append((i, l))
    return out


def cells_of(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def outside_quote(line: str) -> str:
    """법령 인용 구간을 지운 줄. 인용문 안의 표기는 원문 그대로 두는 것이 규칙이다."""
    return RX_LAW_QUOTE.sub(" ", line)


# ── 검사 ──────────────────────────────────────────────────────────────────────


def check_ending_mix(doc: Doc) -> None:
    """의무 표현 두 변형(~하여야 한다 / ~해야 한다)의 혼용."""
    a = [n for n, l in body_lines(doc) if RX_HAYEOYA.search(outside_quote(l))]
    b = [n for n, l in body_lines(doc)
         if RX_HAEYA.search(outside_quote(l)) and not RX_HAYEOYA.search(outside_quote(l))]
    if not a or not b:
        return
    minority, major = (a, "~해야 한다") if len(a) <= len(b) else (b, "~하여야 한다")
    doc.add_agg(
        "ENDING-MIX", "error", minority,
        f"의무 표현이 섞였습니다 — ~하여야 한다 {len(a)}줄 / ~해야 한다 {len(b)}줄",
        f"문서 안에서 하나로 통일하세요. 다수인 '{major}' 쪽으로 맞추는 것이 기본이고, "
        f"가이드라인은 '~해야 한다', 법령형 지침은 '~하여야 한다'입니다. "
        f"법령 인용문 안의 '~하여야 한다'는 원문 그대로 두므로 검사에서 제외됩니다.",
    )


def check_honorific(doc: Doc) -> None:
    """경어체와 비경어체의 혼용. 장르에 따라 어느 쪽이 침입인지 바뀐다."""
    if doc.genre == "manual":
        plain = [n for n, l in body_lines(doc) if RX_PLAIN.search(l)]
        doc.add_agg("HONORIFIC", "error", plain,
                    "실무 안내서인데 비경어체 평서형이 쓰였습니다",
                    "문서 전체를 경어체(~합니다 / ~하세요)로 통일하세요.")
        return
    # 발간사·머리말만 경어체인 것은 코퍼스의 관행이므로 앞부분은 눈감아 준다.
    head_limit = max(30, len(doc.lines) // 12)
    hon = [n for n, l in body_lines(doc) if RX_HONORIFIC.search(l) and n > head_limit]
    doc.add_agg("HONORIFIC", "error", hon,
                "본체 가이드라인에 경어체가 섞였습니다",
                "비경어체 평서형(~한다 / ~해야 한다)으로 바꾸세요. 경어체는 "
                "발간사·머리말, 또는 문서 전체가 실무 안내서일 때만 씁니다. "
                f"(앞 {head_limit}줄은 발간사로 보고 검사하지 않습니다)")


def control_rows(doc: Doc) -> list[tuple[int, list[str], str, int]]:
    """통제항목 ID 가 들어 있는 표 행: (줄번호, 칸 목록, ID, ID 칸 위치)."""
    out = []
    for n, l in body_lines(doc):
        if not TABLE_ROW.match(l):
            continue
        cells = cells_of(l)
        for i, c in enumerate(cells):
            m = RX_ID_OK.fullmatch(c)
            if m and m.group(1) not in ID_IGNORE_PREFIX:
                out.append((n, cells, c, i))
                break
    return out


def mark_zone(cells: list[str], id_idx: int) -> list[str]:
    """한 행에서 등급 표시 칸들만 잘라낸다.

    머리글 위치에 의존하지 않는다. 등급 머리글(`C 기밀 | S 민감 | O 공개`)은
    병합된 소머리글 행에 있어서 본문 행의 열 위치와 맞지 않고, 병합 셀이 있는
    표를 변환하면 열이 밀린다. 그래서 '● 또는 빈칸만으로 된 뒤쪽 연속 구간'을
    등급 구역으로 본다.
    """
    tail: list[str] = []
    for c in reversed(cells[id_idx + 1:]):
        if c in (DOT, "", "-"):
            tail.append(c)
        else:
            break
    tail.reverse()
    return tail


def check_control_obligation(doc: Doc) -> None:
    """통제항목 설명문의 기본 종결은 ~한다. ~해야 한다는 중복."""
    hits, ids = [], []
    for n, cells, cid, idx in control_rows(doc):
        for c in cells[idx + 1:]:
            if len(c) < 12:
                continue
            if RX_HAEYA.search(c) or RX_HAYEOYA.search(c):
                hits.append(n)
                ids.append(cid)
                break
    if not hits:
        return
    shown = ", ".join(ids[:SAMPLE_LIMIT]) + (" …" if len(ids) > SAMPLE_LIMIT else "")
    doc.add_agg("CONTROL-OBLIGATION", "warn", hits,
                f"통제항목 설명문이 '~해야 한다'로 끝납니다 ({shown})",
                "이 장르에서 통제항목 설명은 '~한다'가 기본형입니다. 전부 "
                "'~해야 한다'로 쓰면 모든 항목이 같은 세기가 되어 등급 구분이 "
                "사라집니다. (코퍼스: 서술 3,073회 대 의무 1,332회)")


def check_id_syntax(doc: Doc) -> None:
    """ID 문법 위반과 고아 강화 항목."""
    base: set[str] = set()
    enh: list[tuple[int, str, str]] = []
    bad: dict[str, list[int]] = {}
    bad_single: dict[str, list[int]] = {}

    for n, l in body_lines(doc):
        for m in RX_ID_OK.finditer(l):
            pre, dom, num, sub = m.groups()
            if pre in ID_IGNORE_PREFIX:
                continue
            root = f"{pre}-{dom}-{num}"
            if sub:
                enh.append((n, m.group(0), root))
            else:
                base.add(root)

        for m in RX_ID_LOOSE.finditer(l):
            whole = m.group(0)
            if m.group(1) in ID_IGNORE_PREFIX or RX_ID_OK.match(l, m.start()):
                continue
            dom = m.group(2)
            if len(dom) == 1 and dom.isupper():
                bad_single.setdefault(whole, []).append(n)
            else:
                bad.setdefault(whole, []).append(n)

    if bad_single:
        lines = [n for ns in bad_single.values() for n in ns]
        shown = ", ".join(sorted(bad_single)[:SAMPLE_LIMIT])
        doc.add_agg("ID-SYNTAX", "error", lines,
                    f"도메인 코드가 1글자입니다 — {len(bad_single)}종 ({shown} …)",
                    "도메인 코드는 영문 명칭 머리글자 2글자입니다(최소권한 → LP, "
                    "계정관리 → AC). 1글자 체계는 국가 망 보안체계 초안이 쓰다가 "
                    "2글자로 바뀐 형태이므로 새 문서에는 쓰지 마세요.")
    if bad:
        lines = [n for ns in bad.values() for n in ns]
        shown = ", ".join(sorted(bad)[:SAMPLE_LIMIT])
        doc.add_agg("ID-SYNTAX", "error", lines,
                    f"통제항목 ID 문법에서 벗어났습니다 — {len(bad)}종 ({shown})",
                    "<접두사>-<도메인 2글자>-<번호> / -<번호>(<강화번호>) / -M<번호> "
                    "형태만 씁니다.")

    for n, cid, root in enh:
        if root not in base:
            doc.add("ID-ORPHAN", "error", n,
                    f"강화 항목 {cid} 의 모항목 {root} 이 문서에 없습니다",
                    "강화 항목은 모항목 없이 존재할 수 없습니다. 모항목을 추가하거나 "
                    "이 항목을 기본 항목으로 올리세요.")


def check_grade_gap(doc: Doc) -> None:
    """등급은 C ⊃ S ⊃ O 포함 관계. ● 분포는 C 부터 연속이어야 한다."""
    rows = control_rows(doc)
    if not rows:
        return

    gaps: list[tuple[int, str, str]] = []
    empty: list[tuple[int, str]] = []
    checked = 0

    for n, cells, cid, idx in rows:
        zone = mark_zone(cells, idx)
        if len(zone) < 3:
            continue
        checked += 1
        if DOT not in zone:
            empty.append((n, cid))
            continue
        # ● 는 등급 구역의 앞에서부터 끊기지 않고 이어져야 한다
        first = zone.index(DOT)
        last = len(zone) - 1 - zone[::-1].index(DOT)
        if any(c != DOT for c in zone[first:last + 1]) or first != 0:
            shown = "".join("●" if c == DOT else "·" for c in zone)
            gaps.append((n, cid, shown))

    if gaps:
        ids = ", ".join(f"{cid}({shown})" for _, cid, shown in gaps[:SAMPLE_LIMIT])
        doc.add_agg("GRADE-GAP", "error", [n for n, _, _ in gaps],
                    f"등급 표시가 끊긴 항목이 있습니다 — {ids}",
                    "등급은 기밀 C ⊃ 민감 S ⊃ 공개 O 포함 관계입니다. ● 는 C 부터 "
                    "연속으로 찍혀야 하고, S 나 O 만 단독으로 요구되는 항목은 "
                    "논리적으로 존재할 수 없습니다.")

    if not empty:
        return
    # 등급이 빈 행이 대부분이면 항목의 문제가 아니라 표(또는 변환)의 문제다.
    if checked and len(empty) > checked * 0.3:
        doc.add("GRADE-UNREADABLE", "info", empty[0][0],
                f"통제항목 {checked}행 중 {len(empty)}행에 등급 표시가 없어 "
                f"등급 검사를 신뢰할 수 없습니다",
                "등급 칸이 비어 보이는 것이 대부분이면 표 구조부터 보세요. "
                "병합 셀이 있으면 열이 밀려 ● 가 다른 칸으로 들어갑니다. "
                "병합 셀을 쓰지 말고 C/S/O 를 세 칸으로 두세요.")
        return
    ids = ", ".join(cid for _, cid in empty[:SAMPLE_LIMIT])
    doc.add_agg("GRADE-EMPTY", "warn", [n for n, _ in empty],
                f"요구 등급이 하나도 표시되지 않은 항목이 있습니다 — {ids}",
                "어느 등급에서도 요구되지 않는 항목은 체계에 둘 이유가 없습니다.")


# 본문이 적어 둔 등급별 요구 항목 수. 표 행과 문장 두 형태를 본다.
RX_CNT_ROW = re.compile(
    r"^\s*\|\s*(기밀|민감|공개)\s*\(\s*[CSO]\s*\)\s*\|\s*(\d{1,4})\s*\|"
)
RX_CNT_SENT = re.compile(
    r"기밀\s*(\d{1,4})\s*[,·]\s*민감\s*(\d{1,4})\s*[,·]\s*공개\s*(\d{1,4})"
)


def check_grade_count(doc: Doc) -> None:
    """등급별 요구 항목 수를 적어 두었으면 실제 ● 개수와 맞는지.

    통제항목을 더하거나 빼면 본문의 수치, 체크리스트, 대응표가 함께 밀린다.
    손으로 맞추면 반드시 어긋나므로 기계가 본다.
    """
    rows = control_rows(doc)
    if not rows:
        return
    act = {"기밀": 0, "민감": 0, "공개": 0}
    checked = 0
    for _, cells, _, idx in rows:
        zone = mark_zone(cells, idx)
        if len(zone) < 3:
            continue
        checked += 1
        for key, cell in zip(("기밀", "민감", "공개"), zone[:3]):
            if cell == DOT:
                act[key] += 1
    if checked < 10:
        return

    said: dict[str, list[tuple[int, int]]] = {"기밀": [], "민감": [], "공개": []}
    for n, l in body_lines(doc):
        m = RX_CNT_ROW.match(l)
        if m:
            said[m.group(1)].append((n, int(m.group(2))))
            continue
        m = RX_CNT_SENT.search(l)
        if m:
            for key, g in zip(("기밀", "민감", "공개"), m.groups()):
                said[key].append((n, int(g)))
    bad: list[tuple[int, str, int, int]] = []
    for key, items in said.items():
        for n, v in items:
            if v != act[key]:
                bad.append((n, key, v, act[key]))
    if not bad:
        return
    shown = ", ".join(f"{k} {v}→{a}" for _, k, v, a in bad[:SAMPLE_LIMIT])
    doc.add_agg("GRADE-COUNT", "warn", [n for n, _, _, _ in bad],
                f"적어 둔 등급별 요구 항목 수가 실제 ● 개수와 다릅니다 — {shown}",
                f"실제 집계는 기밀 {act['기밀']} · 민감 {act['민감']} · "
                f"공개 {act['공개']} 입니다(통제항목 {checked}행 기준). 통제항목을 "
                "더하거나 빼면 본문 수치·체크리스트·대응표가 함께 밀립니다. "
                "부록은 본문에서 생성하는 편이 안전합니다.")


def check_vague_cycle(doc: Doc) -> None:
    """주기 없는 통제는 점검할 수 없다."""
    hits = [n for n, l in body_lines(doc)
            if RX_VAGUE_CYCLE.search(l) and not CYCLE_NEAR.search(l)]
    doc.add_agg("PERIOD-VAGUE", "warn", hits,
                "주기를 '정기적으로' 류로만 적었습니다",
                "하한을 명시하세요 — '연1회 이상', '분기 1회 이상'. 주기가 없으면 "
                "이행 여부를 확인할 수 없습니다. 하한을 정할 근거가 없다면 그 통제는 "
                "아직 요구사항이 아니라 권고입니다.")


def check_style(doc: Doc) -> None:
    """발행본 문체에서 벗어난 표현과 표기.

    실무 안내서(경어체)는 친근한 말이 자연스러우므로 비유 표현 검사에서 뺀다.
    """
    if doc.genre != "manual":
        for rx, better in RX_FIGURATIVE:
            hits = [n for n, l in body_lines(doc) if rx.search(unquoted(l))]
            if hits:
                doc.add_agg("FIGURATIVE", "warn", hits,
                            "발행본에 드문 비유적·구어적 표현입니다",
                            "'%s' 처럼 상태나 영향을 그대로 적으세요. "
                            "코퍼스 20종에 이 표현은 없습니다." % better)

    doc.add_agg("MONEY-SPACE", "warn",
                [n for n, l in body_lines(doc) if RX_MONEY.search(unquoted(l))],
                "금액 단위 '원' 을 앞말에 붙였습니다",
                "단위 명사는 띄어 씁니다 — '5천만원' 이 아니라 '5천만 원'.")

    doc.add_agg("MIDDOT-SPACE", "info",
                [n for n, l in body_lines(doc) if RX_MIDDOT_SPACE.search(unquoted(l))],
                "가운뎃점 뒤에 공백이 있습니다",
                "'휴대형· 부착거치형' 이 아니라 '휴대형·부착거치형' 입니다.")

    # 'N 가지' 를 선언하고 그보다 큰 서수를 쓴 곳 — 문단 안에서 본다
    bad = []
    declared = 0
    for n, l in body_lines(doc):
        m = RX_COUNT_DECL.search(l)
        if m:
            declared = COUNT_WORD.get(m.group(1), 0)
            continue
        if not declared:
            continue
        for om in RX_ORDINAL.finditer(l):
            if ORD_WORD.get(om.group(1), 0) > declared:
                bad.append(n)
                declared = 0
                break
    doc.add_agg("COUNT-MISMATCH", "warn", bad,
                "'N 가지' 라고 적고 그보다 많이 늘어놓았습니다",
                "선언한 수와 실제 항목 수를 맞추세요.")


def check_id_order(doc: Doc) -> None:
    """한 표 안에서 통제항목 ID 번호가 뒤섞인 곳.

    일부러 업무 순서로 배치했을 수 있으므로 참고로만 알린다.
    """
    bad = []
    run: list = []
    start = 0
    for n, l in body_lines(doc):
        ids = RX_ID_OK.findall(l) if "RX_ID_OK" in globals() else []
        m = re.match(r"^\|\s*([A-Z][A-Z0-9]{1,7}-[A-Z]{2})-(\d{1,3})", l.strip())
        if m:
            if not run:
                start = n
            run.append((m.group(1), int(m.group(2))))
            continue
        if len(run) >= 3:
            dom = run[0][0]
            nums = [v for d, v in run if d == dom]
            if len(nums) >= 3 and nums != sorted(nums):
                bad.append(start)
        run = []
    if len(run) >= 3:
        dom = run[0][0]
        nums = [v for d, v in run if d == dom]
        if len(nums) >= 3 and nums != sorted(nums):
            bad.append(start)
    doc.add_agg("ID-ORDER", "info", bad,
                "표 안에서 통제항목 번호가 오름차순이 아닙니다",
                "업무 순서로 일부러 배치했다면 그대로 두세요. "
                "아니면 행 순서를 번호에 맞추는 편이 찾기 쉽습니다.")


def check_notation(doc: Doc) -> None:
    """꺾쇠·캡션·가운뎃점 표기의 혼용."""
    sq = [n for n, l in body_lines(doc) if "｢" in l]      # ｢
    an = [n for n, l in body_lines(doc) if "「" in l]      # 「
    if sq and an:
        doc.add_agg("BRACKET-MIX", "warn", sq if len(sq) <= len(an) else an,
                    f"법령 꺾쇠가 섞였습니다 — ｢ ｣ {len(sq)}줄 / 「 」 {len(an)}줄",
                    "하나로 통일하세요. 정부 간행물의 관행은 ｢ ｣ 입니다.")

    cs = [n for n, l in body_lines(doc) if RX_CAPTION_SQ.search(l)]
    ca = [n for n, l in body_lines(doc) if RX_CAPTION_AN.search(l)]
    if cs and ca:
        doc.add_agg("CAPTION-MIX", "warn", cs if len(cs) <= len(ca) else ca,
                    f"표·그림 캡션이 섞였습니다 — [표 N] {len(cs)}줄 / <표 N> {len(ca)}줄",
                    "하나로 통일하세요. 코퍼스에서는 [표 N] 이 우세합니다.")

    doc.add_agg("PARTICLE-SPACE", "warn",
                [n for n, l in body_lines(doc) if RX_PARTICLE_SPACE.search(l)],
                "조사를 앞말에서 띄웠습니다",
                "조사는 앞말에 붙여 씁니다 — 'PDF 까지' 가 아니라 'PDF까지'. "
                "코퍼스는 58 대 1 로 붙여 씁니다.")

    doc.add_agg("MIDDOT", "warn",
                [n for n, l in body_lines(doc) if RX_MIDDOT_BAD.search(unquoted(l))],
                "가운뎃점에 한글 호환 자모 ㆍ(U+318D)가 쓰였습니다",
                "·(U+00B7)로 바꾸세요. ㆍ 는 검색·정렬이 깨집니다.")

    doc.add_agg("LOCATION-REF", "warn",
                [n for n, l in body_lines(doc)
                 if RX_LOCATION_REF.search(unquoted(l))],
                "표·그림을 위치로 가리켰습니다",
                "번호로 가리키세요 — '[표 3-1]과 같이'. 조판이 바뀌면 '아래 표'는 "
                "틀린 말이 됩니다.")


def check_headings(doc: Doc) -> None:
    """제목 레벨 건너뛰기와 과도한 깊이."""
    skips: list[int] = []
    deep: list[int] = []
    max_lv = 0
    prev = 0
    for n, l in body_lines(doc):
        m = HEADING_RX.match(l)
        if not m:
            continue
        lv = len(m.group(1))
        if prev and lv > prev + 1:
            skips.append(n)
        if lv >= 5:
            deep.append(n)
            max_lv = max(max_lv, lv)
        prev = lv
    doc.add_agg("HEADING-SKIP", "warn", skips,
                "제목 레벨이 한 단계 이상 건너뛰었습니다",
                "한 단계씩 내려가세요. 중간 레벨이 비면 목차가 어긋납니다.")
    doc.add_agg("HEADING-DEPTH", "info", deep,
                f"제목 깊이가 {max_lv}단까지 내려갑니다",
                "코퍼스의 실질 깊이는 3단(제N장 / 제N절 / N.)입니다. 4단(가.)까지가 "
                "보통이고 5단 이상은 드뭅니다. 더 깊어지면 절을 나누세요.")


KOR_ORD = "가나다라마바사아자차카타파하"
# `3.1` 같은 2단 번호(실무 안내서가 쓰는 형태)는 `3.` 으로 세지 않는다.
RX_NUM_HEAD = re.compile(
    r"^(#{1,6})\s+(?:제\s?(\d{1,2})\s?(장|절)|(\d{1,2})\.(?!\d)|([가-힣])\.|(\d{1,2})\))\s*\S"
)


def check_heading_seq(doc: Doc) -> None:
    """제목 번호가 1부터 끊기지 않고 이어지는지.

    `N.` 레벨의 번호 중복·누락은 린터가 아니면 찾기 어렵다. 상위 제목이 나오면
    하위 레벨의 기대 번호를 1로 되돌린다.
    """
    expect: dict[tuple[int, str], int] = {}
    bad: list[tuple[int, str, int, int]] = []
    for n, l in body_lines(doc):
        h = HEADING_RX.match(l)
        if not h:
            continue
        m = RX_NUM_HEAD.match(l)
        # 번호가 없는 제목(`부록 1`, `결론`)도 상위 제목이므로 하위 번호를
        # 초기화해야 한다. 이것을 빼면 부록마다 번호가 이어지는 것으로 센다.
        if not m:
            for k in [k for k in expect if k[0] > len(h.group(1))]:
                del expect[k]
            continue
        lv = len(m.group(1))
        if m.group(2):
            kind, got = m.group(3), int(m.group(2))
        elif m.group(4):
            kind, got = "num", int(m.group(4))
        elif m.group(5):
            if m.group(5) not in KOR_ORD:
                continue
            kind, got = "kor", KOR_ORD.index(m.group(5)) + 1
        else:
            kind, got = "paren", int(m.group(6))
        key = (lv, kind)
        for k in list(expect):
            if k[0] > lv:
                del expect[k]
        want = expect.get(key, 1)
        # 번호가 1로 돌아가는 것은 새 묶음의 시작으로 본다. 상위 제목이 빠진
        # 발췌본·변환물에서 흔하고, 그것까지 지적하면 쓸 수 없는 검사가 된다.
        if got == 1:
            expect[key] = 2
            continue
        if got != want:
            bad.append((n, kind, got, want))
        expect[key] = got + 1
    if not bad:
        return
    # 번호가 뒤로 가는 것(중복·역행)과 건너뛴 것을 나눠 보고한다. 둘 다 참고
    # 등급이다 — PDF 에서 변환한 원고에서는 본문 문장이 제목으로 바뀌거나 글자가
    # 깨져 번호가 어긋나는 일이 흔해서, 경고로 두면 변환물에서 신호가 묻힌다.
    back = [x for x in bad if x[2] < x[3]]
    skip = [x for x in bad if x[2] > x[3]]
    if back:
        shown = ", ".join(f"{g}(기대 {w})" for _, _, g, w in back[:SAMPLE_LIMIT])
        doc.add_agg("HEADING-SEQ", "info", [n for n, _, _, _ in back],
                    f"제목 번호가 뒤로 갔습니다 — {shown}",
                    "같은 번호를 두 번 쓰거나 번호가 거꾸로 간 것입니다. 절을 "
                    "끼워 넣거나 지울 때 생기며, 목차를 뽑으면 바로 드러납니다.")
    if skip:
        shown = ", ".join(f"{g}(기대 {w})" for _, _, g, w in skip[:SAMPLE_LIMIT])
        doc.add_agg("HEADING-GAP", "info", [n for n, _, _, _ in skip],
                    f"제목 번호를 건너뛰었습니다 — {shown}",
                    "번호를 하나씩 올리세요. 변환 과정에서 상위 제목이 빠졌거나 "
                    "글자가 깨진 원고에서도 나타나므로, 원본과 대조해 보세요.")


def check_checklist(doc: Doc) -> None:
    """본문 통제항목과 부록 점검표의 1:1 대응.

    본문 통제항목 표는 등급 칸이 붙어 셀이 6개 이상이고, 부록의 점검표·대응표는
    그보다 짧다. 그 차이로 둘을 가른 뒤 ID 집합을 비교한다.
    """
    body: set[str] = set()
    ref: dict[str, list[int]] = {}
    for n, l in body_lines(doc):
        if not TABLE_ROW.match(l):
            continue
        cells = cells_of(l)
        for c in cells:
            m = RX_ID_OK.fullmatch(c)
            if not m or m.group(1) in ID_IGNORE_PREFIX:
                continue
            # 본문 통제항목 표는 등급 칸(C/S/O)이 붙어 셀이 6개 이상이고,
            # 부록의 점검표·대응표는 그보다 짧다.
            if len(cells) >= 6:
                body.add(c)
            else:
                ref.setdefault(c, []).append(n)
            break
    if not body or not ref:
        return
    extra = {c: ns for c, ns in ref.items() if c not in body}
    if extra:
        shown = ", ".join(sorted(extra)[:SAMPLE_LIMIT])
        doc.add_agg("CHECKLIST-EXTRA", "error",
                    [ns[0] for ns in extra.values()],
                    f"본문에 없는 통제항목이 부록에 있습니다 — {len(extra)}종 ({shown})",
                    "부록의 점검표는 본문 통제항목을 뒤집은 것이므로 본문에 없는 "
                    "항목을 둘 수 없습니다. 본문에 추가하거나 부록에서 빼세요.")
    missing = sorted(body - set(ref))
    if missing:
        shown = ", ".join(missing[:SAMPLE_LIMIT])
        doc.add_agg("CHECKLIST-MISS", "warn", [control_rows(doc)[0][0]],
                    f"부록 점검표에서 빠진 통제항목이 있습니다 — "
                    f"{len(missing)}종 ({shown})",
                    "체크리스트는 본문 대책과 1:1로 대응해야 합니다. 빠진 항목은 "
                    "점검되지 않으므로 이행 여부를 확인할 수 없습니다.")


def check_figures(doc: Doc) -> None:
    """표는 많은데 그림이 없는 문서."""
    tb = len(RX_CAPTION_SQ.findall(doc.text)) + len(RX_CAPTION_AN.findall(doc.text))
    fg = len(re.findall(r"\[그림\s?[\d\-–.]+\]|<그림\s?[\d\-–.]+>", doc.text))
    if tb >= 10 and fg == 0:
        doc.add("FIGURE-NONE", "info", 1,
                f"표 {tb}개에 그림이 하나도 없습니다",
                "구조·흐름·경계는 표보다 그림이 빠릅니다. 대상 모델의 구역도, "
                "공격 경로도, 판정 흐름도가 코퍼스에서 가장 흔한 세 가지입니다.")


def check_terms(doc: Doc) -> None:
    """같은 개념의 다른 표현이 함께 쓰였는지."""
    for prefer, others in TERM_PAIRS:
        pn = [n for n, l in body_lines(doc) if prefer in l]
        if not pn:
            continue
        for other in others:
            on = [n for n, l in body_lines(doc) if other in l and prefer not in l]
            if not on:
                continue
            doc.add_agg("TERM-MIX", "info", on,
                        f"'{other}'({len(on)}줄) 와 '{prefer}'({len(pn)}줄) 가 "
                        f"함께 쓰였습니다",
                        f"코퍼스는 '{prefer}' 를 씁니다. 하나로 통일하세요.")


def check_abbr(doc: Doc) -> None:
    """반복되는 약어의 첫 등장 풀네임 병기 누락."""
    intro = set(re.findall(r"\b([A-Z]{2,6})\s?\(", doc.text))
    intro |= {m.group(2) for m in re.finditer(r"\(([^)]{4,60}),\s?([A-Z]{2,6})\)", doc.text)}
    used: dict[str, list[int]] = {}
    for n, l in body_lines(doc):
        if TABLE_ROW.match(l):
            continue
        # 통제항목 ID·점검항목 번호·권고 번호 안의 2~6글자 토큰은 약어가 아니다
        l = RX_IDLIKE.sub(" ", l)
        for ab in re.findall(r"(?<![A-Za-z])([A-Z]{2,6})(?![A-Za-z])", l):
            used.setdefault(ab, []).append(n)
    missing = {ab: ns for ab, ns in used.items()
               if ab not in intro and ab not in ID_IGNORE_PREFIX and len(ns) >= 3}
    if not missing:
        return
    order = sorted(missing, key=lambda a: -len(missing[a]))
    shown = ", ".join(f"{a}({len(missing[a])}회)" for a in order[:SAMPLE_LIMIT])
    doc.add_agg("ABBR-NOINTRO", "info",
                [ns[0] for ns in missing.values()],
                f"풀네임 병기 없이 반복되는 약어 {len(missing)}종 — {shown}",
                "첫 등장에 한 번만 병기하세요 — ABBR(Full Name) 또는 국문명(ABBR). "
                "약어가 10개를 넘으면 부록에 약어표를 두세요.")


CHECKS = {
    "ENDING-MIX": check_ending_mix,
    "HONORIFIC": check_honorific,
    "CONTROL-OBLIGATION": check_control_obligation,
    "ID-SYNTAX": check_id_syntax,
    "GRADE-GAP": check_grade_gap,
    "PERIOD-VAGUE": check_vague_cycle,
    "NOTATION": check_notation,
    "HEADINGS": check_headings,
    "TERM-MIX": check_terms,
    "ABBR-NOINTRO": check_abbr,
    "HEADING-SEQ": check_heading_seq,
    "CHECKLIST": check_checklist,
    "FIGURE-NONE": check_figures,
    "GRADE-COUNT": check_grade_count,
    "STYLE": check_style,
    "ID-ORDER": check_id_order,
}

# 한 검사가 여러 코드를 낼 수 있으므로 --only 용 별칭을 둔다
ALIAS = {
    "ID-ORPHAN": "ID-SYNTAX",
    "GRADE-EMPTY": "GRADE-GAP",
    "GRADE-UNREADABLE": "GRADE-GAP",
    "BRACKET-MIX": "NOTATION",
    "CAPTION-MIX": "NOTATION",
    "MIDDOT": "NOTATION",
    "LOCATION-REF": "NOTATION",
    "FIGURATIVE": "STYLE",
    "MONEY-SPACE": "STYLE",
    "MIDDOT-SPACE": "STYLE",
    "COUNT-MISMATCH": "STYLE",
    "PARTICLE-SPACE": "NOTATION",
    "HEADING-SKIP": "HEADINGS",
    "HEADING-DEPTH": "HEADINGS",
    "HEADING-GAP": "HEADING-SEQ",
    "CHECKLIST-EXTRA": "CHECKLIST",
    "CHECKLIST-MISS": "CHECKLIST",
}


# ── 장르 추정 ─────────────────────────────────────────────────────────────────


def guess_genre(text: str) -> str:
    # 행머리의 조 제목(`제4조(적용 범위)`)은 조문 체계의 확실한 신호다.
    if re.search(r"^\s*제\s?\d+조\s*\(", text, re.M):
        return "ordinance"
    hon = len(RX_HONORIFIC.findall(text))
    plain = len(RX_PLAIN.findall(text))
    if hon > plain:
        return "manual"
    # `제N절` 제목 체계는 분야별 가이드라인의 신호다. 이것이 있으면 조문 인용이
    # 많거나(시험 집필에서 164회) 통제항목 ID 가 많아도 가이드라인으로 본다.
    # 근거 법령을 성실히 인용하고 통제항목 체계를 함께 쓰는 가이드라인이
    # 법령형 지침이나 통제항목 체계 문서로 오판되는 것을 막는다.
    if re.search(r"^#+\s*제\s?\d+절", text, re.M):
        return "guideline"
    if len(re.findall(r"제\s?\d+조", text)) > 20:
        return "ordinance"
    if len(RX_ID_OK.findall(text)) > 20:
        return "control"
    return "guideline"


# ── 실행 ──────────────────────────────────────────────────────────────────────

SEV_ORDER = {"error": 0, "warn": 1, "info": 2}
SEV_LABEL = {"error": "오류", "warn": "경고", "info": "참고"}


def lint(path: Path, genre: str | None, only: set[str] | None) -> Doc:
    text = path.read_text(encoding="utf-8")
    doc = Doc(path=path, lines=text.splitlines(), genre=genre or guess_genre(text), text=text)
    for name, fn in CHECKS.items():
        if only and name not in only:
            continue
        fn(doc)
    doc.findings.sort(key=lambda f: (SEV_ORDER[f.severity], f.line, f.code))
    return doc


def render(doc: Doc, quiet: bool) -> None:
    shown = [f for f in doc.findings if not (quiet and f.severity != "error")]
    counts = {s: sum(1 for f in doc.findings if f.severity == s)
              for s in ("error", "warn", "info")}
    print(f"\n{doc.path}  [장르: {doc.genre}]  "
          f"오류 {counts['error']} · 경고 {counts['warn']} · 참고 {counts['info']}")
    if not shown:
        print("  지적할 것이 없습니다.")
        return
    for f in shown:
        where = f"{doc.path}:{f.line}"
        tail = ""
        if f.count > 1:
            more = f", … 총 {f.count}곳" if f.count > len(f.samples) else ""
            tail = f"  ({f.count}곳 — 줄 {', '.join(map(str, f.samples))}{more})"
        print(f"  {where}  {SEV_LABEL[f.severity]}  [{f.code}] {f.message}{tail}")
        if f.hint:
            print(f"      → {f.hint}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="사이버보안 가이드라인 원고 검사")
    ap.add_argument("paths", nargs="+", help="검사할 Markdown 파일")
    ap.add_argument("--genre", choices=["guideline", "control", "ordinance", "manual"],
                    help="장르를 명시한다 (생략하면 추정)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--only", help="검사 코드를 쉼표로 지정")
    ap.add_argument("--quiet", action="store_true", help="오류만 출력")
    args = ap.parse_args()

    only = None
    if args.only:
        only = {ALIAS.get(c.strip().upper(), c.strip().upper()) for c in args.only.split(",")}
        unknown = only - set(CHECKS)
        if unknown:
            print(f"알 수 없는 검사 코드: {', '.join(sorted(unknown))}", file=sys.stderr)
            print(f"가능한 코드: {', '.join(sorted(set(CHECKS) | set(ALIAS)))}", file=sys.stderr)
            return 2

    files: list[Path] = []
    for p in args.paths:
        hit = sorted(Path().glob(p)) if any(c in p for c in "*?[") else [Path(p)]
        files.extend(hit)
    files = [f for f in files if f.is_file()]
    if not files:
        print("검사할 파일이 없습니다.", file=sys.stderr)
        return 2

    docs = [lint(f, args.genre, only) for f in files]

    if args.format == "json":
        print(json.dumps(
            [{"file": str(d.path), "genre": d.genre,
              "findings": [vars(f) for f in d.findings]} for d in docs],
            ensure_ascii=False, indent=1))
    else:
        for d in docs:
            render(d, args.quiet)

    return 1 if any(f.severity == "error" for d in docs for f in d.findings) else 0


if __name__ == "__main__":
    sys.exit(main())
