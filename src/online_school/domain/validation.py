from __future__ import annotations

from datetime import datetime
from collections.abc import Mapping

from .errors import ErrorCode, SubmissionError
from .models import AIDeclaration, Submission


SUBMISSION_FIELD = {
    "schema_version", "submission_id", "student_id",
    "assigment_id", "submitted_at", "text", "code",
    "template_id", "ai_declaration"
}

DECLARATION_FIELD = {
    "used",
    "tool",
    "purpose",
    "verified_by_student",
}


def require_object(raw: object, name: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, name,
                              "ожидается JSON обьект")
    if any(not isinstance(k, str) for k in raw):
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, name,
                              "ключи должны быть str")
    return raw


def require_fields(raw: Mapping[str, object], expected: frozenset[str],
                 prefix: str = "") -> None:
    missing = expected - raw.keys()
    extra = raw.keys() - expected
    if missing:
        name = sorted(missing)[0]
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, name,
                              "Отсутствует обязательное поле")
    if extra:
        name = sorted(extra)[0]
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, name,
                              "Переданны неизвестные поля")


def require_string(value: object, name: str, *,
                        nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, name,
                              "ожидается строка")
    if nonempty and not value.strip():
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, name,
                              "ожидается не пустая строка")
    return value


def optinal_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    return require_string(value, name)


def require_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, name,
                              "ожидается bool")
    return value


def validate_timestamp(value: object) -> str:
    text = require_string(value, "submitted_at")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "submitted_at",
                              "ожидается формат ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "submitted_at",
                              "часовой пояс обязателен")
    return text


def parse_submission(raw: object) -> Submission:
    data = require_object(raw, "submission")
    require_fields(data, SUBMISSION_FIELD)

    version = data["schema_version"]
    if type(version) is not int:
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "schema_version",
                              "ожидается int")
    if version != 1:
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "schema_version",
                              "поддерживается версия схемы 1")
    decl_data = require_object(data["ai_declaration"], "ai_declaration")
    require_fields(decl_data, DECLARATION_FIELD, "ai_declaration.")
    declaration = AIDeclaration(
        used=require_bool(decl_data["used"], "ai_declaration.used"),
        tool=optinal_string(decl_data["tool"], "ai_declaration.tool"),
        purpose=optinal_string(decl_data["purpose"], "ai_declaration.purpose"),
        verified_by_student=require_bool(
            decl_data["verified_by_student"],
            "ai_declaration.verified_by_student"
        ),
    )
    if declaration.used and declaration.tool is None:
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "ai_declaration",
                              "не заполнено поле инструментов")
    if declaration.used and declaration.purpose is None:
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "ai_declaration",
                              "не заполнено поле назначения")
    text = require_string(data["text"], "text", nonempty=False)
    if not text.strip():
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "text",
                              "текст должен быть не пустым")
    source_code = require_string(data["code"], "code", nonempty=False)
    if not source_code.strip():
        raise SubmissionError(ErrorCode.SCHEMA_ERROR, "code",
                              "поле с кодом должно быть не пустым")

    return Submission(
        schema_version=version,
        submission_id=require_string(data["submission_id"], "submission_id"),
        student_id=require_string(data["student_id"], "student_id"),
        assigment_id=require_string(data["assigment_id"], "assigment_id"),
        submitted_at=validate_timestamp(data["submitted_at"]),
        text=text,
        code=source_code,
        template_id=optinal_string(data["template_id"], "template_id"),
        ai_declaration=declaration,
    )
