import numpy as np
import pytest

from pywatemsedem.errors import (
    PywatemsedemRasterValueError,
    raster_discrete_value_error,
)


@pytest.mark.parametrize(
    "raster_array, allowed_values, should_raise",
    [
        (np.array([1, 2]), [1, 2], False),
        (np.array([1, 1, 1, 1]), [1, 2], False),
        (np.array([1, 2, 2, 3, 2, 1]), [1, 2, 3], False),
        (np.array([1, 2, 4, 2, 1]), [1, 2, 3], True),
        (np.array([1, 2, 4, 2, 1]), [0], True),
    ],
    ids=[
        "valid_case_perfect_match",
        "valid_case_does_not_contain_all_values",
        "valid_case_combintaion",
        "invalid_case_single_value",
        "invalid_case_all_values",
    ],
)
def test_raster_discrete_value_error_handling_without_classes(
    raster_array, allowed_values, should_raise
):
    """Verify raster_discrete_value_error for both valid and invalid cases.

    Special case where the classes are not considered.

    Parameters
    ----------
    raster_array: numpy.ndarray
        Input raster array that needs to be checked.
    allowed_values: list
        List of allowed values for the raster.
    should_raise: bool
        Indicates whether the function should raise an error or not.
    """

    tag = "test_raster_to_be_checked"

    if should_raise:
        with pytest.raises(PywatemsedemRasterValueError):
            raster_discrete_value_error(raster_array, tag, allowed_values)
    else:
        # Should not raise an error
        raster_discrete_value_error(raster_array, tag, allowed_values)


@pytest.mark.parametrize(
    "raster_array, allowed_values, classes, should_raise",
    [
        (np.array([1, 2]), [1, 2], ["one", "two"], False),
        (np.array([1, 1, 1, 1]), [1, 2], ["one", "two"], False),
        (np.array([1, 2, 2, 3, 2, 1]), [1, 2, 3], ["one", "two", "three"], False),
        (np.array([1, 2, 4, 2, 1]), [1, 2, 3], ["one", "two", "three"], True),
        (np.array([1, 2, 4, 2, 1]), [0], ["zero"], True),
    ],
    ids=[
        "valid_case_perfect_match",
        "valid_case_does_not_contain_all_values",
        "valid_case_combiantion",
        "invalid_case_single_value",
        "invalid_case_all_values",
    ],
)
def test_raster_discrete_value_error_handling_with_classes(
    raster_array, allowed_values, classes, should_raise
):
    """Verify raster_discrete_value_error for both valid and invalid cases.

    Special case where the classes are not considered.

    Parameters
    ----------
    raster_array: numpy.ndarray
        Input raster array that needs to be checked.
    allowed_values: list
        List of allowed values for the raster.
    classes: list
        List of class names corresponding to the allowed values.
    should_raise: bool
        Indicates whether the function should raise an error or not.
    """

    tag = "test_raster_to_be_checked"

    if should_raise:
        with pytest.raises(PywatemsedemRasterValueError):
            raster_discrete_value_error(
                raster_array, tag, allowed_values, classes=classes
            )
    else:
        # Should not raise an error
        raster_discrete_value_error(raster_array, tag, allowed_values, classes=classes)
