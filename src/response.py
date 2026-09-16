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

    def _proof_text(self, proof):
        if not proof or not proof.get("path"):
            return None
        names = []
        for edge in proof["path"]:
            subject = self.memory.entities.get(edge["subject"], {}).get("name")
            if subject is None:
                subject = edge["subject"]
            object_id = edge["object"]
            object_name = self.memory.entities.get(object_id, {}).get("name")
            if object_name is None:
                object_name = object_id
                if isinstance(object_id, str) and object_id.startswith("concept:"):
                    object_name = object_id.split(":", 1)[1]
            if not names:
                names.append(subject)
            names.append(object_name)
        return " -> ".join(names)

    def generate(self, parsed, results):
        if not results:
            template = self.query_responses.get(parsed.question_type, {})
            return self.system(template.get("unknown_result", "unknown"))

        template = self.query_responses.get(parsed.question_type)
        if template is None:
            return self.system("unknown")

        first = results[0]
        if isinstance(first, dict):
            entity = first.get("entity")
            concept = first.get("object")
            if not entity or entity not in self.memory.entities or not concept:
                return self.system(template.get("unknown_result", "unknown"))
            context = {
                "subject_name": self.memory.entities[entity]["name"],
                "concept": concept.lower(),
                "status": first.get("status", "UNKNOWN"),
                "source": first.get("source", "UNKNOWN"),
            }
            try:
                answer = template.get("success", "").format(**context)
            except (KeyError, ValueError):
                return self.system("unknown")

            proof_template = template.get("explanation")
            reasoning = self._proof_text(first.get("proof"))
            if proof_template and reasoning:
                try:
                    answer = f"{answer} {proof_template.format(reasoning=reasoning)}"
                except (KeyError, ValueError):
                    pass
            return answer

        entity = first
        if entity not in self.memory.entities:
            return self.system(template.get("unknown_result", "unknown"))
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
