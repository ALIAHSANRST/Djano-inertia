from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetInput:
    title: str
    amount: str
    justification: str
    revision: int | None = None


@dataclass(frozen=True)
class ReviewInput:
    status: str
    feedback: str
    revision: int | None


@dataclass(frozen=True)
class MutationResult:
    errors: dict[str, str]
    message: str = ""
