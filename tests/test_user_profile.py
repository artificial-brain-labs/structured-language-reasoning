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


def test_each_profile_gets_unique_slrm_instance_id():
    first = UserProfile(user_id="USER-001")
    second = UserProfile(user_id="USER-001")

    assert first.slrm_instance_id.startswith("SLRM-")
    assert second.slrm_instance_id.startswith("SLRM-")
    assert first.slrm_instance_id != second.slrm_instance_id


def test_slrm_instance_id_is_separate_from_user_id():
    profile = UserProfile(user_id="USER-001")

    assert profile.slrm_instance_id != profile.user_id
