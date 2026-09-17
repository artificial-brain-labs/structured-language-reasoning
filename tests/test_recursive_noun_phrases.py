from src.lexicon import Lexicon
from src.parser import Parser
from src.compositional_parser import CompositionalGrammarParser


def parser():
    return Parser(Lexicon())


def test_single_adjective_composes_noun_phrase():
    grammar = CompositionalGrammarParser(Lexicon())
    candidates = grammar.parse(["a", "small", "cat"], start_symbol="NP")
    assert len(candidates) == 1
    assert grammar.derivation_signature(candidates[0])[0] == "np_determiner_adjp_noun"


def test_multiple_adjectives_compose_recursively():
    grammar = CompositionalGrammarParser(Lexicon())
    candidates = grammar.parse(["the", "small", "black", "young", "cat"], start_symbol="NP")
    assert len(candidates) == 1
    signature = grammar.derivation_signature(candidates[0])
    assert signature[0] == "np_determiner_adjp_noun"
    assert signature[1][0] == "adjp_adjective_adjp"


def test_adjective_phrase_without_determiner_composes():
    grammar = CompositionalGrammarParser(Lexicon())
    candidates = grammar.parse(["small", "cat"], start_symbol="NP")
    assert len(candidates) == 1


def test_transitive_sentence_uses_recursive_noun_phrases():
    tree = parser().parse("The small cat eats the black mouse.")
    assert tree.rule == "statement_transitive_np_verb_np"
    assert tree.subject_word == "cat"
    assert tree.verb_word == "eats"
    assert tree.object_word == "mouse"


def test_novel_adjective_combination_does_not_need_sentence_rule():
    tree = parser().parse("A young dog sees the black cat.")
    assert tree.rule == "statement_transitive_np_verb_np"
    assert tree.subject_word == "dog"
    assert tree.verb_word == "sees"
    assert tree.object_word == "cat"


def test_unknown_adjective_is_not_guessed():
    tree = parser().parse("A strange cat eats the mouse.")
    assert tree.rule is None
    assert tree.meaning is None
