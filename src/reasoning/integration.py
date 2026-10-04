"""Boundary between SLR V0.2 memory and the SRST kernel.

SRST remains transient. This adapter validates a candidate observation before
it is allowed to become durable DynamicMemory.
"""

from .controller import OperatorController
from .operators import Monitor
from .proof import ProofEdge, ProofNode
from .state import Claim, Evidence, Goal, GoalStatus, ReasoningState
from .termination import check_termination


class SRSTObservationValidator:
    """Use SRST only where semantic validation is actually required."""

    def __init__(self):
        self.controller = OperatorController([Monitor()])

    def validate(self, subject, predicate, object_, source="USER", reliability=1.0):
        claim_id = "observation_1"
        state = ReasoningState(
            goal=Goal(id="validation_goal", target=f"validate:{claim_id}")
        )
        state.add_claim(
            Claim(
                id=claim_id,
                subject=subject,
                predicate=predicate,
                object=object_,
            )
        )
        state.evidence["evidence_1"] = Evidence(
            id="evidence_1",
            source=source,
            content=f"{subject} {predicate} {object_}",
            evidence_type="assertion",
            reliability=reliability,
            supports=[claim_id],
        )

        state, result = self.controller.reason(state, max_steps=1)

        if result.terminated:
            return True, state, result

        claim = state.claims[claim_id]
        if claim.status.value == "supported":
            state.proof.add_node(ProofNode(claim_id, "claim", claim_id))
            state.proof.add_node(
                ProofNode(state.goal.id, "goal", state.goal.id)
            )
            state.proof.add_edge(
                ProofEdge(claim_id, state.goal.id, "supports")
            )
            state.goal.status = GoalStatus.SATISFIED
            result = check_termination(state)

        return result.terminated, state, result
