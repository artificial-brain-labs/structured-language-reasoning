from .relations import RelationSchema

class Reasoner:
    def __init__(self, ontology, memory):
        self.ontology = ontology
        self.memory = memory
        self.schemas = RelationSchema()

    def validate_relation(self, subject_entity, predicate, object_entity):
        schema = self.schemas.get(predicate)
        if not schema:
            return True

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
        return [{"entity": entity_id, "predicate": "IS_A", "object": ancestor}
                for ancestor in self.ontology.ancestors(concept)]
