"""SRST boundary for query answering.

Direct, validated memory answers remain the fast path. SRST records the query
as a transient reasoning state and produces an explicit proof for answers.
No query result is written back to durable memory.
"""

from .proof import ProofEdge, ProofNode
from .state import Claim, Goal, GoalStatus, ReasoningState, ValidationStatus
from .termination import check_termination


class SRSTQueryReasoner:
    """Answer supported SLR queries through a transient SRST state."""

    def __init__(self, memory, lexicon):
        self.memory = memory
        self.lexicon = lexicon

    def _state_for_object_query(self, parsed):
        subject_concept = self.lexicon.concept(parsed.subject_word)
        predicate = self.lexicon.concept(parsed.verb_word)
        if not subject_concept or not predicate:
            return None, []

        subject = self.memory.find_entity(subject_concept)
        memories = [
            memory
            for memory in self.memory.query(subject=subject, predicate=predicate)
            if memory.status != "CONFLICTED"
        ]

        goal_id = "query_object"
        state = ReasoningState(
            goal=Goal(
                id=goal_id,
                target=f"OBJECT:{subject}:{predicate}",
            )
        )

        results = []
        for index, memory in enumerate(memories):
            claim_id = f"memory_{index}"
            claim = Claim(
                id=claim_id,
                subject=memory.subject,
                predicate=memory.predicate,
                object=memory.object,
                source=memory.source,
                status=ValidationStatus.OBSERVED,
                confidence=memory.confidence,
            )
            state.add_claim(claim)
            state.proof.add_node(ProofNode(claim_id, "memory", claim_id))
            results.append(memory.object)

        self._complete_if_supported(state, results)
        return state, results

    def _state_for_subject_query(self, parsed):
        object_concept = self.lexicon.concept(parsed.object_word)
        predicate = self.lexicon.concept(parsed.verb_word)
        if not object_concept or not predicate:
            return None, []

        object_id = self.memory.find_entity(object_concept)
        memories = [
            memory
            for memory in self.memory.query(
                predicate=predicate, object_=object_id
            )
            if memory.status != "CONFLICTED"
        ]

        goal_id = "query_subject"
        state = ReasoningState(
            goal=Goal(
                id=goal_id,
                target=f"SUBJECT:{predicate}:{object_id}",
            )
        )

        results = []
        for index, memory in enumerate(memories):
            claim_id = f"memory_{index}"
            claim = Claim(
                id=claim_id,
                subject=memory.subject,
                predicate=memory.predicate,
                object=memory.object,
                source=memory.source,
                status=ValidationStatus.OBSERVED,
                confidence=memory.confidence,
            )
            state.add_claim(claim)
            state.proof.add_node(ProofNode(claim_id, "memory", claim_id))
            results.append(memory.subject)

        self._complete_if_supported(state, results)
        return state, results

    def _complete_if_supported(self, state, results):
        if not results:
            return

        state.goal.status = GoalStatus.SATISFIED
        state.proof.add_node(
            ProofNode(state.goal.id, "goal", state.goal.id)
        )

        for claim_id in state.claims:
            state.proof.add_edge(
                ProofEdge(claim_id, state.goal.id, "supports")
            )

    def answer(self, parsed):
        """Return (results, reasoning_state).

        A direct durable-memory match is sufficient, so no cognitive operator
        is executed. The transient state still records what supports the
        answer and whether the SRST termination contract is satisfied.
        """
        if parsed.question_type == "OBJECT":
            state, results = self._state_for_object_query(parsed)
        elif parsed.question_type == "SUBJECT":
            state, results = self._state_for_subject_query(parsed)
        else:
            return [], None

        if state is not None:
            state, _ = state, check_termination(state)

        return results, state

    def termination(self, state):
        if state is None:
            return None
        return check_termination(state)
