import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClarificationRequest:
    """A pending clarification required before reasoning can continue."""

    entity_id: str
    question: str
    original_operation: object = None
    original_context: object = None


class ClarificationManager:
    """Manage unresolved clarification state without guessing.

    The manager records what remains unresolved and recognizes an explicit
    classification response for the pending entity. It never invents a type.
    """

    def __init__(self, memory, response_path=None):
        self.memory = memory
        self.pending = None
        path = response_path or Path(__file__).resolve().parent.parent / "knowledge" / "responses.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.system_responses = data.get("system", {})

    def request_lexical_meaning(self, word, candidates, original_text):
        """Ask the user to resolve a lexical ambiguity explicitly."""
        candidate_labels = []
        for candidate in candidates:
            label = candidate.get("id") if isinstance(candidate, dict) else getattr(candidate, "sense_id", None)
            if label:
                candidate_labels.append(label)
        if not candidate_labels:
            return None
        question = f"Which meaning of '{word}' do you mean: " + " or ".join(candidate_labels) + "?"
        self.pending = ClarificationRequest(
            entity_id="",
            question=question,
            original_context=original_text,
            kind="lexical_meaning",
            word=word,
            candidates=tuple(candidate_labels),
        )
        return self.pending

    def resolve_lexical_response(self, text):
        """Accept only an explicit candidate label; do not infer from free text."""
        if self.pending is None or self.pending.kind != "lexical_meaning":
            return None
        answer = text.strip().lower()
        for candidate in self.pending.candidates:
            if answer == candidate.lower():
                return candidate
        return None

    def request_entity_identity(self, entity_id, operation=None, context=None):
        if entity_id not in self.memory.entities:
            return None

        name = self.memory.entities[entity_id]["name"]
        template = self.system_responses.get("clarification_entity_identity")
        if template is None:
            return None
        try:
            question = template.format(entity_name=name)
        except (KeyError, ValueError):
            return None
        self.pending = ClarificationRequest(
            entity_id=entity_id,
            question=question,
            original_operation=operation,
            original_context=context,
        )
        return self.pending

    def has_pending(self):
        return self.pending is not None

    def current(self):
        return self.pending

    def matches_entity(self, entity_id):
        return self.pending is not None and self.pending.entity_id == entity_id

    def clear(self):
        pending = self.pending
        self.pending = None
        return pending
