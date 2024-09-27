"""Test functions for utils scripts"""
import pytest

from pywatemsedem.choices import UserChoice


def test_userchoice_not_allowed_value():
    """Test if a ValueError is raised when a not allowed value is entered"""
    user_choice = UserChoice(
        "Test1",
        "Tests",
        None,
        str,
        False,
        ["This string is allowed", "A second allowed string"],
    )
    with pytest.raises(ValueError) as excinfo:
        user_choice.value = "Not allowed string"
    assert (
        "Value should be one of: ['This string is allowed', 'A second allowed string']."
    ) in str(excinfo.value)


def test_userchoice_wrong_dtype():
    """Test if a ValueError is raised when a value with a wrong dtype is entered"""
    user_choice = UserChoice(
        "Test2",
        "Tests",
        None,
        float,
        False,
    )
    with pytest.raises(ValueError) as excinfo:
        user_choice.value = "This value should be a float"
    assert ("Value assigned to key 'Test2' should be dtype '<class 'str'>'.") in str(
        excinfo.value
    )
