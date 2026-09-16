import pytest

from src.tcm import Communication, TransientCommunicationMemory


def test_tcm_stores_raw_communication():
    tcm = TransientCommunicationMemory(capacity=3)

    record = tcm.add("Tom eats the bird.")

    assert isinstance(record, Communication)
    assert record.content == "Tom eats the bird."
    assert len(tcm) == 1


def test_tcm_is_bounded_and_discards_oldest_record():
    tcm = TransientCommunicationMemory(capacity=2)

    tcm.add("first")
    tcm.add("second")
    tcm.add("third")

    assert [item.content for item in tcm.recent()] == ["second", "third"]


def test_tcm_does_not_change_persistent_evidence():
    tcm = TransientCommunicationMemory()

    tcm.add("Tom is a cat.")

    assert not hasattr(tcm, "evidence")
    assert not hasattr(tcm, "memories")


def test_tcm_rejects_invalid_capacity():
    with pytest.raises(ValueError):
        TransientCommunicationMemory(capacity=0)


def test_tcm_rejects_empty_content():
    tcm = TransientCommunicationMemory()

    with pytest.raises(ValueError):
        tcm.add("   ")


def test_tcm_recent_limit():
    tcm = TransientCommunicationMemory(capacity=4)
    for value in ["one", "two", "three"]:
        tcm.add(value)

    assert [item.content for item in tcm.recent(2)] == ["two", "three"]
    assert tcm.recent(0) == []


def test_tcm_clear_removes_temporary_records():
    tcm = TransientCommunicationMemory()
    tcm.add("temporary")

    tcm.clear()

    assert len(tcm) == 0
    assert tcm.recent() == []
