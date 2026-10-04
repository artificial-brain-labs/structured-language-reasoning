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


    def answer_path(self, path):
        """Answer an explicitly supplied relational path.

        Only non-conflicted durable memories are copied into transient
        reasoning state. The path itself determines which relation sequence
        RELATIONAL_TRAVERSE may execute.
        """
        path.validate()

        if not path.steps:
            return path.start, self._path_state(path)

        from .controller import OperatorController
        from .operators import RelationalTraverse

        state = self._path_state(path)

        # The anchor is an explicit query context, not a world-model fact.
        anchor_id = "query_anchor"
        state.add_claim(
            Claim(
                id=anchor_id,
                subject=path.start,
                predicate="QUERY_ANCHOR",
                object=path.start,
                source="QUERY",
                status=ValidationStatus.OBSERVED,
                confidence=1.0,
            )
        )
        state.proof.add_node(ProofNode(anchor_id, "query_anchor", anchor_id))

        for memory in self.memory.memories:
            if memory.status == "CONFLICTED":
                continue
            state.relations.append(
                (memory.subject, memory.predicate, memory.object)
            )

        state, result = OperatorController(
            [RelationalTraverse()]
        ).reason(state, max_steps=len(path.steps))

        if not result.terminated:
            return None, state

        final_claims = [
            claim
            for claim in state.claims.values()
            if claim.status == ValidationStatus.DERIVED
            and claim.object == path.target
        ]

        if not final_claims:
            return None, state

        return path.target, state

    def _path_state(self, path):
        return ReasoningState(
            goal=Goal(
                id="query_path",
                target=f"PATH:{path.start}:{'->'.join(path.predicates)}",
            ),
            query_path=path,
        )


    def answer_causal_path(self, path):
        """Answer an explicit causal path using CAUSAL_INFER only."""
        path.validate()

        from .controller import OperatorController
        from .operators import CausalInfer

        state = ReasoningState(
            goal=Goal(
                id="causal_query",
                target=f"CAUSE:{path.cause}->{ '->'.join(path.effects) }",
            )
        )
        # Keep the causal query context transient. It deliberately does not
        # become durable memory.
        state.causal_path = path
        state.causal_path_index = 0

        anchor_id = "causal_query_anchor"
        state.add_claim(
            Claim(
                id=anchor_id,
                subject=path.cause,
                predicate="OCCURS",
                object=None,
                source="QUERY",
                status=ValidationStatus.OBSERVED,
                confidence=1.0,
            )
        )
        state.proof.add_node(
            ProofNode(anchor_id, "query_anchor", anchor_id)
        )

        for memory in self.memory.memories:
            if memory.status == "CONFLICTED":
                continue
            state.relations.append(
                (memory.subject, memory.predicate, memory.object)
            )

        state, result = OperatorController(
            [CausalInfer()]
        ).reason(state, max_steps=len(path.steps))

        if not result.terminated:
            return None, state

        final_claims = [
            claim
            for claim in state.claims.values()
            if claim.status == ValidationStatus.DERIVED
            and claim.subject == path.target
            and claim.predicate == "OCCURS"
        ]

        if not final_claims:
            return None, state

        return path.target, state
