from dataclasses import dataclass

from .semantic_graph import GraphEdge, SemanticGraph


@dataclass(frozen=True)
class ReasoningResult:
    """A reasoning result that is explicitly derived and non-persistent."""

    edges: tuple[GraphEdge, ...]


class SemanticGraphReasoner:
    """Derive knowledge from asserted graph relationships and ontology data.

    Relation roles are read from declarative relation schemas. The reasoner is
    a mechanism: it does not embed domain relation names in procedural logic.
    Only ASSERTED classification edges may serve as evidence for derivation.
    """

    def __init__(self, ontology, relation_schemas=None):
        self.ontology = ontology
        self.relation_schemas = relation_schemas or {}

    def _relation_for_role(self, role):
        candidates = [
            (schema.get("priority", 0), name)
            for name, schema in self.relation_schemas.items()
            if schema.get("role") == role
        ]
        if not candidates:
            return None
        highest = max(priority for priority, _ in candidates)
        matches = [name for priority, name in candidates if priority == highest]
        return matches[0] if len(matches) == 1 else None

    def reason(self, graph: SemanticGraph) -> ReasoningResult:
        derived = []
        taxonomic_relation = self._relation_for_role("canonical_taxonomic")
        if not taxonomic_relation:
            return ReasoningResult(())

        for edge in graph.asserted_edges():
            if edge.predicate != taxonomic_relation:
                continue
            subject = graph.nodes.get(edge.subject)
            concept_node = graph.nodes.get(edge.object)
            if not subject or not concept_node:
                continue
            concept = concept_node.concept
            if not self.ontology.class_exists(concept):
                continue
            for ancestor in self.ontology.ancestors(concept):
                target_id = self._concept_node(graph, ancestor)
                if target_id is None:
                    continue
                derived.append(self._edge(edge, target_id, ancestor, len(derived) + 1, taxonomic_relation))
        return ReasoningResult(tuple(self._deduplicate(derived)))

    def _concept_node(self, graph, concept):
        for node in graph.nodes.values():
            if node.node_type in {"CONCEPT", "CLASS"} and node.concept == concept:
                return node.node_id
        return None

    def _edge(self, support_edge, target_id, ancestor, index, taxonomic_relation):
        return GraphEdge(
            edge_id=f"derived:{index:04d}",
            subject=support_edge.subject,
            predicate=taxonomic_relation,
            object=target_id,
            status="DERIVED",
            source="REASONER",
            confidence=1.0,
            support=(support_edge.edge_id,),
            attributes={"reason": "ontology_ancestor", "concept": ancestor},
        )

    def _deduplicate(self, edges):
        seen = set()
        result = []
        for edge in edges:
            key = (edge.subject, edge.predicate, edge.object)
            if key in seen:
                continue
            seen.add(key)
            result.append(edge)
        return result
