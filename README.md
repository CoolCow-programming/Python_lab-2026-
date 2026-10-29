# Python_lab-2026-

Лабораторная работа 1 (Этап А)

Разработана система онлайн-школы, которая принимает сдачи лабораторных в формате JSON и валидирует на корректность данных.

---

## Реализованный функционал (Этап А)

- **Приём и валидация:** строгая проверка JSON, обязательных полей, временной зоны (ISO-8601) и AI-декларации.
- **Безопасность данных:** входные данные не изменяются в процессе обработки (используются `frozen` dataclasses и `deepcopy` в источниках).
- **Строгий парсинг JSON:** запрещены повторяющиеся ключи, значения `NaN` и `Infinity`.
- **Идемпотентность и конфликты:**
  - повторная отправка того же `submission_id` с тем же хешем возвращает статус `duplicate` и не увеличивает количество сдач;
  - отправка того же `submission_id` с другим содержимым вызывает ошибку `conflict` и не перезаписывает исходную запись.
- **Обработка ошибок:** ошибки содержат `code`, `field` и `message`. Битые JSON-строки не останавливают импорт всего файла, а попадают в отчёт с указанием номера строки (`line_no`).
- **Архитектура (Backend):**
  - разделение на доменный слой (чистый Python) и слой адаптеров;
  - использование **Pydantic** для валидации входных DTO и явное преобразование в доменную модель;
  - HTTP-статусы и ORM не проникают в доменный слой (независимость исключений);
  - хранение в памяти (in-memory repository).

---

## Входные данные

Один JSONL-объект — одна версия сдачи. Поля:

| Поле | Тип | Условие корректности |
|------|-----|----------------------|
| `schema_version` | `int` | ровно `1`; `bool` не допускается |
| `submission_id` | `str` | непустое после `strip()` |
| `student_id` | `str` | непустое после `strip()` |
| `assigment_id` | `str` | непустое после `strip()` |
| `submitted_at` | `str` | ISO 8601 **с таймзоной**; naive-дата отклоняется |
| `text` | `str` | непустой после `strip()` |
| `code` | `str` | непустой после `strip()` |
| `template_id` | `str \| None` | если строка — непустая |
| `ai_declaration` | объект | строгий набор полей (см. ниже) |

### Декларация `ai_declaration`

| Поле | Тип | Условие |
|------|-----|---------|
| `used` | `bool` | строго `bool` |
| `tool` | `str \| None` | при `used=true` обязателен и непустой |
| `purpose` | `str \| None` | при `used=true` обязателен и непустой |
| `verified_by_student` | `bool` | строго `bool` |

Неизвестные поля на верхнем уровне и внутри `ai_declaration` отклоняются. Отсутствующие обязательные поля также дают ошибку схемы.

### Категории ошибок

| `code` | Когда |
|--------|-------|
| `invalid_json` | разбор JSON невозможен; повтор ключа; `NaN` / `Infinity` |
| `schema_error` | нарушение схемы: тип, пустота, отсутствующее или лишнее поле, невалидная дата, неполная декларация |
| `conflict` | тот же `submission_id`, другое содержимое |

`field` — машиночитаемое имя поля (`"student_id"`, `"submitted_at"`, `"ai_declaration.tool"` и т. п.), `message` — человекочитаемое пояснение.

При ошибке входной объект не изменяется.

---

## Структура проекта

Проект использует `src-layout` и разделён на слои:

```text
src/online_school/
├── domain/                   # Ядро (не зависит от Pydantic, HTTP, файлов)
│   ├── models.py             # Неизменяемые модели данных (Submission, AIDeclaration)
│   ├── validation.py         # Бизнес-валидация (бросает SubmissionError)
│   ├── errors.py             # Коды и классы ошибок
│   ├── service.py            # Логика приёма (accepted/duplicate/conflict)
│   └── hashing.py            # Стабильные отпечатки (SHA-256)
├── adapters/                 # Внешние детали
│   ├── parser.py             # Строгий разбор JSON
│   ├── repository.py         # In-memory хранилище
│   └── sources.py            # Источники (JSONL и InMemory) через Protocol
├── schemas/                  # Слой Pydantic (только для Backend)
│   └── submission_in.py      # Входные DTO и преобразование в Domain
├── app/
│   └── build.py              # Явная сборка зависимостей (Dependency Injection)
└── cli.py                    # Интерфейс командной строки
```

---

## Установка и запуск

1. Клонируйте репозиторий и перейдите в папку проекта:

   ```bash
   cd Python_lab-2026-
   ```

2. Создайте и активируйте виртуальное окружение:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Установите проект в editable-режиме (вместе с зависимостями):

   ```bash
   pip install -e .
   ```

---

## Использование (CLI)

Для импорта сдач используется команда `import`. На вход подаётся путь к файлу формата `.jsonl` (один JSON-объект на строку).

```bash
python -m online_school.cli import "Путь до jsonl файла"
```

Формат вывода (JSON в stdout):

```json
{
  "accepted": ["sub-001", "sub-002"],
  "duplicate": ["sub-003"],
  "errors": [
    {
      "line_no": 4,
      "code": "invalid_json",
      "field": "json",
      "message": "Ошибка JSON около столбца 2"
    },
    {
      "line_no": 5,
      "code": "conflict",
      "field": "submission_id",
      "message": "Для новой версии требуется новый ID"
    }
  ]
}
```

### Коды завершения процесса (exit codes)

| Код | Значение |
|-----|----------|
| `0` | все записи обработаны без ошибок |
| `1` | импорт завершён, но в некоторых строках есть ошибки (валидация, конфликты) |
| `2` | файл не найден или недоступен для чтения |

---

## Тестирование

### Запуск

```bash
pytest -v
```

### Файлы тестов

- `tests/conftest.py` — фикстуры: `valid_raw_data`, `bad_student_id`, `bad_timestamp`, `unknown_field`. Каждая проблемная фикстура строит `deepcopy` базового объекта и меняет одно поле, поэтому тесты не влияют друг на друга.
- `tests/test_domain.py` — unit-тесты валидации, парсинга JSON, сервиса приёма и strict-режима DTO.
- `tests/test_cli.py` — интеграционный тест CLI на смешанном JSONL-файле.

### Покрытые сценарии

#### Валидация схемы (`test_domain.py`)

| Тест | Вход | Ожидание |
|------|------|----------|
| `test_valid_submission` | `valid_raw_data` | `parse_submission` возвращает модель; `submission_id == "sub-001"`, `text == "Текст"` |
| `test_empty_studetn_id` | `bad_student_id` (`student_id = " "`) | `SubmissionError`, `code = schema_error`, `field = student_id` |
| `test_invalid_timestamp` | `bad_timestamp` (`submitted_at` без таймзоны) | `SubmissionError`, `code = schema_error`, `field = submitted_at` |
| `test_unknown_field` | `unknown_field` (добавлен ключ `"unknown": "typo"`) | `SubmissionError`, `code = schema_error`, `field = unknown` |

#### Строгий разбор JSON (`test_domain.py`)

| Тест | Вход | Ожидание |
|------|------|----------|
| `test_broken_json` | `decode_json('{"broken": ')` | `SubmissionError`, `code = invalid_json` |
| `test_repeated_keys` | `decode_json('{"id": "1", "id": "2"}')` | `SubmissionError`, `code = invalid_json` (срабатывает `object_pairs_hook`) |

#### Неизменность входа (`test_domain.py`)

| Тест | Вход | Ожидание |
|------|------|----------|
| `test_input_immutability` | `valid_raw_data` | `parse_submission` не изменяет входной `dict`: `deepcopy` до вызова равен объекту после вызова |

#### Приём и репозиторий (`test_domain.py`)

| Тест | Шаг | Ожидание |
|------|-----|----------|
| `test_accepted_duplicate_conflict` | 1. `accept(valid_raw_data)` | `status == "accepted"`, `len(repo) == 1` |
| `test_accepted_duplicate_conflict` | 2. `accept(deepcopy(valid_raw_data))` | `status == "duplicate"`, `len(repo) == 1` |
| `test_accepted_duplicate_conflict` | 3. `accept` с тем же `submission_id`, но `text = "Другое"` | `SubmissionError`, `code = conflict`; исходная запись не перезаписана (`repo.get("sub-001").text == "Текст"`) |

#### Strict-режим DTO (`test_domain.py`)

| Тест | Вход | Ожидание |
|------|------|----------|
| `test_pydantic_strict_types` | `valid_raw_data` с `schema_version = "1"` (строка) | `ValidationError` — Pydantic в `strict=True` не приводит строку к `int` |

#### CLI (`test_cli.py`)

| Тест | Вход | Ожидание |
|------|------|----------|
| `test_cli_mixed_data` | `mixed.jsonl` из трёх строк: валидная → `{broken json` → валидная | `main(["import", path])` возвращает `1`; битая строка не останавливает импорт |
