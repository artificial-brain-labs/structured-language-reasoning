from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class VerificationThread:
    thread_id: str
    person_id: str
    candidate_slrm_instance_id: str | None = None
    state: str = "OPEN"
    questions: list[str] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class IdentityProtocol:
    """No-guessing identity discovery and explicit verification workflow."""

    def __init__(self, relationship_memory, protocol_schema=None):
        self.relationship_memory = relationship_memory
        self.schema = protocol_schema or {}
        self.threads = {}

    def open_verification(self, person_id, candidate_slrm_instance_id=None):
        thread = VerificationThread(
            thread_id=f"VERIFY-{uuid4().hex[:12]}",
            person_id=person_id,
            candidate_slrm_instance_id=candidate_slrm_instance_id,
            questions=list(self.schema.get("general_questions", [])),
        )
        self.threads[thread.thread_id] = thread
        person = self.relationship_memory.people[person_id]
        person.verification_state = "PENDING_VERIFICATION"
        for relationship in self.relationship_memory.relationships.values():
            if relationship.person_id == person_id:
                relationship.verification_state = "PENDING_VERIFICATION"
        return thread

    def add_answer(self, thread_id, answer):
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Verification answer must be non-empty")
        thread = self.threads[thread_id]
        if thread.state != "OPEN":
            raise ValueError("Verification thread is not open")
        thread.answers.append(answer.strip())
        return thread

    def confirm_identity(self, thread_id, confirmed):
        thread = self.threads[thread_id]
        if not confirmed:
            thread.state = "REJECTED"
            person = self.relationship_memory.people[thread.person_id]
            person.verification_state = "REJECTED"
            return person
        if not thread.candidate_slrm_instance_id:
            raise ValueError("Cannot verify identity without a candidate SLRM instance")
        person = self.relationship_memory.link_person_to_slrm(
            thread.person_id,
            thread.candidate_slrm_instance_id,
            confirmed=True,
        )
        thread.state = "VERIFIED"
        return person

    def keep_open(self, thread_id):
        thread = self.threads[thread_id]
        thread.state = "OPEN"
        return thread

    def pending_for_person(self, person_id):
        return [
            thread for thread in self.threads.values()
            if thread.person_id == person_id and thread.state == "OPEN"
        ]
