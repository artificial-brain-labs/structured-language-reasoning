class EntityResolver:
    """Resolve words to memory entities without inferring unknown types.

    Lexicon and ontology provide knowledge; this component only performs
    resolution mechanics. An unknown named entity is created explicitly as
    UNKNOWN and remains unclassified until confirmed.
    """

    def __init__(self, lexicon, ontology, memory):
        self.lexicon = lexicon
        self.ontology = ontology
        self.memory = memory

    def resolve(self, word):
        concept = self.lexicon.concept(word)
        if concept in self.ontology.classes:
            return self.memory.find_entity(concept)

        entity = self.memory.find_named_entity(word)
        return entity or self.memory.create_named_entity(word)

    def resolve_canonical(self, word):
        return self.memory.canonical_entity(self.resolve(word))

    def resolve_type(self, word):
        """Resolve a word only when the lexicon maps it to an ontology class."""
        concept = self.lexicon.concept(word)
        if concept not in self.ontology.classes:
            return None
        return concept, self.memory.find_entity(concept)

    def concept(self, entity_id):
        return self.memory.entities[entity_id]["concept"]
