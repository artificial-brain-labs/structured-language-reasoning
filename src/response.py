import json
from pathlib import Path


class ResponseGenerator:
    def __init__(self, memory, policy_path=None):
        self.memory = memory
        path = policy_path or Path(__file__).resolve().parent.parent / "knowledge" / "responses.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.system_responses = data.get("system", {})
        self.query_responses = data.get("queries", {})

    def entity_name(self, entity_id):
        return self.memory.entities[entity_id]["name"]

    def system(self, name, context=None):
        template = self.system_responses.get(name)
        if template is None:
            return None
        try:
            return template.format(**(context or {}))
        except (KeyError, ValueError):
            return None

    def generate(self, parsed, results):
        if not results:
            return self.system("unknown")

        template = self.query_responses.get(parsed.question_type)
        if template is None:
            return self.system("unknown")

        entity = results[0]
        concept = self.memory.entities[entity]["concept"]
        if concept == "UNKNOWN":
            return self.system(template.get("unknown_result", "unknown"))

        context = {
            "subject_name": self.memory.entities[entity]["name"],
            "concept": concept.lower(),
            "result_name": self.entity_name(entity),
            "subject_word": parsed.subject_word or "",
            "verb_word": parsed.verb_word or "",
            "object_word": parsed.object_word or "",
        }
        try:
            return template.get("success", "").format(**context)
        except (KeyError, ValueError):
            return self.system("unknown")
