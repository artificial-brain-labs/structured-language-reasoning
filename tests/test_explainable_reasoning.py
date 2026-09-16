from src.main import SLR


def test_classification_answer_includes_reasoning_path():
    slr = SLR()
    slr.process("Tom is a cat.")

    answer = slr.process("Is Tom an animal?")

    assert "Yes." in answer
    assert "Tom is a animal" not in answer
    assert "Tom -> CAT -> FELINE -> MAMMAL -> ANIMAL" in answer


def test_reasoning_path_preserves_asserted_and_derived_provenance():
    slr = SLR()
    slr.process("Tom is a cat.")

    parsed = slr.parser.parse("Is Tom an animal?")
    result = slr.query.answer(parsed)[0]
    proof = result["proof"]

    assert proof["status"] == "PROVEN"
    assert len(proof["path"]) == 4
    assert proof["path"][0]["status"] == "ASSERTED"
    assert all(edge["status"] == "DERIVED" for edge in proof["path"][1:])
    assert proof["path"][0]["source"] == "USER"
    assert all(edge["source"] == "ONTOLOGY" for edge in proof["path"][1:])


def test_reasoning_does_not_promote_derived_knowledge_to_user_memory():
    slr = SLR()
    slr.process("Tom is a cat.")
    before = list(slr.user_memory.memories)

    slr.process("Is Tom an animal?")

    assert slr.user_memory.memories == before
    assert not any(
        memory.predicate == "IS_A"
        and slr.user_memory.entities.get(memory.object, {}).get("concept") == "ANIMAL"
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )


def test_unknown_classification_has_no_reasoning_path():
    slr = SLR()
    slr.process("Dragon is sleeping.")

    parsed = slr.parser.parse("Is Dragon an animal?")
    results = slr.query.answer(parsed)

    assert results == []
