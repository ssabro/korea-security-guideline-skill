# 이 스킬은 이 저장소가 만든 것이 아닙니다

`humanizer` 는 **korean-skills(Dale Seo)의 스킬을 수정 없이 복사한 것**입니다.
한 글자도 바꾸지 않았습니다.

| | |
|---|---|
| 원저작자 | Dale Seo — https://github.com/DaleSeo |
| 원출처 | https://github.com/DaleSeo/korean-skills |
| 라이선스 | MIT License, Copyright (c) 2026 Dale Seo |
| 복사 시점 | 2026-11-19 |
| 리비전 | `ae12ba2` |

라이선스 전문은 저장소 루트의 [NOTICE](../../NOTICE) 와
[third-party/korean-skills-LICENSE](../../third-party/korean-skills-LICENSE) 에 있습니다.

## 왜 여기 들어 있나

이 저장소의 가이드라인 집필 스킬은 맞춤법 교정과 AI 문체 완화를 korean-skills 에
맡깁니다. 한 번에 설치되도록 함께 넣었습니다.

**업스트림을 직접 쓰고 싶으면** korean-skills 를 설치하고 이 복사본을 지우세요.
원저작자가 관리하는 최신본을 쓰는 것이 낫습니다.

```bash
claude /plugin marketplace add daleseo/korean-skills
```

## 수정하지 마세요

여기 있는 파일을 고치면 업스트림에서 다시 받을 때 덮어씁니다. 변경이 필요하면
**파생본을 별도 이름으로** 만들고 무엇을 바꿨는지 밝히세요.
`skills/govdoc-style` 이 그 예입니다 — korean-skills 의 `style-guide` 에서
구조를 가져와 공문서 관례로 내용을 교체했고, 변경 내역을 SKILL.md 에 적었습니다.

## 갱신

```bash
git clone --depth 1 https://github.com/DaleSeo/korean-skills /tmp/ks
rm -rf skills/humanizer
cp -r /tmp/ks/skills/humanizer skills/
cp /tmp/ks/LICENSE third-party/korean-skills-LICENSE
git -C /tmp/ks rev-parse --short HEAD    # 위 표의 리비전과 NOTICE 를 갱신
```

갱신 후 이 ORIGIN.md 를 다시 넣어야 합니다(원본에는 없는 파일입니다).

## 이 복사본에서 끊어진 링크 하나

`references/structure-patterns.md` 안에 업스트림의 `style-guide` 스킬을 가리키는
상대 링크가 있습니다.

```
../../../style-guide/references/tone-consistency.md
```

이 저장소는 `style-guide` 를 복사하지 않았으므로(대신 공문서 파생본
`govdoc-style` 을 만들었습니다) **그 링크는 끊어져 있습니다.**
원본을 수정하지 않는 것이 원칙이라 손대지 않았습니다.

그 문서가 필요하면 업스트림 korean-skills 를 설치하거나
[GitHub에서 직접](https://github.com/DaleSeo/korean-skills/blob/main/skills/style-guide/references/tone-consistency.md)
보세요.

## 알아 두면 좋은 점

`humanizer/SKILL.md` 의 `description` 에 연구 인용과 수치
("KatFishNet 논문, 94.88% AUC 정확도", "40가지 패턴")가 들어 있습니다.
`description` 은 매 요청에 로드되므로, 라우팅 판단에 쓰이지 않는 수치가 비용을
만들고 구현이 바뀌면 조용히 틀린 값이 됩니다.

**원본 보존이 복사의 원칙이라 고치지 않았습니다.** 이 저장소가 직접 만든
스킬에는 같은 패턴을 쓰지 않았습니다 — `description` 에는 무엇을 언제 쓰는지만
적고 수치와 근거는 본문에 두었습니다.
