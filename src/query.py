class QueryEngine:
    def __init__(self, memory, lexicon):
        self.memory = memory
        self.lexicon = lexicon

    def _resolve(self, word):
        concept = self.lexicon.concept(word)
        if concept:
            entity = self.memory.find_entity(concept)
        else:
            entity = self.memory.find_named_entity(word)
        return self.memory.canonical_entity(entity) if entity else None

    def _canonical_id(self, entity_id):
        return self.memory.canonical_entity(entity_id)

    def _relation(self, word):
        """Resolve a lexical verb to its declarative semantic relation."""
        return self.lexicon.feature(word, "relation") or self.lexicon.concept(word)

    def answer(self, parsed):
        if parsed.question_type == "TYPE":
            entity = self.memory.find_named_entity(parsed.subject_word)
            if entity is None:
                return []
            entity = self._canonical_id(entity)
            concept = self.memory.entities[entity]["concept"]
            if concept == "UNKNOWN":
                return []
            return [entity]

        if parsed.question_type == "OBJECT":
            subject = self._resolve(parsed.subject_word)
            predicate = self._relation(parsed.verb_word)
            if not subject or not predicate:
                return []
            return [
                self._canonical_id(m.object)
                for m in self.memory.query(subject=subject, predicate=predicate)
                if m.status != "CONFLICTED"
            ]

        if parsed.question_type == "SUBJECT":
            object_id = self._resolve(parsed.object_word)
            predicate = self._relation(parsed.verb_word)
            if not object_id or not predicate:
                return []
            return [
                self._canonical_id(m.subject)
                for m in self.memory.query(predicate=predicate)
                if self._canonical_id(m.object) == object_id and m.status != "CONFLICTED"
            ]

        return []
