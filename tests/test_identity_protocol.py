import pytest

from src.identity_protocol import IdentityProtocol
from src.user_relationships import UserRelationshipMemory


def setup():
    memory = UserRelationshipMemory("USER-A", "SLRM-A")
    person = memory.add_person("Rahul", relation="FRIEND")
    protocol = IdentityProtocol(
        memory,
        {"general_questions": ["What context do you know this person from?"]},
    )
    return memory, person, protocol


def test_identity_thread_stays_open_without_candidate():
    memory, person, protocol = setup()
    thread = protocol.open_verification(person.person_id)
    protocol.add_answer(thread.thread_id, "We worked together.")

    assert thread.state == "OPEN"
    assert person.verification_state == "PENDING_VERIFICATION"
    assert protocol.pending_for_person(person.person_id) == [thread]


def test_identity_confirmation_requires_candidate():
    _, person, protocol = setup()
    thread = protocol.open_verification(person.person_id)
    with pytest.raises(ValueError):
        protocol.confirm_identity(thread.thread_id, confirmed=True)


def test_explicit_confirmation_verifies_candidate_slrm():
    memory, person, protocol = setup()
    thread = protocol.open_verification(person.person_id, "SLRM-B")
    protocol.add_answer(thread.thread_id, "We worked together.")
    verified = protocol.confirm_identity(thread.thread_id, confirmed=True)

    assert verified.linked_slrm_instance_id == "SLRM-B"
    assert verified.verification_state == "VERIFIED"
    assert thread.state == "VERIFIED"


def test_rejection_does_not_link_identity():
    _, person, protocol = setup()
    thread = protocol.open_verification(person.person_id, "SLRM-B")
    rejected = protocol.confirm_identity(thread.thread_id, confirmed=False)

    assert rejected.linked_slrm_instance_id is None
    assert rejected.verification_state == "REJECTED"
    assert thread.state == "REJECTED"
