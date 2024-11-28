"""pywatemsedem grass strips processing functions"""
import logging
import tempfile
from pathlib import Path
from typing import Callable

import geopandas as gpd
import numpy as np
from scipy import signal

from pywatemsedem.defaults import PREFIX_TEMP
from pywatemsedem.geo.utils import (
    clean_up_tempfiles,
    estimate_width_of_polygon,
    saga_intersection,
    vct_to_rst_field,
)

# Add new kte scaling functions here
logger = logging.getLogger(__name__)


def _check_grass_strip_width(arr_width: np.array):
    """Check a number of conditions for the definition of grass strip widths array

    1. Grass strip widths (m) are rounded to their integer value.
    2. Grass strip widths (m) smaller than one are not allowed.

    Parameters
    ----------
    arr_width: numpy.ndarray
        Vector array with grass strips widths (m).

    Returns
    -------
    arr_width: numpy.ndarray
        Vector array with rounded grass strips widths (m).
    """

    if not np.issubdtype(arr_width.dtype, np.number):
        msg = (
            f"Grass strip widths array should be a numerical array, not"
            f" {arr_width.dtype}. Abort"
        )
        raise ValueError(msg)

    if np.any(np.isnan(arr_width)):
        msg = "Non defined grass strips widths (nan) are not allowed. Abort"
        raise ValueError(msg)

    # round to integer (m)
    arr_width = np.round(arr_width).astype(int)

    if np.any(arr_width < 1):
        arr_width[arr_width < 1] = 1
        msg = "Grass widths lower than one are observed, setting equal to one."
        logging.warning(msg)
    return arr_width


def scale_cfactor_linear(
    arr_width: np.ndarray,
    resolution: (int, float) = 20,
    upper_cfactor=0.37,
    lower_cfactor=0.01,
):
    """Scale function for ktc based on a lineair interpolation between the defined lower
    and upper boundary condtion, and the resolution.

    Parameters
    ----------
    arr_width: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_cfactor_with_grass_strip_width`
    resolution: int
        Spatial resolution of raster grid on which grass strips are projected.
    upper_cfactor: float, default 0.37
        Upper allowed C-factor.
    upper_cfactor: float, default 0.01
        Lower allowed C-factor.

    Returns
    -------
    arr_cfactor: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_cfactor_with_grass_strip_width`

    Notes
    -----
    The C-factor (:math:`C`) is weighted by the grass strips width (:math:`w`)
    and resolution (:math:`r`):

    .. math::

        C = 0.01*\\frac{w}{r}+0.37*\\frac{r-w}{r}

    Considering an lower and upper C-factor of 0.01 and 0.37, widths are capped to
    model resolution.

    References
    ----------
    Deproost, P., Renders, D., Van de Wauw, J., Van Ransbeeck, N., Verstraeten, G.,
    2018. Herkalibratie van WaTEM/SEDEM met het DHMV-II als hoogtemodel: eindrapport.
    Brussel.
    """
    arr_width = np.where(
        arr_width >= resolution,
        resolution,
        arr_width,
    )
    arr_cfactor = (lower_cfactor * (arr_width / resolution)) + (
        upper_cfactor * ((resolution - arr_width) / resolution)
    )

    return arr_cfactor


def scale_ktc_linear(
    arr_width: np.ndarray,
    resolution: (int, float) = 20,
    ktc_low: (int, float) = 3,
    ktc_high: (int, float) = 12,
):
    """Scale function for ktc based on a lineair interpolation between the defined lower
    and upper boundary condtion, and the resolution.

    Parameters
    ----------
    arr_width: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`
    resolution: int
        Spatial resolution of raster grid on which grass strips are projected.
    ktc_low: float
        The lower boundary to which scale the ktc value.
    ktc_high: float
        The upper boundary to which scale the ktc value.

    Returns
    -------
    arr_ktc: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`
    arr_ste: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`

    Notes
    -----
    1. ktc values for grass strips are determined by a lower and upper boundary of ktc.
    The weighting is defined by the width of the grass strip compared to the resolution
    of the model. This approach is defined in Deproost et al. (2018).

    2. The estimated STE values are determined by using the formula of Verstraete et
    al. (2006):

    .. math::

        STE (percent) = [1 -  * ktc_{var}/ktc_{high}]*100

    with:

        :math:`ktc_{var}` (1/m): the ktc values for the grass strips;

    References
    ----------
    Deproost, P., Renders, D., Van de Wauw, J., Van Ransbeeck, N., Verstraeten, G.,
    2018. Herkalibratie van WaTEM/SEDEM met het DHMV-II als hoogtemodel: eindrapport.
    Brussel.

    Verstraeten, G., Poesen, J., Gillijns, K., Govers, G., 2006. The use of riparian
    vegetated filter strips to reduce river sediment loads: an overestimated control
    measure? Hydrol. Process. 20, 4259–4267. https://doi.org/10.1002/hyp.6155

    """
    if np.any(arr_width > resolution):
        msg = (
            f"Grass strips larger than the resolution {resolution} are not allowed "
            f"for linear scaling of ktc value grass strips, setting to {resolution} m."
        )
        arr_width[arr_width > resolution] = resolution
        logger.warning(msg)

    w1 = arr_width / resolution
    w2 = 1 - arr_width / resolution
    arr_ktc = ktc_low * w1 + ktc_high * w2
    arr_ste = 1 - arr_ktc / ktc_high

    return arr_ktc, arr_ste


def scale_ktc_zhang(
    arr_width: np.ndarray,
    ktc_high: (int, float) = 12,
    k: (int, float) = 90.9,
    b: (int, float) = 0.446,
):
    """Scale function for ktc based on a Zhang et al. (2010).

    Parameters
    ----------
    arr_width: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`
    ktc_high: float
        The upper boundary to which scale the ktc value.
    k: float
        Maximum sediment trappping efficiency (K in Zhang et al., 2010)
    b: float
        Slope coefficient (see Zhang et al., 2010).

    Returns
    -------
    arr_ktc: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`
    arr_ste: numpy.ndarray
        See :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`

    Notes
    -----
    1. The ktc valeus for grass strips are determined by using emperical sediment
    trapping efficiency (STE) values in the equation of Verstraete et al. (2006):

    .. math::

        ktc_{var} = (ktc_{high}/100)*(1-STE/100)


    with:

        :math:`ktc_{var}` (1/m): the ktc values for the grass strips;

    The STE can be determined by using the emperical findings of Zhang et al. (2010):

    .. math::s


        STE (percent) = K * (1-e^{-b*w_{gs}})


    with:

        :math:`K` = 90.9;

        :math:`b` = 0.446;

        :math:`gs` (m) = width grass strips

    References
    ----------
    Zhang, X., Liu, X., Zhang, M., Dahlgren, R.A., Eitzel, M., 2010. A Review of
    Vegetated Buffers and a Meta-analysis of Their Mitigation Efficacy in Reducing
    Nonpoint Source Pollution. J. Environ. Qual. 39, 76–84.
    https://doi.org/10.2134/jeq2008.0496
    """
    arr_ste = k * (1 - np.exp(-b * arr_width)) / 100  # in decimals
    arr_ktc = (ktc_high) * (1 - arr_ste)

    return arr_ktc, arr_ste


# Add new kte scaling functions here
KTC_SCALING_FUNCTIONS = [scale_ktc_linear, scale_ktc_zhang]
CFACTOR_SCALING_FUNCTIONS = [scale_cfactor_linear]


def scale_ktc_with_grass_strip_width(
    arr_width: np.ndarray, scaling_function: Callable, **parameters
):
    """Scale ktc value for grass stripts according to the width of the grass strip.

    The ktc parameters (which determines the amount of sediment which is routed
    downstream) for a grass strip varies as a function of the width of the grass strip.

    Parameters
    ----------
    arr_width: numpy.ndarray
        Vector array with grass strips widths (m)
    scaling_function: callable
        Scaling function
    parameters:
        Scaling function parameters as required by the ``scaling function``.

    Returns
    -------
    arr_ktc: numpy.ndarray
        Vector array with ktc values for grass strips (1/m)
    arr_ste: numpy.ndarray
        Vector array of sediment trapping efficiency of grass strips
        (under the assumption of a flat plane, see Notes)

    Notes
    -----
    The theoretical 'sediment trapping efficiency' (STE) is interpreted as the
    trapping efficiency of a grass strips on a homogenous lineair slope. In other
    words, the slope plane can be defined as a flat plane (as in: can be defined in
    by two dimensions). This is also sometimes referred to as a linear slope (see
    Verstraete et al. (2006))

    References
    ----------
    Verstraeten, G., Poesen, J., Gillijns, K., Govers, G., 2006. The use of riparian
    vegetated filter strips to reduce river sediment loads: an overestimated control
    measure? Hydrol. Process. 20, 4259–4267. https://doi.org/10.1002/hyp.6155
    """
    if scaling_function not in KTC_SCALING_FUNCTIONS:
        msg = f"Ktc scale function {scaling_function} not implemented in pywatemsedem."
        raise IOError(msg)

    arr_width = _check_grass_strip_width(arr_width)

    arr_ktc, arr_ste = scaling_function(arr_width, **parameters)

    return arr_ktc, arr_ste


def estimate_ste(simulated_sediin, simulated_sediout):
    """Compute the estimated :math:`\\hat{STE}` based on simulated sediment output/input

    This function computes the sediment trapping efficiency based on the
    model-simulated incoming and outgoing sediment for each grass strip.

    Parameters
    ----------
    simulated_sediin: numpy.ndarray
        Simulated incoming sediment per grass strip
    simulated_sediout: numpy.ndarray
        Simulated outgoing sediment per grass strip

    Returns
    -------
    float
        Estimated STE (STEe)

    Notes
    -----
    1. The estimated :math:`\\hat{STE}`  is referred to with a hat to make a distinction
       between the theoretical STE defined in
       :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`
    2. Note that the STE can be negative in case there is more erosie produced in the
       grass strip then there is incoming into the grass strip.
    """
    return (1 - simulated_sediout / simulated_sediin) * 100


def scale_cfactor_with_grass_strips_width(
    arr_width: np.ndarray, scaling_function_cfactor: Callable, **parameters
):
    """Scale C-factor value for grass strips according to the width of the grass strip.

    Parameters
    ----------
    arr_width: numpy.ndarray
        Vector array with grass strips widths (m)
    scaling_function_cfactor: callable
        Scaling function
    parameters:
        Scaling function parameters as required by the ``scaling function``.

    Returns
    -------
    arr_cfactor: numpy.ndarray
        Vector array with C-factor values for grass strips (-)
    """
    if scaling_function_cfactor not in CFACTOR_SCALING_FUNCTIONS:
        msg = (
            f"Ktc scale function {scaling_function_cfactor} not implemented in "
            f"pywatemsedem."
        )
        raise IOError(msg)

    arr_width = _check_grass_strip_width(arr_width)

    arr_cfactor = scaling_function_cfactor(arr_width, **parameters)

    return arr_cfactor


def get_width_grass_strips(
    arr_width_gras_strips, arr_gras_polygon_perimeter, arr_gras_polygon_area, resolution
):
    """Get the width of the gras strips for gras strips with width being equal
    to np.nan 'unknown' or zero.

    If width cannot be estimated, estimate is based on polygon shape.

    Parameters
    ----------
    arr_width_gras_strips: numpy.ndarray or pandas.Series
        1D array holding in each row width of the gras strip.
        note: this can all be zeros or np.nan
    arr_gras_polygon_perimeter: numpy.ndarray or pandas.Series
        1D array holding in each row the perimeter of each gras polygon
    arr_gras_polygon_area: numpy.ndarray or pandas.Series
        1D array holding in each row the area of each gras polygon
    resolution: int

    Returns
    -------
    arr_width_gras_strips: numpy.ndarray or pandas.Series
        1D array holding in each row (estimated) width of the gras strip
    """
    arr_est_polygon_width = estimate_width_of_polygon(
        arr_gras_polygon_perimeter, arr_gras_polygon_area, nan_value=resolution
    )
    # fill in zeros with estimates
    arr_width_gras_strips = np.where(
        arr_width_gras_strips == 0,
        arr_est_polygon_width,
        arr_width_gras_strips,
    )
    # fill in np.nan with estimates
    arr_width_gras_strips = np.where(
        np.isnan(arr_width_gras_strips), arr_est_polygon_width, arr_width_gras_strips
    )

    return arr_width_gras_strips


def expand_grass_strips_with_triggers(
    arr_grass_strips: np.ndarray,
    arr_triggers: np.ndarray,
    arr_parcels: np.ndarray = None,
    nodata=None,
    mode=1,
):
    """Expand grass strips based on neighbouring trigger pixels.

    This algorithm expands grass strips with one neighbouring pixel when a neighbouring
    is a trigger pixel. The expansion can be bound within one unique parcel (optional).

    Parameters
    ----------
    arr_grass_strips: numpy.ndarray
        Array with grass strips. Every contiguous grass strips needs to be identified
        with an unique id as array value.
    arr_triggers: numpy.ndarray
        Binary array with 1's when a pixel is a trigger. Nodata values are allowed.
    arr_parcels: numpy.ndarray, default None
        See :func:`pywatemsedem.grasstrips.core_expand_grass_strips_with_triggers`
    nodata: float, default None
        See :func:`pywatemsedem.grasstrips.core_expand_grass_strips_with_triggers`
    mode: int, default 1
        See :func:`pywatemsedem.grasstrips.core_expand_grass_strips_with_triggers`.
        Only for computing neighbours grass strips.

    Returns
    -------
    arr_grass_strips: np.ndarray
        See :func:`pywatemsedem.grassstrips.core_expand_grass_strips_with_triggers`

    Examples
    --------
    >>> # triggers (for instance river, road)
    >>> arr_triggers = np.array([[1, 0, 0, 0],
    >>>                        [0, 1, 0, 0],
    >>>                        [0, 0, 1, 0],
    >>>                        [0, 0, 0, 1]])
    >>> # parcel ids
    >>> arr_parcels_id = np.array([[0, 3, 3, 3],
    >>>                            [1, 0, 2, 2],
    >>>                            [1, 1, 0, 2],
    >>>                            [1, 1, 1, 0]])
    >>> # input gras id's
    >>> arr_grass_strips = np.array([[0, 0, 0, 0],
    >>>                            [0, 0, 0, 0],
    >>>                            [0, 0, 0, 1],
    >>>                            [0, 0, 0, 1]])
    >>> # execute
    >>> arr_out = expand_grass_strips_with_triggers(
    >>>    arr_grass_strips, arr_triggers, arr_parcels_id)

    Notes
    -----
    1. For algorithm description, see
    :func:`pywatemsedem.grasstrips.core_expand_grass_strips_with_triggers`

    For visual example, see image below:

    .. image:: /_static/png/expand_grass_strips_at_infr_parcel_boundary.png
      :width: 600


    2. All input arrays should have the same nodata value in their raster.
    """
    if arr_triggers.shape != arr_grass_strips.shape:
        msg = (
            f"Input grass strips array {arr_grass_strips.shape} has a different "
            f"size than the input triggers array {arr_triggers.shape}."
        )
        raise IOError(msg)

    if set(arr_triggers.ravel()) != {0, 1}:
        msg = "Input trigger can only contain 0's and 1's (and no data) values."
        raise ValueError(msg)

    # remove grass strips from triggers
    arr_grass_strips_nt = arr_grass_strips.copy()
    arr_grass_strips_nt[arr_triggers == 1] = 0

    # add boundaries to cope with boundary condition
    arr_grass_strips = add_boundary_rows_cols_to_arr(arr_grass_strips)
    arr_grass_strips_nt = add_boundary_rows_cols_to_arr(arr_grass_strips_nt)
    arr_triggers = add_boundary_rows_cols_to_arr(arr_triggers)
    if arr_parcels is not None:
        arr_parcels = add_boundary_rows_cols_to_arr(arr_parcels)

    # compute for every pixel how many pixels are trigger pixels
    arr_triggers_neighbours = compute_number_of_non_zero_neighbours(
        arr_triggers, nodata=nodata
    )
    # compute for every pixel how many pixels are gras strip pixels
    arr_grass_strips_neighbours = compute_number_of_non_zero_neighbours(
        arr_grass_strips_nt, nodata=nodata, mode=mode
    )

    # run expansion algorithm
    arr_grass_strips = core_expand_grass_strips_with_triggers(
        arr_grass_strips,
        arr_grass_strips_neighbours,
        arr_triggers_neighbours,
        arr_parcels,
        nodata=nodata,
    )

    return arr_grass_strips[1:-1, 1:-1]


def compute_number_of_non_zero_neighbours(arr, nodata=None, mode=1):
    """Compute number of non-zero neighbour (eight) elemnts for every
    array element.

    This algorithm computes how many neighbours of a pixel are not equal to zero (and
    not equal to nodata.)

    Parameters
    ----------
    arr: numpy.ndarray
        Input array with valid values: (nodata, 0, >0)
        Nodata values are considered as 0-values. >0 values are considerd as 1-values
    nodata: float, default None
        Values to ignore, if equal to None this is not considered.
    mode: int
        Mode of expansion:

        1: Consider ordinal + cardinal direction.
        2: Cardinal direction.
        3: Ordinal direction.

    Returns
    -------
    arr_out: numpy.ndarray
        Array with for each element the number of non-zero neighbours.

    Notes
    -----
    1. Nodata values are not considered!
    2. Boundaries are set to zero.
    3. Grass strips within trigger pixels are not considered.
    """
    arr_out = arr.copy()
    if nodata is not None:
        arr_out[arr_out == nodata] = 0
    arr_out = arr_out.astype(bool)

    if mode == 1:
        weights = np.ones((3, 3))
    elif mode == 2:
        weights = np.array([[1, 0, 1], [0, 1, 0], [1, 0, 1]])
    elif mode == 3:
        weights = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])

    else:
        msg = (
            f"Mode for searching neighbours {mode} not known, please select 1 "
            f"(cardinal + ordinal), 2 (ordinal direction) or 3 (cardinal direction)."
        )
        raise KeyError(msg)

    arr_out[1:-1, 1:-1] = signal.convolve2d(arr_out, weights, "valid")

    # boundaries
    arr_out[0, :] = 0
    arr_out[-1, :] = 0
    arr_out[:, 0] = 0
    arr_out[:, -1] = 0

    arr_out[(arr != 0) & (arr != nodata)] = 0

    return arr_out


def add_boundary_rows_cols_to_arr(arr):
    """Add boundary rows and columns to an array, set values to zero.

    Parameters
    ----------
    arr: numpy.ndarray

    Returns
    -------
    numpy.ndarray
        With two rows added to the top and bottom, and two columns added to the left
        and right
    """
    shape = arr.shape
    _arr = np.zeros((shape[0] + 2, shape[1] + 2))
    _arr[1:-1, 1:-1] = arr

    return _arr


def core_expand_grass_strips_with_triggers(
    arr_grass_strips,
    arr_grass_strips_neighbours,
    arr_triggers_neighbours,
    arr_parcels=None,
    nodata=None,
):
    """Grass strip expansion algorithm based on raster inputs.

    The grass strips expansion algorithm executes following steps:

    1. Expand the grass strips with one pixel. This implies that adjacent (ordinal
       and/or cardinal directions, depending on mode, see
       :func:`pywatemsedem.grasstrips.compute_number_of_non_zero_neighbours`) pixels to
       a grass strip pixel are classified as grass strip pixels.

    2. The added grass strip pixels can only be retained if following rules are
       satisfied:

        - The added grass strip pixels is in the direct vicinity of (one of 8
          neighbours) a trigger pixel (river, infrastructure pixel).
        - (optional) The added grass strip pixels can only be withheld when it belongs
          to a parcel to which the original grass strip was part of.

    Parameters
    ----------
    arr_grass_strips: numpy.ndarray
        Array with unique id's per grass strips
    arr_grass_strips_neighbours:
        See :func:`pywatemsedem.grasstrips.compute_number_of_non_zero_neighbours` applied
        on grass strips array.
    arr_triggers_neighbours: nump.ndarray
        See :func:`pywatemsedem.grasstrips.compute_number_of_non_zero_neighbours` applied
        on triggers array.
    arr_parcels: nump.ndarray, default None
        Parcel ids raster. Pixel belonging to one parcel share the same unique id. The
        value zero indicates that no parcel is present. If None, the expansion is not
        limited to the boundaries of a parcel.
    nodata: float, default None
        Nodata value of all rasters

    Returns
    -------
    arr_grass_strips: numpy.ndarray
        Grass strips array with grass strips expanded at the
        trigger boundary edge cases.

    Notes
    -----
    1. This algorithm is not able to make a distinction between two separate grass
       strip in one parcel.

    2. For the expansion of the grass strips, the source grass pixels overlapping with
       the triggers are not considered. This implies that if a specific gras strip
       completely overlaps with triggers, no expansion will be done.
    """
    for id_grass_strip in np.unique(arr_grass_strips):

        if (id_grass_strip != 0) & (id_grass_strip != nodata):

            if arr_parcels is None:
                cond = (arr_grass_strips_neighbours > 0) & (arr_triggers_neighbours > 0)
                arr_grass_strips[cond] = id_grass_strip
            else:
                un_parcels_id = np.unique(
                    arr_parcels[(arr_grass_strips == id_grass_strip)]
                )
                un_parcels_id = un_parcels_id[un_parcels_id > 0]

                for parcel_id in un_parcels_id:
                    cond = (
                        (arr_parcels == parcel_id)
                        & (arr_grass_strips_neighbours > 0)
                        & (arr_triggers_neighbours > 0)
                    )
                    arr_grass_strips[cond] = id_grass_strip

    return arr_grass_strips


def process_grass_strips(
    arr_grass_strips_ids,
    arr_river,
    arr_infr,
    nodata,
    arr_parcels=None,
    expand_grass_strips=False,
):
    """Create grass strips raster for WaTEM/SEDEM

    This function create the grass strips raster that is used as input creating the
    composite WaTEM/SEDEM parcels raster (see :ref:`here <watemsedem:prcmap>`). The
    output of this function provides a raster with -6-values for grass strip pixels.

    Parameters
    ----------
    arr_grass_id: numpy.ndarray
        Grass strips id's-raster. Pixel belonging to one grass strip share the same
        unique id. Other values should be have nodata-value described in the parameter
        profile.
    arr_river: numpy.ndarray
        River raster. River pixels should have the value differing from 0 or nodata
        (defined in profile).
    arr_infr: numpy.ndarray
        Infrastructure raster. Infrastructure pixels should have the value differing
        from 0 or nodata (defined in profile).
    arr_parcels: numpy.ndarray, default None
        Parcel ids raster. Pixel belonging to one parcel share the same unique id. The
        value zero indicates that no parcel is present. If None, the expansion is not
        limited to the boundaries of a parcel.
    nodata: int
        Nodata value
    expand_grass_strips: bool, default False
        Use expand grass strips algorithm with rivers as triggers, see
         :func:`pywatemsedem.grasstrips.expand_grass_strips_with_triggers`

    Returns
    -------
    arr_grass_strips_ids: numpy.ndarray
        Expanded grass strips id's-raster.
    arr_grass: numpy.ndarray
        -6-value-raster of grass strips id's-raster, formatted according to composite
         WaTEM/SEDEM parcels raster (see :ref:`here <watemsedem:prcmap>`).

    Notes
    -----
    All the input rasters must have the same nodata-value.
    """
    if expand_grass_strips:
        arr_river[(arr_river == nodata)] = 0
        arr_infr[(arr_infr == nodata)] = 0
        arr_triggers = arr_infr + arr_river
        arr_triggers[(arr_triggers != 0)] = 1
        # arr_gras[arr_gras==profile["nodata"]] = 0

        arr_grass_strips_ids = expand_grass_strips_with_triggers(
            arr_grass_strips_ids,
            arr_triggers,
            arr_parcels=arr_parcels,
            nodata=nodata,
            mode=1,
        )
    return arr_grass_strips_ids


def get_neighbour_grass_strips_ids_array(
    vct_grass_strips, rst_params, width_polygon=20
):
    gdf = gpd.read_file(vct_grass_strips)
    gdf["buffer"] = gdf.buffer(width_polygon)
    gdf = gdf[["NR", "buffer"]]
    gdf.rename(columns={"buffer": "geometry"}, inplace=True)
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry")
    gdf.to_file(vct_grass_strips.parent / (vct_grass_strips.stem + "_buffer" + ".shp"))
    rst_out = "neighbour_grass_strips_ids_array.tiff"
    vct_to_rst_field(
        vct_grass_strips, Path(rst_out), rst_params, "NR", alltouched=True, dtype=None
    )


def extract_grass_strips_from_parcels(vct_parcels, year, resmap=Path.cwd(), tag=""):
    """Extract grass buffers from parcels using the Thinnes criterium

    Extract grass buffers from parcels using the Thinnes
    criterium (>0.3) of a given year.

    ! EXPERIMENTAL - NOT IN USE YET !

    Parameters
    ----------
    year : int
        Year for which to extract the grass buffers.
    """
    grass_strips = resmap / f"graspercelen_{year}_{tag}.shp"
    d = {}

    try:
        gdf = gpd.read_file(vct_parcels)
    except Exception:
        msg = f"could not open {vct_parcels}"
        raise IOError(msg)
    else:
        gdf = gdf.loc[gdf["Grasbuffer"] == 1]
        gdf["opp"] = gdf.area
        gdf["perimeter"] = gdf.length

        gdf = gdf.loc[gdf.length**2 >= 16 * gdf.area]
        gdf["width"] = (gdf.length - np.sqrt((gdf.length**2) - (16 * gdf.area))) / 4

        gdf["Aspect"] = (gdf["width"] ** 2) / gdf.area
        gdf["Thinnes"] = 4 * np.pi * gdf.area / (gdf.length**2)
        gdf = gdf.loc[gdf["Thinnes"] < 0.5]
        gdf = gdf.loc[gdf["width"] < 25]
        gdf = gdf.loc[gdf["Aspect"] < 0.25]
        if not gdf.empty:
            d["gras"] = grass_strips
            gdf.to_file(grass_strips)
        vct_grass_strips_parcels = d

    return vct_grass_strips_parcels


def create_grass_strips_from_line_string(
    line_string, polygons=None, width=20, width_polygon=20
):
    """Add bank grass strips

    Adds bank grass strips with a standard length of 20m, along input LineStrings. If
    required, clip by polygons.

    Parameters
    ----------
    line_string: geopandas.GeoDataFrame
        Geopandas dataframe with LineString
    polygons: geopandas.GeoDataFrame, default None
        Geopandas dataframe with Polygon
    width: int, optional, default 20
        Width (m) of the bank grass strip stored in the attribute table.
    width_polygon: int, optional, default 20
        width (m) of the bank grass strip polygon

    Returns
    -------
    grass_strips: geopandas.GeoDataFrame

        - *width* (float): width of grass strips
        - *scale_ktc* (float): scale ktc, see
          :func:`pywatemsedem.grassttips.scale_ktc_with_grass_strip_width`


    Notes
    -----
    The `width` is the estimated true width of the grass strip, whereas the
    `width polygon` the used width is for mapping the shape to a raster. Typically,
    this `width polygon` is set to the resolution to ensure all LineString-surrounding
    pixels are mapped as grass strips. Note that the `width polygon` is not the
    estimated true width, it is a mapping (shape => raster) width.
    """

    line_string["buffer"] = line_string.buffer(width_polygon)
    grass_strips = line_string.drop(columns="geometry")
    grass_strips["width"] = width
    grass_strips["source"] = "bankgrassstrip"
    grass_strips["scale_ktc"] = 1
    grass_strips.rename(columns={"buffer": "geometry"}, inplace=True)
    grass_strips = gpd.GeoDataFrame(grass_strips, geometry="geometry")

    # intersect over years
    # if no intersection with parcels: assign same bank grass strip for every
    # year
    if polygons is not None:
        tmp_bankgrasstrips = tempfile.NamedTemporaryFile(
            prefix=PREFIX_TEMP, suffix=".shp"
        ).name
        grass_strips.to_file(tmp_bankgrasstrips)
        tmp_polygons = tempfile.NamedTemporaryFile(
            prefix=PREFIX_TEMP, suffix=".shp"
        ).name
        polygons.to_file(tmp_polygons)
        tmp_bankstrips_polygons = tempfile.NamedTemporaryFile(
            prefix=PREFIX_TEMP, suffix=".shp"
        ).name
        saga_intersection(
            tmp_bankgrasstrips,
            tmp_polygons,
            tmp_bankstrips_polygons,
        )
        grass_strips = gpd.read_file(tmp_bankstrips_polygons)
        # add dissolve of grass strips here
        grass_strips = grass_strips.dissolve("NR")
        grass_strips["width"] = width
        grass_strips["scale_ktc"] = 1
        clean_up_tempfiles(tmp_bankgrasstrips, "shp")
        clean_up_tempfiles(tmp_polygons, "shp")
        clean_up_tempfiles(tmp_bankstrips_polygons, "shp")

    return grass_strips.reset_index()[["width", "scale_ktc", "geometry"]]
