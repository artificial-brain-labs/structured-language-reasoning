from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .memory import DynamicMemory
from .reasoner import Reasoner
from .query import QueryEngine
from .response import ResponseGenerator
from .semantics import SemanticParser
from .executor import SemanticExecutor


class SLR:
    def __init__(self):
        self.lexicon = Lexicon()
        self.ontology = Ontology()
        self.parser = Parser(self.lexicon)
        self.semantic_parser = SemanticParser(self.lexicon)
        self.memory = DynamicMemory()
        self.reasoner = Reasoner(self.ontology, self.memory)
        self.executor = SemanticExecutor(self.memory)
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

    def _store_classification(self, entity_id, concept):
        entity_id = self._canonical(entity_id)
        self.memory.set_entity_concept(entity_id, concept)
        type_entity = self.memory.find_entity(concept)
        relation_name = self.reasoner.relation_name_for_type("TAXONOMIC")
        if relation_name:
            self.memory.add_memory(entity_id, relation_name, type_entity)

    def _execute_statement(self, parsed):
        meaning = self.semantic_parser.parse(parsed)
        operation = meaning.operation
        if operation is None:
            return None

        if operation.name == "ASSERT_STATE":
            subject_entity = self._entity_for_word(parsed.subject_word)
            operation.subject = self._canonical(subject_entity)
            result = self.executor.execute(operation)
            return result

        if operation.name == "ASSERT_RELATION":
            subject_entity = self._entity_for_word(parsed.subject_word)
            operation.subject = self._canonical(subject_entity)

            if parsed.meaning == "SUBJECT_RELATION":
                object_entity = self._entity_for_word(parsed.object_word)
                operation.object = self._canonical(object_entity)
                operation.predicate = parsed.relation
                return self.executor.execute(operation)

            object_concept = self.lexicon.concept(parsed.object_word) if parsed.object_word else None
            if not object_concept:
                return None
            object_entity = self.memory.find_entity(object_concept)
            if parsed.negated:
                schema = self.reasoner.schemas.get(operation.predicate) or {}
                operation.predicate = schema.get("opposite")
                if not operation.predicate:
                    return None
            if not self.reasoner.validate_relation(operation.subject, operation.predicate, object_entity):
                return None
            operation.object = object_entity
            return self.executor.execute(operation)

        if operation.name == "ASSERT_CLASSIFICATION":
            concept = self.lexicon.concept(parsed.object_word)
            if concept not in self.ontology.classes:
                return None
            subject_entity = self._entity_for_word(parsed.subject_word)
            operation.subject = self._canonical(subject_entity)
            operation.predicate = parsed.relation
            type_entity = self.memory.find_entity(concept)
            operation.object = type_entity
            result = self.executor.execute(operation)
            if result is not None:
                self.memory.set_entity_concept(operation.subject, concept)
            return result

        return None

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

        if parsed.meaning in {"SUBJECT_STATE", "SUBJECT_VERB_OBJECT", "TYPE_ASSIGNMENT", "SUBJECT_RELATION"}:
            result = self._execute_statement(parsed)
            if result is None:
                if parsed.meaning == "TYPE_ASSIGNMENT":
                    return "I don't know that type yet."
                if parsed.meaning == "SUBJECT_RELATION":
                    return "I could not store that identity."
                return "I could not execute that statement."

            if parsed.meaning == "TYPE_ASSIGNMENT":
                self.pending_entity = None
                entity = self._canonical(result.subject)
                name = self.memory.entities[entity]["name"]
                return f"Understood. I know that {name} is a {parsed.object_word}."

            self.pending_entity = None
            return "I have stored that in memory."

        return "I could not parse that sentence."


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
