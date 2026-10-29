import copy
import pytest

from online_school.domain.errors import ErrorCode, SubmissionError
from online_school.domain.validation import parse_submission
from online_school.domain.service import SubmissionService
from online_school.adapters.repository import InMemorySubmissionRepository
from online_school.adapters.parser import decode_json
from online_school.schemas.submission_in import SubmissionInput
from pydantic import ValidationError


def test_valid_submission(valid_raw_data):
    sub = parse_submission(valid_raw_data)
    assert sub.submission_id == "sub-001"
    assert sub.text == "Текст"


def test_empty_studetn_id(bad_student_id):
    with pytest.raises(SubmissionError) as exc:
        parse_submission(bad_student_id)
    assert exc.value.code == ErrorCode.SCHEMA_ERROR
    assert exc.value.field == "student_id"


def test_invalid_timestamp(bad_timestamp):
    with pytest.raises(SubmissionError) as exc:
        parse_submission(bad_timestamp)
    assert exc.value.code == ErrorCode.SCHEMA_ERROR
    assert exc.value.field == "submitted_at"


def test_unknown_field(unknown_field):
    with pytest.raises(SubmissionError) as exc:
        parse_submission(unknown_field)
    assert exc.value.code == ErrorCode.SCHEMA_ERROR
    assert exc.value.field == "unknown"


def test_input_immutability(valid_raw_data):
    original = copy.deepcopy(valid_raw_data)
    parse_submission(valid_raw_data)
    assert valid_raw_data == original


def test_broken_json():
    with pytest.raises(SubmissionError) as exc:
        decode_json('{"broken": ')
    assert exc.value.code == ErrorCode.INVALID_JSON


def test_repeated_keys():
    with pytest.raises(SubmissionError) as exc:
        decode_json('{"id": "1", "id": "2"}')
    assert exc.value.code == ErrorCode.INVALID_JSON


def test_accepted_duplicate_conflict(valid_raw_data):
    repo = InMemorySubmissionRepository()
    servise = SubmissionService(repo)

    res1 = servise.accept(valid_raw_data)
    assert res1.status == "accepted"
    assert len(repo) == 1

    res2 = servise.accept(copy.deepcopy(valid_raw_data))
    assert res2.status == "duplicate"
    assert len(repo) == 1

    conflict_data = copy.deepcopy(valid_raw_data)
    conflict_data["text"] = "Другое"

    with pytest.raises(SubmissionError) as exc:
        servise.accept(conflict_data)

    assert exc.value.code == ErrorCode.CONFLICT
    assert repo.get("sub-001").text == "Текст"


def test_pydantic_strict_types(valid_raw_data):
    bad_data = copy.deepcopy(valid_raw_data)
    bad_data["schema_version"] = "1"
    with pytest.raises(ValidationError):
        SubmissionInput.model_validate(bad_data)
