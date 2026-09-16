from .semantic_graph import GraphEdge, GraphNode, SemanticGraph


class SemanticGraphBuilder:
    """Project asserted memory and optional derived results into a graph.

    This is deliberately a projection mechanism. It does not classify unknown
    entities, promote derived facts, or modify memory.
    """

    def build(self, memory, derived=None):
        graph = SemanticGraph()

        for entity_id, data in memory.entities.items():
            concept = data.get("concept", "UNKNOWN")
            node_type = "CLASS" if entity_id.endswith(f"_{concept.lower()}") and data.get("name") == concept else "ENTITY"
            graph.add_node(
                GraphNode(
                    node_id=entity_id,
                    node_type=node_type,
                    name=data.get("name", entity_id),
                    concept=concept,
                )
            )

        for index, memory_item in enumerate(memory.memories, start=1):
            self._add_memory_edge(graph, memory_item, index)

        for index, item in enumerate(derived or [], start=len(graph.edges) + 1):
            object_id = self._ensure_value_node(graph, memory, item.get("object"))
            graph.add_edge(
                GraphEdge(
                    edge_id=f"derived_{index:04d}",
                    subject=item["subject"],
                    predicate=item["predicate"],
                    object=object_id,
                    status="DERIVED",
                    source=item.get("source", "INFERENCE"),
                    support=tuple(self._support_ids(item.get("support", []))),
                    attributes={"rule": item.get("rule")} if item.get("rule") else {},
                )
            )

        return graph

    def _add_memory_edge(self, graph, memory_item, index):
        object_id = self._ensure_value_node(graph, None, memory_item.object)
        graph.add_edge(
            GraphEdge(
                edge_id=f"asserted_{index:04d}",
                subject=memory_item.subject,
                predicate=memory_item.predicate,
                object=object_id,
                status=memory_item.status,
                source=memory_item.source,
                confidence=memory_item.confidence,
                support=tuple(memory_item.support),
                attributes={
                    "created_at": memory_item.created_at,
                    "contradictions": list(memory_item.contradictions),
                },
            )
        )

    def _ensure_value_node(self, graph, memory, value):
        if value in graph.nodes:
            return value
        if memory is not None and value in memory.entities:
            data = memory.entities[value]
            graph.add_node(GraphNode(value, "ENTITY", data.get("name", value), data.get("concept", "UNKNOWN")))
            return value
        node_id = f"literal:{value}"
        graph.add_node(GraphNode(node_id, "LITERAL", str(value), "LITERAL"))
        return node_id

    def _support_ids(self, support):
        return [getattr(item, "subject", item) for item in support]
