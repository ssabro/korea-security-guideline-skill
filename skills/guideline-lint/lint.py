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
    # 대문자를 붙임표로 이은 겹낱말은 **이름**이다 — 검사 코드 `TERM-MIX`,
    # 도메인 묶음 `ACCESS-CONTROL`. 그 조각(`MIX`)을 약어로 세면 '풀네임을
    # 병기하라' 는 고칠 수 없는 지적이 나온다.
    r"|\b[A-Z]{2,}(?:-[A-Z]{2,})+\b"
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

# 항·호를 위치로 가리키는 것도 같다 — `아래 2. 참조`. 코퍼스 24종에
# 이 꼴은 **한 번도 없다**(절·항을 뭉뚱그려 가리키는 `아래 절` 은
# 15종에 117회 나오므로 보지 않는다).
RX_LOCATION_REF = re.compile(
    r"(?:아래|위|다음|상기|하기)\s*(?:의\s*)?(?:표|그림|도표|그래프|\d+\s*(?:\.|항|호))")
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
    (r"몰려 있|몰린다", "집중되어 있다"),
    (r"다녀도|다닌다", "운용되더라도"),
    (r"버린다|버리고", "적용하지 않는다"),
    (r"넘어간다|넘어가면", "탈취될 수 있다"),
    (r"드러난다", "확인된다"),
    (r"낳는다|낳아", "가진다"),
    (r"걸린다", "적용된다·소요된다"),
    (r"을 타면|를 타면", "을 통해 배포되면"),
    (r"발판", "경유지"),
    # 권장 표현을 짧게 둔다. `해제할 수 없도록 설정하면` 은 길어서, 앞말이
    # 이미 `풀 수 없게` 인 자리에 넣으면 같은 말이 두 번 들어간다. 실제로
    # 원고에 `풀 수 없게 해제할 수 없도록 설정하면` 이 남았다.
    (r"잠그면|잠근다", "해제를 제한하면"),
    (r"풀리|풀면|푼다", "해제되면"),
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
# `N<단위>` 를 선언하고 쉼표로 늘어놓은 개수가 다른 곳
NUM_WORD = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7,
            "여덟": 8, "아홉": 9,
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9}
RX_NUM_UNIT = re.compile(
    r"(한|두|세|네|다섯|여섯|일곱|여덟|아홉|[2-9])\s*"
    r"(도메인|유형|구역|계층|영역|범주)"   # '개' '가지' 는 뺀다 — 오탐이 많다
    r"(?![월년간])")  # '6개월' 의 '6개' 를 선언으로 읽지 않는다

RX_MIDDOT_SPACE = re.compile(r"[가-힣A-Za-z0-9]·[ \t]+[가-힣A-Za-z0-9]")

# 긴 대시로 부연을 잇는 버릇. 코퍼스 20종은 1천 줄당 0.3회뿐이고(20종 중
# 2종만 쓴다) 가장 많이 쓴 문서도 9.3회다. 그보다 훨씬 잦으면 알린다.
RX_EM_DASH = re.compile("\u2014")
EM_DASH_PER_1000 = 15.0

RX_CAPTION_SQ = re.compile(r"\[(?:표|그림)\s?[\d\-–.]+\]")
RX_CAPTION_AN = re.compile(r"<(?:표|그림)\s?[\d\-–.]+>")

# 용어 혼용 — analysis/07-terminology.md
# ── 발간 전 검사에 쓰는 패턴 ──────────────────────────────────────────────

# 자리표시자. **코퍼스 24종에서 한 번도 나오지 않은 꼴만** 늘 지적한다.
PLACEHOLDER_ALWAYS = [
    (r"\(\s*(?:발행)?기관명\s*\)", "(기관명)"),
    (r"\(\s*(?:발간)?등록번호\s*\)", "(등록번호)"),
    (r"\bTBD\b", "TBD"),
    (r"\bTODO\b", "TODO"),
    (r"\bFIXME\b", "FIXME"),
    (r"\(\s*미정\s*\)", "(미정)"),
    (r"0000-00-00", "0000-00-00"),
    (r"\b000-0000\b", "000-0000"),
    (r"\bXX\b", "XX"),
    (r"□□", "□□"),
    (r"작성\s*예정", "작성 예정"),
    (r"\[(?:TODO|확인|보완|추가)\]", "[확인]"),
]
# ○○ · ×× · OOO · ____ 는 발행본도 쓴다 — 다만 **[예시] 와 양식 안에서만**
# 이다(24종 중 ○○ 1종 4회, OOO 3종 23회, ____ 3종 58회. 모두 질의서·
# 서식·예시 블록). 그래서 **실제 값이 들어가야 하는 앞붙이에서만** 본다.
PLACEHOLDER_FRONT = [
    (r"○○", "○○"),
    (r"××", "××"),
    (r"\bOOO\b", "OOO"),
    (r"_{4,}", "____"),
]
# 쓰지 않는 말 — `추후`(2종 8회) `확인 필요`(3종 6회) `(초안)`(2종 3회)
# `Draft`(7종 20회) `기입`(1종) 은 발행본이 실제로 쓴다. 자리표시자가 아니다.

RX_PLACEHOLDER_ALWAYS = [(re.compile(p), s) for p, s in PLACEHOLDER_ALWAYS]
RX_PLACEHOLDER_FRONT = [(re.compile(p), s) for p, s in PLACEHOLDER_FRONT]

# 앞붙이 — 실제 값이 들어가야 하는 구역
RX_HEAD_FRONT = re.compile(
    r"^#{1,3}\s*(?:발간\s*정보|문서\s*정보|문서\s*이력|개정\s*이력|판권)")
# 문서이력 — 이 문서가 무엇을 고쳤는지 적는 곳이라 수와 자료명이 섞인다
RX_HEAD_HIST = re.compile(r"^#{1,6}.*?(?:문서\s*이력|개정\s*이력|변경\s*이력)")
# 집필용 메모가 남기 쉬운 구역
RX_HEAD_NOTE = re.compile(
    r"^#{1,3}\s*(?:목\s*차|발간\s*정보|문서\s*정보|차\s*례)")
# 참고 자료 목록
RX_HEAD_REF = re.compile(
    r"^#{1,6}.*?(?:참고\s*문헌|참고\s*자료|인용\s*자료|근거\s*자료)")

# 문서명·자료명 인용. `outside_quote` 와 같은 꼴을 쓴다.
RX_DOCNAME = re.compile(r"[｢「]([^｣」]{2,60})[｣」]")

# 외부 자료의 수를 단정하는 말 — `112 개 항목`, `점검항목 98개`, `41개 전부`.
# `2건` `3종` 같은 맨 수는 보지 않는다 — 문서이력의 `인용 오류 2건 정정` 이
# 외부 자료의 항목 수로 잡혔다. **세는 대상이 함께 적혀 있어야** 단정이다.
RX_ASSERT_COUNT = re.compile(
    r"\d{1,4}\s*개\s*(?:항목|통제|요구사항|점검항목|조문|분류|전부)"
    r"|(?:항목|통제|요구사항|점검항목|조문|분류)\s*\d{1,4}\s*개"
    r"|\d{1,4}\s*개(?:를|의|이|가|는|와|과)?\s*(?:모두|전부|가운데|중)")

# 법령은 참고 문헌이 아니라 **근거 법령** 절에 적는다. 참고 자료 목록에
# 없다고 지적하면 모든 법령 인용이 걸린다.
RX_LAW_NAME = re.compile(
    r"(?:법|법률|시행령|시행규칙|규정|규칙|고시|훈령|예규|조례|지침)$")

# 접두사를 생략해 줄여 쓴 ID — `TID-105, 110, 118`, `SSDF-03·04·05`
RX_ID_ABBREV = re.compile(
    r"\b[A-Z][A-Z0-9]{1,7}-\d{1,3}(?:[·,]\s*\d{1,3}){2,}")

# 사례 서술의 근거. `출처:` 줄이거나 `(저자, 연도)` 꼴이면 근거가 있다.
RX_EVIDENCE = re.compile(r"출처|\([^)]{2,40},\s*\d{4}\)|[｢「][^｣」]{2,60}[｣」]")
# 사례임을 알리는 수치 — 비율·건수·대수
RX_CASE_NUM = re.compile(r"\d+(?:\.\d+)?\s*%|\d{1,5}\s*(?:건|대|곳|명)")
RX_YEAR = re.compile(r"(?:19|20)\d{2}\s*년")

# 파일 이름과 링크 대상은 약어가 아니다 — `[NOTICE](NOTICE)`, `SKILL.md`
RX_MD_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
RX_FILENAME = re.compile(
    r"\b[A-Za-z][A-Za-z0-9_.-]*\."
    r"(?:md|py|json|html|css|svg|png|pdf|txt|csv|ya?ml|toml|cfg|ini|sh|bat)\b")
FILE_WORDS = {"README", "LICENSE", "NOTICE", "ORIGIN", "SKILL", "CHANGELOG",
              "MEMORY", "CONTRIBUTING", "AUTHORS", "INSTALL", "MAKEFILE"}

# 외부 자료의 항목명 — `WS-06 자산 접근 제어` 처럼 ID 뒤에 이름이 붙은 것.
# 원문 그대로 적어야 하므로 용어 통일 대상이 아니다.
RX_EXT_ITEM = re.compile(r"^[A-Z][A-Z0-9]{1,7}-\d{1,3}(?:\(\d{1,2}\))?\s+\S")

# 머리표로 시작하는 소제목 — 발행본 24종 가운데 5종이 ■ 를, 5종이 ○ 를 쓴다
RX_MARK_HEAD = re.compile(r"^\s*([\u25a0\u25c6\u25cb\u25cf\u25a1\u203b])\s*(\S.*)$")

# 수량 단위는 앞말과 띄어 쓴다 — `연1회` → `연 1회`.
# 코퍼스는 띄움 20회(4종) · 붙임 11회(2종) 로 **띄움이 다수**이고, 한글
# 맞춤법도 관형사 뒤를 띄운다. 다만 붙여 쓴 발행본이 있어 참고로만 알린다.
RX_CYCLE_TIGHT = re.compile(r"(?<![0-9])(연|월|주|분기|반기|년|일)(\d+\s*회)")

# 문서이력 표의 버전과 일자
RX_HIST_ROW = re.compile(r"^\|\s*(\d+\.\d+)\s*\|\s*([\d.\s]{6,20})\|(.*)$")
# 발간 정보의 작성 기준일과 최종 수정일
RX_BASEDATE = re.compile(r"작성\s*기준일\s*\|\s*([\d.\s]{6,20})")
RX_LASTDATE = re.compile(r"최종\s*(?:수정|변경)일?\s*\|\s*([\d.\s]{6,20})")
# `변경 전 → 변경 후` 꼴의 기록
RX_ARROW_PAIR = re.compile(r"([^\s,(（]{2,20})\s*(?:→|->)\s*([^\s,)）]{2,20})")

# 원고가 끌어 쓰는 그림 파일
RX_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def ymd(s: str):
    """`2026. 11. 20.` 을 (2026, 11, 20) 으로. 못 읽으면 None."""
    nums = re.findall(r"\d+", s)
    if len(nums) < 3:
        return None
    y, m, d = (int(x) for x in nums[:3])
    return (y, m, d) if 1900 < y < 2200 and 1 <= m <= 12 and 1 <= d <= 31 else None


# ── 숫자 뒤 조사 ─────────────────────────────────────────────────────────
# 끝 자리 숫자를 **읽는 소리**가 조사를 정한다.
#   0 영 · 1 일 · 3 삼 · 6 육 · 7 칠 · 8 팔  → 받침 있음 → 은·이·을·과·으로
#   2 이 · 4 사 · 5 오 · 9 구               → 받침 없음 → 는·가·를·와·로
# 코퍼스 24종에서 249곳을 재어 **227곳이 규칙대로**였다(91.2%). 틀린 22곳은
# `[표 8]는` 처럼 실제 오류이거나 변환 과정의 잡음이다. 발행본도 열에 한 번
# 틀리므로 참고로만 알린다.
NUM_CODA = {'0': 1, '1': 1, '2': 0, '3': 1, '4': 0, '5': 0,
            '6': 1, '7': 1, '8': 1, '9': 0}
# `로/으로` 만 예외다. **받침이 ㄹ이면 `로`** 를 쓴다(서울로, 1일로). 숫자
# 1(일)·7(칠)·8(팔) 이 ㄹ받침이라 `으로` 가 아니라 `로` 다. 이걸 빼먹고
# `1:1로` 를 `1:1으로` 로 고치라고 한 적이 있다.
NUM_RIEUL = {'1', '7', '8'}
# (받침 있을 때, 받침 없을 때)
PARTICLE_PAIRS = [('은', '는'), ('이', '가'), ('을', '를'), ('과', '와')]
# 숫자나 `숫자]` 에 **붙여 쓴** 조사만 본다. 띄어 쓴 것은 다른 말일 수 있다
# (`4 이상`, `3 와트`).
RX_NUM_PARTICLE = re.compile(
    r"(\d)(\]?)(은|는|이|가|을|를|과|와|으로|로)(?![가-힣])")
# 괄호가 **통제 ID 를 감쌀 때만** 본다. `권장한다`(45)와 의 `와` 는 숫자가
# 아니라 앞말에 붙으므로, 붙임표가 있는 ID 꼴로 한정한다.
RX_ID_PARTICLE = re.compile(
    r"\([A-Z][A-Z0-9]*-[^)]*?(\d)\)()"
    r"(은|는|이|가|을|를|과|와|으로|로)(?![가-힣])")

# ── 교차참조 ─────────────────────────────────────────────────────────────

# 원고가 자기 안의 자리를 가리키는 꼴
RX_REF_SEC = re.compile(
    r"제\s?(\d+)\s?장\s+제\s?(\d+)\s?절(?:\s+(\d+)\s?\.)?"
    r"|(?<![가-힣])제\s?(\d+)\s?절\s+(\d+)\s?\.")
RX_REF_APPX = re.compile(r"부록\s?(\d+)")
RX_REF_CAP = re.compile(r"\[(표|그림)\s?(\d+)-(\d+)\]")

# 제목 — `# 제N장`, `## 제M절`, `### K.`
RX_H_CHAP = re.compile(r"^#\s+제\s?(\d+)\s?장")
RX_H_SECT = re.compile(r"^##\s+제\s?(\d+)\s?절")
RX_H_SUB = re.compile(r"^###\s+(\d+)\s?\.")
RX_H_APPX = re.compile(r"^##\s+부록\s?(\d+)")
# 캡션은 줄 머리에서 시작하고 닫는 괄호 뒤에 공백이 온다. 본문 속의 참조
# `[그림 3-1]의 ④단계` 와 가른다.
RX_CAPTION = re.compile(r"^\[(표|그림)\s?(\d+)-(\d+)\]\s+\S")

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


def head_level(line: str) -> int:
    """`###` 의 깊이. 제목이 아니면 0."""
    m = re.match(r"^(#{1,6})\s", line)
    return len(m.group(1)) if m else 0


def zones_of(doc: Doc, head_rx) -> list[tuple[int, int]]:
    """제목이 `head_rx` 에 맞는 절의 (시작줄, 끝줄) 목록.

    같은 깊이 이상의 다음 제목에서 끊는다. 앞붙이(목차·발간 정보)처럼
    **본문과 성격이 다른 구역**만 보는 검사에 쓴다.
    """
    out: list[tuple[int, int]] = []
    start = lv = 0
    for i, l in enumerate(doc.lines, 1):
        h = head_level(l)
        if start and h and h <= lv:
            out.append((start, i - 1))
            start = lv = 0
        if not start and h and head_rx.match(l):
            start, lv = i, h
    if start:
        out.append((start, len(doc.lines)))
    return out


def in_zones(n: int, zones: list[tuple[int, int]]) -> bool:
    return any(a <= n <= b for a, b in zones)


def docnames(text: str) -> set[str]:
    """꺾쇠로 인용한 문서명. 공백을 지워 비교한다."""
    return {re.sub(r"\s+", "", m) for m in RX_DOCNAME.findall(text)}


def term_line(line: str) -> str:
    """용어 혼용을 볼 때 쓰는 줄.

    **외부 자료의 제목과 항목명은 원문 그대로 적어야 하므로 지운다.** 부록의
    대응표에 선행 자료의 항목명 `WS-06 자산 접근 제어` 를 옮겼더니 '접근 제어'
    와 '접근통제' 가 섞였다고 나왔다 — 고칠 수 없는 것을 지적한 것이다.
    """
    s = outside_quote(unquoted(line))
    if TABLE_ROW.match(line):
        s = " | ".join(c for c in cells_of(s) if not RX_EXT_ITEM.match(c))
    return s


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

    # 산문 줄만 센다. 표 셀의 `문서 — 자산 등록부`, 캡션의 `— 도입·구축 시`
    # 는 문장을 잇는 것이 아니라 이름표를 가르는 것이라 세면 안 된다.
    body = [(n, l) for n, l in body_lines(doc)
            if l.strip() and not l.lstrip().startswith("|")
            and not l.lstrip().startswith("#")
            and not re.match(r"^\[(표|그림)", l.strip())]
    nonblank = [l for _, l in body]
    hits = [n for n, l in body if RX_EM_DASH.search(l)]
    if nonblank and len(hits) / len(nonblank) * 1000 > EM_DASH_PER_1000:
        doc.add_agg("EM-DASH", "warn", hits,
                    "긴 대시(—)로 부연을 잇는 문장이 %d줄입니다 "
                    "(1천 줄당 %.0f회)" % (len(hits), len(hits) / len(nonblank) * 1000),
                    "코퍼스 20종은 1천 줄당 0.3회입니다. 부연은 쉼표로 잇거나 "
                    "문장을 나누세요.")

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

    # 선언한 수와 쉼표로 늘어놓은 개수가 다른 곳. 열거를 세는 일은 어림이므로
    # 짧은 항목이 둘 이상 이어질 때만 센다.
    off = []
    for n, l in body_lines(doc):
        m = RX_NUM_UNIT.search(l)
        if not m:
            continue
        want = NUM_WORD.get(m.group(1), 0)
        if want < 2:
            continue
        tail = l[m.end():]
        for seg in re.findall(r"\*\*([^*]{4,160})\*\*", tail):   # 굵은 글씨 열거만
            items = [x.strip() for x in seg.split(",")]
            if len(items) < 3:
                continue
            if all(0 < len(x) <= 30 for x in items) and len(items) != want:
                off.append(n)
                break
    doc.add_agg("COUNT-LIST", "warn", off,
                "선언한 수와 늘어놓은 항목 수가 다릅니다",
                "'세 도메인' 이라 적고 다섯을 늘어놓으면 읽는 사람이 헷갈립니다.")


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
                "표·그림·항을 위치로 가리켰습니다",
                "번호로 가리키세요 — '[표 3-1]과 같이', '제1장 제3절 4.'. "
                "조판이 바뀌면 '아래 표'와 '아래 2.'는 틀린 말이 됩니다.")


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
    masked = [(n, term_line(l)) for n, l in body_lines(doc)]
    for prefer, others in TERM_PAIRS:
        pn = [n for n, l in masked if prefer in l]
        if not pn:
            continue
        for other in others:
            on = [n for n, l in masked if other in l and prefer not in l]
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
        # 파일 이름과 링크 대상도 약어가 아니다 — `[NOTICE](NOTICE)` 가
        # NOTICE 를 두 번, `SKILL.md` 가 SKILL 을 한 번 세게 만들었다.
        l = RX_FILENAME.sub(" ", RX_MD_LINK.sub(" ", l))
        for ab in re.findall(r"(?<![A-Za-z])([A-Z]{2,6})(?![A-Za-z])", l):
            used.setdefault(ab, []).append(n)
    for w in FILE_WORDS:
        used.pop(w, None)
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


def check_placeholder(doc: Doc) -> None:
    """발간 전에 실제 값으로 바뀌어야 하는 자리표시자.

    기관명·발간등록번호·문의처가 `(발행기관명)` 인 채로 배포본이 만들어진
    일이 있었다. 조판기는 원고를 그대로 옮기므로 **원고에서 걸러야 한다.**

    지적하는 꼴은 코퍼스 24종에서 **한 번도 나오지 않은 것**으로 한정했다.
    ○○ · OOO · ____ 는 발행본도 쓰지만 예시와 양식 안에서만 쓰므로, 실제
    값이 들어가야 하는 앞붙이에서만 본다.
    """
    front = zones_of(doc, RX_HEAD_FRONT)
    hits: dict[str, list[int]] = {}
    for n, raw in body_lines(doc):
        if not raw.strip():
            continue
        # 자리표시자를 **가리켜 설명하는** 자리는 보지 않는다. 이 검사의
        # 설명표에 `(기관명)` 과 `TODO` 를 보기로 적었더니 자기 규칙에 걸렸다.
        l = unquoted(raw)
        for rx, label in RX_PLACEHOLDER_ALWAYS:
            if rx.search(l):
                hits.setdefault(label, []).append(n)
        if in_zones(n, front):
            for rx, label in RX_PLACEHOLDER_FRONT:
                if rx.search(l):
                    hits.setdefault(label, []).append(n)
    if not hits:
        return
    shown = ", ".join(sorted(hits))
    doc.add_agg("PLACEHOLDER", "error",
                [ns[0] for ns in hits.values()],
                f"자리표시자가 남아 있습니다 — {len(hits)}종 ({shown})",
                "발간등록번호·발행기관·문의처는 발간 직전에 채웁니다. "
                "자리표시자가 남으면 배포본에 그대로 인쇄됩니다.")


def check_source_count(doc: Doc) -> None:
    """외부 자료의 수를 단정하면서 그 자료를 참고 자료에 올리지 않은 곳.

    원고가 선행 자료의 점검항목을 98 개라고 적었으나 **실제는 112 개**였다.
    대조한 적이 없는데 대조했다고 적힌 것을 검사가 잡지 못했다.

    검사기가 외부 자료를 세어 볼 수는 없다. 할 수 있는 일은 **그 수를
    단정한 문장이 가리키는 자료가 참고 자료 목록에 있는지** 보는 것이다.
    목록에 없으면 원문을 확인한 적이 없다는 뜻이다.
    """
    refs = zones_of(doc, RX_HEAD_REF)
    if not refs:
        return
    listed: set[str] = set()
    for a, b in refs:
        listed |= docnames("\n".join(doc.lines[a - 1:b]))
    if not listed:
        return
    skip = refs + zones_of(doc, RX_HEAD_HIST)
    bad: dict[str, list[int]] = {}
    for n, l in body_lines(doc):
        if in_zones(n, skip) or not RX_ASSERT_COUNT.search(l):
            continue
        for name in RX_DOCNAME.findall(l):
            flat = re.sub(r"\s+", "", name)
            if RX_LAW_NAME.search(flat):
                continue
            if any(flat in q or q in flat for q in listed):
                continue
            bad.setdefault(name, []).append(n)
    if not bad:
        return
    shown = ", ".join("\uff62%s\uff63" % s for s in sorted(bad)[:SAMPLE_LIMIT])
    doc.add_agg("SOURCE-COUNT", "warn",
                [ns[0] for ns in bad.values()],
                f"참고 자료에 없는 문서의 수를 단정했습니다 — {len(bad)}종 ({shown})",
                "외부 자료의 항목 수를 적으려면 그 자료를 원문으로 확인하고 "
                "참고 자료에 올리세요. 확인하지 않은 수는 틀립니다.")


def check_ref_unused(doc: Doc) -> None:
    """참고 자료에 올렸으나 본문에서 한 번도 인용하지 않은 자료.

    실재하지 않는 자료명이 참고 자료에 남아 있던 일이 있었다. 검사기가
    자료의 실재를 확인할 수는 없지만, **본문이 쓰지 않는 자료**는 집필 중에
    지운 인용의 흔적이거나 확인하지 않고 올린 것이다. 어느 쪽이든 본다.
    """
    refs = zones_of(doc, RX_HEAD_REF)
    if not refs:
        return
    # 비교는 공백을 지운 꼴로 하고, 보여 줄 때는 원문의 표기를 쓴다.
    listed: dict[str, int] = {}
    spell: dict[str, str] = {}
    for a, b in refs:
        for i in range(a, min(b, len(doc.lines)) + 1):
            for name in RX_DOCNAME.findall(doc.lines[i - 1]):
                flat = re.sub(r"\s+", "", name)
                listed.setdefault(flat, i)
                spell.setdefault(flat, name.strip())
    if not listed:
        return
    used: set[str] = set()
    for n, l in body_lines(doc):
        if in_zones(n, refs):
            continue
        used |= docnames(l)
    listed = {q: i for q, i in listed.items() if not RX_LAW_NAME.search(q)}
    idle = {q: i for q, i in listed.items()
            if not any(q in u or u in q for u in used)}
    if not idle:
        return
    shown = ", ".join("\uff62%s\uff63" % spell.get(s, s)
                      for s in sorted(idle)[:SAMPLE_LIMIT])
    doc.add_agg("REF-UNUSED", "info", list(idle.values()),
                f"본문에서 인용하지 않은 참고 자료가 있습니다 — "
                f"{len(idle)}종 ({shown})",
                "쓰지 않는 자료는 목록에서 빼세요. 확인하지 않은 자료명이 "
                "목록에만 남아 있으면 읽는 사람이 실재한다고 믿습니다.")


def check_draft_note(doc: Doc) -> None:
    """앞붙이에 남은 집필용 메모.

    목차 끝의 "쪽번호는 조판 단계에서 붙인다…" 가 발행본에 그대로 인쇄됐다.
    목차와 발간 정보는 **표와 목록으로만 이루어진 구역**이라, 거기 있는
    평서문은 대개 집필 중에 적어 둔 메모다.

    `※` 로 시작하는 줄은 발행본의 관례이므로 보지 않는다.
    """
    zones = zones_of(doc, RX_HEAD_NOTE)
    if not zones:
        return
    hit: list[int] = []
    for n, l in body_lines(doc):
        if not in_zones(n, zones):
            continue
        s = l.strip()
        if (not s or head_level(l) or s.startswith(("|", "*", "-", ">", "!",
                                                   "\u203b", "+"))
                or re.match(r"^\d+[.)]", s) or len(s) < 12):
            continue
        if re.search(r"(?:다|요)[.。]?$|한다[.。]?$|니다[.。]?$", s):
            hit.append(n)
    if not hit:
        return
    doc.add_agg("DRAFT-NOTE", "warn", hit,
                f"앞붙이에 평서문이 있습니다 — 집필용 메모인지 확인하세요 "
                f"({len(hit)}줄)",
                "목차와 발간 정보는 표와 목록으로만 짭니다. 집필 중에 적어 둔 "
                "메모는 발간 전에 지우세요 — 조판기는 원고를 그대로 옮깁니다.")


def check_evidence(doc: Doc) -> None:
    """사례 단락에 근거가 없는 곳.

    제3장의 사례 네 건을 원문과 대조했더니 여섯 곳이 어긋났다 — 원문에 없는
    기간·빈도·순위를 덧붙이고, 연구가 밝힌 근사값 한계를 빼먹었다. 검사기가
    사실을 확인할 수는 없다.

    할 수 있는 일은 **연도와 수치를 함께 든 단락에 출처가 있는지** 보는
    것이다. 집필자가 근거를 적게 만드는 효과가 있다.
    """
    if not zones_of(doc, RX_HEAD_REF):
        return   # 참고 자료를 두지 않는 문서는 보지 않는다
    para: list[tuple[int, str]] = []
    hit: list[int] = []

    def flush() -> None:
        if not para:
            return
        body = " ".join(s for _, s in para)
        if (RX_YEAR.search(body) and RX_CASE_NUM.search(body)
                and not RX_EVIDENCE.search(body)):
            hit.append(para[0][0])
        para.clear()

    for n, l in body_lines(doc):
        s = l.strip()
        if not s or head_level(l) or TABLE_ROW.match(l):
            flush()
            continue
        para.append((n, s))
    flush()
    if not hit:
        return
    doc.add_agg("EVIDENCE-NONE", "info", hit,
                f"연도와 수치를 들었으나 출처가 없는 단락이 있습니다 "
                f"({len(hit)}곳)",
                "사례의 수치는 1차 자료에서 가져오고 `출처:` 로 밝히세요. "
                "원문에 없는 기간·빈도·순위를 덧붙이지 않습니다.")


def check_id_abbrev(doc: Doc) -> None:
    """접두사를 생략해 줄여 쓴 ID.

    `SSDF-03·04·05` 처럼 적으면 읽는 사람이 `SSDF-05` 로 찾아도 걸리지
    않는다. 참고 문서는 ID 로 찾는 일이 잦다.

    다만 **발행본도 이렇게 쓴다** — 코퍼스 24종 중 2종에서 32회 나왔다
    (`TID-105, 110, 118`). 틀린 것이 아니므로 참고로만 알린다.
    """
    hit: list[int] = []
    for n, l in body_lines(doc):
        # 줄여 쓴 보기를 **인용해 설명하는** 자리는 보지 않는다.
        if RX_ID_ABBREV.search(unquoted(l)):
            hit.append(n)
    if not hit:
        return
    doc.add_agg("ID-ABBREV", "info", hit,
                f"접두사를 생략해 줄여 쓴 ID 가 있습니다 ({len(hit)}줄)",
                "`TID-105, 110, 118` 은 `TID-105, TID-110, TID-118` 로 "
                "풀어 쓰세요. 줄여 쓰면 ID 로 찾을 수 없습니다.")


def check_heading_dup(doc: Doc) -> None:
    """한 절 안에 같은 소제목이 두 번.

    제5장 제6절에 `\u25a0 구현 방법 예시` 가 **연달아 두 번** 나왔다. 집필 중에
    문단을 옮기면 생기는 결함인데, 조판기는 둘 다 찍는다. 읽는 사람은 어느
    쪽이 이어지는 내용인지 알 수 없다.
    """
    seen: dict[str, int] = {}
    hit: list[int] = []
    for n, l in body_lines(doc):
        if head_level(l):
            seen.clear()            # 제목을 만나면 새 구역
            continue
        m = RX_MARK_HEAD.match(l)
        if not m:
            continue
        key = re.sub(r"\s+", "", m.group(2))
        if key in seen:
            hit.append(n)
        else:
            seen[key] = n
    if not hit:
        return
    doc.add_agg("HEADING-DUP", "warn", hit,
                f"같은 소제목이 한 절 안에 두 번 나옵니다 ({len(hit)}곳)",
                "하나로 합치세요. 문단을 옮기다 생긴 것입니다 — 조판기는 "
                "둘 다 찍으므로 읽는 사람이 어느 쪽이 이어지는지 모릅니다.")


def check_cycle_space(doc: Doc) -> None:
    """주기 표현의 띄어쓰기 — `연1회` → `연 1회`."""
    hit = [n for n, l in body_lines(doc) if RX_CYCLE_TIGHT.search(unquoted(l))]
    if not hit:
        return
    doc.add_agg("CYCLE-SPACE", "info", hit,
                f"주기를 붙여 썼습니다 — `연1회` 는 `연 1회` ({len(hit)}줄)",
                "코퍼스는 띄움 20회(4종) · 붙임 11회(2종) 로 띄움이 다수이고 "
                "맞춤법도 띄웁니다. 문서 안에서 하나로 통일하세요.")


def check_history(doc: Doc) -> None:
    """문서이력 표의 정렬과 빈 기록.

    `0.1 → 0.2 → 0.7 → 0.6 → 0.5 → 0.4 → 0.3` 처럼 뒤섞인 이력이 발행본에
    그대로 들어갔다. 또 `보완한다→보완한다` 처럼 **변경 전과 후가 같은**
    기록이 있어 무엇을 고쳤는지 알 수 없었다. 표기 교정이 이력 문장에도
    적용되어 변경 전 표현까지 바뀐 것이다.
    """
    zones = zones_of(doc, RX_HEAD_HIST)
    if not zones:
        return
    rows: list[tuple[int, str, tuple]] = []
    noop: list[int] = []
    for a, b in zones:
        for i in range(a, min(b, len(doc.lines)) + 1):
            l = doc.lines[i - 1]
            m = RX_HIST_ROW.match(l)
            if not m:
                continue
            d = ymd(m.group(2))
            if d:
                rows.append((i, m.group(1), d))
            for before, after in RX_ARROW_PAIR.findall(m.group(3)):
                if before == after:
                    noop.append(i)
                    break
    if noop:
        doc.add_agg("HISTORY-NOOP", "warn", noop,
                    f"변경 전과 후가 같은 이력이 있습니다 ({len(noop)}줄)",
                    "`보완한다→보완한다` 로는 무엇을 고쳤는지 알 수 없습니다. "
                    "표기 교정이 이력 문장의 '변경 전' 까지 바꾼 것이니 "
                    "원래 표현을 되살리세요.")
    if len(rows) < 3:
        return
    # 버전은 오름차순이든 내림차순이든 한 방향이어야 한다
    def ver(s: str) -> tuple:
        return tuple(int(x) for x in s.split("."))

    vs = [ver(v) for _, v, _ in rows]
    if vs == sorted(vs) or vs == sorted(vs, reverse=True):
        return
    # 어긋난 줄만 짚는다
    want = sorted(vs, reverse=vs[0] > vs[-1])
    bad = [rows[i][0] for i in range(len(vs)) if vs[i] != want[i]]
    doc.add_agg("HISTORY-ORDER", "warn", bad or [rows[0][0]],
                "문서이력의 버전이 한 방향으로 정렬되지 않았습니다",
                "새 버전을 위에 넣든 아래에 넣든 한 방향으로만 쌓으세요. "
                "뒤섞이면 읽는 사람이 어느 것이 최신인지 알 수 없습니다.")


def check_date_sync(doc: Doc) -> None:
    """발간 정보의 작성 기준일과 문서이력의 최신 일자.

    표지에는 2026. 11. 20. 이, 문서이력의 최신 기록에는 11. 23. 이 적혀
    있었다. 둘 중 어느 것이 이 문서의 날짜인지 알 수 없다.
    """
    m = RX_BASEDATE.search(doc.text)
    if not m:
        return
    base = ymd(m.group(1))
    if not base:
        return
    # 최종 수정일을 따로 적어 두었으면 그것과 맞춰 본다. 작성 기준일은 내용의
    # 기준 시점이고 최종 수정일은 마지막 손질이라 둘은 달라도 된다.
    lm = RX_LASTDATE.search(doc.text)
    if lm:
        lastdecl = ymd(lm.group(1))
        if lastdecl:
            base = max(base, lastdecl)
    zones = zones_of(doc, RX_HEAD_HIST)
    dates = []
    for a, b in zones:
        for i in range(a, min(b, len(doc.lines)) + 1):
            hm = RX_HIST_ROW.match(doc.lines[i - 1])
            if hm:
                d = ymd(hm.group(2))
                if d:
                    dates.append((d, i))
    if not dates:
        return
    last, line = max(dates)
    if last <= base:
        return
    doc.add("DATE-MISMATCH", "warn", line,
            "문서이력의 최신 일자가 작성 기준일보다 뒤입니다 — "
            "%d. %d. %d. > %d. %d. %d." % (last + base),
            "작성 기준일(내용의 기준 시점)과 최종 수정일(마지막 손질)은 다른 "
            "날짜입니다. 발간 정보에 `최종 수정일` 칸을 더해 구분하거나 "
            "기준일을 갱신하세요.")


def check_figure_files(doc: Doc) -> None:
    """원고가 끌어 쓰는 그림 파일이 실제로 있는지.

    검사기가 캡션만 보고 있어 **파일이 없어도 통과**했다. 조판기는 없는
    그림을 조용히 비워 두므로 발행본에 빈 자리가 남는다.
    """
    miss: list[int] = []
    for n, raw in body_lines(doc):
        # 끌어 쓰는 꼴을 **가리켜 설명하는** 자리는 보지 않는다. SKILL.md 가
        # 백틱 안에 `![](figures/*.svg)` 를 적어 두었더니 걸렸다.
        for src in RX_IMG.findall(unquoted(raw)):
            src = src.split()[0].strip('<>"\'')
            if src.startswith(("http://", "https://", "data:")):
                continue
            if not (doc.path.parent / src).exists():
                miss.append(n)
    if not miss:
        return
    doc.add_agg("FIGURE-FILE", "error", miss,
                f"원고가 끌어 쓰는 그림 파일이 없습니다 ({len(miss)}곳)",
                "조판기는 없는 그림을 조용히 비워 둡니다. figures.py 로 "
                "그리거나 경로를 고치세요.")


def outline(doc: Doc) -> tuple[set, set, dict]:
    """원고의 뼈대 — 있는 (장, 절), (장, 절, 소절), 부록 번호."""
    secs: set = set()
    subs: set = set()
    appx: set = set()
    chap = sec = 0
    for l in doc.lines:
        m = RX_H_CHAP.match(l)
        if m:
            chap, sec = int(m.group(1)), 0
            continue
        if RX_H_APPX.match(l):
            appx.add(int(RX_H_APPX.match(l).group(1)))
            chap = sec = 0
            continue
        m = RX_H_SECT.match(l)
        if m:
            sec = int(m.group(1))
            if chap:
                secs.add((chap, sec))
            continue
        m = RX_H_SUB.match(l)
        if m and chap and sec:
            subs.add((chap, sec, int(m.group(1))))
    return secs, subs, appx


def check_xref(doc: Doc) -> None:
    """원고가 가리키는 절·소절·부록·캡션이 실제로 있는지.

    절을 끼워 넣으면 뒤 소절의 번호가 밀린다. `제1장 제3절 7.` 이 가리키던
    곳이 8. 이 되어도 참조는 7. 로 남는다. **발행본에서 독자가 찾아가는
    자리**이므로 오류로 본다.

    `제N장` 이 붙지 않은 `제M절 K.` 는 그 줄이 속한 장에서 찾는다.
    """
    secs, subs, appx = outline(doc)
    if not secs and not appx:
        return
    # 코드 블록 안의 보기는 캡션이 아니다 — `body_lines()` 가 걸러 준다.
    caps = {(m.group(1), int(m.group(2)), int(m.group(3)))
            for m in (RX_CAPTION.match(l) for _, l in body_lines(doc)) if m}
    bad: dict[str, int] = {}
    chap = 0
    for n, raw in body_lines(doc):
        m = RX_H_CHAP.match(raw)
        if m:
            chap = int(m.group(1))
        if RX_H_APPX.match(raw):
            chap = 0
        if head_level(raw):
            continue
        l = unquoted(raw)
        # 한 줄에서 장을 한 번만 적고 이어 쓴다 — `제4장 제1절 6., 제1절 7.`.
        # 앞에서 명시한 장을 이어 받고, 없으면 이 줄이 속한 장으로 본다.
        here = chap
        for m in RX_REF_SEC.finditer(l):
            if m.group(1):
                c, s, k = int(m.group(1)), int(m.group(2)), m.group(3)
                here = c
            else:
                if not here:
                    continue
                c, s, k = here, int(m.group(4)), m.group(5)
            if (c, s) not in secs:
                bad.setdefault('제%d장 제%d절' % (c, s), n)
            elif k and (c, s, int(k)) not in subs:
                bad.setdefault('제%d장 제%d절 %s.' % (c, s, k), n)
        for m in RX_REF_APPX.finditer(l):
            if appx and int(m.group(1)) not in appx:
                bad.setdefault('부록 %s' % m.group(1), n)
        for m in RX_REF_CAP.finditer(l):
            key = (m.group(1), int(m.group(2)), int(m.group(3)))
            if caps and key not in caps:
                bad.setdefault('[%s %d-%d]' % key, n)
    if not bad:
        return
    shown = ", ".join(sorted(bad)[:SAMPLE_LIMIT])
    doc.add_agg("XREF", "error", list(bad.values()),
                f"가리키는 곳이 없는 참조가 있습니다 — {len(bad)}종 ({shown})",
                "절을 끼워 넣거나 표를 더하면 뒤 번호가 밀립니다. 발행본에서 "
                "독자가 찾아가는 자리이므로 번호를 함께 고치세요.")


def check_caption_seq(doc: Doc) -> None:
    """캡션 번호가 지면 순서대로 붙었는지.

    표를 중간에 끼워 넣으면 `[표 1-10]` 이 두 개가 되거나 번호가 거꾸로
    간다. 조판기는 캡션을 글자 그대로 찍으므로 발행본에 그대로 나간다.
    """
    seen: dict[tuple, list[int]] = {}
    order: dict[int, list[tuple[int, int]]] = {}
    for n, l in body_lines(doc):
        m = RX_CAPTION.match(l)
        if not m:
            continue
        kind, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        seen.setdefault((kind, a, b), []).append(n)
        order.setdefault((kind, a), []).append((b, n))
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    if dup:
        shown = ", ".join('[%s %d-%d]' % k for k in sorted(dup)[:SAMPLE_LIMIT])
        doc.add_agg("CAPTION-DUP", "error",
                    [v[1] for v in dup.values()],
                    f"같은 캡션 번호가 두 번 쓰였습니다 — {len(dup)}종 ({shown})",
                    "표나 그림을 중간에 끼워 넣을 때 뒤 번호를 함께 당기세요. "
                    "큰 번호부터 바꿔야 중간에 겹치지 않습니다.")
    gap: list[int] = []
    for (kind, a), items in order.items():
        want = 1
        for b, n in items:
            if b != want:
                gap.append(n)
                want = b
            want += 1
    if gap:
        doc.add_agg("CAPTION-SEQ", "warn", gap,
                    f"캡션 번호가 지면 순서대로 붙지 않았습니다 ({len(gap)}곳)",
                    "같은 장의 표·그림은 나오는 순서대로 1부터 번호를 붙입니다. "
                    "끼워 넣거나 지울 때 밀린 것입니다.")


def check_num_particle(doc: Doc) -> None:
    """숫자 뒤 조사가 읽는 소리에 맞는지.

    `[표 1-9]은` 이 발행 전 검토에서 지적됐다. `9` 는 '구' 로 읽어 받침이
    없으므로 `는` 이다. 표와 그림을 백 번 넘게 가리키는 문서에서 사람이
    매번 맞추기 어렵다.
    """
    bad: dict[str, int] = {}
    for n, raw in body_lines(doc):
        line = unquoted(raw)
        for m in list(RX_NUM_PARTICLE.finditer(line)) + \
                 list(RX_ID_PARTICLE.finditer(line)):
            digit, close, part = m.group(1), m.group(2), m.group(3)
            coda = NUM_CODA[digit]
            # `로/으로` 는 ㄹ받침 예외가 있어 따로 본다
            if part in ('로', '으로'):
                want = '로' if (not coda or digit in NUM_RIEUL) else '으로'
                if part != want:
                    bad.setdefault('%s%s%s → %s%s%s'
                                   % (digit, close, part,
                                      digit, close, want), n)
                continue
            for with_coda, without in PARTICLE_PAIRS:
                if part == with_coda and not coda:
                    bad.setdefault('%s%s%s → %s%s%s'
                                   % (digit, close, part,
                                      digit, close, without), n)
                elif part == without and coda:
                    bad.setdefault('%s%s%s → %s%s%s'
                                   % (digit, close, part,
                                      digit, close, with_coda), n)
                else:
                    continue
                break
    if not bad:
        return
    shown = ", ".join('`%s`' % s for s in sorted(bad)[:SAMPLE_LIMIT])
    doc.add_agg("PARTICLE-NUM", "info", list(bad.values()),
                f"숫자 뒤 조사가 읽는 소리와 맞지 않습니다 — "
                f"{len(bad)}종 ({shown})",
                "끝 자리를 읽은 소리로 고릅니다 — 1(일)·3(삼)·6(육)·7(칠)·"
                "8(팔)·0(영)은 받침이 있어 `은·이·을·과`, "
                "2(이)·4(사)·5(오)·9(구)는 받침이 없어 `는·가·를·와`. "
                "`로/으로`는 ㄹ받침이 예외라 1·7·8도 `로`를 씁니다.")


def check_name_drift(doc: Doc) -> None:
    """같은 통제 ID 의 소항목 이름이 표마다 다른 곳.

    통제 하나가 본문 표·대응표·조달표에 여러 번 나온다. 이름을 바꿀 때
    한 곳을 놓치면 읽는 사람이 다른 통제로 안다.
    """
    names: dict[str, dict[str, int]] = {}
    for n, l in body_lines(doc):
        if not TABLE_ROW.match(l):
            continue
        c = cells_of(l)
        if len(c) < 3:
            continue
        m = RX_ID_OK.fullmatch(c[0])
        if not m or m.group(1) in ID_IGNORE_PREFIX:
            continue
        nm = c[1].strip()
        # 이름 칸이어야 한다 — 짧고, 설명문이 아니다
        if not nm or len(nm) > 24 or nm in ('—', '-') or '.' in nm:
            continue
        names.setdefault(c[0], {}).setdefault(nm, n)
    bad = {k: v for k, v in names.items() if len(v) > 1}
    if not bad:
        return
    shown = ", ".join('%s(%s)' % (k, ' / '.join(sorted(v)))
                      for k in sorted(bad)[:3] for v in [bad[k]])
    doc.add_agg("NAME-DRIFT", "warn",
                [min(v.values()) for v in bad.values()],
                f"같은 통제 ID 의 소항목 이름이 표마다 다릅니다 — "
                f"{len(bad)}종 ({shown})",
                "통제 하나가 본문 표·대응표·조달표에 여러 번 나옵니다. "
                "이름을 바꿀 때 한 곳을 놓치면 읽는 사람이 다른 통제로 "
                "압니다. 모두 같은 이름으로 맞추세요.")


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
    "PLACEHOLDER": check_placeholder,
    "SOURCE-COUNT": check_source_count,
    "REF-UNUSED": check_ref_unused,
    "DRAFT-NOTE": check_draft_note,
    "EVIDENCE-NONE": check_evidence,
    "ID-ABBREV": check_id_abbrev,
    "HEADING-DUP": check_heading_dup,
    "CYCLE-SPACE": check_cycle_space,
    "HISTORY-ORDER": check_history,
    "DATE-MISMATCH": check_date_sync,
    "FIGURE-FILE": check_figure_files,
    "XREF": check_xref,
    "CAPTION-SEQ": check_caption_seq,
    "PARTICLE-NUM": check_num_particle,
    "NAME-DRIFT": check_name_drift,
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
    "COUNT-LIST": "STYLE",
    "EM-DASH": "STYLE",
    "HISTORY-NOOP": "HISTORY-ORDER",
    "CAPTION-DUP": "CAPTION-SEQ",
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
