import pytest

from src.communication_protocol import GovernedCommunicationProtocol
from src.user_relationships import UserRelationshipMemory


def test_envelope_requires_active_connection():
    memory = UserRelationshipMemory(
        "USER-A",
        "SLRM-A",
        {"default_communication_scope": {"personal_messages": True}},
    )
    connection = memory.create_connection_request("SLRM-B")
    protocol = GovernedCommunicationProtocol(memory)

    with pytest.raises(PermissionError):
        protocol.create_envelope(connection.connection_id, "Hello")


def test_envelope_can_be_created_after_mutual_permission():
    memory = UserRelationshipMemory(
        "USER-A",
        "SLRM-A",
        {"default_communication_scope": {"personal_messages": True}},
    )
    connection = memory.create_connection_request("SLRM-B")
    memory.set_local_permission(connection.connection_id, True)
    memory.set_remote_permission(connection.connection_id, True)
    protocol = GovernedCommunicationProtocol(memory)

    envelope = protocol.create_envelope(connection.connection_id, "Hello")
    received = protocol.receive(envelope, "SLRM-B")

    assert envelope.sender_slrm_instance_id == "SLRM-A"
    assert envelope.receiver_slrm_instance_id == "SLRM-B"
    assert received["content"] == "Hello"


def test_envelope_cannot_be_delivered_to_wrong_instance():
    memory = UserRelationshipMemory(
        "USER-A",
        "SLRM-A",
        {"default_communication_scope": {"personal_messages": True}},
    )
    connection = memory.create_connection_request("SLRM-B")
    memory.set_local_permission(connection.connection_id, True)
    memory.set_remote_permission(connection.connection_id, True)
    protocol = GovernedCommunicationProtocol(memory)
    envelope = protocol.create_envelope(connection.connection_id, "Hello")

    with pytest.raises(PermissionError):
        protocol.receive(envelope, "SLRM-C")
