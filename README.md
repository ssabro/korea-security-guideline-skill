# 한국 사이버보안 가이드라인 스킬

> 한국 정부·공공기관 형식의 사이버보안 가이드라인을 쓰고 검사하는 Claude Code 스킬

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Skills](https://img.shields.io/badge/skills-5-green.svg)](#스킬) [![Based on](https://img.shields.io/badge/based%20on-korean--skills-orange.svg)](https://github.com/DaleSeo/korean-skills)

국가 망 보안체계(N2SF), 분야별 보안 가이드라인, 법령형 지침처럼 **정부 간행물의 형식과 문체를 따르는 문서**를 쓸 때 쓰는 스킬입니다. 장·절 골격, 통제항목 ID 체계, 보안등급 매트릭스, 강제력 종결어미, 법령 인용 표기를 적용하고 검사합니다.

규칙은 짐작이 아니라 **국내 사이버보안 가이드라인 20종(1,883쪽 / 약 145만 자)을 측정**해서 뽑았습니다. 측정값은 [`rules/`](rules/) 에 수치와 함께 적혀 있습니다.

## korean-skills 위에 세워져 있습니다

이 저장소는 [**korean-skills**](https://github.com/DaleSeo/korean-skills)(Dale Seo, MIT) 없이는 반쪽입니다. 여섯 개 스킬 중 **둘은 korean-skills 를 그대로 복사한 것이고, 하나는 korean-skills 에서 파생**했습니다.

| 스킬 | 누가 만들었나 |
|---|---|
| `guideline-writer` | 이 저장소 |
| `guideline-lint` | 이 저장소 |
| `guideline-design` | 이 저장소 |
| `govdoc-style` | **korean-skills `style-guide` 에서 파생** (구조를 가져와 내용 교체) |
| `grammar-checker` | **korean-skills 원본 그대로 복사** |
| `humanizer` | **korean-skills 원본 그대로 복사** |

가이드라인 집필은 맞춤법 교정(`grammar-checker`)과 문체 완화(`humanizer`)를 korean-skills 에 맡깁니다. 한 번에 설치되도록 복사본을 함께 넣었지만, **원저작자가 관리하는 최신본을 쓰는 편이 낫습니다** — [korean-skills 를 직접 설치](#korean-skills-를-직접-쓰려면)하고 복사본을 지우세요.

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

스킬이 `rules/` 를 상대 경로로 읽으므로 **저장소를 통째로 두고 쓰는 편이 간단합니다.** 스킬 하나만 떼어 가면 규칙 링크가 끊어집니다.

조판에는 **Chrome 이나 Edge** 와 **PyMuPDF** 가 더 필요합니다.

```bash
pip install pymupdf
```

## 빠른 시작

원고가 있다면 두 줄이면 배포본이 나옵니다.

```bash
python skills/guideline-lint/lint.py 원고.md            # 검사
python skills/guideline-design/publish.py 원고.md       # 배포본 PDF
```

`publish.py` 가 조판·인쇄·책 구성·목차 쪽번호·쪽번호를 차례로 돌립니다. 손으로 하면 명령이 열둘이고 `--skip` 값을 옮겨 적어야 하는데, 그 값을 도구끼리 주고받습니다. 100쪽 문서에 30초쯤 걸립니다.

```
[1/7] 조판 — 국정원 표준형
[2/7] 인쇄 (1차)
[3/7] 책 구성
  앞붙이 8쪽 · 본문 9쪽부터 · 빈 쪽 3장
[4/7] 목차 쪽번호
  39항목 중 39개를 찾았습니다
[5/7] 재조판·재인쇄
[6/7] 검증
  쪽이 밀린 항목 없음
[7/7] 쪽번호
  91쪽에 번호

공공기관 ROS 2 기반 ... 가이드라인.pdf
106쪽 · 188x257mm · 9.4MB · 30초
통제항목 156 / 156
```

**목차 쪽번호 때문에 두 번 인쇄합니다.** 조판하기 전에는 쪽을 알 수 없습니다.

표지와 장 간지에 그래픽을 넣으려면 테마를 바꿉니다.

```bash
python skills/guideline-design/publish.py 원고.md --theme art
```

원고가 아직 없다면 `guideline-writer` 부터 봅니다 — Claude Code 에서 "로봇 보안 가이드라인을 쓰고 싶다" 고 말하면 그 스킬이 골격부터 잡아 줍니다.

## 스킬

### `guideline-writer` — 집필

장르를 정하고 → 골격을 확정하고 → 통제항목·등급 체계를 설계하고 → 본문을 쓰고 → 부록을 붙이는 순서로 진행합니다.

```
가이드라인 써줘: 의료정보시스템 보안 가이드라인, 통제항목 체계 포함
```

- **장르를 먼저 묻습니다.** 법령형 지침 / 분야별 가이드라인 / 통제항목 체계 / 실무 안내서는 골격·번호 체계·종결어미가 전부 다릅니다. 섞으면 바로 어긋나 보입니다.
- **전개 축을 하나만 씁니다.** 보안대책 장은 수명주기별 또는 구성요소·연계유형별 중 하나입니다. 둘을 장 단위로 섞으면 같은 통제가 흩어집니다.
- 장르별 목차 템플릿 5종과 재사용할 통제 도메인 코드 27개를 함께 제공합니다.

### `guideline-lint` — 검사

```bash
python skills/guideline-lint/lint.py 원고.md
python skills/guideline-lint/lint.py 원고.md --genre control --quiet
```

**검사는 줄 단위입니다.** 원고는 한 문단을 한 줄로 쓰세요 — 폭에 맞춰 감아 두면 주기나 용어가 다른 줄에 떨어져 잘못 지적됩니다. 이미 감긴 원고는 `python skills/guideline-writer/unwrap.py 원고.md` 로 펼칩니다.

표준 라이브러리만 씁니다. 기계적으로 판정할 수 있는 23개 항목을 봅니다.

| 등급 | 항목 |
|---|---|
| 오류 | 의무 표현 혼용(`~하여야 한다`/`~해야 한다`), 경어체 혼입, 통제항목 ID 문법, 모항목 없는 강화 항목, 등급 포함 관계 위반, 본문에 없는 항목이 부록 점검표에 있음 |
| 경고 | 통제항목 설명의 `~해야 한다`, 주기 없는 통제, 법령 꺾쇠·캡션 혼용, 가운뎃점 `ㆍ`, 위치 표현("아래 표"), 제목 레벨 건너뛰기, 부록 점검표에서 빠진 통제항목, 등급별 요구 항목 수 불일치 |
| 참고 | 제목 깊이, 제목 번호 중복·건너뜀, 용어 혼용, 풀네임 없는 약어, 그림 없는 문서 |

같은 성격의 지적은 하나로 묶어 횟수와 예시 줄번호만 보여줍니다. 측정에 쓴 가이드라인 20종에 돌려 보면 문서당 오류 0~2건, 경고 0~4건이 나옵니다.

### `guideline-design` — 배포본 조판

원고를 **발행본 모양의 HTML·PDF 로** 만듭니다. 판면·여백·본문 크기·색은 짐작이 아니라 발행본 20종을 측정해 정했습니다.

가장 자주 틀리는 것이 판면입니다. **측정한 20종 중 A4 는 6종뿐이고 전부 짧은 지침입니다** — 본체 가이드라인의 판면은 188×257mm 가 중앙값입니다. 본문에 명조를 쓴 문서는 하나도 없고, 여백은 좌우가 상하보다 넓습니다.

**제본해서 펴낼 것을 전제로 짭니다.** 표지 - 속표지 - 문서 정보 - 목차가 저마다 홀수 쪽에서 시작하고, 앞 내용이 길어지면 뒤 차례가 밀립니다. 본문은 그다음 홀수 쪽에서 시작하며 거기가 1쪽입니다. 마지막은 판권지입니다.

```bash
python skills/guideline-design/publish.py 원고.md --theme nis
```

한 명령이 일곱 단계를 돌립니다. 단계별로 따로 부르고 싶으면 [SKILL.md](skills/guideline-design/SKILL.md) 에 `render` · `book` · `toc` · `paginate` · `coverart` 를 각각 쓰는 법이 있습니다.

목차 쪽번호 때문에 **두 번 인쇄합니다.** 조판하기 전에는 쪽을 알 수 없습니다. 빈 쪽도 원고에 박지 않고 인쇄한 뒤에 필요한 만큼만 끼웁니다 — 브라우저가 `break-before: recto` 를 무시하기 때문입니다.

결과 HTML 은 외부 자원을 하나도 받아오지 않아 망 분리 환경에서 그대로 열립니다.

기관이 이미 펴낸 책이 있으면 **거기서 재서 테마를 만듭니다.**

```bash
python skills/guideline-design/themegen.py 기관_작년_가이드라인.pdf --key ourorg
```

판면·여백·본문 크기·색을 재서 `themes/ourorg.py` 를 씁니다. 주조색은 제목 글자 색에서 찾고, 후보를 모두 주석에 적어 두니 한 줄 바꿔 끼우면 됩니다. 값 몇 개만 바꿀 때는 `--set accent=#1b3a6b` 처럼 줘도 됩니다.

**테마는 10종**입니다. `themes/` 에 파일 하나가 테마 하나라 직접 더할 수 있습니다 — [테마 만들기](skills/guideline-design/themes/README.md).

| | |
|---|---|
| `nis` `field` `control` `manual` `print` | 측정에서 바로 나온 판면 |
| `typo` `tab` `spec` `formal` | 타이포그래피 주도 · 장별 색과 측면 탭 · 기술 규격서 · 국가 간행물 |
| `art` | 전면 기하 아트워크 표지에 기관 로고 |

### 삽도

같은 스킬이 **삽도도 그립니다.** 색은 조판 테마를 따르므로 `nis` 면 남색, `print` 면 흑백이 되고, 캡션은 `[그림 N-M]` 규칙이라 `guideline-lint` 검사를 그대로 통과합니다.

```bash
python skills/guideline-design/figplan.py 원고.md --mode review   # 어디에 무엇이
python skills/guideline-design/figures.py 계획.json --theme nis   # 그린다
python skills/guideline-design/figplan.py 원고.md --mode auto --plan 계획.json
```

**두 단계인 이유가 있습니다.** `review` 가 내놓는 계획에는 명세가 비어 있고, 원고를 읽고 채워야 그립니다. 도구가 혼자 노드와 연결을 지어내지 못하게 막은 것입니다 — 원고에 없는 구성요소를 그린 도식은 그럴듯해서 더 위험합니다.

이미지 생성 API 는 쓰지 않습니다. 사진 같은 그래픽이 필요하면 계획에 적어 두고 발행기관이 따로 만듭니다. 규칙은 [삽도 — 무엇을, 언제, 어떻게](skills/guideline-design/references/figure-design.md)에 있습니다.

수치의 근거는 [발행본 디자인 측정값](skills/guideline-design/references/publication-design.md)에 있습니다.

### `govdoc-style` — 공문서 문체 일관성

korean-skills `style-guide` 에서 구조를 가져와 공문서 관례로 내용을 교체한 파생본입니다. 맞춤법이 아니라 **같은 문서 안에서의 일관성**을 봅니다 — 강제력 종결어미, 경어체 여부, 용어 통일, 법령 인용, 영문 병기, 숫자·날짜, 목록·제목 형식, 인용·강조.

원본과 무엇이 달라졌는지는 [SKILL.md 의 "원본과 달라진 점"](skills/govdoc-style/SKILL.md) 에 있습니다.

### `grammar-checker` · `humanizer` — korean-skills 원본

맞춤법·띄어쓰기·구두점 교정과 AI 문체 완화입니다. **수정 없이 복사했습니다.** 자세한 내용은 [grammar-checker/ORIGIN.md](skills/grammar-checker/ORIGIN.md), [humanizer/ORIGIN.md](skills/humanizer/ORIGIN.md) 를 보세요.

`humanizer` 는 초안이 AI가 쓴 듯 읽힐 때만 쓰세요. **통제항목 표나 조문처럼 형식이 정해진 부분에는 쓰지 마세요** — 형식이 곧 내용인 곳에서 문체를 다듬으면 규범의 세기가 흔들립니다.

> `humanizer` 의 참조 문서 하나가 업스트림의 `style-guide` 스킬을 상대 경로로
> 가리킵니다. 이 저장소는 `style-guide` 를 복사하지 않았으므로(대신 파생본
> `govdoc-style` 을 두었습니다) 그 링크 하나는 끊어져 있습니다. 원본을
> 수정하지 않는 것이 원칙이라 손대지 않았습니다 — 자세한 내용은
> [humanizer/ORIGIN.md](skills/humanizer/ORIGIN.md).

## 대화로 부르는 스킬

여섯 스킬 중 **셋만 스크립트**입니다(`lint.py` · `publish.py` · `figplan.py`). 나머지는 Claude Code 안에서 **말로 부릅니다.** 외울 명령은 없고, 무엇을 하려는지 말하면 설명이 맞는 스킬이 붙습니다.

이름을 콕 집어 부르려면 슬래시를 씁니다 — 플러그인으로 설치했다면 `/korea-security-guideline:guideline-writer`, 직접 복사했다면 `/guideline-writer` 입니다.

### 집필을 시작할 때

> ROS 2 기반 로봇 보안 가이드라인을 쓰려고 해. 공공기관용이야.

`guideline-writer` 가 붙어 **네 가지를 먼저 묻습니다.**

| 묻는 것 | 선택지 | 이게 바꾸는 것 |
|---|---|---|
| 장르 | 분야별 가이드라인 / 통제항목 체계 / 법령형 지침 / 실무 안내서 | 골격·번호 체계·종결어미 전부 |
| 대상 | 보호할 시스템·기술·분야 | 2장의 서술 방식 |
| 전개 축 | 수명주기별 / 구성요소·연계유형별 | 4장 절 구성 |
| 통제항목 체계 | 쓴다 / 안 쓴다 | ID 부여와 등급 매트릭스 필요 여부 |

답하면 **선행 자료가 있는지 먼저 찾고**(0단계) 골격을 잡습니다.

**바로 본문부터 쓰자고 하지 마세요.** 골격을 건너뛰면 나중에 통제항목을 하나 더할 때마다 부록과 등급표가 어긋납니다.

### 검사 결과를 고칠 때

```bash
python skills/guideline-lint/lint.py 원고.md
```

> 이 결과 붙여넣을게. 오류부터 고쳐줘.
> (lint 출력 붙여넣기)

줄 번호와 규칙 코드가 함께 나오므로 그대로 붙여넣으면 됩니다. **경고는 판단해서** 고치세요 — 가령 `TERM-MIX '보안사고' / '침해사고'` 는 ｢보안업무규정｣ 용어를 일부러 쓴 것일 수 있습니다.

### 법령 인용을 검증할 때

**이 단계가 가장 중요하고 자동화되지 않습니다.**

> ｢정보통신기반 보호법｣ 제5조 원문이야. 우리 원고 제1장 제3절의 인용이 맞는지
> 조문과 대조해줘.
> (법제처에서 복사한 조문 붙여넣기)

조문을 직접 가져다 붙이세요. 기억에 기대면 틀립니다. 이 저장소의 예제 원고를 만들며 **정부 발행물에서 그대로 옮겨 온 인용 오류 2건**을 이 방식으로 찾았습니다 — ｢국가정보원법｣의 조항 번호, ｢보안업무규정｣의 '보호구역/보호지역' 용어였습니다.

### 요약본을 만들 때

> 운영 담당자용 요약본을 만들어줘.

`guideline-writer` 가 **장르가 바뀐다는 것을 먼저 말해 줍니다.** 본문은 `~한다`, 요약본은 `~합니다` 이고 번호 체계도 `제N장/제N절` 에서 `N./N.N` 로 바뀝니다. 본문 문장을 그대로 옮기면 즉시 어긋나므로 재구성해야 합니다.

### 문체와 맞춤법을 볼 때

| 이렇게 말하면 | 붙는 스킬 |
|---|---|
| 문체 일관성 검사해줘 | `govdoc-style` |
| 맞춤법 봐줘 | `grammar-checker` |
| AI 가 쓴 티가 나는지 봐줘 | `humanizer` |

`humanizer` 는 **초안이 AI 처럼 읽힐 때만** 쓰세요. 통제항목 표나 조문처럼 형식이 곧 내용인 곳에 쓰면 규범의 세기가 흔들립니다.

### 삽도 명세를 채울 때

후보를 찾는 것까지는 스크립트가 하고, **명세는 대화로 채웁니다.**

```bash
python skills/guideline-design/figplan.py 원고.md --mode review
```

> figure-plan.json 이 후보 6곳을 짚었어. 원고를 읽고 정말 필요한 곳만 골라서
> 명세를 채워줘. 표로 이미 설명된 곳은 빼고.

예제 원고에서는 이렇게 물었더니 여섯 중 다섯이 이미 표로 설명돼 있어 하나만 남았습니다. **"여섯 개 다 그려줘" 라고 하지 마세요** — 표와 같은 내용을 두 번 보이면 어느 쪽이 정본인지 헷갈리고, 원고가 바뀔 때 한쪽만 고쳐집니다.

명세를 채울 때는 **근거를 어디서 가져왔는지** 함께 적게 하세요.

> 제4장 머리글의 서술만 근거로 써. 원고에 없는 구성요소는 넣지 마.

### 스킬이 안 붙을 때

말이 짧으면 일반 대화로 처리될 수 있습니다. 무엇을 하려는지 한 문장 더 붙이거나, `/guideline-writer` 처럼 이름을 직접 부르세요.

## 전체 과정

빈 폴더에서 배포본까지 실제로 가 보면 이렇습니다.

### 1. 같은 분야 발행물이 있는지 먼저 본다

`guideline-writer` 0단계입니다. 이미 나온 자료와 겹치면 **중복해서 쓰지 말고 역할을 나눕니다.** 이 저장소의 예제 원고도 작업 도중에 선행 자료를 발견해 구조를 다시 짰습니다 — 겹치는 108개 통제를 베끼는 대신 "그 자료를 따른다" 로 넘기고 ROS 2 고유 부분만 썼습니다.

### 2. 원고를 쓴다

`guideline-writer` 가 골격·통제 ID 체계·등급 매트릭스를 잡아 줍니다.

**한 문단을 한 줄로 씁니다.** 줄바꿈을 넣지 마세요. 검사기가 줄 단위로 보기 때문에, 한 문단을 여러 줄로 쪼개면 "주기가 없다" 같은 오탐이 납니다. 이미 쪼개져 있으면 `python skills/guideline-writer/unwrap.py 원고.md` 로 폅니다.

### 3. 쓰는 동안 계속 검사한다

```bash
python skills/guideline-lint/lint.py 원고.md
```

오류부터 고칩니다. 경고는 판단해서, 참고는 무시해도 됩니다. 통제항목을 하나 더하면 체크리스트·대응표·등급별 항목 수가 함께 밀리므로 **부록은 손으로 맞추지 말고 본문에서 다시 생성**하세요.

### 4. 법령 인용을 사람이 검증한다

**이 단계는 자동화하지 않습니다.** 조문 원문을 직접 대조하세요. 예제 원고를 만들며 정부 발행물에서 그대로 옮겨 온 인용 오류 2건을 찾았습니다 — 인용은 베끼면 틀린 채로 퍼집니다. [법령 조문을 확인하는 도구](#법령-조문을-확인하는-도구) 를 보세요.

### 5. 문체와 맞춤법을 본다

```bash
# govdoc-style · grammar-checker — Claude Code 에서 스킬로 부릅니다
```

요약본을 함께 낸다면 **장르가 바뀌므로 문체를 통째로 갑니다.** 본문은 `~한다`, 요약본은 `~합니다` 이고 번호 체계도 바뀝니다. 검사도 따로 돌립니다 — `lint.py 요약본.md --genre manual`.

### 6. 삽도가 필요한 곳을 본다

```bash
python skills/guideline-design/figplan.py 원고.md --mode review
```

후보를 짚어 주면 **정말 필요한지 사람이 판단합니다.** 예제 원고에서는 여섯 곳 중 다섯이 이미 표로 설명돼 있어 그리지 않았습니다. 표로 충분하면 그리지 않습니다 — 같은 내용을 두 번 보이면 어느 쪽이 정본인지 헷갈리고, 원고가 바뀔 때 한쪽만 고쳐집니다.

명세를 채우고 그립니다. **도구가 혼자 노드와 연결을 지어내지 못하게** 명세를 사람이 채우는 구조입니다 — 원고에 없는 구성요소를 그린 도식은 그럴듯해서 더 위험합니다.

```bash
python skills/guideline-design/figplan.py 원고.md --mode auto --plan 계획.json
python skills/guideline-design/figplan.py 원고-삽도.md --verify
```

`auto` 는 `<이름>-삽도.md` 를 새로 씁니다. 쓰기로 했다면 **원본 자리로 올리세요.** 원고가 둘이면 곧 어느 쪽이 정본인지 헷갈립니다.

### 7. 배포본을 뽑는다

```bash
python skills/guideline-design/publish.py 원고.md --theme nis
```

원고가 확정된 뒤에 합니다. 조판은 원고를 고치지 않습니다.

## 기관에 맞추기

### 기존 발행물에서 테마 뽑기

기관이 이미 펴낸 책이 있으면 거기서 재서 테마를 만듭니다.

```bash
python skills/guideline-design/themegen.py 기관_작년_가이드라인.pdf --key ourorg
python skills/guideline-design/publish.py 원고.md --theme ourorg
```

판면·여백·본문 크기·색을 재서 `themes/ourorg.py` 를 씁니다. **뼈대일 뿐이니 열어서 손보세요.** 주조색 후보를 주석에 적어 두니 한 줄 바꿔 끼우면 됩니다.

값 몇 개만 바꿀 때는 파일을 만들지 않아도 됩니다.

```bash
python skills/guideline-design/publish.py 원고.md --theme nis \
  --theme-set accent=#1b3a6b --theme-set body=10.2
```

### 기관 로고

원고 폴더에 `logos/` 를 만들고 기관이 준 파일(SVG·PNG)을 넣으면 표지에 올라갑니다. 폴더가 없으면 아무것도 그리지 않습니다.

**로고를 지어내지 않습니다.** 정부기관 로고를 만들어 붙이는 것은 위조입니다.

## 자주 걸리는 곳

만들면서 실제로 걸렸던 것들입니다.

**판면을 A4 로 잡는다.** 가장 흔한 실수입니다. 측정한 20종 중 A4 는 6종뿐이고 전부 6쪽짜리 지침이나 훈령입니다. 본체 가이드라인은 **188×257mm** 가 중앙값입니다. 본문에 명조를 쓴 문서는 하나도 없고, 여백은 좌우가 상하보다 넓습니다.

**원고를 여러 줄로 쪼갠다.** 검사기가 줄 단위로 봅니다. 한 문단을 한 줄로 쓰세요. `unwrap.py` 가 펴 줍니다.

**문단이 `[표 2-3]은 …` 으로 시작한다.** 캡션으로 오인될 수 있습니다. 캡션은 `[표 2-3] 제목` 처럼 **닫는 괄호 뒤에 공백**이 옵니다. 조판기는 이 규칙으로 가르지만, 원고를 쓸 때도 참조와 캡션을 섞지 마세요.

**원고가 둘이 된다.** `figplan --mode auto` 는 원본을 지키려고 새 파일을 씁니다. 쓰기로 했으면 원본 자리로 올리세요. 둘을 놔두면 곧 어느 쪽이 정본인지 헷갈립니다.

**Chrome 을 못 찾는다.** `--chrome` 으로 경로를 주세요. Edge 도 됩니다.

**통제항목 수가 맞지 않는다.** 배포본을 뽑을 때 `통제항목 156 / 156` 이 나옵니다. 숫자가 다르면 표가 잘렸거나 부록이 본문과 어긋난 것입니다.

**목차 쪽번호가 비어 있다.** 두 번 인쇄해야 나옵니다. `publish.py` 가 알아서 합니다. 단계별로 부를 때는 `toc.py` 를 건너뛰지 마세요.

**테마를 만들 때** — 음수 여백으로 색을 종이 끝까지 보내면 **글자가 잘립니다.** 색 바탕에 `print-color-adjust: exact` 가 없으면 인쇄에서 사라집니다. CSS 에 `%` 서식을 쓰면 터집니다. 자세한 것은 [테마 만들기](skills/guideline-design/themes/README.md).

**조판은 글로 검사되지 않습니다.** 만들고 끝내지 말고 **인쇄해서 보세요.** 이 저장소를 만드는 동안 눈으로만 잡힌 결함이 여럿이었고, 어느 것도 도구가 오류를 내지 않았습니다 — 잘린 제목, 캡션에 먹힌 문단, 빈 간지, 쪽번호 없는 90쪽 문서.

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

측정값을 그대로 규범으로 올리지 않은 곳이 한 군데 있습니다 — `정기적으로`는 원본 문서들에서 102회 쓰이지만, 주기가 없으면 점검할 수 없으므로 `연1회 이상` 같은 하한을 적도록 권고합니다. 이유는 [rules/06-notation.md](rules/06-notation.md) 의 숫자·기간 절에 있습니다.

## 법령 조문을 확인하는 도구

이 저장소는 법령 자료를 담지 않습니다. 집필 중 조문을 확인할 때는 다음을 씁니다.

- **법제처 국가법령정보 공동활용**(`open.law.go.kr`) — 조항호목 조회, 행정규칙, 신구법 비교 API. 1차 출처입니다.
- **[Legalize-KR Agent Skills](https://github.com/legalize-kr/agent-skills)** — 법령·판례·행정규칙·자치법규를 조회하는 에이전트용 스킬(Apache-2.0 · MIT). 인증키 없이 동작합니다.

**복사해 넣지 않은 이유는 법령이 시간에 민감하기 때문입니다.** 문체 규칙과 달리 법령 자료의 사본은 개정이 반영되지 않으면 틀린 조문을 자신 있게 인용하게 만듭니다. 필요하면 직접 최신본을 설치하시고, **발행 전에는 1차 출처와 대조하세요** — 자세한 내용은 [verification-log.md](skills/guideline-writer/references/verification-log.md).

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

플러그인으로 설치하면 스킬 이름이 플러그인별로 구분되므로 (`korea-security-guideline:grammar-checker` / `korean-skills:grammar-checker`) 둘을 함께 설치해도 충돌하지는 않습니다. 다만 같은 일을 하는 스킬이 두 개 로드되므로 한쪽만 두는 편이 깔끔합니다.

## 한계

- **규칙은 20종에서 뽑은 것입니다.** 발행처마다 자체 양식이 있으면 그것이 우선합니다. 스킬도 그렇게 동작합니다.
- **린터는 법령 인용의 정확성을 보지 않습니다.** 꺾쇠·띄어쓰기 같은 표기만 봅니다. 조문 번호는 사람이 원문과 대조해야 합니다. 조문 본문은 법제처 국가법령정보 공동활용(`open.law.go.kr`)의 조항호목 조회 API 로 가져올 수 있습니다 — **발행된 정부 간행물의 인용도 틀립니다.** 시험 집필에서 코퍼스 간행물의 ｢국가정보원법｣ 조문 인용을 따랐다가 틀린 사례가 나왔습니다 ([rules/06-notation.md](rules/06-notation.md)).
- **린터는 구조를 보지 않습니다.** 장·절 구성이 장르에 맞는지, 3장의 위협과 4장의 대책이 맞물리는지, 부록 체크리스트가 본문과 1:1인지는 사람이 봐야 합니다.
- **등급 검사는 병합 셀이 있는 표에서 동작하지 않습니다.** 열이 밀려 `●` 가 다른 칸으로 들어갑니다. 원고에서 병합 셀을 쓰지 마세요.
- **원본 가이드라인을 배포하지 않습니다.** `rules/` 에는 문장이 아니라 구조·체계· 표기 규칙과 측정 수치만 담았습니다.

## 라이선스

이 저장소가 만든 부분은 MIT입니다 — [LICENSE](LICENSE). 복사·파생한 korean-skills 부분은 Dale Seo의 MIT이며, 전문과 범위는 [NOTICE](NOTICE) 에 있습니다.
