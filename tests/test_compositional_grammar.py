from src.lexicon import Lexicon
from src.parser import Parser



def parser():
    return Parser(Lexicon())



def test_composes_noun_phrase_for_type_question():
    tree = parser().parse("What is a cat?")
    assert tree.rule == "question_type_question_aux_np"
    assert tree.question_type == "TYPE"
    assert tree.subject_word == "cat"



def test_composes_noun_phrase_for_determined_type_question():
    tree = parser().parse("What is a cat?")
    assert tree.subject_word == "cat"



def test_composes_entity_and_noun_phrases_for_classification():
    tree = parser().parse("Is Tom a cat?")
    assert tree.rule == "question_classification_aux_np_np"
    assert tree.subject_word == "tom"
    assert tree.object_word == "cat"



def test_composes_two_noun_phrases_for_concept_classification():
    tree = parser().parse("Is a cat an animal?")
    assert tree.rule == "question_classification_aux_np_np"
    assert tree.subject_word == "cat"
    assert tree.object_word == "animal"



def test_composes_transitive_sentence_from_phrase_categories():
    tree = parser().parse("A cat eats the mouse.")
    assert tree.rule == "statement_transitive_np_verb_np"
    assert tree.subject_word == "cat"
    assert tree.verb_word == "eats"
    assert tree.object_word == "mouse"



def test_composes_type_assignment_without_sentence_specific_pattern():
    tree = parser().parse("Tom is a cat.")
    assert tree.rule == "statement_type_entity_aux_np"
    assert tree.subject_word == "tom"
    assert tree.object_word == "cat"



def test_preserves_entity_relation_distinction():
    tree = parser().parse("Dom is Tom.")
    assert tree.rule == "statement_entity_relation"
    assert tree.subject_word == "dom"
    assert tree.object_word == "tom"



def test_object_question_uses_composed_noun_phrase():
    tree = parser().parse("What does Tom eat?")
    assert tree.rule == "question_object_question_aux_np_verb"
    assert tree.subject_word == "tom"
    assert tree.verb_word == "eat"



def test_unknown_sentence_remains_unparsed_instead_of_guessing():
    tree = parser().parse("Is Tom is mammal?")
    assert tree.rule is None
    assert tree.meaning is None
