import json
from pathlib import Path

from .graph_query import SemanticGraphQuery


class QueryEngine:
    def __init__(self, memory, lexicon, reasoner=None, policy_path=None, graph=None, relationship_memory=None):
        self.memory = memory
        self.lexicon = lexicon
        self.reasoner = reasoner
        self.graph = graph
        self.graph_query = SemanticGraphQuery(graph) if graph is not None else None
        self.relationship_memory = relationship_memory
        path = policy_path or Path(__file__).resolve().parent.parent / "knowledge" / "query_policy.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.policy = data.get("question_types", {})

    def _resolve(self, word):
        concept = self.lexicon.concept(word)
        if concept:
            entity = self.memory.find_entity(concept)
        else:
            entity = self.memory.find_named_entity(word)
        return self.memory.canonical_entity(entity) if entity else None

    def _canonical_id(self, entity_id):
        return self.memory.canonical_entity(entity_id)

    def _classification(self, parsed):
        """Return graph-backed asserted or derived type evidence."""
        subject = self._resolve(parsed.subject_word)
        target_concept = self.lexicon.concept(parsed.object_word)
        if subject is None or target_concept is None:
            return []

        if self.graph_query is not None:
            path = self.graph_query.classification(subject, target_concept)
            if path:
                last = path[-1]
                status = "ASSERTED" if len(path) == 1 and last.status == "ASSERTED" else "DERIVED"
                proof = self.graph_query.explain_classification(subject, target_concept)
                return [{
                    "entity": subject,
                    "predicate": "IS_A",
                    "object": target_concept,
                    "status": status,
                    "source": last.source,
                    "support": list(last.support) or path,
                    "path": path,
                    "proof": proof,
                }]

        target_entity = self.memory.find_entity(target_concept)
        asserted_classifications = [
            memory
            for memory in self.memory.query(subject=subject, predicate="IS_A")
            if memory.status == "ASSERTED"
            and self._canonical_id(memory.object) == target_entity
        ]
        if asserted_classifications:
            memory = asserted_classifications[0]
            return [{
                "entity": subject,
                "predicate": "IS_A",
                "object": target_concept,
                "status": "ASSERTED",
                "source": memory.source,
                "support": [memory],
            }]

        subject_concept = self.memory.entities[subject]["concept"]
        if subject_concept == target_concept:
            return [{
                "entity": subject,
                "predicate": "IS_A",
                "object": target_concept,
                "status": "ASSERTED",
                "source": "MEMORY",
                "support": [subject],
            }]

        if self.reasoner is not None:
            for derived in self.reasoner.infer_is_a(subject):
                if derived["object"] == target_concept:
                    return [derived]

            for memory in self.memory.query(subject=subject, predicate="IS_A"):
                if memory.status != "ASSERTED":
                    continue
                source_concept = self.memory.entities.get(memory.object, {}).get("concept")
                if source_concept and self.reasoner.ontology.is_a(source_concept, target_concept):
                    return [{
                        "entity": subject,
                        "predicate": "IS_A",
                        "object": target_concept,
                        "status": "DERIVED",
                        "source": "ONTOLOGY",
                        "support": [memory],
                    }]

            for derived in self.reasoner.derive():
                if (
                    derived["subject"] == subject
                    and derived["predicate"] == "IS_A"
                    and self._canonical_id(derived["object"]) == target_entity
                ):
                    return [derived]

            if subject_concept != "UNKNOWN" and self.reasoner.ontology.is_a(subject_concept, target_concept):
                return [{
                    "entity": subject,
                    "predicate": "IS_A",
                    "object": target_concept,
                    "status": "DERIVED",
                    "source": "ONTOLOGY",
                    "support": [subject_concept],
                }]

        return []

    def _entity_type(self, parsed):
        """Return explicit type evidence, or an explicit user relationship."""
        entity = self._resolve(parsed.subject_word)
        if entity is not None:
            if self.graph_query is not None:
                asserted = [
                    edge for edge in self.graph.edges_from(entity, "IS_A")
                    if edge.status == "ASSERTED"
                ]
                for edge in asserted:
                    concept = self._node_concept(edge.object)
                    if concept and concept != "UNKNOWN":
                        return [{
                            "entity": entity,
                            "predicate": "IS_A",
                            "object": concept,
                            "status": "ASSERTED",
                            "source": edge.source,
                            "support": list(edge.support),
                        }]
            else:
                for memory in self.memory.query(subject=entity, predicate="IS_A"):
                    if memory.status != "ASSERTED":
                        continue
                    object_entity = self._canonical_id(memory.object)
                    concept = self.memory.entities.get(object_entity, {}).get("concept")
                    if concept and concept != "UNKNOWN":
                        return [{
                            "entity": entity,
                            "predicate": "IS_A",
                            "object": concept,
                            "status": "ASSERTED",
                            "source": memory.source,
                            "support": [memory],
                        }]

        # A person relationship is not an ontology type. It is a separate,
        # explicit piece of USER MEMORY and therefore can answer WHO/WHAT
        # without guessing that the person belongs to an ontology class.
        if self.relationship_memory is not None:
            people = self.relationship_memory.find_people_by_name(parsed.subject_word)
            if people:
                person = people[0]
                relationships = [
                    record for record in self.relationship_memory.relationships.values()
                    if record.person_id == person.person_id
                ]
                if relationships:
                    return [{
                        "person_id": person.person_id,
                        "person_name": person.name,
                        "relation": relationships[0].relation,
                        "status": relationships[0].verification_state,
                    }]

        return []

    def _node_concept(self, node_id):
        node = self.graph.nodes.get(node_id)
        return node.concept if node else None

    def answer(self, parsed):
        policy = self.policy.get(parsed.question_type)
        if policy is None:
            return []

        result_kind = policy.get("result_kind")
        if result_kind == "classification":
            return self._classification(parsed)

        if result_kind == "entity_type":
            return self._entity_type(parsed)

        if result_kind == "object":
            subject = self._resolve(parsed.subject_word)
            predicate = self._relation(parsed.verb_word)
            if not subject or not predicate:
                return []
            if self.graph_query is not None:
                return self.graph_query.objects(subject, predicate)
            return [
                self._canonical_id(m.object)
                for m in self.memory.query(subject=subject, predicate=predicate)
                if m.status != "CONFLICTED"
            ]

        if result_kind == "subject":
            object_id = self._resolve(parsed.object_word)
            predicate = self._relation(parsed.verb_word)
            if not object_id or not predicate:
                return []
            if self.graph_query is not None:
                return self.graph_query.subjects(object_id, predicate)
            return [
                self._canonical_id(m.subject)
                for m in self.memory.query(predicate=predicate)
                if self._canonical_id(m.object) == object_id and m.status != "CONFLICTED"
            ]

        return []

    def _relation(self, word):
        return self.lexicon.feature(word, "relation") or self.lexicon.concept(word)
