from dataclasses import dataclass

from .semantic_graph import SemanticGraph


@dataclass(frozen=True)
class QueryReasoningResult:
    """Answer to a graph query without persisting the reasoning result."""

    status: str
    subject: str
    target: str
    path: tuple[str, ...] = ()
    reason: str | None = None


class GraphQueryReasoner:
    """Answer classification queries using asserted graph facts and ontology data.

    The query layer derives an answer at query time. It never writes derived
    edges back into the graph or into memory. Relation roles come from the
    declarative relation schemas, so the query mechanism does not embed domain
    relation names.
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

    def is_a(self, graph: SemanticGraph, subject_id: str, target_concept: str) -> QueryReasoningResult:
        subject = graph.nodes.get(subject_id)
        if subject is None:
            return QueryReasoningResult("UNKNOWN", subject_id, target_concept, reason="unknown_subject")
        if not self.ontology.class_exists(target_concept):
            return QueryReasoningResult("UNKNOWN", subject_id, target_concept, reason="unknown_target_concept")

        relation = self._relation_for_role("canonical_taxonomic")
        if relation is None:
            return QueryReasoningResult("UNKNOWN", subject_id, target_concept, reason="no_taxonomic_relation")

        starts = self._explicit_classifications(graph, subject_id, relation)
        if not starts:
            return QueryReasoningResult("UNKNOWN", subject_id, target_concept, reason="no_explicit_classification")

        for concept, edge_id in starts:
            if not self.ontology.class_exists(concept):
                continue
            path = [edge_id, concept]
            if self.ontology.is_a(concept, target_concept):
                current = concept
                while current != target_concept:
                    current = self.ontology.parent(current)
                    if current is None:
                        break
                    path.append(current)
                return QueryReasoningResult("YES", subject_id, target_concept, tuple(path))

        return QueryReasoningResult("UNKNOWN", subject_id, target_concept, reason="not_derivable")

    def _explicit_classifications(self, graph, subject_id, relation):
        return [
            (graph.nodes[edge.object].concept, edge.edge_id)
            for edge in graph.edges_from(subject_id, relation)
            if edge.status == "ASSERTED"
            and edge.object in graph.nodes
            and graph.nodes[edge.object].node_type in {"CONCEPT", "CLASS"}
        ]
