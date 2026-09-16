import json
from pathlib import Path


class QueryEngine:
    def __init__(self, memory, lexicon, reasoner=None, policy_path=None):
        self.memory = memory
        self.lexicon = lexicon
        self.reasoner = reasoner
        path = policy_path or Path(__file__).resolve().parent.parent / "knowledge" / "query_policy.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.policy = data.get("question_types", {})

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
        return self.lexicon.feature(word, "relation") or self.lexicon.concept(word)

    def _classification(self, parsed):
        """Return asserted or derived type evidence without mutating memory."""
        subject = self._resolve(parsed.subject_word)
        target_concept = self.lexicon.concept(parsed.object_word)
        if subject is None or target_concept is None:
            return []

        target_entity = self.memory.find_entity(target_concept)
        asserted_classifications = [
            memory
            for memory in self.memory.query(subject=subject, predicate="IS_A")
            if memory.status == "ASSERTED"
            and self._canonical_id(memory.object) == target_entity
        ]
        if asserted_classifications:
            memory = asserted_classifications[0]
            return [{
                "entity": subject,
                "predicate": "IS_A",
                "object": target_concept,
                "status": "ASSERTED",
                "source": memory.source,
                "support": [memory],
            }]

        subject_concept = self.memory.entities[subject]["concept"]

        if subject_concept == target_concept:
            return [{
                "entity": subject,
                "predicate": "IS_A",
                "object": target_concept,
                "status": "ASSERTED",
                "source": "MEMORY",
                "support": [subject],
            }]

        if self.reasoner is not None:
            for derived in self.reasoner.infer_is_a(subject):
                if derived["object"] == target_concept:
                    return [derived]

            for memory in self.memory.query(subject=subject, predicate="IS_A"):
                if memory.status != "ASSERTED":
                    continue
                source_concept = self.memory.entities.get(memory.object, {}).get("concept")
                if source_concept and self.reasoner.ontology.is_a(source_concept, target_concept):
                    return [{
                        "entity": subject,
                        "predicate": "IS_A",
                        "object": target_concept,
                        "status": "DERIVED",
                        "source": "ONTOLOGY",
                        "support": [memory],
                    }]

            for derived in self.reasoner.derive():
                if (
                    derived["subject"] == subject
                    and derived["predicate"] == "IS_A"
                    and self._canonical_id(derived["object"]) == target_entity
                ):
                    return [derived]

            if subject_concept != "UNKNOWN" and self.reasoner.ontology.is_a(subject_concept, target_concept):
                return [{
                    "entity": subject,
                    "predicate": "IS_A",
                    "object": target_concept,
                    "status": "DERIVED",
                    "source": "ONTOLOGY",
                    "support": [subject_concept],
                }]

        return []

    def _entity_type(self, parsed):
        """Return the entity's explicit user classification without mutation.

        Identity is resolved first, so a name such as Tom can inherit an
        explicitly asserted classification stored for Dom when Tom IS Dom.
        No ontology-derived type is promoted to asserted user knowledge.
        """
        entity = self._resolve(parsed.subject_word)
        if entity is None:
            return []

        for memory in self.memory.query(subject=entity, predicate="IS_A"):
            if memory.status != "ASSERTED":
                continue
            object_entity = self._canonical_id(memory.object)
            concept = self.memory.entities.get(object_entity, {}).get("concept")
            if concept and concept != "UNKNOWN":
                return [{
                    "entity": entity,
                    "predicate": "IS_A",
                    "object": concept,
                    "status": "ASSERTED",
                    "source": memory.source,
                    "support": [memory],
                }]

        return []

    def answer(self, parsed):
        policy = self.policy.get(parsed.question_type)
        if policy is None:
            return []

        result_kind = policy.get("result_kind")
        if result_kind == "classification":
            return self._classification(parsed)

        if result_kind == "entity_type":
            return self._entity_type(parsed)

        if result_kind == "object":
            subject = self._resolve(parsed.subject_word)
            predicate = self._relation(parsed.verb_word)
            if not subject or not predicate:
                return []
            return [
                self._canonical_id(m.object)
                for m in self.memory.query(subject=subject, predicate=predicate)
                if m.status != "CONFLICTED"
            ]

        if result_kind == "subject":
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
