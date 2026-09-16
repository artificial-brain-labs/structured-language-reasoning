import pytest

from src.user_relationships import InterSLRMCommunication, UserRelationshipMemory


SCHEMA = {
    "default_communication_scope": {
        "personal_messages": True,
        "relationship_context": True,
        "private_memory": False,
        "private_reasoning": False,
    }
}


def make_memory(user_id, instance_id):
    return UserRelationshipMemory(user_id, instance_id, SCHEMA)


def test_every_instance_identity_is_unique():
    from src.user_profile import UserProfile

    a = UserProfile("USER-A")
    b = UserProfile("USER-B")
    assert a.slrm_instance_id != b.slrm_instance_id


def test_friend_starts_as_unresolved_person_with_open_thread():
    memory = make_memory("USER-A", "SLRM-A")
    person = memory.add_person("Rahul", relation="FRIEND")

    assert person.verification_state == "UNRESOLVED"
    assert person.linked_slrm_instance_id is None
    assert memory.open_threads[person.person_id]["status"] == "OPEN"


def test_same_name_does_not_auto_link_to_slrm():
    memory = make_memory("USER-A", "SLRM-A")
    person = memory.add_person("Rahul")

    assert person.linked_slrm_instance_id is None
    assert person.verification_state == "UNRESOLVED"


def test_identity_link_requires_explicit_confirmation():
    memory = make_memory("USER-A", "SLRM-A")
    person = memory.add_person("Rahul")

    with pytest.raises(ValueError):
        memory.link_person_to_slrm(person.person_id, "SLRM-B", confirmed=False)

    memory.link_person_to_slrm(person.person_id, "SLRM-B", confirmed=True)
    assert person.linked_slrm_instance_id == "SLRM-B"
    assert person.verification_state == "VERIFIED"
    assert memory.open_threads[person.person_id]["status"] == "CLOSED"


def test_connection_requires_mutual_permission():
    memory = make_memory("USER-A", "SLRM-A")
    connection = memory.create_connection_request("SLRM-B")

    assert connection.status == "REQUESTED"
    memory.set_local_permission(connection.connection_id, True)
    assert connection.status == "PENDING_MUTUAL_PERMISSION"

    memory.set_remote_permission(connection.connection_id, True)
    assert connection.status == "ACTIVE"


def test_communication_is_blocked_until_mutual_permission():
    memory = make_memory("USER-A", "SLRM-A")
    connection = memory.create_connection_request("SLRM-B")
    communication = InterSLRMCommunication(memory)

    with pytest.raises(PermissionError):
        communication.send(connection.connection_id, "Hello")

    memory.set_local_permission(connection.connection_id, True)
    with pytest.raises(PermissionError):
        communication.send(connection.connection_id, "Hello")

    memory.set_remote_permission(connection.connection_id, True)
    message = communication.send(connection.connection_id, "Hello")
    assert message["from_slrm_instance_id"] == "SLRM-A"
    assert message["to_slrm_instance_id"] == "SLRM-B"
    assert message["content"] == "Hello"


def test_private_memory_is_not_a_default_communication_capability():
    memory = make_memory("USER-A", "SLRM-A")
    connection = memory.create_connection_request("SLRM-B")
    memory.set_local_permission(connection.connection_id, True)
    memory.set_remote_permission(connection.connection_id, True)
    communication = InterSLRMCommunication(memory)

    with pytest.raises(PermissionError):
        communication.send(connection.connection_id, "private", capability="private_memory")
