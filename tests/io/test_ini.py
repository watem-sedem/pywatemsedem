import shutil
from pathlib import Path

import pytest
from conftest import ini_file

from pywatemsedem.io.ini import add_field, get_item_from_ini, modify_field


class TestModifyField:
    """Class combining all tests for the modify_field function"""

    def test_modify(self, tmp_path):
        """Test basic func"""
        modify_field(ini_file, "User Choices", "max kernel", 3)

    def test_wrong_section(self, tmp_path):
        """Expect error when the section does not exist"""
        with pytest.raises(KeyError) as excinfo:
            modify_field(ini_file, "User Choice", "max kernel", 3)
        assert "Section 'User Choice' does not exist" in str(excinfo.value)

    def test_wrong_key(self, tmp_path):
        """Expect error when the to-modify-key does not exist"""
        with pytest.raises(KeyError) as excinfo:
            modify_field(ini_file, "User Choices", "max kernelzz", 3)
        assert "Key 'max kernelzz' does not exist" in str(excinfo.value)


class TestAddField:
    """Class combining all tests for the add field section"""

    def test_add(self, tmp_path):
        """Test basic func"""
        shutil.copy(ini_file, tmp_path / "test.ini")
        add_field(tmp_path / "test.ini", "User Choices", "max kernelzzz", 3)

    def test_wrong_section(self, tmp_path):
        """Expect error when the section does not exist"""
        with pytest.raises(KeyError) as excinfo:
            add_field(ini_file, "User Choice", "max kernel", 3)
        assert "Section 'User Choice' does not exist" in str(excinfo.value)

    def test_key_exists(self, tmp_path):
        """Expect error when the to-add-key already exists"""
        with pytest.raises(KeyError) as excinfo:
            add_field(ini_file, "User Choices", "max kernel", 3)
        assert "Key 'max kernel' already exist in" in str(excinfo.value)


class TestGetItemFromIni:
    """Class combining all tests for the get_item_from_ini function"""

    def test_get_string_from_ini(self):
        """Test if a string can be retrieved from an ini-file"""
        value = get_item_from_ini(
            ini_file, section="Test Section", option="string_option", dtype=str
        )
        expected_string = "This is a string"
        assert value == expected_string

    def test_get_float_from_ini(self):
        """Test if a float can be retrieved from an ini-file"""
        value = get_item_from_ini(
            ini_file, section="Test Section", option="float_option", dtype=float
        )
        expected_float = 0.03
        assert value == expected_float

    def test_get_int_from_ini(self):
        """Test if an int can be retrieved from an ini-file"""
        value = get_item_from_ini(
            ini_file, section="Test Section", option="int_option", dtype=int
        )
        expected_int = 10
        assert value == expected_int

    def test_get_bool_from_ini(self):
        """Test if a bool can be retrieved from an ini-file"""
        value = get_item_from_ini(
            ini_file, section="Test Section", option="bool_option", dtype=bool
        )
        expected_bool = True
        assert value == expected_bool

    def test_non_existant_section(self):
        """Test if a ValueError is raised when a value from a non-existing section in the ini-file is wanted"""
        with pytest.raises(ValueError) as excinfo:
            get_item_from_ini(
                ini_file,
                section="Not existing section",
                option="bool_option",
                dtype=bool,
            )
        assert ("Section Not existing section does not exist in ini-file") in str(
            excinfo.value
        )

    def test_non_existant_option(self):
        """Test if a ValueError is raised when a value from a non-existing option in the ini-file is wanted"""
        with pytest.raises(ValueError) as excinfo:
            get_item_from_ini(
                ini_file,
                section="Test Section",
                option="Not existing option",
                dtype=bool,
            )
        assert (
            "Option Not existing option does not exist in ini-file (section Test Section)"
        ) in str(excinfo.value)

    def test_wrong_dtype_from_ini(self):
        """Test if a TypeError is raised
        when no correct dtype is given"""
        with pytest.raises(TypeError) as excinfo:
            get_item_from_ini(
                ini_file,
                section="Test Section",
                option="bool_option",
                dtype="this is not a dtype",
            )
        assert ("not a correct Type") in str(excinfo.value)

    def test_wrong_ini_file(self):
        """Test if a FileNotFoundError is raised when no correct ini file is given"""
        with pytest.raises(FileNotFoundError) as excinfo:
            get_item_from_ini(
                Path("This/File/Does/Not/Exist.ini"),
                "Test Section",
                "bool_option",
                bool,
            )
        assert "This/File/Does/Not/Exist.ini does not exist" in str(excinfo.value)
