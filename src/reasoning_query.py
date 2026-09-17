from dataclasses import dataclass

from .semantic_graph import SemanticGraph
from .graph_reasoner import SemanticGraphReasoner


@dataclass(frozen=True)
class QueryReasoningResult:
    """Answer to a graph query without persisting the reasoning result."""

    status: str
    subject: str
    target: str
    path: tuple[str, ...] = ()
    reason: str | None = None


class GraphQueryReasoner:
    """Answer classification queries using explicit graph facts and ontology data.

    The query layer derives an answer at query time. It never writes derived
    edges back into the graph or into memory. Unknown remains unknown.
    """

    def __init__(self, ontology):
        self.reasoner = SemanticGraphReasoner(ontology)
        self.ontology = ontology

    def is_a(self, graph: SemanticGraph, subject_id: str, target_concept: str) -> QueryReasoningResult:
        subject = graph.nodes.get(subject_id)
        if subject is None:
            return QueryReasoningResult("UNKNOWN", subject_id, target_concept, reason="unknown_subject")
        if not self.ontology.class_exists(target_concept):
            return QueryReasoningResult("UNKNOWN", subject_id, target_concept, reason="unknown_target_concept")

        starts = self._explicit_is_a_targets(graph, subject_id)
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

    def _explicit_is_a_targets(self, graph, subject_id):
        return [
            (graph.nodes[edge.object].concept, edge.edge_id)
            for edge in graph.edges_from(subject_id, "IS_A")
            if edge.status == "ASSERTED"
            and edge.object in graph.nodes
            and graph.nodes[edge.object].node_type in {"CONCEPT", "CLASS"}
        ]
