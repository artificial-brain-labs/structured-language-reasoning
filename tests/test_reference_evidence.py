from src.contextual_reference_memory import ContextualReferenceMemory


def test_reference_mention_carries_explicit_evidence():
    memory = ContextualReferenceMemory()
    mention = memory.add("entity_001", "cat", "subject", concepts=("CAT",))

    assert [item.kind for item in mention.evidence] == ["PRIOR_MENTION", "ROLE"]
    assert mention.evidence[0].detail


def test_required_evidence_filters_contextual_candidates():
    memory = ContextualReferenceMemory()
    memory.add("entity_001", "cat", "subject")

    assert len(memory.candidates(required_evidence=["PRIOR_MENTION"])) == 1
    assert memory.candidates(required_evidence=["UNSUPPORTED_EVIDENCE"]) == []


def test_resolution_exposes_evidence_trace():
    from src.main import SLR

    slr = SLR()
    slr.process("cat sleeps")

    resolution = slr.reference_resolver.resolve("it")

    assert resolution.status == "RESOLVED"
    assert resolution.evidence == ((
        slr.user_memory.find_named_entity("cat"),
        ("PRIOR_MENTION", "ROLE"),
    ),)


def test_agreement_mismatch_does_not_resolve_candidate():
    from src.main import SLR

    slr = SLR()
    slr.contextual_reference_memory.add(
        "person_001", "person", "subject",
        agreement={"number": "PLURAL"},
    )
    resolution = slr.reference_resolver.resolve("it")

    assert resolution.status == "UNKNOWN"
    assert "incompatible" in resolution.reason.lower()
    assert "AGREEMENT_INCOMPATIBLE" in resolution.evidence[0][1]


def test_unknown_candidate_agreement_does_not_count_as_mismatch():
    from src.main import SLR

    slr = SLR()
    slr.contextual_reference_memory.add("cat_001", "cat", "subject")
    resolution = slr.reference_resolver.resolve("it")

    assert resolution.status == "RESOLVED"
    assert "AGREEMENT_COMPATIBLE" in resolution.evidence[0][1]
