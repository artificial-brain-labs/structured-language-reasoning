from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class PersonRecord:
    person_id: str
    name: str
    linked_slrm_instance_id: str | None = None
    verification_state: str = "UNRESOLVED"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class RelationshipRecord:
    relationship_id: str
    owner_user_id: str
    relation: str
    person_id: str
    person_name: str
    verification_state: str = "UNRESOLVED"
    linked_slrm_instance_id: str | None = None
    source_interaction_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ConnectionRecord:
    connection_id: str
    local_slrm_instance_id: str
    remote_slrm_instance_id: str
    relationship_type: str
    local_permission: bool = False
    remote_permission: bool = False
    status: str = "PENDING_MUTUAL_PERMISSION"
    communication_scope: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class UserRelationshipMemory:
    """Per-user relationship and inter-SLRM connection state.

    This is user memory, not system/global knowledge. No identity is inferred
    from names; instance connections become ACTIVE only after both sides grant
    permission.
    """

    def __init__(self, owner_user_id, relationship_schema=None):
        self.owner_user_id = owner_user_id
        self.relationship_schema = relationship_schema or {}
        self.people = {}
        self.relationships = {}
        self.connections = {}
        self.open_threads = {}

    def add_person(self, name, relation="FRIEND", source_interaction_id=None):
        normalized = name.strip().lower()
        for person in self.people.values():
            if person.name.lower() == normalized:
                person_id = person.person_id
                self.relationships.setdefault(
                    (relation, person_id),
                    RelationshipRecord(
                        relationship_id=f"REL-{uuid4().hex[:12]}",
                        owner_user_id=self.owner_user_id,
                        relation=relation,
                        person_id=person_id,
                        person_name=person.name,
                        verification_state=person.verification_state,
                        linked_slrm_instance_id=person.linked_slrm_instance_id,
                        source_interaction_id=source_interaction_id,
                    ),
                )
                return person

        person = PersonRecord(person_id=f"PERSON-{uuid4().hex[:12]}", name=name.strip())
        self.people[person.person_id] = person
        key = (relation, person.person_id)
        self.relationships[key] = RelationshipRecord(
            relationship_id=f"REL-{uuid4().hex[:12]}",
            owner_user_id=self.owner_user_id,
            relation=relation,
            person_id=person.person_id,
            person_name=person.name,
            source_interaction_id=source_interaction_id,
        )
        self.open_threads[person.person_id] = {
            "thread_id": f"THREAD-{uuid4().hex[:12]}",
            "person_id": person.person_id,
            "reason": "IDENTITY_VERIFICATION",
            "status": "OPEN",
        }
        return person

    def find_people_by_name(self, name):
        normalized = name.strip().lower()
        return [p for p in self.people.values() if p.name.lower() == normalized]

    def link_person_to_slrm(self, person_id, slrm_instance_id, confirmed=False):
        if not confirmed:
            raise ValueError("SLRM identity linking requires explicit confirmation")
        person = self.people[person_id]
        person.linked_slrm_instance_id = slrm_instance_id
        person.verification_state = "VERIFIED"
        for relationship in self.relationships.values():
            if relationship.person_id == person_id:
                relationship.linked_slrm_instance_id = slrm_instance_id
                relationship.verification_state = "VERIFIED"
        if person_id in self.open_threads:
            self.open_threads[person_id]["status"] = "CLOSED"
        return person

    def create_connection_request(self, remote_slrm_instance_id, relationship_type="FRIEND", scope=None):
        connection = ConnectionRecord(
            connection_id=f"CONN-{uuid4().hex[:12]}",
            local_slrm_instance_id=self.local_slrm_instance_id,
            remote_slrm_instance_id=remote_slrm_instance_id,
            relationship_type=relationship_type,
            communication_scope=dict(scope or self.default_scope()),
        )
        self.connections[connection.connection_id] = connection
        return connection

    def set_local_permission(self, connection_id, allowed):
        connection = self.connections[connection_id]
        connection.local_permission = bool(allowed)
        self._refresh_connection_status(connection)
        return connection

    def set_remote_permission(self, connection_id, allowed):
        connection = self.connections[connection_id]
        connection.remote_permission = bool(allowed)
        self._refresh_connection_status(connection)
        return connection

    def _refresh_connection_status(self, connection):
        if connection.local_permission and connection.remote_permission:
            connection.status = "ACTIVE"
        elif not connection.local_permission and not connection.remote_permission:
            connection.status = "PENDING_MUTUAL_PERMISSION"
        else:
            connection.status = "PENDING_MUTUAL_PERMISSION"

    def can_communicate(self, connection_id, capability):
        connection = self.connections[connection_id]
        return connection.status == "ACTIVE" and bool(connection.communication_scope.get(capability, False))

    def default_scope(self):
        return dict(self.relationship_schema.get("default_communication_scope", {}))

    def attach_instance_identity(self, slrm_instance_id):
        self.local_slrm_instance_id = slrm_instance_id
