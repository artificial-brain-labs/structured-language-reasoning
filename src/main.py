from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .memory import DynamicMemory
from .reasoner import Reasoner
from .query import QueryEngine
from .response import ResponseGenerator
from .semantics import SemanticParser
from .executor import SemanticExecutor
from .statement_router import StatementRouter, StatementResult
from .entity_resolver import EntityResolver
from .clarification_manager import ClarificationManager


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
        self.router = StatementRouter()
        self.router.register_all(self.executor.definitions.operations, self._handle_operation)
        self.clarification = ClarificationManager(self.memory)
        self.query = QueryEngine(self.memory, self.lexicon)
        self.response = ResponseGenerator(self.memory)

    def _canonical(self, entity_id):
        return self.memory.canonical_entity(entity_id)

    def _handle_operation(self, operation, parsed):
        definition = self.executor.definitions.get(operation.name)
        if definition is None:
            return StatementResult(operation=operation)

        kind = definition.get("kind")
        subject_entity = self.resolver.resolve_canonical(parsed.subject_word)
        operation.subject = subject_entity
        subject_concept = self.resolver.concept(operation.subject)

        if kind == "CLASSIFICATION":
            resolved_type = self.resolver.resolve_type(parsed.object_word)
            if resolved_type is None:
                return StatementResult(operation=operation)

            concept, type_entity = resolved_type
            operation.object = type_entity
            result = self.executor.execute(operation)
            if result is not None:
                self.memory.set_entity_concept(operation.subject, concept)
            return StatementResult(result=result, operation=operation)

        if kind == "RELATION":
            relation_schema = self.memory.relations.get(operation.predicate) or {}
            if relation_schema.get("type") == "IDENTITY":
                operation.object = self.resolver.resolve_canonical(parsed.object_word)
                result = self.executor.execute(operation)
                return StatementResult(result=result, operation=operation)

            if subject_concept == "UNKNOWN":
                request = self.clarification.request_entity_identity(
                    operation.subject, operation, parsed
                )
                return StatementResult(
                    clarification=request.question if request else None,
                    operation=operation,
                )

            object_concept = self.lexicon.concept(parsed.object_word) if parsed.object_word else None
            if not object_concept:
                return StatementResult(operation=operation)

            object_entity = self.resolver.resolve_canonical(parsed.object_word)
            if not self.reasoner.validate_relation(
                operation.subject, operation.predicate, object_entity
            ):
                return StatementResult(operation=operation)

            operation.object = object_entity
            result = self.executor.execute(operation)
            return StatementResult(result=result, operation=operation)

        if kind == "FACT":
            result = self.executor.execute(operation)
            if result is not None and subject_concept == "UNKNOWN":
                request = self.clarification.request_entity_identity(
                    operation.subject, operation, parsed
                )
                return StatementResult(
                    result=result,
                    clarification=request.question if request else None,
                    operation=operation,
                )
            return StatementResult(result=result, operation=operation)

        return StatementResult(operation=operation)

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
        resumed = self._handle_operation(original_operation, original_context)
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

        # Clarification is a valid execution outcome: no memory result is
        # expected yet because the operation is intentionally waiting for
        # information. Handle it before treating a missing result as failure.
        if execution.clarification:
            return execution.clarification

        if execution.result is None:
            if execution.operation is not None:
                definition = self.executor.definitions.get(execution.operation.name) or {}
                if definition.get("kind") == "CLASSIFICATION":
                    return "I don't know that type yet."
                if (self.memory.relations.get(execution.operation.predicate) or {}).get("type") == "IDENTITY":
                    return "I could not store that identity."
            return "I could not execute that statement."

        definition = self.executor.definitions.get(execution.operation.name) or {}
        if definition.get("kind") == "CLASSIFICATION":
            entity = self._canonical(execution.result.subject)
            name = self.memory.entities[entity]["name"]
            return f"Understood. I know that {name} is a {parsed.object_word}."

        return (
            "Memory created, but it conflicts with an existing memory."
            if execution.result.status == "CONFLICTED"
            else "I have stored that in memory."
        )


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
