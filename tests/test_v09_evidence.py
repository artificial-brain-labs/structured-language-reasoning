import pytest

from src.evidence import Evidence, EvidenceKind, EvidenceState, EvidenceStore
from src.main import SLR


def test_observation_is_not_assertion():
    store = EvidenceStore()

    observation = store.observe(subject="tom", predicate="EATS", object="bird")

    assert observation.kind == EvidenceKind.OBSERVATION
    assert observation.confirmed is False
    assert not any(record.kind == EvidenceKind.ASSERTION for record in store.records)


def test_interpretation_is_not_assertion():
    store = EvidenceStore()

    interpretation = store.interpret(
        subject="tom",
        predicate="IS_A",
        object="CAT",
        support=("lexical_evidence",),
    )

    assert interpretation.kind == EvidenceKind.INTERPRETATION
    assert interpretation.confirmed is False
    assert not any(record.kind == EvidenceKind.ASSERTION for record in store.records)


def test_hypothesis_cannot_be_marked_confirmed():
    with pytest.raises(ValueError, match="HYPOTHESIS"):
        EvidenceState.validate(
            Evidence(
                kind=EvidenceKind.HYPOTHESIS,
                subject="tom",
                predicate="IS_A",
                object="CAT",
                confirmed=True,
            )
        )


def test_assertion_requires_explicit_confirmation():
    with pytest.raises(ValueError, match="explicit confirmation"):
        EvidenceState.validate(
            Evidence(
                kind=EvidenceKind.ASSERTION,
                subject="tom",
                predicate="IS_A",
                object="CAT",
                confirmed=False,
            )
        )


def test_user_memory_records_explicit_assertion_evidence():
    slr = SLR()

    slr.process("Tom is a cat.")

    tom = slr.user_memory.find_named_entity("Tom")
    cat = slr.user_memory.find_entity("CAT")
    assertions = [record for record in slr.user_memory.evidence.records if record.kind == EvidenceKind.ASSERTION]
    assert assertions
    assert any(
        record.subject == tom
        and record.predicate == "IS_A"
        and record.object == cat
        and record.confirmed
        for record in assertions
    )


def test_derived_knowledge_is_recordable_but_not_user_assertion():
    slr = SLR()

    slr.process("Tom is a cat.")
    tom = slr.user_memory.find_named_entity("Tom")
    derived = slr.reasoner.infer_is_a(tom)

    for item in derived:
        slr.user_memory.record_derivation(
            subject=item["entity"],
            predicate=item["predicate"],
            object=item["object"],
            support=item.get("support", ()),
        )

    assert any(record.kind == EvidenceKind.DERIVATION for record in slr.user_memory.evidence.records)
    assert not any(
        record.kind == EvidenceKind.ASSERTION
        and record.object in {"FELINE", "MAMMAL", "ANIMAL"}
        for record in slr.user_memory.evidence.records
    )


def test_system_memory_has_no_user_evidence_ledger():
    slr = SLR()

    slr.process("Tom is a cat.")

    assert not hasattr(slr.memory, "evidence")
