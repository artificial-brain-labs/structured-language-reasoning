"""CAUSAL_INFER: derive an effect only from an explicit CAUSES relation."""

from ..controller import CognitiveOperator
from ..state import Claim, GoalStatus, ReasoningState, ValidationStatus
from ._utils import transition


class CausalInfer(CognitiveOperator):
    name = "CAUSAL_INFER"

    def _candidate(self, state):
        for claim in state.claims.values():
            if claim.status not in (
                ValidationStatus.OBSERVED,
                ValidationStatus.SUPPORTED,
                ValidationStatus.DERIVED,
            ):
                continue
            for source, predicate, effect in state.relations:
                if predicate != "CAUSES" or claim.subject != source:
                    continue
                claim_id = f"cause_{claim.id}_{effect}"
                if claim_id not in state.claims:
                    return claim, effect, claim_id
        return None

    def applicable(self, state):
        return state.goal.status == GoalStatus.OPEN and self._candidate(state) is not None

    def necessary(self, state):
        return self.applicable(state)

    def execute(self, state):
        candidate = self._candidate(state)
        if candidate is None:
            return state, transition(
                state,
                self.name,
                "no causal relation is available",
                success=False,
                failure_reason="no new causal edge",
            )

        claim, effect, claim_id = candidate
        state.add_claim(
            Claim(
                id=claim_id,
                subject=effect,
                predicate="OCCURS",
                object=None,
                source=claim.id,
                status=ValidationStatus.DERIVED,
                confidence=claim.confidence,
                dependencies=[claim.id],
            )
        )

        return state, transition(
            state,
            self.name,
            "explicit causal relation supports an effect",
            inputs=[claim.id],
            outputs=[claim_id],
            state_changes=["derived_causal_effect"],
            validation_after=ValidationStatus.DERIVED,
        )
