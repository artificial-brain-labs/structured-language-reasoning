"""Termination criteria for SRST reasoning."""

from dataclasses import dataclass

from .state import GoalStatus, ReasoningState
from .validation import validate_state


@dataclass(frozen=True)
class TerminationResult:
    terminated: bool
    reason: str
    goal_satisfied: bool
    evidence_sufficient: bool
    semantically_valid: bool
    no_critical_conflict: bool
    proof_complete: bool


def check_termination(state: ReasoningState) -> TerminationResult:
    goal_satisfied = state.goal.status == GoalStatus.SATISFIED

    # Evidence sufficiency is represented explicitly by the goal reaching
    # SATISFIED. Operators can later provide a richer evidence policy without
    # changing the termination contract.
    evidence_sufficient = goal_satisfied
    semantically_valid = validate_state(state)
    no_critical_conflict = not bool(state.unresolved_conflicts())

    # A satisfied goal must have a proof node identifying the goal. For an
    # observational answer, the proof may be a direct goal node.
    proof_complete = bool(
        state.proof
        and state.proof.has_node(state.goal.id)
    )

    terminated = (
        goal_satisfied
        and evidence_sufficient
        and semantically_valid
        and no_critical_conflict
        and proof_complete
    )

    if terminated:
        reason = "termination criteria satisfied"
    elif not goal_satisfied:
        reason = "goal not satisfied"
    elif not semantically_valid:
        reason = "state is not semantically valid"
    elif not no_critical_conflict:
        reason = "critical conflict remains unresolved"
    elif not proof_complete:
        reason = "proof is incomplete"
    else:
        reason = "evidence is insufficient"

    return TerminationResult(
        terminated=terminated,
        reason=reason,
        goal_satisfied=goal_satisfied,
        evidence_sufficient=evidence_sufficient,
        semantically_valid=semantically_valid,
        no_critical_conflict=no_critical_conflict,
        proof_complete=proof_complete,
    )
