import numpy as np
import pandas as pd
import pytest

from pywatemsedem.errors import (
    PywatemsedemRasterValueError,
    PywatemsedemVectorAttributeError,
    PywatemsedemVectorAttributeValueError,
    attribute_continuous_value_error,
    attribute_discrete_value_error,
    missing_attribute_error_in_vct,
    raster_discrete_value_error,
)


def test_raster_discrete_value_error_allowed():
    """Verify that no error is raised for allowed discrete values in raster."""
    arr = np.array([1, 2, 2, 1])
    allowed = [1, 2]
    raster_discrete_value_error(arr, tag="test", allowed_values=allowed)


def test_raster_discrete_value_error_not_allowed():
    """Verify that error is raised for not allowed discrete values in raster."""
    arr = np.array([1, 2, 3])
    allowed = [1, 2]
    with pytest.raises(PywatemsedemRasterValueError):
        raster_discrete_value_error(arr, tag="test", allowed_values=allowed)


@pytest.mark.parametrize(
    "df,lower,upper",
    [
        (pd.DataFrame({"val": [1, 2, 3]}), 1, 3),
        (pd.DataFrame({"val": [0, 1, 2]}), 0, 2),
        (pd.DataFrame({"val": [5, 6, 7]}), 5, 7),
    ],
)
def test_attribute_continuous_value_error_allowed(df, lower, upper):
    """Verify that no error is raised for allowed continuous values in vector."""
    attribute_continuous_value_error(
        df, tag="test", attribute="val", lower=lower, upper=upper
    )


@pytest.mark.parametrize(
    "df,lower,upper",
    [
        (pd.DataFrame({"val": [1, 2, 5]}), 1, 3),
        (pd.DataFrame({"val": [-1, 0, 1]}), 0, 2),
        (pd.DataFrame({"val": [5, 6, 8]}), 5, 7),
    ],
)
def test_attribute_continuous_value_error_not_allowed(df, lower, upper):
    """Verify that error is raised for not allowed continuous values in vector."""
    with pytest.raises(PywatemsedemVectorAttributeValueError):
        attribute_continuous_value_error(
            df, tag="test", attribute="val", lower=lower, upper=upper
        )


@pytest.mark.parametrize(
    "df,allowed",
    [
        (pd.DataFrame({"cat": [1, 2, 1]}), {1, 2}),
        (pd.DataFrame({"cat": [0, 0, 0]}), {0}),
        (pd.DataFrame({"cat": [5, 6, 5]}), {5, 6}),
    ],
)
def test_attribute_discrete_value_error_allowed(df, allowed):
    """Verify that no error is raised for allowed discrete values in vector."""
    attribute_discrete_value_error(
        df, tag="test", attribute="cat", allowed_values=allowed
    )


@pytest.mark.parametrize(
    "df,allowed",
    [
        (pd.DataFrame({"cat": [1, 2, 3]}), {1, 2}),
        (pd.DataFrame({"cat": [0, 1, 2]}), {0}),
        (pd.DataFrame({"cat": [5, 6, 7]}), {5, 6}),
    ],
)
def test_attribute_discrete_value_error_not_allowed(df, allowed):
    """Verify that error is raised for not allowed discrete values in vector."""
    with pytest.raises(PywatemsedemVectorAttributeValueError):
        attribute_discrete_value_error(
            df, tag="test", attribute="cat", allowed_values=allowed
        )


@pytest.mark.parametrize(
    "df,req",
    [
        (pd.DataFrame({"a": [1], "b": [2]}), {"a", "b"}),
        (pd.DataFrame({"x": [1], "y": [2], "z": [3]}), {"x", "y"}),
    ],
)
def test_missing_attribute_error_in_vct_allowed(df, req):
    """Verify that no error is raised when all required attrs are present in vector."""
    missing_attribute_error_in_vct(df, tag="test", req_attributes=req)


@pytest.mark.parametrize(
    "df,req",
    [
        (pd.DataFrame({"a": [1]}), {"a", "b"}),
        (pd.DataFrame({"x": [1], "z": [2]}), {"x", "y"}),
    ],
)
def test_missing_attribute_error_in_vct_not_allowed(df, req):
    """Verify that error is raised when required attributes are missing in vector."""
    with pytest.raises(PywatemsedemVectorAttributeError):
        missing_attribute_error_in_vct(df, tag="test", req_attributes=req)
