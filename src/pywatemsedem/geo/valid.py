from functools import wraps
from inspect import signature
from pathlib import Path

import fiona
import numpy as np
import rasterio
from fiona.errors import DriverError
from rasterio.errors import RasterioIOError

from .rasterproperties import RasterProperties


class PywatemsedemInputError(Exception):
    """Raise when input data are not conform the pywatemsedem required input format."""


class PywatemsedemTypeError(Exception):
    """Raise when input data type are not conform the pywatemsedem required type format."""


def valid_polygonvector(vct, fun):
    """Check if input vector file is a valid polygon shape

    Parameters
    ----------
    vct: pathlib.Path
        File path to vector.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    """
    valid_exists(vct, fun)
    valid_vector(vct, fun, "Polygon")

    return True


def valid_pointvector(vct, fun):
    """Check if input vector file is a valid point shape

    Parameters
    ----------
    vct: pathlib.Path
        File path to vector.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    """
    valid_exists(vct, fun)
    valid_vector(vct, fun, "Point")

    return True


def valid_linesvector(vct, fun):
    """Check if input vector file is a valid lines shape

    Parameters
    ----------
    vct: pathlib.Path
        File path to vector.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    """
    valid_exists(vct, fun)
    valid_vector(vct, fun, "LineString")

    return True


def valid_rasterlist(lst_rst, fun):
    """Check if input is a valid list of rasters

    Parameters
    ----------
    lst_rst: list
        List of file paths to rasters.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    """
    if type(lst_rst) is not list:
        msg = (
            f"Input '{lst_rst}' is not a valid list of rasters input, "
            f"cannot execute '{fun.__name__}'."
        )
        raise PywatemsedemInputError(msg)

    for rst in lst_rst:
        valid_raster(rst, fun)

    return True


def valid_vectorlist(lst_vct, fun, req_type=None):
    """Check if input is a valid list of rasters

    Parameters
    ----------
    lst_vct: list
        List of file paths to rasters.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    req_type:
        Required geometry type of vector. See :func:`pywatemsedem.geo.valid.valid_vector`

    Note
    -----
    req_type can only be one type, not a mix.
    """
    if type(lst_vct) is not list:
        msg = (
            f"Input '{lst_vct}' is not a valid list of vectors input, "
            f"cannot execute '{fun.__name__}'."
        )
        raise PywatemsedemInputError(msg)

    for vct in lst_vct:
        valid_vector(vct, fun, req_type)

    return True


def valid_vector(vct, fun, req_type=None):
    """Check if input file is a valid vector

    Parameters
    ----------
    Parameters
    ----------
    vct: pathlib.Path
        File path to vector.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    req_type:
        Required geometry type of vector, limited to "Polygon", "LineString", "Point"
        and None (i.e. don't check).
    """
    if req_type not in ["Polygon", "LineString", "Point", None]:
        msg = f"Geomtry type '{req_type}' not known."
        raise IOError(msg)
    try:
        c = fiona.open(vct)
        if req_type is not None:
            if c.schema["geometry"] is not req_type:
                msg = (
                    f"Geometry input type ('{c.schema['geometry']}') of '{vct}' is "
                    f"not of "
                    f"type '{req_type}', cannot execute '{fun.__name__}'."
                )
                raise PywatemsedemTypeError(msg)
        c.close()

    except DriverError:
        msg = (
            f"The fiona engine in pywatemsedem cannot open '{vct}' as it is not "
            f"recognized as a supported file format, cannot execute '{fun.__name__}'."
        )
        raise PywatemsedemTypeError(msg)

    return True


def valid_raster(rst, fun):
    """Check if input file is a valid raster

    Parameters
    ----------
    rst: pathlib.Path
        File path to raster.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    """

    valid_exists(rst, fun)

    try:
        c = rasterio.open(rst)
        c.close()
    except RasterioIOError:
        msg = (
            f"The rasterio engine in pywatemsedem cannot open '{rst}' as it is not "
            f"recognized as a supported file format, cannot execute '{fun.__name__}'."
        )
        raise PywatemsedemTypeError(msg)

    return True


def valid_exists(rst, fun):
    """Check if input file exists

    Parameters
    ----------
    rst: pathlib.Path
        File path to raster.
    fun: callable
        See :func:`pywatemsedem.geo.valid.valid_input`.
    """

    if not Path(rst).exists():
        if fun is not None:
            msg = (
                f"Input raster '{rst}' does not exist, cannot execute "
                f"'{fun.__name__}'."
            )
        else:
            msg = f"Input raster '{rst}' does not exist"
        raise PywatemsedemInputError(msg)

    return True


VALID_FUN = [
    "valid_vectorlist",
    "valid_pointvector",
    "valid_polygonvector",
    "valid_linesvector",
    "valid_raster",
    "valid_vector",
    "valid_rasterlist",
]


def valid_input(func=None, dict=None):
    """Customizable wrapper function that allows to check arg-defined function input.

    This wrapper is defined to check formats of file-based raster and vector input. It
    makes use of a dictionary to apply specific valid functions on non-keyword
    arguments.  This valid function is typically applied to functions which have file
    paths that have to be checked in their input.

    Parameters
    ----------
    func: callable
        To call function for which to check inputs. Note that only function with all
        keyword-arguments as parameters can be used.
    dict: dictionary
        Holding string of fun parameters as keys, and valid-callable function as
        values.

    Returns
    -------
    function output

    Examples
    --------
    Use with a '@'-decorator to check input types for utils functions:

    ::

        from pywatemsedem.geo.utils import valid_input,valid_rasterlist,valid_polygonvector
        #note: only on-keyword arguments!
        @valid_input(dict={"lst_rst": valid_rasterlist, "vct_in": valid_polygonvector})
        def grid_statistics(lst_rst,vct_in):
        # ... function code

    Above example check if input of lst_rst is a list of rasters (and rasters exist)
    (1) and if input of vct_in is a polygoon shape (2).

    Note
    -----
    1. Can only be applied to non-keyword arguments.
    2. Validation methods should be added to VALID_FUN.
    """
    assert callable(func) or func is None

    def _decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for it, key in enumerate(signature(func).parameters.keys()):
                if key in dict:
                    valid_fun = dict[key]
                    if valid_fun.__name__ not in VALID_FUN:
                        msg = (
                            f"Validation fuction {valid_fun} for {key} not "
                            f"implemented"
                        )
                        raise KeyError(msg)
                    else:
                        valid_fun(args[it], func)
            return func(*args, **kwargs)

        return wrapper

    return _decorator(func) if callable(func) else _decorator


def valid_rp(rp):
    """Check if rasterproperties is not equal to none and valid

    Parameters
    ----------
    rp: pywatemsedem.geo.rasterproperties.RasterProperties
    """
    if rp is None:
        msg = "Please define rasterproperties"
        raise PywatemsedemInputError(msg)
    if not isinstance(rp, RasterProperties):
        msg = (
            f"Input RasterProperties '{rp}' is not a valid instance of the "
            f"'{RasterProperties}' class"
        )
        raise PywatemsedemTypeError(msg)

    return True


def valid_mask(mask):
    """Check if mask is not equal to none and valid

    Parameters
    ----------
    mask
    """
    if mask is None:
        msg = "Please define a mask"
        raise PywatemsedemInputError(msg)
    if set(np.unique(mask)) != {0, 1}:
        msg = "Please define a valid mask with only 0,1-values"
        raise PywatemsedemTypeError(msg)

    return True
