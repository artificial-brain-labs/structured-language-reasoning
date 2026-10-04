"""CAUSAL_INFER: derive an effect only from an explicit CAUSES relation."""

from ..controller import CognitiveOperator
from ..proof import ProofEdge, ProofNode
from ..state import Claim, GoalStatus, ReasoningState, ValidationStatus
from ._utils import transition


class CausalInfer(CognitiveOperator):
    name = "CAUSAL_INFER"

    def _candidate(self, state):
        causal_path = getattr(state, "causal_path", None)

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

                if causal_path is not None:
                    index = getattr(state, "causal_path_index", 0)
                    if index >= len(causal_path.steps):
                        continue
                    expected = causal_path.steps[index].effect
                    if expected != effect:
                        continue

                claim_id = f"cause_{claim.id}_{effect}"
                if claim_id not in state.claims:
                    return claim, effect, claim_id

        return None

    def applicable(self, state):
        return (
            state.goal.status == GoalStatus.OPEN
            and self._candidate(state) is not None
        )

    def necessary(self, state):
        return self.applicable(state)

    def execute(self, state):
        candidate = self._candidate(state)
        if candidate is None:
            return state, transition(
                state,
                self.name,
                "no authorized causal relation is available",
                success=False,
                failure_reason="no authorized causal edge",
            )

        claim, effect, claim_id = candidate
        state.evidence[f"evidence_{claim_id}"] = Evidence(
            id=f"evidence_{claim_id}",
            source="DYNAMIC_MEMORY",
            content=f"{claim.subject} CAUSES {effect}",
            evidence_type="memory",
            reliability=claim.confidence,
            supports=[claim_id],
        )

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

        state.proof.add_node(ProofNode(claim.id, "claim", claim.id))
        state.proof.add_node(ProofNode(claim_id, "causal_effect", claim_id))
        state.proof.add_edge(
            ProofEdge(claim.id, claim_id, "causes")
        )

        state_changes = ["derived_causal_effect"]

        causal_path = getattr(state, "causal_path", None)
        if causal_path is not None:
            state.causal_path_index += 1
            if state.causal_path_index == len(causal_path.steps):
                state.goal.status = GoalStatus.SATISFIED
                state.proof.add_node(
                    ProofNode(state.goal.id, "goal", state.goal.id)
                )
                state.proof.add_edge(
                    ProofEdge(claim_id, state.goal.id, "answers")
                )
                state_changes.append("causal_path_completed")

        return state, transition(
            state,
            self.name,
            "explicit CAUSES relation supports an effect",
            inputs=[claim.id],
            outputs=[claim_id],
            state_changes=state_changes,
            validation_after=ValidationStatus.DERIVED,
        )
