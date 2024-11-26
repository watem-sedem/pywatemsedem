import tempfile
import warnings
from pathlib import Path

import numpy as np

from pywatemsedem.grasstrips import (
    scale_cfactor_linear,
    scale_cfactor_with_grass_strips_width,
)

from .geo.utils import clean_up_tempfiles


def create_cfactor_degerick2015(
    rivers,
    infrastructure,
    composite_landuse,
    mask,
    vct_parcels=None,
    vct_grass_strips=None,
    cfactor_aggriculture=0.37,
    use_source_oriented_measures=False,
):
    """Creates the C-factor raster based on river, infrastructure and composite landuse.

    The C-factor is set to (in order)

    - 0 if the landuse is river or infrastructure.
    - scaled according to the width of the grass strips.
    - C-factor of the crop for parcels (any model possible).
    - 0.001 if the landuse is forest
    - 0.01 if the landuse is grass land
    - 0 if the landuse is pond
    - 0.01 if the landuse is grass strip (where not grass strip vector is defined)

    Left-over pixels are set to 0.37

    Parameters
    ----------
    rivers: numpy.ndarray
        River raster, all rivers must have a no-nodata or no-0-value.
    infrastructure: numpy.ndarray
        Infrastructure raster, all infrastructure pixels must have a no-nodata or
        no-0 value.
    composite_landuse: numpy.ndarray
        WaTEM/SEDEM composite landuse. (see :ref:`here <watemsedem:prcmap>`).
    mask: pywatemsedem.geo.rasters.AbstractRaster
        Mask
    vct_parcels: geopandas.GeoDataFrame, default None
        Dataframe holding C-factor values, columns:
        - *C_factor* (float)
    vct_grass_strips: geopandas.GeoDataFrame, default None
        Dataframe holding C-factor values, columns:
        - *C_factor* (float)
    cfactor_aggriculture: numpy.ndarray , default 0.37
        Default C-factor value for left-over pixels
    use_source_oriented_measures: bool
        True / False. In case True, vct_parcels should contain the column 'C_reduct'.

    Returns
    -------
    vct_grass_strips: geopandas.GeoDataFrame
        Grass strips vector added with C-factor.
    arr_cfactor: numpy.ndarray

    Notes
    -----
    1. If users input parcels and/or grass strips vectors, then they are responsible of
       defining 'C_factor' and/or grass strip 'width'. #TODO: optimize
    2. C-reduction based on source-oriented measures ('C_reduc') are only applied at
       the level of parcel polygons (see
       :func:`pywatemsedem.cfactor.reduce_cfactor_with_source_oriented_measures`).
    """
    # use to rasterize
    tiff_temp = Path(
        tempfile.NamedTemporaryFile(
            suffix=".tif", prefix="pywatemsedem", delete=False
        ).name
    )
    mask.write(tiff_temp, format="tiff")

    arr_cfactor = np.full(
        composite_landuse.arr.shape, composite_landuse.rp.nodata
    ).astype("float32")
    nodata = composite_landuse.rp.nodata

    # waterlopen
    if rivers is not None:
        temp = np.where(rivers.arr != rivers.rp.nodata, 0, rivers.rp.nodata)
        arr_cfactor = np.where(arr_cfactor == nodata, temp, arr_cfactor)

    # infrastructuur
    if infrastructure is not None:
        temp = np.where(
            np.isin(infrastructure.arr, np.array([-2, -7])), 0, infrastructure.arr
        )
        arr_cfactor = np.where(arr_cfactor == nodata, temp, arr_cfactor)

    # grass strips
    # TODO: optimize workflow
    if not vct_grass_strips.is_empty():
        res = composite_landuse.rp.resolution
        vct_grass_strips._geodata["C_factor"] = scale_cfactor_with_grass_strips_width(
            vct_grass_strips._geodata["width"], scale_cfactor_linear, resolution=res
        )
        # write calculated C-factor to shapefile -> needed for efficiency plots
        # vct_grass = grass.write()
        arr_grass_cfactor = vct_grass_strips.rasterize(
            tiff_temp, epsg=composite_landuse.rp.epsg, col="C_factor", gdal=True
        )
        arr_cfactor = np.where(arr_cfactor == nodata, arr_grass_cfactor, arr_cfactor)

    # parcels
    # TODO: optimize workflow
    if not vct_parcels.is_empty():
        if "C_crop" in vct_parcels.geodata.columns:
            vct_parcels.geodata["C_factor"] = vct_parcels.geodata["C_crop"]
        if "default_cfactor" in vct_parcels.geodata:
            msg = (
                f"Conversion to default C-factor is defined for a number of "
                f"records in parcels, converting C-factor to "
                f"'{cfactor_aggriculture}'."
            )
            warnings.warn(msg)
            cond = vct_parcels.geodata["default_cfactor"] == 1
            vct_parcels.geodata.loc[cond, "LANDUSE"] = -9999
            vct_parcels.geodata.loc[cond, "GWSCOD_H"] = 9999
            vct_parcels.geodata.loc[cond, "C_factor"] = cfactor_aggriculture
        if "C_factor" in vct_parcels.geodata.columns:
            vct_parcels.geodata[
                "C_factor"
            ] = reduce_cfactor_with_source_oriented_measures(
                vct_parcels.geodata["C_factor"],
                vct_parcels.geodata["C_reduct"],
                use_source_oriented_measures,
            )
            arr = vct_parcels.rasterize(
                tiff_temp, composite_landuse.rp.epsg, col="C_factor", gdal=True
            )
            arr_cfactor = np.where(
                arr_cfactor == nodata,
                arr,
                arr_cfactor,
            )
        else:
            msg = (
                "C_factor field not available in parcel vector, model will "
                "ignore the parcels for C-factors."
            )
            warnings.warn(msg)

    # other landuse
    if not composite_landuse.is_empty():
        # reclass landarr to C-factors
        temp = composite_landuse.arr.copy()
        temp = np.where(temp == -1, 0, temp)
        temp = np.where(temp == -2, 0, temp)
        temp = np.where(temp == -3, 0.001, temp)
        temp = np.where(temp == -4, 0.01, temp)
        temp = np.where(temp == -5, 0, temp)
        temp = np.where(temp == -6, 0.01, temp)
        temp = np.where(np.isin(temp, np.arange(1, 11, 1)), cfactor_aggriculture, temp)
        arr_cfactor = np.where(arr_cfactor == nodata, temp, arr_cfactor)

    # last posible pixels
    arr_mask = np.where(mask.arr, cfactor_aggriculture, 0)
    arr_cfactor = np.where(arr_cfactor == nodata, arr_mask, arr_cfactor)
    arr_cfactor = arr_cfactor.astype("float32")
    clean_up_tempfiles(tiff_temp, "tiff")

    return vct_grass_strips, arr_cfactor


def reduce_cfactor_with_source_oriented_measures(
    c_factor, c_reduction, use_source_oriented_measures
):
    """Reduce the C-factor with the amount defined in 'C_reduction' for every element
    in the vector. This formule is used to implement impact of source oriented measures
    on C-factor.

    Formula:

    .. math:

        C_{factor,reduced}=C_{factor}∗(1-C_{reduction})

    Parameters
    ----------
    c_factor: numpy.ndarray
        1D-array of C-factor values, vary between 0 and 1.
    c_reduction: numpy.ndarray
        1D array of reduction coefficients, vary between 0 and 1.
    use_source_oriented_measures: bool
        True / False. In case True, vct_parcels should contain the column 'C_reduction'.

    Returns
    -------
    c_factor: numpy.ndarray
        Reduced C-factors.
    """
    if (
        np.any(c_reduction > 1.0)
        | np.any(c_reduction < 0.0)
        | np.any(np.isnan(c_reduction))
    ):
        msg = "Values of c-reduction should be between 0 and 1. Cannot contain NaN."
        raise IOError(msg)
    if np.any(c_factor > 1.0) | np.any(c_factor < 0.0) | np.any(np.isnan(c_factor)):
        msg = "Values of c-factor should be between 0 and 1. Cannot contain NaN."
        raise IOError(msg)

    if use_source_oriented_measures:
        msg = (
            "Implementing source-oriented measures: reducing C-factor with "
            "value defined in '1 - C_reduction'."
        )
        warnings.warn(msg)
        c_factor = c_factor * (1 - c_reduction)

    return c_factor
