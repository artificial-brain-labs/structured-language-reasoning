"""Explicit proof/derivation graph for SRST."""

from dataclasses import dataclass, field


@dataclass
class ProofNode:
    id: str
    node_type: str
    reference_id: str


@dataclass
class ProofEdge:
    source: str
    target: str
    relation: str


@dataclass
class ProofGraph:
    nodes: list[ProofNode] = field(default_factory=list)
    edges: list[ProofEdge] = field(default_factory=list)

    def add_node(self, node: ProofNode) -> None:
        if not any(existing.id == node.id for existing in self.nodes):
            self.nodes.append(node)

    def add_edge(self, edge: ProofEdge) -> None:
        self.edges.append(edge)

    def has_node(self, node_id: str) -> bool:
        return any(node.id == node_id for node in self.nodes)

    def dependencies_for(self, node_id: str) -> list[str]:
        return [
            edge.source
            for edge in self.edges
            if edge.target == node_id
        ]
