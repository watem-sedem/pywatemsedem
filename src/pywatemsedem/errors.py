import numpy as np

from pywatemsedem.io.valid import valid_boundaries


class PywatemsedemVectorAttributeError(Exception):
    """Raise error when input data are not conform the required pywatemsedem attributes."""


class PywatemsedemVectorAttributeValueError(Exception):
    """Raise error when input data attribute values are not conform required attributes
    values"""


class PywatemsedemRasterValueError(Exception):
    """Raise error when input data attribute values are not conform required
    attributes
    values"""


def raster_discrete_value_error(raster_array, tag, allowed_values, classes=None):
    """Value error for discrete attributes in input raster

    Raises error when an attribute of an input raster contains incorrect discrete
    values.

    Parameters
    ----------
    raster_array: numpy.ndarray
        Input raster.
    tag: str
        Internal naming.
    allowed_values: list
        Allowed values
    classes: list
        Name of classes of values, if None: not considered.
    """
    if not set(np.unique(raster_array)).issubset(allowed_values):
        if classes is not None:
            allowed_values = [f"{x}: {y}" for x, y in zip(allowed_values, classes)]
        str_values = "'" + "' ,'".join(allowed_values) + "'"
        msg = f"Input raster for '{tag}' can only contain values {str_values}"
        raise PywatemsedemRasterValueError(msg)


def attribute_continuous_value_error(source, tag, attribute, lower=None, upper=None):
    """Value error for continuous attributes in input vector

    Raises error when an attribute of an input vector contains out-of-bound values.

    Parameters
    ----------
    source: geopandas.GeoDataFrame
        Input vector.
    tag: str
        Internal naming.
    lower: int or float, default None
        Lower boundary, if None: no boundary.
    upper: int or float, default None
        Upper boundary, if None: no boundary.
    """
    try:
        valid_boundaries(source[attribute], lower=lower, upper=upper)
    except ValueError:
        if lower is None:
            lower = -float("inf")
        if upper is None:
            upper = float("inf")
        msg = (
            f"Column '{attribute}' in '{tag}' vector should contain values in "
            f"[{lower}, {upper}]"
        )
        raise PywatemsedemVectorAttributeValueError(msg)


def attribute_discrete_value_error(
    source, tag, attribute, allowed_values, classes=None
):
    """Value error for discrete attributes in input vector

    Raises error when an attribute of an input vector contains incorrect discrete
    values.

    Parameters
    ----------
    source: geopandas.GeoDataFrame
        Input vector.
    tag: str
        Internal naming.
    attribute: str
        Column name
    allowed_values: set of int and/or float
        Allowed values
    classes: set of string, default None
        Name of classes of values, if None: not considered.
    """
    if not set(np.unique(source[attribute])).issubset(allowed_values):
        if classes is not None:
            allowed_values = [f"{x}: {y}" for x, y in zip(allowed_values, classes)]
        str_values = "'" + "' ,'".join(allowed_values) + "'"
        msg = (
            f"Column '{attribute}' in '{tag}' vector can only contain values "
            f"{str_values}"
        )
        raise PywatemsedemVectorAttributeValueError(msg)


def missing_attribute_error_in_vct(source, tag, req_attributes):
    """Missing attribute error in vectors

    Raises error when not all required attributes/columns are present in input vector.

    Parameters
    ----------
    source: geopandas.GeoDataFrame
        Input vector.
    tag: str
        Internal naming.
    req_attributes: set
        Required attributes in input source.
    """

    if not req_attributes.issubset(set(source.columns)):
        str_col = "'" + "' ,'".join(req_attributes) + "'"
        msg = (
            f"'{tag}' input vector should contain {str_col} as vector attribute/column."
        )
        raise PywatemsedemVectorAttributeError(msg)
