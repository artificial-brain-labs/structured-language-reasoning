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
    def nodes(self):
        return self._graph.nodes

    @property
    def entities(self):
        return {
            node_id: {"type": node.concept}
            for node_id, node in self._graph.nodes.items()
            if node.node_type in {"ENTITY", "REFERENT", "CLASS", "CONCEPT"}
        }

    @property
    def edges(self):
        return [
            Edge(edge.subject, edge.predicate, edge.object, edge.source, edge.status)
            for edge in self._graph.edges.values()
        ]

    def asserted_edges(self):
        """Return asserted edges as a computed compatibility view."""
        return [edge for edge in self.edges if edge.status == "ASSERTED"]

    def derived_edges(self):
        """Return derived edges as a computed compatibility view."""
        return [edge for edge in self.edges if edge.status == "DERIVED"]

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

    def edges_from(self, subject, predicate=None):
        return self._graph.edges_from(subject, predicate)

    def edges_to(self, object_, predicate=None):
        return self._graph.edges_to(object_, predicate)

    def query(self, subject=None, predicate=None, object_=None):
        return [
            edge for edge in self.edges
            if (subject is None or edge.subject == subject)
            and (predicate is None or edge.predicate == predicate)
            and (object_ is None or edge.object == object_)
        ]
