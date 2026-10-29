from __future__ import annotations
import json
from ..domain.errors import ErrorCode, SubmissionError


def reject_repeated_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SubmissionError(ErrorCode.INVALID_JSON,
                                  key, "Повторный key в JSON")
        result[key] = value
    return result


def reject_constant(value: str) -> object:
    raise SubmissionError(ErrorCode.INVALID_JSON, "json",
                          f"значение {value} не допускается")


def decode_json(line: str) -> object:
    try:
        return json.loads(line, object_pairs_hook=reject_repeated_keys,
                          parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise SubmissionError(ErrorCode.INVALID_JSON, "json",
                              f"Ошибка JSON столбец: {exc.colno}")
