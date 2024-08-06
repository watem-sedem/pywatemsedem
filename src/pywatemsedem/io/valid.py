import warnings

import numpy as np


def valid_boundaries(arr, lower=None, upper=None):
    """Checks if values are within specified boundaries

    Parameters
    ---------
    arr: numpy.ndarray
        Input array
    lower: int, float, default None
        Lower boundary
    upper: int, float, default None
        Upper boundary

    Returns
    -------
    True
    """

    if (lower is None) and (upper is None):
        msg = "No lower or upper boundaries are defined, omitting boundary check"
        warnings.warn(msg)

    if upper is not None:
        if not isinstance(upper, (int, float)):
            msg = "Upper boundary should be numeric."
            raise TypeError(msg)
        if np.any(arr > upper):
            raise ValueError(f"Values are higher than upper bound ('{upper}')")
    if lower is not None:
        if not isinstance(lower, (int, float)):
            msg = "Lower boundary should be numeric."
            raise TypeError(msg)
        if np.any(arr < lower):
            raise ValueError(f"Values are lower than lower bound ('{lower}')")

    return True


def valid_values(arr, unique_values):
    """Checks if values in an array are within the set of unique values

    The input array can only have the input values defined in unique_values.

    Parameters
    ----------
    arr: numpy.ndarray
        Input array
    unique_values: list
        Unique values that the raster can have

    Returns
    -------
    True
    """

    if not (set(np.unique(arr)).issubset(set(unique_values))):
        msg = "The array contains values that are not present in unique_values"
        raise ValueError(msg)

    return True


def valid_non_nan(arr):
    """Checks if Nan are present in the array

    Parameters
    ----------
    arr: numpy.ndarray
        Input array

    Returns
    -------
    True
    """

    if np.any(np.isnan(arr)):
        msg = "Input array can not contain nan values"
        raise ValueError(msg)

    return True


def valid_array_type(arr, required_type):
    """Checks if arr is
    1) a numpy.dtype
    2) the desired numpy.dtype

    Parameters
    ----------
    arr: numpy.ndarray
        Input array
    required_type: numpy.dtype
         required datatype.

    Returns
    -------
    True
    """
    try:
        if not (np.issubdtype(required_type, np.number)):
            msg = f"No valid numpy dtype chosen for arr! Change to '{required_type}'"
            raise TypeError(msg)
    except TypeError as e:
        msg = str(e) + ". Use numpy dtype as required type."
        raise TypeError(msg)

    if arr.dtype != required_type:
        msg = f"""numpy.dtype (`np.{arr.dtype}`) is not required type
        ('{required_type}')"""
        raise ValueError(msg)

    return True


def valid_nodata(arr, nodata_value=-9999):
    """Checks if a nodata value is present in arr

    Parameters
    --------
    arr: numpy.ndarray
        Input array
    nodata_value: int, default -9999
                    Value to be interpreted as no data present

    Returns
    -------
    True
    """
    if np.any(arr == nodata_value):
        msg = f"A nodata value ({nodata_value}) is present, check if allowed"
        raise Warning(msg)
