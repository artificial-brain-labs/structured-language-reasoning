class QueryEngine:
    def __init__(self, memory, lexicon):
        self.memory = memory
        self.lexicon = lexicon

    def _resolve(self, word):
        concept = self.lexicon.concept(word)
        if concept:
            entity = self.memory.find_entity(concept)
            return entity
        return self.memory.find_named_entity(word)

    def answer(self, parsed):
        if parsed.question_type == "OBJECT":
            subject = self._resolve(parsed.subject_word)
            predicate = self.lexicon.concept(parsed.verb_word)
            if not subject or not predicate:
                return []
            return [
                m.object
                for m in self.memory.query(subject=subject, predicate=predicate)
                if m.status != "CONFLICTED"
            ]

        if parsed.question_type == "SUBJECT":
            object_id = self._resolve(parsed.object_word)
            predicate = self.lexicon.concept(parsed.verb_word)
            if not object_id or not predicate:
                return []
            return [
                m.subject
                for m in self.memory.query(predicate=predicate, object_=object_id)
                if m.status != "CONFLICTED"
            ]

        return []
