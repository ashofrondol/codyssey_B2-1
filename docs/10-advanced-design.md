# 10. 고급 설계 주제 — 원자성, 불변식, 성능, 트레이드오프

이 설계가 **무엇을 보장하고 무엇을 보장하지 않는지**를 정직하게 분석합니다. crash 시나리오, ID 불변식, 성능 한계, 동시성, 그리고 남아 있는 약점까지 다룹니다.

> **난이도**: 🔴 고급
>
> **먼저 읽으면 좋은 문서**: [07. 저장소 계층](./07-repository.md), [08. 서비스 계층](./08-services.md)

---

## 1. 원자성 심화 — 세 호출이 각각 보장하는 것

### 1.1 일반 개념: rename 의 원자성

POSIX 와 Windows 모두 "같은 파일시스템 안에서의 이름 바꾸기"를 **원자적 연산**으로 규정합니다. 외부 관찰자 입장에서 그 경로가 가리키는 대상은 "이전 파일" 아니면 "새 파일"이며, **중간 상태가 존재하지 않습니다.**

파이썬의 `os.replace(src, dst)` 는 대상이 이미 있어도 덮어쓰는 rename 이고, 플랫폼 차이를 흡수해 이 보장을 제공합니다.

> **🔎 문법의 출처** — `os.replace` 는 파이썬 3.3 에서 추가됐습니다. 그 전에는
> `os.rename` 하나뿐이었는데, POSIX 에서는 대상이 있어도 덮어쓰고 Windows 에서는
> `FileExistsError` 로 실패해 **플랫폼마다 동작이 달랐습니다.** `os.replace` 는
> "항상 덮어쓴다"로 의미를 통일한 함수입니다. 그래서 이 코드는 `rename` 이 아니라
> `replace` 를 씁니다. → [12 §3](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `os.replace` 는 CPython 의 `posixmodule.c` 에서 POSIX 계열은
> `rename(2)` 시스템 콜로, Windows 는 `MoveFileExW(src, dst, MOVEFILE_REPLACE_EXISTING)`
> 로 내려갑니다. 원자성은 **같은 파일시스템 안에서 디렉터리 엔트리를 교체**하는
> 것에 대해서만 보장되며(파일시스템이 다르면 POSIX 는 `EXDEV` 로 실패합니다),
> "내용이 디스크에 도달했다"는 뜻은 전혀 아닙니다 — 그래서 앞에 `fsync` 가
> 필요합니다. → [12 §3](./12-syntax-and-stdlib.md)

### 1.2 이 프로젝트의 구현

budget_app/storage/jsonl.py:48-72

```python
def stage_lines(path: Path, lines: Iterable[str]) -> Path:
    """임시 파일에 전부 쓰고 디스크에 내린 뒤, 그 임시 경로를 돌려준다.
    ...
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + config.TMP_SUFFIX)
    with open(
        tmp,
        "w",
        encoding=config.FILE_ENCODING,
        errors=config.FILE_ERRORS,
        newline=config.LINE_TERMINATOR,
    ) as f:
        for line in lines:
            f.write(line + config.LINE_TERMINATOR)
        f.flush()
        os.fsync(f.fileno())
    return tmp
```

**쓰기가 두 단계로 나뉜 것**이 Unit of Work 패턴을 위한 준비입니다. 이전에는
``atomic_write_lines`` 하나가 "tmp 작성 → fsync → replace"를 통째로 했는데, 그러면
**여러 파일을 함께 커밋할 수 없습니다.** 지금은 ``stage_lines`` 가 준비만 하고
``commit_staged`` 가 교체만 하므로, 호출자가 "전부 준비 → replace 만 연달아"를
구성할 수 있습니다(→ [07 §9](./07-repository.md)).

파일 하나만 바꾸는 경로(``rewrite``)는 여전히 ``atomic_write_lines`` 한 줄로 둘을
연달아 부릅니다 — 기존 사용처는 아무것도 달라지지 않았습니다.

budget_app/storage/jsonl.py:75-87

```python
def commit_staged(tmp: Path, target: Path) -> None:
    """준비된 임시 파일을 대상 이름으로 교체한다 — 같은 파일시스템에서 원자적."""
    os.replace(tmp, target)


def atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    """파일 하나를 원자적으로 교체한다 — 준비와 커밋을 연달아 수행.

    이름에 밑줄이 없는 이유: 같은 계층의 ``ids.IdWatermark`` 도 이 함수를 쓴다.
    ...
    """
    commit_staged(stage_lines(path, lines), path)
```

**이름에 밑줄이 없는 것이 의도적입니다.** 파이썬에서 앞 밑줄(`_name`)은 "이 모듈
밖에서는 쓰지 말라"는 관례적 신호인데, 이 함수는 `storage/ids.py:78` 의
`IdWatermark.remember` 도 씁니다. 즉 **저장소 계층의 공용 도구**라 밑줄이 없습니다
(소스 docstring 이 그 이유를 직접 밝힙니다).

> **🔎 문법의 출처** — 앞 밑줄은 문법이 아니라 **관례**입니다(PEP 8). 파이썬이
> 강제하는 것은 딱 하나, `from module import *` 가 `_` 로 시작하는 이름을 가져오지
> 않는다는 것뿐입니다. 클래스 안의 **두 개**짜리 밑줄(`__name`)만이 진짜 문법으로,
> 컴파일러가 `_클래스명__name` 으로 이름을 바꿉니다(name mangling).
> → [12 §1-B](./12-syntax-and-stdlib.md)

**세 호출이 서로 다른 것을 보장합니다.**

```
 파이썬 버퍼        OS 페이지 캐시        물리 디스크          디렉터리 엔트리
      │                  │                   │                     │
      ├── f.flush() ────▶│                   │                     │
      │                  ├── os.fsync() ────▶│                     │
      │                  │                   │◀── os.replace() ────┤
      │                  │                   │      (이름 교체)      │
```

| 호출 | 보장 | 보장하지 않는 것 |
|---|---|---|
| `f.flush()` | 파이썬 버퍼 → OS 버퍼 | OS 버퍼가 디스크에 도달했는지 |
| `os.fsync(fd)` | OS 버퍼 → 물리 디스크 | 이름이 바뀌었는지 |
| `os.replace()` | 이름 교체가 **원자적** | 내용이 디스크에 도달했는지 |

> **⚙️ 내부 동작 — `f.flush()`** — 여기서 `f` 는 텍스트 모드 `open()` 이 돌려준
> `io.TextIOWrapper` 입니다. 파이썬의 파일 객체는 **3층**입니다:
> `TextIOWrapper`(문자→바이트 인코딩) → `BufferedWriter`(바이트 버퍼, 기본 8 KiB
> 안팎) → `FileIO`(원시 fd). `flush()` 는 이 3층을 차례로 밀어내려 마지막에
> `write(2)` 시스템 콜을 냅니다. 즉 flush 가 끝나면 데이터는 **커널 안**에 있고,
> 여전히 물리 디스크에는 없습니다. → [12 §3](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `os.fsync(f.fileno())`** — `fileno()` 는 3층을 뚫고 내려가
> 커널이 아는 정수 파일 디스크립터를 꺼냅니다. `os.fsync` 는 POSIX 에서
> `fsync(2)`, Windows 에서 CRT 의 `_commit()`(내부적으로 `FlushFileBuffers`)로
> 내려가 커널 페이지 캐시를 저장 장치까지 내립니다. **`flush()` 없이 `fsync` 만
> 부르면 소용이 없습니다** — 파이썬 버퍼에 남아 있는 바이트는 커널이 아직 모르기
> 때문입니다. 그래서 코드에서 둘이 반드시 붙어 다닙니다.
> → [12 §3](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처 — `with open(...) as f:`** — `with` 는 PEP 343 으로 파이썬 2.5 에
> 들어왔습니다. `with X() as f:` 는 `f = X().__enter__()` 를 실행한 뒤 본문을
> `try/finally` 로 감싸 `f.__exit__(...)` 를 부르는 코드로 풀립니다(desugar).
> 파일 객체의 `__exit__` 이 `close()` 를 부르고, `close()` 는 **닫기 전에
> `flush()` 를 수행**합니다. 이 코드가 `with` 블록 **안에서** 명시적으로
> `flush()`/`fsync()` 를 부르는 이유가 여기 있습니다 — `with` 를 나간 뒤에는
> `fileno()` 가 이미 닫힌 fd 라 `fsync` 를 걸 수 없습니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

`fsync` 는 리팩터에서 추가됐습니다. 이전 코드는 `os.replace` 만 있었습니다.
지금은 **두 쓰기 경로가 같은 내구성을 약속합니다** — 재작성 경로(`stage_lines`,
storage/jsonl.py:70-71)뿐 아니라 이어 쓰기 경로(`_append_lines`,
storage/jsonl.py:246-247)도 `flush` + `fsync` 로 끝납니다. 한쪽만 fsync 하면
"어느 명령으로 저장했느냐"에 따라 내구성이 달라지는데, 사용자가 그 차이를
알 방법이 없습니다.

### 1.3 crash 시나리오 4종

**시나리오 A — 임시 파일 쓰기 도중 프로세스 종료**

```
상태: tmp 에 절반 기록, os.replace 전
결과: ✅ 원본 파일 무사. tmp 찌꺼기만 남음.
근거: 원본은 replace 이전까지 한 글자도 바뀌지 않는다.
정리: 다음 같은 연산이 tmp 를 덮어쓴다(같은 이름을 재사용하므로 누적되지 않음).
```

> **⚙️ 내부 동작 — tmp 이름이 고정인 것** — 임시 경로는
> `path.with_suffix(path.suffix + config.TMP_SUFFIX)` 로 만듭니다(storage/jsonl.py:60).
> `Path.with_suffix` 는 **마지막 확장자만 갈아 끼웁니다**. 그래서
> `transactions.jsonl` 의 `suffix` 는 `".jsonl"` 이고, 여기에 `".tmp"` 를 붙여
> `".jsonl.tmp"` 로 바꾸면 `transactions.jsonl.tmp` 가 됩니다. 확장자가 없는
> `id_counter` 는 `suffix` 가 `""` 라 그냥 `id_counter.tmp` 가 됩니다.
> `tempfile.mkstemp` 처럼 **무작위 이름을 쓰지 않는 것이 의도**입니다 — 이름이
> 고정이라야 crash 로 남은 찌꺼기가 다음 실행에서 덮어써지고 무한히 쌓이지 않습니다.
> 대신 **같은 파일에 대한 동시 쓰기는 서로의 tmp 를 밟습니다**(→ §6).
> → [12 §2-B](./12-syntax-and-stdlib.md)

**시나리오 B — `os.replace` 실행 순간 전원 차단**

```
상태: 이름 교체 중
결과: ✅ "이전 파일" 또는 "새 파일" 둘 중 하나. 반쪽 파일은 없음.
근거: rename 이 원자적이므로.
```

**시나리오 C — `fsync` 후 `replace` 전 전원 차단**

```
상태: tmp 는 디스크에 완전히 기록됨. 이름은 아직 원본.
결과: ✅ 원본이 살아 있음. tmp 는 완전하지만 사용되지 않음.
근거: 데이터는 잃지 않았고 연산만 취소된 것.
```

**시나리오 D — (fsync 가 없었다면) replace 직후 전원 차단**

```
상태: 이름은 새 파일을 가리키지만 내용이 아직 OS 버퍼에만 있음
결과: ❌ 새 이름이 빈 파일 또는 잘린 파일을 가리킬 수 있음
근거: replace 는 메타데이터(이름) 연산이고, 데이터가 디스크에 도달했음을 보장하지 않음.
```

**D 를 막은 것이 `fsync` 입니다.** 이론적인 위험처럼 보이지만, ext4 의 `data=writeback` 모드나 배터리 없는 SSD 캐시에서는 실제로 재현됩니다.

### 1.4 남은 한계 (1) — 디렉터리 fsync

**엄밀히 말하면 아직 완전하지 않습니다.** `os.replace` 후 **디렉터리 엔트리 자체**를 fsync 하지 않았습니다.

`fsync(파일)` 이 내려 보내는 것은 **그 파일의 내용과 그 파일의 메타데이터**입니다. 그런데 "`transactions.jsonl` 이라는 이름이 어느 inode 를 가리키는가"는 파일이 아니라 **부모 디렉터리**에 적힌 정보입니다. `os.replace` 가 바꾸는 것이 바로 그 디렉터리 엔트리이고, 그 변경은 아직 디스크에 내려가지 않았을 수 있습니다.

```python
# 개선안 — 현재 코드에 없음
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)      # 디렉터리 엔트리 변경을 디스크에 내림
    finally:
        os.close(dir_fd)
```

이것이 없으면 **"파일 내용은 디스크에 있는데 새 이름이 아직 디스크에 반영되지 않은"** 창이 남습니다. 그 순간 전원이 끊기면 재부팅 후 옛 파일이 보이거나(연산 취소), 최악의 경우 이름이 어느 쪽도 확정되지 않을 수 있습니다. 다만:

- 창이 매우 짧고(밀리초 단위),
- Windows 에는 디렉터리 fsync 에 해당하는 이식 가능한 API 가 없으며(아래 참고),
- 이 앱은 개인용 가계부라 트랜잭션 DB 수준의 내구성이 요구되지 않습니다.

> **⚙️ 내부 동작 — 왜 이식이 안 되는가** — 위 개선안이 성립하는 것은 POSIX 가
> "디렉터리도 파일"이라 `open(2)` 으로 열 수 있기 때문입니다. Windows 에서는
> `os.open(디렉터리)` 자체가 `PermissionError` 로 실패합니다(디렉터리 핸들을
> 얻으려면 `CreateFileW` 에 `FILE_FLAG_BACKUP_SEMANTICS` 가 필요한데 파이썬
> 표준 라이브러리는 이를 노출하지 않습니다). 즉 이 코드를 넣으면 **한 플랫폼에서만
> 동작하는 분기**가 생깁니다. 이 프로젝트가 생략한 이유의 절반이 그것입니다.
> → [12 §3](./12-syntax-and-stdlib.md)

### 1.5 남은 한계 (2) — Windows 에서 `replace` 는 그냥 실패할 수 있습니다

원자성 논의는 보통 "전원이 끊기면"으로 흐르지만, 실무에서 훨씬 흔한 실패는 이쪽입니다. **Windows 에서 대상 파일을 다른 프로세스가 열고 있으면 `os.replace` 가 `PermissionError` 로 실패합니다.** 텍스트 에디터로 `transactions.jsonl` 을 열어 둔 채 `delete` 를 실행하면 재현됩니다. POSIX 의 `rename(2)` 은 대상이 열려 있어도 성공합니다(열려 있던 프로세스는 이름을 잃은 옛 inode 를 계속 봅니다).

이 차이가 실제 코드에 반영돼 있습니다.

budget_app/storage/unit_of_work.py:145-156

```python
        done: list[str] = []
        try:
            while self._staged:
                tmp, target = self._staged[0]
                commit_staged(tmp, target)
                self._staged.pop(0)  # 성공한 것만 목록에서 뺀다 — 나머지는 rollback 대상
                done.append(target.name)
        except OSError:
            pending = [target.name for _, target in self._staged]
            logger.warning(messages.LOG_UOW_PARTIAL, done or "없음", pending)
            self.rollback()
            raise
```

"rename 두 번 사이의 창"이 전원 차단만 뜻하지 않는다는 것 — 그래서 두 번째 `replace` 실패를 **로그로 남기고 예외를 그대로 올린다**는 것이 `UnitOfWork.commit` 의 docstring(unit_of_work.py:128-143)이 직접 설명하는 내용입니다.

**"어디까지 보장하고 어디부터는 안 하는지"를 아는 것**이 중요합니다. 과제 방어에서 "완벽하다"고 말하는 것보다 이 경계를 정확히 말하는 편이 낫습니다.

---

## 2. 데이터 무결성 불변식 — 리팩터가 세운 세 가지

이 프로젝트가 **파일 상태에 대해 보장하는 것**을 명시합니다. 셋 다 리팩터에서 세워졌습니다.

### 2.1 불변식 1 — "해석하지 못한 줄은 사라지지 않는다"

**보장 내용**: 어떤 쓰기 연산도 파싱에 실패한 줄을 삭제하지 않습니다.

**구현**: 재작성의 재료가 `iter_raw()`(모든 줄, storage/jsonl.py:162-179) 이고, 해석 불가 줄은 `raw.text` 를 그대로 다시 씁니다.

budget_app/storage/jsonl.py:289-292

```python
        for raw in self.iter_raw():
            if not raw.is_valid:
                lines.append(raw.text)  # 해석 불가 — 원문 보존
                preserved += 1
```

**같은 약속이 인코딩 층까지 내려갑니다.** 읽기와 쓰기가 모두 `errors="surrogateescape"` 를 씁니다(`storage/config.py:25` 의 `FILE_ERRORS`). 이전에는 엄격 디코딩이라 UTF-8 이 아닌 바이트가 **한 줄만 있어도 파일 전체 읽기가 `UnicodeDecodeError` 로 죽었습니다** — JSON 이 깨진 줄은 격리하면서 바이트가 깨진 줄은 격리하지 못하는, 같은 약속의 구멍이었습니다.

> **🔎 문법의 출처 — `surrogateescape`** — PEP 383(파이썬 3.1)이 도입한 오류 처리기
> 입니다. 디코딩할 수 없는 바이트 `0xNN` 을 예외 대신 `U+DCNN`(대리 영역의 미사용
> 코드 포인트)으로 바꿔 담아 두고, 같은 처리기로 **인코딩할 때 원래 바이트를 그대로
> 복원**합니다. 그래서 "읽어서 다시 쓰면 바이트가 동일하다"는 무손실 왕복이
> 성립하고, 손상 줄 보존 약속이 인코딩 층에서도 지켜집니다.
> → [12 §3](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — 대리 문자는 정상 문자가 아니므로 그대로 `print` 하면
> `UnicodeEncodeError` 가 납니다. 이 코드가 안전한 이유는 손상 줄을 **화면에 찍지
> 않고** 파일로만 되돌려 쓰기 때문입니다. 로그에는 파일명·줄 번호·오류 사유만
> 남습니다(storage/jsonl.py:203). → [12 §3](./12-syntax-and-stdlib.md)

**리팩터 전 위반 사례**:

```
$ cat data/transactions.jsonl
{"id":"TX-000001", ...}
{ BROKEN LINE }
{"id":"TX-000002", ...}

$ python -m budget_app delete --id TX-000001
$ cat data/transactions.jsonl
{"id": "TX-000002", ...}          ← BROKEN LINE 이 함께 사라짐
```

**리팩터 후 검증**:

```
$ python -m budget_app delete --id TX-000001
[WARNING] transactions.jsonl: 손상된 줄 1개를 해석하지 않고 원문 그대로 보존했습니다.
$ cat data/transactions.jsonl
{ BROKEN LINE }                   ← 보존됨
{"id": "TX-000002", ...}
```

**왜 중요한가.** 손상된 줄은 **복구 가능한 데이터일 수 있습니다.** 사용자가 텍스트 에디터로 고칠 기회를 프로그램이 빼앗으면 안 됩니다. 게다가 유실 사실을 알리지도 않았다는 것이 더 큰 문제였습니다.

**주의할 점**: 이 불변식은 "손상 줄이 파일 안에서 **위치**를 유지한다"는 보장까지는 아닙니다. 삭제된 줄이 앞에 있었다면 손상 줄의 줄 번호는 당겨집니다.

### 2.2 불변식 2 — "발급된 id 는 재사용되지 않는다"

**보장 내용**: 새 거래에 발급되는 id 는 **파일 어디에도 존재하지 않는** 번호입니다.

**구현**: `id_state()` 가 `iter_raw()` 기반이므로 검증에 실패하는 줄의 id 도 인식하고(storage/repositories.py:53-63), `IdAllocator.next()` 가 `taken` 집합을 확인하며 발급합니다(storage/ids.py:105-116).

거기에 **파일 스캔만으로는 부족한 축이 하나 더** 있습니다. 스캔 최대값은 삭제하면 줄어들어 지운 번호가 부활하므로, `id_allocator()` 는 스캔 최대값과 **워터마크 파일**(`data/id_counter`, `IdWatermark`)의 **최대값**에서 시작합니다(storage/repositories.py:65-77). 워터마크는 줄어들지 않습니다.

> **⚙️ 내부 동작 — `taken` 이 `set` 인 이유** — `set` 은 해시 테이블이라 `in` 검사가
> 평균 O(1) 입니다. 리스트면 O(N) 이 되어 `IdAllocator.next()` 의 `while` 루프가
> 최악에 O(N²) 이 됩니다. 이 집합에 `TransactionId` **값 객체**를 그대로 담을 수
> 있는 것은 그것이 `@dataclass(frozen=True)` 라 파이썬이 `__hash__` 를 자동으로
> 만들어 주기 때문입니다(`eq=True` + `frozen=True` 조합에서만 생성됩니다).
> → [12 §1-B](./12-syntax-and-stdlib.md)

**리팩터 전 위반 사례**:

```
$ cat data/transactions.jsonl
{"id":"TX-000009","amount":0, ...}            ← amount=0 → 검증 실패
{"id":"TX-000010","date":"2024-13-99", ...}   ← 날짜 불량 → 검증 실패

$ python -m budget_app import --from new.csv
$ tail -1 data/transactions.jsonl
{"id": "TX-000001", ...}                       ← 1번부터 재발급 (충돌 대기 상태)
```

**리팩터 후 검증**:

```
$ python -m budget_app import --from new.csv
$ tail -1 data/transactions.jsonl
{"id": "TX-000011", ...}                       ← 검증 실패 줄의 id 도 인식
```

**두 단계 방어:**

```
1) _scan_id: raw.data 에서 id 를 읽음  (JSON 은 되지만 규칙 위반인 줄)
              실패 시 원문 정규식 search  (JSON 조차 아닌 줄)
2) IdAllocator.next(): taken 에 있으면 건너뛰고 다음 번호
```

**여전히 남는 위험**: 파일을 손으로 편집해 `"id": "TX-abc"` 처럼 규칙에서 완전히 벗어난 값을 넣으면 스캔이 못 찾습니다. 다만 그런 id 는 `TransactionId.parse`(domain/tx_id.py:104-107)를 통과할 수 없으므로 — 정확히는 `__post_init__` 의 `_EXACT.match` 가 거부하므로(domain/tx_id.py:83-89) — 프로그램이 만들지 않습니다.

> **⚙️ 내부 동작 — `re.match` vs `re.search`** — 두 스캔 단계가 쓰는 정규식 메서드가
> 다릅니다. 검증용 `_EXACT.match` 는 **문자열 처음부터** 맞춰 보고(끝까지 맞을
> 필요는 없어서 패턴에 `$` 가 들어 있습니다), 발굴용 `_SCAN.search` 는 **줄 어디든**
> 훑습니다(domain/tx_id.py:45-48, 116). `re.compile` 로 모듈 최상위에서 미리 컴파일해
> 두는 것은, 정규식 객체를 한 번만 만들어 두면 파일의 모든 줄이 그것을 재사용하기
> 때문입니다(`re` 모듈 내부 캐시에 의존하지 않는 명시적인 방식입니다).
> → [12 §2-A](./12-syntax-and-stdlib.md)

### 2.3 불변식 3 — "export → import 왕복은 멱등이다"

**보장 내용**: 내보낸 CSV 를 그대로 다시 가져오면 데이터가 변하지 않습니다.

**구현**: export 가 `id` 컬럼을 포함하고(storage/csv_io.py:131-148), import 가 이미 있는 id 를 중복으로 인식합니다(`_resolve_id`, services/importexport.py:133-164).

> **⚙️ 내부 동작 — 왕복을 지키는 인코딩 비대칭** — 쓰기는 `utf-8`, 읽기는
> `utf-8-sig` 입니다(storage/config.py:39-40). `utf-8-sig` 는 파일 맨 앞의
> BOM(`EF BB BF`)이 **있으면 먹고 없으면 그냥 넘어가는** 코덱이라, 엑셀이 저장한
> CSV 도 첫 컬럼명이 `﻿id` 로 깨지지 않습니다. 반대로 쓸 때 `utf-8-sig` 를
> 쓰면 **우리가 BOM 을 만들어** 다른 도구를 깨뜨리므로 쓰기는 BOM 없는 `utf-8` 로
> 고정합니다. "관대하게 읽고 엄격하게 쓴다"의 구체적인 사례입니다.
> → [12 §3](./12-syntax-and-stdlib.md)

**리팩터 전 위반 사례**:

```
$ python -m budget_app export --out rt.csv --month 2024-01
[완료] rt.csv (1 records)
$ python -m budget_app import --from rt.csv
[완료] mode=부분 성공, imported=1, skipped=0     ← 같은 거래가 복제됨
```

**리팩터 후 검증**:

```
$ python -m budget_app import --from rt.csv
[완료] mode=부분 성공, imported=0, duplicated=1, skipped=0
```

**멱등성(idempotence)** 이란 "같은 연산을 여러 번 해도 결과가 한 번 한 것과 같다"는 성질입니다. 백업·복구 시나리오에서 특히 중요합니다 — 복구 스크립트가 중간에 죽어 다시 실행해도 데이터가 두 배가 되지 않습니다.

**의도적 예외**: `--on-duplicate new-id` 를 쓰면 멱등하지 않습니다. "같은 내역을 의도적으로 복제"하는 것이 목적이기 때문입니다.

**한계**: 멱등성은 `id` 컬럼이 있을 때만 성립합니다. `--no-id` 로 내보낸 파일은 매번 새 id 를 받습니다. 이 트레이드오프는 문서화되어 있습니다(README §6).

---

## 3. import 실패 정책 — 준비→커밋 2단계 트랜잭션

### 3.1 두 정책 축

| 축 | 다루는 것 | 옵션 | 기본 |
|---|---|---|---|
| 실패 정책 | 데이터가 **잘못된** 줄 | `--atomic` | 부분 성공 |
| 중복 정책 | 이미 **저장된** 거래 | `--on-duplicate` | `skip` |

**두 축이 독립이라는 것**이 설계의 핵심입니다. "깨진 줄은 전부 거부하되 중복은 조용히 넘어간다"(`--atomic --on-duplicate skip`) 같은 조합이 자연스럽게 표현됩니다.

### 3.2 준비→커밋 = 사실상의 트랜잭션

```
[준비 단계 — 파일을 읽기만 함]
    ┌──────────────────────────────────────────┐
    │ id_allocator()   거래 파일 1회 스캔        │
    │ name_set()       카테고리 파일 1회 스캔     │
    │                                          │
    │ for row in csv:                          │
    │     parse_row()  ← 실패 + atomic → 중단!  │
    │     _resolve_id() ← 중복 + error → 중단!  │
    │     batch 에 적재 (메모리)                 │
    └──────────────────────────────────────────┘
                        │
                        │ 여기까지 파일은 그대로
                        ▼
[커밋 단계 — 처음으로 파일이 바뀜]
    ┌──────────────────────────────────────────┐
    │ cats.add_many(new_categories)            │
    │ txs.append_many(transactions, atomic)    │
    └──────────────────────────────────────────┘
```

**DB 트랜잭션과의 대응:**

| DB 개념 | 이 프로젝트의 대응 |
|---|---|
| BEGIN | `_prepare` 시작 |
| 검증·준비 | 행별 `parse_row` + `_resolve_id` → `_Batch` 적재 |
| ROLLBACK | 예외로 함수 탈출 → `_commit` 미실행 |
| COMMIT | `_commit` → `os.replace` |
| 원자성 | `os.replace` 의 rename 원자성 |

### 3.3 부수 효과까지 롤백되는 이유

**카테고리 자동 등록이 커밋 단계에 있습니다.**

budget_app/services/importexport.py:188-206
```python
    def _commit_atomic(self, batch: _Batch) -> int:
        """원자 모드 — 두 파일을 **한 단위로** 커밋한다.
        ...
        """
        fresh_categories = [Category(name=n) for n in batch.new_categories]
        # 파일을 저장소 밖(UoW)에서 쓰므로 id 워터마크는 여기서 명시적으로 알린다.
        self.txs.remember_ids(batch.transactions)
        with UnitOfWork() as uow:
            if fresh_categories:
                uow.stage(self.cats, extra=fresh_categories)
            uow.stage(self.txs, extra=batch.transactions)
        return len(batch.transactions)
```

준비 단계에서는 `batch.new_categories` 리스트에 **이름만 모읍니다.** 만약 준비 중에 카테고리를 바로 등록했다면, 원자 모드에서 실패했을 때 "거래는 안 들어갔는데 카테고리만 늘어난" 상태가 남습니다.

**실제 검증:**

```bash
$ python -m budget_app import --from mixed.csv --atomic --data-dir ./d5
[오류] 원자적 가져오기 실패 — line 3: ... (반영된 항목 없음)
$ wc -l < ./d5/transactions.jsonl
0                                        ← 거래 0건
$ python -m budget_app category list --data-dir ./d5 | wc -l
5                                        ← 기본 5개만 (CSV 의 salary 안 늘어남)
```

**ID 발급도 같은 논리입니다.** 준비 단계의 `IdAllocator` 는 메모리 객체이므로, 실패하면 발급 기록이 흔적 없이 사라집니다.

### 3.4 남은 비원자성 — 정직한 분석

**부분 성공 모드(기본)의 커밋 단계 안에는 두 번의 파일 쓰기가 있습니다.**

budget_app/services/importexport.py:185-186

```python
        self.cats.add_many(batch.new_categories)
        return self.txs.append_many(batch.transactions)
```

첫 줄이 `categories.jsonl` 에 쓰고, 둘째 줄이 `transactions.jsonl` 에 씁니다. **두 쓰기 사이에 프로세스가 죽으면** 카테고리만 등록되고 거래는 안 들어간 상태가 됩니다.

**`--atomic` 모드는 이 자리를 좁혔습니다.** 위 §3.3 의 `_commit_atomic` 은 두 파일의 최종 내용을 각각 `.tmp` 로 준비한 뒤 `os.replace` 두 번을 연달아 실행하므로, 취약 구간이 "파일 쓰기 2회 사이"에서 "rename 2회 사이"로 줄어듭니다. **없어진 것은 아닙니다** — 진짜 다중 파일 원자성은 저널이나 SQLite 가 필요합니다(unit_of_work.py:38-42 가 이 경계를 직접 적어 두었습니다). 아래 표는 좁히지 않은 **부분 성공 모드** 기준입니다.

**이 상태가 실제로 문제인가?**

| 관점 | 판단 |
|---|---|
| 데이터 유실 | 없음 — 기존 거래는 그대로 |
| 사용자 혼란 | 약간 — 안 쓰는 카테고리가 몇 개 생김 |
| 복구 | 쉬움 — `category remove` 로 지우거나 무시 |
| 재실행 | 안전 — 다시 import 하면 카테고리는 이미 있어 건너뜀 |

**즉 "고아 카테고리"는 무해한 잔여물**입니다. 완전한 원자성을 얻으려면 두 파일을 한 트랜잭션으로 묶어야 하는데, 그러려면 저널 파일이나 SQLite 가 필요합니다. **비용 대비 이득이 없다고 판단한 것**이고, 그 판단 근거를 말할 수 있는 것이 중요합니다.

**순서가 반대였다면 더 나빴을 것입니다.** 거래를 먼저 쓰고 카테고리를 나중에 쓰면, 중간에 죽었을 때 **등록되지 않은 카테고리를 참조하는 거래**가 남습니다. 그것은 참조 무결성 위반이라 실제 문제가 됩니다. **덜 해로운 쪽을 나중에** 두는 것이 지금 순서입니다.

---

## 4. 성능 분석 — 명령별 복잡도와 병목

### 4.1 명령별 시간/공간 복잡도

기호: **N** = 전체 거래 수, **k** = 필터 통과 수, **C** = 카테고리 수, **M** = import 대상 행 수, **B** = 예산 항목 수.

"읽기"는 파일을 처음부터 끝까지 훑는 횟수, "쓰기"는 파일에 손대는 방식입니다. **append(끝에 이어 쓰기)와 rewrite(전량 재작성)는 비용이 완전히 다르므로** 한 칸에 뭉뚱그리지 않았습니다.

| 명령 | 시간 | 추가 메모리 | 거래 파일 읽기/쓰기 | 그 밖의 파일 | 지배 요인 |
| --- | --- | --- | --- | --- | --- |
| `add` | O(N + C) | **O(N)** | 1 읽기 + append | 카테고리 **3+ 읽기**, `id_counter` | `next_id()` 의 전체 스캔 |
| `list` | O(N log N) | O(N) | 1 읽기 | — | 필터 없음 → 전량 정렬 |
| `search` | O(N + k log k) | O(k) | 1 읽기 | — | 스캔 + 통과분만 정렬 |
| `summary` | O(N + B + C log C) | O(C) | 1 읽기 | 예산 1 읽기 | 단일 패스 집계 + TOP 정렬 |
| `update` | O(N) | O(N) | **2 읽기** + rewrite | (`--category` 시 카테고리 1 읽기) | 아래 §4.3 |
| `delete` | O(N) | O(N) | **1 읽기** + rewrite | — | 전량 재작성 |
| `import` (부분) | O(N + C + M) | **O(N + M)** | 1 읽기 + append | 카테고리 2 읽기 + append | id 스캔 1 + 카테고리 2 |
| `import --atomic` | O(N + C + M) | O(N + M) | 2 읽기 + rewrite | 카테고리 2 읽기 + rewrite | 기존+신규 전량 재작성 |
| `category remove --replace-with` | O(N + C) | O(N) | **2 읽기** + rewrite | 카테고리 **3 읽기** + rewrite | 아래 §4.4 |
| `budget set` | O(B) | O(B) | — | 예산 1 읽기 + rewrite | 예산 파일 재작성 |
| `export` | O(N) | **O(1)** | 1 읽기 | — | 제너레이터 그대로 기록 |

**`add` 의 추가 메모리가 O(1) 이 아닌 것**이 표에서 가장 눈에 띄는 항목입니다. `next_id()` → `id_allocator()` → `id_state()` 가 **파일에 있는 모든 id 를 `set` 에 담아** 돌려주기 때문입니다(storage/repositories.py:53-63). 즉 거래 하나를 추가하는 데 시간도 O(N), 메모리도 O(N) 입니다. `IdAllocator` 가 "이미 쓰인 번호를 건너뛴다"를 보장하려면 그 집합이 필요하고, 그 대가입니다.

**`add` 의 "카테고리 3+ 읽기"도 표를 정직하게 쓴 결과입니다.** `cmd_add` 가 (1) 목록이 비었는지 보려고 `list_names()`, (2) 대화형 입력 검증에서 `exists()`(재입력할 때마다 한 번 더), (3) 서비스의 `_require_registered_category` 에서 `exists()` 를 각각 부릅니다. 카테고리 수 C 가 수십 개 규모라 문제가 되지 않을 뿐, **같은 질문을 세 번 묻는 구조**인 것은 맞습니다.

**`update`/`delete`/`rewrite` 계열의 메모리도 O(N)** 입니다. `plan_rewrite` 가 새 파일의 **모든 줄을 리스트로 만든 뒤** `stage_lines` 에 넘기기 때문입니다(storage/jsonl.py:286, 302). 스트리밍 재작성으로 바꾸면 O(1) 이 되지만, 그러면 "바뀐 것이 없으면 파일을 건드리지 않는다"(`RewritePlan.changed`)를 쓰기 전에 알 수 없습니다.

### 4.2 `export` 만 O(1) 메모리인 이유

budget_app/services/importexport.py:83-84

```python
        rows = (tx for tx in self.txs.stream() if flt.matches(tx))
        return csv_io.write_transactions(out_path, rows, include_id=include_id)
```

**제너레이터 식을 그대로 넘깁니다.** `csv_io.write_transactions` 가 `for tx in txs:` 로 하나씩 당겨 쓰므로, 100만 건을 내보내도 메모리는 한 건분입니다.

> **🔎 문법의 출처 — 제너레이터 식** — 대괄호가 아니라 **소괄호**라는 것이 전부입니다.
> `[...]` 는 리스트 컴프리헨션이라 즉시 전부 만들고, `(...)` 는 제너레이터 식이라
> **아무것도 만들지 않고 제너레이터 객체 하나만** 돌려줍니다(PEP 289, 파이썬 2.4).
> 파이썬은 이것을 익명 제너레이터 함수 하나로 컴파일합니다 — 바깥 `for` 의 대상만
> 즉시 평가되고 나머지는 `next()` 가 불릴 때마다 한 걸음씩 실행됩니다. 이 한 글자
> 차이가 §4.1 표에서 `export` 의 메모리를 O(N) 에서 O(1) 로 바꿉니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

반면 `list`/`search` 는 정렬 때문에 전부 모아야 합니다. **정렬은 본질적으로 전체를 봐야 하는 연산**이라 스트리밍이 불가능합니다.

budget_app/services/transactions.py:85-87

```python
        items = [tx for tx in self.txs.stream() if flt is None or flt.matches(tx)]
        items.sort(key=lambda t: (t.date, t.id), reverse=True)
        yield from items
```

**모으는 것은 필터를 통과한 것뿐입니다.** 그래서 `search` 의 메모리는 O(N) 이 아니라 O(k) 입니다. `list` 는 필터가 없어 k = N 이 되는 특수한 경우일 뿐입니다.

> **⚙️ 내부 동작 — `list.sort`** — CPython 의 리스트 정렬은 **Timsort** 입니다.
> 최악 O(n log n) 이지만 이미 정렬된 구간(run)을 찾아 병합하므로 **거의 정렬된
> 입력에서는 O(n) 에 가깝습니다** — 파일에 날짜순으로 쌓인 가계부 데이터가 정확히
> 그런 입력입니다. **안정 정렬**이라 키가 같은 원소의 원래 순서가 보존되고,
> `reverse=True` 도 이 안정성을 깨지 않습니다(뒤집는 것이 아니라 비교 방향만
> 바꿉니다). 병합에 최대 n/2 만큼의 임시 공간을 씁니다.
> `sorted(...)` 가 아니라 `items.sort(...)` 인 것은 이미 우리 것인 리스트를
> 제자리에서 정렬해 사본 하나를 아끼기 때문입니다.
> → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `key=lambda t: (t.date, t.id)`** — 정렬 키가 **튜플**이면 파이썬은
> 앞 원소부터 비교하다 같을 때만 다음으로 내려갑니다(사전식 비교). 즉 "날짜순,
> 같으면 id 순"이 한 줄로 표현됩니다. 그런데 `t.id` 는 `TransactionId` 값 객체라
> 비교 연산이 있어야 하고, 그래서 그 클래스에 `__lt__` + `@functools.total_ordering`
> 이 붙어 있습니다(domain/tx_id.py:51, 91-95). 없으면 **날짜가 겹치는 거래가 둘 이상
> 생기는 순간** `TypeError` 로 죽습니다 — 날짜가 전부 다르면 드러나지 않는 버그입니다.
> `key` 는 원소마다 **한 번만** 호출되고(decorate-sort-undecorate), 비교 함수를
> 넘기는 `cmp` 방식은 파이썬 3 에서 없어졌습니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

### 4.3 `update` 는 2번, `delete` 는 1번 훑습니다

**둘의 횟수가 다른 것이 설계의 흔적입니다.** 소스로 따라가 보면 이렇습니다.

```
update (services/transactions.py:52-70)
  1) self.txs.get(tx_id)          ← 현재 상태 조회 (없으면 AppError)
     · 도메인이 current.with_patch(patch) 로 새 객체를 만든다  (파일 접근 없음)
  2) self.txs.replace(tx_id, updated) → rewrite(_swap) → plan_rewrite → iter_raw
                                  ← 재작성 (읽으면서 쓸 줄을 만든다)

delete (services/transactions.py:72-77)
  1) self.txs.delete(tx_id) → rewrite(_drop) → plan_rewrite → iter_raw
                                  ← 읽기와 판정과 재작성이 한 번에
```

**`update` 만 한 번 더 읽는 이유는 "무엇으로 바꿀지"를 도메인이 정하기 때문입니다.** 부분 수정(`TransactionPatch`)을 적용하려면 **현재 값이 손에 있어야** 하고, 그것을 얻는 유일한 방법이 조회입니다. `delete` 는 바꿀 값이 없어 "만나면 버린다"로 끝나므로 한 번이면 됩니다.

**리팩터 전에는 `delete` 도 2번이었습니다.** `exists()` 로 확인한 뒤 재작성하며 또 훑었는데, 문제는 횟수가 아니라 **두 스캔의 판정 기준이 서로 달랐다**는 것입니다 — `exists()` 는 손상 줄에서 건져낸 id 까지 "있다"고 했지만, 재작성은 해석된 엔티티만 훑으므로 그 줄은 지울 수 없었습니다. "있다고 해 놓고 못 지운다"가 되는 것이죠. 지금은 **훑으면서 만나는 것이 곧 판정**이라 어긋날 수가 없습니다(storage/repositories.py:150-171 의 docstring 이 이 이야기입니다).

> **🔎 문법의 출처 — `nonlocal found`** — `_drop`/`_swap` 안의 `nonlocal` 은 PEP 3104
> 로 파이썬 3.0 에 들어왔습니다. 중첩 함수에서 **바깥 함수의 지역 변수**에 대입하기
> 위한 선언입니다(없으면 대입이 새 지역 변수를 만들어 바깥 `found` 는 영원히
> `False` 입니다). 파이썬 2 에서는 이것이 불가능해 리스트 한 칸(`found[0] = True`)에
> 담는 우회법을 썼습니다. 여기서 이 패턴이 필요한 이유는 `plan_rewrite` 가
> **변환 함수의 반환값만** 보고 "찾았는가"는 모르기 때문입니다 — 부수 효과로
> 바깥에 알립니다. → [12 §1-C](./12-syntax-and-stdlib.md)

**왜 이 구조를 받아들였나:**

| 관점 | 판단 |
|---|---|
| 정확성 | 도메인 변경(`with_patch`)이 도메인 계층으로 올라감 — 저장소가 판단하지 않음 |
| 일관성 | 한 번 훑는 동안 판정과 재작성이 같은 기준을 씀 |
| 비용 | `update` 만 파일을 1번 더 읽음 — N 이 작으면 무시할 수준 |

**개선안(현재 코드에 없음)**: `plan_rewrite` 의 변환 함수가 "현재 값"을 호출자에게 돌려주게 하면 `update` 도 1회가 됩니다. 다만 그러면 변환 함수가 조회까지 겸하게 되어 역할이 흐려집니다.

### 4.4 `category remove --replace-with` 가 가장 비쌉니다

budget_app/services/categories.py:61-73 (① ~ ⑤ 주석은 설명용으로 덧붙인 것이고, `raise` 인자는 줄였습니다)

```python
        target = validators.parse_category(name)
        replacement = validators.parse_category(replace_with) if replace_with else None

        if not self.cats.exists(target):            # ① 카테고리 읽기 O(C)
            raise AppError(...)
        reassigned = 0
        if self.txs.category_in_use(target):        # ② 거래 읽기 O(N)
            reassigned = self._reassign_before_remove(target, replacement)
            #   └ self.cats.exists(replace_with)    # ③ 카테고리 읽기 O(C)
            #   └ self.txs.reassign_category(...)
            #        └ rewrite(_reassign)           # ④ 거래 읽기 + 재작성 O(N)
        self.cats.remove(target)                    # ⑤ 카테고리 읽기 + 재작성 O(C)
        return reassigned
```

거래 파일을 **2번 읽고 1번 다시 쓰며**, 카테고리 파일을 **3번 읽고 1번 다시 씁니다.**

(`reassign_category` 자체는 `category_in_use` 를 다시 부르지 않습니다 — `rewrite(_reassign)` 한 번으로 훑으면서 세고 바꿉니다: storage/repositories.py:194-214.)

**하지만 이것은 최적화 대상이 아닙니다.** 카테고리 삭제는 (1) 드물게 실행되고, (2) 되돌리기 어려운 파괴적 연산이라 **방어를 겹치는 편이 낫습니다.** "느리지만 확실한" 쪽을 택한 의도적 선택입니다.

### 4.5 `add` 가 O(1) 이 아닌 것

budget_app/storage/repositories.py:79-81

```python
    def next_id(self) -> TransactionId:
        """단건 추가용 — 발급기를 한 번 쓰고 버린다."""
        return self.id_allocator().next()
```

`id_allocator()` 가 `id_state()` 를 부르고, 그것이 파일 전체를 훑습니다. append 자체는 O(1) 이지만 **ID 발급이 O(N)** 입니다.

100만 건 파일에서는 "거래 하나 추가"에도 100만 줄 스캔이 선행되고, 그 줄들의 id 가 전부 `set` 에 담깁니다.

**메타 파일은 이미 있습니다 — 다만 캐시로 쓰지 않습니다.** `data/id_counter` 에 "발급한 적 있는 최대 번호"를 숫자 한 줄로 남기는 `IdWatermark` 가 그것입니다(storage/ids.py:26-78).

budget_app/storage/repositories.py:76-77

```python
        max_n, taken = self.id_state()
        return IdAllocator(start=max(max_n, self._watermark.read()), taken=taken)
```

`max(...)` 인 것이 핵심입니다. 워터마크는 **기준선(floor)** 이지 정답이 아닙니다.

| | 파일 스캔 최대값 | 워터마크 |
|---|---|---|
| 아는 것 | 지금 무엇이 있는가 | 무엇을 발급한 적이 있는가 |
| 삭제하면 | **줄어든다**(지운 번호가 부활) | 줄어들지 않는다 |
| 손으로 편집/복사하면 | 따라간다 | **모른다** |

**한쪽만 믿으면 각각 다른 버그가 납니다.** 워터마크만 믿으면 다른 폴더에서 복사해 온 파일의 id 와 충돌하고, 스캔만 믿으면 지운 번호가 부활해 "예전에 내보낸 CSV 를 다시 가져오면 조용히 버려지는" 일이 생깁니다(그 시나리오가 storage/ids.py:29-45 에 적혀 있습니다).

**개선안(현재 코드에 없음)**: 워터마크를 기준선이 아니라 **권위 있는 캐시**로 승격시켜 파일 스캔을 아예 건너뛰면 `add` 가 O(1) 이 됩니다. 그러려면 `taken` 집합 없이도 충돌하지 않는다는 보장이 필요한데, 그것은 "이 파일을 이 프로그램만 만졌다"를 전제해야 성립합니다. 지금은 **손으로 편집한 파일도 정상 동작해야 한다**를 더 중요하게 봤습니다.

### 4.6 배치 작업의 최적화 — 실제로 한 것

리팩터에서 **가져오기의 파일 재스캔은 실제로 제거했습니다.**

| 연산 | 리팩터 전 | 리팩터 후 |
|---|---|---|
| 행마다 카테고리 확인 | `cats.exists()` × M회 스캔 | `name_set()` 1회 스캔 |
| 커밋 시 카테고리 등록 | `cats.add()` × K회 스캔 | `add_many()` 1회 스캔 |
| ID 발급 | `max_id_num()` 1회 + 메모리 카운터 | `id_allocator()` 1회 + `IdAllocator` |

M=1000 행에 새 카테고리 K=10개인 CSV 를 가져올 때:

```
리팩터 전: 카테고리 파일을 1000 + 10 = 1010회 스캔
리팩터 후: 카테고리 파일을 1 + 1 = 2회 스캔
```

**ID 발급은 이전에도 최적화돼 있었지만 방식이 문제였습니다.** 서비스가 `config.TX_ID_FORMAT` 을 직접 쓰며 저장소를 흉내 냈기 때문에, 계층 경계를 넘으면서 얻은 성능이었습니다. `IdAllocator` 객체로 바꾸면서 **성능은 유지하고 경계는 복구**했습니다.

### 4.7 10만 건에서 무엇이 먼저 무너지는가

| 순위 | 병목 | 증상 | 개선 방향 |
|---|---|---|---|
| 1 | `list` 전량 정렬 | 메모리 O(N), 정렬 O(N log N) | 파일을 날짜 역순으로 유지하거나 인덱스 |
| 2 | `add` 의 ID 스캔 | 1건 추가에 전체 읽기 | 메타 파일 캐시 |
| 3 | `update`/`delete` 재작성 | 1건 수정에 전체 재작성 | 삭제 마커(tombstone) + 주기적 압축 |
| 4 | `search` 전체 스캔 | 조건과 무관하게 O(N) | 날짜/카테고리 인덱스 |

**공통 개선 방향은 "인덱스"** 이고, 그것을 제대로 하려면 **SQLite** 가 답입니다(§5.3).

---

## 5. 저장 포맷 트레이드오프

### 5.1 비교표

| 항목 | JSONL (채택) | CSV | 단일 JSON | SQLite |
| --- | --- | --- | --- | --- |
| 타입 보존 | ✅ int/list 그대로 | ❌ 전부 문자열 | ✅ | ✅ |
| 중첩 구조 | ✅ `tags` 리스트 | ❌ 인코딩 필요 | ✅ | ❌ 정규화 필요 |
| append 비용 | ✅ O(1) | ✅ O(1) | ❌ 전체 재작성 | ✅ |
| 스트리밍 읽기 | ✅ 한 줄씩 | ✅ | ❌ 전체 파싱 | ✅ 커서 |
| 손상 격리 | ✅ 한 줄만 | ✅ | ❌ 전체 파괴 | ✅ |
| 사람이 읽기 | ✅ | ✅ 가장 쉬움 | 🔺 | ❌ 바이너리 |
| 인덱스/질의 | ❌ 전체 스캔 | ❌ | ❌ | ✅ SQL |
| 트랜잭션 | ❌ 직접 구현 | ❌ | ❌ | ✅ ACID |
| 동시성 | ❌ 잠금 없음 | ❌ | ❌ | ✅ 파일 잠금 |

### 5.2 왜 JSONL 인가

> **🔎 출처 — JSONL 은 표준이 아닙니다** — JSON 자체는 RFC 8259 로 표준화돼
> 있지만, **JSON Lines(JSONL / NDJSON)** 는 RFC 도 W3C 권고도 아닌 **관행**입니다.
> 규칙은 한 줄에 하나의 JSON 값, 구분자는 `\n`, 파일 전체는 유효한 JSON 이 **아님**
> — 그게 전부입니다. 그래서 파이썬 표준 라이브러리에도 `jsonl` 모듈은 없고,
> 이 프로젝트는 `json.dumps` 한 줄 + `"\n"` 으로 **직접 구현**합니다
> (storage/jsonl.py:207-208, 69). 규격이 없다는 것이 오히려 요점입니다 —
> 구현할 것이 거의 없습니다.

**"한 줄 = 한 레코드"가 두 가지를 동시에 사 줍니다.**

- **append 가 O(1)**: 파일 끝에 줄 하나를 붙이면 끝입니다. 단일 JSON 배열이면
  닫는 `]` 를 지우고 다시 써야 하므로 전체 재작성입니다.
- **손상이 한 줄에 갇힘**: 파서를 줄 단위로 돌릴 수 있으므로, 깨진 줄에서 난 예외가
  그 줄에서 끝납니다. 이 프로젝트의 `_parse_line`(storage/jsonl.py:181-191)이
  예외를 밖으로 던지지 않고 `RawLine` 으로 **돌려주는** 것이 그 구조를 그대로
  이용한 것입니다.

**손상 격리가 결정적입니다.** 단일 JSON 파일이면 한 글자만 깨져도 `json.load` 가 실패해 **전체 데이터를 못 읽습니다.** JSONL 은 한 줄이 깨져도 나머지가 살아 있고, 리팩터 후에는 그 줄이 **파일에 그대로 보존**되기까지 합니다.

**append 가 O(1)** 인 것도 큽니다. 가계부의 가장 흔한 연산이 "거래 하나 추가"인데, 단일 JSON 이면 매번 전체를 다시 써야 합니다.

**타입 보존**은 CSV 대비 이점입니다. `tags` 가 리스트로, `amount` 가 정수로 저장되므로 읽을 때마다 파싱할 필요가 없습니다.

**그래서 CSV 는 저장 포맷이 아니라 교환 포맷으로만 씁니다.** `export`/`import` 가 CSV 를 쓰는 것은 엑셀·타 가계부와 주고받기 위해서이고, 그 경계에서 `csv_io.parse_row` 가 모든 값을 `validators` 로 다시 세웁니다(storage/csv_io.py:107-123).

> **🔎 출처 — RFC 4180 과 파이썬 `csv` 모듈** — CSV 는 표준이 **나중에** 생긴
> 포맷입니다. 수십 년간 쓰이던 관행을 2005년 RFC 4180 이 뒤늦게 기술한 것이라,
> "RFC 4180 을 지키지 않는 CSV"가 세상에 널려 있습니다. 그래서 파이썬 `csv` 모듈은
> RFC 를 **강제하지 않고** *dialect* 라는 개념으로 갈라 둡니다 — 기본값은 엑셀의
> 동작을 흉내 낸 `excel` dialect 입니다. 이 프로젝트는 dialect 를 지정하지 않으므로
> `excel` 을 씁니다. → [12 §2-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `newline=""` 이 필수인 이유** — CSV 를 여는 `open()` 은 전부
> `newline=""` 입니다(storage/csv_io.py:82, 142). `csv` 모듈은 **줄바꿈을 스스로
> 처리합니다** — 필드 안에 개행이 든 따옴표 인용 값(`"메모\n두 줄"`)을 한 레코드로
> 읽어야 하기 때문입니다. `newline` 을 주지 않으면 `TextIOWrapper` 의 범용 개행
> 변환이 먼저 끼어들어, 쓸 때는 Windows 에서 `\r\r\n` 이 되고 읽을 때는 인용된
> 개행이 잘립니다. `newline=""` 은 "변환하지 말고 그대로 달라"는 뜻이고, 이것이
> `csv` 모듈 문서가 요구하는 사용법입니다. (JSONL 쪽이 `newline="\n"` 인 것과
> 대비됩니다 — 그쪽은 우리가 개행을 소유합니다.)
> → [12 §2-A](./12-syntax-and-stdlib.md)

### 5.3 `sqlite3` 도 표준 라이브러리인데 왜 안 썼나

**과제 제약**이 "파일 기반"이었을 가능성이 높지만, 설계 관점에서도 근거를 댈 수 있습니다.

**JSONL 이 나은 점:**
- 데이터 파일을 텍스트 에디터로 열어 확인·수정할 수 있음 (학습·디버깅에 유리)
- 손상 시 사람이 고칠 수 있음
- 스키마 마이그레이션이 필요 없음
- `git diff` 로 변경 내역이 읽힘

**SQLite 가 나은 점:**
- 인덱스 → `search`/`summary` 가 O(log N)
- 진짜 트랜잭션 → §3.4 의 "고아 카테고리" 문제가 사라짐
- 파일 잠금 → 동시 실행 안전 (§6)
- `UNIQUE` 제약 → ID 중복이 **원리적으로** 불가능

**전환 기준을 말할 수 있어야 합니다.** 거래가 10만 건을 넘거나, 여러 프로세스가 동시에 접근하거나, 복합 조건 검색이 잦아지면 SQLite 가 맞습니다. 지금은 개인용·단일 프로세스·수천 건 규모라 JSONL 의 단순함이 이깁니다.

**전환 비용이 낮다는 것도 설계의 성과입니다.** 서비스 계층에 `open()` 이 한 곳도 없으므로, `storage/` 패키지(`jsonl.py` + `repositories.py` + `csv_io.py`)를 SQLite 버전으로 갈아 끼우면 `services/` 이상은 그대로입니다. 확인 방법은 간단합니다 — `grep -rn "open(" budget_app/services/*.py` 를 돌리면 걸리는 것이 `services/__init__.py:4` 의 **docstring 한 줄**("`open()` 이 하나도 없다")뿐입니다. 실행되는 코드에는 0건입니다.

---

## 6. 동시성의 한계 — 잠금이 없는 세계

**이 프로그램에는 파일 잠금이 없습니다.** 두 프로세스가 동시에 실행되면 문제가 생깁니다.

### 6.1 ID 중복 발급 시나리오

```
시각  프로세스 A                          프로세스 B
──────────────────────────────────────────────────────────────
t1    id_allocator() → start=5, taken={…TX-000005}
t2                                        id_allocator() → start=5, taken={…}
t3    next() → TX-000006
t4                                        next() → TX-000006    ← 같은 번호!
t5    append(TX-000006)   워터마크 6
t6                                        append(TX-000006)     ← 중복 저장
```

**`IdAllocator` 는 프로세스 안에서만 유일성을 보장합니다.** 두 프로세스가 각자 파일을 읽어 각자 발급하면 겹칩니다.

**워터마크 파일도 이것을 막지 못합니다.** `IdWatermark.remember` 자체가 "읽고(`read`) 비교하고 쓰는"(`atomic_write_lines`) read-modify-write 이기 때문입니다(storage/ids.py:77-78). t1·t2 에 둘 다 5 를 읽었으면 둘 다 6 을 씁니다 — §6.2 의 lost update 와 **정확히 같은 구조**입니다. 워터마크가 푸는 문제는 "삭제로 번호가 되돌아가는 것"이지 "동시 실행"이 아닙니다.

리팩터가 고친 것은 **단일 프로세스 안에서의 재발급**(손상 줄 때문에 번호를 못 봐서 생긴 문제 + 삭제로 인한 번호 부활)이고, 프로세스 간 경합은 여전히 남아 있습니다.

### 6.2 lost update 시나리오

```
시각  프로세스 A (delete TX-1)          프로세스 B (add 새 거래)
────────────────────────────────────────────────────────────
t1    iter_raw() 로 전체 읽음
t2                                      append(TX-100)  → 파일에 기록됨
t3    tmp 에 (TX-1 제외한) 내용 기록
t4    os.replace(tmp, path)             ← B 가 추가한 TX-100 이 사라짐!
```

**A 가 읽은 시점의 스냅숏으로 파일을 덮어쓰므로**, 그 사이 B 가 추가한 것이 유실됩니다. 이것을 **lost update** 라고 합니다.

**원자적인 것은 마지막 한 걸음뿐입니다.** 모든 쓰기 명령은 사실 세 걸음짜리 **read-modify-write** 입니다.

```
read    iter_raw() 로 전체를 읽는다        ← 여기서 본 것이 A 의 세계관
modify  plan_rewrite 가 새 줄 목록을 만든다  ← 메모리
write   stage_lines + os.replace          ← 이 마지막 한 걸음만 원자적
```

`os.replace` 가 보장하는 것은 **write 한 걸음**이 쪼개지지 않는다는 것뿐입니다. read 와 write 사이의 틈은 그대로 열려 있고, 그 사이에 다른 프로세스가 무엇을 했든 A 는 **자기가 읽은 스냅숏으로 통째로 덮어씁니다.** 그래서 B 의 변경이 흔적 없이 사라집니다.

**원자성(atomicity)과 격리성(isolation)은 다른 보장입니다.** DB 의 ACID 에서 A 와 I 가 따로 있는 이유가 이것입니다. 이 프로그램은 A 를 (파일 하나에 대해) 갖고 있고 I 는 전혀 갖고 있지 않습니다. "`os.replace` 를 쓰니까 동시 실행도 안전합니다"는 **틀린 문장**이고, 방어 질문에서 이 구분을 못 하면 원자성을 이해했다고 보기 어렵습니다.

### 6.3 임시 파일 이름 충돌

한 가지가 더 있습니다. tmp 경로가 `transactions.jsonl.tmp` 로 **고정**이므로(§1.3), 같은 파일을 동시에 재작성하는 두 프로세스는 **같은 임시 파일에 함께 씁니다.**

```
t1    A: stage_lines → transactions.jsonl.tmp 에 쓰기 시작
t2    B: stage_lines → 같은 이름을 "w" 로 열어 잘라 버림(truncate)
t3    A: fsync 후 os.replace(tmp, path)   ← B 가 쓰던 내용을 커밋할 수도
```

찌꺼기가 무한히 쌓이지 않게 하려고 고른 고정 이름이 동시성에서는 약점이 됩니다. 이것도 잠금이 있으면 사라지는 문제입니다.

### 6.4 개선 방향 (전부 현재 코드에 없음)

**(1) 파일 잠금**

```python
# POSIX
import fcntl
with open(lock_path, "w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    ...  # 임계 구역

# Windows 는 msvcrt.locking() — 이식성이 없어 분기 필요
```

> **⚙️ 내부 동작** — `fcntl` 모듈은 **Windows 에 아예 없습니다**(`import fcntl` 이
> `ModuleNotFoundError`). 표준 라이브러리이면서 플랫폼 전용인 모듈이고, `msvcrt`
> 는 반대로 Windows 전용입니다. 즉 이 방향을 택하면 `sys.platform` 분기가 코드에
> 들어옵니다. 게다가 `flock` 은 **권고적(advisory)** 잠금이라 — 잠그지 않고 그냥
> 여는 프로그램은 아무 방해 없이 파일을 씁니다. 텍스트 에디터가 그 예입니다.
> → [12 §3](./12-syntax-and-stdlib.md)

**(2) 잠금 디렉터리 (이식 가능)**

```python
# mkdir 은 대부분의 파일시스템에서 원자적
try:
    os.mkdir(lock_dir)          # 이미 있으면 FileExistsError
except FileExistsError:
    raise AppError("다른 프로세스가 실행 중입니다")
try:
    ...
finally:
    os.rmdir(lock_dir)
```

> **⚙️ 내부 동작** — `mkdir(2)` 은 "만들거나 `EEXIST` 로 실패하거나" 둘 중 하나라
> **검사와 생성이 한 시스템 콜 안에서 끝납니다**. `if not exists: mkdir` 로 쓰면 두
> 호출 사이에 다른 프로세스가 끼어드는 TOCTOU(time-of-check to time-of-use) 창이
> 생기지만, `os.mkdir` + `except FileExistsError` 는 그 창이 없습니다. 같은 원리가
> 이 소스에도 이미 쓰이고 있습니다 — `backup.py:30` 의
> `dest.mkdir(parents=True, exist_ok=False)` 가 기존 백업 폴더 덮어쓰기를 막는
> 방식이 정확히 이것입니다. → [12 §3](./12-syntax-and-stdlib.md)

**(3) SQLite 로 전환** — 잠금을 직접 구현하지 않고 얻습니다.

**과제 방어에서는 "동시 실행을 가정하지 않은 단일 사용자 CLI"라는 전제를 명시**하고, 위 세 방향을 제시할 수 있으면 충분합니다.

---

## 7. 방어적 프로그래밍 인덱스

이 코드가 방어하고 있는 것들을 한곳에 모읍니다.

| # | 방어 대상 | 구현 | 위치 |
|---|---|---|---|
| 1 | 잘못된 필드 값 | 생성자 불변식 (`__post_init__`) | domain/entities.py:68-80 |
| 2 | 손상된 JSONL 줄 (읽기) | `_parse_line` 이 예외 대신 `RawLine` 반환 | storage/jsonl.py:181-191 |
| 3 | 손상된 JSONL 줄 (쓰기) | `plan_rewrite` 가 원문 보존 | storage/jsonl.py:289-292 |
| 4 | 쓰기 중 crash | 임시 파일 + fsync + `os.replace` | storage/jsonl.py:48-87 |
| 5 | ID 재발급 | `iter_raw` 기반 스캔 + `taken` 집합 + 워터마크 | storage/repositories.py:39-77, storage/ids.py:26-116 |
| 6 | 왕복 중복 | CSV `id` 컬럼 + 중복 정책 | storage/csv_io.py:131-148 + services/importexport.py:133-164 |
| 7 | 대화형 EOF 무한 대기 | `InputAborted` | cli/prompts.py:28-37, 52-57 |
| 8 | 잘못된 입력 무한 루프 | `for _ in range(MAX_INPUT_RETRIES)` | cli/prompts.py:66 |
| 9 | 참조 무결성 (카테고리) | 사용 중 삭제 차단 + 재지정 | services/categories.py:38-89 |
| 10 | 파이프 끊김 | `raise` → `_silence_broken_pipe` | cli/error_handler.py:57-60 + cli/app.py:50-58, 91-94 |
| 11 | Ctrl+C | `except KeyboardInterrupt` → 130 | cli/error_handler.py:61-63 (`EXIT_INTERRUPT`, cli/config.py:29) |
| 12 | 스택트레이스 노출 | `except Exception` + `logger.exception`(= `exc_info=True`) | cli/error_handler.py:106-119 |
| 13 | 인코딩 불일치 | 모든 `open` 에 `encoding` 명시 | 전역 (값은 storage/config.py:22, 39-40) |
| 14 | CRLF 오염 | JSONL 은 `newline="\n"`, CSV 는 `newline=""` | storage/jsonl.py:66, 239 / storage/csv_io.py:82, 142 |
| 15 | 음수 `--top` | `max(0, top_n)` | services/budgets.py:57 |
| 16 | 환경변수 `=0` 오독 | `FALSY_ENV_VALUES` 집합 | cli/config.py:19 |
| 17 | falsy 반환값 오독 | `EXIT_OK if result is None else result` | cli/error_handler.py:54 |
| 18 | 백업 폴더 덮어쓰기 | `mkdir(exist_ok=False)` | storage/backup.py:30 |
| 19 | 검색 조건 정규화 누락 | 각 명세 생성자가 `validators` 를 호출 | domain/specs.py:176, 189, 200, 211 |
| 20 | 부분 수정 필드명 오타 | `TransactionPatch` dataclass | domain/entities.py:127-154 |
| 21 | 바뀐 것 없는데 재작성 | `RewritePlan.changed` 선판정 후 건너뜀 | storage/jsonl.py:264-311, 325-327 |
| 22 | 빈 CSV 오진단 | 헤더 없음과 컬럼 누락 구분 | storage/csv_io.py:90-104 |
| 23 | 찢어진 꼬리에 이어 쓰기 | 마지막 바이트를 `rb`+`seek` 로 확인 후 개행 보충 | storage/jsonl.py:249-262 |
| 24 | 다중 파일 부분 커밋 은폐 | 어디까지 반영됐는지 로그 + 예외 재전파 | storage/unit_of_work.py:145-156 |
| 25 | 백업에서 `id_counter` 누락 | glob 밖의 데이터 파일을 명시 목록으로 | storage/backup.py:36-47 |

**5·6·19·20·21·22·23·24·25 번은 리팩터에서 추가된 방어**입니다.

> **⚙️ 내부 동작 — 23번의 `f.seek(-1, os.SEEK_END)`** — 마지막 바이트가 개행인지
> 보려고 파일을 통째로 읽지 않습니다. `os.SEEK_END`(값 2)를 기준으로 **음수 오프셋**을
> 주면 끝에서 1바이트 앞으로 가고, 거기서 1바이트만 읽습니다. 이 음수 seek 는
> **바이너리 모드에서만 됩니다** — 텍스트 모드(`TextIOWrapper`)는 인코딩 때문에
> "문자 개수"와 "바이트 위치"가 일치하지 않아
> `io.UnsupportedOperation: can't do nonzero end-relative seeks` 로 거부합니다
> (직접 실행해 확인할 수 있습니다). 그래서 이 코드만 `open(self.path, "rb")` 입니다. 인코딩이 깨진 파일에서도
> 안전하다는 것이 덤입니다. → [12 §3](./12-syntax-and-stdlib.md)

---

## 8. 확장 아이디어 (전부 개선안 — 현재 코드에 없음)

| 아이디어 | 필요한 변경 | 계층 |
|---|---|---|
| 반복 거래(구독료 자동 등록) | 새 서비스 + 저장소 | services/ + storage/ |
| 다중 통화 | `Transaction.currency` 필드 + 환율 | domain/ + services/ |
| 예산 초과 알림 | `add` 후 요약 확인 | services/ |
| JSON 출력(`--json`) | 프레젠터를 하나 더 | cli/presenter.py |
| 웹 UI | CLI 계층만 교체 | **services 이하 무변경** |
| SQLite 전환 | 저장소 교체 | **services 이상 무변경** |
| 정렬 옵션(`--sort`) | `stream_sorted` 에 키 인자 | services/transactions.py |
| 태그 AND/OR 검색 | `HasTag` 를 `&` / `\|` 로 조합 | domain/specs.py (**새 클래스 불필요**) |

**"어느 계층만 바꾸면 되는가"를 말할 수 있는 것**이 계층 설계의 실질적 이득입니다. 웹 UI 는 CLI 계층만, SQLite 는 저장소 계층만 바꿉니다.

**마지막 줄은 "코드를 아예 안 고쳐도 되는" 경우입니다.** `Spec` 이 `__and__`/`__or__`/`__invert__` 를 정의해 두었으므로(domain/specs.py:84-91), `HasTag("a") | HasTag("b")` 가 이미 동작합니다. 남은 일은 CLI 가 그 조합을 만들도록 인자를 받는 것뿐입니다.

> **🔎 문법의 출처 — 연산자 오버로딩** — `a & b` 는 파이썬이 `type(a).__and__(a, b)`
> 로 바꿔 실행합니다. `NotImplemented` 가 돌아오면 반대쪽의 `__rand__` 를 시도하고,
> 그것도 없으면 `TypeError` 를 냅니다. `&`/`|`/`~` 를 고른 것은 파이썬의
> `and`/`or`/`not` 이 **오버로딩 불가능**하기 때문입니다 — 그 셋은 메서드 호출이
> 아니라 단축 평가(short-circuit)를 하는 **문법 구조**라 바꿔 낄 자리가 없습니다.
> 같은 이유로 NumPy·Django ORM·SQLAlchemy 도 전부 `&`/`|` 를 씁니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

---

## 9. 정리 — 방어 질문 대비 핵심 문장

**"데이터가 깨지면 어떻게 되나요?"**
> 읽기 경로가 둘입니다. 조회는 손상 줄을 건너뛰고 경고를 남기되 파일은 손대지 않고, 재작성은 손상 줄을 원문 그대로 보존합니다. 리팩터 전에는 이 둘이 하나여서 무관한 삭제가 손상 줄을 함께 지웠습니다.

**"쓰는 도중에 죽으면요?"**
> 임시 파일에 전부 쓰고 `flush`+`fsync` 로 디스크에 내린 뒤 `os.replace` 로 이름을 바꿉니다. `os.replace` 는 POSIX 의 `rename(2)`, Windows 의 `MoveFileExW(MOVEFILE_REPLACE_EXISTING)` 로 내려가고, 같은 파일시스템 안에서 원자적이라 "이전" 아니면 "이후"만 존재합니다. 경계는 두 군데입니다 — 디렉터리 엔트리는 fsync 하지 않아 아주 짧은 창이 남고(개인용 CLI 규모에서 의도적으로 생략), Windows 에서는 대상 파일이 열려 있으면 `os.replace` 가 `PermissionError` 로 **그냥 실패**합니다. 후자는 `UnitOfWork.commit` 이 어디까지 반영됐는지 로그로 남기고 예외를 그대로 올립니다.

**"거래가 10만 건이면요?"**
> `list` 의 전량 정렬이 먼저 무너집니다(메모리 O(N)). 그다음이 `add` 의 ID 스캔 — 시간뿐 아니라 **메모리도 O(N)** 입니다. 파일의 모든 id 를 `taken` 집합에 담아야 재발급을 막을 수 있기 때문입니다. 그다음이 `update`/`delete` 의 전량 재작성입니다. 공통 해법은 인덱스이고, 제대로 하려면 SQLite 가 맞습니다. 서비스 계층에 `open()` 이 없으므로 저장소만 교체하면 됩니다.

**"import 에 깨진 행이 섞이면요?"**
> 두 축으로 답합니다. 잘못된 데이터는 `--atomic` 여부로, 이미 저장된 거래는 `--on-duplicate` 로 정합니다. 두 숫자(`skipped`/`duplicated`)를 나눠 보고하는 이유는 사용자가 해야 할 일이 정반대이기 때문입니다. 원자 모드에서는 준비 단계가 끝나기 전에 파일을 건드리지 않으므로 카테고리 자동 등록까지 함께 롤백됩니다.

**"동시에 두 번 실행하면요?"**
> 안전하지 않습니다. ID 중복 발급과 lost update 가 가능합니다. 단일 사용자 CLI 를 전제한 설계이며, 필요하면 잠금 디렉터리(`mkdir` 의 원자성 이용)나 SQLite 로 해결할 수 있습니다. `os.replace` 의 원자성은 격리성을 보장하지 않는다는 점을 구분해서 말하는 것이 중요합니다.

**"이 설계의 가장 큰 약점은?"**
> 인덱스가 없다는 것입니다. 모든 조회가 O(N) 전체 스캔이라 데이터가 커지면 선형으로 느려집니다. 두 번째는 프로세스 간 격리가 없다는 것입니다. 둘 다 SQLite 로 해결되지만, 지금 규모에서는 "텍스트로 읽고 고칠 수 있다"는 JSONL 의 이점이 더 큽니다.

---

**다음 문서**: [11. 설계 FAQ & 용어집](./11-faq-and-glossary.md)
