from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .memory import DynamicMemory
from .reasoner import Reasoner
from .query import QueryEngine
from .response import ResponseGenerator

class SLR:
    def __init__(self):
        self.lexicon=Lexicon(); self.ontology=Ontology(); self.parser=Parser()
        self.memory=DynamicMemory(); self.reasoner=Reasoner(self.ontology,self.memory)
        self.query=QueryEngine(self.memory,self.lexicon); self.response=ResponseGenerator(self.memory)
        self.pending_entity=None

    def process(self,text):
        p=self.parser.parse(text)
        # Answer to a pending clarification: "Tom is a cat" / "Tom is my cat".
        if self.pending_entity and p.verb_word=="instance_of" and p.object_word:
            concept=self.lexicon.concept(p.object_word)
            if concept in self.ontology.classes:
                eid=self.pending_entity; self.memory.set_entity_concept(eid,concept)
                tid=self.memory.find_entity(concept); self.memory.add_memory(eid,"IS_A",tid)
                self.pending_entity=None
                return f"Understood. I know that {self.memory.entities[eid]['name']} is a {p.object_word}."

        if p.question_type:
            return self.response.generate(p,self.query.answer(p))
        if not p.subject_word or not p.verb_word:
            return "I could not parse that sentence."

        eid=self.memory.find_named_entity(p.subject_word)
        if eid is None: eid=self.memory.create_named_entity(p.subject_word)

        # A state is valid knowledge even when the entity's type is unknown.
        if p.verb_word=="sleeping" and not p.object_word:
            self.memory.add_memory(eid,"SLEEPING","TRUE")
            if self.memory.entities[eid]["concept"]=="UNKNOWN":
                self.pending_entity=eid
                return f"Who is {p.subject_word}? I don't know whether {p.subject_word} is a human, an animal, or something else."
            return "I have stored that in memory."

        if p.verb_word=="instance_of" and p.object_word:
            concept=self.lexicon.concept(p.object_word)
            if concept not in self.ontology.classes: return "I don't know that type yet."
            self.memory.set_entity_concept(eid,concept); tid=self.memory.find_entity(concept)
            self.memory.add_memory(eid,"IS_A",tid); self.pending_entity=None
            return "I have stored that classification in memory."

        subject_concept=self.memory.entities[eid]["concept"]
        if subject_concept=="UNKNOWN":
            self.pending_entity=eid
            return f"Who is {p.subject_word}? I don't know enough about this entity yet."
        oc=self.lexicon.concept(p.object_word) if p.object_word else None
        pred=self.lexicon.concept(p.verb_word)
        if not oc: return "I don't understand the object."
        if not pred: return "I don't understand the verb."
        oid=self.memory.find_entity(oc)
        if p.negated: pred=f"NOT_{pred}"
        if not self.reasoner.validate_relation(eid,pred,oid):
            return "I cannot add that memory because the relationship is inconsistent with my world model."
        m=self.memory.add_memory(eid,pred,oid)
        return "Memory created, but it conflicts with an existing memory." if m.status=="CONFLICTED" else "I have stored that in memory."

def main():
    slr=SLR(); print("Structured Language Reasoning V0.3"); print("Type 'exit' to stop.")
    while True:
        text=input("> ")
        if text.lower()=="exit": break
        print(slr.process(text))

if __name__=="__main__": main()