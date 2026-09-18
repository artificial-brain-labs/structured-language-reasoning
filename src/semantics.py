import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Entity:
    entity_id: str
    concept: str


@dataclass
class Fact:
    subject: str
    predicate: str
    object: str | None = None


@dataclass
class SemanticOperation:
    name: str
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    attributes: dict = field(default_factory=dict)


@dataclass
class SemanticRepresentation:
    entities: list[Entity] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    operation: SemanticOperation | None = None


class SemanticMappings:
    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parent.parent / "knowledge" / "semantics.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.meanings = data.get("meanings", {})

    def get(self, meaning):
        return self.meanings.get(meaning)


class SemanticParser:
    def __init__(self, lexicon=None, mappings=None, contextual_memory=None, semantic_context_resolver=None):
        self.lexicon = lexicon
        self.mappings = mappings or SemanticMappings()
        self.entity_counter = 0
        self.contextual_memory = contextual_memory
        self.semantic_context_resolver = semantic_context_resolver

    def _concept(self, word):
        return self.lexicon.concept(word) if self.lexicon else None

    def _feature(self, word, name):
        return self.lexicon.feature(word, name) if self.lexicon else None

    def _new_entity_id(self, concept, word=None):
        self.entity_counter += 1
        base = (concept or word or "unknown").lower()
        return f"{base}_{self.entity_counter:03d}"

    def _entity(self, word, context=None):
        senses = self.lexicon.senses(word) if self.lexicon is not None else []
        concept = self._concept(word) or "UNKNOWN"
        selected_sense = None

        if len(senses) > 1 and self.semantic_context_resolver is not None:
            selected_sense = self.semantic_context_resolver.resolve(
                word,
                context,
                [sense.sense_id for sense in senses],
            )

        if selected_sense is None and len(senses) == 1:
            selected_sense = senses[0].sense_id

        if selected_sense:
            for sense in senses:
                if sense.sense_id == selected_sense:
                    concept = sense.concept or concept
                    break

        return Entity(self._new_entity_id(concept, word), concept)

    def _operation_attributes(self, subject_word=None, object_word=None, tree=None):
        attributes = {}
        if subject_word is not None:
            attributes["subject_word"] = subject_word
        if object_word is not None:
            attributes["object_word"] = object_word
        if tree is not None and tree.relationship_target:
            attributes["relationship_target"] = tree.relationship_target
        return attributes

    def _predicate(self, tree, mapping):
        definition = mapping.get("predicate")
        if not definition:
            return None
        source = definition.get("source")
        if source == "grammar":
            return getattr(tree, definition.get("field"), None)
        if source == "lexicon":
            feature = definition.get("feature")
            predicate = self._feature(tree.verb_word, feature)
            if predicate is None and definition.get("fallback"):
                predicate = self._feature(tree.verb_word, definition["fallback"])
            return predicate
        return None

    def _apply_negation(self, predicate, tree, mapping):
        if not tree.negated or not predicate:
            return predicate
        definition = mapping.get("negation")
        if not definition:
            return predicate
        return f"{definition.get('prefix', '')}{predicate}"

    def _operation_object(self, mapping, object_):
        if "object" in mapping:
            return mapping["object"]
        return object_.entity_id if object_ else None

    def _build_operation(self, tree, subject, predicate, object_value, object_entity=None):
        if not tree.operation:
            return None
        attributes = self._operation_attributes(tree.subject_word, tree.object_word, tree)
        if subject is not None:
            attributes["subject_concept"] = subject.concept
        if object_value is not None:
            attributes["object_concept"] = object_entity.concept if object_entity is not None else "UNKNOWN"
        return SemanticOperation(
            name=tree.operation,
            subject=subject.entity_id if subject else None,
            predicate=predicate,
            object=object_value,
            attributes=attributes,
        )

    def parse(self, tree, context=None):
        meaning = SemanticRepresentation()
        mapping = self.mappings.get(tree.meaning)
        if mapping is None:
            return meaning
        subject = self._entity(tree.subject_word, context=context) if tree.subject_word else None
        object_ = self._entity(tree.object_word, context=context) if tree.object_word else None
        predicate = self._predicate(tree, mapping)
        if predicate is None:
            return meaning
        predicate = self._apply_negation(predicate, tree, mapping)
        fact_object = self._operation_object(mapping, object_)
        if subject:
            meaning.entities.append(subject)
        if object_:
            meaning.entities.append(object_)
        meaning.facts.append(Fact(subject=subject.entity_id if subject else "", predicate=predicate, object=fact_object))
        meaning.operation = self._build_operation(tree, subject, predicate, fact_object, object_entity=object_)
        return meaning
