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
        self.memory.set_entity_concept(entity_id, concept)
        type_entity = self.memory.find_entity(concept)
        relation = "IS_A"
        self.memory.add_memory(entity_id, relation, type_entity)

    def process(self, text):
        p = self.parser.parse(text)

        if p.meaning == "TYPE_ASSIGNMENT" and p.object_word:
            concept = self.lexicon.concept(p.object_word)
            if concept not in self.ontology.classes:
                return "I don't know that type yet."

            entity = self._canonical(self._entity_for_word(p.subject_word))
            self._store_classification(entity, concept)
            self.pending_entity = None
            name = self.memory.entities[entity]["name"]
            return f"Understood. I know that {name} is a {p.object_word}."

        if p.question_type:
            if p.question_type == "TYPE":
                entity = self.memory.find_named_entity(p.subject_word)
                if entity is None:
                    return "I don't know."
                entity = self._canonical(entity)
                concept = self.memory.entities[entity]["concept"]
                if concept == "UNKNOWN":
                    return "I don't know yet."
                return f"{self.memory.entities[entity]['name']} is a {concept.lower()}."
            return self.response.generate(p, self.query.answer(p))

        if not p.subject_word or not p.verb_word:
            return "I could not parse that sentence."

        entity = self._canonical(self._entity_for_word(p.subject_word))
        subject_concept = self.memory.entities[entity]["concept"]

        if p.meaning == "SUBJECT_STATE":
            state_concept = self.lexicon.concept(p.verb_word)
            if not state_concept:
                return "I don't understand the state."
            self.memory.add_memory(entity, state_concept, "TRUE")
            if subject_concept == "UNKNOWN":
                self.pending_entity = entity
                name = self.memory.entities[entity]["name"]
                return f"Who is {name.title()}? I don't know whether {name} is a human, an animal, or something else."
            return "I have stored that state in memory."

        if p.meaning == "SUBJECT_RELATION" and p.object_word:
            object_entity = self._entity_for_word(p.object_word)
            if not p.relation:
                return "I don't understand that relationship."
            self.memory.add_identity(entity, object_entity)
            self.pending_entity = None
            return "I have stored that identity in memory."

        if subject_concept == "UNKNOWN":
            self.pending_entity = entity
            name = self.memory.entities[entity]["name"]
            return f"Who is {name.title()}? I don't know enough about this entity yet."

        object_concept = self.lexicon.concept(p.object_word) if p.object_word else None
        predicate = self.lexicon.concept(p.verb_word)
        if not object_concept:
            return "I don't understand the object."
        if not predicate:
            return "I don't understand the verb."

        object_entity = self.memory.find_entity(object_concept)
        if p.negated:
            predicate = f"NOT_{predicate}"
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
