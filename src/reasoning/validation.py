"""Semantic validation helpers for SRST.

Validation is intentionally richer than a binary true/false result.
UNKNOWN and AMBIGUOUS are not treated as false.
"""

from .state import ReasoningState, ValidationStatus


_VALID_STATUSES = {
    ValidationStatus.OBSERVED,
    ValidationStatus.SUPPORTED,
    ValidationStatus.DERIVED,
}


def validate_state(state: ReasoningState) -> bool:
    """Return whether the current state is semantically valid for termination.

    A valid state has no unresolved contradictions or ambiguity/unknown claims.
    Goal satisfaction is checked separately by the termination module.
    """
    if state.unresolved_conflicts():
        return False

    if any(
        claim.status in {
            ValidationStatus.UNKNOWN,
            ValidationStatus.AMBIGUOUS,
            ValidationStatus.CONTRADICTED,
        }
        for claim in state.claims.values()
    ):
        return False

    # Every derived claim must have a valid dependency chain and proof node.
    # This prevents an operator from becoming an implicit source of truth.
    visiting = set()

    def valid_chain(claim_id):
        if claim_id in visiting:
            return False

        claim = state.claims.get(claim_id)
        if claim is None or claim.status not in _VALID_STATUSES:
            return False

        if not state.proof or not state.proof.has_node(claim_id):
            return False

        if claim.status != ValidationStatus.DERIVED:
            return True

        visiting.add(claim_id)
        try:
            return all(valid_chain(dep_id) for dep_id in claim.dependencies)
        finally:
            visiting.remove(claim_id)

    return all(valid_chain(claim.id) for claim in state.claims.values())
