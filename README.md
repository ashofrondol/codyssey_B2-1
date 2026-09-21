# budget_app — 파일 기반 가계부 콘솔 프로그램

Python 표준 라이브러리만으로 만든 콘솔 가계부입니다. JSONL 영구 저장, 제너레이터 스트리밍, 데코레이터 분리, 생성자 불변식 검증, 설정·문자열 중앙화(config), 타입 힌트, 모듈화 구조를 갖췄습니다.

> **구조를 먼저 그림으로 보려면** `docs/budget-app-atlas.html` 을 브라우저로 여세요 — 계층·데이터 모델·실행 흐름·저장소 메커니즘을 도면 27장으로 그린 도면집입니다. 자세한 안내는 아래 **14. 도면집**.

## 0. 과제 명세 (원본 미션 요구사항)

> 출처: `codyssey_assignments/B2-1.pdf` — 원문 요구사항을 그대로 옮기고, 해설은 💡 로 구분했다.

---

### 0.1 미션 한눈에 보기

| 항목 | 내용 |
| --- | --- |
| 분야 | AI/SW 기초 |
| 구분 | Python과 Git 심화 |
| 학습시간 | 60시간 |
| 미션 제목 | **나만의 용돈 기입장 프로그램 만들기** |
| 산출물 | 10가지 기능이 정상 동작하는 애플리케이션 1개 |
| 개발 환경 | Python 3.10 이상 |
| 제약 | 표준 라이브러리만 사용 (pip install 금지) |

#### 원문 — 1. 미션 소개

> '작은 서비스'란 기능이 많은 게 아니라 예외 상황에서도 데이터가 안전한 것을 말합니다. 이번에 만드는 건 콘솔 가계부인데, 제너레이터 스트리밍, 데코레이터 분리, 타입 힌트까지 구조를 제대로 챙깁니다. 단순한 프로그램이 아니라, 유지보수 가능한 설계로 완성한다는 관점으로 접근하세요.
>
> 이번 미션은 Python으로 파일 입출력 기반의 가계부 콘솔 프로그램을 구현하는 과제입니다. 수입과 지출 내역을 단순히 저장하는 수준을 넘어, 수정/삭제, 검색, 월별 요약, 카테고리 관리, 예산 초과 경고까지 포함한 "작은 서비스" 형태로 완성합니다.
>
> 학습자는 터미널에서 명령어를 입력해 내역을 추가하고(add), 목록을 조회하며(list), 특정 조건으로 검색하고(search), 월별 요약과 카테고리 리포트를 출력하고(summary), 데이터를 내보내고(export), 기존 파일을 가져오는(import) 기능을 구현합니다. 데이터는 프로그램 종료 후에도 유지되도록 JSONL 또는 CSV 파일로 영구 저장해야 합니다.
>
> 또한, 저장 파일을 한 번에 모두 읽지 않고 제너레이터로 스트리밍 처리하며, 데코레이터로 공통 기능(예외 처리, 실행 로그, 실행 시간 측정 등)을 분리합니다. 타입 힌트를 적용해 함수와 데이터 구조의 계약을 명확히 하고, 모듈 분리로 유지보수 가능한 구조를 설계합니다.

#### 💡 (해설) 이 과제가 진짜로 묻는 것

> 💡 **1) "기능 10개 구현"은 껍데기다.** 채점의 무게중심은 *기능 목록*이 아니라 *구조*에 있다. 같은 기능을 한 파일 500줄로 짜면 탈락, 모델/저장소/서비스/CLI로 쪼개면 통과다. 명세가 "최소 3개 모듈", "최소 2개 클래스"를 **숫자로 못 박은** 이유가 여기 있다.
>
> 💡 **2) "데이터가 안전한 것"이 핵심 주제다.** 파일 기반 저장에서 update/delete는 본질적으로 위험한 연산이다(쓰는 도중 죽으면 원본이 날아간다). 명세가 "전체 재작성/임시 파일/원자적 교체(권장)"를 콕 집어 언급하고, 보너스에까지 "저장 원자성 강화"를 넣은 것은 **파일 기반 트랜잭션 감각**을 기르라는 뜻이다.
>
> 💡 **3) 메모리에 다 올리지 말라는 훈련이다.** `list`/`search`를 "제너레이터 기반 스트리밍"으로 구현하라는 조건은, `json.load(open(f))` 한 줄로 끝내는 습관을 깨려는 의도다. 평가자는 "왜 유리한가"를 반드시 물어본다(체크리스트 3장).
>
> 💡 **4) 횡단 관심사(cross-cutting concern) 분리를 배운다.** 예외 처리·로그·실행 시간 측정은 모든 명령에 공통으로 필요한데, 이를 각 함수에 복붙하지 않고 데코레이터로 뽑아내는 것이 요구사항이다.
>
> 💡 **5) CLI를 "프로그램"이 아니라 "인터페이스 계약"으로 본다.** `--help`, `--` 옵션 표기, 종료 코드(0 / 0이 아님), 스택트레이스 금지는 전부 *유닉스 CLI 관례*다. 내 프로그램이 다른 프로그램(쉘 스크립트, CI)에 의해 호출될 수 있다는 관점을 요구한다.

---

### 0.2 최종 산출물 (제출물)

#### 원문 — 2. 최종 결과물

> 다음 10가지 기능이 정상 동작하는 애플리케이션 1개를 완성한다.

| # | 기능 | 입력/요청 | 출력/화면 |
| --- | --- | --- | --- |
| 1 | 거래 추가(add) | 대화형 입력(날짜, 타입, 카테고리, 금액, 메모/태그) | 저장 성공 메시지 + 생성된 거래 id |
| 2 | 거래 목록(list) | `-limit` 등 옵션 | 최신순 거래 리스트(스트리밍 처리) |
| 3 | 거래 검색(search) | `-from`/`--to` , `-category` , `-type` , `-q` , `-tag` | 조건에 맞는 거래 리스트(최신순) |
| 4 | 월별 요약(summary) | `-month YYYY-MM` , `-top N` | 총수입/총지출/잔액 + 카테고리별 지출 TOP N |
| 5 | 예산 설정/조회(budget) | `budget set --month YYYY-MM --amount 금액` | 저장 성공 메시지 + summary에서 예산 사용률/초과 경고 |
| 6 | 카테고리 관리(category) | `category add/list/remove` | 카테고리 목록/추가/삭제 결과(사용 중 카테고리 처리 포함) |
| 7 | 거래 수정(update) | `-id` 기반(옵션 방식 또는 대화형 중 1개로 고정) | 수정 성공/실패 메시지(없는 id 처리 포함) |
| 8 | 거래 삭제(delete) | `delete --id <id>` | 삭제 성공/실패 메시지(없는 id 처리 포함) |
| 9 | 가져오기/내보내기(import/export) | `import --from <csv>` , `export --out <csv> --month ...` 또는 `-from`/`--to` | 처리 건수 출력 + CSV 파일 생성/반영 확인 |
| 10 | 추가 조건(최종 결과물의 필수 구성) | (아래 참조) | (아래 참조) |

**10. 추가 조건 (최종 결과물의 필수 구성)** — 원문 그대로:

- 데이터는 **3개 이상 파일로 영구 저장**되어야 한다. (예: transactions / categories / budgets)
- `README.md` 에 **실행 방법, 저장 파일 위치/형식, 주요 명령 예시, import/export CSV 스키마**가 포함되어야 한다.

#### 제출 증거 체크리스트

- [ ] 애플리케이션 1개 (10가지 기능 정상 동작)
- [ ] 저장 파일 3개 이상 (`transactions.<fmt>` / `categories.<fmt>` / `budgets.<fmt>`)
- [ ] `README.md` — 실행 방법
- [ ] `README.md` — 저장 파일 위치/형식
- [ ] `README.md` — 주요 명령 예시
- [ ] `README.md` — import/export CSV 스키마
- [ ] `README.md` — `update` 방식(옵션 기반 / 대화형 기반) **명확히 고정 명시** (R6-3 참조)
- [ ] `README.md` — 카테고리 파일이 비어있을 때의 동작(안 A / 안 B) 명시 (R3-5 참조)

> 💡 (해설) 마지막 두 줄은 PDF가 "문서에 명확히 고정해야 합니다", "동작을 명확히 하세요"라고 요구한 **선택지 고정 의무**를 제출 증거로 옮긴 것이다. 어느 쪽을 골랐든 상관없지만, **고르지 않았거나 문서에 안 적었으면 미충족**이다.

---

### 0.3 과제 목표 — 수료 후 스스로 설명할 수 있어야 하는 것

#### 원문 — 3. 과제 목표

> 이 과제를 마친 후, 학습자는 아래를 스스로 설명할 수 있어야 한다.

- [ ] **G1.** 파일 기반 저장(JSONL/CSV)으로 데이터를 영구 저장하고, CRUD/검색/요약/입출력을 구현할 수 있다.
- [ ] **G2.** 콘솔 프로그램을 클래스/모듈로 구조화하고, 각 계층(모델/저장소/서비스/CLI)의 책임을 설명할 수 있다.
- [ ] **G3.** `yield` 기반 제너레이터로 대용량 파일도 스트리밍 처리하는 이유와 동작 방식을 설명할 수 있다.
- [ ] **G4.** 데코레이터로 공통 관심사(로그/예외/시간 측정)를 분리한 구조와 이유를 설명할 수 있다.
- [ ] **G5.** 타입 힌트를 통해 입출력 계약을 명확히 했을 때 얻는 이점을 실제 코드 예로 설명할 수 있다.

---

### 0.4 기능 요구 사항 (필수)

> 원문 — 4. 기능 요구 사항: **다음 요구사항을 모두 만족해야 한다.**

> 💡 (해설) 아래 `R#` ID는 README/검증 편의를 위해 **내가 부여한 것**이며 PDF에는 없다. 항목의 내용·순서·문구는 원문 그대로다. PDF 원문의 번호는 소제목에 병기했다.

#### R1. 실행 및 입력 방식 (원문 4-1)

- [ ] **R1-1.** 실행 예시는 아래 중 하나를 권장합니다.
  ```
  python -m budget_app <command> [options]
  ```
- [ ] **R1-2.** 모든 명령은 `--help` 옵션으로 사용 방법이 출력되어야 합니다.
- [ ] **R1-3.** 입력 기본 방식은 **"대화형"** 입니다.
  - 예: `add` 실행 시 날짜/타입/카테고리/금액 등을 `input()` 으로 순차 입력
- [ ] **R1-4.** 단, 아래 항목은 **옵션 인자 방식도 허용(권장)** 합니다.
  - `search` , `list` , `summary` , `export` , `import` , `delete`
  - `update` 는 "옵션 방식 또는 대화형" 중 하나를 선택해도 되나, **문서에 명확히 고정해야 합니다**(아래 6번 참고).
- [ ] **R1-5.** 옵션 표기는 **리눅스 표준인 `--` 로 통일**해야 합니다.
  - 예: `--help` , `--limit` , `--from` , `--to` , `--month`

#### R2. 데이터 모델 (원문 4-2)

- [ ] **R2-1.** 거래 내역(Transaction)은 **최소 아래 필드**를 포함해야 합니다.
  - `id` (유일), `type` (income/expense), `date` (YYYY-MM-DD), `amount` (양수), `category` , `memo` (선택), `tags` (선택)
- [ ] **R2-2.** 데이터 모델은 **`dataclass` 또는 그에 준하는 구조**로 정의해야 합니다.
- [ ] **R2-3.** **최소 2개 이상의 클래스**를 사용해야 합니다.
  - 예시: `Transaction` , `TransactionRepository` , `BudgetStore` , `CategoryStore` , `BudgetService` 등
- [ ] **R2-4.** 입력 검증 — 날짜 형식 오류, 음수/0 금액, 허용되지 않은 type, 존재하지 않는 category 등은 **재입력 요구 또는 오류 메시지 출력**으로 처리합니다.

#### R3. 저장 정책 (원문 4-3)

- [ ] **R3-1.** 저장 포맷은 **JSONL 또는 CSV 중 1개**를 선택합니다.
- [ ] **R3-2.** 저장 파일은 **3개 이상(필수)** 로 분리해 영구 저장합니다.
  - `transactions.<fmt>` , `categories.<fmt>` , `budgets.<fmt>`
- [ ] **R3-3.** 기본 저장 폴더는 `./data` 를 권장하며, **옵션으로 변경 가능**해야 합니다 (예: `-data-dir`).
  - > 💡 (해설) PDF 본문 표기는 `-data-dir` 이지만, R1-5가 "옵션 표기는 `--` 로 통일"을 요구하므로 실제 구현은 `--data-dir` 로 보는 것이 일관적이다. (추론)
- [ ] **R3-4.** 초기 실행(저장 파일이 없을 때) — 파일이 없으면 **자동 생성**하거나, **"초기화 안내 메시지"** 를 출력해야 합니다.
- [ ] **R3-5.** 카테고리 파일이 비어있으면 아래 중 하나를 택해 **동작을 명확히** 하세요.
  - (안 A) 기본 카테고리 자동 생성 (예: `food`, `transport`, `rent`, `etc`)
  - (안 B) `category add` 를 먼저 하도록 안내하고 `add` 를 막음

#### R4. add(거래 추가) (원문 4-4)

- [ ] **R4-1.** `add` 실행 후 **대화형으로 필드를 입력받아** 거래를 저장해야 합니다.
- [ ] **R4-2.** category는 **등록된 목록에 존재**해야 합니다 (없으면 안내 후 재입력/등록 유도).
- [ ] **R4-3.** 저장 완료 시 **생성된 `id` 를 사용자에게 출력**해야 합니다.

#### R5. list(목록 조회) (원문 4-5)

- [ ] **R5-1.** `list` 는 **최신순**으로 거래를 출력해야 합니다.
- [ ] **R5-2.** `--limit N` 옵션을 지원해야 합니다 (**기본값 제공**).
- [ ] **R5-3.** 파일 전체를 한 번에 로드하지 않고, **제너레이터 기반 스트리밍 처리**로 구현해야 합니다.

#### R6. update/delete(수정/삭제) (원문 4-6)

- [ ] **R6-1.** `delete --id <id>` 로 특정 거래를 삭제할 수 있어야 합니다.
- [ ] **R6-2.** 존재하지 않는 id는 **"없는 데이터"로 처리하고 사용자 메시지를 출력**해야 합니다.
- [ ] **R6-3.** `update` 는 아래 중 **하나의 방식으로 문서에 명확히 고정**해 구현해야 합니다.
  - (안 A) 옵션 기반: `update --id <id> [--date ...] [--type ...] [--category ...] [--amount ...] [--memo ...] [--tags ...]`
  - (안 B) 대화형 기반: 수정할 필드만 선택/재입력 받는 흐름
- [ ] **R6-4.** 파일 기반 저장에서 update/delete는 **"전체 재작성 / 임시 파일 / 원자적 교체(권장)"** 등 **안정성을 고려**해야 합니다.

#### R7. search(검색) (원문 4-7)

- [ ] **R7-1.** 조건 기반 검색을 지원해야 합니다.
  - 기간: `--from` , `--to`
  - 카테고리: `--category`
  - 타입: `--type`
  - 메모 키워드: `--q`
  - 태그: `--tag`
- [ ] **R7-2.** 검색 결과는 **최신순**으로 출력해야 합니다.
- [ ] **R7-3.** **스트리밍 처리(제너레이터 기반)를 유지**해야 합니다.

#### R8. summary(월별 요약) (원문 4-8)

- [ ] **R8-1.** `summary --month YYYY-MM` 입력을 받아 해당 월의 요약을 출력해야 합니다.
- [ ] **R8-2.** 출력 항목:
  - 총 수입, 총 지출, **잔액(총수입-총지출)**
  - 카테고리별 지출 합계 **TOP N** (`-top` 옵션 지원)
- [ ] **R8-3.** 데이터가 없는 달은 **"데이터 없음"을 명확히 출력**해야 합니다.

#### R9. budget(예산) (원문 4-9)

- [ ] **R9-1.** `budget set --month YYYY-MM --amount <금액>` 으로 월 예산을 저장해야 합니다.
- [ ] **R9-2.** `summary` 실행 시 예산이 설정되어 있으면 아래를 **함께 출력**해야 합니다.
  - 예산 대비 **사용률(%)**
  - **초과 여부**(초과 시 경고 문구)
- [ ] **R9-3.** 예산 데이터도 **반드시 영구 저장**되어야 합니다.

#### R10. category(카테고리 관리) (원문 4-10)

- [ ] **R10-1.** `category add/list/remove` 를 제공해야 합니다.
- [ ] **R10-2.** 카테고리 삭제 시, **해당 카테고리를 사용하는 내역이 존재하면**
  - 삭제를 막거나
  - 대체 카테고리를 요구해야 합니다

#### R11. import/export(가져오기/내보내기) (원문 4-11)

- [ ] **R11-1.** `import --from <csv>` 로 거래를 일괄 등록한다.
  - > 💡 (해설) PDF 추출 텍스트에는 `import --from \로 거래를 일괄 등록한다.` 로 꺾쇠(`<csv>`)가 유실되어 있다. 동일 PDF의 "최종 결과물" 9번 항목에 `import --from <csv>` 로 명시되어 있으므로 그 표기를 채택했다.
- [ ] **R11-2.** `export --out <csv>` 로 조건에 맞는 거래를 CSV로 저장한다.
- [ ] **R11-3.** export는 `--month YYYY-MM` **또는** `--from YYYY-MM-DD --to YYYY-MM-DD` **중 하나 이상 조건을 필수로 받는다.**
- [ ] **R11-4.** import/export는 아래 **CSV 최소 스키마를 고정**한다.

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | YYYY-MM-DD |
| `type` | Y | income / expense |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표(,) 구분 문자열 |
| **공통: UTF-8, 헤더 포함** |   |   |

#### R12. 데코레이터(Decorator) (원문 4 하위 재번호 1)

- [ ] **R12-1.** 공통 관심사(예: 예외 처리 / 로그 / 시간 측정) 데코레이터를 **1개 이상 구현하고 실제 적용**한다.

#### R13. 예외 처리 및 종료 코드 (원문 4 하위 재번호 2)

- [ ] **R13-1.** 오류는 **스택트레이스 대신 원인 + 해결 힌트로 출력**한다.
- [ ] **R13-2.** **정상 종료는 0, 오류 종료는 0이 아닌 값**으로 종료한다.

#### R14. 모듈화(구조화) (원문 4 하위 재번호 3)

- [ ] **R14-1.** 한 파일에 몰아넣지 않고 **최소 3개 이상 모듈로 분리**한다.
- [ ] **R14-2.** (권장) **CLI / 서비스 / 저장소(파일 I/O) / 모델(데이터 구조)** 로 책임을 나눈다.

#### R15. 산출물 문서화 (원문 2-10 추가 조건, 필수)

- [ ] **R15-1.** 데이터는 **3개 이상 파일로 영구 저장**되어야 한다. (예: transactions / categories / budgets)
- [ ] **R15-2.** `README.md` 에 **실행 방법, 저장 파일 위치/형식, 주요 명령 예시, import/export CSV 스키마**가 포함되어야 한다.

> 💡 (해설) R15는 PDF의 "4. 기능 요구 사항"이 아니라 "2. 최종 결과물 → 10. 추가 조건"에 있는 항목이다. 그러나 원문이 **"최종 결과물의 필수 구성"** 이라고 못 박았으므로 필수 요구사항으로 함께 ID를 부여했다. (R15-1은 R3-2와 내용이 겹친다 — 명세가 두 곳에서 반복 강조한 것.)

---

### 0.5 보너스 과제 (선택)

> 원문 — 5. 보너스 과제 (선택)

- [ ] **B1. 백업 기능**
  - `backup` 실행 시 **타임스탬프가 포함된 백업 파일**을 생성한다.
  - 배움 포인트: 파일 처리 + 운영 안전장치(복구 가능성)
- [ ] **B2. 반복 내역 기능**
  - 월급/월세처럼 반복되는 내역을 등록하고, **특정 월에 자동 생성**한다.
  - 배움 포인트: 규칙 기반 데이터 생성 + 예외 처리
- [ ] **B3. 출력 포맷 테이블 정렬**
  - **외부 라이브러리 없이 문자열 정렬로** 가독성을 개선한다.
  - 배움 포인트: 콘솔 UX + 포맷터 분리
- [ ] **B4. 저장 원자성 강화**
  - update/delete 시 **임시 파일에 쓰고 `rename`으로 교체**하는 방식을 적용한다.
  - 배움 포인트: 파일 기반 트랜잭션/원자성 사고

---

### 0.6 개발 환경 · 제약 사항

#### 원문 — 6. 개발 환경

- **Python 3.10 이상**

#### 원문 — 7. 제약 사항

| 구분 | 제약 |
| --- | --- |
| **라이브러리** | **표준 라이브러리만 사용 가능** / 별도 `pip install` 이 필요한 **외부 라이브러리 사용 금지** |
| **저장 방식** | JSONL 또는 CSV 중 **1개를 선택**해 사용 / 저장 파일은 **3개 이상**(transactions/categories/budgets)으로 분리 |
| **CLI 규칙** | 옵션 표기는 `-` 로 통일 |
| **오류 처리** | **스택트레이스 출력 금지**(원인 + 해결 힌트 출력) / **오류 종료 시 exit code는 0이 아니어야 함** |

> 🚫 **금지 사항 요약 (놓치면 즉시 감점)**
> - `pip install` 이 필요한 **외부 라이브러리 금지** (argparse·json·csv·dataclasses·datetime·functools·typing 등 **표준 라이브러리만**)
> - **스택트레이스(traceback) 출력 금지** — 사용자에게는 원인 + 해결 힌트만
> - **한 파일에 몰아넣기 금지** (최소 3개 모듈)
> - 저장 파일 **1개로 합치기 금지** (최소 3개)
> - JSONL과 CSV **혼용 금지** (1개 포맷 선택)
> - 오류인데 **exit code 0 반환 금지**

> 💡 (해설) 제약 사항의 "옵션 표기는 `-` 로 통일"은 PDF 텍스트 추출 과정에서 `--` 의 하이픈 하나가 유실된 것으로 보인다. 같은 PDF의 기능 요구 사항 R1-5가 **"옵션 표기는 리눅스 표준인 `--` 로 통일해야 합니다. 예: `--help`, `--limit`, `--from`, `--to`, `--month`"** 라고 명시하고, 결과 예시도 모두 `--` 를 쓰므로 **실제 규칙은 `--`(더블 대시)** 다. (본 문서 0.2 표와 최종 결과물 절에 남아 있는 `-limit`, `-from`, `-category`, `-type`, `-q`, `-tag`, `-month`, `-top`, `-id`, `-data-dir` 표기도 모두 같은 추출 유실이며, 구현 시에는 `--limit`, `--from` … 으로 읽어야 한다.)

---

### 0.7 결과/출력 예시

> 원문 — 8. 결과 예시
> **"아래는 정답이 아니라 참고 예시다. 실제 문구와 디자인은 달라도 된다."**

#### add(거래 추가) 화면

```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

#### list(거래 목록) 화면

```
$ python -m budget_app list --limit 3
TX-000012 | 2024-01-15 | expense | food | 15000 | 점심
TX-000011 | 2024-01-14 | income  | salary | 3000000 |
TX-000010 | 2024-01-12 | expense | transport | 20000 |
```

#### category(카테고리 관리) 화면

```
$ python -m budget_app category add
카테고리명: food
[저장 완료] category=food

$ python -m budget_app category list
- food
- transport
```

#### budget + summary(예산 + 월별 요약) 화면

```
$ python -m budget_app budget set --month 2024-01 --amount 500000
[저장 완료] 2024-01 예산 500000원

$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)
지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
```

#### export / import(CSV 내보내기/가져오기) 화면

```
$ python -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ python -m budget_app import --from import.csv
[완료] imported=5, skipped=0
```

#### 오류 출력(예시) 화면

```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-13-40
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
```

> 💡 (해설) 이 예시에서 **형식만은 정확히 읽어야 하는 것**들:
> - id 포맷 `TX-000012` — **접두사 + 6자리 제로패딩**. 예시일 뿐이지만 "유일한 id"(R2-1)를 순번으로 만들면 이 모양이 자연스럽다.
> - list 한 줄 형식 `id | date | type | category | amount | memo` — **파이프 구분, 메모 없으면 빈칸**.
> - summary의 `사용률 43.0%` — **소수점 1자리**.
> - 오류 출력 2줄 구조 `[오류] 원인` + `[힌트] 해결 방법` — R13-1의 "원인 + 해결 힌트"가 화면상 어떤 모양인지 보여주는 유일한 근거다.
> - `[완료] imported=5, skipped=0` — import가 **건너뛴 행 수까지 보고**한다는 힌트. 체크리스트 4장의 "깨진 행 처리" 질문과 직결된다.

---

### 0.8 📚 이 과제가 공부하길 원하는 것 (학습 지도)

> 💡 이 표 전체가 (해설)이다. 왼쪽 두 칸은 PDF 요구사항, 오른쪽 두 칸은 **평가 체크리스트(`checklists_md/python_cli_budget_app.md`)의 질문을 근거로 역산한 학습 목표**다.

| 요구사항 | 표면적으로 시키는 일 | 실제로 학습시키려는 개념 | 스스로 답해볼 질문 |
| --- | --- | --- | --- |
| **R5-3, R7-3** (제너레이터 스트리밍) | `list`/`search`에서 파일을 한 번에 로드하지 않기 | **이터레이터 프로토콜 / 지연 평가(lazy evaluation) / 상수 메모리 처리.** `yield`가 함수 실행을 어떻게 "일시정지"하는지, `return [ ... ]` 와 메모리 곡선이 어떻게 다른지 | list/search를 제너레이터로 "어떻게" 구현했고 "왜" 유리한가? 파일이 10GB여도 RSS가 안 늘어난다고 증명할 수 있나? |
| **R5-1, R5-2 + R5-3** (최신순 + limit + 스트리밍) | 최신순으로 N건만 출력 | **스트리밍과 정렬의 충돌.** 전체 정렬은 본질적으로 전체를 봐야 한다 → 역순 읽기, 파일을 시간순 append로 유지하기, `heapq.nlargest`로 상위 N만 유지하기 등 **부분 정렬** 기법 | "최신순"을 위해 결국 전부 읽었다면 스트리밍의 의미가 남아 있나? `--limit 3`일 때 실제로 몇 줄을 읽었나? |
| **R12-1** (데코레이터) | 예외/로그/시간 측정 데코레이터 1개 이상 | **횡단 관심사(cross-cutting concern) 분리, 고차 함수, 클로저, `functools.wraps`**(메타데이터 보존) | 데코레이터로 분리한 공통 기능이 무엇이며 "왜" 분리가 필요했나? 데코레이터 없이 짰다면 몇 곳에 같은 try/except가 복붙됐을까? |
| **R2-1 ~ R2-2** (dataclass + 타입 힌트) | Transaction을 dataclass로 정의 | **데이터 계약(contract)과 구조적 설계.** `dict` 대신 타입 있는 객체를 쓸 때의 오타 방지·IDE 지원·`mypy` 검증, `Optional`/`Literal`로 허용값 표현 | 타입 힌트 덕에 실제로 잡힌 버그가 있었나? `type: Literal["income","expense"]` 와 문자열 검증 코드는 어떤 관계인가? |
| **R2-3, R14-1, R14-2** (2+ 클래스 / 3+ 모듈 / 계층 분리) | 파일과 클래스를 나눠라 | **계층형 아키텍처와 의존성 방향.** CLI→서비스→저장소→모델로 흐르고 역방향 의존이 없어야 한다. 저장소를 바꿔도(JSONL→SQLite) 서비스가 안 바뀌는 구조 | 각 모듈의 책임을 "어떻게" 나눴나? 저장 포맷을 CSV로 바꾸려면 몇 개 파일을 고쳐야 하나? |
| **R6-4, B4** (원자적 교체) | update/delete를 안전하게 | **파일 기반 트랜잭션·원자성.** 임시 파일 쓰기 → `os.replace()`(같은 파일시스템에서 원자적) → 실패 시 원본 보존. `fsync`와 크래시 일관성 | 파일을 덮어쓰는 도중 프로세스가 죽으면 데이터는 어떻게 되나? `os.rename`과 `os.replace`의 차이는? |
| **R3-1** (JSONL vs CSV 선택) | 둘 중 하나 고르기 | **저장 포맷 트레이드오프.** JSONL=중첩/가변 스키마·append 친화·행 단위 파싱 / CSV=범용·엑셀 호환·스키마 고정·쉼표 이스케이프 문제(특히 `tags`!) | "왜" 그 포맷을 택했나? tags에 쉼표가 들어가는데 CSV로 어떻게 저장했나? |
| **R13-1** (스택트레이스 금지) | 예쁜 오류 메시지 | **사용자 대면 오류 vs 개발자용 진단의 분리.** 예외를 도메인 예외로 감싸 올리고 경계(CLI)에서만 사람이 읽을 문구로 변환. 로그는 파일로, 화면은 힌트로 | 내 프로그램이 던지는 모든 예외를 한 곳에서 잡고 있나? 디버깅용 traceback은 어디에 남겼나? |
| **R13-2** (종료 코드) | `sys.exit(1)` | **프로세스 종료 코드 규약과 자동화 가능성.** `$?`, 쉘 `&&`/`\|\|` 연결, CI가 성공/실패를 판별하는 방법 | `python -m budget_app add < bad_input.txt; echo $?` 가 무엇을 출력하나? 경고인데 1을 반환하고 있진 않나? |
| **R1-2, R1-5** (`--help`, `--` 통일) | 도움말과 옵션 표기 | **CLI 인터페이스 설계 + `argparse` 서브커맨드.** `add_subparsers()`로 `budget set`, `category add` 같은 2단 명령 만들기, 자동 생성되는 usage/help | 서브커맨드마다 `--help`가 다 나오나? `budget set --help`도 동작하나? |
| **R8-2** (카테고리별 TOP N) | 지출 상위 N개 | **집계 자료구조.** `collections.defaultdict`/`Counter`, `sorted(key=..., reverse=True)`, `heapq.nlargest`의 복잡도 차이 | 카테고리가 1만 개라면 정렬 대신 무엇을 쓰나? 동점일 때 순서는 무엇으로 정하나? |
| **R9-2** (예산 사용률/초과 경고) | 퍼센트 출력 | **파생값 계산과 경계 조건.** 0원 예산일 때의 0 나누기, 반올림 규칙, "경고만 할 것인가 실패로 볼 것인가"의 설계 판단 | 예산이 0원이면 사용률은? 초과했을 때 exit code는 0인가 1인가 — 그 근거는? |
| **R10-2** (사용 중 카테고리 삭제) | 삭제 막기 / 대체 요구 | **참조 무결성(referential integrity).** RDB의 FK `ON DELETE RESTRICT`/`SET DEFAULT`를 파일로 직접 구현해 보는 경험 | 카테고리 삭제 전에 전체 거래를 스캔하나? 10만 건이면 얼마나 걸리나? 인덱스가 필요할까? |
| **R11-3, R11-4** (export 조건 필수 + CSV 스키마 고정) | 옵션 검증과 컬럼 고정 | **인터페이스 계약과 상호운용성.** "조건 없는 전체 export 금지"라는 방어적 기본값, 스키마를 문서로 고정해야 import/export가 왕복(round-trip) 가능해진다 | export한 CSV를 그대로 import하면 데이터가 똑같이 복원되나(round-trip)? id는 어떻게 되나? |
| **R11-1** (import 일괄 등록) | CSV 읽어 저장 | **부분 실패 설계.** 깨진 행을 만나면 전부 롤백할지, 건너뛰고 리포트할지(`imported=5, skipped=0`), 사용자 신뢰를 지키는 보고 방식 | 100행 중 3행이 깨졌다면 어떻게 하나? 그 결정을 사용자에게 어떻게 알리나? |
| **R3-4, R3-5** (초기 상태 처리) | 파일 없을 때/비었을 때 | **콜드 스타트와 기본값 설계.** "빈 상태"는 오류가 아니라 정상 상태 중 하나라는 관점 | 처음 설치한 사용자가 `list`를 치면 크래시하나, 친절한 안내가 나오나? |
| **B1** (백업) / **확장 사고** | 타임스탬프 백업 파일 | **운영 안전장치와 복구 가능성(recoverability).** 백업 없는 원자성은 절반짜리 | 실수로 delete한 거래를 어떻게 되살리나? |
| **확장 사고** (10만 건) | — | **성능 병목 분석.** 전체 스캔 O(n), 매 요청 파일 재파싱, 인덱스 부재, 재작성 비용 O(n) → 어디를 먼저 고칠 것인가 | 거래가 10만 건이면 병목은 어디이며 "어떻게" 개선하나? SQLite로 갈 시점은 언제인가? |

---

### 0.9 자주 놓치는 함정

> 💡 전부 (해설)이다. 명세를 빠르게 읽으면 놓치기 쉬운 조건들을 모았다.

1. **"스트리밍"은 `list`/`search` 둘 다에 걸린다.** R5-3만 보고 `list`만 제너레이터로 만들기 쉽지만, R7-3이 "스트리밍 처리(제너레이터 기반)를 **유지**해야 합니다"라고 `search`에도 별도로 못 박았다. 더 흔한 함정은 **제너레이터로 읽어 놓고 `list(gen)`으로 전부 받아 정렬**하는 것 — 형태만 제너레이터고 메모리 특성은 그대로다.

2. **"경고 출력"과 "exit 1"은 다르다.** R9-2의 예산 초과는 **경고 문구를 함께 출력**하라는 요구일 뿐, 실패가 아니다. 정상 처리된 `summary`는 R13-2에 따라 **종료 코드 0**이어야 한다. 반대로 R6-2의 "없는 id"는 사용자 메시지를 출력하되 **"오류 종료"로 볼 것인지** 스스로 정하고 일관되게 지켜야 한다. (PDF는 "없는 데이터로 처리하고 사용자 메시지 출력"까지만 규정 — 종료 코드는 명시하지 않았다.)

3. **저장 파일 3개는 "권장"이 아니라 "필수"다.** R3-2가 `3개 이상(필수)`, 제약 사항에도 다시, 최종 결과물 추가 조건에도 또 등장한다. 거래+카테고리+예산을 JSON 하나에 묶으면 **세 번 위반**이다.

4. **`update` 방식과 카테고리 초기화 방식은 "골랐다"가 아니라 "문서에 적었다"까지 해야 충족이다.** R6-3("문서에 명확히 고정"), R3-5("동작을 명확히 하세요") — 코드로는 구현했는데 README에 안 적으면 미충족으로 읽힌다.

5. **`export`는 조건 없이 실행되면 안 된다.** R11-3은 `--month` 또는 `--from`+`--to` 중 **하나 이상을 필수**로 받는다. 옵션을 "있으면 필터, 없으면 전체"로 짜는 것이 자연스러워 보이지만 그건 명세 위반이다.

6. **CSV의 `tags`는 "쉼표(,) 구분 문자열"이다.** 즉 CSV 필드 안에 쉼표가 들어간다 → 반드시 따옴표 인용/이스케이프가 필요하다. 문자열 `split(",")` 로 CSV를 직접 파싱하면 여기서 깨진다. (`csv` 모듈을 쓰라는 신호)

7. **`--help`는 "모든 명령"에 필요하다.** R1-2. 최상위뿐 아니라 `add --help`, `budget set --help`, `category remove --help`까지 동작해야 한다.

8. **`--limit`에는 기본값이 있어야 한다.** R5-2의 괄호 "(기본값 제공)"을 놓치고 필수 인자로 만들면 미충족이다.

9. **데이터가 없는 달은 조용히 빈 화면이면 안 된다.** R8-3 — **"데이터 없음"을 명확히 출력**해야 한다.

10. **입력 기본은 대화형이다.** R1-3. `add`를 옵션 전용(`add --date ... --amount ...`)으로만 만들면 기본 방식 위반이다. 옵션 방식이 허용된 것은 `search/list/summary/export/import/delete`(+`update`는 택1)뿐이다.

### 0.10 ✅ 과제 수행 점검 (명세 대조)

> 점검 방식: 저장소의 실제 소스를 명세의 요구사항 ID 와 1:1 대조. 판정 근거는 파일 경로로 명시.
> README 의 주장은 근거로 채택하지 않고, 해당 기능의 소스와 **실제 실행 결과**로 확인했다.
> 실행 검증은 저장소를 건드리지 않도록 전부 `--data-dir <스크래치패드>` 로 격리해 수행했고, 점검 후 `git status` 가 깨끗함을 확인했다.

**종합 판정: 충족** — 필수 46개 중 충족 46 / 부분 0 / 미충족 0 / 로컬검증불가 0
(보너스 4개 중 충족 3 / 부분 0 / 미충족 1 — B3 는 2026-09-21 에 보완했다. 아래 B3 행 참조)

#### 필수 요구사항

| ID | 요구사항 (요약) | 판정 | 근거 / 비고 |
| --- | --- | --- | --- |
| R1-1 | `python -m budget_app <command> [options]` 실행 | ✅ 충족 | `budget_app/__main__.py:1-8` — `sys.exit(main())`. 실행 확인: `python3 -m budget_app --help` rc=0 |
| R1-2 | 모든 명령이 `--help` 지원 | ✅ 충족 | `budget_app/cli/parser.py` 의 `build_parser()` 와 `_add_add()`~`_add_backup()` (argparse 서브파서). **최상위 1종 + 하위 17종 전수 실행 확인** — `add/list/search/summary/budget/budget set/budget get/budget list/category/category add/category list/category remove/update/delete/export/import/backup --help` 모두 rc=0 (2026-09-21 `budget get`·`budget list` 추가 후 재확인) |
| R1-3 | 입력 기본 방식은 대화형 | ✅ 충족 | `budget_app/cli/handlers.py:39-48` → `prompts.ask_transaction()`; `budget_app/cli/prompts.py:112-127` 이 날짜/타입/카테고리/금액/메모/태그를 `input()` 으로 순차 수집. `category add` 도 `--name` 생략 시 대화형 (`prompts.py:130-134`) |
| R1-4 | search/list/summary/export/import/delete 는 옵션 방식 허용, update 는 택1 고정 | ✅ 충족 | `parser.py:114-146`(list/search/summary), `203-254`(delete/export/import), `190-200`(update=옵션 방식). `add` 는 옵션 인자를 아예 두지 않아 대화형 전용 (`parser.py:108-111`) |
| R1-5 | 옵션 표기 `--` 로 통일 | ✅ 충족 | `parser.py:75-76, 117-254` — 정의된 모든 옵션이 `--data-dir/--debug/--limit/--from/--to/--category/--type/--q/--tag/--month/--top/--id/--amount/--name/--replace-with/--out/--no-id/--atomic/--on-duplicate/--auto-category`. 단일 대시 옵션은 argparse 기본 `-h` 뿐 |
| R2-1 | Transaction 최소 필드(id/type/date/amount/category/memo/tags) | ✅ 충족 | `budget_app/domain/entities.py:60-66` — 7개 필드 전부. `memo`/`tags` 는 기본값이 있어 선택 |
| R2-2 | dataclass 또는 준하는 구조 | ✅ 충족 | `entities.py:27`(Transaction), `:127`(TransactionPatch), `:157`(Budget), `:176`(Category) — 전부 `@dataclass(frozen=True)` + `__post_init__` 검증 |
| R2-3 | 최소 2개 이상의 클래스 | ✅ 충족 | AST 집계 **클래스 42개 / 모듈 43개**. 예: `storage/repositories.py:27 TransactionRepository`, `:217 CategoryStore`, `:283 BudgetStore`, `services/transactions.py:27 TransactionService`, `services/budgets.py:20 BudgetService`, `domain/tx_id.py:53 TransactionId` |
| R2-4 | 입력 검증(날짜/금액/타입/카테고리) | ✅ 충족 | `budget_app/domain/validators.py:63-195` (`parse_amount`/`parse_type`/`parse_date`/`parse_month`/`parse_category`/`parse_tags`), 재입력 루프는 `cli/prompts.py:60-74`. 실행 확인: `2024-13-40`→재입력, `-5`/`0`/`abc` 금액→재입력, 미등록 카테고리→재입력 |
| R3-1 | 저장 포맷 JSONL 또는 CSV 중 1개 | ✅ 충족 | JSONL 단일 선택 — `storage/config.py:17-19`, 공통 처리 `storage/jsonl.py:131-351`. CSV 는 저장이 아니라 R11 이 요구한 **교환 경로 전용**(`storage/csv_io.py`). 선택 근거는 README 8장 「저장 포맷 선택 — JSONL vs CSV」 |
| R3-2 | 저장 파일 3개 이상 분리 | ✅ 충족 | `storage/config.py:17-19` — `transactions.jsonl` / `categories.jsonl` / `budgets.jsonl`. 실행 후 생성 확인 — 빈 폴더(`data/` 자체가 없는 상태)에서 `category list` 한 번으로 세 파일이 만들어진다. 추가로 첫 `add` 때 `id_counter`(:21, 숫자 한 줄)가 ID 워터마크로 생성됨(`category list` 만으로는 만들어지지 않는다) — 레코드 저장소가 아니라 카운터라 "포맷 혼용"에 해당하지 않음 |
| R3-3 | 기본 `./data`, 옵션으로 변경 가능 | ✅ 충족 | `cli/config.py:13` (`DEFAULT_DATA_DIR="./data"`), `parser.py:86-88` (`--data-dir`), 하위 파서까지 전파 `parser.py:58-76`. 실행 확인: `list --data-dir <경로>`, `--data-dir` 를 명령 앞/뒤 어느 자리에 둬도 동작 |
| R3-4 | 초기 실행 시 파일 자동 생성 또는 안내 | ✅ 충족 | `budget_app/context.py:59-65` `prepare()` → `storage/jsonl.py:150-154` `ensure_ready()` (mkdir + touch). 실행 확인: 빈 폴더에 `add` 1회로 4개 파일 생성 |
| R3-5 | 카테고리 파일이 비었을 때 동작을 명확히 (안 A/안 B) | ✅ 충족 | **안 A 채택** — `storage/repositories.py:226-235 seed_defaults()` + `storage/config.py:14 DEFAULT_CATEGORIES=("food","transport","rent","salary","etc")`. 문서 고정: README 3장 「저장 파일 위치 / 형식」. 실행 확인: 빈 `categories.jsonl` 로 `add` 실행 시 기본 5종이 시딩됨. (시딩조차 실패한 극단 상황의 2차 방어로 안내 후 차단 경로도 있음 — `cli/handlers.py:34-37`, 종료 코드 5, README 11장 「종료 코드」 표에 문서화) |
| R4-1 | add 는 대화형으로 필드 입력 | ✅ 충족 | `cli/handlers.py:39-48`, `cli/prompts.py:112-127`. 실행 확인 |
| R4-2 | category 는 등록된 목록에 존재해야 함 | ✅ 충족 | 대화형: `cli/prompts.py:100-107` (미등록이면 `ValidationError`→재입력, 사용 가능 목록 표시). 서비스: `services/transactions.py:44, 110-112`. 실행 확인 |
| R4-3 | 저장 완료 시 생성된 id 출력 | ✅ 충족 | `cli/handlers.py:49` + `cli/messages.py:69` `"[저장 완료] id={id}"`. 실행 확인: `[저장 완료] id=TX-000001` |
| R5-1 | list 는 최신순 | ✅ 충족 | `services/transactions.py:22-24 _sort_key=(date, id)`, `:104-108` (`nlargest` / `sorted(reverse=True)`). 실행 확인: 01-20 → 01-15 → 01-14 순 |
| R5-2 | `--limit N` 지원 + 기본값 | ✅ 충족 | `parser.py:117-120` (`default=config.DEFAULT_LIST_LIMIT`), `cli/config.py:15` **기본 20**. 실행 확인: `list` 기본 동작, `list --limit 2` 2건, `--limit 0` 은 rc=2 로 거절 (`parser.py:38-55`) |
| R5-3 | 제너레이터 기반 스트리밍 (전체 로드 금지) | ✅ 충족 | 읽기 진입점이 `yield` 기반 — `storage/jsonl.py:162-182 iter_raw()`, `:215-225 stream()`. `list --limit N` 은 `services/transactions.py:104-107` 에서 `heapq.nlargest` 로 **크기 N 힙만 유지**(메모리 O(limit), 파일 크기 무관). `json.load()` 로 파일 전체를 올리는 코드는 저장소 전체에 없음 |
| R6-1 | `delete --id <id>` | ✅ 충족 | `parser.py:203-207`, `cli/handlers.py:166-169`, `storage/repositories.py:150-171`. 실행 확인 |
| R6-2 | 없는 id 는 "없는 데이터"로 처리 + 메시지 | ✅ 충족 | `services/transactions.py:80-84`(delete), `:69-73`(update) → `AppError`; 문구 `services/messages.py:14-15`. 실행 확인: `[오류] 해당 id 의 거래를 찾을 수 없습니다: TX-999999` / `[힌트] list 로 id 를 확인하세요.` rc=4 (일관) |
| R6-3 | update 방식을 하나로 고정 + 문서 명시 | ✅ 충족 | **옵션 기반(안 A) 고정** — `parser.py:190-200` (`--id` 필수 + 6개 필드 옵션), 대화형 경로 없음. 문서 고정: README 4장 「명령 요약」 의 `update` 주석과 5장 「거래 수정 (update) — 옵션 방식」, 그리고 0.4 절 R6-3 |
| R6-4 | update/delete 안정성(임시 파일/원자적 교체) | ✅ 충족 | `storage/jsonl.py:48-72 stage_lines()`(tmp + flush + `os.fsync`), `:75-77 commit_staged()`(`os.replace`), `:335-351 rewrite()`. 해석 실패 줄은 원문 보존(`:311-313`). append 경로도 fsync (`:242-269`) |
| R7-1 | `--from/--to/--category/--type/--q/--tag` 검색 | ✅ 충족 | `parser.py:124-133` 6종 전부. 조건 조립 `domain/queries.py:58-73`, 판정 `domain/specs.py:173-243`. 실행 확인: 기간+카테고리, `--q`, `--tag`, `--type` 각각 동작 |
| R7-2 | 검색 결과 최신순 | ✅ 충족 | `cli/handlers.py:72` → `services/transactions.py:108 sorted(..., reverse=True)`. 실행 확인 |
| R7-3 | 검색도 스트리밍 유지 | ✅ 충족 | 읽기·필터가 제너레이터 — `services/transactions.py:104` 제너레이터 식 + `storage/jsonl.py:215 stream()`. 비고: `search` 는 `--limit` 이 없어 "최신순" 보장을 위해 **필터 통과분**만 정렬 버퍼에 모은다(메모리 O(일치 건수), 파일 크기 아님). 이 한계를 README 10장 「아키텍처」 의 「설계 포인트」 가 명시하고 있어 은폐가 아님 |
| R8-1 | `summary --month YYYY-MM` | ✅ 충족 | `parser.py:136-144`(`--month` required), `services/budgets.py:51-86`. 실행 확인 |
| R8-2 | 총수입/총지출/잔액 + 카테고리 지출 TOP N(`--top`) | ✅ 충족 | 집계 `services/budgets.py:61-78`, 잔액 `domain/results.py:38-40`, 출력 `cli/presenter.py:110-121`. `--top` 기본 5 (`parser.py:140-143`, `services/config.py:17`). 실행 확인: 총수입/총지출/잔액/`지출 TOP N` 출력 |
| R8-3 | 데이터 없는 달은 "데이터 없음" 명시 | ✅ 충족 | `domain/results.py:52-55 is_empty`, `cli/presenter.py:106-108`. 실행 확인: `summary --month 2030-05` → `2030-05: 데이터 없음` rc=0 |
| R9-1 | `budget set --month --amount` 로 저장 | ✅ 충족 | `parser.py:147-155`, `cli/handlers.py:82-85`, `storage/repositories.py:300-307`(같은 달은 덮어쓰기). 실행 확인: `[저장 완료] 2024-01 예산 500000원` |
| R9-2 | summary 에 예산 사용률(%) + 초과 경고 | ✅ 충족 | `domain/results.py:42-50`(`usage_pct` 소수점 1자리, `over_budget`), `cli/presenter.py:123-130`, 문구 `cli/messages.py:76-79`. 실행 확인: `예산: 500000원 (사용률 33.0%)` / 초과 시 `[경고] 예산을 초과했습니다!` + **rc=0 유지**(경고는 실패가 아님). 예산 0원은 `N/A`(0 나누기 방어) |
| R9-3 | 예산도 영구 저장 | ✅ 충족 | `storage/config.py:19 budgets.jsonl`, `storage/repositories.py:283-307`. 실행 확인: 파일 생성 및 재실행 후 조회 |
| R10-1 | `category add/list/remove` | ✅ 충족 | `parser.py:167-187` 3종, 핸들러 `cli/handlers.py:103-130`. 실행 확인 |
| R10-2 | 사용 중 카테고리 삭제 시 차단 또는 대체 요구 | ✅ 충족 | `services/categories.py:38-89` — 사용 중인데 `--replace-with` 미지정이면 `AppError` 차단, 지정 시 일괄 재지정 후 삭제(`storage/repositories.py:194-214`). 자기 자신 대체·미등록 대체도 차단(`:82-88`). 실행 확인: 차단 rc=4 → `--replace-with etc` 로 `1건 재지정` 후 삭제, 고아 거래 없음 |
| R11-1 | `import --from <csv>` 일괄 등록 | ✅ 충족 | `parser.py:226-254`, `services/importexport.py:88-149`. 보고 형식 `[완료] mode=..., imported=N, duplicated=N, skipped=N` (`cli/messages.py:122-124`). 실행 확인: 정상/깨진 행 혼합 CSV → `imported=1, skipped=1` + 줄별 사유 출력 |
| R11-2 | `export --out <csv>` | ✅ 충족 | `parser.py:210-223`, `cli/handlers.py:172-176`, `storage/csv_io.py:145-186`. 실행 확인: `[완료] out.csv (2 records)` |
| R11-3 | export 는 `--month` 또는 `--from`+`--to` 필수 | ✅ 충족 | `cli/handlers.py:179-192` — 조건 없으면 `AppError`, `--month` 와 범위 동시 지정도 충돌로 차단. 실행 확인: 조건 없는 `export` rc=4, `--from` 만 줘도 거절 |
| R11-4 | CSV 최소 스키마 고정 (UTF-8, 헤더 포함) | ✅ 충족 | `storage/config.py:42-44` — 필수 `date,type,category,amount` + 선택 `memo,tags`(+왕복용 선택 `id`), 헤더 검증 `csv_io.py:104-118`, 쓰기 시 헤더 포함 `:170-172`. 인코딩: 쓰기 `utf-8`(BOM 없음), 읽기 `utf-8-sig`(엑셀 BOM 흡수) — `storage/config.py:39-40`. 문서: README 6장 「import / export CSV 스키마」. **실행 확인: 쉼표 포함 태그·메모가 `"tag1,tag2"` 로 인용돼 export→import 왕복 후 바이트 동일(diff 일치)** |
| R12-1 | 공통 관심사 데코레이터 1개 이상 구현·적용 | ✅ 충족 | 3개 구현 — `budget_app/decorators.py:37-47 @log_call`, `:50-66 @measure_time`, `cli/error_handler.py:20-128 @handle_errors`. 실제 적용: `services/transactions.py:34,59,79`, `services/budgets.py:50`, `cli/app.py:63`. 전부 `functools.wraps` 사용. **실행 확인: `--debug add` → `call add`/`done add`, `--debug summary` → `monthly_summary took 1.45ms`** |
| R13-1 | 스택트레이스 대신 원인 + 해결 힌트 | ✅ 충족 | `cli/error_handler.py:47-126` 4부류 분류 + `[오류]`/`[힌트]` 2줄 출력(`cli/messages.py:30-31, 137-156`), 최후 방어선도 트레이스백은 `--debug` 일 때만(`:113-125`). 오류 방패가 `AppContext` 생성까지 감쌈(`cli/app.py:63-83`). **실행 확인: `--data-dir <파일경로>` 로 실행 시 트레이스백 0줄, `[오류] 디렉터리가 아닙니다` + `[힌트]` rc=3** |
| R13-2 | 정상 0 / 오류 0 아님 | ✅ 충족 | `cli/config.py:22-29` (0/1/2/3/4/5/6/130), `__main__.py:8 sys.exit(main())`. **실행 확인: 정상 0, 검증 실패 2, 파일 없음 3, 앱 오류(없는 id·export 조건 누락·카테고리 사용 중) 4, argparse 오류 2. 예산 초과 경고는 0 유지** |
| R14-1 | 최소 3개 이상 모듈로 분리 | ✅ 충족 | **43개 모듈**(AST 집계). 패키지 4계층 `domain/`(10) `storage/`(9) `services/`(8) `cli/`(11) + 루트 5 |
| R14-2 | CLI/서비스/저장소/모델 책임 분리 (권장) | ✅ 충족 | 구조는 README 10장 「아키텍처」 의 계층도. **AST 로 직접 검증**(`tests/test_architecture.py` 로직을 별도 스크립트로 재실행): 상향 import 0건, `cli → storage` 직접 참조 0건, domain 이 상위 계층 참조 0건, `AppContext` 공개 속성에 저장소 노출 없음(`backup_service/budget_service/cat_service/data_dir/io_service/tx_service`), 핸들러 15개 전원 `HANDLERS` 등록 — 이 규칙은 문서가 아니라 검사에 산다(`tests/test_architecture.py::test_every_handler_is_registered`) |
| R15-1 | 데이터 3개 이상 파일 영구 저장 | ✅ 충족 | R3-2 와 동일 근거 — `data/transactions.jsonl`, `data/categories.jsonl`, `data/budgets.jsonl` 에 영구 저장된다. **2026-09-21 부터 이 세 파일은 git 에 담지 않는다**(`.gitignore` 의 `data/`). 개인 가계부 내용은 코드가 아니고, 저장소에 넣어 두면 각자의 메모·금액이 함께 공개되기 때문이다. 요구사항은 "프로그램이 파일에 영구 저장하는가"이지 "그 파일이 커밋돼 있는가"가 아니며, `AppContext.prepare()` → `JsonlStore.ensure_ready()` 와 `CategoryStore.seed_defaults()` 가 첫 실행에 폴더·파일·기본 카테고리를 만든다(R3-4·R3-5 와 같은 경로). 빈 폴더에서 실제로 재확인함 |
| R15-2 | README 에 실행 방법/저장 위치·형식/명령 예시/CSV 스키마 | ✅ 충족 | 실행 방법은 README 2장, 저장 파일 위치·형식은 3장, 주요 명령 예시는 5장, import/export CSV 스키마는 6장. 추가로 update 방식 고정(4장)·빈 카테고리 동작(3장)·종료 코드 표(11장)까지 명시 |

#### 보너스 과제

| ID | 요구사항 (요약) | 판정 | 근거 / 비고 |
| --- | --- | --- | --- |
| B1 | `backup` — 타임스탬프 포함 백업 생성 | ✅ 충족 | `storage/backup.py:17-47` (`backup_YYYYMMDD_HHMMSS/`), `services/maintenance.py:29-37`, `parser.py:257-261`. 확장자 없는 `id_counter` 까지 복사(`:36-47`). **실행 확인: `backup_20260919_132233/` 에 jsonl 3개 + id_counter 복사됨.** 문서는 README 13장 「보너스 — 백업」 |
| B2 | 반복 내역(월급/월세)을 특정 월에 자동 생성 | ❌ 미충족 | `grep -rniE 'recurring\|반복 내역\|recur' budget_app/ README.md` 결과 0건. 관련 명령·서비스·저장 파일 없음. README 도 이 기능을 주장하지 않음(과대 주장은 아님) |
| B3 | 출력 포맷 테이블 정렬 (외부 라이브러리 없이) | ✅ 충족 | **2026-09-21 보완.** `cli/messages.py` 의 `FMT_TX_LINE` 이 `date`·`type`·`category`·`amount` 까지 폭을 지정하고(금액만 `>` 우측 정렬), 머리글은 `cli/presenter.py` 의 `_header_line()` 이 **같은 템플릿**으로 찍고, 구분선은 `_rule_line()` 이 그 머리글을 글자 단위로 훑어 만든다 — 폭이 적히는 자리가 한 곳뿐이라 셋이 갈라질 수 없다. `{id}` 만 폭이 없는데 `TransactionId` 에 `__format__` 이 없어 `{id:<9}` 가 TypeError 이고 값 길이가 이미 고정이기 때문이며, 머리글의 `id` 칸만 `TX_ID_FORMAT` 에서 **계산한** 폭으로 채운다. 결과가 0건이면 머리글 없이 `(데이터 없음)` 만 낸다. 표준 라이브러리만 사용(문자열 포맷 미니 언어). 검사: `tests/test_smoke.py` 의 `test_tx_table_columns_line_up_across_header_rule_and_rows` 가 머리글·구분선·모든 행의 `\|`/`+` **문자 위치**가 같은지 확인한다(폭 지정을 하나라도 빼면 빨개지는 것을 실제로 확인함) |
| B4 | update/delete 시 임시 파일 + rename 원자 교체 | ✅ 충족 | `storage/jsonl.py:48-87`(stage/commit 분리, fsync 후 `os.replace`), `:335-351 rewrite()`, CSV 내보내기도 동일 규칙(`storage/csv_io.py:167-186`). 다중 파일 커밋은 `storage/unit_of_work.py:73-181` (`--atomic` import). 한계(rename 2회 사이 창)를 `unit_of_work.py:38-42` 와 README 3장 「동시 실행은 전제하지 않습니다」 가 정직하게 명시 |

#### 🔍 발견된 격차와 보완 제안

**필수 요구사항(R1~R15): 격차 없음.** 46개 항목 전부 소스 근거와 실행 결과가 일치했고, 명세가 특히 강조한 함정 8종(스트리밍·저장 파일 3개·update 방식 문서 고정·export 조건 필수·CSV 태그 쉼표 인용·모든 명령 `--help`·`--limit` 기본값·데이터 없는 달 명시)도 전부 통과했다.

아래는 보너스·완성도 차원의 지적이다.

1. **B2 반복 내역 기능 미구현 (선택 과제)**
   - 부족한 점: 월급·월세처럼 매달 반복되는 내역을 등록하고 특정 월에 자동 생성하는 경로가 전혀 없다.
   - 보완안: `data/recurrings.jsonl`(`{"id","type","category","amount","day","memo","tags"}`) 저장소를 추가하고 `recurring add/list/remove` + `recurring apply --month YYYY-MM` 을 붙인다. 적용 시 **이미 생성된 달을 두 번 적용하지 않도록** 생성된 거래에 `source_id` 를 남기거나 적용 이력을 기록해야 한다(명세의 배움 포인트 "규칙 기반 생성 + 예외 처리"가 정확히 이 지점). 기존 `UnitOfWork`(`storage/unit_of_work.py`)를 쓰면 다건 생성도 원자적으로 커밋된다.

2. **B3 테이블 정렬** — ✅ **해소됨 (2026-09-21)**
   - 무엇이었나: `cli/messages.py` 의 `FMT_TX_LINE` 이 `{type:<7}` 만 폭을 고정해, 카테고리·금액 길이가 다르면 열이 어긋났다. 머리글 행과 구분선도 없었다.
   - 어떻게 고쳤나: 폭을 **템플릿 한 줄**에 모으고(`date`/`type`/`category` 는 좌측, `amount` 는 우측 정렬), 머리글은 그 템플릿에 열 이름을 넣어 찍고, 구분선은 완성된 머리글을 훑어 만든다. 폭이 적히는 자리가 하나뿐이라 셋이 어긋나는 상태가 성립하지 않는다.
   - 메모리 성질은 건드리지 않았다: 아래 보완안이 경고한 "폭 계산을 위해 행을 모으는" 방식을 **쓰지 않고** 고정 폭을 택했으므로, `tx_table` 은 여전히 제너레이터이고 R5-3 의 O(limit) 성질이 그대로다.
   - 남은 것: 한글 카테고리를 쓰면 글자 수와 화면 폭이 달라 열이 밀린다(`unicodedata.east_asian_width` 보정이 필요). 기본 카테고리 5종이 전부 ASCII 라 현재 출력에서는 드러나지 않는다.
   - (아래는 처음 적어 둔 보완안 원문이다.)
   - 보완안: `cli/presenter.py` 에 폭 계산 단계를 두어 (a) 출력할 행들의 컬럼별 최대 길이를 구하고 (b) `f"{v:<{w}}"` 로 좌/우 정렬(금액은 우측 정렬)한 뒤 (c) 헤더 + 구분선을 얹는다. 단, `list` 는 현재 `heapq` 로 상위 N 만 들고 있으므로 **폭 계산 대상은 이미 화면에 낼 N 행으로 한정**해야 R5-3 의 상수 메모리 성질이 깨지지 않는다. 한글 폭(East Asian Width) 보정이 필요하면 `unicodedata.east_asian_width` 로 계산한다(표준 라이브러리이므로 제약 위반 아님).

3. **(경미) `budget` 조회 전용 하위 명령** — ✅ **해소됨 (2026-09-21)**
   - `budget get --month YYYY-MM` 과 `budget list` 를 추가했다. 파서는 `cli/parser.py` 의 `_add_budget()`, 핸들러는 `cli/handlers.py` 의 `cmd_budget_get`/`cmd_budget_list`, 서비스는 `services/budgets.py` 의 `BudgetService.get_budget`/`list_budgets` 이고, 조회 경로는 `summary` 가 쓰던 `BudgetStore.get` 과 **같은 것**이라 두 화면이 다른 답을 낼 수 없다.
   - 설정된 적 없는 달은 오류가 아니라 답이므로 `{month}: 예산 없음` 과 함께 종료 코드 0 으로 끝난다(`summary` 의 빈 달과 같은 규칙).
   - 검사: `tests/test_smoke.py` 의 `test_budget_get_*` / `test_budget_list_*` 6개. 그중 하나는 같은 달이 파일에 두 줄 남아 있을 때 `get` 과 `list` 가 **같은 값**을 고르는지 본다.
   - (아래는 처음 적어 둔 관찰 원문이다.)
   - 명세 원문 R9-1/R9-2/R9-3 은 전부 충족한다. 다만 "최종 결과물" 표의 5번 기능 제목이 *예산 설정/조회* 이고, 현재는 `budget set` 만 있어 **저장된 예산을 보려면 반드시 `summary --month` 를 거쳐야** 한다(해당 월에 거래가 없어도 예산 줄은 나오므로 조회는 가능하다).
   - 보완안: `budget list`(전 월 목록) / `budget get --month YYYY-MM` 를 추가한다. `storage/repositories.py:292-298 BudgetStore.get()` 과 `stream()` 이 이미 있어 핸들러 한 개와 파서 5줄이면 끝난다.

4. **(관찰) 저장 폴더에 4번째 파일 `id_counter` 가 생긴다**
   - 결함은 아니다. 레코드 저장소가 아니라 "발급한 적 있는 최대 번호" 워터마크(숫자 한 줄, `storage/ids.py:26-78`)이며, 삭제된 id 재사용으로 인한 조용한 데이터 손실을 막는 안전장치다. README 3장 「저장 파일 위치 / 형식」 표에 위치·형식·역할이 문서화돼 있어 "포맷 혼용 금지" 제약 위반으로 읽힐 여지도 막아 두었다. 제출 시 심사자가 오해하지 않도록 이 한 줄 설명을 README 3장 표 바로 아래에 유지할 것.

5. **(관찰, 요구사항 외) 저자성 표기**
   - `docs/00-INDEX.md:3` 이 "이 프로젝트는 과제 명세에 따라 AI 가 생성한 코드"라고 스스로 밝히고 있다. 명세의 과제 목표 G1~G5 는 "수료 후 **스스로 설명할 수 있어야** 한다"를 요구하므로, 제출·방어 시에는 `docs/` 12편과 `docs/budget-app-atlas.html` 로 실제 설명 가능 상태를 만들어 두는 것이 이 항목의 실질 충족 조건이다. 코드 자체의 요구사항 충족 판정에는 영향을 주지 않는다.

#### 🧪 실행 검증 기록

> 모든 실행은 저장소 루트에서 하되 `--data-dir` 를 스크래치패드로 돌려 **저장소의 `data/` 를 건드리지 않았다**. `PYTHONDONTWRITEBYTECODE=1` 로 `.pyc` 생성도 막았다. 점검 종료 후 `git status --porcelain` → **출력 없음(저장소 무변경 확인)**.

| # | 명령 | 결과 |
| --- | --- | --- |
| 1 | `python3 -V` | `Python 3.14.4` (요구 3.10+ 충족) |
| 2 | `python3 -m py_compile $(find budget_app -name '*.py')` | 전체 43개 모듈 **컴파일 성공** |
| 3 | 3rd-party import 스캔 (`grep` 후 최상위 모듈 집계) | `abc argparse calendar collections csv dataclasses datetime errno functools heapq json logging os pathlib re sys time types typing` — **전부 표준 라이브러리**. `pyproject.toml:12 dependencies = []`, `uv.lock` 에도 런타임 패키지 없음 → 제약 충족 |
| 4 | `--help` 전수 (2026-09-21 기준 최상위 1 + 하위 17종) | 전부 rc=0 (`budget set/get/list --help`, `category remove --help` 포함) |
| 5 | `add` 대화형 3건 (stdin 파이프) | rc=0, `[저장 완료] id=TX-000001~3`, 빈 폴더에 `transactions/categories/budgets.jsonl` + `id_counter` 자동 생성 |
| 6 | `list`, `list --limit 2` | 최신순 정렬 확인, limit 동작 확인 |
| 7 | `search --from/--to/--category`, `--q`, `--tag`, `--type` | 6개 조건 모두 정상 필터링 |
| 8 | `budget set` → `summary --month --top 3` | `예산: 500000원 (사용률 33.0%)`; 예산 100000 재설정 시 `사용률 165.0%` + `[경고] 예산을 초과했습니다!` **rc=0** |
| 9 | `summary --month 2030-05` | `2030-05: 데이터 없음` rc=0 |
| 10 | `category list/add/remove` | 기본 5종 시딩 확인; 사용 중 `food` 삭제 차단 rc=4; `--replace-with etc` 로 `1건 재지정` 후 삭제, 고아 거래 0 |
| 11 | `update --id ... --amount --memo` / 없는 id | 수정 성공 rc=0; 없는 id rc=4 + `[오류]/[힌트]` |
| 12 | `delete --id` / 없는 id | 삭제 rc=0; 없는 id rc=4 |
| 13 | `export --out --month` / 조건 없음 / `--from --to` | 2건 기록 rc=0; 조건 없으면 rc=4 거절; 범위 지정 rc=0 |
| 14 | export→import 왕복 (기본 / `--on-duplicate new-id`) | 기본은 `duplicated=2, imported=0` (중복 생성 없음), `new-id` 는 `imported=2` |
| 15 | 쉼표 포함 태그·메모 왕복 | CSV 에 `"점심, 회식","tag1,tag2"` 로 **인용 저장**, 재-export 결과가 원본과 `diff` 완전 일치 (`ROUNDTRIP_IDENTICAL`) |
| 16 | 깨진 CSV import (기본 / `--atomic`) | 기본 `imported=1, skipped=1` + `line 3` 사유 출력 rc=0; `--atomic` 은 `(반영된 항목 없음)` rc=4 |
| 17 | 없는 CSV import | `[오류] 파일을 찾을 수 없습니다` + `[힌트]` **rc=3**, 트레이스백 없음 |
| 18 | `list --limit 0` | argparse 거절 `1 이상이어야 합니다: 0` **rc=2** |
| 19 | `backup` | `backup_20260919_132233/` 에 jsonl 3개 + `id_counter` 복사 rc=0 |
| 20 | 빈 `categories.jsonl` 로 `add` | 기본 카테고리 5종 자동 시딩 후 진행 (안 A 동작 확인) |
| 21 | `--data-dir <파일 경로>` | `[오류] 디렉터리가 아닙니다` + `[힌트]` **rc=3**, **트레이스백 0줄** |
| 22 | 대화형 재입력 루프 | `2024-13-40`→재입력, 금액 `-5`/`0`/`abc`→각각 사유 출력 후 재입력, 최종 `[저장 완료]` rc=0 |
| 23 | `--debug add` / `--debug summary` | `@log_call` → `call add`/`done add`, `@measure_time` → `monthly_summary took 1.45ms` (데코레이터 실제 적용 확인) |
| 24 | 계층 규칙 AST 검증 (`tests/test_architecture.py` 로직 재실행) | 상향 import 0 / `cli→storage` 0 / domain 상향 0 / `AppContext` 저장소 비공개 / 핸들러 등록 누락 0. 모듈 43개, 클래스 42개 |
| 25 | `python -m pytest` | 2026-09-19 점검 시점에는 **미실행** — `.venv` 에 pytest 가 없고 시스템 파이썬에도 없어, **설치 금지** 규칙을 지켜 돌리지 않고 24번처럼 로직을 재구현해 확인했다. **2026-09-21 에는 미리 설치돼 있던 외부 가상환경의 pytest 로 실제 실행: 137개 → (B3·budget 조회 보완 후) 147개 전부 통과** |
| 26 | `bash -n` | **해당 없음** — 저장소에 셸 스크립트(`*.sh`)가 없다 |
| 27 | (2026-09-21) `data/` 를 통째로 지우고 `category list` → `add` → `budget set` → `summary` | `data/` 와 jsonl 3개 + `id_counter` 자동 생성, 기본 카테고리 5종 시딩, 전 과정 rc=0. **`data/*.jsonl` 을 git 에서 뺀 뒤에도 README 2장의 실행 안내가 그대로 성립함을 확인** |
| 28 | (2026-09-21) `list` / `search` 출력 열 정렬 | 머리글·구분선·모든 행의 `\|` 위치가 일치. `list \| head -1` 은 이제 머리글을 낸다(09-cli 문서의 예시도 그에 맞춰 정정) |
| 29 | (2026-09-21) `budget get` / `budget list` | 설정된 달 `2024-01 예산 500000원`, 설정 안 된 달 `2030-05: 예산 없음` **rc=0**, `--month 2024-3` → `2024-03` 로 정규화해 응답, `budget list` 는 월 오름차순 표 |

---

## 1. 실행 환경

- Python 3.10 이상 (표준 라이브러리만 사용)
- 외부 의존성 없음 (`pip install` 불필요)

### 개발용 검사 명령

런타임 의존성은 0 이지만, 린트와 테스트는 도구가 필요합니다. CI 가 없으므로 **손으로 돌립니다**.

```bash
# 린트 — pyproject.toml 의 설정(py310, E/F/I/UP/B)을 그대로 적용
uv run --no-project --with ruff ruff check budget_app/ tests/

# 테스트
python -m pytest
```

`ruff` 설정을 켜 두고 지키지 않으면 설정이 문서가 되어 버립니다. 현재 두 명령 모두 통과 상태를 유지합니다 (테스트 **147개**, 2026-09-21 기준).

## 2. 실행 방법

프로젝트 루트(`codyssey_B2-1/`)에서 실행합니다.

```bash
python -m budget_app <command> [options]
python -m budget_app --help
python -m budget_app <command> --help
```

데이터 폴더는 `--data-dir` 로 변경할 수 있습니다(기본 `./data`).

```bash
python -m budget_app list --data-dir ./mydata
```

## 3. 저장 파일 위치 / 형식

기본 저장 폴더: `./data/`

| 파일 | 내용 | 형식 |
| --- | --- | --- |
| `data/transactions.jsonl` | 거래 내역 | JSON Lines (한 줄에 거래 1건) |
| `data/categories.jsonl` | 카테고리 목록 | JSON Lines |
| `data/budgets.jsonl` | 월별 예산 | JSON Lines |
| `data/id_counter` | 발급된 최대 거래 번호 | 숫자 한 줄 |

폴더가 없으면 첫 실행 시 자동 생성되며, 카테고리 파일이 비어 있으면 기본 카테고리(`food`, `transport`, `rent`, `salary`, `etc`)가 자동으로 등록됩니다.

**`data/` 는 저장소에 담지 않습니다**(`.gitignore`). 가계부 내용은 코드가 아니라 쓰는 사람의 개인 기록이고, 커밋해 두면 메모·금액이 저장소를 보는 모든 사람에게 함께 공개됩니다. 받아서 바로 쓸 수 있는 이유는 위 자동 생성 때문입니다 — `git clone` 직후 아무 명령이나 한 번 실행하면 폴더와 세 파일이 만들어지고 기본 카테고리가 심깁니다.

`id_counter` 는 **삭제해도 줄어들지 않는 기준선**입니다. 거래를 지우면 파일 안의 최대 id 는 줄어들지만, 이미 내보낸 CSV 에는 그 번호가 남아 있습니다. 번호를 재사용하면 그 CSV 를 다시 가져올 때 서로 다른 거래가 "중복"으로 판정돼 조용히 버려집니다. 지워도 안전하지만(파일 스캔 값으로 되돌아갑니다) 그만큼 방어가 사라집니다.

### 동시 실행은 전제하지 않습니다

이 프로그램은 **한 번에 한 프로세스**가 데이터 폴더를 쓴다고 가정합니다. 파일 잠금이 없으므로, 같은 `--data-dir` 를 두 프로세스가 동시에 수정하면 나중에 커밋한 쪽이 앞선 변경을 덮어쓸 수 있습니다.

잠금을 넣지 않은 이유는 이 도구가 대화형 단일 사용자 CLI 이고, 잠금 파일은 그 자체로 새로운 고장(비정상 종료 후 남은 잠금 때문에 실행이 막힘)을 들여오기 때문입니다. 여러 프로세스가 함께 쓰는 상황이 실제로 필요해지는 시점은 저장소를 SQLite 로 바꿀 시점과 같습니다 — 그때는 트랜잭션이 이 문제를 통째로 가져갑니다.

한 프로세스 안에서의 안전성은 보장합니다. 모든 파일 교체는 임시 파일 + `fsync` + `os.replace` 로 이뤄지므로, 중간에 죽어도 **원본이 반쯤 쓰인 상태로 남지 않습니다**.

### transactions.jsonl 한 줄 예시

```json
{"id":"TX-000001","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}
```

### categories.jsonl 한 줄 예시

```json
{"name":"food"}
```

### budgets.jsonl 한 줄 예시

```json
{"month":"2024-01","amount":500000}
```

## 4. 명령 요약

| 명령 | 설명 |
| --- | --- |
| `add` | 거래 추가 (대화형) |
| `list` | 최신순 거래 목록 |
| `search` | 조건 검색 |
| `summary` | 월별 요약 (예산 사용률 포함) |
| `budget set` | 월 예산 설정 |
| `budget get` | 한 달 예산 조회 (없으면 `예산 없음`, 종료 코드는 0) |
| `budget list` | 설정된 모든 월 예산 목록 (월 오름차순) |
| `category add/list/remove` | 카테고리 관리 |
| `update` | 거래 수정 (옵션 방식 — 후술) |
| `delete` | 거래 삭제 |
| `import` | CSV 일괄 가져오기 (`--atomic` 로 전수 롤백, `--auto-category` 로 미등록 카테고리 자동 등록) |
| `export` | CSV 내보내기 |
| `backup` | data 폴더 백업 (보너스) |

> `update` 는 **옵션 방식으로 고정**합니다. 대화형이 아니라 `--id` 와 변경할 필드 옵션으로만 동작합니다.

공통 옵션: 모든 명령이 `--data-dir`(데이터 폴더)와 `--debug`(디버그 로그, [12장](#12-출력-스트림과-디버그-로그))를 받습니다.

## 5. 주요 명령 예시

### 거래 추가 (add) — 대화형

```text
$ python -m budget_app add
[안내] 거래 추가 - 대화형 입력입니다.
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000001
```

값이 규칙에 맞지 않으면(날짜 형식, 0/음수 금액, 허용되지 않는 타입, 미등록 카테고리, **UTF-8 로 표현할 수 없는 문자**) 그 자리에서 사유와 함께 **다시 묻습니다**. 저장 파일은 항상 유효한 UTF-8 이므로, 저장에 성공한 거래는 언제든 `export` 로 내보낼 수 있습니다.

```text
메모(선택): (UTF-8 이 아닌 바이트)
[오류] UTF-8 로 표현할 수 없는 문자가 포함되어 있습니다 (터미널·입력 파일의 인코딩을 UTF-8 로 맞춰 다시 입력해 주세요).
[힌트] 다시 입력해 주세요.
메모(선택):
```

### 목록 (list)

```bash
python -m budget_app list --limit 3
```

```text
id        | date       | type    | category     |       amount | memo
----------+------------+---------+--------------+--------------+-----
TX-000005 | 2024-01-22 | expense | food         |        35000 | 회식
TX-000004 | 2024-01-20 | expense | rent         |       150000 | 공과금
TX-000001 | 2024-01-15 | expense | food         |        15000 | 점심
```

열 폭은 `cli/messages.py` 의 `FMT_TX_LINE` **한 줄**에만 적혀 있습니다. 머리글은 같은 템플릿에 열 이름을 넣어 찍고, 구분선은 완성된 머리글을 글자 단위로 훑어 만듭니다(`cli/presenter.py` 의 `_header_line` / `_rule_line`) — 폭을 고치는 자리가 하나뿐이라 셋이 어긋날 수 없습니다. 결과가 0건이면 머리글 없이 `(데이터 없음)` 한 줄만 나옵니다.

### 검색 (search)

```bash
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python -m budget_app search --type expense --tag meal
python -m budget_app search --q 점심
```

### 월별 요약 + 예산 (summary, budget)

```bash
python -m budget_app budget set --month 2024-01 --amount 500000
python -m budget_app budget get --month 2024-01     # 한 달만 조회
python -m budget_app budget list                    # 설정된 모든 달
python -m budget_app summary --month 2024-01 --top 3
```

```text
2024-01 예산 500000원

month   |       amount
--------+-------------
2023-12 |       250000
2024-01 |       500000
2024-02 |       300000
```

```text
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
```

예산을 초과하면 `[경고] 예산을 초과했습니다!` 가 함께 출력됩니다.

설정된 적 없는 달을 `budget get` 으로 물으면 `2030-05: 예산 없음` 과 함께 **종료 코드 0** 으로 끝납니다. 없다는 것은 실패가 아니라 조회의 답이기 때문이고, 데이터가 없는 달에 `summary` 가 `데이터 없음` 을 내면서 0 으로 끝나는 것과 같은 규칙입니다.

### 카테고리 관리 (category)

```bash
python -m budget_app category add --name groceries
python -m budget_app category list
python -m budget_app category remove --name food --replace-with etc
```

사용 중인 카테고리는 `--replace-with` 없이는 삭제할 수 없습니다.

### 거래 수정 (update) — **옵션 방식**

```bash
python -m budget_app update --id TX-000005 --amount 35000 --memo "회식"
python -m budget_app update --id TX-000005 --category etc --tags "company,dinner"
```

지원 옵션: `--id`(필수), `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags`.

### 거래 삭제 (delete)

```bash
python -m budget_app delete --id TX-000005
```

### CSV 내보내기 / 가져오기 (export / import)

```bash
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out range.csv --from 2024-01-01 --to 2024-03-31
python -m budget_app export --out plain.csv --month 2024-01 --no-id   # id 컬럼 제외(외부 도구용)

python -m budget_app import --from import.csv            # 부분 성공 + 중복 skip (기본)
python -m budget_app import --from import.csv --atomic   # 전수 롤백
python -m budget_app import --from import.csv --on-duplicate new-id   # 중복도 새 id 로 추가
python -m budget_app import --from import.csv --on-duplicate error    # 중복이면 중단
python -m budget_app import --from import.csv --auto-category         # 미등록 카테고리도 등록하며 가져오기
```

`export` 는 `--month` 또는 `--from/--to` 중 하나가 **필수**입니다.
`import` 는 **등록된 카테고리만** 받습니다 — 미등록 카테고리 행은 건너뛰고(`skipped`) 사유를 알려 줍니다. 자동 등록이 필요하면 `--auto-category` 를 명시하세요([7장](#7-가져오기-실패-정책--부분-성공-vs-원자적전수-롤백)).
`import` 의 실패 정책(부분 성공 vs 원자적)은 [7. 가져오기 실패 정책](#7-가져오기-실패-정책--부분-성공-vs-원자적전수-롤백) 을 참고하세요.

## 6. import / export CSV 스키마

- 인코딩: **UTF-8 (BOM 없음)**
- 헤더 포함

> **인코딩/BOM 방침**: 내보내기는 `encoding="utf-8"`(BOM 없음)로 고정한다. 한글이 그대로 보존되고, **가져오기는 반대로 `utf-8-sig` 로 읽어** BOM 이 붙은 외부(Excel) CSV 도 그대로 받는다 — BOM 을 흡수하므로 헤더 첫 컬럼명이 깨지지 않는다. 구형 Excel 에서 한글이 깨져 보이면 Excel 의 *데이터 → 텍스트/CSV 가져오기* 에서 원본 인코딩을 **UTF-8** 로 지정하면 된다.

| column | required | 설명 |
| --- | --- | --- |
| `id` | N | `TX-000001` 형식. **내보내기는 기본 포함**, 가져오기는 있으면 쓰고 없으면 새로 발급 |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` / `expense` |
| `category` | Y | **등록된 카테고리**. 가져오기에서 미등록이면 그 행을 건너뜁니다(`--auto-category` 를 주면 등록하고 받습니다) |
| `amount` | Y | 양의 정수 |
| `memo` | N | 자유 문자열 |
| `tags` | N | 쉼표(`,`) 구분 문자열 |

### `id` 컬럼 — 왕복(round-trip) 안전성

예전 스키마에는 `id` 가 없었습니다. 그래서 `export` 한 파일을 그대로 `import` 하면
**같은 거래가 새 id 를 받아 한 번 더 저장**됐습니다. 내보낸 CSV 가 원본 거래를 식별할
수단을 갖고 있지 않았기 때문입니다.

`id` 는 **선택** 컬럼이라 기존 호환성이 유지됩니다.

- `export` 는 기본으로 포함합니다 → 자기 파일을 다시 넣어도 중복이 생기지 않습니다.
- `import` 는 id 가 있으면 그 id 를 복원하고, 없거나 비어 있으면 새로 발급합니다
  → 필수 컬럼만 갖춘 외부 CSV(엑셀·타 가계부)는 예전 그대로 들어옵니다.
- 외부 도구에 넘길 때 id 가 거슬리면 `export --no-id` 로 뺄 수 있습니다.

### CSV 예시

```csv
id,date,type,category,amount,memo,tags
TX-000001,2024-01-15,expense,food,15000,점심,meal
TX-000002,2024-01-14,income,salary,3000000,월급,
TX-000003,2024-01-20,expense,rent,150000,공과금,
```

`id` 없이도 그대로 가져올 수 있습니다(이 경우 전부 새로 발급).

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
```

## 7. 가져오기 실패 정책 — 부분 성공 vs 원자적(전수 롤백)

CSV `import` 는 일부 줄이 손상됐을 때의 처리 방식을 **옵션으로 선택**할 수 있습니다.

| 모드 | 옵션 | 손상된 줄이 있을 때 | 결과 파일 | 종료 코드 |
| --- | --- | --- | --- | --- |
| 부분 성공 (기본) | *(없음)* | 그 줄만 건너뛰고(skip) 나머지는 저장 | 유효한 줄만 반영 | `0` |
| 원자적(전수 롤백) | `--atomic` | 첫 오류에서 중단, **아무것도 저장하지 않음** | 변화 없음(원본 유지) | `4` |

### 중복 정책 — 이미 있는 `id` 를 만났을 때

`--on-duplicate` 로 고릅니다. 손상 여부와는 **독립된 축**입니다(`--atomic` 과 함께 쓸 수 있음).

| 옵션 | 동작 | 쓰는 상황 |
| --- | --- | --- |
| `skip` (기본) | 건너뛰고 `duplicated` 로 집계 | 내보낸 파일을 다시 넣는 정상 왕복 |
| `new-id` | 새 id 를 발급해 별도 거래로 추가 | 같은 내역을 의도적으로 복제 |
| `error` | `AppError` 로 중단 (아무것도 저장 안 됨) | 중복이 있으면 안 되는 정산 데이터 |

결과 요약에서 `skipped` 와 `duplicated` 를 나눠 보여 주는 이유는 **사용자가 해야 할 일이
정반대**이기 때문입니다. `skipped` 는 데이터가 잘못돼 CSV 를 고쳐야 하고, `duplicated` 는
이미 저장돼 있어서 아무것도 안 해도 됩니다. 한 숫자로 합치면 정상 왕복이 실패처럼 읽힙니다.

```bash
python -m budget_app export --out backup.csv --month 2024-01
python -m budget_app import --from backup.csv
# [완료] mode=부분 성공, imported=0, duplicated=3, skipped=0   ← 중복 생성 없음
```

### 카테고리 정책 — 미등록 카테고리를 만났을 때

기본은 **거부**입니다. CSV 스키마(G13)가 `category` 를 "등록된 카테고리"로 규정하고, 같은 프로그램의 `add`/`update` 도 미등록 카테고리를 거부하기 때문입니다. 가져오기만 규칙이 반대이면 오타 하나(`food` → `fod`)가 경고 없이 카테고리 마스터에 영구 등록되고, 그 뒤로는 요약·검색이 두 이름으로 갈립니다.

| 옵션 | 미등록 카테고리 행 | 카테고리 파일 |
| --- | --- | --- |
| *(없음, 기본)* | 건너뛰고 `skipped` 로 집계 + 줄마다 사유 출력 | 변화 없음 |
| `--auto-category` | 카테고리를 등록하고 그 행도 저장 | 새 이름이 추가되고 `[안내] 새 카테고리 N개를 등록했습니다: ...` 출력 |

`--atomic` 과 함께 쓰면 미등록 카테고리도 다른 검증 실패와 똑같이 **첫 줄에서 전수 롤백**(종료 코드 `4`)입니다.

```bash
printf 'date,type,category,amount,memo,tags\n2024-01-01,expense,fod,1000,typo,\n' > typo.csv
python -m budget_app import --from typo.csv
# [완료] mode=부분 성공, imported=0, duplicated=0, skipped=1
# [오류 라인 일부]
#   - line 2: 등록되지 않은 카테고리입니다: fod (`category add --name fod` 으로 등록하거나 `--auto-category` 를 쓰세요)
```

### 동작 방식(준비 → 커밋 2단계)

두 모드 모두 **먼저 전체 행을 검증(준비 단계)한 뒤에만** 파일에 씁니다(커밋 단계).

- **부분 성공**: 준비 단계에서 검증 실패한 줄은 `skipped` 로 집계하고, 통과한 줄만 모아 마지막에 한 번에 append 합니다. 오류 줄은 앞쪽 일부를 `[오류 라인 일부]` 로 안내합니다.
- **원자적(`--atomic`)**: 준비 단계에서 한 줄이라도 검증에 실패하면 즉시 `AppError` 를 던지고 **파일을 전혀 건드리지 않습니다**. 커밋 단계는 기존 내용 + 신규 전부를 임시 파일에 쓴 뒤 `os.replace()` 로 교체하므로, 커밋 도중 프로세스가 죽어도 원본이 그대로 남습니다(파일 시스템 레벨의 전수 롤백). ID 는 준비 단계에서 메모리상으로만 확정되고(파일은 건드리지 않습니다), 카테고리 등록(`--auto-category`)·워터마크 기록·거래 쓰기 같은 **파일 반영은 전부 커밋 단계**에서 일어납니다. 그래서 준비 중 실패하면 카테고리/거래 어느 쪽에도 잔여가 남지 않습니다.

```bash
# 손상된 줄이 하나라도 있으면 전체가 반영되지 않음 → 종료 코드 4
python -m budget_app import --from import.csv --atomic
# [오류] 원자적 가져오기 실패 — line 3: 금액은 양의 정수여야 합니다 ... (반영된 항목 없음)
# [힌트] CSV 를 고쳐 다시 시도하거나, --atomic 없이 부분 가져오기를 사용하세요.
```

> **선택 기준**: 회계·정산처럼 "일부만 들어가면 안 되는" 데이터는 `--atomic`, 로그성 대량 유입처럼 "가능한 만큼 최대한 넣는" 경우는 기본(부분 성공)을 사용하세요.

## 8. 저장 포맷 선택 — JSONL vs CSV

영구 저장은 **JSONL(JSON Lines)**, 외부 교환은 **CSV** 로 역할을 나눴습니다.

| 항목 | JSONL (내부 저장) | CSV (외부 교환) |
| --- | --- | --- |
| 구조 | 중첩/가변 필드 자연스러움 (`tags` 리스트를 그대로 표현) | 평면 표만 가능 (리스트는 `,` 로 인코딩 필요) |
| 타입 | JSON 타입 보존 (숫자/문자/배열 구분) | 모두 문자열 → 매번 재파싱·재검증 |
| 추가 쓰기 | 한 줄 append 로 O(1) 삽입, 원자적 교체 용이 | 헤더·따옴표 규칙 탓에 부분 수정이 번거로움 |
| 스트리밍 | 한 줄 = 레코드 1건 → 제너레이터로 자연스러운 스트리밍 | 따옴표 내 개행 등으로 라인=레코드 보장 안 됨 |
| 사람 가독성 | 보통 | 좋음 (Excel/시트에서 바로 열림) |
| 상호운용성 | 도구가 제한적 | 사실상 표준, 어디서나 열림 |

**JSONL 을 내부 저장 포맷으로 택한 이유**

1. **레코드 단위 추가·스트리밍**: 거래는 계속 쌓이는 append 중심 데이터입니다. JSONL 은 "한 줄 = 거래 1건" 이라 append 가 O(1) 이고, `stream()` 제너레이터가 한 줄씩 흘려보내 대용량에서도 전체를 메모리에 올리지 않습니다.
2. **타입·구조 보존**: `tags`(리스트), `amount`(정수) 를 형 손실 없이 저장합니다. CSV 라면 매 읽기마다 `,` 분해와 정수 파싱을 다시 해야 합니다.
3. **원자적 교체와 궁합**: 수정/삭제는 `임시 파일 + os.replace()` 로 교체하는데, 라인 지향 포맷이라 이 패턴이 단순합니다.
4. **손상 격리**: 한 줄이 깨져도 그 줄만 건너뛰면 되고 나머지는 유효합니다.

반대로 **가져오기/내보내기(import/export)** 는 Excel·구글시트·타 가계부와 주고받는 통로이므로, 상호운용성이 가장 좋은 **CSV** 를 씁니다. 즉 "내부 저장은 JSONL, 경계에서의 교환은 CSV" 라는 역할 분리입니다.

## 9. 대용량(100k+) 성능 — 병목과 개선안

현재 설계는 읽기를 제너레이터로 스트리밍하므로 **단순 조회/합계(summary)** 는 건수가 늘어도 메모리가 일정합니다. 다만 다음 지점은 건수가 커지면 병목이 됩니다.

| # | 병목 지점 | 현재 비용 | 원인 | 개선안 |
| --- | --- | --- | --- | --- |
| B1 | `list`/`search` 정렬 (`stream_sorted`) | `list --limit N`: (개선 완료) 메모리 **O(N)** — 20만 행에서 피크 RSS 146MB → 16MB. `search`(limit 없음): 필터 통과분을 모아 정렬 → 메모리 O(k) | 파일이 시간순으로 정렬돼 있지 않음 | `limit` 이 있으면 `heapq.nlargest(limit, ...)` 로 상위 N 만 힙에 유지 *(이번 수정 반영)*. 남은 개선: ① append 시 시간순 유지(정렬 불변식) → 정렬 없이 tail-read ② 전체 정렬이 필요하면 **외부 정렬**(청크 정렬 후 k-way merge) |
| B2 | 대량 `import` 의 ID 발급 | (개선 완료) 과거 행마다 `next_id()` 가 전체를 재스캔 → O(N²) | 매 삽입마다 최대 ID 재계산 | `id_allocator()` 가 `id_state()` 로 파일을 **한 번만** 훑어 (최대 번호, 사용 중인 id 집합) 을 얻고, 워터마크와의 최대값을 시작점 삼아 메모리에서 연속 발급 → O(N). *(이번 수정 반영)* |
| B3 | `--atomic` import 커밋 | 기존 전체 + 신규를 다시 씀 → O(전체) I/O·메모리 | 원자적 교체를 위해 전량 재작성 | 원자성의 대가로 감수. 초대용량은 부분 성공 모드 사용 또는 파일 **샤딩**(아래 B4) |
| B4 | 단일 파일 전체 스캔(모든 조회 공통) | 매 명령이 파일 전체를 읽음 → O(전체) | 인덱스가 없음 | ① **월별 샤딩**(`transactions-YYYY-MM.jsonl`) 으로 조회 범위를 해당 월로 축소 ② `id → offset` **경량 인덱스** 파일로 단건 조회 O(1) ③ 임계 규모를 넘으면 SQLite 로 이전 |

### 구체적 임계치·전략 가이드

- **~ 수만 건**: 현재 구조로 충분. 정렬도 체감 지연이 거의 없습니다.
- **~ 10만 건**: `list --limit N` 은 `heapq.nlargest` 덕분에 메모리가 건수와 무관합니다(시간은 여전히 전체 스캔이라 O(N)). 조건 없는 전체 정렬(`search`)이 필요하면 append 정렬 불변식 도입을 권장합니다.
- **100만 건 이상**: 단일 파일 전체 스캔(B4)이 지배적. **월별 샤딩 + 경량 인덱스**, 또는 **SQLite** 등 인덱스 지원 저장소로의 이전을 권장합니다. 정렬은 **외부 정렬**로 전환합니다.

> 요약: 지금은 "스트리밍으로 메모리는 잡고(상위 N 조회는 heapq 로 O(N) 상한), 전체 스캔은 시간 O(전체)" 지점에 있습니다. 확장 순서는 **정렬 불변식 → 월별 샤딩/인덱스 → 외부 정렬/SQLite** 입니다.

## 10. 아키텍처

4개 계층으로 책임을 분리했고, **계층을 폴더로 드러냈습니다**. **파일 하나 = 책임 하나**가
원칙이라 어떤 변경이든 고칠 파일이 한눈에 정해집니다.

```
budget_app/
├── __main__.py                # 엔트리포인트 (python -m budget_app)
├── config.py                  # 앱 정체성 (로거 이름) — 계층 아님
├── errors.py                  # 예외 어휘 (ValidationError / AppError) — import 0개
├── decorators.py              # 관측 — @log_call / @measure_time
├── context.py                 # 합성 루트 — 저장소·서비스 조립 (계층 밖)
│
├── domain/                    # ── 도메인 (I/O 를 전혀 모름) ──
│   ├── config.py              #    타입 어휘·날짜 형식·ID 형식
│   ├── messages.py            #    필드 검증 실패 메시지
│   ├── validators.py          #    규칙 하나 = 함수 하나
│   ├── tx_id.py               #    TransactionId 값 객체
│   ├── entities.py            #    Transaction / Budget / Category / TransactionPatch
│   ├── specs.py               #    Specification — 조합 가능한 검색 조건
│   ├── queries.py             #    SearchFilter — CLI 인자를 명세로 조립
│   ├── results.py             #    MonthlySummary / ImportReport
│   └── periods.py             #    month_range — "이 달"의 정의처
│
├── storage/                   # ── 저장소 (open() 은 전부 여기) ──
│   ├── config.py              #    파일명·인코딩·CSV 스키마·백업
│   ├── messages.py            #    손상 줄 로그 / CSV 헤더 오류
│   ├── jsonl.py               #    JsonlStore / RawLine / stage·commit
│   ├── ids.py                 #    IdAllocator
│   ├── repositories.py        #    거래·카테고리·예산 저장소
│   ├── csv_io.py              #    CSV 경계 어댑터
│   ├── unit_of_work.py        #    UnitOfWork — 다중 파일 커밋
│   └── backup.py              #    데이터 폴더 백업
│
├── services/                  # ── 서비스 (판단만) ──
│   ├── config.py              #    중복 정책·한도
│   ├── messages.py            #    AppError message / hint
│   ├── transactions.py        #    거래 유스케이스
│   ├── budgets.py             #    예산 + 월별 요약
│   ├── categories.py          #    카테고리 + 참조 무결성
│   ├── importexport.py        #    CSV 정책 (실패 축 × 중복 축)
│   └── maintenance.py         #    BackupService — 폴더 단위 운영 유스케이스
│
└── cli/                       # ── CLI (사람과 만나는 곳) ──
    ├── __init__.py            #    main 만 재수출
    ├── config.py              #    한도·종료 코드
    ├── messages.py            #    프롬프트·결과·오류 표시 (전체의 3분의 2)
    ├── app.py                 #    HANDLERS 레지스트리 + main
    ├── handlers.py            #    cmd_* 15개
    ├── parser.py              #    argparse 문법
    ├── prompts.py             #    대화형 입력
    ├── presenter.py           #    도메인 → 문자열 (출력 안 함)
    ├── output.py              #    채널 결정
    └── error_handler.py       #    예외 → 종료 코드
```

의존은 **아래로만** 흐릅니다. `services` 는 `open()` 을 호출하지 않고, `storage` 는
화면 문자열을 모르며, `presenter` 는 출력하지 않고 문자열을 돌려줍니다.

**폴더 이름이 곧 계층입니다.** 평평하게 두면 알파벳순이 계층을 흩뜨려서
(`csv_io.py` 와 `decorators.py` 가 나란히 보이는 식) 구조가 코드에는 있는데 파일
트리에는 없는 상태가 됩니다. 횡단 4개만 폴더 없이 루트에 두어 "이들은 계층이 아니다"를
위치로 표현했습니다 — `errors` 는 10개 모듈이 import 하고, 계층별로 나뉜
`config`/`messages` 는 각각 20개·15개가 가져다 씁니다(`messages` 는 루트가 아니라
계층마다 하나씩 있습니다).

### 설계 포인트

- **제너레이터 스트리밍**: 파일 읽기 진입점(`iter_raw()` / `stream()`)은 `yield` 기반이라 파일을 `json.load()` 로 한 번에 올리지 않습니다. 다만 **명령 전부가 상수 메모리로 끝나는 것은 아닙니다.**
  - 끝까지 스트리밍: `summary`, `export` — 한 건씩 흘려보내며 누적/기록만 합니다.
  - 상위 N 만 들고 있습니다: `list --limit N` — `heapq.nlargest` 로 크기 N 짜리 힙만 유지하며 흘려보냅니다. 메모리는 **파일 크기가 아니라 N** 에 비례합니다.
  - 중간에 모읍니다: `search` — 한도가 없어 **정렬** 때문에 통과한 항목을 리스트로 모아야 합니다(파일이 날짜순이 아니므로). 메모리는 '필터를 통과한 건수'에 비례합니다.
  - 통째로 모읍니다: `update`/`delete`/재지정 — 재작성할 줄 목록 전체를 만든 뒤 원자적으로 교체합니다. 이건 원자성의 대가입니다.
  
  즉 스트리밍이 사는 것은 **읽기 진입점·집계 경로·상위 N 조회**이고, 한도 없는 전체 정렬과 재작성은 원리상 전량을 들고 있어야 합니다. 개선 방향은 9장에 있습니다.
- **읽기 경로가 둘**: `iter_raw()` 는 **모든 줄을 원문과 함께** 주고, `stream()` 은 **검증을 통과한 객체만** 줍니다. UTF-8 로 다시 쓸 수 없는 바이트가 섞인 줄도 '손상 줄'로 격리되므로(원문은 보존), 그런 줄 하나 때문에 `export` 전체가 실패하지 않습니다. 재작성(update/delete/재지정)은 `iter_raw()` 를 쓰므로 손상된 줄이 원문 그대로 보존됩니다. 하나로 합쳐 두면 무관한 거래를 지울 때 손상된 줄까지 디스크에서 사라집니다. ID 스캔도 `iter_raw()` 기반이라, 검증에 실패하는 줄에 들어 있던 id 도 "이미 쓰인 번호"로 인식되어 재발급 충돌이 생기지 않습니다.
- **원자적 쓰기**: `update`/`delete` 와 `export` 는 임시 파일에 전부 쓴 뒤 `flush` + `fsync` 하고 `os.replace()` 로 교체합니다(내보내기가 중간에 실패해도 헤더만 남은 반쪽 CSV 가 생기지 않습니다). 쓰는 도중 프로세스가 죽어도 원본 파일이 깨지지 않습니다. `os.replace` 가 보장하는 것은 "이름이 가리키는 대상이 순간적으로 바뀐다"이지 "내용이 디스크에 도달했다"가 아니라서 `fsync` 가 함께 필요합니다.
- **데코레이터로 공통 관심사 분리**: `@handle_errors` 가 명령 실행 전체(`app._dispatch`)를 한 번 감싸서 `[오류]` / `[힌트]` 메시지를 **stderr** 로 출력하고 적절한 종료 코드를 반환합니다(어느 부류든 화면에는 원인 + 힌트만 나가고, **스택트레이스는 `--debug` 일 때만** 붙습니다). 잡는 예외는 *종료 신호 / 입력 오류 / 환경 상태 / 최후 방어선* 네 부류로 묶여 있고 `except` 순서가 그 분류를 그대로 따릅니다. `@log_call`, `@measure_time` 은 디버깅용으로 서비스 계층에 적용되어 있습니다.
- **관측과 표현을 다른 파일에**: `@log_call`/`@measure_time`(관측)은 `decorators.py`, `@handle_errors`(예외를 화면 문구와 종료 코드로 바꾸는 표현 정책)는 `error_handler.py` 에 있습니다. 한 파일에 두면 서비스 계층이 `@log_call` 하나를 쓰려다 출력 모듈까지 끌고 들어와 `services → decorators → output` 이라는 역방향 의존이 생깁니다. 지금은 모든 화살표가 아래로만 향합니다.
- **출력 채널 분리**: 명령의 *결과*만 stdout 으로, *진단*(오류/힌트/경고)은 stderr 로 나갑니다. 덕분에 `list > out.txt` 의 데이터 파일에 오류 문자열이 섞이지 않고, 파이프가 끊겨 stdout 이 깨진 상황에서도 오류는 사용자에게 전달됩니다. 두 채널 모두 `output.out()` / `output.err()` 라는 이름이 있어서, `grep 'output\.'` 한 번이면 프로그램이 밖으로 내보내는 모든 글자가 나옵니다.
- **프레젠터는 출력하지 않는다**: `presenter` 는 문자열을 **반환**하고 채널 선택은 호출자가 합니다. 덕분에 화면 형식을 프로세스 없이 검증할 수 있고, 채널 결정이 `output` 한 곳에만 남습니다.
- **타입 힌트**: 공개 API 는 입력/출력에 타입을 명시했습니다(argparse 서브파서를 받는 `parser.py` 의 내부 헬퍼와 데코레이터 래퍼 등 21곳은 예외입니다). 부분 수정은 문자열 키 dict 대신 `TransactionPatch` dataclass 로 받으므로 필드명을 잘못 쓰면 조용히 무시되지 않고 `TypeError` 로 즉시 드러납니다.
- **생성자 불변식 검증**: `Transaction`, `Budget`, `Category` dataclass 는 `__post_init__` 에서 필드를 검증·정규화합니다. 즉 **생성자가 유일한 강제 지점**이라, 서비스/CLI/`from_dict`/직접 호출 등 어떤 경로로 만들어져도 잘못된 객체가 존재할 수 없습니다. 개별 규칙은 전부 `validators.py` 의 모듈 함수(`parse_date`/`parse_amount`/…)로 **규칙 하나 = 함수 하나**로 정의되고, 모델·CSV 어댑터·대화형 입력이 모두 같은 함수를 씁니다.
- **파생값은 모델이 계산**: `MonthlySummary.usage_pct` / `over_budget` 처럼 계산으로 얻는 값은 `@property` 로 모델에 둡니다. 서비스는 집계만, 프레젠터는 표시만 담당합니다.
- **설정·문자열 중앙화**: 값 상수(카테고리·파일명·형식·한도·종료 코드)는 `config.py`, 사용자 노출 문자열(프롬프트·메시지·오류/힌트·로그)은 `messages.py` 에 모았습니다. 나눈 이유는 **바꿨을 때 일어나는 일이 다르기 때문**입니다 — `config` 를 바꾸면 동작이 달라지고, `messages` 를 바꾸면 글자만 달라집니다. 덕분에 도메인 계층(`entities`/`validators`)이 CLI 문구 변경에 묶이지 않습니다.

## 11. 종료 코드

| 코드 | 의미 |
| --- | --- |
| `0` | 정상 종료 |
| `1` | 예기치 못한 오류 |
| `2` | 입력 검증 실패 (`ValidationError`) |
| `3` | 파일 입출력 오류 (없음 / 디렉터리 / 권한 / 일반 I/O) |
| `4` | 애플리케이션 오류 (예: 없는 id, 미등록 카테고리, `--atomic` import 전수 롤백) |
| `5` | 카테고리 미등록 상태에서 add 시도 |
| `6` | 인코딩 오류 (읽을 파일이 UTF-8 이 아님 / UTF-8 로 쓸 수 없는 값) |
| `130` | 사용자 Ctrl+C 중단 |

## 12. 출력 스트림과 디버그 로그

명령의 **결과**는 stdout, **진단**(`[오류]`/`[힌트]`/경고/재입력 안내)은 stderr 로 나갑니다. 둘을 셸에서 따로 다룰 수 있습니다.

```bash
python -m budget_app list > out.txt          # out.txt 에는 거래 목록만 (오류가 섞이지 않음)
python -m budget_app import --from nope.csv 2>/dev/null   # 진단만 버리기 → 아무것도 안 보임
python -m budget_app import --from nope.csv 1>/dev/null   # 결과만 버리기 → 오류만 보임
python -m budget_app list | head -3          # 하류가 먼저 닫혀도 조용히 종료 (코드 0)
```

오류는 **스택트레이스 대신 원인 + 해결 힌트**로 나갑니다. 분류된 세 부류(입력 오류·환경 상태·종료 신호)는 `[오류]` / `[힌트]` 한 줄로 끝나고, 분류 밖의 예기치 못한 오류도 같은 한 줄 요약에 `[ERROR] unhandled error` 기록 한 줄만 덧붙습니다. **스택트레이스는 `--debug`(또는 `BUDGET_APP_DEBUG`)를 켰을 때만** stderr 로 나옵니다 — 힌트가 안내하는 그대로입니다. 디버그를 켜면 여기에 `@log_call`·`@measure_time` 의 호출/시간 로그가 더해집니다.

```bash
python -m budget_app --debug summary --month 2024-01   # 하위 명령 앞
python -m budget_app summary --month 2024-01 --debug   # 하위 명령 뒤 (둘 다 동작)
BUDGET_APP_DEBUG=1 python -m budget_app summary --month 2024-01   # 환경변수로도 가능
```

디버그를 켜면 로그 레벨이 DEBUG 가 되어 `@log_call`·`@measure_time` 의 호출/시간 로그와 `handle_errors` 가 보존한 스택트레이스가 stderr 로 출력됩니다. 끈 상태에서는 WARNING 이상(예: 손상된 JSONL 줄 경고)만 나옵니다.

> `category` / `budget` 처럼 하위 명령이 또 있어도 `--data-dir` 와 `--debug` 는 **어느 자리에나** 쓸 수 있습니다 — `category --debug list` 와 `category list --debug` 가 모두 동작합니다. 최상위·중간·말단 파서 모두 같은 옵션을 받도록 붙여 두었기 때문입니다.

## 13. 보너스 — 백업

```bash
python -m budget_app backup
```

`./backup_YYYYMMDD_HHMMSS/` 폴더에 `data/*.jsonl` 과 `data/id_counter` 가 복사됩니다. 확장자가 없다고 `id_counter` 를 빠뜨리면, 백업을 되돌렸을 때 "발급한 적 있는 번호" 기록이 사라져 삭제된 id 재사용이 되살아납니다.

## 14. 도면집 — 구조를 그림으로

`docs/budget-app-atlas.html` 을 브라우저로 열면 이 프로그램의 구조 전체를 **도면 27장**으로 볼 수 있습니다. 위 13개 절이 글로 설명한 것과 같은 내용을, 계층·관계·흐름으로 나눠 그린 것입니다.

| 파트 | 도면 |
|---|---|
| A · 전경 | 01 시스템 전경 · 02 모듈 지도(43개 전수)와 의존 방향 |
| B · 데이터 모델 | 03 ERD · 04 엔티티 클래스도 · 05 결과·질의 모델 · 06 Specification 패턴 |
| C · 실행 수명주기 | 07 `main()` 부팅 시퀀스 · 08 CLI 문법 트리 · 09 명령 13개 전수 대응 · 10 오류 분류와 종료 코드 · 11 출력 채널 |
| D · 저장소 메커니즘 | 12 저장소 클래스도 · 13 JSONL 읽기 두 경로 · 14 쓰기 세 경로 · 15 거래 ID 발급 · 16 UnitOfWork 시퀀스 |
| E · 유스케이스 | 17 add · 18 update/delete · 19 list/search · 20 summary · 21 category remove · 22 import · 23 export · 24 backup |
| F · 경계 | 25 검증·정규화 파이프라인 · 26 설정·메시지 소유권 · 27 테스트 지도 |
| 부록 | 명령·종료 코드·저장 파일 레퍼런스 표 · 도구 안내 |

> ⚠️ **도면은 2026-08-26 판입니다.** 2026-09-21 에 추가한 `budget get` / `budget list` 는 아직 도면 08·09 와 부록 레퍼런스 표에 반영돼 있지 않습니다(그 외 내용은 유효합니다). 도면 생성에는 외부 도구가 필요해 이 환경에서 다시 그리지 못했습니다 — 다시 그리는 방법은 아래 「도면을 고치거나 다시 그리려면」 을 보세요.

전부 SVG 벡터라 확대해도 선이 뭉개지지 않습니다. 처음에는 폭에 맞춰 도면 전체가 한눈에 들어오도록 축소돼 있고, 시트마다 다음을 할 수 있습니다.

| 조작 | 방법 |
|---|---|
| 축소 / 확대 | 시트 오른쪽 위 `−` `+` (20~500%), 또는 <kbd>Ctrl</kbd>+휠 |
| 맞춤 배율로 복귀 | 가운데 배율 숫자 클릭 |
| 전체 화면 | `⛶` — <kbd>Esc</kbd> 또는 바깥 클릭으로 닫기 |
| 도면 옮기기 | 도면 위를 마우스로 끌기 (커서가 손 모양일 때) | **색은 계층을 뜻하며 27장 내내 같은 뜻을 유지합니다** — 보라 `domain`, 초록 `storage`, 주황 `services`, 파랑 `cli`, 회색은 계층 밖 루트 모듈, 노랑은 디스크 파일입니다. 한 번만 외우면 어느 장이든 읽힙니다.

한 장에 몰아넣지 않은 이유는 "생략 없음"과 "읽힘"이 서로 당기기 때문입니다. 건축 도면집이 배치도·평면도·상세도를 나누고 색인으로 묶는 것과 같은 방식이고, 여기서는 왼쪽 시트 색인이 그 역할을 합니다.

도면 02(의존 방향)는 `tests/test_architecture.py` 가 AST 로 강제하므로 **그 테스트가 통과하는 한 틀릴 수 없습니다**. 나머지는 사람이 그린 것이라 코드가 바뀌면 낡습니다 — 명령이나 상수를 추가할 때 가장 먼저 낡는 것은 도면 09(명령 대응)와 26(설정 소유권)입니다.

### 여는 방법

파일을 브라우저로 열면 됩니다. 도면은 Mermaid 텍스트로 들어 있고 페이지 끝의 스크립트가 CDN 에서 Mermaid 를 받아 SVG 로 그리므로, **이 파일 하나만 인터넷이 필요합니다**(아래 `docs/html/` 학습 문서는 여전히 완전 오프라인입니다). 오프라인으로 봐야 한다면 도면을 미리 SVG 로 구워 두면 됩니다.

### 도면을 고치거나 다시 그리려면

각 도면은 `<pre class="mermaid">` 블록 안의 순수 텍스트입니다. 그 블록만 `.mmd` 파일로 저장하면 아래 어디서든 열립니다.

- **mermaid.live** — 설치 없이 브라우저에서 편집하고 SVG 로 저장
- **VS Code** — `Markdown Preview Mermaid Support` 확장
- **draw.io** — Arrange → Insert → Advanced → Mermaid 로 붙여넣어 도형으로 변환

```bash
# .mmd 를 SVG 로 굽기 (오프라인 열람용)
npx -p @mermaid-js/mermaid-cli mmdc -i p01.mmd -o p01.svg
```

코드에서 자동 생성해 손으로 그린 도면과 대조할 수도 있습니다. 런타임 의존성 0 을 지키려고 전부 일회 실행으로 씁니다.

```bash
uvx --from pylint pyreverse -o svg -p budget_app budget_app   # 도면 04·12 대조
uvx pydeps budget_app --max-bacon 3 -o deps.svg               # 도면 02 대조 (Graphviz 필요)
uvx code2flow budget_app -o calls.svg                         # 도면 09 대조
```

**자동 생성물은 대조용이지 대체용이 아닙니다.** 클래스와 의존은 정확히 뽑아내지만 "왜 `frozen` 인가", "왜 워터마크와 파일 스캔을 둘 다 보는가" 같은 **결정의 이유**는 코드에 형태로 남지 않습니다. 도면마다 붙은 설명 문단이 그 부분입니다.

### 함께 보는 학습 문서

`docs/` 에는 이 코드의 문법·기법·설계를 초보부터 고급까지 해설하는 문서가 함께 있습니다. 도면집이 "무엇이 어디에 있는가"의 지도라면, 이쪽은 "왜 그렇게 되어 있는가"의 본문입니다.

- `docs/00-INDEX.md` — 목차와 읽기 가이드 (여기서 시작)
- `docs/01-overview.md` ~ `docs/12-syntax-and-stdlib.md` — 개요 · 파이썬 기초/심화 · 아키텍처 · 설정과 모델 · 데코레이터 · 저장소 · 서비스 · CLI · 고급 설계 · FAQ와 용어집 · 문법과 표준 라이브러리
- `docs/html/index.html` — 위 문서를 사이드바 내비게이션이 있는 정적 HTML 로 빌드한 것 (외부 CDN 없이 오프라인 동작)

HTML 을 다시 빌드하려면 (프로젝트 venv 를 건드리지 않습니다):

```bash
uv run --no-project --with markdown --with pygments python docs/_build_html.py
```
