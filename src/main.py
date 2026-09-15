from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .memory import DynamicMemory
from .reasoner import Reasoner
from .query import QueryEngine
from .response import ResponseGenerator


class SLR:
    def __init__(self):
        self.lexicon = Lexicon()
        self.ontology = Ontology()
        self.parser = Parser(self.lexicon)
        self.memory = DynamicMemory()
        self.reasoner = Reasoner(self.ontology, self.memory)
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
        relation = self.reasoner.schemas.get("IS_A")
        relation_name = next(
            (name for name, schema in self.reasoner.schemas.schemas.items() if schema is relation),
            "IS_A",
        )
        self.memory.add_memory(entity_id, relation_name, type_entity)

    def process(self, text):
        parsed = self.parser.parse(text)

        if parsed.meaning == "TYPE_ASSIGNMENT" and parsed.object_word:
            concept = self.lexicon.concept(parsed.object_word)
            if concept not in self.ontology.classes:
                return "I don't know that type yet."

            subject_entity = self._entity_for_word(parsed.subject_word)
            self._store_classification(subject_entity, concept)
            self.pending_entity = None
            entity = self._canonical(subject_entity)
            name = self.memory.entities[entity]["name"]
            return f"Understood. I know that {name} is a {parsed.object_word}."

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

        if not parsed.subject_word or not parsed.verb_word:
            return "I could not parse that sentence."

        subject_entity = self._entity_for_word(parsed.subject_word)

        if parsed.meaning == "SUBJECT_RELATION" and parsed.object_word:
            object_entity = self._entity_for_word(parsed.object_word)
            relation = parsed.relation
            if not relation:
                return "I don't understand that relationship."
            self.memory.add_memory(subject_entity, relation, object_entity)
            schema = self.reasoner.schemas.get(relation) or {}
            if schema.get("symmetric"):
                self.memory.add_memory(object_entity, relation, subject_entity)
            self.pending_entity = None
            return "I have stored that identity in memory."

        entity = self._canonical(subject_entity)
        subject_concept = self.memory.entities[entity]["concept"]

        if parsed.meaning == "SUBJECT_STATE":
            state_concept = self.lexicon.concept(parsed.verb_word)
            if not state_concept:
                return "I don't understand the state."
            self.memory.add_memory(entity, state_concept, "TRUE")
            if subject_concept == "UNKNOWN":
                self.pending_entity = entity
                name = self.memory.entities[entity]["name"]
                return f"Who is {name.title()}? I don't know whether {name} is a human, an animal, or something else."
            return "I have stored that state in memory."

        if subject_concept == "UNKNOWN":
            self.pending_entity = entity
            name = self.memory.entities[entity]["name"]
            return f"Who is {name.title()}? I don't know enough about this entity yet."

        object_concept = self.lexicon.concept(parsed.object_word) if parsed.object_word else None
        predicate = self.lexicon.concept(parsed.verb_word)
        if not object_concept:
            return "I don't understand the object."
        if not predicate:
            return "I don't understand the verb."

        if parsed.negated:
            schema = self.reasoner.schemas.get(predicate) or {}
            predicate = schema.get("opposite")
            if not predicate:
                return "I don't know the negated form of that relationship."

        object_entity = self.memory.find_entity(object_concept)
        if not self.reasoner.validate_relation(entity, predicate, object_entity):
            return "I cannot add that memory because the relationship is inconsistent with my world model."
        memory = self.memory.add_memory(entity, predicate, object_entity)
        return (
            "Memory created, but it conflicts with an existing memory."
            if memory.status == "CONFLICTED"
            else "I have stored that in memory."
        )


def main():
    slr = SLR()
    print("Structured Language Reasoning V0.4")
    print("Type 'exit' to stop.")
    while True:
        text = input("> ")
        if text.lower() == "exit":
            break
        print(slr.process(text))


if __name__ == "__main__":
    main()
