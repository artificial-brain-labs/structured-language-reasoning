from .memory import DynamicMemory
from .evidence import EvidenceStore


class UserMemory(DynamicMemory):
    """Per-user memory for explicitly provided or explicitly confirmed facts.

    System knowledge (lexicon, ontology, grammar, relation definitions) is
    never written here. This store contains user-specific entities and
    asserted memories only. Derived knowledge remains transient in the
    reasoner and is never promoted automatically.

    V0.9 adds an epistemic evidence ledger. Assertions stored here are backed
    by explicit user evidence; observations, interpretations, derivations and
    hypotheses can be recorded without becoming asserted memory.
    """

    def __init__(self, relation_schema=None):
        super().__init__(relation_schema=relation_schema)
        self.evidence = EvidenceStore()

    def add_memory(self, subject, predicate, object_, source="USER", confidence=1.0):
        memory = super().add_memory(subject, predicate, object_, source, confidence)
        if memory is not None and memory.status == "ASSERTED":
            self.evidence.assert_explicit(
                subject=memory.subject,
                predicate=memory.predicate,
                object=memory.object,
                source=source,
            )
        return memory

    def record_observation(self, subject=None, predicate=None, object=None, source="USER", content=None):
        return self.evidence.observe(subject, predicate, object, source, content=content)

    def record_interpretation(self, subject=None, predicate=None, object=None, support=(), source="SYSTEM"):
        return self.evidence.interpret(subject, predicate, object, support, source)

    def record_derivation(self, subject=None, predicate=None, object=None, support=(), source="REASONER"):
        return self.evidence.derive(subject, predicate, object, support, source)

    def record_hypothesis(self, subject=None, predicate=None, object=None, support=(), source="REASONER"):
        return self.evidence.hypothesize(subject, predicate, object, support, source)

    def set_entity_concept(self, entity_id, concept):
        """Disabled: explicit classification is stored as IS_A evidence."""
        raise ValueError(
            "UserMemory does not mutate entity concepts; store explicit IS_A evidence instead."
        )
