from src.compositional_parser import CompositionalGrammarParser
from src.lexicon import Lexicon
from src.parser import Parser
from src.semantic_composer import SemanticComposer


def test_semantic_composer_preserves_recursive_adjectives():
    lexicon = Lexicon()
    grammar = CompositionalGrammarParser(lexicon)
    candidates = grammar.parse(["the", "small", "black", "cat"], start_symbol="NP")
    assert len(candidates) == 1

    structure = SemanticComposer(lexicon, grammar).compose(candidates[0], ["the", "small", "black", "cat"])

    assert structure["category"] == "NP"
    assert structure["production"] == "np_determiner_adjp_noun"
    assert structure["head"]["token"] == "cat"
    assert structure["head"]["concept"] == "CAT"
    assert structure["children"][1]["production"] == "adjp_adjective_adjp"


def test_parser_exposes_composed_semantic_structure():
    tree = Parser(Lexicon()).parse("The small black cat eats the mouse.")

    assert tree.parse_status == "DETERMINED"
    assert tree.semantic_structure["category"] == "STATEMENT"
    assert tree.semantic_structure["production"] == "statement_transitive_np_verb_np"
    assert tree.semantic_structure["roles"]["subject"]["head"]["concept"] == "CAT"
    assert tree.semantic_structure["roles"]["object"]["head"]["concept"] == "MOUSE"


def test_semantic_composition_does_not_infer_unknown_words():
    tree = Parser(Lexicon()).parse("The strange cat eats the mouse.")

    assert tree.parse_status == "UNPARSED"
    assert tree.semantic_structure is None
