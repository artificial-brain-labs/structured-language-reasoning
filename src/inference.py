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
        """Return True only when an explicit type or asserted classification proves it."""
        explicit_concept = self._explicit_concept(graph, entity_id)
        if explicit_concept is not None:
            return self.ontology.is_a(explicit_concept, target_class)

        result = self.reasoner.reason(graph)
        for edge in result.edges:
            if edge.subject != entity_id or edge.predicate != self._taxonomic_relation():
                continue
            node = graph.nodes.get(edge.object)
            if node and node.concept == target_class:
                return True
        return self._explicit_type_matches(graph, entity_id, target_class)

    def inherited_properties(self, graph, entity_id):
        """Return ontology properties justified by an explicit graph type."""
        explicit_concept = self._explicit_concept(graph, entity_id)
        if explicit_concept is not None:
            return self.ontology.properties(explicit_concept)

        for edge in graph.edges_from(entity_id):
            if edge.status != "ASSERTED" or edge.predicate != self._taxonomic_relation():
                continue
            node = graph.nodes.get(edge.object)
            if node and self.ontology.class_exists(node.concept):
                return self.ontology.properties(node.concept)
        return {}

    def explain_is_a(self, graph, entity_id, target_class):
        """Return the ontology chain when explicit graph evidence supports it."""
        explicit_concept = self._explicit_concept(graph, entity_id)
        if explicit_concept is not None and self.ontology.is_a(explicit_concept, target_class):
            chain = [explicit_concept] + self.ontology.ancestors(explicit_concept)
            return chain[: chain.index(target_class) + 1]

        for edge in graph.edges_from(entity_id, self._taxonomic_relation()):
            if edge.status != "ASSERTED":
                continue
            node = graph.nodes.get(edge.object)
            if node and self.ontology.class_exists(node.concept) and self.ontology.is_a(node.concept, target_class):
                chain = [node.concept] + self.ontology.ancestors(node.concept)
                return chain[: chain.index(target_class) + 1]
        return None

    def _explicit_concept(self, graph, entity_id):
        """Read an explicitly stored graph type; never infer a type from other relations."""
        node = graph.nodes.get(entity_id)
        if node is None:
            return None
        concept = getattr(node, "concept", "UNKNOWN")
        if concept == "UNKNOWN" or not self.ontology.class_exists(concept):
            return None
        return concept

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
