from src.main import SLR


def test_lexicon_exposes_multiple_pos_candidates():
    slr = SLR()
    # Add a true multi-POS dictionary entry for the parser foundation.
    slr.lexicon.words["record"] = {
        "pos": "NOUN", "concept": "RECORD",
        "senses": [
            {"id": "record.noun", "pos": "NOUN", "concept": "RECORD", "definition": "A written record."},
            {"id": "record.verb", "pos": "VERB", "concept": "RECORD_ACTION", "definition": "To capture information."},
        ],
    }
    assert set(slr.lexicon.pos_candidates("record")) == {"NOUN", "VERB"}


def test_ambiguous_word_keeps_multiple_dictionary_senses_in_semantic_structure():
    slr = SLR()
    parsed = slr.parser.parse("Tom sees bat")
    # The lexical entry remains available to semantic composition rather than
    # being silently collapsed to one sense.
    assert parsed.semantic_structure is not None
    text = str(parsed.semantic_structure)
    assert "bat.animal" in text
    assert "bat.sports" in text


def test_unknown_word_has_no_synthetic_meaning():
    slr = SLR()
    assert slr.lexicon.meanings("zorb") == []
