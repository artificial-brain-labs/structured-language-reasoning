from uuid import uuid4

from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .memory import DynamicMemory
from .user_memory import UserMemory
from .user_profile import UserProfile
from .user_relationships import UserRelationshipMemory, InterSLRMCommunication
from .identity_protocol import IdentityProtocol
from .communication_protocol import GovernedCommunicationProtocol
from .reasoner import Reasoner
from .query import QueryEngine
from .response import ResponseGenerator
from .response_policy import ResponsePolicy
from .semantics import SemanticParser
from .executor import SemanticExecutor
from .statement_router import StatementRouter, StatementResult
from .entity_resolver import EntityResolver
from .clarification_manager import ClarificationManager
from .clarification_policy import ClarificationPolicy
from .operation_engine import OperationEngine
from .semantic_graph import SemanticGraph
from .graph_reasoner import SemanticGraphReasoner
from .graph_builder import SemanticGraphBuilder
from .tcm import TransientCommunicationMemory
from .contextual_meaning_memory import ContextualMeaningMemory
from .semantic_context import SemanticContextExtractor
from .semantic_context_resolver import SemanticContextResolver


class SLR:
    def __init__(self, user_id=None, username=None):
        # A missing user_id means an anonymous runtime instance, not an inferred identity.
        if user_id is None:
            user_id = f"ANONYMOUS-{uuid4().hex}"
        self.user_profile = UserProfile(user_id=user_id, username=username)
        self.lexicon = Lexicon()
        self.ontology = Ontology()
        self.parser = Parser(self.lexicon)

        self.memory = DynamicMemory()
        self.user_memory = UserMemory()
        self.tcm = TransientCommunicationMemory()
        self.contextual_meaning = ContextualMeaningMemory(self.lexicon)
        self.semantic_context = SemanticContextExtractor(self.lexicon)
        self.semantic_context_resolver = SemanticContextResolver(
            self.contextual_meaning, self.lexicon, self.ontology
        )
        self.semantic_parser = SemanticParser(
            self.lexicon,
            contextual_memory=self.contextual_meaning,
            semantic_context_resolver=self.semantic_context_resolver,
        )

        self.relationships = UserRelationshipMemory(
            owner_user_id=self.user_profile.user_id,
            slrm_instance_id=self.user_profile.slrm_instance_id,
        )
        self.inter_slrm = InterSLRMCommunication(self.relationships)
        self.identity_protocol = IdentityProtocol(self.relationships)
        self.communication_protocol = GovernedCommunicationProtocol(self.relationships)

        self.reasoner = Reasoner(self.ontology, self.user_memory)
        self.executor = SemanticExecutor(self.user_memory)
        self.resolver = EntityResolver(self.lexicon, self.ontology, self.user_memory)
        self.clarification = ClarificationManager(self.user_memory)
        self.clarification_policy = ClarificationPolicy()
        self.operation_engine = OperationEngine(
            self.executor.definitions,
            self.resolver,
            self.reasoner,
            self.executor,
            self.user_memory,
            self.lexicon,
            self.clarification,
            relationship_memory=self.relationships,
        )
        self.router = StatementRouter()
        self.router.register_all(self.executor.definitions.operations, self.operation_engine.execute)

        # The graph builder requires the same ontology data used by the reasoner.
        self.graph_builder = SemanticGraphBuilder(self.ontology)
        self.graph_reasoner = SemanticGraphReasoner(self.ontology, self.user_memory.relations.schemas)
        self.graph = SemanticGraph()
        self._refresh_graph()

        self.query = QueryEngine(
            self.user_memory,
            self.lexicon,
            self.reasoner,
            graph=self.graph,
            relationship_memory=self.relationships,
            semantic_context_resolver=self.semantic_context_resolver,
        )
        self.response = ResponseGenerator(self.user_memory)
        self.response_policy = ResponsePolicy(self.executor.definitions)

    def _refresh_graph(self):
        # Reasoning starts from an asserted-only graph. Derived edges produced
        # by the canonical reasoner are projected only after that pass.
        asserted_graph = self.graph_builder.build(self.user_memory)
        reasoning = self.graph_reasoner.reason(asserted_graph)

        derived = []
        for edge in reasoning.edges:
            derived.append({
                "edge_id": edge.edge_id,
                "subject": edge.subject,
                "predicate": edge.predicate,
                "object": edge.object,
                "status": edge.status,
                "source": edge.source,
                "confidence": edge.confidence,
                "support": list(edge.support),
                "rule": edge.attributes.get("rule"),
            })

        self.graph = self.graph_builder.build(self.user_memory, derived=derived)
        if hasattr(self, "query"):
            self.query.graph = self.graph
            self.query.graph_query.graph = self.graph
    def _lexical_ambiguity(self, parsed, original_text, semantic_context=None):
        """Return the first unresolved lexical ambiguity in this sentence."""
        checked = set()
        property_value = (
            ((parsed.operation == "ASSERT_RELATION" and parsed.relation == "HAS_PROPERTY")
            or parsed.question_type == "PROPERTY")
            and parsed.object_word is not None
        )
        for word in (parsed.subject_word, parsed.verb_word, parsed.object_word, *(parsed.tokens or ())):
            if not word or word.lower() in checked:
                continue
            checked.add(word.lower())

            # A property value can remain an unresolved lexical reference.
            # The asserted relation is still explicit: entity HAS_PROPERTY word.
            # Forcing a dictionary sense here would block valid observations
            # such as "zorb is blue" and would confuse property with type.
            if property_value and word.lower() == parsed.object_word.lower():
                continue

            senses = self.lexicon.senses(word) if hasattr(self.lexicon, "senses") else []
            if len(senses) <= 1:
                continue
            candidate_ids = [sense.sense_id for sense in senses]
            resolution = self.semantic_context_resolver.resolve_result(
                word, semantic_context, candidate_ids
            )
            if resolution.status == "AMBIGUOUS":
                return word, senses
        return None

    def _record_observation(self, text, parsed):
        self.user_memory.record_observation(
            subject=parsed.subject_word,
            predicate=parsed.verb_word,
            object=parsed.object_word,
            source="USER",
            content=text.strip(),
        )

    def _record_interpretation(self, parsed, operation):
        self.user_memory.record_interpretation(
            subject=operation.subject,
            predicate=operation.predicate,
            object=operation.object,
            support=(parsed.rule,) if parsed.rule else (),
            source="SYSTEM",
        )

    def _execute_statement(self, parsed, context=None):
        meaning = self.semantic_parser.parse(parsed, context=context)
        operation = meaning.operation
        if operation is None:
            return StatementResult()
        self._record_interpretation(parsed, operation)
        return self.router.dispatch(operation, parsed)

    def _handle_pending_clarification(self, text):
        request = self.clarification.current()
        if request is None:
            return None
        if request.kind == "lexical_meaning":
            selected = self.clarification.resolve_lexical_response(text)
            if selected is None:
                return request.question
            original_text = request.original_context
            original_parsed = self.parser.parse(original_text)
            original_semantic_context = self.semantic_context.extract(
                original_parsed, original_text
            )
            self.contextual_meaning.learn(
                request.word,
                selected,
                request.candidates,
                original_text,
                semantic_context=original_semantic_context,
            )
            self.clarification.clear()

            # The user explicitly resolved the only lexical ambiguity in the
            # original statement. Resume that same observation directly.
            # Any unresolved entity remains UNKNOWN; no type is inferred.
            resumed_parsed = self.parser.parse(original_text)
            resumed_context = self.semantic_context.extract(
                resumed_parsed, original_text
            )
            if not resumed_parsed.meaning:
                return self.response.system("parse_failure")
            resumed_meaning = self.semantic_parser.parse(
                resumed_parsed, context=resumed_context
            )
            resumed_operation = resumed_meaning.operation
            if resumed_operation is None:
                return self.response.system("execution_failure")
            resumed_operation.attributes["explicitly_confirmed_context"] = True
            self._record_interpretation(resumed_parsed, resumed_operation)
            execution = self.router.dispatch(resumed_operation, resumed_parsed)
            if execution.clarification:
                return execution.clarification
            if execution.result is None:
                failure = self.response_policy.render(resumed_operation, "failure")
                return failure or self.response.system("execution_failure")
            self._refresh_graph()
            success_context = {}
            if resumed_parsed.subject_word:
                entity = self.user_memory.canonical_entity(execution.result.subject)
                success_context["subject_name"] = self.user_memory.entities[entity]["name"]
            if resumed_parsed.object_word:
                success_context["object_word"] = resumed_parsed.object_word
            success = self.response_policy.render(
                resumed_operation, "success", success_context
            )
            return success or self.response.system("execution_failure")
        return self._handle_pending_entity_clarification(text)

    def _handle_pending_entity_clarification(self, text):
        request = self.clarification.current()
        if request is None:
            return None
        parsed = self.parser.parse(text)
        accepted_meanings = self.clarification_policy.accepted_meanings("entity_identity")
        if parsed.meaning not in accepted_meanings:
            return None
        pending_entity = request.entity_id
        pending_name = self.user_memory.entities[pending_entity]["name"]
        if not parsed.subject_word or parsed.subject_word.lower() != pending_name.lower():
            return None
        # A validated clarification response is explicit user communication.
        # Preserve it in the evidence ledger before applying its classification.
        self._record_observation(text, parsed)
        meaning = self.semantic_parser.parse(parsed)
        classification_operation = meaning.operation
        if classification_operation is None:
            return None
        classification_operation.subject = pending_entity
        self._record_interpretation(parsed, classification_operation)
        execution = self.operation_engine.execute(classification_operation, parsed)
        if execution.result is None:
            return None
        original_operation = request.original_operation
        original_context = request.original_context
        self.clarification.clear()
        confirmation_context = {"subject_name": pending_name, "object_word": parsed.object_word}
        confirmation = self.response_policy.render(execution.operation, "success", confirmation_context)
        if original_operation is None or original_context is None:
            self._refresh_graph()
            return confirmation
        original_operation.subject = self.user_memory.canonical_entity(pending_entity)
        resumed = self.operation_engine.execute(original_operation, original_context)
        self._refresh_graph()
        if resumed.result is None:
            return self.response.system("classification_resumed_failure", confirmation_context)
        if resumed.clarification:
            return resumed.clarification
        success = self.response.system("classification_resumed_success")
        return f"{confirmation} {success}" if confirmation and success else confirmation or success

    def _relationship_response(self, execution):
        result = execution.result
        person = self.relationships.people[result.subject]
        return self.response_policy.render(
            execution.operation,
            "success",
            {"person_name": person.name},
        )

    def process(self, text, _add_tcm=True):
        if _add_tcm:
            self.tcm.add(text)
        if self.clarification.has_pending():
            clarification_result = self._handle_pending_clarification(text)
            if clarification_result is not None:
                return clarification_result
        parsed = self.parser.parse(text)
        semantic_context = self.semantic_context.extract(parsed, text)
        if not parsed.question_type:
            self._record_observation(text, parsed)
            ambiguity = self._lexical_ambiguity(parsed, text, semantic_context)
            if ambiguity is not None:
                word, senses = ambiguity
                request = self.clarification.request_lexical_meaning(
                    word,
                    [{"id": sense.sense_id} for sense in senses],
                    text,
                )
                if request is not None:
                    return request.question
        if parsed.question_type:
            return self.response.generate(parsed, self.query.answer(parsed, semantic_context=semantic_context))
        if not parsed.meaning:
            return self.response.system("parse_failure")
        execution = self._execute_statement(parsed, context=semantic_context)
        if execution.clarification:
            self._refresh_graph()
            return execution.clarification
        operation = execution.operation
        if execution.result is None:
            if operation is not None:
                failure = self.response_policy.render(operation, "failure")
                if failure:
                    return failure
            return self.response.system("execution_failure")
        if operation and operation.name == "ASSERT_USER_RELATIONSHIP":
            return self._relationship_response(execution)
        self._refresh_graph()
        success_context = {}
        if parsed.subject_word:
            entity = self.user_memory.canonical_entity(execution.result.subject)
            success_context["subject_name"] = self.user_memory.entities[entity]["name"]
        if parsed.object_word:
            success_context["object_word"] = parsed.object_word
        success = self.response_policy.render(operation, "success", success_context)
        if success:
            return success
        conflict_response = self.response_policy.render(operation, "conflict")
        if execution.result.status == "CONFLICTED" and conflict_response:
            return conflict_response
        return self.response.system("memory_conflict" if execution.result.status == "CONFLICTED" else "execution_failure")


def main():
    slr = SLR(user_id="USER-001")
    print("Structured Language Reasoning V1.0")
    print(f"SLRM Instance: {slr.user_profile.slrm_instance_id}")
    print("Type 'exit' to stop.")
    while True:
        text = input("> ")
        if text.lower() == "exit":
            break
        print(slr.process(text))


if __name__ == "__main__":
    main()
