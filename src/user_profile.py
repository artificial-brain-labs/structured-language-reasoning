from dataclasses import dataclass


@dataclass
class UserProfile:
    """Application-level identity context for a user.

    user_id is mandatory and must be supplied by the application/session
    layer. username is optional and is never inferred by SLRM.
    """

    user_id: str
    username: str | None = None

    @property
    def identity_state(self):
        return "IDENTIFIED" if self.username else "UNIDENTIFIED"

    @property
    def display_name(self):
        return self.username if self.username else self.user_id
