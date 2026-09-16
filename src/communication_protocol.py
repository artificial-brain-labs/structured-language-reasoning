from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class CommunicationEnvelope:
    message_id: str
    connection_id: str
    sender_slrm_instance_id: str
    receiver_slrm_instance_id: str
    capability: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class GovernedCommunicationProtocol:
    """Create messages only across an active, mutually authorized connection."""

    def __init__(self, relationship_memory):
        self.relationship_memory = relationship_memory

    def create_envelope(self, connection_id, content, capability="personal_messages"):
        message = self.relationship_memory.connections[connection_id]
        if not self.relationship_memory.can_communicate(connection_id, capability):
            raise PermissionError("Communication is not authorized for this connection/capability")
        return CommunicationEnvelope(
            message_id=f"MSG-{uuid4().hex[:12]}",
            connection_id=message.connection_id,
            sender_slrm_instance_id=message.local_slrm_instance_id,
            receiver_slrm_instance_id=message.remote_slrm_instance_id,
            capability=capability,
            content=content.strip(),
        )

    def receive(self, envelope, expected_local_slrm_instance_id):
        if envelope.receiver_slrm_instance_id != expected_local_slrm_instance_id:
            raise PermissionError("Message is addressed to a different SLRM instance")
        return {
            "message_id": envelope.message_id,
            "connection_id": envelope.connection_id,
            "from_slrm_instance_id": envelope.sender_slrm_instance_id,
            "capability": envelope.capability,
            "content": envelope.content,
            "received_at": datetime.now(UTC).isoformat(),
        }
