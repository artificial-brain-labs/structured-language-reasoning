from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SemanticContextMatch:
    """Evidence-backed match between a current context and a learned sense."""
    sense_id: str
    score: int
    evidence: tuple[str, ...]


class SemanticContextResolver:
    """Resolve lexical meaning from structured, previously confirmed context.

    It compares parser-derived structure with contexts stored after explicit
    user clarification. It never creates a semantic fact or chooses between
    equally supported senses.
    """

    def __init__(self, contextual_memory=None, lexicon=None, ontology=None):
        self.contextual_memory = contextual_memory
        self.lexicon = lexicon
        self.ontology = ontology

    def _tokens(self, text):
        stopwords = getattr(self.contextual_memory, "STOPWORDS", set())
        return {
            token for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in stopwords
        }

    def _sense(self, sense_id):
        if self.lexicon is None:
            return None
        for entry in self.lexicon.words.values():
            for sense in entry.get("senses", []):
                if sense.get("id") == sense_id:
                    return sense
        return None

    def _definition_anchors(self, sense_id):
        if self.contextual_memory is None:
            return set()
        return self.contextual_memory._sense_anchors(sense_id)

    def _fields(self, context):
        if context is None:
            return {}
        features = dict(getattr(context, "features", {}) or {})
        return {
            "subject": (getattr(context, "subject", None) or "").lower(),
            "predicate": (getattr(context, "predicate", None) or "").lower(),
            "object": (getattr(context, "object", None) or "").lower(),
            "concepts": set(getattr(context, "concepts", ()) or ()),
            "relation": (features.get("relation") or "").lower(),
            "operation": (features.get("operation") or "").lower(),
            "grammar_rule": (features.get("grammar_rule") or "").lower(),
        }

    def _role(self, word, context):
        fields = self._fields(context)
        target = (word or "").lower()
        roles = set()
        if fields.get("subject") == target:
            roles.add("subject")
        if fields.get("predicate") == target:
            roles.add("predicate")
        if fields.get("object") == target:
            roles.add("object")
        return roles

    def _structured_evidence(self, word, current, learned):
        current_fields = self._fields(current)
        learned_fields = self._fields(learned)
        evidence = []

        shared_roles = self._role(word, current) & self._role(word, learned)
        same_relation = (
            current_fields.get("relation")
            and current_fields["relation"] == learned_fields.get("relation")
        )
        same_operation = (
            current_fields.get("operation")
            and current_fields["operation"] == learned_fields.get("operation")
        )

        # A grammatical role alone is not semantic evidence. Otherwise a
        # learned sense for "bat" as an object could leak into an unrelated
        # relation such as "eat bat". Role evidence is admitted only when
        # the surrounding structured relation or operation also agrees.
        if shared_roles and (same_relation or same_operation):
            evidence.append("same_role")
        if same_relation:
            evidence.append("same_relation")
        if same_operation:
            evidence.append("same_operation")

        shared = current_fields.get("concepts", set()) & learned_fields.get("concepts", set())
        evidence.extend(f"shared_concept:{value}" for value in sorted(shared))

        if (
            current_fields.get("grammar_rule")
            and current_fields["grammar_rule"] == learned_fields.get("grammar_rule")
        ):
            evidence.append("same_grammar_rule")
        return evidence

    def resolve(self, word, current_context, candidates=None):
        """Return a uniquely supported sense, or None when ambiguity remains.

        Explicit structural constraints are evaluated before learned context.
        In particular, an IS_A statement can constrain a lexical sense through
        the existing ontology without requiring a prior clarification.
        """
        if not word:
            return None

        allowed = set(candidates or ())
        dictionary_senses = {
            sense.sense_id: sense
            for sense in (self.lexicon.senses(word) if self.lexicon is not None else [])
        }
        if allowed:
            dictionary_senses = {
                sense_id: sense
                for sense_id, sense in dictionary_senses.items()
                if sense_id in allowed
            }
        if not dictionary_senses:
            return None

        current_fields = self._fields(current_context)
        current_relation = str(current_fields.get("relation") or "").upper()
        target_word = current_fields.get("object")

        # First apply an explicit ontology constraint. This is not a heuristic:
        # the sentence itself names a target class, and Ontology.is_a() defines
        # whether each candidate concept belongs to that class.
        if (
            self.ontology is not None
            and self.lexicon is not None
            and current_relation == "IS_A"
            and self._role(word, current_context) == {"subject"}
            and target_word
        ):
            target_senses = self.lexicon.senses(target_word)
            target_concepts = {
                sense.concept
                for sense in target_senses
                if sense.concept and self.ontology.class_exists(sense.concept)
            }
            if len(target_concepts) == 1:
                target = next(iter(target_concepts))
                compatible = [
                    sense_id
                    for sense_id, sense in dictionary_senses.items()
                    if sense.concept
                    and self.ontology.is_a(sense.concept, target)
                ]
                if len(compatible) == 1:
                    return compatible[0]
                # Zero or multiple compatible senses means the ontology has
                # not established a unique interpretation.
                return None

        if self.contextual_memory is None:
            return None

        matches = []
        for resolution in self.contextual_memory.find(word):
            if allowed and resolution.selected_sense_id not in allowed:
                continue

            evidence = self._structured_evidence(
                word, current_context, resolution.semantic_context
            )
            score = len(evidence) * 3

            current_tokens = self._tokens(getattr(current_context, "text", ""))
            learned_tokens = self._tokens(resolution.context)
            direct = (current_tokens & learned_tokens) - {word.lower()}
            evidence.extend(f"context_word:{value}" for value in sorted(direct))
            score += len(direct)

            anchors = self._definition_anchors(resolution.selected_sense_id)
            semantic_words = current_tokens & anchors
            evidence.extend(
                f"sense_definition:{value}" for value in sorted(semantic_words)
            )
            score += len(semantic_words)

            if score:
                matches.append(SemanticContextMatch(
                    resolution.selected_sense_id, score, tuple(evidence)
                ))

        if not matches:
            return None

        best_score = max(item.score for item in matches)
        best = [item for item in matches if item.score == best_score]
        sense_ids = {item.sense_id for item in best}
        if len(sense_ids) != 1:
            return None
        return next(iter(sense_ids))
\n