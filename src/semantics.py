from dataclasses import dataclass, field


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
    """A mechanism-level operation produced from structured meaning.

    Operation names describe execution mechanics. Domain concepts and
    relations remain data-driven and are carried as operation data.
    """

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


class SemanticParser:
    def __init__(self, lexicon=None):
        self.lexicon = lexicon
        self.entity_counter = 0

    def _concept(self, word):
        if not self.lexicon:
            return None
        return self.lexicon.concept(word)

    def _new_entity_id(self, concept, word=None):
        self.entity_counter += 1
        base = (concept or word or "unknown").lower()
        return f"{base}_{self.entity_counter:03d}"

    def _entity(self, word):
        concept = self._concept(word) or "UNKNOWN"
        return Entity(self._new_entity_id(concept, word), concept)

    def _operation_attributes(self, subject_word=None, object_word=None):
        attributes = {}
        if subject_word is not None:
            attributes["subject_word"] = subject_word
        if object_word is not None:
            attributes["object_word"] = object_word
        return attributes

    def parse(self, tree):
        meaning = SemanticRepresentation()

        if tree.meaning == "SUBJECT_STATE":
            subject = self._entity(tree.subject_word)
            state_concept = self._concept(tree.verb_word)
            if not state_concept:
                return meaning

            meaning.entities.append(subject)
            meaning.facts.append(Fact(subject=subject.entity_id, predicate=state_concept))
            meaning.operation = SemanticOperation(
                name=tree.operation,
                subject=subject.entity_id,
                predicate=state_concept,
                attributes=self._operation_attributes(tree.subject_word),
            ) if tree.operation else None
            return meaning

        if tree.meaning == "SUBJECT_VERB_OBJECT":
            subject = self._entity(tree.subject_word)
            object_ = self._entity(tree.object_word)
            predicate = self._concept(tree.verb_word)
            if not predicate:
                return meaning

            if tree.negated:
                predicate = f"NOT_{predicate}"

            meaning.entities.extend([subject, object_])
            meaning.facts.append(
                Fact(subject=subject.entity_id, predicate=predicate, object=object_.entity_id)
            )
            meaning.operation = SemanticOperation(
                name=tree.operation,
                subject=subject.entity_id,
                predicate=predicate,
                object=object_.entity_id,
                attributes=self._operation_attributes(tree.subject_word, tree.object_word),
            ) if tree.operation else None
            return meaning

        if tree.meaning == "TYPE_ASSIGNMENT":
            subject = self._entity(tree.subject_word)
            object_ = self._entity(tree.object_word)
            if not tree.relation:
                return meaning

            meaning.entities.extend([subject, object_])
            meaning.facts.append(
                Fact(subject=subject.entity_id, predicate=tree.relation, object=object_.entity_id)
            )
            meaning.operation = SemanticOperation(
                name=tree.operation,
                subject=subject.entity_id,
                predicate=tree.relation,
                object=object_.entity_id,
                attributes=self._operation_attributes(tree.subject_word, tree.object_word),
            ) if tree.operation else None
            return meaning

        if tree.meaning == "SUBJECT_RELATION":
            subject = self._entity(tree.subject_word)
            object_ = self._entity(tree.object_word)
            if not tree.relation:
                return meaning

            meaning.entities.extend([subject, object_])
            meaning.facts.append(
                Fact(subject=subject.entity_id, predicate=tree.relation, object=object_.entity_id)
            )
            meaning.operation = SemanticOperation(
                name=tree.operation,
                subject=subject.entity_id,
                predicate=tree.relation,
                object=object_.entity_id,
                attributes=self._operation_attributes(tree.subject_word, tree.object_word),
            ) if tree.operation else None
            return meaning

        return meaning
