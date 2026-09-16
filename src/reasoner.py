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

    def explicit_types(self, entity_id):
        """Return directly asserted user classifications for an entity.

        These are explicit IS_A relations, not inferred classifications.
        """
        if entity_id not in self.memory.entities:
            return []
        types = []
        for memory in self.memory.query(subject=entity_id, predicate="IS_A"):
            if memory.status != "ASSERTED":
                continue
            concept = self.memory.entities.get(memory.object, {}).get("concept")
            if concept and concept != "UNKNOWN" and concept not in types:
                types.append(concept)
        return types

    def known_types(self, entity_id):
        """Return explicit types plus ontology ancestors, without storing them."""
        types = list(self.explicit_types(entity_id))
        for concept in list(types):
            for ancestor in self.ontology.ancestors(concept):
                if ancestor not in types:
                    types.append(ancestor)
        return types

    def validate_relation(self, subject_entity, predicate, object_entity):
        schema = self.memory.relations.get(predicate)
        if not schema:
            return False

        subject_concepts = self.known_types(subject_entity)
        object_concepts = self.known_types(object_entity)

        # If an entity has no explicit type, do not guess one from its name.
        if not subject_concepts:
            subject_concept = self.memory.entities[subject_entity]["concept"]
            if subject_concept != "UNKNOWN":
                subject_concepts = [subject_concept, *self.ontology.ancestors(subject_concept)]

        if not object_concepts:
            object_concept = self.memory.entities[object_entity]["concept"]
            if object_concept != "UNKNOWN":
                object_concepts = [object_concept, *self.ontology.ancestors(object_concept)]

        required_subject = schema.get("subject_type")
        required_object = schema.get("object_type")

        if required_subject and not any(self.ontology.is_a(concept, required_subject) for concept in subject_concepts):
            return False

        # An explicit relation may refer to an entity whose type is not yet
        # known. That is not permission to guess the type; it is an explicit
        # observation whose object classification remains UNKNOWN. Whether
        # such observations are accepted is declared by the relation schema.
        if required_object and not object_concepts:
            return schema.get("allow_unknown_object", False)

        if required_object and not any(self.ontology.is_a(concept, required_object) for concept in object_concepts):
            return False
        return True

    def infer_is_a(self, entity_id):
        """Return ontology-derived classifications without storing them."""
        if entity_id not in self.memory.entities:
            return []
        concepts = self.explicit_types(entity_id)
        if not concepts:
            cached = self.memory.entities[entity_id]["concept"]
            if cached != "UNKNOWN":
                concepts = [cached]

        relation_name = self.relation_name_for_role("canonical_taxonomic")
        if not relation_name:
            return []

        results = []
        for concept in concepts:
            for ancestor in self.ontology.ancestors(concept):
                results.append({
                    "entity": entity_id,
                    "predicate": relation_name,
                    "object": ancestor,
                    "status": "DERIVED",
                    "source": "ONTOLOGY",
                    "support": [concept],
                })
        return results

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
