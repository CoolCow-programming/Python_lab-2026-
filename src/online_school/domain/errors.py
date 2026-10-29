"Ошибки и поля"

from __future__ import annotations


class ErrorCode:
    INVALID_JSON = "invalid_json"
    SCHEMA_ERROR = "schema_error"
    UNSUPPORTED_VERSION = "unsupported_version"
    CONFLICT = "conflict"


class SubmissionError(Exception):
    def __init__(self,
                 code: str,
                 field: str | None,
                 message: str,
                 line_no: int | None = None,
                 ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message
        self.line_no = line_no

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
        }
