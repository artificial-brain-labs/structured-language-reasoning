import json

from src.compositional_parser import CompositionalGrammarParser
from src.lexicon import Lexicon
from src.parser import Parser


def test_compositional_parser_preserves_multiple_derivations(tmp_path):
    grammar = {
        "version": "test",
        "lexical_categories": ["NOUN"],
        "phrase_categories": ["NP"],
        "productions": [
            {"name": "np_noun_primary", "lhs": "NP", "rhs": ["NOUN"], "head": 0},
            {"name": "np_noun_alternative", "lhs": "NP", "rhs": ["NOUN"], "head": 0}
        ]
    }
    grammar_path = tmp_path / "ambiguous_grammar.json"
    grammar_path.write_text(json.dumps(grammar), encoding="utf-8")

    parser = CompositionalGrammarParser(Lexicon(), grammar_path=str(grammar_path))
    candidates = parser.parse(["cat"], start_symbol="NP")

    assert len(candidates) == 2
    signatures = {parser.derivation_signature(candidate) for candidate in candidates}
    assert signatures == {
        ("np_noun_primary", ("NOUN",)),
        ("np_noun_alternative", ("NOUN",)),
    }


def test_parser_does_not_fallback_when_compositional_parse_is_ambiguous(tmp_path):
    grammar = {
        "version": "test",
        "lexical_categories": ["NOUN"],
        "phrase_categories": ["NP", "STATEMENT"],
        "start_symbol_by_first_category": {"NOUN": "STATEMENT"},
        "productions": [
            {"name": "statement_primary", "lhs": "STATEMENT", "rhs": ["NP"], "head": 0},
            {"name": "statement_alternative", "lhs": "STATEMENT", "rhs": ["NP"], "head": 0},
            {"name": "np_noun", "lhs": "NP", "rhs": ["NOUN"], "head": 0}
        ]
    }
    grammar_path = tmp_path / "ambiguous_grammar.json"
    grammar_path.write_text(json.dumps(grammar), encoding="utf-8")

    parser = Parser(Lexicon(), grammar_path="knowledge/grammar.json")
    parser.compositional = CompositionalGrammarParser(
        Lexicon(), grammar_path=str(grammar_path)
    )

    result = parser.parse("cat")

    assert result.parse_status == "AMBIGUOUS"
    assert result.rule is None
    assert len(result.parse_candidates) == 2
