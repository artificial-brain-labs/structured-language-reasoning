"""Explicit query-path representation for demand-driven relational reasoning.

A query path states exactly which relations may be traversed. It does not
authorize arbitrary graph inference and it never implies causal semantics.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QueryPathStep:
    """One directed relation that the query explicitly permits."""

    predicate: str
    target: str | None = None


@dataclass(frozen=True)
class QueryPath:
    """An explicit relational path from a known entity."""

    start: str
    steps: tuple[QueryPathStep, ...] = field(default_factory=tuple)

    @property
    def target(self) -> str | None:
        if not self.steps:
            return self.start
        return self.steps[-1].target

    @property
    def predicates(self) -> tuple[str, ...]:
        return tuple(step.predicate for step in self.steps)

    def validate(self) -> None:
        if not self.start:
            raise ValueError("QueryPath requires a start entity.")

        for step in self.steps:
            if step.predicate == "CAUSES":
                raise ValueError(
                    "QueryPath cannot encode CAUSES; causal inference "
                    "requires CAUSAL_INFER."
                )

    def next_predicate(self, index: int) -> str | None:
        if index < 0 or index >= len(self.steps):
            return None
        return self.steps[index].predicate
