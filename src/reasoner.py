from .inference_rules import InferenceRules
from .graph_builder import SemanticGraphBuilder
from .graph_reasoner import SemanticGraphReasoner


class Reasoner:
    def __init__(self, ontology, memory, inference_rules=None):
        self.ontology = ontology
        self.memory = memory
        self.inference_rules = inference_rules or InferenceRules()
        self.graph_reasoner = SemanticGraphReasoner(
            ontology,
            getattr(memory.relations, "schemas", {}),
            self.inference_rules,
        )
        self.graph_builder = SemanticGraphBuilder(ontology)

    def relation_name_for_role(self, role):
        """Resolve a relation role using explicit declarative priority."""
        candidates = [
            (schema.get("priority", 0), name)
            for name, schema in self.memory.relations.schemas.items()
            if schema.get("role") == role
        ]
        if not candidates:
            return None
        highest = max(priority for priority, _ in candidates)
        matches = [name for priority, name in candidates if priority == highest]
        return matches[0] if len(matches) == 1 else None

    def explicit_types(self, entity_id):
        """Return directly asserted user classifications for an entity."""
        if entity_id not in self.memory.entities:
            return []
        types = []
        for memory in self.memory.query(subject=entity_id, predicate="IS_A"):
            if memory.status != "ASSERTED":
                continue
            concept = self.memory.entities.get(memory.object, {}).get("concept")
            if concept and concept != "UNKNOWN" and concept not in types:
                types.append(concept)
        return types

    def known_types(self, entity_id):
        """Return explicit types plus ontology ancestors, without storing them."""
        types = list(self.explicit_types(entity_id))
        for concept in list(types):
            for ancestor in self.ontology.ancestors(concept):
                if ancestor not in types:
                    types.append(ancestor)
        return types

    def validate_relation(self, subject_entity, predicate, object_entity):
        schema = self.memory.relations.get(predicate)
        if not schema:
            return False
        subject_concepts = self.known_types(subject_entity)
        object_concepts = self.known_types(object_entity)

        if not subject_concepts:
            subject_concept = self.memory.entities[subject_entity]["concept"]
            if subject_concept != "UNKNOWN":
                subject_concepts = [subject_concept, *self.ontology.ancestors(subject_concept)]

        if not object_concepts:
            object_concept = self.memory.entities[object_entity]["concept"]
            if object_concept != "UNKNOWN":
                object_concepts = [object_concept, *self.ontology.ancestors(object_concept)]

        required_subject = schema.get("subject_type")
        required_object = schema.get("object_type")
        if required_subject and not any(self.ontology.is_a(concept, required_subject) for concept in subject_concepts):
            return False
        if required_object and not object_concepts:
            return schema.get("allow_unknown_object", False)
        if required_object and not any(self.ontology.is_a(concept, required_object) for concept in object_concepts):
            return False
        return True

    def _compatibility_seed(self, graph, entity_id):
        """Return a temporary class seed for legacy class-handle queries."""
        entity = self.memory.entities.get(entity_id)
        concept = entity.get("concept") if entity else None
        if not concept or not self.ontology.class_exists(concept):
            return

        if any(edge.subject == entity_id and edge.predicate == "IS_A" for edge in graph.asserted_edges()):
            return

        concept_node = next(
            (node.node_id for node in graph.nodes.values()
             if node.node_type == "CLASS" and node.concept == concept),
            None,
        )
        if concept_node is None:
            return

        from .semantic_graph import GraphEdge
        graph.add_edge(
            GraphEdge(
                edge_id=f"compatibility_seed:{entity_id}",
                subject=entity_id,
                predicate="IS_A",
                object=concept_node,
                status="ASSERTED",
                source="SYSTEM",
            )
        )

    def _canonical_result_for_entity(self, graph, entity_id):
        """Project canonical class-chain derivations onto a legacy entity API.

        This translates representation only. It does not perform inference.
        """
        asserted_types = self.explicit_types(entity_id)
        if asserted_types:
            starting_concepts = set(asserted_types)
        else:
            entity = self.memory.entities.get(entity_id, {})
            concept = entity.get("concept")
            starting_concepts = {concept} if concept and self.ontology.class_exists(concept) else set()

        reasoning = self.graph_reasoner.reason(graph)
        results = []
        for edge in reasoning.edges:
            subject_concept = graph.nodes.get(edge.subject).concept if edge.subject in graph.nodes else None
            if subject_concept not in starting_concepts and not any(
                self.ontology.is_a(concept, subject_concept) for concept in starting_concepts
            ):
                continue
            object_concept = graph.nodes.get(edge.object).concept if edge.object in graph.nodes else edge.object
            results.append({
                "entity": entity_id,
                "predicate": edge.predicate,
                "object": object_concept,
                "status": edge.status,
                "source": edge.source,
                "support": list(edge.support),
                "rule": edge.attributes.get("rule"),
            })
        return results

    def infer_is_a(self, entity_id):
        """Compatibility projection over the canonical graph reasoning kernel."""
        graph = self.graph_builder.build(self.memory)
        self._compatibility_seed(graph, entity_id)
        return self._canonical_result_for_entity(graph, entity_id)

    def _legacy_subject(self, graph, subject_id):
        node = graph.nodes.get(subject_id)
        if node is None:
            return subject_id
        if node.node_type == "ENTITY":
            return node.name
        return subject_id

    def _legacy_object(self, graph, object_id):
        """Project graph objects without losing memory-level entity identity."""
        if object_id in self.memory.entities:
            return object_id
        node = graph.nodes.get(object_id)
        if node is None:
            return object_id
        return node.concept or node.name or object_id

    def derive(self):
        """Compatibility projection over canonical graph reasoning."""
        graph = self.graph_builder.build(self.memory)
        reasoning = self.graph_reasoner.reason(graph)
        results = []
        for edge in reasoning.edges:
            results.append({
                "subject": self._legacy_subject(graph, edge.subject),
                "predicate": edge.predicate,
                "object": self._legacy_object(graph, edge.object),
                "status": edge.status,
                "source": edge.source,
                "support": list(edge.support),
                "rule": edge.attributes.get("rule"),
            })
        return results
