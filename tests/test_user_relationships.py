import pytest

from src.user_relationships import InterSLRMCommunication, UserRelationshipMemory


def memory():
    return UserRelationshipMemory(
        owner_user_id="USER-A",
        slrm_instance_id="SLRM-A",
        relationship_schema={
            "default_communication_scope": {
                "personal_messages": True,
                "private_memory": False,
            }
        },
    )


def test_friend_creates_unresolved_person_and_open_thread():
    rel = memory()
    person = rel.add_person("Rahul", relation="FRIEND", source_interaction_id="INT-1")

    assert person.verification_state == "UNRESOLVED"
    assert person.linked_slrm_instance_id is None
    assert rel.open_threads[person.person_id]["status"] == "OPEN"


def test_same_name_does_not_create_or_link_identity_automatically():
    rel = memory()
    first = rel.add_person("Rahul")
    second = rel.add_person("Rahul")

    assert first.person_id == second.person_id
    assert first.linked_slrm_instance_id is None
    assert first.verification_state == "UNRESOLVED"


def test_identity_link_requires_explicit_confirmation():
    rel = memory()
    person = rel.add_person("Rahul")

    with pytest.raises(ValueError):
        rel.link_person_to_slrm(person.person_id, "SLRM-B")

    rel.link_person_to_slrm(person.person_id, "SLRM-B", confirmed=True)
    assert person.linked_slrm_instance_id == "SLRM-B"
    assert person.verification_state == "VERIFIED"
    assert rel.open_threads[person.person_id]["status"] == "CLOSED"


def test_connection_requires_mutual_permission():
    rel = memory()
    connection = rel.create_connection_request("SLRM-B")

    assert connection.status == "REQUESTED"
    rel.set_local_permission(connection.connection_id, True)
    assert connection.status == "PENDING_MUTUAL_PERMISSION"
    rel.set_remote_permission(connection.connection_id, True)
    assert connection.status == "ACTIVE"


def test_rejecting_side_never_activates_connection():
    rel = memory()
    connection = rel.create_connection_request("SLRM-B")
    rel.set_local_permission(connection.connection_id, True)
    rel.set_remote_permission(connection.connection_id, False)

    assert connection.status == "PENDING_MUTUAL_PERMISSION"
    assert not rel.can_communicate(connection.connection_id, "personal_messages")


def test_communication_blocked_until_connection_is_active():
    rel = memory()
    connection = rel.create_connection_request("SLRM-B")
    channel = InterSLRMCommunication(rel)

    with pytest.raises(PermissionError):
        channel.send(connection.connection_id, "Hello")

    rel.set_local_permission(connection.connection_id, True)
    rel.set_remote_permission(connection.connection_id, True)
    message = channel.send(connection.connection_id, "Hello")

    assert message["from_slrm_instance_id"] == "SLRM-A"
    assert message["to_slrm_instance_id"] == "SLRM-B"
    assert message["content"] == "Hello"


def test_private_memory_is_not_communicable_by_default():
    rel = memory()
    connection = rel.create_connection_request("SLRM-B")
    rel.set_local_permission(connection.connection_id, True)
    rel.set_remote_permission(connection.connection_id, True)
    channel = InterSLRMCommunication(rel)

    with pytest.raises(PermissionError):
        channel.send(connection.connection_id, "secret", capability="private_memory")
