from src.tokenizer import tokenize
from src.lexicon import Lexicon
from src.parser import Parser


def test_cat_sleeping():

    lexicon = Lexicon()

    parser = Parser(lexicon)

    words = tokenize(
        "A cat is sleeping."
    )

    tree = parser.parse(words)

    assert tree.rule == "statement_state_np_aux_state"

    assert tree.meaning == "SUBJECT_STATE"