from src.main import SLR

def test_coordinated_object_creates_multiple_operations():
    slr = SLR()
    parsed = slr.parser.parse("cat eats rat and mouse")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.object_words == ("rat", "mouse")
    result = slr.process("cat eats rat and mouse")
    assert "stored" in result.lower()
    cat_id = slr.user_memory.find_named_entity("cat")
    rat_id = slr.user_memory.find_named_entity("rat")
    mouse_id = slr.user_memory.find_named_entity("mouse")
    assert slr.user_memory.query(subject=cat_id, predicate="EATS", object=rat_id)
    assert slr.user_memory.query(subject=cat_id, predicate="EATS", object=mouse_id)

def test_coordinated_subject_creates_multiple_operations():
    slr = SLR()
    parsed = slr.parser.parse("cat and dog eat rat")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.subject_words == ("cat", "dog")
    slr.process("cat and dog eat rat")
    rat_id = slr.user_memory.find_named_entity("rat")
    cat_id = slr.user_memory.find_named_entity("cat")
    dog_id = slr.user_memory.find_named_entity("dog")
    assert slr.user_memory.query(subject=cat_id, predicate="EATS", object=rat_id)
    assert slr.user_memory.query(subject=dog_id, predicate="EATS", object=rat_id)

def test_nested_coordination_is_explicitly_ambiguous():
    slr = SLR()
    parsed = slr.parser.parse("cat eats rat and mouse and dog")
    assert parsed.parse_status == "AMBIGUOUS"


def test_coordination_expands_both_roles_as_cartesian_product():
    slr = SLR()
    parsed = slr.parser.parse("cat and dog eat rat and mouse")
    assert parsed.parse_status == "DETERMINED"
    assert parsed.subject_words == ("cat", "dog")
    assert parsed.object_words == ("rat", "mouse")

    meaning = slr.semantic_parser.parse(parsed)
    assert len(meaning.operations) == 4
