from dataclasses import dataclass, field


@dataclass(frozen=True)
class GraphNode:
    """A node in a structured semantic representation."""

    node_id: str
    node_type: str
    name: str
    concept: str = "UNKNOWN"
    attributes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    """A semantic relationship with explicit evidence and provenance."""

    edge_id: str
    subject: str
    predicate: str
    object: str
    status: str = "ASSERTED"
    source: str = "USER"
    confidence: float = 1.0
    support: tuple = ()
    attributes: dict = field(default_factory=dict)


class SemanticGraph:
    """In-memory structured semantic representation.

    The graph is a representation layer: it does not invent knowledge and it
    does not replace USER MEMORY persistence. Asserted graph content must be
    supplied explicitly; derived content can be represented with status
    DERIVED without being persisted as asserted memory.
    """

    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node):
        if node.node_id not in self.nodes:
            self.nodes[node.node_id] = node
        return self.nodes[node.node_id]

    def add_edge(self, edge):
        if edge.subject not in self.nodes or edge.object not in self.nodes:
            raise ValueError("Graph edge endpoints must exist")
        if edge.edge_id not in self.edges:
            self.edges[edge.edge_id] = edge
        return self.edges[edge.edge_id]

    def edges_from(self, subject, predicate=None):
        return [
            edge for edge in self.edges.values()
            if edge.subject == subject
            and (predicate is None or edge.predicate == predicate)
        ]

    def edges_to(self, object_, predicate=None):
        return [
            edge for edge in self.edges.values()
            if edge.object == object_
            and (predicate is None or edge.predicate == predicate)
        ]

    def asserted_edges(self):
        return [edge for edge in self.edges.values() if edge.status == "ASSERTED"]

    def derived_edges(self):
        return [edge for edge in self.edges.values() if edge.status == "DERIVED"]

    def to_dict(self):
        return {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "name": node.name,
                    "concept": node.concept,
                    "attributes": dict(node.attributes),
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "subject": edge.subject,
                    "predicate": edge.predicate,
                    "object": edge.object,
                    "status": edge.status,
                    "source": edge.source,
                    "confidence": edge.confidence,
                    "support": list(edge.support),
                    "attributes": dict(edge.attributes),
                }
                for edge in self.edges.values()
            ],
        }
