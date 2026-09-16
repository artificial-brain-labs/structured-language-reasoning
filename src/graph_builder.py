from .semantic_graph import GraphEdge, GraphNode, SemanticGraph


class SemanticGraphBuilder:
    """Project memory and derived results into a semantic graph."""

    def build(self, memory, derived=None):
        graph = SemanticGraph()
        for entity_id, data in memory.entities.items():
            concept = data.get("concept", "UNKNOWN")
            node_type = "CLASS" if data.get("name") == concept else "ENTITY"
            graph.add_node(GraphNode(entity_id, node_type, data.get("name", entity_id), concept))

        for index, item in enumerate(memory.memories, 1):
            object_id = self._ensure_value_node(graph, memory, item.object)
            graph.add_edge(GraphEdge(
                edge_id=f"asserted_{index:04d}", subject=item.subject,
                predicate=item.predicate, object=object_id, status=item.status,
                source=item.source, confidence=item.confidence,
                support=tuple(item.support), attributes={
                    "created_at": item.created_at,
                    "contradictions": list(item.contradictions),
                },
            ))

        for index, item in enumerate(derived or [], len(graph.edges) + 1):
            subject_id = item.get("subject", item.get("entity"))
            if subject_id is None:
                continue
            object_id = self._ensure_value_node(graph, memory, item.get("object"))
            graph.add_edge(GraphEdge(
                edge_id=f"derived_{index:04d}", subject=subject_id,
                predicate=item["predicate"], object=object_id, status="DERIVED",
                source=item.get("source", "INFERENCE"),
                support=tuple(self._support_ids(item.get("support", []))),
                attributes={"rule": item["rule"]} if item.get("rule") else {},
            ))
        return graph

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
        node_id = f"literal:{value}"
        graph.add_node(GraphNode(node_id, "LITERAL", str(value), "LITERAL"))
        return node_id

    def _support_ids(self, support):
        return [getattr(item, "subject", item) for item in support]
