# 테마 만들기

파일 하나가 테마 하나입니다. `_` 로 시작하는 파일은 읽지 않습니다. 여러 사람이
동시에 테마를 만들어도 서로 건드릴 일이 없습니다.

```python
THEME = dict(key='mytheme', label='이름', note='한 줄 설명', ...)
EXTRA_CSS = """ ... """
```

`python render.py --themes` 로 등록됐는지 확인합니다.

## THEME 에 쓰는 값

| 이름 | 뜻 | 기본값 |
|---|---|---|
| `key` | 테마 이름. `--theme` 에 쓰는 말. **필수** | — |
| `label` `note` | 목록에 보이는 이름과 설명 | |
| `page` | 판면 `(너비mm, 높이mm)` | `(188, 257)` |
| `margin` | 여백 `(좌, 우, 상, 하)` mm | `(25, 24, 19, 16)` |
| `body` | 본문 글자 크기 pt | `10.5` |
| `ink` `accent` `accent2` `tint` `rule` `soft` | 글자색·주조색·보조색·연한 바탕·괘선·흐린 글자 | 남색 계열 |
| `badge` | 배지 모서리 `pill`(둥근) `tag`(살짝) `square`(각진) | `pill` |
| `chapter` | 장을 `page`(새 쪽) 또는 `inline` | `page` |
| `cover` | 표지 꼴 `rule` `band` `side` `tint` | `rule` |
| `mark` | 등급 표시 글자 | `●` |

수치는 발행본 20종을 잰 값에서 가져오세요 —
[publication-design.md](../references/publication-design.md). 측정에 없는 값을
쓸 때는 **왜 그 값인지 주석으로 적으세요.**

## EXTRA_CSS

기본 CSS 뒤에 붙습니다. 무엇이든 다시 칠할 수 있습니다.

`%` 서식을 쓰지 않습니다. CSS 에는 `%` 와 중괄호가 흔해서 터집니다. 판면 값이
필요하면 **토큰**을 쓰세요 — `{{w}}` `{{h}}` `{{ml}}` `{{mr}}` `{{mt}}` `{{mb}}`
`{{body}}` `{{coverp}}`(본문 영역 높이) `{{coverh}}` `{{coverb}}`.

## 조판기가 내는 이름

| 자리 | 이름 |
|---|---|
| 쪽 | `.sheet` · 화면용 머리말 `.rh`(인쇄에선 숨김) |
| 표지 | `.cover.cv-*` > `.cvtop`(`.ckind` `.ctitle`) + `.cvbot`(`.cdate` `.corg` `.cver`) |
| 속표지 | `.halftitle > h1` |
| 문서 정보 | `.docinfo` |
| 목차 | `.tocpage` · 제목 `.toch` · 줄 `.toc`(장·부록은 `.toc.tc`) > `.tt` + `.tp`(쪽번호) |
| 장 간지 | `.chapter > .chno + h1` |
| 절 제목 | `h2 > .bdg + .ht` · 부록은 `h2.apx` |
| 항·목 | `h3` `h4` · 번호 문단 `.num > .n` |
| 캡션 | `.cap.cap-tbl` `.cap.cap-fig` > `.capn`(배지) + `.capt`(제목) |
| 표 | `table.tbl` · 통제항목표 `table.ctl`(등급 칸 `th.g` `td.g`, ID 칸 `td.idc`) |
| 삽도 | `figure > svg` |
| 보충 | `.note`(※) · `.implhead`(■) · `pre` · `code` · `.cid`(통제 ID) · `.law`(법령) |
| 판권지 | `.colophon > .colt + table.colt-t` |

## 반드시 지킬 것

- **외부 자원을 받아오지 않습니다.** 글꼴·스크립트·이미지 주소를 쓰지 마세요.
  망 분리 환경에서 파일 하나로 열려야 합니다. 글꼴은 설치된 것을 차례로 씁니다.
- **본문은 고딕입니다.** 발행본 20종 중 본문에 명조를 쓴 것은 없습니다.
- **색은 넷을 넘기지 마세요.** 짙은 색 하나, 중간 하나, 연한 바탕 하나, 보조 하나.
- 인쇄가 산출물입니다. 색 바탕에는 `print-color-adjust: exact` 를 주세요. 없으면
  인쇄에서 사라집니다.
- 종이 끝까지 색을 보내려면 **음수 여백을 쓰지 마세요.** 인쇄 영역 밖은 잘리고
  글자까지 함께 잘립니다. 이름 붙은 페이지를 쓰세요 —
  `@page cover{margin:0}` 과 `.cover{page:cover}`.
- `break-before: recto` 는 Chrome 이 무시합니다. 홀수 쪽 맞추기는 `book.py` 가
  인쇄 뒤에 합니다. 테마에서 신경 쓸 일이 아닙니다.
- 표 행과 삽도가 쪽을 넘어 잘리지 않게 `break-inside: avoid` 를 지키세요.
- 한글은 `word-break: keep-all` 입니다. 바꾸면 낱말이 잘립니다.

## 만들었으면 눈으로 보세요

조판은 글로 검사되지 않습니다.

```bash
python render.py ../../drafts/design-samples/sample-excerpt.md --theme mytheme
chrome --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="…/dist/mytheme.pdf" "file:///…/dist/mytheme.html"
python - <<'PY'
import fitz
from PIL import Image
d = fitz.open('dist/mytheme.pdf')
for i in range(min(6, d.page_count)):
    p = d[i].get_pixmap(dpi=100)
    Image.frombytes('RGB', (p.width, p.height), p.samples).save('p%d.png' % i)
PY
```

표지, 목차, 장이 바뀌는 쪽, 통제항목 표, 삽도가 있는 쪽을 봅니다. 글자가 잘리거나
겹치지 않는지, 색이 인쇄에 남는지 확인하세요.
