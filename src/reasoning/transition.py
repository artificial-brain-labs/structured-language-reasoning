"""State-transition record for SRST."""

from dataclasses import dataclass, field

from .state import ValidationStatus


@dataclass
class Transition:
    id: str
    previous_step: int
    resulting_step: int
    operator: str
    trigger: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    state_changes: list[str] = field(default_factory=list)
    validation_before: ValidationStatus | None = None
    validation_after: ValidationStatus | None = None
    success: bool = True
    failure_reason: str | None = None

    def is_valid_step(self) -> bool:
        return self.resulting_step == self.previous_step + 1
