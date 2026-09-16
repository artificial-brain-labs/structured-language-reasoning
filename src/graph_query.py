class SemanticGraphQuery:
    """Query the semantic graph without creating or mutating knowledge.

    The graph is a representation layer. Queries may traverse asserted and
    derived edges, but traversal never promotes a derived edge to USER MEMORY.
    """

    def __init__(self, graph):
        self.graph = graph

    def _node_concept(self, node_id):
        node = self.graph.nodes.get(node_id)
        return node.concept if node else None

    def classification(self, subject_id, target_concept):
        """Return a path proving subject_id is classified as target_concept.

        A direct graph edge is sufficient. Otherwise, IS_A edges are traversed
        breadth-first. Unknown nodes simply produce no result: no type is
        guessed from a name or from an absent edge.
        """
        if subject_id not in self.graph.nodes:
            return None

        queue = [(subject_id, [])]
        visited = {subject_id}
        while queue:
            current, path = queue.pop(0)
            for edge in self.graph.edges_from(current, "IS_A"):
                next_path = path + [edge]
                if self._node_concept(edge.object) == target_concept:
                    return next_path
                if edge.object not in visited:
                    visited.add(edge.object)
                    queue.append((edge.object, next_path))
        return None

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
