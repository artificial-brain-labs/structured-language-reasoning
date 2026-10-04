from dataclasses import dataclass

from .inference_rules import InferenceRules
from .relations import RelationSchema
from .semantic_graph import GraphEdge, SemanticGraph


@dataclass(frozen=True)
class ReasoningResult:
    """A reasoning result that is explicitly derived and non-persistent."""

    edges: tuple[GraphEdge, ...]


class SemanticGraphReasoner:
    """Derive knowledge from asserted graph relationships and ontology data.

    Relation roles are read from declarative relation schemas. The reasoner is
    a mechanism: it does not embed domain relation names in procedural logic.
    Only ASSERTED classification edges may serve as evidence for derivation.
    """

    def __init__(self, ontology, relation_schemas=None, inference_rules=None):
        self.ontology = ontology
        self.relation_schemas = relation_schemas or RelationSchema().schemas
        self.inference_rules = inference_rules or InferenceRules()

    def _relation_for_role(self, role):
        candidates = [
            (schema.get("priority", 0), name)
            for name, schema in self.relation_schemas.items()
            if schema.get("role") == role
        ]
        if not candidates:
            return None
        highest = max(priority for priority, _ in candidates)
        matches = [name for priority, name in candidates if priority == highest]
        return matches[0] if len(matches) == 1 else None

    def reason(self, graph: SemanticGraph) -> ReasoningResult:
        """Derive only from asserted graph evidence and declared knowledge.

        Ontology inheritance is derived from asserted taxonomic edges. Other
        transitive derivations are driven by the declarative inference-rule
        registry. Derived edges never become evidence during the same pass.
        """
        derived = []
        taxonomic_relation = self._relation_for_role("canonical_taxonomic")

        if taxonomic_relation:
            for edge in graph.asserted_edges():
                if edge.predicate != taxonomic_relation:
                    continue
                concept_node = graph.nodes.get(edge.object)
                if concept_node is None or not self.ontology.class_exists(concept_node.concept):
                    continue
                current_id = edge.object
                for ancestor in self.ontology.ancestors(concept_node.concept):
                    target_id = self._concept_node(graph, ancestor)
                    if target_id is None:
                        continue
                    derived.append(
                        self._edge(
                            edge, current_id, target_id, ancestor, len(derived) + 1,
                            taxonomic_relation, support=(edge.edge_id,),
                            rule="ONTOLOGY_PARENT",
                        )
                    )
                    current_id = target_id

        for rule in self.inference_rules.enabled():
            if rule.get("type") != "TRANSITIVE":
                continue
            relation = rule.get("relation")
            target = (rule.get("derive") or {}).get("predicate")
            if not relation or not target:
                continue
            asserted = [edge for edge in graph.asserted_edges() if edge.predicate == relation]
            for first in asserted:
                for second in asserted:
                    if first.object != second.subject or first.subject == second.object:
                        continue
                    derived.append(
                        GraphEdge(
                            edge_id=f"derived:{len(derived) + 1:04d}",
                            subject=first.subject,
                            predicate=target,
                            object=second.object,
                            status="DERIVED",
                            source="INFERENCE",
                            confidence=1.0,
                            support=(first.edge_id, second.edge_id),
                            attributes={"rule": rule.get("name")},
                        )
                    )

        return ReasoningResult(tuple(self._deduplicate(derived)))

    def _concept_node(self, graph, concept):
        for node in graph.nodes.values():
            if node.node_type in {"CONCEPT", "CLASS"} and node.concept == concept:
                return node.node_id
        return None

    def _edge(self, support_edge, subject_id, target_id, ancestor, index, taxonomic_relation, support=(), rule=None):
        return GraphEdge(
            edge_id=f"derived:{index:04d}",
            subject=subject_id,
            predicate=taxonomic_relation,
            object=target_id,
            status="DERIVED",
            source="ONTOLOGY",
            confidence=1.0,
            support=tuple(support) or (support_edge.edge_id,),
            attributes={
                "reason": "ontology_ancestor",
                "concept": ancestor,
                "rule": rule or "ONTOLOGY_PARENT",
            },
        )

    def _deduplicate(self, edges):
        seen = set()
        result = []
        for edge in edges:
            key = (edge.subject, edge.predicate, edge.object)
            if key in seen:
                continue
            seen.add(key)
            result.append(edge)
        return result
