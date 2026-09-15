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


class SLR:
    def __init__(self):
        self.lexicon = Lexicon()
        self.ontology = Ontology()
        self.parser = Parser(self.lexicon)
        self.semantic_parser = SemanticParser(self.lexicon)
        self.memory = DynamicMemory()
        self.reasoner = Reasoner(self.ontology, self.memory)
        self.executor = SemanticExecutor(self.memory)
        self.router = StatementRouter()
        self.router.register_all(self.executor.definitions.operations, self._handle_operation)
        self.query = QueryEngine(self.memory, self.lexicon)
        self.response = ResponseGenerator(self.memory)
        self.pending_entity = None

    def _entity_for_word(self, word):
        concept = self.lexicon.concept(word)
        if concept in self.ontology.classes:
            return self.memory.find_entity(concept)
        entity = self.memory.find_named_entity(word)
        return entity or self.memory.create_named_entity(word)

    def _canonical(self, entity_id):
        return self.memory.canonical_entity(entity_id)

    def _handle_operation(self, operation, parsed):
        definition = self.executor.definitions.get(operation.name)
        if definition is None:
            return StatementResult(operation=operation)

        kind = definition.get("kind")
        subject_entity = self._entity_for_word(parsed.subject_word)
        operation.subject = self._canonical(subject_entity)
        subject_concept = self.memory.entities[operation.subject]["concept"]

        if kind == "CLASSIFICATION":
            concept = self.lexicon.concept(parsed.object_word)
            if concept not in self.ontology.classes:
                return StatementResult(operation=operation)

            type_entity = self.memory.find_entity(concept)
            operation.object = type_entity
            result = self.executor.execute(operation)
            if result is not None:
                self.memory.set_entity_concept(operation.subject, concept)
            return StatementResult(result=result, operation=operation)

        if kind == "RELATION":
            relation_schema = self.memory.relations.get(operation.predicate) or {}
            if relation_schema.get("type") == "IDENTITY":
                object_entity = self._entity_for_word(parsed.object_word)
                operation.object = self._canonical(object_entity)
                result = self.executor.execute(operation)
                return StatementResult(result=result, operation=operation)

            if subject_concept == "UNKNOWN":
                self.pending_entity = operation.subject
                name = self.memory.entities[operation.subject]["name"]
                return StatementResult(
                    clarification=f"Who is {name.title()}? I don't know enough about this entity yet.",
                    operation=operation,
                )

            object_concept = self.lexicon.concept(parsed.object_word) if parsed.object_word else None
            if not object_concept:
                return StatementResult(operation=operation)

            object_entity = self.memory.find_entity(object_concept)
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
                self.pending_entity = operation.subject
                name = self.memory.entities[operation.subject]["name"]
                return StatementResult(
                    result=result,
                    clarification=(
                        f"Who is {name.title()}? I don't know whether {name} is a human, "
                        "an animal, or something else."
                    ),
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

    def process(self, text):
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
        if execution.result is None:
            if execution.operation is not None:
                kind = self.executor.definitions.get(execution.operation.name) or {}
                if kind.get("kind") == "CLASSIFICATION":
                    return "I don't know that type yet."
                if (self.memory.relations.get(execution.operation.predicate) or {}).get("type") == "IDENTITY":
                    return "I could not store that identity."
            return "I could not execute that statement."

        if execution.clarification:
            return execution.clarification

        definition = self.executor.definitions.get(execution.operation.name) or {}
        if definition.get("kind") == "CLASSIFICATION":
            self.pending_entity = None
            entity = self._canonical(execution.result.subject)
            name = self.memory.entities[entity]["name"]
            return f"Understood. I know that {name} is a {parsed.object_word}."

        self.pending_entity = None
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
