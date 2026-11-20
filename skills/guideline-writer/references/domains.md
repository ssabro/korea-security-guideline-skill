# 재사용할 통제 도메인 코드

국가 망 보안체계(N2SF)가 정한 6 대항목 / 27 도메인입니다. 접근통제·인증·암호 같은 공통 영역은 **이미 코드가 있으므로 재사용하세요.** 새로 만들면 두 체계를 대조할 수 없게 됩니다.

항목 수는 N2SF의 실제 항목 수(총 274개)이고, 새 문서에서 같은 수를 채울 필요는 없습니다. 도메인을 쓸지 말지, 몇 항목을 둘지는 분야에 따라 다릅니다.

## 권한

| 코드 | 국문 | English | N2SF 항목수 |
|---|---|---|--:|
| LP | 최소권한 | Least Privilege | 13 |
| IV | 신원검증 | Identity Verification | 5 |
| IM | 식별자관리 | Identifier Management | 5 |
| AC | 계정관리 | Account Management | 14 |

## 인증

| 코드 | 국문 | English | N2SF 항목수 |
|---|---|---|--:|
| MA | 다중요소인증 | Multi-Factor Authentication | 6 |
| EI | 외부인증수단 | External Identity | 3 |
| DA | 단말인증 | Device Authentication | 7 |
| AU | 인증보호 | Authentication Protection | 10 |
| AP | 인증정책 | Authentication Policy | 8 |
| AM | 인증수단 | Authentication Method | 11 |
| LI | 로그인 | Login | 12 |

## 분리 및 격리

| 코드 | 국문 | English | N2SF 항목수 |
|---|---|---|--:|
| SG | 분리 | Segregation | 14 |
| IS | 격리 | Isolation | 6 |

## 통제

| 코드 | 국문 | English | N2SF 항목수 |
|---|---|---|--:|
| IF | 정보흐름 | Information Flow | 20 |
| EB | 외부경계 | External Boundary | 20 |
| CD | 크로스도메인 보안 | Cross Domain Solution | 17 |
| RA | 원격접속 | Remote Access | 10 |
| SN | 세션 | Session | 12 |
| WA | 무선망접속 | Wireless Network Access | 8 |
| BC | 블루투스연결 | Bluetooth Connection | 1 |

## 데이터

| 코드 | 국문 | English | N2SF 항목수 |
|---|---|---|--:|
| EK | 암호 키 관리 | Encryption Key Management | 9 |
| EA | 암호 모듈 사용 | Encryption Technology Application | 3 |
| DT | 데이터전송 | Data Transmission | 6 |
| DU | 데이터사용 | Data Usage | 8 |

## 정보자산

| 코드 | 국문 | English | N2SF 항목수 |
|---|---|---|--:|
| MD | 모바일단말 | Mobile Device | 13 |
| DV | 하드웨어 | Device | 14 |
| IN | 정보시스템 구성요소 | Information System Component | 19 |

---

## 도메인을 새로 만들 때

- **통제 대상이 분리되면 도메인을 나눕니다.** 항목 수로 맞추려 하지 마세요 — 블루투스(BC)는 N2SF에서 1개뿐이지만 독립 도메인입니다.
- 코드는 **영문 명칭의 머리글자 2글자**입니다. 한글 명칭에서 따지 않습니다 (최소권한 → LP, 계정관리 → AC).
- 위 27개와 겹치지 않는 2글자를 고르세요. 남은 조합은 많지만, 기존 코드와 한 글자만 다른 것(예: `AB`, `AE`)은 오독을 부르니 피하세요.
- 분야 고유 도메인의 예:
- 의료정보시스템 → `MI` 의료기기 / `PH` 환자정보보호
- 산업제어시스템 → `OT` 운영기술망 / `PL` 제어로직
- AI 시스템 → `MO` 모델보호 / `TD` 학습데이터

## 대항목을 새로 만들 때

6 대항목(권한 / 인증 / 분리 및 격리 / 통제 / 데이터 / 정보자산)은 기술적 통제만 담습니다. **관리적 통제**(정책·조직, 자산 관리, 교육, 물리 보안, 침해사고 대응)는 N2SF 체계에 대항목이 없으므로 새로 추가해야 합니다.

관리적 통제는 기술 구성요소에 매핑되지 않으므로 별도 대항목으로 분리하고, 문서 구성에서도 별도 장으로 두는 것이 코퍼스의 처리 방식입니다 (병원정보시스템 가이드라인 `제4장 관리적 보안대책`).
