from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .adapters.sources import JSONLSource, SubmissionSource
from .app.build import build_aplication
from .domain.errors import ErrorCode, SubmissionError
from .schemas.submission_in import SubmissionInput


@dataclass
class ImportSummary:
    accepted: list[str] = field(default_factory=list)
    duplicate: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    def to_dict(self):
        return {
            "accepted": self.accepted,
            "duplicate": self.duplicate,
            "errors": self.errors,
        }


def import_source(source: SubmissionSource, app) -> ImportSummary:
    summary = ImportSummary()

    with source.open() as records:
        for record in records:
            if record.error is not None:
                summary.errors.append(
                    {"line_no": record.line_no, **record.error.to_dict()}
                    )
                continue
            try:
                dto = SubmissionInput.model_validate(record.raw)
                result = app.submission_servise.accept(dto.model_dump())
            except ValidationError as exc:
                first_err = exc.errors()[0]
                summary.errors.append({
                    "line_no": record.line_no,
                    "code": ErrorCode.SCHEMA_ERROR,
                    "field": ".".join(str(loc) for loc in first_err["loc"]),
                    "message": first_err["msg"],
                })
            except SubmissionError as exc:
                summary.errors.append({
                    "line_no": record.line_no, **exc.to_dict()
                })
            else:
                if result.status == "accepted":
                    target = summary.accepted
                else:
                    target = summary.duplicate
                target.append(result.submission_id)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="online-school")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="JSONL импорт")
    imp.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    if args.command == "import":
        app = build_aplication()
        try:
            source = JSONLSource(args.path)
            summary = import_source(source, app)
        except (OSError, UnicodeError) as exc:
            print(json.dumps(
                {"code": "source_unavailable", "message": str(exc)},
                ensure_ascii=False), file=sys.stderr)
            return 2
        print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
        return 1 if summary.errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
