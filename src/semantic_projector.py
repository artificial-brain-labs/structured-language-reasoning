from .semantic_graph import GraphEdge, GraphNode, SemanticGraph


class SemanticGraphProjector:
    """Project composed sentence semantics into a non-persistent semantic graph.

    Projection preserves what the grammar and lexicon explicitly provide. It does
    not promote sentence content into system knowledge or user memory and it does
    not infer missing concepts.
    """

    def __init__(self, relation_schemas=None):
        self.relation_schemas = relation_schemas or {}

    def project(self, semantic_structure, source="INTERACTION", support=(), entity_resolver=None):
        graph = SemanticGraph(relation_schemas=self.relation_schemas)
        if not semantic_structure or semantic_structure.get("category") != "STATEMENT":
            return graph

        roles = semantic_structure.get("roles", {})
        subject = roles.get("subject")
        object_ = roles.get("object")
        verb = roles.get("verb")
        if not subject:
            return graph

        subject_id = self._project_np(graph, subject, "subject", entity_resolver)
        object_id = self._project_np(graph, object_, "object", entity_resolver) if object_ else None

        if subject_id and object_id and verb:
            predicate = self._head(verb).get("concept")
            if predicate and predicate != "UNKNOWN":
                self._add_edge(graph, subject_id, predicate, object_id, source, support, "relation")
        return graph

    def _project_np(self, graph, structure, role, entity_resolver):
        head = self._head(structure)
        concept = head.get("concept")
        token = head.get("token")
        if not token or not concept or concept == "UNKNOWN":
            return None

        resolved = entity_resolver(token, concept) if entity_resolver else None
        if resolved:
            node_id = resolved
            node_type = "ENTITY"
            name = token
        else:
            node_id = f"sentence:{role}:{token}"
            node_type = "REFERENT"
            name = token
        graph.add_node(GraphNode(node_id, node_type, name, concept, attributes={"role": role}))

        for modifier in self._modifiers(structure):
            modifier_concept = modifier.get("concept")
            if not modifier_concept or modifier_concept == "UNKNOWN":
                continue
            property_id = f"concept:{modifier_concept}"
            graph.add_node(GraphNode(property_id, "PROPERTY", modifier.get("token", modifier_concept), modifier_concept))
            self._add_edge(graph, node_id, "HAS_PROPERTY", property_id, "SEMANTIC_PROJECTION", (), "modifier")
        return node_id

    def _head(self, structure):
        current = structure or {}
        while isinstance(current, dict) and "head" in current:
            current = current["head"]
        return current if isinstance(current, dict) else {}

    def _modifiers(self, structure):
        modifiers = []
        if not isinstance(structure, dict):
            return modifiers
        if structure.get("category") == "ADJECTIVE":
            modifiers.append(structure)
        for child in structure.get("children", []):
            modifiers.extend(self._modifiers(child))
        return modifiers

    def _add_edge(self, graph, subject, predicate, object_, source, support, kind):
        edge_id = f"projection:{len(graph.edges) + 1:04d}"
        graph.add_edge(GraphEdge(
            edge_id=edge_id,
            subject=subject,
            predicate=predicate,
            object=object_,
            status="OBSERVED",
            source=source,
            confidence=1.0,
            support=tuple(support),
            attributes={"projection_kind": kind},
        ))
