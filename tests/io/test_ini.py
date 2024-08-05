import shutil

import pytest
from conftest import ini_file

from pywatemsedem.io.ini import add_field, modify_field


class TestModifyField:
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
