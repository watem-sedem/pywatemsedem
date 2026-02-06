import numpy as np
import pytest

from pywatemsedem.io.valid import (
    valid_array_type,
    valid_boundaries,
    valid_nodata,
    valid_non_nan,
    valid_values,
)


def test_check_boundaries():
    """test for check_boundaries"""
    arr = np.array([[0, 1, 2, np.nan], [0, 1, 3, 4]])

    # proper numeric bounds
    lower = 0
    upper = 4
    assert valid_boundaries(arr, lower, upper)

    # invalid nan bounds: allowable
    lower = np.nan
    upper = np.nan
    assert valid_boundaries(arr, lower, upper)

    # invalid type inputted for lower and upper
    lower = 0
    upper = "4"
    with pytest.raises(TypeError, match="Upper boundary should be numeric."):
        valid_boundaries(arr, lower, upper)
    lower = "0"
    upper = 4
    with pytest.raises(TypeError, match="Lower boundary should be numeric."):
        valid_boundaries(arr, lower, upper)

    # None bounds
    lower = None
    upper = None
    with pytest.warns(UserWarning, match="No lower or upper boundaries are"):
        valid_boundaries(arr, lower, upper)

    # wrong lower/upper bound
    upper = 2
    with pytest.raises(ValueError, match="are higher than upper bound"):
        valid_boundaries(arr, upper=upper)
    lower = 2
    with pytest.raises(ValueError, match="are lower than lower bound"):
        valid_boundaries(arr, lower=lower)


def test_check_unique_values():
    """test for check_unique_values"""
    arr = np.array([[0, 1, 2, 0], [0, 1, 3, 4]])
    unique_values = [0, 1, 2, 3, 4, 5]
    assert valid_values(arr, unique_values)

    # unique values not known in array
    arr2 = np.concatenate((arr, np.array([5, 6, 7, 8]).reshape(-1, 4)))
    with pytest.raises(
        ValueError, match=" values that are not present in unique_values"
    ):
        valid_values(arr2, unique_values)


def test_check_nan():
    """test for check_nan"""
    arr = np.array([[0, 1, 2, 0], [0, 1, 3, 4]], dtype=np.float64)
    assert valid_non_nan(arr)
    # input nan
    arr[1, 3] = np.nan
    with pytest.raises(ValueError, match="can not contain nan values"):
        valid_non_nan(arr)


def test_valid_array_type():
    """test for check_datatype"""
    arr = np.array([[0, 1, 2, 0], [0, 1, 3, 4]], dtype=np.int32)
    assert valid_array_type(arr, np.int32)

    # wrong datatype required
    with pytest.raises(ValueError, match="is not required type"):
        valid_array_type(arr, np.float32)

    # wrong datatype array
    arr_str = arr.astype(str)
    with pytest.raises(ValueError, match="is not required type"):
        valid_array_type(arr_str, np.int32)

    # string instead of np.dtype: not allowed
    req_type = "string"
    with pytest.raises(TypeError, match="Use numpy dtype as required type."):
        valid_array_type(arr, req_type)


def test_valid_nodata():
    """test for check_nodata"""
    arr = np.array([[0, 1, 2, 0], [0, 1, 3, 4]], dtype=np.float32)
    valid_nodata(arr, nodata_value=-9999)
    arr[1, 2] = -9999
    with pytest.raises(Warning, match="A nodata value"):
        valid_nodata(arr)
    # nan as nodatavalue
    nodata_value = np.nan
    valid_nodata(arr, nodata_value=nodata_value)
