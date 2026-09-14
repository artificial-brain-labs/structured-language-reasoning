class QueryEngine:
    def __init__(self, memory, lexicon):
        self.memory = memory
        self.lexicon = lexicon

    def answer(self, parsed):
        if parsed.question_type == "OBJECT":
            subject_concept = self.lexicon.concept(parsed.subject_word)
            predicate = self.lexicon.concept(parsed.verb_word)
            if not subject_concept or not predicate:
                return []
            subject = self.memory.find_entity(subject_concept)
            return [m.object for m in self.memory.query(subject=subject, predicate=predicate)
                    if m.status != "CONFLICTED"]

        if parsed.question_type == "SUBJECT":
            object_concept = self.lexicon.concept(parsed.object_word)
            predicate = self.lexicon.concept(parsed.verb_word)
            if not object_concept or not predicate:
                return []
            object_id = self.memory.find_entity(object_concept)
            return [m.subject for m in self.memory.query(predicate=predicate, object_=object_id)
                    if m.status != "CONFLICTED"]

        return []
