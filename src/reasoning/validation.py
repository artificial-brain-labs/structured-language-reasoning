"""Semantic validation helpers for SRST.

Validation is intentionally richer than a binary true/false result.
UNKNOWN and AMBIGUOUS are not treated as false.
"""

from .state import ReasoningState, ValidationStatus


def validate_state(state: ReasoningState) -> bool:
    """Return whether the current state is semantically valid for termination.

    A valid state has no unresolved contradictions or ambiguity/unknown claims.
    Goal satisfaction is checked separately by the termination module.
    """
    if state.unresolved_conflicts():
        return False

    return not any(
        claim.status in {
            ValidationStatus.UNKNOWN,
            ValidationStatus.AMBIGUOUS,
            ValidationStatus.CONTRADICTED,
        }
        for claim in state.claims.values()
    )
