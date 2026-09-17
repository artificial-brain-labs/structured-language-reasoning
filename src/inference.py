"""Compatibility facade for the pre-V1 inference API.

The canonical reasoning kernel is ``SemanticGraphReasoner``. This module keeps
legacy ontology-inheritance helpers available without maintaining a second
reasoning implementation.
"""

from .graph_reasoner import SemanticGraphReasoner


class InferenceEngine:
    """Compatibility facade over the canonical semantic-graph reasoner."""

    def __init__(self, ontology, relation_schemas=None):
        self.ontology = ontology
        self.reasoner = SemanticGraphReasoner(ontology, relation_schemas)

    def inherited_classes(self, concept):
        return [concept] + self.ontology.ancestors(concept)

    def entity_is_a(self, graph, entity_id, target_class):
        """Return True only when an explicit asserted classification proves it."""
        result = self.reasoner.reason(graph)
        for edge in result.edges:
            if edge.subject == entity_id and edge.predicate == self._taxonomic_relation():
                node = graph.nodes.get(edge.object)
                if node and node.concept == target_class:
                    return True
        return self._explicit_type_matches(graph, entity_id, target_class)

    def inherited_properties(self, graph, entity_id):
        """Return ontology properties justified by an explicit graph type."""
        for edge in graph.edges_from(entity_id):
            if edge.status != "ASSERTED" or edge.predicate != self._taxonomic_relation():
                continue
            node = graph.nodes.get(edge.object)
            if node and self.ontology.class_exists(node.concept):
                return self.ontology.properties(node.concept)
        return {}

    def explain_is_a(self, graph, entity_id, target_class):
        """Return the ontology chain when explicit graph evidence supports it."""
        for edge in graph.edges_from(entity_id, self._taxonomic_relation()):
            if edge.status != "ASSERTED":
                continue
            node = graph.nodes.get(edge.object)
            if node and self.ontology.class_exists(node.concept) and self.ontology.is_a(node.concept, target_class):
                chain = [node.concept] + self.ontology.ancestors(node.concept)
                return chain[: chain.index(target_class) + 1]
        return None

    def _taxonomic_relation(self):
        candidates = [
            (schema.get("priority", 0), name)
            for name, schema in getattr(self.reasoner, "relation_schemas", {}).items()
            if schema.get("role") == "canonical_taxonomic"
        ]
        if not candidates:
            return "IS_A"
        highest = max(priority for priority, _ in candidates)
        matches = [name for priority, name in candidates if priority == highest]
        return matches[0] if len(matches) == 1 else None

    def _explicit_type_matches(self, graph, entity_id, target_class):
        relation = self._taxonomic_relation()
        if relation is None:
            return False
        for edge in graph.edges_from(entity_id, relation):
            if edge.status != "ASSERTED":
                continue
            node = graph.nodes.get(edge.object)
            if node and self.ontology.class_exists(node.concept) and self.ontology.is_a(node.concept, target_class):
                return True
        return False
