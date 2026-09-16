from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .memory import DynamicMemory
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


class SLR:
    def __init__(self):
        self.lexicon = Lexicon()
        self.ontology = Ontology()
        self.parser = Parser(self.lexicon)
        self.semantic_parser = SemanticParser(self.lexicon)
        self.memory = DynamicMemory()
        self.reasoner = Reasoner(self.ontology, self.memory)
        self.executor = SemanticExecutor(self.memory)
        self.resolver = EntityResolver(self.lexicon, self.ontology, self.memory)
        self.clarification = ClarificationManager(self.memory)
        self.clarification_policy = ClarificationPolicy()
        self.operation_engine = OperationEngine(
            self.executor.definitions,
            self.resolver,
            self.reasoner,
            self.executor,
            self.memory,
            self.lexicon,
            self.clarification,
        )
        self.router = StatementRouter()
        self.router.register_all(self.executor.definitions.operations, self.operation_engine.execute)
        self.query = QueryEngine(self.memory, self.lexicon, self.reasoner)
        self.response = ResponseGenerator(self.memory)
        self.response_policy = ResponsePolicy(self.executor.definitions)

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

        entity = self.resolver.resolve_canonical(parsed.subject_word)
        if not self.clarification.matches_entity(entity):
            return None

        execution = self._execute_statement(parsed)
        if execution.result is None:
            return None

        original_operation = request.original_operation
        original_context = request.original_context
        self.clarification.clear()

        confirmation_context = {
            "subject_name": parsed.subject_word,
            "object_word": parsed.object_word,
        }
        confirmation = self.response_policy.render(
            execution.operation, "success", confirmation_context
        )
        if original_operation is None or original_context is None:
            return confirmation

        original_operation.subject = self.memory.canonical_entity(entity)
        resumed = self.operation_engine.execute(original_operation, original_context)
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

        success_context = {}
        if parsed.subject_word:
            entity = self.memory.canonical_entity(execution.result.subject)
            success_context["subject_name"] = self.memory.entities[entity]["name"]
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
