"""BACKTRACK: invalidate dependent derived claims after a bad premise."""

from ..controller import CognitiveOperator
from ..state import GoalStatus, ReasoningState, ValidationStatus
from ._utils import transition


class Backtrack(CognitiveOperator):
    name = "BACKTRACK"

    def _invalidated(self, state):
        invalidated = {
            claim.id
            for claim in state.claims.values()
            if claim.status == ValidationStatus.CONTRADICTED
        }

        changed = True
        while changed:
            changed = False
            for claim in state.claims.values():
                if claim.id in invalidated:
                    continue
                if any(dep in invalidated for dep in claim.dependencies):
                    invalidated.add(claim.id)
                    changed = True

        return invalidated

    def applicable(self, state):
        return (
            state.goal.status == GoalStatus.OPEN
            and any(
                claim.status == ValidationStatus.CONTRADICTED
                for claim in state.claims.values()
            )
        )

    def necessary(self, state):
        return self.applicable(state)

    def execute(self, state):
        invalidated = self._invalidated(state)
        changed = []

        for claim_id in invalidated:
            claim = state.claims[claim_id]
            if claim.status == ValidationStatus.CONTRADICTED:
                changed.append(f"{claim_id}:preserved")
                continue
            if claim.status != ValidationStatus.UNKNOWN:
                claim.status = ValidationStatus.UNKNOWN
                state.validation[claim_id] = claim.status
                changed.append(f"{claim_id}:invalidated")

        return state, transition(
            state,
            self.name,
            "a failed premise invalidates dependent derivations",
            inputs=sorted(invalidated),
            state_changes=changed,
        )
