"""RELATIONAL_TRAVERSE: follow explicit semantic relations without inferring causality."""

from ..controller import CognitiveOperator
from ..state import Claim, GoalStatus, ReasoningState, ValidationStatus
from ._utils import transition


class RelationalTraverse(CognitiveOperator):
    name = "RELATIONAL_TRAVERSE"

    def _candidate(self, state: ReasoningState):
        for claim in state.claims.values():
            if claim.status not in {
                ValidationStatus.OBSERVED,
                ValidationStatus.SUPPORTED,
                ValidationStatus.DERIVED,
            }:
                continue
            for subject, predicate, object_ in state.relations:
                if claim.object == subject:
                    return claim, (subject, predicate, object_)
        return None

    def applicable(self, state: ReasoningState) -> bool:
        return state.goal.status == GoalStatus.OPEN and self._candidate(state) is not None

    def necessary(self, state: ReasoningState) -> bool:
        return self.applicable(state)

    def execute(self, state: ReasoningState):
        candidate = self._candidate(state)
        if candidate is None:
            return state, transition(
                state,
                self.name,
                "no traversable relation",
                success=False,
                failure_reason="no applicable relational edge",
            )

        claim, (_, predicate, object_) = candidate
        claim_id = f"traverse_{claim.id}_{predicate}_{object_}"
        if claim_id not in state.claims:
            state.add_claim(
                Claim(
                    id=claim_id,
                    subject=claim.object,
                    predicate=predicate,
                    object=object_,
                    source=claim.id,
                    status=ValidationStatus.DERIVED,
                    confidence=claim.confidence,
                    dependencies=[claim.id],
                )
            )

        return state, transition(
            state,
            self.name,
            "known relation can be traversed",
            inputs=[claim.id],
            outputs=[claim_id],
            state_changes=["derived_relation"],
            validation_after=ValidationStatus.DERIVED,
        )
