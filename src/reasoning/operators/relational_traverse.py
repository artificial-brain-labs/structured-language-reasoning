"""RELATIONAL_TRAVERSE: follow explicit semantic relations."""

from ..controller import CognitiveOperator
from ..proof import ProofEdge, ProofNode
from ..state import Claim, GoalStatus, ReasoningState, ValidationStatus
from ._utils import transition


class RelationalTraverse(CognitiveOperator):
    name = "RELATIONAL_TRAVERSE"

    def _candidate(self, state):
        query_path = state.query_path

        for claim in state.claims.values():
            if claim.status not in (
                ValidationStatus.OBSERVED,
                ValidationStatus.SUPPORTED,
                ValidationStatus.DERIVED,
            ):
                continue

            for subject, predicate, object_ in state.relations:
                if claim.object != subject or predicate == "CAUSES":
                    continue

                # Explicit query paths constrain traversal to the requested
                # relation sequence and, when supplied, its target entity.
                if query_path is not None:
                    index = state.query_path_index
                    expected = query_path.next_predicate(index)
                    if expected != predicate:
                        continue

                    requested_step = query_path.steps[index]
                    if (
                        requested_step.target is not None
                        and requested_step.target != object_
                    ):
                        continue

                claim_id = f"traverse_{claim.id}_{predicate}_{object_}"
                if claim_id not in state.claims:
                    return claim, (subject, predicate, object_), claim_id

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
                "no traversable relation",
                success=False,
                failure_reason="no authorized relational edge",
            )

        claim, (_, predicate, object_), claim_id = candidate

        state.evidence[f"evidence_{claim_id}"] = Evidence(
            id=f"evidence_{claim_id}",
            source="DYNAMIC_MEMORY",
            content=f"{claim.object} {predicate} {object_}",
            evidence_type="memory",
            reliability=claim.confidence,
            supports=[claim_id],
        )

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

        state.proof.add_node(ProofNode(claim.id, "claim", claim.id))
        state.proof.add_node(ProofNode(claim_id, "claim", claim_id))
        state.proof.add_edge(
            ProofEdge(claim.id, claim_id, "traverses")
        )

        state_changes = ["derived_relation"]

        if state.query_path is not None:
            state.query_path_index += 1

            if state.query_path_index == len(state.query_path.steps):
                state.goal.status = GoalStatus.SATISFIED
                state.proof.add_node(
                    ProofNode(state.goal.id, "goal", state.goal.id)
                )
                state.proof.add_edge(
                    ProofEdge(claim_id, state.goal.id, "answers")
                )
                state_changes.append("query_path_completed")

        return state, transition(
            state,
            self.name,
            "explicit query path authorizes relational traversal",
            inputs=[claim.id],
            outputs=[claim_id],
            state_changes=state_changes,
            validation_after=ValidationStatus.DERIVED,
        )
