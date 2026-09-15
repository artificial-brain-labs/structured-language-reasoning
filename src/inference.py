from .ontology import Ontology


class InferenceEngine:
    """Derives facts from confirmed graph edges and ontology inheritance."""

    def __init__(self, ontology: Ontology):
        self.ontology = ontology

    def inherited_classes(self, concept):
        return [concept] + self.ontology.ancestors(concept)

    def entity_is_a(self, graph, entity_id, target_class):
        """Return True only when the graph explicitly types the entity."""
        entity = graph.entities.get(entity_id)
        if not entity or not entity.get("type"):
            return False
        return self.ontology.is_a(entity["type"], target_class)

    def inherited_properties(self, graph, entity_id):
        """Return ontology properties justified by an entity's explicit type."""
        entity = graph.entities.get(entity_id)
        if not entity or not entity.get("type"):
            return {}
        return self.ontology.properties(entity["type"])

    def explain_is_a(self, graph, entity_id, target_class):
        """Return a derivation chain, or None if the fact cannot be justified."""
        entity = graph.entities.get(entity_id)
        if not entity or not entity.get("type"):
            return None
        source = entity["type"]
        if not self.ontology.is_a(source, target_class):
            return None
        chain = [source] + self.ontology.ancestors(source)
        index = chain.index(target_class)
        return chain[: index + 1]
