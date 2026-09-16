class SemanticGraphQuery:
    """Read-only query operations over the semantic graph.

    The graph is a representation layer. Queries may traverse asserted and
    derived edges, but traversal never promotes a derived edge to USER MEMORY.
    Identity relationships are traversal edges: they allow a query to move
    from one explicit identity to another before following semantic facts.
    """

    def __init__(self, graph, ontology=None, identity_predicates=None):
        self.graph = graph
        self.ontology = ontology
        self.identity_predicates = set(identity_predicates or ())

    def _node_concept(self, node_id):
        node = self.graph.nodes.get(node_id)
        return node.concept if node else None

    def _identity_edges(self, subject_id):
        """Return explicit identity edges used only for traversal."""
        if not self.identity_predicates:
            return []
        return [
            edge for edge in self.graph.edges_from(subject_id)
            if edge.predicate in self.identity_predicates
            and edge.status != "CONFLICTED"
        ]

    def _identity_paths(self, subject_id):
        """Traverse the explicit identity component and retain proof paths."""
        if subject_id not in self.graph.nodes:
            return []
        queue = [(subject_id, [])]
        visited = {subject_id}
        results = []
        while queue:
            current, path = queue.pop(0)
            results.append((current, path))
            for edge in self._identity_edges(current):
                if edge.object in visited:
                    continue
                visited.add(edge.object)
                queue.append((edge.object, path + [edge]))
        return results

    def classification(self, subject_id, target_concept):
        """Return a path proving subject_id is classified as target_concept.

        Traversal may cross explicit identity relationships before following
        semantic classification edges. Identity traversal is not itself a
        classification and never creates a stored derived fact.
        """
        if subject_id not in self.graph.nodes:
            return None

        queue = [(subject_id, [])]
        visited = {subject_id}
        while queue:
            current, path = queue.pop(0)

            for edge in self._identity_edges(current):
                next_path = path + [edge]
                if edge.object not in visited:
                    visited.add(edge.object)
                    queue.append((edge.object, next_path))

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

    def entity_type(self, subject_id):
        """Return the first explicit type reachable through identity traversal."""
        for entity_id, identity_path in self._identity_paths(subject_id):
            for edge in self.graph.edges_from(entity_id, "IS_A"):
                if edge.status != "ASSERTED":
                    continue
                concept = self._node_concept(edge.object)
                if concept and concept != "UNKNOWN":
                    return {
                        "entity": subject_id,
                        "predicate": "IS_A",
                        "object": concept,
                        "status": "ASSERTED" if not identity_path else "DERIVED",
                        "source": edge.source,
                        "support": list(identity_path) + [edge],
                        "path": identity_path + [edge],
                    }
        return None

    def explain_classification(self, subject_id, target_concept):
        """Return a complete structured proof for a classification query.

        The proof begins with explicit identity traversal when required,
        then follows asserted IS_A classification edges and derives the
        ontology-parent chain to the requested target. Derived explanation
        steps are never persisted as USER MEMORY.
        """
        if subject_id not in self.graph.nodes:
            return None

        for entity_id, identity_path in self._identity_paths(subject_id):
            asserted = [
                edge for edge in self.graph.edges_from(entity_id, "IS_A")
                if edge.status == "ASSERTED"
            ]

            for first in asserted:
                source_concept = self._node_concept(first.object)
                if source_concept is None or source_concept == "UNKNOWN":
                    continue

                path = []
                if identity_path:
                    path.extend(identity_path)
                path.append(self._proof_edge(first))

                if source_concept == target_concept:
                    return self._proof(subject_id, target_concept, path)

                if self.ontology is None or not self.ontology.is_a(source_concept, target_concept):
                    continue

                concepts = [source_concept]
                current_concept = source_concept
                seen = {current_concept}
                while current_concept != target_concept:
                    parent = self.ontology.parent(current_concept)
                    if parent is None or parent in seen:
                        break
                    concepts.append(parent)
                    seen.add(parent)
                    current_concept = parent

                if concepts[-1] != target_concept:
                    continue

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
