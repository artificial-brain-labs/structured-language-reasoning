class ResponseGenerator:
    def __init__(self, memory):
        self.memory = memory

    def entity_name(self, entity_id):
        return self.memory.entities[entity_id]["concept"].lower()

    def generate(self, parsed, results):
        if not results:
            return "I don't know."

        if parsed.question_type == "OBJECT":
            return f"The {parsed.subject_word} {parsed.verb_word} the {self.entity_name(results[0])}."

        if parsed.question_type == "SUBJECT":
            return f"The {self.entity_name(results[0])} {parsed.verb_word} the {parsed.object_word}."

        return "I don't know."
