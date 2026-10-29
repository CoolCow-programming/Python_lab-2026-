import json
from pathlib import Path
from online_school.cli import main


def test_cli_mixed_data(tmp_path:  Path):
    file_path = tmp_path / "mixed.jsonl"

    valid_line = json.dumps({
        "schema_version": 1, "submission_id": "sub-1", "student_id": "st-1",
        "assigment_id": "as-1", "submitted_id": "2026-09-01T10:00:00+03:00",
        "text": "text", "code": "code", "template_id": None,
        "ai_declaration": {
            "used": False, "tool": None,
            "purpose": None, "verified_by_student": True}
    })
    file_path.write_text(
        valid_line + "\n" +
        "{broken json\n" +
        valid_line + "\n",
        encoding="utf-8"
    )
    exit_code = main(["import", str(file_path)])
    assert exit_code == 1
