from pathlib import Path

import pytest

from pywatemsedem.io.folders import check_and_create_folder


def test_check_and_create_folder(tmp_path):
    """Test creation of pywatemsedem folders"""
    foldername = Path(tmp_path) / "test"
    # check if it exists
    with pytest.raises(IOError) as excinfo:
        check_and_create_folder(foldername, f"Folder '{foldername}'")
    assert (f"Folder '{foldername}' does not exist.") in str(excinfo.value)

    # create it
    check_and_create_folder(foldername, f"Folder '{foldername.stem}'", create=True)
    assert foldername.exists()

    # check if empty
    with pytest.raises(IOError) as excinfo:
        check_and_create_folder(
            foldername, f"Folder '{foldername.stem}'", error_if_empty=True
        )
    assert (f"Folder '{foldername.stem}' is empty.") in str(excinfo.value)
