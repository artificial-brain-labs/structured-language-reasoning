class SemanticGraphQuery:
    """Read-only query operations over the semantic graph.

    The graph is a representation layer. Queries may traverse asserted and
    derived edges, but traversal never promotes a derived edge to USER MEMORY.
    """

    def __init__(self, graph):
        self.graph = graph

    def _node_concept(self, node_id):
        node = self.graph.nodes.get(node_id)
        return node.concept if node else None

    def classification(self, subject_id, target_concept):
        """Return a path proving subject_id is classified as target_concept."""
        if subject_id not in self.graph.nodes:
            return None

        queue = [(subject_id, [])]
        visited = {subject_id}
        while queue:
            current, path = queue.pop(0)
            for edge in self.graph.edges_from(current, "IS_A"):
                if edge.status == "CONFLICTED":
                    continue
                next_path = path + [edge]
                if self._node_concept(edge.object) == target_concept:
                    return next_path
                if edge.object not in visited:
                    visited.add(edge.object)
                    queue.append((edge.object, next_path))
        return None

    def explain_classification(self, subject_id, target_concept):
        """Return structured evidence for a classification query.

        The returned proof contains only graph edges actually traversed. If no
        path exists, ``None`` is returned; absence of evidence is never treated
        as a negative classification.
        """
        path = self.classification(subject_id, target_concept)
        if path is None:
            return None
        return {
            "subject": subject_id,
            "target": target_concept,
            "status": "PROVEN",
            "path": [
                {
                    "subject": edge.subject,
                    "predicate": edge.predicate,
                    "object": edge.object,
                    "status": edge.status,
                    "source": edge.source,
                    "support": list(edge.support),
                    "rule": edge.attributes.get("rule"),
                }
                for edge in path
            ],
        }

    def objects(self, subject_id, predicate):
        """Return object node IDs for non-conflicted graph edges."""
        return [
            edge.object
            for edge in self.graph.edges_from(subject_id, predicate)
            if edge.status != "CONFLICTED"
        ]

    def subjects(self, object_id, predicate):
        """Return subject node IDs for non-conflicted graph edges."""
        return [
            edge.subject
            for edge in self.graph.edges_to(object_id, predicate)
            if edge.status != "CONFLICTED"
        ]
