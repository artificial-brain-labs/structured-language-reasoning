class Reasoner:
    def __init__(self, ontology, memory):
        self.ontology = ontology
        self.memory = memory

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
        concept = self.memory.entities[entity_id]["concept"]
        relation_name = self.relation_name_for_role("canonical_taxonomic")
        return [{"entity": entity_id, "predicate": relation_name, "object": ancestor}
                for ancestor in self.ontology.ancestors(concept)]
