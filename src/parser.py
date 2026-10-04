from dataclasses import dataclass
from .tokenizer import tokenize
from .compositional_parser import CompositionalGrammarParser
from .semantic_composer import SemanticComposer


@dataclass
class ParsedSentence:
    subject_word: str | None = None
    verb_word: str | None = None
    object_word: str | None = None
    subject_surface_word: str | None = None
    verb_surface_word: str | None = None
    object_surface_word: str | None = None
    negated: bool = False
    question_type: str | None = None
    rule: str | None = None
    meaning: str | None = None
    operation: str | None = None
    relation: str | None = None
    relationship_target: str | None = None
    tokens: list[str] | None = None
    parse_status: str = "UNKNOWN"
    parse_candidates: tuple = ()
    semantic_structure: dict | None = None


class Parser:
    def __init__(self, lexicon=None, grammar_path="knowledge/grammar_foundation.json"):
        self.lexicon = lexicon
        self.grammar_path = grammar_path
        self.compositional = (
            CompositionalGrammarParser(lexicon)
            if lexicon is not None
            else None
        )
        self.semantic_composer = (
            SemanticComposer(lexicon, self.compositional)
            if self.compositional is not None
            else None
        )

    def _pos(self, word):
        return self.lexicon.pos(word) if self.lexicon else None

    def _concept(self, word):
        if self.lexicon is None:
            return None
        return self.lexicon.concept(word)

    def _from_compositional(self, tokens, surface_tokens):
        if self.compositional is None:
            return None

        first_categories = self.compositional.lexical_categories(tokens[0])
        start_by_category = self.compositional.grammar.get("start_symbol_by_first_category", {})
        start_symbols = []
        for category in first_categories:
            symbol = start_by_category.get(category, "STATEMENT")
            if symbol not in start_symbols:
                start_symbols.append(symbol)
        candidates = []
        for start_symbol in start_symbols:
            candidates.extend(self.compositional.parse(tokens, start_symbol=start_symbol))
        if not candidates:
            return None

        if len(candidates) > 1:
            return ParsedSentence(
                tokens=tokens,
                parse_status="AMBIGUOUS",
                parse_candidates=tuple(
                    self.compositional.derivation_signature(candidate)
                    for candidate in candidates
                ),
            )

        node = candidates[0]
        production = self.compositional.production_for(node)
        if not production:
            return None

        def token_for(role):
            index = self.compositional.role_token_index(node, role)
            return tokens[index] if index is not None else None

        def surface_for(role):
            index = self.compositional.role_token_index(node, role)
            return surface_tokens[index] if index is not None else None

        semantic_structure = self.semantic_composer.compose(node, tokens) if self.semantic_composer else None

        return ParsedSentence(
            subject_word=token_for("subject"),
            verb_word=token_for("verb"),
            object_word=token_for("object"),
            subject_surface_word=surface_for("subject"),
            verb_surface_word=surface_for("verb"),
            object_surface_word=surface_for("object"),
            question_type=production.get("question_type"),
            rule=production.get("legacy_rule") or production.get("name"),
            meaning=production.get("meaning"),
            operation=production.get("operation"),
            relation=production.get("relation"),
            negated=bool(production.get("negated", False)),
            tokens=tokens,
            parse_status="DETERMINED",
            parse_candidates=(self.compositional.derivation_signature(node),),
            semantic_structure=semantic_structure,
        )

    def parse(self, text):
        surface_tokens = tokenize(text) if isinstance(text, str) else list(text)
        tokens = [token.lower() for token in surface_tokens]
        if not tokens:
            return ParsedSentence(tokens=tokens, parse_status="UNPARSED")
        compositional = self._from_compositional(tokens, surface_tokens)
        if compositional is not None:
            return compositional
        return self.parse_statement(tokens, surface_tokens=surface_tokens)

    def parse_statement(self, tokens, surface_tokens=None):
        """Parse through the authoritative V1 grammar foundation."""
        surface_tokens = surface_tokens if surface_tokens is not None else tokens
        return self._from_compositional(list(tokens), list(surface_tokens))
