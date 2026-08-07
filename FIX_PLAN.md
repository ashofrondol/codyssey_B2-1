# budget_app 수정 계획 (코드 리뷰 후속)

> 6개 관점 멀티에이전트 리뷰 + 적대적 검증(58건 중 55 CONFIRMED / 3 PARTIAL) 결과를 기반으로 한 순차 작업 목록.
> 고심각도 버그는 전부 실행 재현으로 확인된 것들이다.

## 공통 지침 (작업자에게)

- **런타임은 표준 라이브러리만** 사용한다는 제약 유지 (테스트는 .venv의 pytest 사용 가능).
- **Phase 단위로 커밋**한다. 한 커밋에 여러 Phase를 섞지 않는다.
- 버그 수정은 **실패하는 테스트를 먼저 작성해 재현 확인 후** 고친다.
- 기존 docstring 스타일(한국어, '왜' 중심)을 유지하되, **사실과 다른 주장은 반드시 정정**한다.
- `docs/` 학습 문서 12편이 소스 라인 번호를 참조하므로, **소스 수정이 끝난 뒤 마지막에 일괄 갱신**한다 (Phase 6).
- ⚖️ 표시는 사용자 결정이 필요한 항목 — 기본 권고안이 함께 적혀 있다.

---

## Phase 0 — 안전망: 회귀 테스트 작성 (수정 전 필수)

현재 테스트가 0개다. 아래 재현 시나리오를 `tests/`에 pytest로 먼저 작성한다 (이 시점에는 전부 **실패**해야 정상):

- [ ] 0-1. `parse_date('2024-1-5')` → `'2024-01-05'` 정규화 기대 / 비패딩 날짜 거래가 월 요약에 포함되는지
- [ ] 0-2. `budget set 2024-1` 후 `summary 2024-01`에서 예산이 보이는지
- [ ] 0-3. 최대 번호 거래 삭제 후 add 시 **다른 ID**가 발급되는지
- [ ] 0-4. `remove('etc', replace_with=' etc ')`가 차단/정규화되어 고아 거래가 안 생기는지
- [ ] 0-5. `TransactionId('TX-1')`과 `TransactionId('TX-000001')`이 동일 취급되는지
- [ ] 0-6. 개행 없이 잘린 꼬리를 가진 jsonl에 append 시 새 레코드가 살아남는지
- [ ] 0-7. UTF-8 BOM 붙은 CSV import 성공 여부
- [ ] 0-8. `--data-dir <기존 파일 경로>` 실행 시 트레이스백 없이 친절한 오류 + EXIT_IO(3)
- [ ] 0-9. `list --limit 0` 이 "(데이터 없음)"을 출력하지 않는지 (오류 또는 전체 출력)
- [ ] 0-10. 바이트 손상(`\xff`) 줄 하나가 파일 전체 읽기를 죽이지 않는지
- [ ] 정상 경로 스모크 테스트: add→list→search→summary→export→import 왕복

## Phase 1 — 조용한 데이터 손상 버그 (최우선)

- [ ] 1-1. **날짜/월 정규화** — `domain/validators.py:58,67`
  `parse_date`/`parse_month`가 `strptime` 검증 후 원문을 반환한다. `dt.strftime(config.DATE_FORMAT/MONTH_FORMAT)`으로 **재직렬화해 반환**하도록 수정. 기존 파일의 비정규 날짜는 읽기 시 `__post_init__`을 다시 통과하므로 자동 치유된다 — 단, 손상 줄 처리와 충돌 없는지 테스트로 확인.
- [ ] 1-2. **TransactionId 정규화(별칭 제거)** — `domain/config.py:25`, `domain/tx_id.py`
  `TX_ID_PATTERN`이 `^TX-(\d+)$`라 `TX-1`/`TX-000001`이 별개 ID로 공존하고 order=True 문자열 정렬 전제가 깨진다. `TransactionId.__post_init__`에서 번호를 뽑아 `TX_ID_FORMAT`으로 **정규형으로 재포맷**(TX-1 → TX-000001)하는 방식 권장 (기존 저장 데이터도 읽기 시 자동 정규화됨).
- [ ] 1-3. **삭제된 최대 ID 재사용 방지** — `storage/repositories.py:52-71`, `storage/ids.py`
  최대값 파일 스캔만으로 시작점을 잡아 최대 번호 거래 삭제 시 같은 ID가 재발급된다 (skip 정책의 export→import 왕복과 결합 시 조용한 데이터 손실). **최대 발급 번호를 별도 영속화**(예: `data/id_counter` 파일, 원자적 교체로 갱신)하고 `id_allocator()`는 `max(파일 스캔 최대값, 카운터)`로 시작. 1-2 이후에 작업(정규형 전제).
- [ ] 1-4. **카테고리 비교 정규화 통일** — `services/categories.py:37-61`, `storage/repositories.py:102,164-180`
  `CategoryService.remove` 진입부에서 `name`/`replace_with`를 `parse_category`로 정규화한 뒤 사용하고, `category_in_use`/`reassign_category`도 인자를 정규화. `replace_with == name` 자기자신 가드도 정규화 후 비교. (` etc ` 우회로 사용 중 카테고리가 삭제되던 버그)

## Phase 2 — 저장 계층 견고성

- [ ] 2-1. **append 꼬리 개행 확인** — `storage/jsonl.py:181-194`
  append 전 마지막 바이트가 `\n`인지 확인(`rb`로 seek), 아니면 개행을 먼저 쓴다. (찢어진 꼬리에 새 레코드가 병합·소실되던 버그)
- [ ] 2-2. **append 경로 fsync** — `storage/jsonl.py:181-194`
  재작성 경로만 fsync하는 내구성 비대칭 해소: `append`/`append_all`에도 flush+fsync 추가 (CLI 단건 쓰기라 비용 무시 가능).
- [ ] 2-3. **UnitOfWork.commit 실패 후처리** — `storage/unit_of_work.py:77-91`
  두 번째 `os.replace` 실패 시(Windows PermissionError 등) 반쪽 커밋 + tmp 잔존 + 무후처리로 끝난다. commit을 try로 감싸 실패 시 남은 tmp unlink 시도 + 경고 로그(어느 파일까지 반영됐는지) 후 재raise. 죽은 필드 `_committed` 제거.
- [ ] 2-4. **바이트 손상 라인 격리** — `storage/jsonl.py:138-150`
  텍스트 모드 읽기라 `\xff` 한 줄이 UnicodeDecodeError로 파일 전체를 죽인다. `rb`로 줄 분리 후 줄별 decode, 실패 줄은 `RawLine(error=...)`로 편입해 "손상 줄 격리" 약속을 인코딩 층까지 관철.
- [ ] 2-5. **CSV 읽기 utf-8-sig** — `storage/csv_io.py:83`, `storage/config.py:30`
  읽기 인코딩만 `utf-8-sig`로 (BOM 없는 파일에도 무해). 쓰기는 BOM 없는 utf-8 유지(왕복 안전성 주석 근거 유지).
- [ ] 2-6. ⚖️ **태그 CSV 왕복 무손실** — `storage/csv_io.py:159`
  쉼표 포함 태그가 join/split에서 분해된다. 권고: 태그 검증(`parse_tags`)에서 구분자 포함을 거부하는 쪽이 단순(CSV 포맷 불변). 대안: 이스케이프 도입(포맷 변경).
- [ ] 2-7. **`append_many(atomic=True)` 죽은 분기 제거** — `storage/repositories.py:106-119`
  UoW 도입 후 원자 커밋 메커니즘이 2개다. atomic 플래그를 제거하고 호출부를 정리.
- [ ] 2-8. ⚖️ **동시 실행 방어(선택)** — `storage/jsonl.py:59`
  최소안 권고: `.tmp` 이름 고유화(mkstemp) + 데이터 폴더 단일 잠금 파일(msvcrt/fcntl 래퍼). 과제 범위상 스코프 아웃한다면 README에 "단일 프로세스 전제"를 명시하는 것으로 대체.

## Phase 3 — CLI 정확성

- [ ] 3-1. **`ctx.prepare()`를 오류 방패 안으로** — `cli/app.py:61-75`
  AppContext 생성+prepare가 `@handle_errors` 밖이라 `--data-dir` 오류가 원시 트레이스백(exit 1)으로 터진다. prepare 이후 로직을 handle_errors와 동일 정책으로 감싸 EXIT_IO 경로로 수렴시키기.
- [ ] 3-2. **`--limit`/`--top` 양수 검증** — `cli/parser.py`, `cli/presenter.py:51`
  argparse type에서 양수만 허용 (limit 0/음수 → "(데이터 없음)" 거짓 출력 제거). summary `--top` 가드와 일관되게.
- [ ] 3-3. **export 기간 옵션 조합 방어** — `cli/handlers.py:153`
  `--month`와 `--from/--to` 동시 지정 시 조용히 무시하지 말고 오류로 차단.
- [ ] 3-4. **`--data-dir` 위치 규칙 정합화** — `cli/parser.py:68`
  `--debug`처럼 최상위에서도 받거나, 오도하는 오류 메시지를 정정.
- [ ] 3-5. **update의 tags 타입 계약** — `cli/handlers.py:124`
  쉼표 문자열을 `Optional[List[str]]`로 선언된 `TransactionPatch.tags`에 그대로 넣는다. 핸들러에서 `validators.parse_tags`를 통과시켜 전달.
- [ ] 3-6. **예기치 못한 예외 로깅 레벨** — `cli/error_handler.py:105`
  스택트레이스가 DEBUG로만 남아 기본 실행에서 증발한다. logger.exception(ERROR)로 격상.

## Phase 4 — 계층 규칙을 코드로 강제

- [ ] 4-1. **CLI→storage 우회 3곳 제거** — `cli/prompts.py:20`, `cli/handlers.py:21,28,34`
  (a) backup을 감싸는 서비스 메서드 추가 후 핸들러는 서비스 호출, (b) `ctx.cats.list_names()` 직접 호출 → `ctx.cat_service.list_names()`, (c) prompts는 `CategoryStore` 타입 대신 필요한 callable(또는 서비스)을 주입받도록. 카테고리 등록 검사 메시지 이중 구현(prompts vs TransactionService)도 이때 단일화.
- [ ] 4-2. **AppContext 저장소 비공개화** — `context.py:42-48`
  `txs/cats/budgets` → `_txs/_cats/_budgets`, 핸들러에는 서비스만 노출. (4-1 완료가 선행 조건)
- [ ] 4-3. **ImportReport에서 표시 문자열 제거** — `domain/results.py:73-74`, `services/importexport.py:51-61`
  errors/duplicate_notes에 포맷 완료된 사용자 문자열 대신 구조화 데이터(lineno, reason)를 담고, 문자열 포맷은 presenter로 이동. MonthlySummary(원자료+property) 설계와 일관되게.
- [ ] 4-4. **config/messages 자기 규칙 위반 정리** — `storage/unit_of_work.py:90`, `budget_app/config.py`
  하드코딩 한국어 debug 문자열을 `storage/messages.py`로. 루트 config의 로거 이름 alias 재수출(cli/storage config) 등 순수 보일러플레이트 정리. (9개 상수 모듈의 전면 통합은 ⚖️ 선택 — 과제 서사상 유지해도 됨)

## Phase 5 — 디자인 패턴 정합화

- [ ] 5-1. ⚖️ **Specification 패턴 처리** — `domain/specs.py`
  Or/Not/연산자/`date_range` 사용처 0, "조건 추가 = 클래스 하나, 기존 코드 무변경" 문서 주장 거짓(실제 4곳 수정 필요).
  **권고(과제가 패턴 시연 목적이므로 유지 쪽): 죽은 `date_range` 삭제 + 허위 문서 주장을 "조합 대수는 선행 투자이며 현재 소비자는 AND 하나"로 정직하게 정정.** 대안: Or/Not/연산자까지 걷어내고 평평한 필드 검사로 축소.
- [ ] 5-2. **UoW 문서 정직화** — `storage/unit_of_work.py`
  Fowler식 변경 추적 UoW가 아니라 staged-rename 배치임을 docstring에 명시(또는 `StagedCommit` 등으로 개명 ⚖️). commit 실패 의미론(2-3에서 수정)도 문서에 반영. 서비스가 `plan_rewrite` 반환 줄 목록을 나르는 계층 누수는 `uow.stage(store, transform, extra=...)` 형태로 UoW가 내부에서 plan을 호출하게 바꾸면 해소.
- [ ] 5-3. **이중 전체 스캔 제거 + 존재 판정 통일** — `storage/repositories.py:121-180`
  delete/replace/reassign이 존재 확인 스캔 후 재작성 스캔을 또 한다(update는 파일 3회 읽기). `rewrite`가 found 여부를 반환하게 해 1회 스캔으로 통일하고, delete(원시 id 스캔)와 replace(유효 엔티티)의 존재 판정 기준 비대칭도 해소. "변경 없으면 커밋 안 함"은 plan 결과 비교로 유지.
- [ ] 5-4. **엔티티 frozen 전환** — `domain/entities.py`
  "생성자가 유일한 불변식 강제 지점" 주장과 달리 전부 가변이다. Transaction/Budget/Category를 `frozen=True`로 바꾸고 `__post_init__`은 `object.__setattr__` 사용 (TransactionId가 이미 이 방식). 변경은 이미 `with_patch` 경유라 제자리 수정 코드는 없음 — 전환 후 전체 테스트로 확인.

## Phase 6 — 코드 품질·문서 정합

- [ ] 6-1. **ruff 자체 설정 통과** — 전 모듈
  pyproject 선언 설정(py310, E/F/I/UP/B) 기준 167건. `ruff check --fix` 후 잔여 수동 정리 (Optional→`| None`, List/Dict→list/dict, deprecated typing import, 문자열 어노테이션 제거 등). CI 없으니 최소한 README에 검사 명령 명시.
- [ ] 6-2. **죽은 코드 제거**
  `Transaction.id_number`(entities.py:66), `ImportReport.has_problems`, `ParsedRow.lineno`, (`_committed`·`date_range`는 앞 Phase에서 제거됨).
- [ ] 6-3. **잔여 검증 구멍** — `domain/validators.py`
  `parse_tags` 중복 제거(순서 보존 dedupe), `parse_amount`의 `1_000` 언더스코어 통과 차단(`^\d+$` 검사).
- [ ] 6-4. **문서-코드 정합화**
  README 10장 "모든 읽기는 yield 기반" 과장 정정(진짜 스트리밍은 summary/export뿐), `cli/__init__.py`·`cli/parser.py`의 stale 참조(존재하지 않는 cli.py, 성립 않는 순환 import 근거), `errors.py` docstring의 사라진 모듈 참조 정정.
- [ ] 6-5. **docs/ 12편 라인 번호 일괄 갱신** — 모든 소스 수정 완료 후 마지막에.
- [ ] 6-6. **전체 테스트 + 스모크 실행**으로 마무리 검증.
