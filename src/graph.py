"""Compatibility facade for the pre-V1 semantic graph API.

The canonical graph implementation is :mod:`src.semantic_graph`. This module
contains no independent graph state or reasoning rules; it exists only for
older callers that still use the original KnowledgeGraph API.
"""

from dataclasses import dataclass

from .semantic_graph import GraphEdge, GraphNode, SemanticGraph


@dataclass(frozen=True)
class Edge:
    subject: str
    predicate: str
    object: str
    source: str = "USER"
    status: str = "ASSERTED"


class KnowledgeGraph:
    """Compatibility facade backed by the canonical SemanticGraph."""

    def __init__(self):
        self._graph = SemanticGraph()

    @property
    def entities(self):
        return {
            node_id: {"type": node.concept if node.node_type in {"CLASS", "CONCEPT"} else node.concept}
            for node_id, node in self._graph.nodes.items()
            if node.node_type in {"ENTITY", "REFERENT", "CLASS", "CONCEPT"}
        }

    @property
    def edges(self):
        return [
            Edge(edge.subject, edge.predicate, edge.object, edge.source, edge.status)
            for edge in self._graph.edges.values()
        ]

    @property
    def asserted_edges(self):
        """Compatibility view of asserted edges from the canonical graph.

        This is deliberately a computed view rather than a second edge store,
        preserving the V1 rule that ``SemanticGraph`` is the single graph
        source of truth.
        """
        return [
            edge
            for edge in self.edges
            if edge.status == "ASSERTED"
        ]

    @property
    def derived_edges(self):
        """Compatibility view of derived edges from the canonical graph."""
        return [
            edge
            for edge in self.edges
            if edge.status == "DERIVED"
        ]

    def add_entity(self, entity_id, entity_type=None):
        concept = entity_type or "UNKNOWN"
        node_type = "CLASS" if entity_type is not None else "ENTITY"
        self._graph.add_node(GraphNode(entity_id, node_type, entity_id, concept))

    def add_edge(self, subject, predicate, object_, source="USER", status="ASSERTED"):
        if subject not in self._graph.nodes:
            self.add_entity(subject)
        if object_ not in self._graph.nodes:
            self.add_entity(object_)
        return self._graph.add_edge(
            GraphEdge(
                edge_id=f"compat:{len(self._graph.edges) + 1:04d}",
                subject=subject,
                predicate=predicate,
                object=object_,
                source=source,
                status=status,
            )
        )

    def has_edge(self, subject, predicate, object_=None):
        return any(
            edge.subject == subject
            and edge.predicate == predicate
            and (object_ is None or edge.object == object_)
            for edge in self._graph.edges_from(subject, predicate)
        )

    def query(self, subject=None, predicate=None, object_=None):
        return [
            edge for edge in self.edges
            if (subject is None or edge.subject == subject)
            and (predicate is None or edge.predicate == predicate)
            and (object_ is None or edge.object == object_)
        ]
