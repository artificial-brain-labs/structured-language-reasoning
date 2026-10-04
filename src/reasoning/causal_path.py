"""Explicit causal query representation.

Causal paths are deliberately separate from QueryPath because CAUSES is not
ordinary relational traversal. They authorize CAUSAL_INFER only.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CausalPathStep:
    effect: str


@dataclass(frozen=True)
class CausalPath:
    cause: str
    steps: tuple[CausalPathStep, ...] = field(default_factory=tuple)

    @property
    def target(self) -> str | None:
        return self.steps[-1].effect if self.steps else self.cause

    def validate(self) -> None:
        if not self.cause:
            raise ValueError("CausalPath requires a cause entity.")
        if not self.steps:
            raise ValueError("CausalPath requires at least one effect.")

    @property
    def effects(self) -> tuple[str, ...]:
        return tuple(step.effect for step in self.steps)
