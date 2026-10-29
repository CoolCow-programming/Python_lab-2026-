from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..domain.models import Submission
from ..domain.validation import parse_submission, validate_timestamp
from ..domain.errors import SubmissionError


class DeclarationInput(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)

    used: bool
    tool: str | None
    purpose: str | None
    verified_by_student: bool

    @field_validator("tool", "purpose")
    @classmethod
    def check_optional_nonempty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise (ValueError("Строка должна быть не пустой или null"))
        return value

    @model_validator(mode="after")
    def checked_used_field(self):
        if self.used and (self.tool is None or self.purpose is None):
            raise ValueError(
                "Если used = True, поля tool и purpose должны быть заполнены")
        return self


class SubmissionInput(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)

    schema_version: int
    submission_id: str
    student_id: str
    assigment_id: str
    submitted_at: str
    text: str
    code: str
    template_id: str | None
    ai_declaration: DeclarationInput

    @field_validator("schema_version")
    @classmethod
    def suported_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("поддерживается версия 1")
        return value

    @field_validator("submission_id", "student_id",
                     "assigment_id", "template_id")
    @classmethod
    def identifiers(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Требуется не пустые идентификаторы")
        return value

    @field_validator("submitted_at")
    @classmethod
    def timestamp(cls, value: str) -> str:
        try:
            return validate_timestamp(value)
        except SubmissionError as exc:
            raise ValueError(exc.message) from exc

    @model_validator(mode='after')
    def has_content(self):
        if not self.text.strip() and not self.code.strip():
            raise ValueError("Поле text или code должно быть не пустым")
        return self

    def to_domain(self) -> Submission:
        return parse_submission(self.model_dump())
