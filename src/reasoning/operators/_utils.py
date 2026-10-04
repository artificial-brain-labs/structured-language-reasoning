"""Small shared helpers for concrete SRST operators."""

from ..state import ReasoningState, ValidationStatus
from ..transition import Transition


def transition(
    state: ReasoningState,
    operator: str,
    trigger: str,
    *,
    inputs=None,
    outputs=None,
    state_changes=None,
    validation_before=None,
    validation_after=None,
    success=True,
    failure_reason=None,
) -> Transition:
    return Transition(
        id=f"{operator.lower()}_{state.step + 1}",
        previous_step=state.step,
        resulting_step=state.step + 1,
        operator=operator,
        trigger=trigger,
        inputs=list(inputs or []),
        outputs=list(outputs or []),
        state_changes=list(state_changes or []),
        validation_before=validation_before,
        validation_after=validation_after,
        success=success,
        failure_reason=failure_reason,
    )


def unresolved_claims(state: ReasoningState):
    return [
        claim for claim in state.claims.values()
        if claim.status in {
            ValidationStatus.UNKNOWN,
            ValidationStatus.AMBIGUOUS,
        }
    ]
