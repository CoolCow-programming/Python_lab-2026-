from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .errors import ErrorCode, SubmissionError
from .hashing import submission_hash
from .validation import parse_submission


if TYPE_CHECKING:
    from ..adapters.repository import SubmissionRepository


AcceptanceStatus = Literal["accepted", "duplicated"]


@dataclass(frozen=True, slots=True)
class Acceptance:
    status: AcceptanceStatus
    submission_id: str
    content_hash: str


class SubmissionService:
    def __init__(self, repository: "SubmissionRepository") -> None:
        self.repository = repository

    def accept(self, raw: object) -> Acceptance:
        submission = parse_submission(raw)
        digest = submission_hash(submission)
        previous = self.repository.get(submission.submission_id)

        if previous is not None:
            if submission_hash(previous) != digest:
                raise SubmissionError(
                    ErrorCode.CONFLICT, "submission_id",
                    "для новой версии нужен новый id")
            return Acceptance("duplicate", submission.submission_id, digest)
        self.repository.add(submission)
        return Acceptance("accepted", submission.submission_id, digest)
