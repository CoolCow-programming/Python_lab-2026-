from dataclasses import dataclass

from ..adapters.repository import InMemorySubmissionRepository
from ..domain.service import SubmissionService


@dataclass(frozen=True)
class Application:
    repository: InMemorySubmissionRepository
    submission_servise: SubmissionService


def build_aplication() -> Application:
    repo = InMemorySubmissionRepository()
    service = SubmissionService(repo)
    return Application(repository=repo, submission_servise=service)
