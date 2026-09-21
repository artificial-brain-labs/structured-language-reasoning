from .ontology import Ontology
from .semantic_graph import GraphEdge, GraphNode, SemanticGraph


class SemanticGraphBuilder:
    """Project user memory and transient derivations into one semantic graph.

    User memory remains the source of asserted user facts. The graph is a
    projection and therefore never writes back to memory. When available,
    user-memory evidence records are attached as provenance metadata.
    """

    def __init__(self, ontology=None):
        # Keep the legacy no-argument construction usable while allowing the
        # canonical SLR runtime to inject its shared ontology instance.
        self.ontology = ontology if ontology is not None else Ontology()

    def build(self, memory, derived=None):
        graph = SemanticGraph(relation_schemas=getattr(memory.relations, "schemas", {}))
        self._add_ontology_nodes(graph)

        for entity_id, data in memory.entities.items():
            concept = data.get("concept", "UNKNOWN")
            node_type = "CLASS" if data.get("name") == concept else "ENTITY"
            graph.add_node(GraphNode(entity_id, node_type, data.get("name", entity_id), concept))

        for index, item in enumerate(memory.memories, 1):
            subject_id = self._ensure_value_node(graph, memory, item.subject)
            object_id = self._ensure_value_node(graph, memory, item.object)
            attributes = {
                "created_at": item.created_at,
                "contradictions": list(item.contradictions),
                "evidence": self._evidence_for_memory(memory, item),
            }
            graph.add_edge(GraphEdge(
                edge_id=f"asserted_{index:04d}", subject=subject_id,
                predicate=item.predicate, object=object_id, status=item.status,
                source=item.source, confidence=item.confidence,
                support=tuple(item.support), attributes=attributes,
            ))

        for index, item in enumerate(derived or [], len(graph.edges) + 1):
            subject_id = item.get("subject", item.get("entity"))
            if subject_id is None:
                continue
            object_id = self._ensure_value_node(graph, memory, item.get("object"))
            graph.add_edge(GraphEdge(
                edge_id=item.get("edge_id", f"derived_{index:04d}"), subject=subject_id,
                predicate=item["predicate"], object=object_id, status="DERIVED",
                source=item.get("source", "INFERENCE"), confidence=item.get("confidence", 1.0),
                support=tuple(self._support_ids(item.get("support", []))),
                attributes={"rule": item["rule"]} if item.get("rule") else {},
            ))
        return graph

    def _add_ontology_nodes(self, graph):
        for concept, data in self.ontology.classes.items():
            graph.add_node(GraphNode(f"concept:{concept}", "CLASS", concept, concept))

    def _evidence_for_memory(self, memory, item):
        evidence_store = getattr(memory, "evidence", None)
        if evidence_store is None:
            return []
        matches = []
        for index, record in enumerate(evidence_store.records):
            if (
                record.subject == item.subject
                and record.predicate == item.predicate
                and record.object == item.object
            ):
                matches.append({
                    "index": index,
                    "kind": record.kind,
                    "source": record.source,
                    "confirmed": record.confirmed,
                    "support": list(record.support),
                })
        return matches

    def _ensure_value_node(self, graph, memory, value):
        if value in graph.nodes:
            return value
        if memory is not None and value in memory.entities:
            data = memory.entities[value]
            graph.add_node(GraphNode(value, "ENTITY", data.get("name", value), data.get("concept", "UNKNOWN")))
            return value
        if memory is not None:
            for entity_id, data in memory.entities.items():
                if data.get("concept") == value and data.get("name") == value:
                    return entity_id
        if isinstance(value, str):
            node_id = f"concept:{value}"
            graph.add_node(GraphNode(node_id, "CLASS", value, value))
            return node_id
        node_id = f"literal:{value}"
        graph.add_node(GraphNode(node_id, "LITERAL", str(value), "LITERAL"))
        return node_id

    def _support_ids(self, support):
        return [getattr(item, "subject", item) for item in support]
