class EntityResolver:
    """Resolve words without inferring unknown types.

    The resolver receives the active USER MEMORY store. Lexicon and ontology
    remain system knowledge and are used only as data for resolution.
    """

    def __init__(self, lexicon, ontology, memory):
        self.lexicon = lexicon
        self.ontology = ontology
        self.memory = memory

    def resolve(self, word):
        concept = self.lexicon.concept(word)
        if concept in self.ontology.classes:
            # Class nodes are references to system ontology concepts. Creating
            # a local node is not user knowledge; it is only a graph handle
            # needed to represent an explicit user assertion such as IS_A.
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
