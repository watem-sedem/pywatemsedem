# Standard libraries
import logging
import os
import subprocess
import tempfile
from copy import deepcopy
from functools import wraps
from pathlib import Path

import fiona
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from rasterio.merge import merge

from pywatemsedem.geo.rasterproperties import RasterProperties

from ..defaults import (
    SAGA_FLAGS,
    SUFFIXES_RST,
    SUFFIXES_SAGA,
    SUFFIXES_SHP,
    SUFFIXES_TIF,
    SUFFIXES_TXT,
)
from .valid import (
    valid_input,
    valid_linesvector,
    valid_pointvector,
    valid_polygonvector,
    valid_raster,
    valid_rasterlist,
    valid_vector,
    valid_vectorlist,
)

logger = logging.getLogger(__name__)


@valid_input(dict={"rst_in": valid_raster})
def check_rst_dimensions(rst_in, minmax, ncols, nrows, transform=None):
    """This function checks if the input raster has the desired dimensions.

    Parameters
    ----------
    rst_in: str
        File path to input raster
    minmax: list
        Containing xmin, ymin, xmax, ymax
    ncols: int
        Number of columns in the raster
    nrows: int
        Number of rows in the raster
    transform:  rasterio.transform, default None
        Transformation as defined in Rasterio.

    Returns
    -------
    bool
        Raster has the required dimensions (True/False)
    """
    coordinates, transf, cols, rows = read_rst_params(rst_in)

    if cols != ncols:
        return False

    elif rows != nrows:
        return False

    elif minmax != coordinates:
        return False

    elif transform is not None:
        if transf != transform:
            return False
    else:
        return True


@valid_input(dict={"rst_in": valid_raster})
def read_rst_params(rst_in):
    """Read all spatial dimensions of a raster

    Parameters
    ----------
    rst_in: pathlib.Path
        File path to the input raster

    Returns
    -------
    minmax: list
        A list with the extreme coordinate values (xmin, ymin, xmax and ymax)
    transform: rasterio.transform
        Transformation as defined in Rasterio.
    cols: int
        The number of columns in the raster
    rows: int
        The number of rows in the raster
    """
    with rasterio.open(rst_in) as src:
        cols = src.width
        rows = src.height
        xmin = src.bounds[0]
        ymin = src.bounds[1]
        xmax = src.bounds[2]
        ymax = src.bounds[3]
        transf = src.transform
        minmax = [xmin, ymin, xmax, ymax]
    return minmax, transf, cols, rows


@valid_input(dict={"rst_in": valid_raster})
def read_dtype_raster(rst_in):
    """Read dtype of raster

    Parameters
    ----------
    rst_in: pathlib.Path
        File path to the input raster

    Returns
    -------
    dtype: numpy.dtype

    Note
    -----
    Only works for single band rasters
    """
    with rasterio.open(rst_in) as src:
        dtype = src.dtypes[0]
    return np.dtype(dtype)


@valid_input(dict={"rst_in": valid_raster})
def read_rasterio_profile(rst_in):
    """Read all spatial dimensions of a raster

    Parameters
    ----------
    rst_in: pathlib.Path
        File path to the input raster

    Returns
    -------
    profile: dict
        See :func:`pywatemsedem.geo.rasterproperties.RasterProperties.rasterio_profile`
    """
    with rasterio.open(rst_in) as src:
        profile = src.profile

    return profile


def write_arr_as_rst(arr, rst_out, dtype, profile):
    """Write numpy.ndarray as a raster-file

    Parameters
    ----------
    arr: numpy.ndarray
        2D numpy array to be written as a raster file
    rst_out: str
        File path to the output raster
    dtype: numpy.dtype
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`
    """
    mandatorykeys = [
        "driver",
        "height",
        "width",
        "crs",
        "transform",
        "count",
        "nodata",
    ]
    for key in mandatorykeys:
        if key not in profile.keys():
            msg = "not all mandatory keys in the profile are given! "
            msg += key
            raise Exception(msg)
    if "compress" not in profile:
        profile["compress"] = "DEFLATE"

    if "dtype" in profile.keys():
        profile.pop("dtype", None)

    if not rasterio.dtypes.check_dtype(dtype):
        msg = f"no valid dtype chosen! {dtype}"
        raise TypeError(msg)

    if arr.shape[1] != profile["width"] or arr.shape[0] != profile["height"]:
        msg = "dimensions of array are not the same of the given profile"
        raise Exception(msg)

    with rasterio.open(rst_out, "w", dtype=dtype, **profile) as dst:
        dst.write(arr, 1)


def check_raster_properties_raster_with_template(path_check, path_template, epsg):
    """Checks if extent and resolution of new raster and template raster align

    Parameters
    ----------
    path_check: pathlib.Path | RasterProperties
                Incoming, new raster
    path_template: pathlib.Path
                    Template raster
    epsg: int
            EPSG code of the cartographic projection
    """
    if isinstance(path_check, Path):
        rp_check = RasterProperties.from_rasterio(
            read_rasterio_profile(path_check), epsg=epsg
        )
    else:
        rp_check = path_check

    rp_template = RasterProperties.from_rasterio(
        read_rasterio_profile(path_template), epsg=epsg
    )
    if rp_check.bounds != rp_template.bounds:
        msg = "Extent of new raster not the same as of template raster"
        raise ValueError(msg)
    elif rp_check.resolution != rp_template.resolution:
        msg = "Resolution of new raster not the same as of template raster"
        raise ValueError(msg)


@valid_input(dict={"rst_in1": valid_raster, "rst_in2": valid_raster})
def grid_difference(rst_in1, rst_in2, rst_out):
    """Make the difference between two grids

    Parameters
    ----------
    rst_in1: str
        File path to inputraster 1
    rst_in2: str
        File path to inputraster 2
    rst_out: str
        File path to outputraster
    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "grid_calculus", "3"]
    cmd_args += ["-A", str(rst_in1), "-B", str(rst_in2), "-C", str(rst_out)]

    execute_saga(cmd_args)


@valid_input(dict={"rst_in": valid_raster})
def create_hillshade(rst_in, rst_hillshade):
    """Create a hillshade raster of the DTM

    Parameters
    ----------
    rst_in: str
        File path of input raster
    rst_hillshade: str
        File path of output raster
    """
    if isinstance(rst_hillshade, str):
        rst_hillshade = Path(rst_hillshade).parent / (Path(rst_hillshade).stem + ".tif")
    elif isinstance(rst_hillshade, Path):
        rst_hillshade = rst_hillshade.parent / (rst_hillshade.stem + ".tif")
    else:
        msg = (
            f"'hillshade' is of type {type(rst_hillshade)}, "
            f"cannot be converted to Pathlib Path"
        )
        raise TypeError(msg)

    cmd_args = ["gdaldem", "hillshade", "-q"]
    cmd_args += ["-co", "COMPRESS=DEFLATE"]
    cmd_args += [str(rst_in), str(rst_hillshade)]
    execute_subprocess(cmd_args)


@valid_input(dict={"vct": valid_vector})
def get_fields_vct(vct):
    """Get a list of all fields in a shapefile

    Parameters
    ----------
    vct: str
        File path to shapefile

    Returns
    -------
    list
        Field names of the shape/vector-file.
    """
    with fiona.open(vct) as c:
        fields = c.schema["properties"].keys()
        return fields


@valid_input(dict={"vct": valid_vector})
def get_geometry_type(vct):
    """Get the geometry type of a shapefile

    Parameters
    ----------
    vct: str
        File path to shapefile

    Returns
    -------
    str
        Geometry type (see fiona documentation for all possibilities)
    """
    with fiona.open(vct) as c:
        geom = c.schema["geometry"]
    return geom


def copy_rst(rst_in, rt_out):
    """Copy a raster and converts it to an idrisi-raster

    Parameters
    ----------
    rst_in: str
        File path of input raster
    rt_out: str
        File path of output raster (extension must be .rst!)

    Note
    -----
    Uses and relies on gdal_translate CLI
    """
    if rt_out.exists():
        delete_rst(rt_out)

    cmd_args = ["gdal_translate", "-q", "-of", "RST", str(rst_in), str(rt_out)]
    execute_subprocess(cmd_args)


@valid_input(dict={"vct_in": valid_vector})
def copy_vct(vct_in, folder_out):
    """Copies a shapefile to another location

    Parameters
    ----------
    vct_in: str or pathlib.Path
        File path of the shapefile to be copied.
    folder_out: str or pathlib.Path
        File path of the destination shapefile.

    Note
    -----
    Uses and relies on ogr2ogr CLI
    """
    cmd_args = ["ogr2ogr", str(folder_out), str(vct_in)]
    execute_subprocess(cmd_args)


@valid_input(dict={"tiff_in": valid_raster})
def tiff_to_esri_shp(tiff_in, vct_out, epsg):
    """
    Transform a tiff file to an esri shape (raster to shape)

    Parameters
    ----------
    tiff_in: str or pathlib.Path
        name input tiff
    vct_out: str or pathlib.Path
        name input shapefile
    epsg: str, default None
        the epsg code defining the coordinate system of the raster,
        format = "EPSG:XXXXX"
    """
    gpd_db = tiff_to_geopandas_df(tiff_in, epsg)
    gpd_db.to_file(Path(vct_out))


@valid_input(dict={"tiff_in": valid_raster})
def tiff_to_geopandas_df(tiff_in):
    """Transform a tiff file to a geopandas dataframe

    Parameters
    ----------
    tiff_in: str or pathlib.Path
        File path of tiff raster file

    Returns
    -------
    gdf: geopandas.GeoDataFrame
        Geopandas representation of tiff raster
    """
    with rasterio.open(str(tiff_in)) as src:
        image = src.read(1)
        crs = src.profile["profile"]
        results = (
            {"properties": {"values": values}, "geometry": geometry}
            for i, (geometry, values) in enumerate(
                shapes(image, transform=src.profile["transform"])
            )
        )

    geoms = list(results)
    gdf = gpd.GeoDataFrame.from_features(geoms, crs=crs)

    return gdf


@valid_input(dict={"rst_in": valid_raster})
def idrisi_to_tiff(rst_in, tiff_out, dtype, epsg="EPSG:31370"):
    """Convert an Idrisi RST to GeoTiff

    Parameters
    ----------
    rst_in: str
        File path of the input rst.
    tiff_out: str
        File path of the output tiff file.
    dtype: str
        Data type of the destination rst, either 'integer' or 'float'.

    Note
    -----
    Uses and relies on gdal_translate CLI
    """

    if dtype == "integer":
        cmd_args = [
            "gdal_translate",
            "-q",
            "-ot",
            "Int16",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=DEFLATE",
            "-a_srs",
            str(epsg),
            str(rst_in),
            str(tiff_out),
        ]
        execute_subprocess(cmd_args)
    elif dtype == "float":
        cmd_args = [
            "gdal_translate",
            "-q",
            "-ot",
            "Float32",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=DEFLATE",
            "-a_srs",
            str(epsg),
            str(rst_in),
            str(tiff_out),
        ]
        execute_subprocess(cmd_args)
    else:
        msg = 'Saving rst as tif. Type must be "integer" or "float"'
        logger.error(msg)
        raise TypeError(msg)


def valid_gdal_type(func):
    """Check if your input array mask is valid. Use as decorator"""

    @wraps(func)
    def wrapper(*args, dtype):
        """Wrapper function

        Parameters
        ----------
        *args:
            non keyword arguments
        dtype: numpy.dtype or str
            allowed types are "Float32", "Float64", "Int16", "Int32", "Int64"
            integer is Int16, float is Float32
        """
        if dtype == "integer":
            dtype = "Int16"
        if dtype == "float":
            dtype = "Float32"
        implemented_types = ["Float32", "Float64", "Int16", "Int32", "Int64"]
        # check value dtype and if not string
        if dtype in [np.int16, np.int32, np.int64, np.float32, np.float64]:
            try:
                dtype = dtype.__name__
            except AttributeError:
                dtype = dtype.name
        dtype = dtype.capitalize()
        if dtype not in implemented_types:
            raise IOError(
                f"Raster type {dtype} not known for gdal, please select "
                f"{', '.join(implemented_types)}"
            )
        func(*args, dtype)

    return wrapper


@valid_input(dict={"tiff_in": valid_raster})
@valid_gdal_type
def tiff_to_idrisi(tiff_in, rst_out, dtype):
    """Convert a GeoTiff to an Idrisi RST

    Parameters
    ----------
    tiff_in: str
        File path of the input tiff file
    rst_out: str
        File path of the destination rst
    dtype: str, default Float64
        Raster type

    Note
    ----
    Uses and relies on gdal_translate CLI
    """
    cmd_args = [
        "gdal_translate",
        "-q",
        "-ot",
        dtype.capitalize(),
        "-of",
        "RST",
        str(tiff_in),
        str(rst_out),
    ]
    execute_subprocess(cmd_args)


def get_feature_count(vct):
    """Count the amount of features in a shapefile

    Parameters
    ----------
    vct: str
        File path of the shapefile.

    Returns
    -------
    nr_features: int
        Number of features in the shapefile
    """
    with fiona.open(vct) as c:
        nr_features = len(c)
    return nr_features


@valid_input(dict={"lst_vct": valid_vectorlist})
def merge_lst_vct(lst_vct, vct_out, epsg):
    """Merge a list of shapefiles to one shapefile

    Parameters
    ----------
    lst_vct: list
        List with file paths (str) of all shapefiles to be merged.
    vct_out: str
        File path of merged vct
    epsg: str
        The epsg code defining the coordinate system of the raster,
        format = "EPSG:XXXXX"

    Note
    ----
    Uses and relies on ogr2ogr CLI
    """
    for i, vct in enumerate(lst_vct):
        if i == 0:
            copy_vct(vct, vct_out)
        else:
            cmd_args = ["ogr2ogr", "-update", "-a_srs", str(epsg)]
            cmd_args += ["-append", str(vct_out)]
            cmd_args.append(str(vct))
            cmd_args += ["-nln", vct_out.stem]

            execute_subprocess(cmd_args)


@valid_input(dict={"lst_vct": valid_vectorlist})
def merge_lst_vct_saga(lst_vct, vct_out):
    """Merge a list of shapefiles to one shapefile

    Parameters
    ----------
    lst_vct: list
        List with file paths (str) of all shapefiles to be merged.
    vct_out: str
        File path + name of the destination shapefile.

    Note
    ----
    Uses and relies on ogr2ogr CLI
    """

    cmd_args = (
        ["saga_cmd", SAGA_FLAGS, "shapes_tools", "2"]
        + [f"-INPUT={';'.join(lst_vct)}"]
        + [f"-MERGED={vct_out}"]
    )
    execute_saga(cmd_args)


@valid_input(dict={"rst_in": valid_raster})
def delete_rst(rst_in):
    """Delete a raster dataset

    Parameters
    ----------
    rst_in: str
        File path of the raster dataset to be deleted

    """
    cmd_args = ["gdalmanage", "delete", str(rst_in)]
    execute_subprocess(cmd_args)
    return


@valid_input(dict={"rst_in": valid_raster})
def clip_rst(rst_in, rst_out, Cnst, resampling="near"):
    """Clips a raster to a certain bounding box with a given resolution

    Parameters
    ----------
    rst_in: str
        File path to in input raster.
    rst_out: str
        File path to the destination raster.
    Cnst: dict
        Dictionary with following keys:

        - *epsg* (str): the EPSG-code of the rst_in
        - *res* (int): resolution
        - *nodata* (int): nodata flag
        - *minmax* (list): list with xmin, ymin, xmax, ymax
    resampling: str, default 'near'
        Either "mode" or "near"

    Notes
    -----
    1. "mode" and "near" have been tested, see
        https://gdal.org/programs/gdalwarp.html#cmdoption-gdalwarp-r
    """

    rst_in = Path(rst_in)
    rst_out = Path(rst_out)

    logger.info(f"Clipping {rst_in.name}...")
    cmd_args = ["gdalwarp", "-q", "-s_srs", str(Cnst["epsg"])]
    cmd_args += ["-t_srs", str(Cnst["epsg"])]
    cmd_args += ["-te"]
    for oor in Cnst["minmax"]:
        cmd_args += [str(oor)]
    cmd_args += ["-tr", str(Cnst["res"]), str(Cnst["res"])]
    cmd_args += ["-r", resampling]
    cmd_args += [str(rst_in), str(rst_out)]
    execute_subprocess(cmd_args)


@valid_input(dict={"vct": valid_vector})
def get_extent_vct(vct):
    """Gets the bounding box coordinates of a shapefile

    Parameters
    ----------
    vct: str or pathlib.Path
        File path of the input shapefile.

    Returns
    -------
    tuple
        xmin, ymin, xmax, ymax
    """
    with fiona.open(vct) as c:
        extent = c.bounds
    return extent  # xmin, ymin, xmax, ymax


@valid_input(dict={"vct": valid_vector, "vct_clip": valid_vector})
def clip_vct(vct_in, vct_out, vct_clip, overwrite=False, lst_ignore_field=None):
    """Clip a shapefile by another shapefile

    Parameters
    ----------
    vct_in: pathlib.Path
        File path of shapefile to be clipped.
    vct_out: pathlib.Path
        File path of the destination shapefile
    vct_clip: str
        File path of the clip boundary vector
    overwrite: bool, default False
        If True, overwrite existing file
    lst_ignore_field: list, optional
        Ignore a specific field from input in output.

    Note
    ----
    Uses and relies on ogr2ogr CLI
    """
    cond = True
    if not overwrite:
        if vct_out.exists():
            cond = False
    if cond:
        logger.info(f"Clipping {vct_in.name}...")
        ext = get_extent_vct(vct_clip)
        cmd_args = [
            "ogr2ogr",
            "-spat",
            str(ext[0]),
            str(ext[1]),
            str(ext[2]),
            str(ext[3]),
        ]
        cmd_args += ["-skipfailures"]
        cmd_args += ["-clipsrc", str(vct_clip)]
        if lst_ignore_field is not None:
            fields = get_fields_vct(vct_in)
            cmd_args += [
                "-select",
                (", ").join(
                    [field for field in fields if field not in lst_ignore_field]
                ),
            ]
        cmd_args += [str(vct_out), str(vct_in)]
        execute_subprocess(cmd_args)


@valid_input(dict={"lst_rasters": valid_rasterlist, "vct_polygon": valid_vector})
def compute_statistics_rasters_per_polygon_vector(
    lst_rasters,
    vct_polygon,
    vct_out,
    lst_names,
    dict_operators,
    normalize=True,
    ton=False,
):
    """Compute statistics

    Parameters
    ----------
    lst_rasters: list
        File path rasters (pathlib.Path)
    vct_polygon: str
        File path to input polygon vector.
    vct_out: str
        File path to output polygon vector.
    lst_names: dict
        List of output names in output vector for files in lst_rasters.
    dict_operators: dict
        Operators. For a description of the dictionary of statistics, see
        inputs in :func:`pywatemsedem.geo.utils.grid_statistics`. See example for use.
    normalize: bool, default False
        Normalize with shape area (True)
    ton: bool, default False
        Use ton (true)

    Note
    ----
    The desired statistics are inputted after the file reference of the raster, and are
    formatted as a dictionary, e.g.:

    .. code-block:: python

        dict_operators = {"COUNT":True,"SUM":True}

    Examples
    --------

    >>> vct_aho = "AHO.shp"
    >>> vct_out = "statistics_aho.shp"
    >>> rst_sewerin ="sewerin.rst"
    >>> rst_sediexport ="SediExport.rst"
    >>> compute_statistics_rasters_per_polygon_vector(vct_aho,
    >>>                                                   vct_out,
    >>>                                                   [rst_sewerin,rst_sediexport]
    >>>                                                   ["River","Sewers"],
    >>>                                                   {"COUNT":True,"SUM":True},
    >>>                                                   ton = True)
    """
    grid_statistics(lst_rasters, vct_polygon, vct_out, **dict_operators)

    gdf = gpd.read_file(vct_out)
    rename = {
        f"G{ind + 1:02d}_{op}": name
        for ind, name in enumerate(lst_names)
        for op in dict_operators
    }
    gdf = gdf.rename(columns=rename)
    for col in lst_names:
        gdf.loc[gdf[col].isnull(), col] = 0
        if ton:
            gdf[col] = gdf[col] / 1000.0
        if normalize:
            gdf[col + "_ha"] = gdf[col] * 100**2 / (gdf.area)

    gdf.to_file(vct_out)

    return gdf


@valid_input(dict={"rst_in": valid_raster})
def rst_to_vct_points(rst_in, vct_out):
    """Convert all no nodata values in a raster to a vector point file.

    Parameters
    ----------
    rst_in: str or pathlib.Path
        File path of the raster file that should be converted to a shapefile.
    vct_out: pathlib.Path
        File path of the destination vct.
    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_grid", "3"]
    cmd_args += ["-GRIDS", str(rst_in)]
    cmd_args += ["-SHAPES", str(vct_out)]
    execute_saga(cmd_args)


@valid_input(dict={"vct_in": valid_vector})
def vct_to_rst_value(
    vct_in, rst_out, rstval, Cnst, nodata=-9999, alltouched=True, dtype=None
):
    """Rasterizes a shapefile by a given constant value

    Parameters
    ----------
    vct_in: str or pathlib.Path
        File path of the shapefile to be rasterized.
    rst_out: pathlib.Path
        File path of the destination rst
    Cnst: dict
        Dictionary with following keys:

        - *res* (int): resolution
        - *nodata* (int): nodata flag
        - *minmax* (list): list with xmin, ymin, xmax, ymax

    rstval: str
        The value all features of the shapefile will get in the raster.
    alltouched: bool, default true
        Enables the ALL_TOUCHED rasterization option so that all pixels
        touched by lines or polygons will be updated.
    dtype: str, default None
        Data type of the values, e.g. Byte/Int16/UInt16/UInt32/Int32/Float32...

    Note
    -----
    Uses and relies on gdal_rasterize CLI
    """
    cmd_args = ["gdal_rasterize", "-q", "-a_nodata", str(nodata)]
    if alltouched:
        cmd_args += ["-at"]
    cmd_args += ["-burn", str(rstval)]
    cmd_args += ["-l", vct_in.stem]
    cmd_args += ["-of", "GTiff", "-te"]
    for oor in Cnst["minmax"]:
        cmd_args += [str(oor)]
    if dtype is not None:
        cmd_args += ["-ot", dtype]
    cmd_args += ["-tr", str(Cnst["res"]), str(Cnst["res"])]
    cmd_args += ["-co", "COMPRESS=DEFLATE"]
    cmd_args += [str(vct_in), str(rst_out)]

    execute_subprocess(cmd_args)


@valid_input(dict={"rst_in": valid_raster})
def reclass_rst(rst_in, rst_out, df_reclass):
    """Reclass of a raster based on pandas dataframe

    Parameters
    ----------
    rst_in: str or pathlib.Path
        File path of the input raster
    rst_out: pathlib.Path
        File path of the destination rst (.sdat)
    df_reclass: pandas.DataFrame
        DataFrame containing the mapping with the columns:

        - *RST_VAL*: current values
        - *NEWVAL*: new value

    Note
    -----
    Uses and relies on saga_cmd CLI
    """
    df_reclass["MAX"] = df_reclass["RST_VAL"] + 1
    txt_reclass = rst_out.parent / (rst_out.stem + "_reclasstable.csv")
    df_reclass[["RST_VAL", "MAX", "NEWVAL"]].to_csv(txt_reclass, index=False)
    cmd_args = ["saga_cmd", SAGA_FLAGS, "grid_tools", "15", "-INPUT", str(rst_in)]
    cmd_args += ["-RESULT", str(rst_out), "-METHOD", "3", "-RETAB_2", str(txt_reclass)]
    cmd_args += [
        "-F_MIN=RST_VAL",
        "-F_MAX=MAX",
        "-F_CODE=NEWVAL",
        "-TOPERATOR=0",
        "-RESULT_NODATA_CHOICE=0",
    ]

    execute_saga(cmd_args)


@valid_input(dict={"rst_in": valid_raster})
def raster_to_polygon(rst_in, vct_out):
    """Polygonize a raster

    This function converts rastercells to polygons

    Parameters
    ----------
    rst_in: str or pathlib.Path
        File path of theinput raster
    vct_out: str or pathlib.Path
        File path of the destination shapefile

    Note
    -----
    Uses and relies on saga_cmd CLI
    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_grid", "6", "-GRID", str(rst_in)]
    cmd_args += ["-POLYGONS", str(vct_out), "-CLASS_ALL", "1", "-SPLIT", "0"]
    execute_saga(cmd_args)


@valid_input(dict={"vct_lines": valid_linesvector, "vct_points": valid_pointvector})
def lines_to_points(vct_lines, vct_points, distance):
    """Converts a shapefile with lines to a shapefile with points.

    Parameters
    ----------
    vct_lines: str or pathlib.Path
        File path to the input shapefile with lines.
    vct_points: str or pathlib.Path
        File path to the output shapefile with points.
    distance: float
        Distance between two points

    Note
    -----
    Uses and relies on saga_cmd CLI
    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_points", "5"]
    cmd_args += ["-LINES", str(vct_lines), "-POINTS", str(vct_points)]
    cmd_args += ["-ADD", "1", "-METHOD_INSERT", "0", "-DIST", distance]
    cmd_args += ["-ADD_POINT_ORDER", "1"]

    execute_saga(cmd_args)
    return


@valid_input(dict={"vct_line": valid_linesvector, "rst_template": valid_raster})
def lines_to_direction(vct_line, rst_out, rst_template):
    """Converts line features to a direction raster

    This function converts the direction of line features to a raster. See the
    :ref:`docs of cnws for more information <watemsedem:routingmap>` about this raster

    Parameters
    ----------
    vct_line: str or pathlib.Path
        File path to the input line shapefile
    rst_out: pathlib.Path
        File path to the output raster
    rst_template: str or pathlib.Path
        File path to a template raster

    Note
    -----
    Uses and relies on saga_cmd CLI

    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "line_direction", "0"]
    cmd_args += [
        "-INPUT",
        str(vct_line),
        "-TARGET_DEFINITION",
        "1",
        "-TARGET_TEMPLATE",
        str(rst_template),
    ]
    cmd_args += ["-GRID", str(rst_out), "-ORDER_FIELD", "sort_order"]

    execute_saga(cmd_args)

    rst_out = rst_out.parent / (rst_out.stem + ".sdat")

    arr, profile = load_raster(rst_out)
    profile["compress"] = "DEFLATE"
    profile["nodata"] = 0
    arr += 1
    arr = np.where(arr == 256, 0, arr).astype("int16")
    write_arr_as_rst(arr, rst_out, "int16", profile)
    return


@valid_input(dict={"vct": valid_vector})
def check_single_polygon(vct):
    """Check if the catchment polygon is a single polygon (not empty or
    multipolygon).

    Parameters
    -----------
    vct: str or pathlib.Path
        File path of the shapefile
    """
    with fiona.open(vct) as c:
        nr_polygons = len(c)
        if nr_polygons != 1:
            msg = (
                f"Catchment polygon should be a single polygon, current "
                f"catchment polygon holds '{nr_polygons}' polygons."
            )
            IOError(msg)


@valid_input(dict={"vct_in": valid_vector})
def vct_to_rst_field(
    vct_in, rst_out, Cnst, field=None, alltouched=True, dtype="Float64"
):
    """Rasterizes a shapefile by a given attribute field

    Parameters
    ----------
    vct_in: str or pathlib.Path
        File path of the shapefile to be rasterized.
    rst_out: pathlib.Path
        File path of the destination rst
    Cnst: dict
        Dictionary with following keys:

        - *res* (int): resolution
        - *nodata* (int): nodata flag
        - *minmax* (list): list with xmin, ymin, xmax, ymax

    field: str
        The field of the shapefile containing the values for the raster
    alltouched: bool, default True
        Enables the ALL_TOUCHED rasterization option so that all pixels
        touched by lines or polygons will be updated.
    dtype: str, default None
        Data type of the values, e.g. Byte/Int16/UInt16/UInt32/Int32/Float32...

    Note
    ----
    Uses and relies on gdal_rasterize CLI
    """
    # if rst_out.exists():
    #    delete_rst(rst_out)

    if isinstance(rst_out, str):
        rst_out = Path(rst_out).parent / (Path(rst_out).stem + ".tif")
    elif isinstance(rst_out, Path):
        rst_out = rst_out.parent / (rst_out.stem + ".tif")
    else:
        msg = (
            f"'outrst' is of type {type(rst_out)}, "
            f"can not be converted to Pathlib Path"
        )
        raise TypeError(msg)

    if isinstance(vct_in, str):
        vct_in = Path(vct_in).parent / (Path(vct_in).stem + ".shp")
    elif isinstance(vct_in, Path):
        vct_in = vct_in.parent / (vct_in.stem + ".shp")
    else:
        msg = (
            f"'inshp' is of type {type(vct_in)}, "
            f"can not be converted to Pathlib Path"
        )
        raise TypeError(msg)

    cmd_args = ["gdal_rasterize", "-q", "-a_nodata", str(Cnst["nodata"])]
    if alltouched:
        cmd_args += ["-at"]
    if field:
        cmd_args += ["-a", field]
    cmd_args += ["-l", vct_in.stem]
    cmd_args += ["-of", "GTiff", "-te"]
    for oor in Cnst["minmax"]:
        cmd_args += [str(oor)]

    cmd_args += ["-ot", dtype]
    cmd_args += ["-tr", str(Cnst["res"]), str(Cnst["res"])]
    cmd_args += ["-co", "COMPRESS=DEFLATE"]
    cmd_args += [str(vct_in), str(rst_out)]

    execute_subprocess(cmd_args)


def execute_saga(cmd_args):
    """Run saga executable and catch non-informative error

    This function catches saga error command and ignores 'corrupted size vs. prev_size
    in fastbins' error in case output runs from saga are okay.

    Parameters
    ----------
    saga_cmd: list
        Saga command
    """
    if "saga_cmd" not in cmd_args:
        msg = f"{' '.join(cmd_args)} is not a saga command."
        raise IOError(msg)
    try:
        subprocess.check_output(cmd_args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if ("corrupted size vs. prev_size in fastbins" in e.output.decode()) & (
            "okay" in e.output.decode()
        ):
            pass
        else:
            print(e.output.decode())


@valid_input(dict={"vct_polygon": valid_polygonvector, "rst_template": valid_raster})
def polygons_to_raster(vct_polygon, rst_out, rst_template, field, dtype):
    """Converts a polygon shapefile to a raster

    Parameters
    ----------
    vct_polygon: str or pathlib.Path
        File path of input polygon shapefile
    rst_out: str or pathlib.Path
        File path of output rasterfile
    rst_template: str or pathlib.Path
        File path to a template raster
    field: str
        The field of the shapefile containing the values for the raster
    dtype: str, default None
        Data type of the values, e.g. Byte/Int16/UInt16/UInt32/Int32/Float32...

    Note
    -----
    Uses and relies on saga_cmd CLI

    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "grid_gridding", "0"]
    cmd_args += ["-INPUT", str(vct_polygon), "-FIELD", str(field)]
    cmd_args += ["-OUTPUT", "2", "-POLY_TYPE", "1"]
    if dtype == "integer":
        grid_type = "6"  # 4 byte unsigned integer
    elif dtype == "float":
        grid_type = "7"  # 4 byte floating point
    else:
        grid_type = "9"  # same as attribute
    cmd_args += ["-GRID_TYPE", grid_type, "-TARGET_DEFINITION", "1"]
    cmd_args += ["-TARGET_TEMPLATE", str(rst_template), "-GRID", str(rst_out)]
    execute_saga(cmd_args)


@valid_input(dict={"vct_line": valid_linesvector, "rst_template": valid_raster})
def lines_to_raster(vct_line, rst_out, rst_template, field, dtype):
    """Converts a line shapefile to a raster

    Parameters
    ----------
    vct_line: str or pathlib.Path
        File path of input line shapefile
    rst_out: str or pathlib.Path
        File path of output rasterfile
    rst_template: str or pathlib.Path
        File path to a template raster
    field: str
        The field of the shapefile containing the values for the raster
    dtype: str, default None
        Data type of the values, e.g. Byte/Int16/UInt16/UInt32/Int32/Float32...

    Note
    -----
    Uses and relies on saga_cmd CLI

    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "grid_gridding", "0"]
    cmd_args += ["-INPUT", str(vct_line), "-FIELD", str(field)]
    cmd_args += ["-OUTPUT", "2", "-LINE_TYPE", "1"]
    if dtype == "integer":
        grid_type = "6"  # 4 byte unsigned integer
    elif dtype == "float":
        grid_type = "7"  # 4 byte floating point
    else:
        grid_type = "9"  # same as attribute
    cmd_args += ["-GRID_TYPE", grid_type, "-TARGET_DEFINITION", "1"]
    cmd_args += ["-TARGET_TEMPLATE", str(rst_template), "-GRID", str(rst_out)]

    try:
        execute_subprocess(cmd_args)
    except OSError as e:
        if "corrupted size vs. prev_size in fastbins" in str(e):
            try:

                rasterio.open(rst_out.with_suffix(".sdat"))
            except rasterio.errors.RasterioIOError:
                raise IOError(e)


@valid_input(dict={"vct_in": valid_vector})
def create_spatial_index(vct_in):
    """Creates a qix-file for a given shapefile

    Parameters
    ----------
    vct_in: str or pathlib.Path
        File path of the input shapefile

    Note
    -----
    Uses and relies on ogrinfo CLI
    """
    if vct_in.exists():
        cmd_args = ["ogrinfo", str(vct_in)]
        cmd_args += ["-q", "-sql", f"CREATE SPATIAL INDEX ON {vct_in.stem}"]
        execute_subprocess(cmd_args)
    else:
        msg = f"Shapefile does not exist! ({vct_in})"
        logger.error(msg)
        raise FileNotFoundError(msg)
    return


@valid_input(dict={"rst": valid_raster})
def load_raster(rst, return_bounds=False):
    """load raster with rasterio

    Parameters
    ----------
    rst: str or pathlib.Path
        File path of the file, .rst arr.
    return_bounds: bool, default False
        Flag to indicate whether a bounds of the arr should be returned.

    Returns
    -------
    arr: numpy.ndarray
        Array format of raster file.
    bounds: list
        List of bounds (xmin,ymin,xmax,ymax).
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`
    """
    # load
    try:
        with rasterio.open(rst) as src:
            arr = src.read()[0]
            profile = src.profile
            if return_bounds:
                bounds = src.bounds
    except rasterio.errors.RasterioIOError as e:
        logger.error(e)
        msg = f"could not open {rst}"
        raise Exception(msg)
    if return_bounds:
        return arr, profile, bounds
    else:
        return arr, profile


def raster_array_to_pandas_dataframe(arr_raster, profile):
    """Convert a raster array to a pandas dataframe.

    Parameters
    ----------
    arr_raster: numpy.ndarray
        Array raster format
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`

    Returns
    -------
    df: pandas.DataFrame
        A pandas format of the array raster with

        - *row* (int): the row id
        - *col* (int): the column id
        - *val* (float): the value
    """
    nrows = profile["height"]
    ncols = profile["width"]
    # convert to list
    arr = np.empty([nrows * ncols, 3], dtype=np.float32)
    arr[:, 0] = arr_raster.flatten()
    arr[:, 2] = np.tile(np.arange(1, ncols + 1, 1), nrows)
    arr[:, 1] = np.repeat(np.arange(1, nrows + 1, 1), ncols)
    df = pd.DataFrame(arr, columns=["val", "row", "col"])

    return df


def raster_dataframe_to_arr(df, profile, col, dtype):
    """Convert a pandas dataframe column to an array

    Parameters
    ----------
    df: pandas.DataFrame
        A pandas format of the array raster with

        - *row* (int): the row id
        - *col* (int): the column id
        - *val* (float): the value

    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`
    col: str
        Column name to convert to raster
    dtype: numpy.dtype

    Returns
    -------
    arr: numpy.ndarray
        Array of dataframe columns 'val'
    """
    nrows = profile["height"]
    ncols = profile["width"]
    if col in df:
        df[col] = deepcopy(df[col]).astype(dtype)
    else:
        raise ValueError(f"{col} not in list of raster")
    df = df.sort_values(["row", "col"])
    arr = np.reshape(df[col].values, (nrows, ncols))
    return arr


@valid_input(dict={"vct_a": valid_vector, "vct_b": valid_vector})
def saga_intersection(vct_a, vct_b, vct_intersect):
    """Calculate the intersection between two shapefiles

    Parameters
    ----------
    vct_a: str or pathlib.Path
        File path of input shapefile 1
    vct_b: str or pathlib.Path
        File path of input shapefile 2
    vct_intersect: str or pathlib.Path
        File path of the calculated intersection shapefile

    Note
    -----
    Uses and relies on saga_cmd CLI

    """

    cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_polygons", "14"]
    cmd_args += ["-A", str(vct_a)]
    cmd_args += ["-B", str(vct_b)]
    cmd_args += ["-RESULT", str(vct_intersect)]

    execute_saga(cmd_args)


@valid_input(dict={"vct": valid_vector})
def write_area_ha_to_vct(vct):
    """Add a field 'AREA_HA' to a shapefile

    This function calculates the area of every feature in a shapefile in hectare

    Parameters
    ----------
    vct: str or pathlib.Path
        File path to the input shapefile

    """
    gdf = gpd.read_file(vct)
    gdf["AREA_HA"] = gdf.area / 100.0**2
    gdf.to_file(vct)


@valid_input(dict={"vct_lines": valid_linesvector, "vct_polygons": valid_polygonvector})
def add_length_lines_to_polygons(vct_lines, vct_polygons, vct_out, name_field):
    """Calculate the total length of line segments within a polygon

    Parameters
    ----------
    vct_lines: str or pathlib.Path
        File path of the input line shapefile
    vct_polygons: str or pathlib.Path
        File path of the input polygon shapefile
    vct_out: str or pathlib.Path
        File path of the output polygon shapefile
    name_field: str
        Attribute name containing the lenght of the lines within a polygon

    """
    gdf_lines = gpd.read_file(vct_lines)
    gdf_poly = gpd.read_file(vct_polygons)
    gdf_lines = gdf_lines[["geometry"]]
    gdf_lines[name_field] = gdf_lines.length
    sjoin = gpd.sjoin(gdf_lines, gdf_poly[["geometry"]], how="inner", op="within")
    sjoin = sjoin.groupby(["index_right"]).sum()
    gdf_poly = pd.merge(gdf_poly, sjoin, how="left", left_index=True, right_index=True)
    gdf_poly.to_file(vct_out)


@valid_input(dict={"lst_rst": valid_rasterlist, "vct_in": valid_polygonvector})
def grid_statistics(
    lst_rst,
    vct_in,
    vct_out,
    naming=0,
    COUNT=False,
    MIN=False,
    MAX=False,
    RANGES=False,
    SUM=True,
    MEAN=False,
):
    """Calculate zonal statistics for a raster based on polygons

    Parameters
    ----------
    lst_rst: list
        File paths (str or pathlib.Path) of the input rasters
    vct_in: str or pathlib.Path
        File path of the input polygon shapefile
    vct_out: str or pathlib.Path
        File path of the output shapefile with the raster statistics
    naming: int, default 0
        1: grid name (note: esrsi shapes ar capped on 10 characters)
        0: grid id
    COUNT: bool, default False
        Count the raster cells within every polygon
    MIN: bool, default False
        Calculate the minimum value within every polygon
    MAX: bool, default False
        Calculate the maximum value within every polygon
    RANGES: bool, default False
        Calculate the range within every polygon
    SUM: bool, default False
        Calculate the sum of all pixel values within every polygon
    MEAN: bool, default False
        Calculate the mean of all pixel values within every polygon

    Note
    -----
    Uses and relies on saga_cmd CLI

    """
    cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_grid", "2"]
    cmd_args += ["-GRIDS", ";".join([str(i) for i in lst_rst])]
    cmd_args += ["-NAMING", str(naming)]
    cmd_args += ["-POLYGONS", str(vct_in)]
    cmd_args += ["-RESULT", str(vct_out)]
    a = ["-COUNT", "-MIN", "-MAX", "-RANGE", "-SUM", "-MEAN"]
    for j, opt in enumerate([COUNT, MIN, MAX, RANGES, SUM, MEAN]):
        cmd_args += [a[j]]
        if opt:
            cmd_args += ["1"]
        else:
            cmd_args += ["0"]

    cmd_args += ["-VAR", "0", "-STDDEV", "0"]
    execute_saga(cmd_args)


@valid_input(dict={"rst_in": valid_raster, "rst_mask": valid_raster})
def mask_raster(rst_in, rst_mask, un_id, folder="masked"):
    """Mask a raster by setting no data with no data positions of mask

    The input raster is masked by the nodata value in the mask raster.

    Parameters
    ----------
    rst_in: str or pathlib.Path
        File path raster to be masked
    rst_mask: str  or pathlib.Path
        File path mask raster, see note for format
    un_id: int
        unique id of the raster
    folder: str, default 'masked'
        Folder in which to safe masked raster

    Returns
    -------
    rst_masker: str
        File path of masked raster

    Note
    ----
    1. This mask raster should be a (**no** `nodata`, `nodata`)-raster in which the
       nodata  values indicate masking, and non-nodata values indicates not masking.
    2. Masking of the input raster is facilitated by setting to-mask-values in the
       input raster to `nodata`.

    """
    if folder not in os.listdir():
        os.mkdir(folder)
    arr_mask, profile_mask = load_raster(rst_mask, list_format=True)
    arr_in, profile_in = load_raster(rst_in, list_format=True)
    rst_masked = Path(rst_in)
    rst_masked = Path("temp") / f"{rst_masked.stem}-{un_id}{rst_masked.suffix}"

    arr_in[arr_mask == profile_mask["nodata"]] = profile_in["nodata"]
    write_arr_as_rst(arr_in, rst_masked, arr_in.dtype, profile_in)

    return rst_masked


@valid_input(dict={"lst_rst": valid_rasterlist})
def merge_rasters(lst_rst, rst_out, lst_rst_masks=None):
    """Merge several rasters to one raster with option to mask input rasters

    Parameters
    ----------
    lst_rst: list of str or list of pathlib.Path
        List of file paths of rasters which have to be merged together
    rst_out: str or pathlib.Path
        File path of merged raster
    lst_rst_masks: list
        List of file paths of mask files to be used to mask lst_rst_in, see
        :func:`pywatemsedem.geo.utils.mask_raster`.
    """
    if lst_rst_masks is not None:
        lst_rst_temp = []
        for i, rst_in in enumerate(lst_rst):
            lst_rst_temp.append(mask_raster(rst_in, lst_rst_masks[i], i, "temp"))
        lst_rst = lst_rst_temp

    lst_src = []
    for rst in lst_rst:
        src = rasterio.open(rst)
        lst_src.append(src)

    if len(lst_src) > 0:
        mosaic, out_trans = merge(lst_src)
        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "compress": "DEFLATE",
            }
        )
        with rasterio.open(rst_out, "w", **out_meta) as dest:
            dest.write(mosaic)


def load_discharge_file(filename):
    """Function to read the discharge file as a dictionary

    Parameters
    ----------
    filename: str or pathlib.Path
        discharge file

    Returns
    -------
    discharge: dict
        contains discharge information
    """
    with open(filename) as f:
        lines = f.readlines()
    discharge = {}
    for line in lines[0:5]:
        discharge[line.split(":")[0]] = float(line.split(": ")[1].split(" (")[0])

    return discharge


def rasterprofile_to_rstparams(profile):
    """Transform rasterprofile to rstparams

    Parameters
    ----------
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`

    Returns
    -------
    rstparams: dict
        gdal dictionary holding all metadata for idrisi rasters

    """
    rstparams = {}

    rstparams["driver"] = "GTiff"
    minmax = profile["minmax"]
    rstparams["height"] = int(round((minmax[3] - minmax[1]) / profile["res"]))
    rstparams["width"] = int(round((minmax[2] - minmax[0]) / profile["res"]))
    rstparams["crs"] = profile["epsg"]
    rstparams["transform"] = rasterio.Affine(
        profile["res"],
        0,
        minmax[0],
        0,
        -profile["res"],
        minmax[3],
    )
    rstparams["count"] = 1
    rstparams["nodata"] = profile["nodata"]
    rstparams["compress"] = "DEFLATE"

    return rstparams


def rstparams_to_rasterprofile(rstparams, epsg=None):
    """Transform rstparams dictionary to to rasterio rasterprofile dictionary

    Parameters
    ----------
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`
    epsg: str, default None
        The epsg code defining the coordinate system of the raster,
        format = "EPSG:XXXXX"

    Returns
    -------
    rstparams: dict
        gdal dictionary holding all metadata for idrisi rasters

    """
    profile = {}

    profile["nodata"] = rstparams["nodata"]

    if "init" in list(rstparams["crs"].to_dict().keys()):
        profile["epsg"] = rstparams["crs"].to_dict()["init"]
    else:
        if epsg is not None:
            profile["epsg"] = epsg
        else:
            raise IOError("Cannot get epsg-code from rstparams, and no epsg defined!")

    profile["res"] = rstparams["transform"][0]

    xmin = rstparams["transform"][2]
    xmax = xmin + rstparams["transform"][0] * rstparams["width"]
    ymax = rstparams["transform"][5]
    ymin = ymax + rstparams["transform"][4] * rstparams["height"]

    profile["minmax"] = [xmin, ymin, xmax, ymax]
    profile["ncols"] = rstparams["width"]
    profile["nrows"] = rstparams["height"]

    return profile


@valid_input(dict={"rst_in": valid_raster})
def set_no_data_rst(
    rst_in, rst_out, arr_bindomain, profile, dtype=None, nodata_val=-9999
):
    """Set all pixels of a raster outside the model domain equal to NoData

    Parameters
    ----------
    rst_in: str
        File path of input raster to set no data values
    rst_out: str
        File path of output raster with no data values
    arr_bindomain: numpy.ndarray
        Array used to define domain nodata. In domain is equal to one,
        outside domain is equal to zero.
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`
    dtype: numpy.dtype, default None
        e.g. np.float64, np.float32, ..
    nodata_val: int, default -9999
        Standard value for nodata
    """

    profile["nodata"] = nodata_val

    arr_out, _ = load_raster(rst_in)
    arr_out[arr_bindomain == 0] = profile["nodata"]

    arr_out, profile = set_dtype_arr_rst(arr_out, profile, dtype=dtype)

    write_arr_as_rst(arr_out, rst_out, arr_out.dtype, profile)


def valid_mask(func):
    """Check if your input array mask is valid. Use as decorator"""

    @wraps(func)
    def wrapper(arr, arr_mask, nodata):
        """Wrapper function

        Parameters
        ----------
        arr:
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`
        arr_mask:
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`
        nodata:
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`
        """
        # check values mask
        un_mask = np.unique(arr_mask)
        if set(un_mask) != set([1, 0]):
            msg = (
                f"Mask array should have values 1 (no mask) and 0 (mask)"
                f"(mask) values, instead of {un_mask}."
            )
            raise ValueError(msg)

        # check if size input array is equal to mask array
        if arr.size != arr_mask.size:
            msg = "Mask array has different size from input array"
            raise IOError(msg)

        # check if input array is not empty after masking
        cond = np.all(arr[arr_mask == 1] == nodata) or arr[arr_mask == 1].size == 0

        if cond:
            msg = (
                "Array after masking has only nodata values/is empty. Please check "
                "your mask/input array."
            )
            raise ValueError(msg)

        return func(arr, arr_mask, nodata)

    return wrapper


@valid_mask
def set_no_data_arr(arr, arr_mask, nodata):
    """Set no data to values to raster array outside mask.

    Parameters
    ----------
    arr: numpy.ndarray
        To mask array
    arr_mask: numpy.ndarray
        Mask array
    nodata: float
        The no data value to set in input array
    """
    arr = np.where(arr_mask == 1, arr, nodata)
    return arr


def set_dtype_arr_rst(arr, profile, dtype=None):
    """Set type for an array

    Parameters
    ----------
    arr: numpy.ndarray
        arr of a raster for which dtype has to be changed
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`
    dtype: numpy.dtype, default None
        e.g. np.float64, np.float32, ..

    Returns
    -------
    arr: numpy.ndarray
        dtype-updated arr of a raster for which dtype has to be changed
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile` with update dtype geo medata information
    """
    if dtype is not None:
        arr = arr.astype(dtype)
        profile["dtype"] = dtype

    return arr, profile


@valid_input(dict={"rst": valid_raster})
def calculate_sum_rst(rst):
    """Calculate sum of a raster values

    Parameters
    ----------
    rst: pathlib.Path
        File path of the raster file

    Returns
    -------
    float:
        sum of the values in the raster
    """
    arr, profile = load_raster(rst)

    return np.sum(arr[arr != profile["nodata"]])


def get_rstparams(CNWS_modelinputfolder, epsg=None, catchmentname="", template=None):
    """Get rstparams and rasterprofile from template raster (default:pkaart)

    Parameters
    ----------
    CNWS_modelinputfolder: str or pathlib.Path
        the path to the CNWS_modelinputfolder
    epsg: str, default None
        the epsg code defining the coordinate system of the raster,
        format = "EPSG:XXXXX"
    catchmentname: str, default ""
        catchment name
    template: str or pathlib.Path, default None
        File path to a template file that can be used as template for
        geodata and bin mask. Default the "P" raster is used.

    Returns
    -------
    profile: rasterio.profiles
        See :class:`rasterio.profiles.Profile`
    rstparams: dict
        gdal dictionary holding all metadata for idrisi rasters
    arr_bindomain: numpy.ndarray
        binary mask of modelling domain

    """
    # this template is used to generate binair mask
    if template is None:
        template = Path(CNWS_modelinputfolder) / "pfactor.rst"
    # open and assign profile to rstparams
    try:
        src = rasterio.open(template)
    except IOError:
        msg = (
            f"Templatefile '{template}' not known for getting spatial metadata "
            f"'rstparams' and 'profile'."
        )
        raise IOError(msg)
    rstparams = src.profile
    rstparams["compress"] = "DEFLATE"
    profile = rstparams_to_rasterprofile(rstparams, epsg=epsg)

    return rstparams, profile


def get_mask_template(CNWS_modelinputfolder, catchmentname, rst_template=None):
    """Get a binary raster from template raster (P-factor)

    Parameters
    ----------
    CNWS_modelinputfolder: str or pathlib.Path
        File path to the CNWS_modelinputfolder
    catchmentname: str
        Catchment name
    rst_template: str or pathlib.Path, default None
        Path to a template file that can be used as template for geodata and bin mask

    Returns
    -------
    arr_bindomain: numpy.ndarray
        In domain is equal to one, outside domain is equal to zero.
    """

    if rst_template is None:
        rst_template = Path(CNWS_modelinputfolder) / "pfactor.rst"
    try:
        src = rasterio.open(rst_template)
    except IOError:
        msg = (
            f"Templatefile '{rst_template}' not known for getting spatial metadata"
            f" 'rstparams' and 'rasterprofile'."
        )
        raise IOError(msg)
    # get bin_arr
    arr_bindomain = src.read()[0]
    arr_bindomain[arr_bindomain != src.profile["nodata"]] = 1
    arr_bindomain[arr_bindomain == src.profile["nodata"]] = 0

    return arr_bindomain


def any_equal_element_in_vector(geoseries_left, geoseries_right):
    """Check if there are equal vectors in the left and right geoseries

    Parameters
    ----------
    geoseries_left: geopandas.GeoSeries
    geoseries_right: geopandas.GeoSeries

    Return
    ------
    bool
        Line strings present in left and right geoseries
    """
    for x in geoseries_left:
        n = np.sum(geoseries_right.geom_equals(x))
        if n > 0:
            return True
    return False


@valid_input(dict={"rst_in": valid_raster})
def check_spatial_resolution_rst(rst_in, resolution, precision=0.01):
    """Check if the resolution of a tiff raster is equal to a defined one

    Parameters
    ----------
    rst_in: str or pathlib.Path
        File path of input raster
    resolution: int
        Resolution to compare with
    precision: float, default 0.01
        Precision to check resolution

    Returns
    -------
    cond: bool
        Equal/non-equal (True/False)
    """
    cond = True
    with rasterio.open(str(rst_in)) as src:
        res_tif = src.profile["transform"][0]
        if int(res_tif * 1 / precision) != int(resolution * 1 / precision):
            cond = False
    return cond


def estimate_width_of_polygon(
    arr_polygon_perimeter, arr_polygon_area, nan_value=np.nan
):
    """
    Estimate the width of a polygon with the length and area of the polygon
    see also
    https://gis.stackexchange.com/questions/20279/calculating-average-width-of-polygon/

    Parameters
    ----------
    arr_polygon_perimeter: numpy.ndarray or pandas.Series
        1D array holding in each row the perimeter of each polygon
    arr_polygon_area: numpy.ndarray or pandas.Series
        1D array holding in each row the area of each polygon
    nan_value: float
        The value to fill in for nan_values

    Returns
    -------
    arr_est_polygon_width: numpy.ndarray or pandas.Series
        1D array holding in each row the estimated width

    Note
    -----

    1. The width is only estimated for polygons which approximate a cuboid
    2. The width is estimated by

    .. math::

        B_gr =  1/4 [A-√(B-C)]
            1/4 [P_{poly}-√(〖P_{poly}〗^2-16A_{poly} )]

    with

    - :math:`P_{poly}` = perimeter of polygon
    - :math:`A_{poly}` = area of polygon

    See Also
    --------
    check_cuboid_condition

    """
    condition = check_cuboid_condition(arr_polygon_perimeter, arr_polygon_area)

    arr_est_polygon_width = np.ones(condition.shape) * nan_value

    arr_est_polygon_width[condition] = (
        arr_polygon_perimeter[condition]
        - np.sqrt(
            (arr_polygon_perimeter[condition] ** 2) - (16 * arr_polygon_area[condition])
        )
    ) / 4

    return arr_est_polygon_width


def check_cuboid_condition(arr_polygon_perimeter, arr_polygon_area):
    """Check if a shape can be classified as a cuboid

    Parameters
    ----------
    arr_polygon_perimeter: numpy.ndarray or pandas.Series
        1D array holding in each row the perimeter of each polygon
    arr_polygon_area: numpy.ndarray or pandas.Series
        1D array holding in each row the area of each polygon

    Returns
    -------
    condition: numpy.ndarray or pandas.Series
        1D array holding True/False if cuboid

    See Also
    --------
    estimate_width_of_polygon

    """
    condition = arr_polygon_perimeter**2 > 16 * arr_polygon_area

    return condition


def execute_subprocess(cmd_args):
    """Run a command line tool

    Logs error with command output and error

    Parameters
    ----------
    cmd_args: list
        list with all argmunts that must be given to the console

    Returns
    -------
    Returns True if function call is successfull.
    """
    try:
        logger.debug(cmd_args)
        subprocess.run(cmd_args, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(e.stdout.decode())
        logger.error(e.stderr.decode())
        raise OSError(
            f"Could not run '{cmd_args}', returning '{e.stderr.decode()}'-error"
        )

    return True


@valid_input(dict={"vct_in": valid_vector})
def clip_vct_with_bounds(vct_in, vct_out, bounds, overwrite=False):
    """Clip a shapefile using a bounding box


    Parameters
    ----------
    vct_in: pathlib.Path
        File path of shapefile to be clipped.
    vct_out: pathlib.Path
        File path of the destination shapefile
    bounds: list
        list with xmin, ymin, xmax, ymax
    overwrite: bool, default False
        if True, overwrite existing file

    Note
    -----
    Uses and relies on ogr2ogr CLI
    """
    cond = True
    if not overwrite:
        if vct_out.exists():
            cond = False
    if cond:
        logger.info("Clipping %s..." % vct_in.name)
        cmd_args = [
            "ogr2ogr",
            "-spat",
            str(bounds[0]),
            str(bounds[1]),
            str(bounds[2]),
            str(bounds[3]),
        ]
        cmd_args += ["-skipfailures"]
        cmd_args += [str(vct_out), str(vct_in)]
        execute_subprocess(cmd_args)


@valid_input(dict={"valid_catchment": valid_polygonvector})
def define_extent_from_vct(
    vct_catchment, resolution, nodata, epsg, bounds=None, buffer=100
):
    """Read the extent of the catchment

    Parameters
    ----------
    vct_catchment: str or pathlib.Path
        File path of the vector shapefile
    bounds: list, default None
        if None, bounds are determined from
        The **first** entry is **x_left**, the **second** entry is **y_lower**,
        the **third** entry is **x_right** and the **fourth** entry is **y_upper**
        [x_left, y_lower, x_right, y_upper].
    resolution: int
        Spatial resolution
    epsg: int
        EPSG code should be a numeric value, see https://epsg.io/.
    Returns
    -------
    rp: RasterProperties see :class:`pywatemsedem.geo.rasterproperties.RasterProperties`

    """
    with fiona.open(vct_catchment) as c:
        # Get spatial extent of catchment.
        extent = c.bounds
        minmax = [
            round(extent[0]) - buffer,
            round(extent[1]) - buffer,
            round(extent[2]) + buffer,
            round(extent[3]) + buffer,
        ]

    if bounds is not None:
        for i in range(4):
            if i < 2:  # xmin en ymin
                rest = (minmax[i] - bounds[i]) % resolution
                if rest != 0:
                    minmax[i] = minmax[i] - rest
            else:  # xmax en ymax
                rest = (minmax[i] - bounds[i - 2]) % resolution
                if rest != 0:
                    minmax[i] = minmax[i] - rest + resolution

    rp = RasterProperties(minmax, resolution, nodata, epsg)

    return rp


def clean_up_tempfiles(temporary_file, file_format):
    """Clean up extra generated tempfiles

    This function can be used to clean-up extra files (for example auxilary files)
    generated during a write of raster or vector file.

    Parameters
    ----------
    temporary_file: pathlib.Path | str

    file_format: {"tiff","shp","rst","txt"}
            format of the temporary files
    """
    if type(temporary_file) is str:
        temporary_file = Path(temporary_file)
    elif type(temporary_file) is tempfile._TemporaryFileWrapper:
        temporary_file.close()
        temporary_file = Path(temporary_file.name)
    if file_format == "tiff":
        check_suffix = SUFFIXES_TIF
    elif file_format == "rst":
        check_suffix = SUFFIXES_RST
    elif file_format == "shp":
        check_suffix = SUFFIXES_SHP
    elif file_format == "txt":
        check_suffix = SUFFIXES_TXT
    elif file_format == "saga":
        check_suffix = SUFFIXES_SAGA
    else:
        msg = f"File format '{file_format}' not implemented, cannot execute."
        raise NotImplementedError(msg)
    for suffix in check_suffix:
        filename = temporary_file.with_suffix(suffix)
        if filename.exists():
            filename.unlink()


def generate_vct_mask_from_raster_mask(rst_catchment, vct_catchment, resolution):
    """
    Generate a catchment fileshape from a raster file

    Parameters
    ----------
    rst_catchment: str or pathlib.Path
        Input raster format of the catchment (can be any type that can be read by
        rasterio)

    vct_catchment: str or pathlib.Path
        output shapefile format of the catchment

    resolution: int
        resolution of the model run
    """
    condition = check_spatial_resolution_rst(rst_catchment, resolution)
    if not condition:
        msg = (
            f"Defined resolution '{resolution}' is not the same as resolution "
            f"catchment raster '{rst_catchment}'. Aborting run."
        )
        raise IOError(msg)
    # gdf_catchment = tiff_to_geopandas_df(rst_catchment, crs)
    raster_to_polygon(rst_catchment, vct_catchment)
    gdf_catchment = gpd.read_file(vct_catchment)
    gdf_catchment = process_mask_shape_from_raster_file(gdf_catchment)
    gdf_catchment.to_file(Path(vct_catchment))


def process_mask_shape_from_raster_file(gdf_catchment, catchment_value=1):
    """
    Process the geopandas shape format of the input raster

    Parameters
    ----------
    gdf_catchment: geopandas.GeoDataFrame
        dataframe holding the mask , possible in multiple polygons (rows)
    catchment_value: int, default 1
        value that is used to define catchment

    Returns
    -------
    gdf_catchment: geopandas.GeoDataFrame
        dissolved dataframe holding mask, in one polygon (row)
    """
    gdf_catchment = gdf_catchment[gdf_catchment["VALUE"] == catchment_value]
    gdf_catchment = gdf_catchment.dissolve(by="VALUE")

    return gdf_catchment


def mask_array_with_val(arr, mask, mask_val):
    """Masking array by a mask

    Parameters
    ---------
    arr: numpy.ndarray
        array of which values are masked
    mask: numpy.ndarray
        masking array with same dimensions as arr
    mask_val: float or int
            masking arr when mask is mask_val
    """
    arr_masked = np.ma.masked_where(mask == mask_val, arr)
    return arr_masked


def nearly_identical(geoms, p, threshold=0.75):
    """Identify nearly identical geometries

    Parameters
    ----------
    geoms: geopandas.GeoSeries
    p: shapely.Geometry

    Returns
    -------
    pandas.Series
        True/False
    """

    nearly = (geoms.intersection(p).area / p.area) > threshold
    # return index values where nearly is True
    return pd.Series(nearly.index[nearly])
