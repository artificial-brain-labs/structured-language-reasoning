import pytest

from src.user_profile import UserProfile


def test_user_profile_requires_user_id():
    with pytest.raises(TypeError):
        UserProfile()


def test_user_profile_can_be_unidentified():
    profile = UserProfile(user_id="USER-001")

    assert profile.user_id == "USER-001"
    assert profile.username is None
    assert profile.identity_state == "UNIDENTIFIED"
    assert profile.display_name == "USER-001"


def test_user_profile_uses_explicit_username():
    profile = UserProfile(user_id="USER-001", username="Purnendu")

    assert profile.user_id == "USER-001"
    assert profile.username == "Purnendu"
    assert profile.identity_state == "IDENTIFIED"
    assert profile.display_name == "Purnendu"


def test_username_is_not_inferred():
    profile = UserProfile(user_id="USER-001", username=None)

    assert profile.username is None
    assert profile.display_name == "USER-001"
