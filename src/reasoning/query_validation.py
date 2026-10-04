"""Proof-aware validation for transient SRST query results.

Query validation is stricter than checking that an operator produced a claim.
A derived result is admissible only when its dependency chain is valid and its
proof node exists. Unknown and ambiguous states remain non-answers.
"""

from .state import ReasoningState, ValidationStatus


_VALID_STATUSES = {
    ValidationStatus.OBSERVED,
    ValidationStatus.SUPPORTED,
    ValidationStatus.DERIVED,
}


def validate_claim_chain(state: ReasoningState, claim_id: str) -> bool:
    """Validate a claim and every claim it depends on.

    This is intentionally recursive over the transient proof dependency graph.
    Cycles are rejected rather than guessed through.
    """
    visiting = set()

    def visit(current_id: str) -> bool:
        if current_id in visiting:
            return False

        claim = state.claims.get(current_id)
        if claim is None or claim.status not in _VALID_STATUSES:
            return False

        if not state.proof or not state.proof.has_node(current_id):
            return False

        visiting.add(current_id)
        try:
            return all(visit(dep_id) for dep_id in claim.dependencies)
        finally:
            visiting.remove(current_id)

    return visit(claim_id)


def validate_query_result(state: ReasoningState, claim_id: str) -> bool:
    """Return whether a query result is admissible for termination."""
    if not validate_claim_chain(state, claim_id):
        return False

    if not state.proof or not state.proof.has_node(state.goal.id):
        return False

    return not state.unresolved_conflicts()
