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

    def process(self, text):
        p = self.parser.parse(text)

        if self.pending_entity and p.verb_word == "instance_of" and p.object_word:
            concept = self.lexicon.concept(p.object_word)
            if concept in self.ontology.classes:
                eid = self._canonical(self.pending_entity)
                self.memory.set_entity_concept(eid, concept)
                tid = self.memory.find_entity(concept)
                self.memory.add_memory(eid, "IS_A", tid)
                self.pending_entity = None
                name = self.memory.entities[eid]["name"]
                return f"Understood. I know that {name} is a {p.object_word}."

        if p.question_type:
            if p.question_type == "TYPE":
                eid = self.memory.find_named_entity(p.subject_word)
                if eid is None:
                    return "I don't know."
                eid = self._canonical(eid)
                concept = self.memory.entities[eid]["concept"]
                if concept == "UNKNOWN":
                    return "I don't know yet."
                return f"{self.memory.entities[eid]['name']} is a {concept.lower()}."
            return self.response.generate(p, self.query.answer(p))

        if not p.subject_word or not p.verb_word:
            return "I could not parse that sentence."

        eid = self._canonical(self._entity_for_word(p.subject_word))
        subject_concept = self.memory.entities[eid]["concept"]

        state_concept = self.lexicon.concept(p.verb_word)
        if p.meaning == "SUBJECT_STATE" and state_concept:
            self.memory.add_memory(eid, state_concept, "TRUE")
            if subject_concept == "UNKNOWN":
                self.pending_entity = eid
                name = self.memory.entities[eid]["name"]
                return f"Who is {name.title()}? I don't know whether {name} is a human, an animal, or something else."
            return "I have stored that state in memory."

        if p.verb_word == "instance_of" and p.object_word:
            concept = self.lexicon.concept(p.object_word)
            if concept not in self.ontology.classes:
                return "I don't know that type yet."
            self.memory.set_entity_concept(eid, concept)
            tid = self.memory.find_entity(concept)
            self.memory.add_memory(eid, "IS_A", tid)
            self.pending_entity = None
            return "I have stored that classification in memory."

        if p.meaning == "SUBJECT_RELATION" and p.object_word:
            oid = self._entity_for_word(p.object_word)
            self.memory.add_identity(eid, oid)
            self.pending_entity = None
            return "I have stored that identity in memory."

        if subject_concept == "UNKNOWN":
            self.pending_entity = eid
            name = self.memory.entities[eid]["name"]
            return f"Who is {name.title()}? I don't know enough about this entity yet."

        oc = self.lexicon.concept(p.object_word) if p.object_word else None
        pred = self.lexicon.concept(p.verb_word)
        if not oc:
            return "I don't understand the object."
        if not pred:
            return "I don't understand the verb."
        oid = self.memory.find_entity(oc)
        if p.negated:
            pred = f"NOT_{pred}"
        if not self.reasoner.validate_relation(eid, pred, oid):
            return "I cannot add that memory because the relationship is inconsistent with my world model."
        m = self.memory.add_memory(eid, pred, oid)
        return "Memory created, but it conflicts with an existing memory." if m.status == "CONFLICTED" else "I have stored that in memory."


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
