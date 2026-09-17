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
            if hasattr(edge, "subject") and hasattr(edge, "object"):
                subject_id = edge.subject
                object_id = edge.object
            else:
                subject_id = edge["subject"]
                object_id = edge["object"]

            subject = self.memory.entities.get(subject_id, {}).get("name")
            if subject is None:
                subject = subject_id

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
        if isinstance(first, dict) and first.get("kind") == "LEXICAL_AMBIGUITY":
            senses = first.get("senses", [])
            descriptions = []
            for sense in senses:
                definition = sense.get("definition") or sense.get("concept") or "unknown meaning"
                descriptions.append(f'{sense.get("id", "sense")}: {definition}')
            return f"{first.get('word')} has multiple dictionary meanings: " + "; ".join(descriptions)
        if isinstance(first, dict) and first.get("relation"):
            # Relationship knowledge is not an ontology classification. It is
            # returned separately so the response does not turn FRIEND/KNOWS
            # into guessed semantic types.
            context = {
                "subject_name": first.get("person_name") or parsed.subject_surface_word or parsed.subject_word,
                "relation": first["relation"].lower(),
                "status": first.get("status", "UNKNOWN"),
            }
            try:
                return template.get("relationship_success", "{subject_name} is your {relation}.").format(**context)
            except (KeyError, ValueError):
                return self.system("unknown")

        if isinstance(first, dict):
            entity = first.get("entity")
            concept = first.get("object")
            if not entity or entity not in self.memory.entities or not concept:
                return self.system(template.get("unknown_result", "unknown"))
            # Use the name the user actually queried when it resolves to the
            # same canonical entity. This preserves aliases such as Tom -> Dom
            # without changing the underlying canonical identity.
            queried_name = getattr(parsed, "subject_surface_word", None)
            subject_name = self.memory.entities[entity]["name"]
            if queried_name:
                queried_entity = self.memory.find_named_entity(queried_name)
                if queried_entity is not None and self.memory.canonical_entity(queried_entity) == entity:
                    subject_name = queried_name
            context = {
                "subject_name": subject_name,
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

        context = {
            "subject_name": self.memory.entities[entity]["name"],
            "concept": self.memory.entities[entity]["concept"].lower(),
            "result_name": self.entity_name(entity),
            "subject_word": parsed.subject_word or "",
            "verb_word": parsed.verb_word or "",
            "object_word": parsed.object_word or "",
        }
        try:
            return template.get("success", "").format(**context)
        except (KeyError, ValueError):
            return self.system("unknown")
