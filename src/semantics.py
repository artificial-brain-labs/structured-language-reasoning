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
class SemanticRepresentation:
    entities: list[Entity] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)


class SemanticParser:

    def __init__(self, lexicon=None):
        self.lexicon = lexicon
        self.entity_counter = 0

    def _concept(self, word):

        if self.lexicon:
            concept = self.lexicon.concept(word)

            if concept:
                return concept

        # Handle forms that aren't yet in the lexicon.
        if word == "sleeping":
            return "SLEEP"

        return word.upper()

    def _new_entity_id(self, concept):

        self.entity_counter += 1

        return f"{concept.lower()}_{self.entity_counter:03d}"

    def parse(self, tree):

        meaning = SemanticRepresentation()

        # -------------------------------------------------
        # SUBJECT STATE
        #
        # A cat is sleeping.
        # -------------------------------------------------

        if tree.meaning == "SUBJECT_STATE":

            noun = tree.subject_word
            verb = tree.verb_word

            concept = self._concept(noun)

            # sleeping -> SLEEP
            predicate = self._concept(verb)

            entity_id = self._new_entity_id(concept)

            meaning.entities.append(
                Entity(
                    entity_id=entity_id,
                    concept=concept
                )
            )

            meaning.facts.append(
                Fact(
                    subject=entity_id,
                    predicate=predicate
                )
            )

            return meaning

        # -------------------------------------------------
        # SUBJECT VERB OBJECT
        #
        # The cat eats the mouse.
        # -------------------------------------------------

        if tree.meaning == "SUBJECT_VERB_OBJECT":

            subject_concept = self._concept(
                tree.subject_word
            )

            object_concept = self._concept(
                tree.object_word
            )

            predicate = self._concept(
                tree.verb_word
            )

            subject_id = self._new_entity_id(
                subject_concept
            )

            object_id = self._new_entity_id(
                object_concept
            )

            meaning.entities.extend([
                Entity(
                    entity_id=subject_id,
                    concept=subject_concept
                ),
                Entity(
                    entity_id=object_id,
                    concept=object_concept
                )
            ])

            if tree.negated:
                predicate = f"NOT_{predicate}"

            meaning.facts.append(
                Fact(
                    subject=subject_id,
                    predicate=predicate,
                    object=object_id
                )
            )

            return meaning

        return meaning