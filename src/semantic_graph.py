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
    """In-memory structured semantic representation with relation metadata."""

    def __init__(self, relation_schemas=None):
        self.nodes = {}
        self.edges = {}
        self.relation_schemas = relation_schemas or {}

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
        return [edge for edge in self.edges.values() if edge.subject == subject and (predicate is None or edge.predicate == predicate)]

    def edges_to(self, object_, predicate=None):
        return [edge for edge in self.edges.values() if edge.object == object_ and (predicate is None or edge.predicate == predicate)]

    def asserted_edges(self):
        return [edge for edge in self.edges.values() if edge.status == "ASSERTED"]

    def derived_edges(self):
        return [edge for edge in self.edges.values() if edge.status == "DERIVED"]

    def to_dict(self):
        return {
            "nodes": [
                {"node_id": n.node_id, "node_type": n.node_type, "name": n.name, "concept": n.concept, "attributes": dict(n.attributes)}
                for n in self.nodes.values()
            ],
            "edges": [
                {"edge_id": e.edge_id, "subject": e.subject, "predicate": e.predicate, "object": e.object, "status": e.status, "source": e.source, "confidence": e.confidence, "support": list(e.support), "attributes": dict(e.attributes)}
                for e in self.edges.values()
            ],
        }
