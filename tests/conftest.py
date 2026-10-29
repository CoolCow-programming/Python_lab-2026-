import copy
import pytest


@pytest.fixture
def valid_raw_data():
    return {
        "schema_version": 1,
        "submission_id": "sub-001",
        "student_id": "student-001",
        "assigment_id": "assigment-01",
        "submitted_at": "2026-09-01T10:01:00+03:00",
        "text": "Текст",
        "code": "print('Hello world')",
        "template_id": "template-01",
        "ai_declaration": {
            "used": False,
            "tool": None,
            "purpose": None,
            "verified_by_student": True
        }
    }


@pytest.fixture
def bad_student_id(valid_raw_data):
    data = copy.deepcopy(valid_raw_data)
    data["student_id"] = "   "
    return data


@pytest.fixture
def bad_timestamp(valid_raw_data):
    data = copy.deepcopy(valid_raw_data)
    data["submitted_at"] = "2026-09-01T10:01:00"
    return data


@pytest.fixture
def unknown_field(valid_raw_data):
    data = copy.deepcopy(valid_raw_data)
    data["unknown"] = "typo"
    return data
