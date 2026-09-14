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
        self.parser = Parser()
        self.memory = DynamicMemory()
        self.reasoner = Reasoner(self.ontology, self.memory)
        self.query = QueryEngine(self.memory, self.lexicon)
        self.response = ResponseGenerator(self.memory)

    def process(self, text):
        parsed = self.parser.parse(text)

        if parsed.question_type:
            results = self.query.answer(parsed)
            return self.response.generate(parsed, results)

        if not parsed.subject_word or not parsed.verb_word or not parsed.object_word:
            return "I could not parse that sentence."

        subject_concept = self.lexicon.concept(parsed.subject_word)
        object_concept = self.lexicon.concept(parsed.object_word)
        predicate = self.lexicon.concept(parsed.verb_word)

        if not subject_concept:
            return "I don't understand the subject."
        if not object_concept:
            return "I don't understand the object."
        if not predicate:
            return "I don't understand the verb."

        subject = self.memory.find_entity(subject_concept)
        object_id = self.memory.find_entity(object_concept)

        if parsed.negated:
            predicate = f"NOT_{predicate}"

        if not self.reasoner.validate_relation(subject, predicate, object_id):
            return "I cannot add that memory because the relationship is inconsistent with my world model."

        memory = self.memory.add_memory(subject, predicate, object_id)

        if memory.status == "CONFLICTED":
            return "Memory created, but it conflicts with an existing memory."

        return "I have stored that in memory."

def main():
    slr = SLR()
    print("Structured Language Reasoning V0.2")
    print("Type 'exit' to stop.")
    while True:
        text = input("> ")
        if text.lower() == "exit":
            break
        print(slr.process(text))

if __name__ == "__main__":
    main()
