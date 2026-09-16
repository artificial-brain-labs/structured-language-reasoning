from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class UserProfile:
    """Application-level identity context for a user and SLRM instance."""

    user_id: str
    username: str | None = None
    slrm_instance_id: str = field(default_factory=lambda: f"SLRM-{uuid4().hex}")

    @property
    def identity_state(self):
        return "IDENTIFIED" if self.username else "UNIDENTIFIED"

    @property
    def display_name(self):
        return self.username if self.username else self.user_id
