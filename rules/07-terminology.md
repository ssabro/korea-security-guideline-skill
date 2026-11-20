# 용어 선택 규칙 + 약어

## 용어 선택

같은 뜻의 두 표현 중 코퍼스가 어느 쪽을 쓰는지 측정한 결과입니다. 괄호 안은 20종 전체 등장 횟수.

| 쓰세요 | 쓰지 마세요 | 비고 |
|---|---|---|
| **사용자** (1,311) | 이용자 (71) | `이용자`는 대민서비스 문맥에서만 |
| **기관** (3,197) | 조직 (261) / 기업 (202) | 공공 문서의 주체는 `기관` |
| **정보시스템** (834) | 정보 시스템 (7) | 붙여 씁니다 |
| **취약점** (678) | 취약성 (22) | |
| **데이터** (2,413) | 자료 (384) | `자료`는 문서·간행물을 가리킬 때만 |
| **모니터링** (371) | 감시 (41) | |
| **침해사고** (48) | 보안사고 (16) | 붙여 씁니다 |
| **이상행위** (46) | 비정상 행위 (7) | 붙여 씁니다 |
| **접근통제** (77) | 접근 제어 (42) / 접근제어 (43) | 세 형태가 비슷하게 쓰이나 `접근통제`가 우세 |
| **암호화** (687) | — | 항상 붙여 씁니다 |

### 법정 용어는 코퍼스 선호보다 우선합니다

이 표는 **같은 뜻의 두 표현 중 무엇을 고를지**에 대한 것입니다. 한쪽이 법령이 정한 용어라면 그 선택지는 애초에 열려 있지 않습니다.

시험 집필에서 두 번 걸렸습니다.

| 코퍼스 선호 | 법정 용어 | 어떻게 처리했나 |
|---|---|---|
| 침해사고 | **보안사고** — ｢보안업무규정｣ 제38조가 정한 개념(비밀의 누설·분실, 국가보안시설의 파괴, 승인 없는 보호지역 출입) | 통일하지 않고 **구별을 본문과 용어 정의에 명시**. 범위가 다른 별개의 개념이다 |
| (해당 없음) | **보호지역** — ｢보안업무규정｣ 제34조. 중요도에 따라 제한지역·제한구역·통제구역 | '보호구역'으로 38회 잘못 쓴 것을 전역 치환 |

규칙은 둘입니다.

- **법령·훈령이 정의한 용어는 그대로 씁니다.** 더 흔한 말로 바꾸면 법적 근거를 가리키지 못합니다.
- **법정 용어와 일반 용어가 겹쳐 보이면 통일하지 말고 구별을 적습니다.** 용어 정의 부록에 범위 차이를 쓰고, 린터의 용어 혼용 지적은 그 경우 무시합니다.

### 보안대책 / 보안통제 / 보안 요구사항

세 용어가 모두 쓰이고(637 / 445 / 169) **구별이 있습니다.**

| 용어 | 뜻 | 쓰는 자리 |
|---|---|---|
| **보안대책** | 위협에 대응하는 조치. 설명·근거를 포함한 서술 단위 | 분야별 가이드라인의 본문 장·절 제목 |
| **보안통제** | ID가 붙은 요구사항 항목. 점검·이행 확인의 단위 | 통제항목 체계 문서, 표 |
| **보안 요구사항** | 시스템이 만족해야 하는 조건. 조달·설계 기준 | 도입요건·구축 기준 문서 |

**섞어 쓰지 마세요.** `제4장 보안대책` 아래에 ID 붙은 항목을 두면 그 항목은 `보안통제`이고, 장 제목은 `보안대책`입니다 — 코퍼스가 실제로 이렇게 씁니다. `보안조치`(39)는 드물어 피하는 편이 낫습니다.

### 동사 선택

| 선호 | 측정 | 용법 |
|---|--:|---|
| **적용한다** | 1,587 | 통제·정책을 대상에 거는 기본 동사 |
| **확인한다** | 1,091 | 상태를 보는 것 |
| **구축한다** | 859 | 시스템·체계를 새로 만드는 것 |
| **수립한다** | 786 | 정책·계획·절차를 만드는 것 |
| **제한한다** | 673 | 범위를 좁히는 것 (금지보다 약함) |
| **점검한다** | 590 | 주기적으로 보는 것 |
| **차단한다** | 578 | 통신·접근을 끊는 것 |
| **검토한다** | 554 | 판단을 포함해 보는 것 |

구분이 필요한 짝:

- `수립` vs `구축` — 문서·절차는 **수립**, 시스템·환경은 **구축**.
- `점검` vs `검토` — 기준 대조는 **점검**, 적정성 판단은 **검토**.
- `제한` vs `차단` vs `금지` — 범위 축소는 **제한**, 기술적 단절은 **차단**, 규범적 불허는 **금지**(05-normative-language.md).
- `준수`(292) vs `이행`(80) — 외부 규범은 **준수**, 자기 계획은 **이행**.

## 약어

코퍼스에서 풀네임과 함께 도입된 약어 94종 중, 보안 가이드라인에서 재사용 가치가 있는 것들입니다. 전체 목록은 `python tools/analyze_corpus.py` 로 재추출할 수 있습니다.

표의 풀네임은 **표준 표기로 정규화**했습니다. 코퍼스에는 `Identity Access Management`(IAM), `Common Vulnerabilities Exposures`(CVE), `De-Militarized Zone`(DMZ), `SW Bill of Materials`(SBOM)처럼 접속사가 빠지거나 줄인 형태가 섞여 있습니다. 새 문서에는 표준 표기를 쓰세요. `†` 표시는 코퍼스에 약어는 나오지만 풀네임 병기가 없어 외부 표준에서 가져온 항목입니다.

### 접근·인증

| 약어 | 풀네임 | 국문 |
|---|---|---|
| AAA | Authentication, Authorization, Accounting | 인증·인가·과금 |
| AD | Active Directory | |
| IAM | Identity and Access Management | 식별·접근 관리 |
| MFA | Multi-Factor Authentication | 다중요소 인증 |
| NAC | Network Access Control | 네트워크 접근통제 |
| PAM | Privileged Access Management | 특수권한 접근관리 |
| PDP / PEP | Policy Decision Point / Policy Enforcement Point | 정책 결정부 / 정책 집행부 |
| SSO | Single Sign-On | 통합 인증 |
| TOTP | Time-based One Time Password | 시간기반 일회용 비밀번호 |

### 암호·키

| 약어 | 풀네임 | 국문 |
|---|---|---|
| CRL | Certificate Revocation List | 인증서 폐지 목록 |
| FDE | Full Disk Encryption | 전체 디스크 암호화 |
| HSM | Hardware Security Module | 하드웨어 보안 모듈 |
| KCMVP | Korea Cryptographic Module Validation Program | 암호모듈 검증제도 |
| TPM | Trusted Platform Module | 신뢰 플랫폼 모듈 |
| TRNG | True Random Number Generator | 참 난수 발생기 |

### 망 분리·경계

| 약어 | 풀네임 | 국문 |
|---|---|---|
| CDS | Cross Domain Solution | 크로스도메인 보안 |
| CDR † | Content Disarm and Reconstruction | 콘텐츠 무해화 |
| DMZ | Demilitarized Zone | 비무장지대 |
| DPI | Deep Packet Inspection | 심층 패킷 분석 |
| MLS | Multi Level Security | 다중등급보안 |
| N2SF | National Network Security Framework | 국가 망 보안체계 (코퍼스 734회) |

### 탐지·대응

| 약어 | 풀네임 | 국문 |
|---|---|---|
| DLP | Data Loss Prevention | 정보유출 방지 |
| IDS / IPS † | Intrusion Detection / Prevention System | 침입 탐지 / 방지 시스템 |
| LOTL | Living off the Land | 정상 도구 악용 공격 |
| NDR † | Network Detection and Response | |
| NTA | Network Traffic Analysis | 네트워크 트래픽 분석 |
| SIEM | Security Information and Event Management | 보안정보·이벤트 관리 |
| SOAR | Security Orchestration, Automation and Response | 보안 오케스트레이션·자동화·대응 |
| UEBA | User and Entity Behavior Analytics | 사용자·엔터티 행위 분석 |

### 취약점·공급망

| 약어 | 풀네임 | 국문 |
|---|---|---|
| CVE | Common Vulnerabilities and Exposures | 공통 취약점 식별자 |
| CVSS | Common Vulnerability Scoring System | 공통 취약점 등급 체계 |
| KEV | Known Exploited Vulnerabilities | 알려진 악용 취약점 |
| NVD | National Vulnerability Database | 미국 취약점 데이터베이스 |
| SBOM | Software Bill of Materials | 소프트웨어 구성명세서 |
| SCA | Software Composition Analysis | 소프트웨어 구성 분석 |
| SPDX | Software Package Data Exchange | 코퍼스 28회, SBOM 표준 포맷 |
| VDP | Vulnerability Disclosure Program | 취약점 신고 제도 |

### 제도·프레임워크

| 약어 | 풀네임 | 국문 |
|---|---|---|
| CRA | Cyber Resilience Act | 사이버복원력법 (EU) |
| GSCP | Government Security Classifications Policy | 정부 보안등급 정책 (영국) |
| ISM | Information Security Manual | 정보보안 매뉴얼 (호주) |
| RMF | Risk Management Framework | 위험관리 프레임워크 |
| OWASP | Open Worldwide Application Security Project | |

### 단말·자산

| 약어 | 풀네임 | 국문 |
|---|---|---|
| CSP | Cloud Service Provider | 클라우드 서비스 제공자 |
| DRM | Digital Rights Management | 디지털 저작권 관리 |
| MDM | Mobile Device Management | 모바일 단말 관리 |
| OEM | Original Equipment Manufacturer | |

## 약어를 쓸 때

1. **첫 등장에 풀네임을 병기합니다** — `SBOM(Software Bill of Materials)`. 06-notation.md 의 병기 형태 중 하나로 통일.
2. **약어가 10개를 넘으면 부록에 약어표를 둡니다.** 코퍼스 5/20 문서가 그렇습니다.
3. **국문 번역어가 정착된 것은 국문을 본문에, 약어를 괄호에 둡니다** — `다중요소 인증(MFA)`. 정착되지 않은 것은 약어를 본문에 둡니다 — `SBOM`.
4. **국내 제도 약어는 풀네임보다 국문 명칭이 먼저입니다** — `암호모듈 검증제도(KCMVP)`.
5. 외국 제도를 인용할 때는 **어느 나라인지 밝힙니다** — `정부 보안등급 정책(GSCP, 영국)`. 코퍼스는 미국·영국·호주·EU·일본 제도를 비교 근거로 자주 인용합니다.
