import json
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class ParseNode:
    category: str
    start: int
    end: int
    children: tuple = ()
    head_index: int | None = None


class CompositionalGrammarParser:
    """Data-driven CFG parser for the foundational language grammar.

    The parser knows how to compose categories. It does not contain English
    words, sentence-specific patterns, or semantic facts. Those belong in
    knowledge data. Ambiguity is represented as multiple candidates rather
    than resolved by guessing.
    """

    def __init__(self, lexicon, grammar_path="knowledge/grammar_foundation.json"):
        self.lexicon = lexicon
        with open(grammar_path, "r", encoding="utf-8") as file:
            self.grammar = json.load(file)
        self.productions = self.grammar.get("productions", [])
        self.by_lhs = {}
        for production in self.productions:
            self.by_lhs.setdefault(production["lhs"], []).append(production)

    def lexical_category(self, word):
        pos = self.lexicon.pos(word) if self.lexicon else None
        return pos or "ENTITY"

    def _head_lexical_category(self, node, lexical_categories):
        if node.head_index is None:
            return None
        child = node.children[node.head_index]
        if child.category in lexical_categories:
            return child.category
        return self._head_lexical_category(child, lexical_categories)

    def _constraints_match(self, production, children, lexical_categories):
        constraints = production.get("constraints", {})
        for index, allowed in constraints.get("head_categories", {}).items():
            index = int(index)
            if index >= len(children):
                return False
            actual = self._head_lexical_category(children[index], lexical_categories)
            if actual not in allowed:
                return False
        return True

    def parse(self, tokens, start_symbol="STATEMENT"):
        tokens = list(tokens)
        lexical_categories = {i: self.lexical_category(token) for i, token in enumerate(tokens)}

        @lru_cache(maxsize=None)
        def parse_category(category, start, end):
            candidates = []
            if end == start + 1 and lexical_categories[start] == category:
                candidates.append(ParseNode(category, start, end))
            for production in self.by_lhs.get(category, []):
                children_options = [[]]
                cursor = start
                possible = True
                for symbol in production.get("rhs", []):
                    next_options = []
                    for partial in children_options:
                        current = start if not partial else partial[-1].end
                        for child in parse_category(symbol, current, end):
                            next_options.append(partial + [child])
                    children_options = next_options
                    if not children_options:
                        possible = False
                        break
                if not possible:
                    continue
                for children in children_options:
                    if not children or children[-1].end != end:
                        continue
                    if children[0].start != start:
                        continue
                    head = production.get("head")
                    node = ParseNode(category, start, end, tuple(children), head)
                    if self._constraints_match(production, children, set(self.grammar.get("lexical_categories", []))):
                        candidates.append(node)
            return tuple(candidates)

        return parse_category(start_symbol, 0, len(tokens))

    def production_for(self, node):
        for production in self.by_lhs.get(node.category, []):
            rhs = production.get("rhs", [])
            if len(rhs) != len(node.children):
                continue
            if all(child.category == symbol for child, symbol in zip(node.children, rhs)):
                if self._constraints_match(production, node.children, set(self.grammar.get("lexical_categories", []))):
                    return production
        return None

    def role_token_index(self, node, role):
        production = self.production_for(node)
        if not production:
            return None
        role_path = production.get("roles", {}).get(role)
        if not role_path:
            return None
        child_index, selector = role_path
        child = node.children[child_index]
        if selector != "head":
            return None
        return self._head_token_index(child)

    def _head_token_index(self, node):
        if node.head_index is None:
            return node.start if node.end == node.start + 1 else None
        return self._head_token_index(node.children[node.head_index])
