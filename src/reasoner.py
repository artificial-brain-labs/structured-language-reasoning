from .inference_rules import InferenceRules


class Reasoner:
    def __init__(self, ontology, memory, inference_rules=None):
        self.ontology = ontology
        self.memory = memory
        self.inference_rules = inference_rules or InferenceRules()

    def relation_name_for_role(self, role):
        """Resolve a relation role using explicit declarative priority.

        A unique highest-priority declaration wins. Ties remain unresolved
        rather than being decided by dictionary insertion order.
        """
        candidates = [
            (schema.get("priority", 0), name)
            for name, schema in self.memory.relations.schemas.items()
            if schema.get("role") == role
        ]
        if not candidates:
            return None

        highest = max(priority for priority, _ in candidates)
        matches = [name for priority, name in candidates if priority == highest]
        return matches[0] if len(matches) == 1 else None

    def validate_relation(self, subject_entity, predicate, object_entity):
        schema = self.memory.relations.get(predicate)
        if not schema:
            return False

        subject_concept = self.memory.entities[subject_entity]["concept"]
        object_concept = self.memory.entities[object_entity]["concept"]

        required_subject = schema.get("subject_type")
        required_object = schema.get("object_type")

        if required_subject and not self.ontology.is_a(subject_concept, required_subject):
            return False
        if required_object and not self.ontology.is_a(object_concept, required_object):
            return False
        return True

    def infer_is_a(self, entity_id):
        """Return ontology-derived classifications without storing them."""
        if entity_id not in self.memory.entities:
            return []
        concept = self.memory.entities[entity_id]["concept"]
        relation_name = self.relation_name_for_role("canonical_taxonomic")
        if not relation_name:
            return []
        return [
            {
                "entity": entity_id,
                "predicate": relation_name,
                "object": ancestor,
                "status": "DERIVED",
                "source": "ONTOLOGY",
                "support": [concept],
            }
            for ancestor in self.ontology.ancestors(concept)
        ]

    def derive(self):
        """Compute declarative inference results without mutating memory.

        Derived facts are returned separately from asserted memory. No rule
        invents facts: every result is supported by an explicit rule and
        existing knowledge.
        """
        derived = []
        for rule in self.inference_rules.enabled():
            rule_type = rule.get("type")
            relation = rule.get("relation")
            target = (rule.get("derive") or {}).get("predicate")
            if rule_type != "TRANSITIVE" or not relation or not target:
                continue

            edges = [
                memory for memory in self.memory.memories
                if memory.status == "ASSERTED" and memory.predicate == relation
            ]
            for first in edges:
                for second in edges:
                    if first.object != second.subject:
                        continue
                    if first.subject == second.object:
                        continue
                    candidate = {
                        "subject": first.subject,
                        "predicate": target,
                        "object": second.object,
                        "status": "DERIVED",
                        "source": "INFERENCE",
                        "support": [first, second],
                        "rule": rule.get("name"),
                    }
                    if not any(
                        item["subject"] == candidate["subject"]
                        and item["predicate"] == candidate["predicate"]
                        and item["object"] == candidate["object"]
                        for item in derived
                    ):
                        derived.append(candidate)
        return derived
