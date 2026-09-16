from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .memory import DynamicMemory
from .user_memory import UserMemory
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
from .graph_builder import SemanticGraphBuilder


class SLR:
    def __init__(self):
        self.lexicon = Lexicon()
        self.ontology = Ontology()
        self.parser = Parser(self.lexicon)
        self.semantic_parser = SemanticParser(self.lexicon)

        # System memory is reserved for system/runtime knowledge. User facts
        # are isolated in a per-instance USER MEMORY store.
        self.memory = DynamicMemory()
        self.user_memory = UserMemory()

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
        )
        self.router = StatementRouter()
        self.router.register_all(self.executor.definitions.operations, self.operation_engine.execute)
        self.query = QueryEngine(self.user_memory, self.lexicon, self.reasoner)
        self.response = ResponseGenerator(self.user_memory)
        self.response_policy = ResponsePolicy(self.executor.definitions)

        # V0.5: the semantic graph is a representation/projection layer. It is
        # rebuilt from USER MEMORY and never becomes a second source of truth.
        self.graph_builder = SemanticGraphBuilder()
        self.graph = SemanticGraph()
        self._refresh_graph()

    def _refresh_graph(self):
        derived = list(self.reasoner.derive())
        for entity_id in self.user_memory.entities:
            derived.extend(self.reasoner.infer_is_a(entity_id))
        self.graph = self.graph_builder.build(self.user_memory, derived=derived)

    def _execute_statement(self, parsed):
        meaning = self.semantic_parser.parse(parsed)
        operation = meaning.operation
        if operation is None:
            return StatementResult()
        return self.router.dispatch(operation, parsed)

    def _handle_pending_clarification(self, text):
        request = self.clarification.current()
        if request is None:
            return None

        parsed = self.parser.parse(text)
        accepted_meanings = self.clarification_policy.accepted_meanings("entity_identity")
        if parsed.meaning not in accepted_meanings:
            return None

        pending_entity = request.entity_id
        pending_name = self.user_memory.entities[pending_entity]["name"]
        if parsed.subject_word.lower() != pending_name.lower():
            return None

        # Execute the explicit clarification directly against the existing
        # pending entity. Do not re-resolve it through a fresh semantic entity
        # path: clarification is binding information for that exact node.
        meaning = self.semantic_parser.parse(parsed)
        classification_operation = meaning.operation
        if classification_operation is None:
            return None
        classification_operation.subject = pending_entity
        execution = self.operation_engine.execute(classification_operation, parsed)
        if execution.result is None:
            return None

        original_operation = request.original_operation
        original_context = request.original_context
        self.clarification.clear()

        confirmation_context = {
            "subject_name": pending_name,
            "object_word": parsed.object_word,
        }
        confirmation = self.response_policy.render(
            execution.operation, "success", confirmation_context
        )
        if original_operation is None or original_context is None:
            self._refresh_graph()
            return confirmation

        # Rebind the deferred operation to the same user-memory entity after
        # its explicit classification has been recorded.
        original_operation.subject = self.user_memory.canonical_entity(pending_entity)
        resumed = self.operation_engine.execute(original_operation, original_context)
        self._refresh_graph()
        if resumed.result is None:
            return self.response.system("classification_resumed_failure", confirmation_context)

        if resumed.clarification:
            return resumed.clarification

        success = self.response.system("classification_resumed_success")
        return f"{confirmation} {success}" if confirmation and success else confirmation or success

    def process(self, text):
        if self.clarification.has_pending():
            clarification_result = self._handle_pending_clarification(text)
            if clarification_result is not None:
                return clarification_result

        parsed = self.parser.parse(text)

        if parsed.question_type:
            return self.response.generate(parsed, self.query.answer(parsed))

        if not parsed.meaning:
            return self.response.system("parse_failure")

        execution = self._execute_statement(parsed)

        if execution.clarification:
            return execution.clarification

        operation = execution.operation
        if execution.result is None:
            if operation is not None:
                failure = self.response_policy.render(operation, "failure")
                if failure:
                    return failure
            return self.response.system("execution_failure")

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
    slr = SLR()
    print("Structured Language Reasoning V0.5")
    print("Type 'exit' to stop.")
    while True:
        text = input("> ")
        if text.lower() == "exit":
            break
        print(slr.process(text))


if __name__ == "__main__":
    main()
