class SemanticGraphQuery:
    """Read-only query operations over the semantic graph.

    The graph is a representation layer. Queries may traverse asserted and
    derived edges, but traversal never promotes a derived edge to USER MEMORY.
    """

    def __init__(self, graph, ontology=None):
        self.graph = graph
        self.ontology = ontology

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
        """Return a complete structured proof for a classification query.

        The first step must be an asserted classification. Subsequent steps
        are ontology-backed parent relationships. The ontology is used as
        relationship data for explanation; no derived step is persisted.
        """
        if subject_id not in self.graph.nodes:
            return None

        asserted = [
            edge for edge in self.graph.edges_from(subject_id, "IS_A")
            if edge.status == "ASSERTED" and edge.status != "CONFLICTED"
        ]

        for first in asserted:
            source_concept = self._node_concept(first.object)
            if source_concept is None:
                continue
            if source_concept == target_concept:
                path = [self._proof_edge(first)]
                return self._proof(subject_id, target_concept, path)

            if self.ontology is None or not self.ontology.is_a(source_concept, target_concept):
                continue

            concepts = [source_concept]
            current = source_concept
            seen = {current}
            while current != target_concept:
                parent = self.ontology.parent(current)
                if parent is None or parent in seen:
                    break
                concepts.append(parent)
                seen.add(parent)
                current = parent

            if concepts[-1] != target_concept:
                continue

            path = [self._proof_edge(first)]
            for child, parent in zip(concepts, concepts[1:]):
                path.append({
                    "subject": child,
                    "predicate": "IS_A",
                    "object": parent,
                    "status": "DERIVED",
                    "source": "ONTOLOGY",
                    "support": [child],
                    "rule": "ONTOLOGY_PARENT",
                })
            return self._proof(subject_id, target_concept, path)

        return None

    def _proof_edge(self, edge):
        return {
            "subject": edge.subject,
            "predicate": edge.predicate,
            "object": self._node_concept(edge.object) or edge.object,
            "status": edge.status,
            "source": edge.source,
            "support": list(edge.support),
            "rule": edge.attributes.get("rule"),
        }

    def _proof(self, subject_id, target_concept, path):
        return {
            "subject": subject_id,
            "target": target_concept,
            "status": "PROVEN",
            "path": path,
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
