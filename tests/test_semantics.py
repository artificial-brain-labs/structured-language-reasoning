from src.tokenizer import tokenize
from src.lexicon import Lexicon
from src.parser import Parser
from src.semantics import SemanticParser


def test_semantic_representation():

    lexicon = Lexicon()

    parser = Parser(lexicon)

    semantic_parser = SemanticParser(lexicon)

    words = tokenize(
        "A cat is sleeping."
    )

    tree = parser.parse(words)

    meaning = semantic_parser.parse(tree)

    assert len(meaning.entities) == 1

    assert meaning.entities[0].concept == "CAT"

    assert meaning.facts[0].predicate == "SLEEP"

def test_semantic_parser_uses_resolved_ambiguous_sense():
    slr = __import__("src.main", fromlist=["SLR"]).SLR()
    parsed = slr.parser.parse("bat is animal")
    context = slr.semantic_context.extract(parsed, "bat is animal")
    meaning = slr.semantic_parser.parse(parsed, context=context)
    assert meaning.entities[0].concept == "BAT_ANIMAL"
