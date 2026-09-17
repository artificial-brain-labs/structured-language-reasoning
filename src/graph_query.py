class SemanticGraphQuery:
    """Read-only semantic graph traversal driven by relation metadata."""

    def __init__(self, graph, ontology=None, relation_schemas=None, identity_predicates=None):
        self.graph = graph
        self.ontology = ontology
        self.relation_schemas = relation_schemas or getattr(graph, "relation_schemas", {})
        self.identity_predicates = set(identity_predicates or ())

    def _node_concept(self, node_id):
        node = self.graph.nodes.get(node_id)
        return node.concept if node else None

    def _schema(self, predicate):
        return self.relation_schemas.get(predicate) or {}

    def _is_identity(self, predicate):
        schema = self._schema(predicate)
        return schema.get("role") == "identity" or predicate in self.identity_predicates

    def _is_taxonomic(self, predicate):
        return self._schema(predicate).get("role") == "canonical_taxonomic"

    def _traversable(self, predicate):
        return bool(self._schema(predicate).get("traversable"))

    def _neighbors(self, subject_id, classification_only=False):
        """Return schema-permitted traversal edges, including symmetric reverse traversal."""
        results = []
        for edge in self.graph.edges_from(subject_id):
            if edge.status == "CONFLICTED" or not self._traversable(edge.predicate):
                continue
            if classification_only and not (self._is_identity(edge.predicate) or self._is_taxonomic(edge.predicate)):
                continue
            results.append((edge, edge.object))
        for edge in self.graph.edges_to(subject_id):
            schema = self._schema(edge.predicate)
            if edge.status == "CONFLICTED" or not self._traversable(edge.predicate) or not schema.get("symmetric"):
                continue
            if classification_only and not (self._is_identity(edge.predicate) or self._is_taxonomic(edge.predicate)):
                continue
            results.append((edge, edge.subject))
        return results

    def _identity_paths(self, subject_id):
        if subject_id not in self.graph.nodes:
            return []
        queue = [(subject_id, [])]
        visited = {subject_id}
        results = []
        while queue:
            current, path = queue.pop(0)
            results.append((current, path))
            for edge, neighbor in self._neighbors(current):
                if not self._is_identity(edge.predicate) or neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append((neighbor, path + [edge]))
        return results

    def classification(self, subject_id, target_concept):
        if subject_id not in self.graph.nodes:
            return None
        queue = [(subject_id, [])]
        visited = {subject_id}
        while queue:
            current, path = queue.pop(0)
            for edge, neighbor in self._neighbors(current, classification_only=True):
                next_path = path + [edge]
                if self._is_taxonomic(edge.predicate) and self._node_concept(neighbor) == target_concept:
                    return next_path
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, next_path))
        return None

    def entity_type(self, subject_id):
        for entity_id, identity_path in self._identity_paths(subject_id):
            for edge, neighbor in self._neighbors(entity_id, classification_only=True):
                if not self._is_taxonomic(edge.predicate) or edge.status != "ASSERTED":
                    continue
                concept = self._node_concept(neighbor)
                if concept and concept != "UNKNOWN":
                    return {"entity": subject_id, "predicate": edge.predicate, "object": concept,
                            "status": "ASSERTED" if not identity_path else "DERIVED", "source": edge.source,
                            "support": list(identity_path) + [edge], "path": identity_path + [edge]}
        return None

    def explain_classification(self, subject_id, target_concept):
        if subject_id not in self.graph.nodes:
            return None
        for entity_id, identity_path in self._identity_paths(subject_id):
            for edge, neighbor in self._neighbors(entity_id, classification_only=True):
                if not self._is_taxonomic(edge.predicate) or edge.status != "ASSERTED":
                    continue
                source_concept = self._node_concept(neighbor)
                if source_concept is None or source_concept == "UNKNOWN":
                    continue
                path = list(identity_path) + [self._proof_edge(edge)]
                if source_concept == target_concept:
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
                for child, parent in zip(concepts, concepts[1:]):
                    path.append({"subject": child, "predicate": edge.predicate, "object": parent,
                                 "status": "DERIVED", "source": "ONTOLOGY", "support": [child],
                                 "rule": "ONTOLOGY_PARENT"})
                return self._proof(subject_id, target_concept, path)
        return None

    def _proof_edge(self, edge):
        return {"subject": edge.subject, "predicate": edge.predicate,
                "object": self._node_concept(edge.object) or edge.object,
                "status": edge.status, "source": edge.source,
                "support": list(edge.support), "rule": edge.attributes.get("rule")}

    def _proof(self, subject_id, target_concept, path):
        return {"subject": subject_id, "target": target_concept, "status": "PROVEN", "path": path}

    def objects(self, subject_id, predicate):
        return [edge.object for edge in self.graph.edges_from(subject_id, predicate) if edge.status != "CONFLICTED"]

    def subjects(self, object_id, predicate):
        return [edge.subject for edge in self.graph.edges_to(object_id, predicate) if edge.status != "CONFLICTED"]
