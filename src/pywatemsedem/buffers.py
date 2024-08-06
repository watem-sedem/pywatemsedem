import logging

import numpy as np

logger = logging.getLogger(__name__)


def process_buffer_outlets(gdf_outlets, gdf_buffer):
    """Map user-defined outlets to buffers.

    This function maps outlets to buffer id's based on the overlap between the outlet
    definition and the buffer polygon definition.

    #TODO: write test function

    Parameters
    ----------
    gdf_outlets: gpd.GeoDataFrame
        GeoDataFrame with a geometry definition.
    gdf_buffer: gpd.GeoDataFrame
        Holding buffer id's and geometry

    Returns
    -------
    gdf_outlets: gpd.GeoDataFrame
        Updated outlets with buf id assigedn
    """
    gdf_outlets["BUF_ID"] = 0
    # 1. per buffer kijken welke outlets er in liggen en het
    # buf_id toekennen aan deze outlet
    for b_id, geom in gdf_buffer[["BUF_ID", "geometry"]]:
        gdf_outlets["test"] = gdf_outlets.within(geom)
        mask = gdf_outlets.loc[gdf_outlets["test"]]
        if not mask.empty:
            msg = f"multiple buffer outlets present in buffer" f"with id {b_id}."
            msg += " only one, random is outlet chosen!"
            logger.warning(msg)
            gdf_outlets.loc[mask.index[0], "BUF_ID"] = b_id
        elif mask.empty:
            msg = f"no buffer outlet defined for buffer with id " f"{b_id}."
            logger.warning(msg)
        else:
            gdf_outlets.loc[mask.index[0], "BUF_ID"] = b_id

    return gdf_outlets


def filter_outlets_in_arr_extension_id(gdf, arr, arr_dtm, arr_outlet=None):
    """Map buffer outlet on extension id raster

    This function filters outlet id's to single outlet id, for every buffer. The
    function returns an array with single entries for every buffer id and
    multiple entries for every buffer extension id.

    The algorithm takes a single pixel that

    - corresponds to the pixel defined in arr_outlet (use-defined).

    OR

    - corresponds to the minimum dtm value in the extension of the buffer.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
        Holding id's (column: 'buf_id' (int)), all id's should be present in arr and
        vice versa.
    arr: numpy.ndarray
        Array with buffer outlet (<16 385) and extension id's (16 385>=). This array
        can hold multiple entries for buffer outlet. All outlet id's should be present
        in gdf
    arr_dtm: numpy.ndarray
        DTM array, should have dimension of arr
    arr_outlet: numpy.ndarray
        Holds number of forced outlets, should have dimension of arr.

    Returns
    -------
    arr: numpy.ndarray
        Array with single entries for every buffer id and multiple entries for every
        buffer extension id.
    """
    un_outlets = np.unique(arr_outlet) if arr_outlet is None else []

    for row in gdf.itertuples():
        if row.buf_id in un_outlets:
            outlet_loc = arr_dtm[np.where(arr_outlet == row.buf_id)]
        else:
            outlet_loc = arr_dtm[arr == row.buf_exid].min()
        arr[(arr_dtm == outlet_loc) & (arr == row.buf_exid)] = row.buf_id
    return arr


def process_buffers_in_river(gdf, arr, arr_river, nodata):
    """This functions filters buffers from the buffer raster that overlap with a
    river

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
        Geopandas representation of arr, in buf_exid.
    arr: numpy.ndarray
        Array with buffer outlet (<16 385) and extension id's (16 385>=). This array
        can hold multiple entries for buffer outlet. All outlet id's should be present
        in gdf.
    arr_river: numpy.ndarray
        River raster, should be -1 and nodata
    nodata: float
        Nodata value in arr_river.

    Returns
    -------
    gdf: geopandas.GeoDataFrame
        Filtered
    arr: numpy.ndarray
        Filtered

    """
    # remove buffer pixels that coincide with river pixels
    arr = np.where(arr_river == -1, nodata, arr).astype("int16")
    # remove buffers that are not present in raster
    cond = np.isin(gdf["buf_exid"], np.unique(arr))
    gdf = gdf.loc[cond]

    return arr, gdf
