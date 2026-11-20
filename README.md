# 한국 사이버보안 가이드라인 스킬

> 한국 정부·공공기관 형식의 사이버보안 가이드라인을 쓰고 검사하는 Claude Code 스킬

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-5-green.svg)](#스킬)
[![Based on](https://img.shields.io/badge/based%20on-korean--skills-orange.svg)](https://github.com/DaleSeo/korean-skills)

국가 망 보안체계(N2SF), 분야별 보안 가이드라인, 법령형 지침처럼 **정부 간행물의
형식과 문체를 따르는 문서**를 쓸 때 쓰는 스킬입니다. 장·절 골격, 통제항목 ID
체계, 보안등급 매트릭스, 강제력 종결어미, 법령 인용 표기를 적용하고 검사합니다.

규칙은 짐작이 아니라 **국내 사이버보안 가이드라인 20종(1,883쪽 / 약 145만 자)을
측정**해서 뽑았습니다. 측정값은 [`rules/`](rules/) 에 수치와 함께 적혀 있습니다.

## korean-skills 위에 세워져 있습니다

이 저장소는 [**korean-skills**](https://github.com/DaleSeo/korean-skills)(Dale Seo, MIT)
없이는 반쪽입니다. 여섯 개 스킬 중 **둘은 korean-skills 를 그대로 복사한 것이고,
하나는 korean-skills 에서 파생**했습니다.

| 스킬 | 누가 만들었나 |
|---|---|
| `guideline-writer` | 이 저장소 |
| `guideline-lint` | 이 저장소 |
| `guideline-design` | 이 저장소 |
| `govdoc-style` | **korean-skills `style-guide` 에서 파생** (구조를 가져와 내용 교체) |
| `grammar-checker` | **korean-skills 원본 그대로 복사** |
| `humanizer` | **korean-skills 원본 그대로 복사** |

가이드라인 집필은 맞춤법 교정(`grammar-checker`)과 문체 완화(`humanizer`)를
korean-skills 에 맡깁니다. 한 번에 설치되도록 복사본을 함께 넣었지만,
**원저작자가 관리하는 최신본을 쓰는 편이 낫습니다** —
[korean-skills 를 직접 설치](#korean-skills-를-직접-쓰려면)하고 복사본을 지우세요.

출처·라이선스·변경 내역은 [NOTICE](NOTICE) 와 각 폴더의 `ORIGIN.md` 에 있습니다.

## 설치

### Claude Code 플러그인

```bash
claude /plugin marketplace add ssabro/korea-security-guideline-skill
claude /plugin install korea-security-guideline
```

### 직접 복사

```bash
git clone https://github.com/ssabro/korea-security-guideline-skill
cd korea-security-guideline-skill
cp -r skills/* ~/.claude/skills/        # 또는 프로젝트의 .claude/skills/
cp -r rules ~/.claude/                  # 스킬이 ../../rules/ 를 읽습니다
```

스킬이 `rules/` 를 상대 경로로 읽으므로 **저장소를 통째로 두고 쓰는 편이
간단합니다.** 스킬 하나만 떼어 가면 규칙 링크가 끊어집니다.

## 스킬

### `guideline-writer` — 집필

장르를 정하고 → 골격을 확정하고 → 통제항목·등급 체계를 설계하고 → 본문을 쓰고 →
부록을 붙이는 순서로 진행합니다.

```
가이드라인 써줘: 의료정보시스템 보안 가이드라인, 통제항목 체계 포함
```

- **장르를 먼저 묻습니다.** 법령형 지침 / 분야별 가이드라인 / 통제항목 체계 /
  실무 안내서는 골격·번호 체계·종결어미가 전부 다릅니다. 섞으면 바로 어긋나 보입니다.
- **전개 축을 하나만 씁니다.** 보안대책 장은 수명주기별 또는 구성요소·연계유형별
  중 하나입니다. 둘을 장 단위로 섞으면 같은 통제가 흩어집니다.
- 장르별 목차 템플릿 5종과 재사용할 통제 도메인 코드 27개를 함께 제공합니다.

### `guideline-lint` — 검사

```bash
python skills/guideline-lint/lint.py 원고.md
python skills/guideline-lint/lint.py 원고.md --genre control --quiet
```

**검사는 줄 단위입니다.** 원고는 한 문단을 한 줄로 쓰세요 — 폭에 맞춰 감아 두면
주기나 용어가 다른 줄에 떨어져 잘못 지적됩니다. 이미 감긴 원고는
`python skills/guideline-writer/unwrap.py 원고.md` 로 펼칩니다.

표준 라이브러리만 씁니다. 기계적으로 판정할 수 있는 23개 항목을 봅니다.

| 등급 | 항목 |
|---|---|
| 오류 | 의무 표현 혼용(`~하여야 한다`/`~해야 한다`), 경어체 혼입, 통제항목 ID 문법, 모항목 없는 강화 항목, 등급 포함 관계 위반, 본문에 없는 항목이 부록 점검표에 있음 |
| 경고 | 통제항목 설명의 `~해야 한다`, 주기 없는 통제, 법령 꺾쇠·캡션 혼용, 가운뎃점 `ㆍ`, 위치 표현("아래 표"), 제목 레벨 건너뛰기, 부록 점검표에서 빠진 통제항목, 등급별 요구 항목 수 불일치 |
| 참고 | 제목 깊이, 제목 번호 중복·건너뜀, 용어 혼용, 풀네임 없는 약어, 그림 없는 문서 |

같은 성격의 지적은 하나로 묶어 횟수와 예시 줄번호만 보여줍니다. 측정에 쓴
가이드라인 20종에 돌려 보면 문서당 오류 0~2건, 경고 0~4건이 나옵니다.

### `guideline-design` — 배포본 조판

원고를 **발행본 모양의 HTML·PDF 로** 만듭니다. 판면·여백·본문 크기·색은 짐작이
아니라 발행본 20종을 측정해 정했습니다.

가장 자주 틀리는 것이 판면입니다. **측정한 20종 중 A4 는 6종뿐이고 전부 짧은
지침입니다** — 본체 가이드라인의 판면은 188×257mm 가 중앙값입니다. 본문에 명조를
쓴 문서는 하나도 없고, 여백은 좌우가 상하보다 넓습니다.

**제본해서 펴낼 것을 전제로 짭니다.** 표지 - 속표지 - 문서 정보 - 목차가 저마다
홀수 쪽에서 시작하고, 앞 내용이 길어지면 뒤 차례가 밀립니다. 본문은 그다음 홀수
쪽에서 시작하며 거기가 1쪽입니다. 마지막은 판권지입니다.

```bash
python skills/guideline-design/render.py 원고.md --theme nis    # 조판
# 인쇄(브라우저) → 1차.pdf
python skills/guideline-design/book.py  dist/1차.pdf --out dist/책.pdf
python skills/guideline-design/toc.py   dist/책.pdf --source 원고.md --skip 8
python skills/guideline-design/render.py 원고.md --theme nis --toc dist/toc.json
# 다시 인쇄 → book.py 다시
python skills/guideline-design/paginate.py dist/책.pdf --style bottom \
  --skip 8 --start 1 --end 1 --head --title "문서명"
```

목차 쪽번호 때문에 **두 번 인쇄합니다.** 조판하기 전에는 쪽을 알 수 없습니다.
빈 쪽도 원고에 박지 않고 `book.py` 가 인쇄한 뒤에 필요한 만큼만 끼웁니다 —
브라우저가 `break-before: recto` 를 무시하기 때문입니다.

결과 HTML 은 외부 자원을 하나도 받아오지 않아 망 분리 환경에서 그대로 열립니다.

기관이 이미 펴낸 책이 있으면 **거기서 재서 테마를 만듭니다.**

```bash
python skills/guideline-design/themegen.py 기관_작년_가이드라인.pdf --key ourorg
```

판면·여백·본문 크기·색을 재서 `themes/ourorg.py` 를 씁니다. 주조색은 제목 글자
색에서 찾고, 후보를 모두 주석에 적어 두니 한 줄 바꿔 끼우면 됩니다. 값 몇 개만
바꿀 때는 `--set accent=#1b3a6b` 처럼 줘도 됩니다.

**테마는 10종**입니다. `themes/` 에 파일 하나가 테마 하나라 직접 더할 수 있습니다
— [테마 만들기](skills/guideline-design/themes/README.md).

| | |
|---|---|
| `nis` `field` `control` `manual` `print` | 측정에서 바로 나온 판면 |
| `typo` `tab` `spec` `formal` | 타이포그래피 주도 · 장별 색과 측면 탭 · 기술 규격서 · 국가 간행물 |
| `art` | 전면 기하 아트워크 표지에 기관 로고 |

### 삽도

같은 스킬이 **삽도도 그립니다.** 색은 조판 테마를 따르므로 `nis` 면 남색,
`print` 면 흑백이 되고, 캡션은 `[그림 N-M]` 규칙이라 `guideline-lint` 검사를
그대로 통과합니다.

```bash
python skills/guideline-design/figplan.py 원고.md --mode review   # 어디에 무엇이
python skills/guideline-design/figures.py 계획.json --theme nis   # 그린다
python skills/guideline-design/figplan.py 원고.md --mode auto --plan 계획.json
```

**두 단계인 이유가 있습니다.** `review` 가 내놓는 계획에는 명세가 비어 있고,
원고를 읽고 채워야 그립니다. 도구가 혼자 노드와 연결을 지어내지 못하게 막은
것입니다 — 원고에 없는 구성요소를 그린 도식은 그럴듯해서 더 위험합니다.

이미지 생성 API 는 쓰지 않습니다. 사진 같은 그래픽이 필요하면 계획에 적어 두고
발행기관이 따로 만듭니다. 규칙은
[삽도 — 무엇을, 언제, 어떻게](skills/guideline-design/references/figure-design.md)에
있습니다.

수치의 근거는
[발행본 디자인 측정값](skills/guideline-design/references/publication-design.md)에
있습니다.

### `govdoc-style` — 공문서 문체 일관성

korean-skills `style-guide` 에서 구조를 가져와 공문서 관례로 내용을 교체한
파생본입니다. 맞춤법이 아니라 **같은 문서 안에서의 일관성**을 봅니다 —
강제력 종결어미, 경어체 여부, 용어 통일, 법령 인용, 영문 병기, 숫자·날짜,
목록·제목 형식, 인용·강조.

원본과 무엇이 달라졌는지는
[SKILL.md 의 "원본과 달라진 점"](skills/govdoc-style/SKILL.md) 에 있습니다.

### `grammar-checker` · `humanizer` — korean-skills 원본

맞춤법·띄어쓰기·구두점 교정과 AI 문체 완화입니다. **수정 없이 복사했습니다.**
자세한 내용은 [grammar-checker/ORIGIN.md](skills/grammar-checker/ORIGIN.md),
[humanizer/ORIGIN.md](skills/humanizer/ORIGIN.md) 를 보세요.

`humanizer` 는 초안이 AI가 쓴 듯 읽힐 때만 쓰세요. **통제항목 표나 조문처럼
형식이 정해진 부분에는 쓰지 마세요** — 형식이 곧 내용인 곳에서 문체를 다듬으면
규범의 세기가 흔들립니다.

> `humanizer` 의 참조 문서 하나가 업스트림의 `style-guide` 스킬을 상대 경로로
> 가리킵니다. 이 저장소는 `style-guide` 를 복사하지 않았으므로(대신 파생본
> `govdoc-style` 을 두었습니다) 그 링크 하나는 끊어져 있습니다. 원본을
> 수정하지 않는 것이 원칙이라 손대지 않았습니다 — 자세한 내용은
> [humanizer/ORIGIN.md](skills/humanizer/ORIGIN.md).

## 쓰는 순서

```
선행 자료 조사  guideline-writer 0단계  ← 같은 분야 발행물이 있는지
  ↓
집필          guideline-writer
  ↓
법령 인용 검증  guideline-writer 5단계  ← 조문 원문 대조. 사람이 한다
  ↓
기계적 검사    guideline-lint          ← 오류부터 고친다
  ↓
문체 일관성    govdoc-style
  ↓
맞춤법         grammar-checker
  ↓
삽도          guideline-design        ← figplan.py 로 찾고 figures.py 로 그린다
  ↓
배포본 조판     guideline-design        ← 원고가 확정된 뒤에 한다
```

요약본을 함께 낸다면 **장르가 바뀌므로 문체를 통째로 갈고** 검사도 따로
돌립니다 — `python skills/guideline-lint/lint.py 요약본.md --genre manual`.

## 규칙

[`rules/`](rules/) 의 7개 문서가 이 스킬들의 근거입니다. 스킬이 작업 중에 읽습니다.

| 문서 | 핵심 |
|---|---|
| [구조 골격](rules/01-structure.md) | `개요 → 대상 분석 → 보안위협 → 보안대책 → 부록`. 대책 장의 전개 축은 두 가지뿐 |
| [제목 체계](rules/02-headings.md) | `제N장` → `제N절` → `N.` → `가.`. 실질 깊이 3단, 불릿 2단 |
| [통제항목 ID](rules/03-control-ids.md) | `<약어>-<도메인2>-<번호>[(강화)]` / `-M<번호>`. 6 대항목 / 27 도메인 |
| [등급 매트릭스](rules/04-grades.md) | 기밀 C ⊃ 민감 S ⊃ 공개 O 포함 관계. 요구 항목 273 / 221 / 85 |
| [강제력 종결어미](rules/05-normative-language.md) | 통제항목의 기본형은 `~한다`. `~해야 한다`는 본문 강조용 |
| [표기 규칙](rules/06-notation.md) | 법령은 `｢ ｣`, 영문 병기 `한글(English)`, 캡션 `[표 N]` |
| [용어](rules/07-terminology.md) | 사용자>이용자, 기관>조직. 보안대책·보안통제·보안 요구사항은 구별. 약어 94종 |

측정값을 그대로 규범으로 올리지 않은 곳이 한 군데 있습니다 — `정기적으로`는
원본 문서들에서 102회 쓰이지만, 주기가 없으면 점검할 수 없으므로 `연1회 이상`
같은 하한을 적도록 권고합니다. 이유는
[rules/06-notation.md](rules/06-notation.md) 의 숫자·기간 절에 있습니다.

## 법령 조문을 확인하는 도구

이 저장소는 법령 자료를 담지 않습니다. 집필 중 조문을 확인할 때는 다음을 씁니다.

- **법제처 국가법령정보 공동활용**(`open.law.go.kr`) — 조항호목 조회, 행정규칙,
  신구법 비교 API. 1차 출처입니다.
- **[Legalize-KR Agent Skills](https://github.com/legalize-kr/agent-skills)** —
  법령·판례·행정규칙·자치법규를 조회하는 에이전트용 스킬(Apache-2.0 · MIT).
  인증키 없이 동작합니다.

**복사해 넣지 않은 이유는 법령이 시간에 민감하기 때문입니다.** 문체 규칙과 달리
법령 자료의 사본은 개정이 반영되지 않으면 틀린 조문을 자신 있게 인용하게
만듭니다. 필요하면 직접 최신본을 설치하시고, **발행 전에는 1차 출처와
대조하세요** — 자세한 내용은
[verification-log.md](skills/guideline-writer/references/verification-log.md).

## korean-skills 를 직접 쓰려면

복사본 대신 원저작자의 최신본을 쓰는 방법입니다.

```bash
claude /plugin marketplace add daleseo/korean-skills
claude /plugin install korean-skills
```

그다음 이 저장소의 복사본을 지우세요.

```bash
rm -rf skills/grammar-checker skills/humanizer
```

플러그인으로 설치하면 스킬 이름이 플러그인별로 구분되므로
(`korea-security-guideline:grammar-checker` / `korean-skills:grammar-checker`)
둘을 함께 설치해도 충돌하지는 않습니다. 다만 같은 일을 하는 스킬이 두 개
로드되므로 한쪽만 두는 편이 깔끔합니다.

## 한계

- **규칙은 20종에서 뽑은 것입니다.** 발행처마다 자체 양식이 있으면 그것이
  우선합니다. 스킬도 그렇게 동작합니다.
- **린터는 법령 인용의 정확성을 보지 않습니다.** 꺾쇠·띄어쓰기 같은 표기만
  봅니다. 조문 번호는 사람이 원문과 대조해야 합니다. 조문 본문은 법제처
  국가법령정보 공동활용(`open.law.go.kr`)의 조항호목 조회 API 로 가져올 수
  있습니다 —
  **발행된 정부 간행물의 인용도 틀립니다.** 시험 집필에서 코퍼스 간행물의
  ｢국가정보원법｣ 조문 인용을 따랐다가 틀린 사례가 나왔습니다
  ([rules/06-notation.md](rules/06-notation.md)).
- **린터는 구조를 보지 않습니다.** 장·절 구성이 장르에 맞는지, 3장의 위협과
  4장의 대책이 맞물리는지, 부록 체크리스트가 본문과 1:1인지는 사람이 봐야 합니다.
- **등급 검사는 병합 셀이 있는 표에서 동작하지 않습니다.** 열이 밀려 `●` 가 다른
  칸으로 들어갑니다. 원고에서 병합 셀을 쓰지 마세요.
- **원본 가이드라인을 배포하지 않습니다.** `rules/` 에는 문장이 아니라 구조·체계·
  표기 규칙과 측정 수치만 담았습니다.

## 라이선스

이 저장소가 만든 부분은 MIT입니다 — [LICENSE](LICENSE).
복사·파생한 korean-skills 부분은 Dale Seo의 MIT이며, 전문과 범위는
[NOTICE](NOTICE) 에 있습니다.
