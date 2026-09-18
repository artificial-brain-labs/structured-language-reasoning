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
    production_name: str | None = None


class CompositionalGrammarParser:
    """Data-driven CFG parser for the foundational language grammar.

    The parser returns all valid derivations. A parse node records the
    production that created it so alternative derivations remain distinct
    instead of being silently collapsed.
    """

    def __init__(self, lexicon, grammar_path="knowledge/grammar_foundation.json"):
        self.lexicon = lexicon
        with open(grammar_path, "r", encoding="utf-8") as file:
            self.grammar = json.load(file)
        self.productions = self.grammar.get("productions", [])
        self.by_lhs = {}
        for production in self.productions:
            self.by_lhs.setdefault(production["lhs"], []).append(production)
        self._lexical_categories = set(self.grammar.get("lexical_categories", []))

    def lexical_categories(self, word):
        if self.lexicon is not None and hasattr(self.lexicon, "pos_candidates"):
            categories = self.lexicon.pos_candidates(word)
            if categories:
                return tuple(categories)
        pos = self.lexicon.pos(word) if self.lexicon else None
        return (pos,) if pos else ("ENTITY",)

    def lexical_category(self, word):
        return self.lexical_categories(word)[0]

    def _head_lexical_category(self, node):
        if node.category in self._lexical_categories:
            return node.category
        if node.head_index is None:
            return None
        return self._head_lexical_category(node.children[node.head_index])

    def _constraints_match(self, production, children):
        for index, allowed in production.get("constraints", {}).get("head_categories", {}).items():
            index = int(index)
            if index >= len(children):
                return False
            if self._head_lexical_category(children[index]) not in allowed:
                return False
        return True

    def parse(self, tokens, start_symbol="STATEMENT"):
        tokens = list(tokens)
        lexical_categories = tuple(self.lexical_categories(token) for token in tokens)

        @lru_cache(maxsize=None)
        def parse_category(category, start, end):
            candidates = []
            if end == start + 1 and category in lexical_categories[start]:
                candidates.append(ParseNode(category, start, end))
            for production in self.by_lhs.get(category, []):
                for children in parse_sequence(tuple(production.get("rhs", [])), start, end):
                    if self._constraints_match(production, children):
                        candidates.append(ParseNode(
                            category,
                            start,
                            end,
                            tuple(children),
                            production.get("head"),
                            production.get("name"),
                        ))
            return tuple(candidates)

        @lru_cache(maxsize=None)
        def parse_sequence(symbols, start, end):
            if not symbols:
                return ((),) if start == end else ()
            if len(symbols) == 1:
                return tuple((node,) for node in parse_category(symbols[0], start, end))

            results = []
            for split in range(start + 1, end):
                left_nodes = parse_category(symbols[0], start, split)
                if not left_nodes:
                    continue
                for left in left_nodes:
                    for rest in parse_sequence(symbols[1:], split, end):
                        results.append((left,) + rest)
            return tuple(results)

        return parse_category(start_symbol, 0, len(tokens))

    def production_for(self, node):
        if node.production_name is not None:
            for production in self.by_lhs.get(node.category, []):
                if production.get("name") == node.production_name:
                    return production
        for production in self.by_lhs.get(node.category, []):
            rhs = production.get("rhs", [])
            if len(rhs) == len(node.children) and all(
                child.category == symbol for child, symbol in zip(node.children, rhs)
            ) and self._constraints_match(production, node.children):
                return production
        return None

    def derivation_signature(self, node):
        """Return a stable, data-derived representation of one parse tree."""
        if node.production_name is None:
            return node.category
        children = tuple(self.derivation_signature(child) for child in node.children)
        return (node.production_name, children)

    def role_token_index(self, node, role):
        production = self.production_for(node)
        role_path = production.get("roles", {}).get(role) if production else None
        if not role_path or role_path[1] != "head":
            return None
        return self._head_token_index(node.children[int(role_path[0])])

    def _head_token_index(self, node):
        if node.head_index is None:
            return node.start if node.end == node.start + 1 else None
        return self._head_token_index(node.children[node.head_index])
