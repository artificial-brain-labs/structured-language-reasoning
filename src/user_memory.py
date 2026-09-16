from .memory import DynamicMemory


class UserMemory(DynamicMemory):
    """Per-user memory for explicitly provided or explicitly confirmed facts.

    System knowledge (lexicon, ontology, grammar, relation definitions) is
    never written here. This store contains user-specific entities and
    asserted memories only. Derived knowledge remains transient in the
    reasoner and is never promoted automatically.
    """

    def add_memory(self, subject, predicate, object_, source="USER", confidence=1.0):
        return super().add_memory(subject, predicate, object_, source, confidence)

    def set_entity_concept(self, entity_id, concept):
        """Disabled: explicit classification is stored as IS_A evidence."""
        raise ValueError(
            "UserMemory does not mutate entity concepts; store explicit IS_A evidence instead."
        )
