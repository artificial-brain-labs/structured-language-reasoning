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

            # First traverse explicit identity relationships. This preserves
            # the actual proof path instead of collapsing identities and then
            # losing the relationship between the names/entities.
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

    def explain_classification(self, subject_id, target_concept):
        """Return a complete structured proof for a classification query.

        The proof may begin with explicit identity traversal followed by an
        asserted classification. Ontology relationships are then represented
        as derived explanation steps. No derived step is persisted.
        """
        if subject_id not in self.graph.nodes:
            return None

        queue = [(subject_id, [])]
        visited = {subject_id}
        while queue:
            current, identity_path = queue.pop(0)

            # Identity is explicit user knowledge, so it may be traversed as
            # part of the proof without asserting anything new.
            for identity_edge in self._identity_edges(current):
                if identity_edge.object in visited:
                    continue
                visited.add(identity_edge.object)
                queue.append((identity_edge.object, identity_path + [identity_edge]))

            asserted = [
                edge for edge in self.graph.edges_from(current, "IS_A")
                if edge.status == "ASSERTED"
            ]

            for first in asserted:
                source_concept = self._node_concept(first.object)
                if source_concept is None:
                    continue

                if source_concept == target_concept:
                    path = identity_path + [self._proof_edge(first)]
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

                path = identity_path + [self._proof_edge(first)]
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
