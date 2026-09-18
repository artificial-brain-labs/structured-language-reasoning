import json
from pathlib import Path

from .graph_query import SemanticGraphQuery
from .query_planner import QueryPlanner


class QueryEngine:
    def __init__(self, memory, lexicon, reasoner=None, policy_path=None, graph=None, relationship_memory=None):
        self.memory = memory
        self.lexicon = lexicon
        self.reasoner = reasoner
        self.graph = graph
        self.relationship_memory = relationship_memory
        self.identity_predicates = {
            predicate
            for predicate, schema in getattr(self.memory.relations, "schemas", {}).items()
            if schema.get("role") == "identity"
        }
        self.graph_query = (
            SemanticGraphQuery(
                graph,
                ontology=reasoner.ontology if reasoner is not None else None,
                identity_predicates=self.identity_predicates,
            )
            if graph is not None
            else None
        )
        path = policy_path or Path(__file__).resolve().parent.parent / "knowledge" / "query_policy.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.policy = data.get("question_types", {})
        self.planner = QueryPlanner(self.policy)

    def _resolve(self, word):
        """Resolve the explicit surface identity without collapsing it early."""
        concept = self.lexicon.concept(word)
        if concept:
            return self.memory.find_entity(concept)
        return self.memory.find_named_entity(word)

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
        """Return explicit type evidence or dictionary meaning without guessing."""
        senses = self.lexicon.senses(parsed.subject_word) if parsed.subject_word else []
        if len(senses) > 1:
            return [{
                "kind": "LEXICAL_AMBIGUITY",
                "word": parsed.subject_word,
                "senses": [
                    {"id": x.sense_id, "concept": x.concept, "definition": x.definition, "pos": x.pos}
                    for x in senses
                ],
            }]

        entity = self._resolve(parsed.subject_word)
        if entity is not None and self.graph_query is not None:
            result = self.graph_query.entity_type(entity)
            if result is not None:
                result["entity"] = entity
                return [result]

        if entity is not None:
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

        # A lexical noun may resolve to an ontology class rather than an
        # individual entity. Its type is the explicitly declared ontology
        # parent; no world knowledge is invented here.
        concept = self.lexicon.concept(parsed.subject_word)
        if concept and self.reasoner is not None and concept in self.reasoner.ontology.classes:
            parent = self.reasoner.ontology.parent(concept)
            if parent is not None:
                return [{
                    "entity": entity or concept,
                    "predicate": "IS_A",
                    "object": parent,
                    "status": "DERIVED",
                    "source": "ONTOLOGY",
                    "support": [concept],
                }]

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
                        "status": person.verification_state,
                    }]

        return []

    def _meaning(self, parsed):
        """Return dictionary senses only; do not convert meaning into type."""
        word = parsed.subject_word
        if not word:
            return []
        senses = self.lexicon.senses(word)
        if not senses:
            return []
        return [{
            "kind": "LEXICAL_MEANING",
            "word": word,
            "senses": [
                {
                    "id": sense.sense_id,
                    "concept": sense.concept,
                    "definition": sense.definition,
                    "pos": sense.pos,
                }
                for sense in senses
            ],
        }]

    def _property(self, parsed):
        subject = self._resolve(parsed.subject_word)
        value = self._resolve(parsed.object_word)
        if subject is None or value is None:
            return []
        if self.graph_query is not None:
            matches = self.graph_query.objects(subject, "HAS_PROPERTY")
        else:
            matches = [m.object for m in self.memory.query(subject=subject, predicate="HAS_PROPERTY")
                       if m.status != "CONFLICTED"]
        return [item for item in matches if self._canonical_id(item) == self._canonical_id(value)]

    def _objects(self, parsed):
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

    def _subjects(self, parsed):
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

    def _node_concept(self, node_id):
        node = self.graph.nodes.get(node_id)
        return node.concept if node else None

    def _relation(self, word):
        concept = self.lexicon.concept(word)
        if concept:
            entry = self.lexicon.get(word) if hasattr(self.lexicon, "get") else None
            if isinstance(entry, dict):
                return entry.get("relation") or concept
        return concept

    def answer(self, parsed):
        plan = self.planner.plan(parsed)
        if plan is None:
            return []
        handler_name = plan.get("handler")
        if not handler_name:
            return []
        handler = getattr(self, handler_name, None)
        if handler is None:
            return []
        return handler(parsed)
