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
        self.query = QueryEngine(self.memory, self.lexicon)
        self.response = ResponseGenerator(self.memory)
        self.response_policy = ResponsePolicy(self.executor.definitions)

    def _canonical(self, entity_id):
        return self.memory.canonical_entity(entity_id)

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
        if parsed.meaning != "TYPE_ASSIGNMENT":
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

        if original_operation is None or original_context is None:
            return f"Understood. I know that {parsed.subject_word} is a {parsed.object_word}."

        original_operation.subject = self._canonical(entity)
        resumed = self.operation_engine.execute(original_operation, original_context)
        if resumed.result is None:
            return (
                f"Understood. I know that {parsed.subject_word} is a {parsed.object_word}. "
                "I could not validate the earlier statement with that classification."
            )

        if resumed.clarification:
            return resumed.clarification

        return (
            f"Understood. I know that {parsed.subject_word} is a {parsed.object_word}. "
            "I have also stored the earlier statement."
        )

    def process(self, text):
        if self.clarification.has_pending():
            clarification_result = self._handle_pending_clarification(text)
            if clarification_result is not None:
                return clarification_result

        parsed = self.parser.parse(text)

        if parsed.question_type:
            if parsed.question_type == "TYPE":
                entity = self.memory.find_named_entity(parsed.subject_word)
                if entity is None:
                    return "I don't know."
                entity = self._canonical(entity)
                concept = self.memory.entities[entity]["concept"]
                if concept == "UNKNOWN":
                    return "I don't know yet."
                return f"{self.memory.entities[entity]['name']} is a {concept.lower()}."
            return self.response.generate(parsed, self.query.answer(parsed))

        if not parsed.meaning:
            return "I could not parse that sentence."

        execution = self._execute_statement(parsed)

        if execution.clarification:
            return execution.clarification

        operation = execution.operation
        if execution.result is None:
            if operation is not None:
                failure = self.response_policy.render(operation, "failure")
                if failure:
                    return failure
                if (self.memory.relations.get(operation.predicate) or {}).get("type") == "IDENTITY":
                    return "I could not store that identity."
            return "I could not execute that statement."

        success_context = {}
        if parsed.subject_word:
            entity = self._canonical(execution.result.subject)
            success_context["subject_name"] = self.memory.entities[entity]["name"]
        if parsed.object_word:
            success_context["object_word"] = parsed.object_word

        success = self.response_policy.render(operation, "success", success_context)
        if success:
            return success

        conflict = execution.result.status == "CONFLICTED"
        if conflict:
            conflict_response = self.response_policy.render(operation, "conflict")
            if conflict_response:
                return conflict_response
            return "Memory created, but it conflicts with an existing memory."

        return "I have stored that in memory."


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
