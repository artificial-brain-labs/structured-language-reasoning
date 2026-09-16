from src.main import SLR


def test_process_records_raw_communication_in_tcm():
    slr = SLR()

    slr.process("Tom is a cat.")

    assert [record.content for record in slr.tcm.recent()] == ["Tom is a cat."]


def test_tcm_records_questions_without_creating_user_memory_facts():
    slr = SLR()

    slr.process("What is Tom?")

    assert [record.content for record in slr.tcm.recent()] == ["What is Tom?"]
    assert slr.user_memory.memories == []


def test_tcm_is_separate_from_user_memory():
    slr = SLR()

    slr.process("Tom is a cat.")

    assert slr.tcm is not slr.user_memory
    assert not hasattr(slr.tcm, "evidence")
    assert not hasattr(slr.tcm, "entities")


def test_tcm_preserves_communication_even_when_parsing_fails():
    slr = SLR()

    slr.process("this sentence cannot be parsed")

    assert slr.tcm.recent()[-1].content == "this sentence cannot be parsed"
