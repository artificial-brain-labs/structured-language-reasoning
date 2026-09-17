from dataclasses import dataclass

from .semantic_graph import GraphEdge, SemanticGraph


@dataclass(frozen=True)
class ReasoningResult:
    """A reasoning result that is explicitly derived and non-persistent."""

    edges: tuple[GraphEdge, ...]


class SemanticGraphReasoner:
    """Derive knowledge from explicit asserted graph relationships without storing it.

    Ontology hierarchy is supplied as data. The reasoner provides mechanisms for
    traversing that data; it never embeds domain knowledge in procedural code.
    Only ASSERTED classification edges may serve as evidence for derived facts.
    OBSERVED, HYPOTHESIS, and other non-asserted states are not promoted by
    reasoning.
    """

    def __init__(self, ontology):
        self.ontology = ontology

    def reason(self, graph: SemanticGraph) -> ReasoningResult:
        derived = []
        for edge in graph.asserted_edges():
            if edge.predicate != "IS_A":
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
                derived.append(self._edge(edge, target_id, ancestor, len(derived) + 1))
        return ReasoningResult(tuple(self._deduplicate(derived)))

    def _concept_node(self, graph, concept):
        for node in graph.nodes.values():
            if node.node_type in {"CONCEPT", "CLASS"} and node.concept == concept:
                return node.node_id
        return None

    def _edge(self, support_edge, target_id, ancestor, index):
        return GraphEdge(
            edge_id=f"derived:{index:04d}",
            subject=support_edge.subject,
            predicate="IS_A",
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
