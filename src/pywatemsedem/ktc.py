import numpy as np

from pywatemsedem.grasstrips import scale_ktc_with_grass_strip_width, scale_ktc_zhang


def create_ktc_cnws(
    landuse_parcels,
    cfactor,
    mask,
    ktc_low,
    ktc_high,
    ktc_limit,
    sfolder,
    grass=None,
    correction_width=True,
):
    """Create KTC map for a given year, season.

    Parameters
    ----------
    # TODO
    """
    rst_mask = sfolder.scenario_folder / "mask.rst"
    mask.write(rst_mask)

    if cfactor is None:
        msg = "Unable to create KTC map, C-factor map is not known"
        raise FileNotFoundError(msg)
    if landuse_parcels is None:
        msg = "Unable to create KTC map, Prc map is not known"
        raise FileNotFoundError(msg)

    # reclass based on C-factor
    arr_ktc = np.where(cfactor <= ktc_limit, ktc_low, ktc_high)

    # give certain landuse classes an extremely high ktc-value
    arr_ktc = np.where(np.isin(landuse_parcels.arr, [-2, -1, -5]), 9999, arr_ktc)

    # set KTC outside modeldomain to zero
    # KTC_arr = np.where(self.catchm.binarr == 1, KTC_arr, 0)

    if correction_width is not None and grass is not None:

        grass._geodata = scale_ktc_gdf_grass_strips(
            grass.geodata,
            ktc_low,
            ktc_high,
        )
        arr_grass = grass.rasterize(
            rst_mask, landuse_parcels.rp.epsg, col="KTC", gdal=True
        )
        arr_ktc = np.where(
            np.logical_and(landuse_parcels.arr == -6, arr_grass != mask.rp.nodata),
            arr_grass,
            arr_ktc,
        )
        arr_ktc = np.where(
            np.logical_and(landuse_parcels.arr == -6, arr_grass == mask.rp.nodata),
            ktc_low,
            arr_ktc,
        )
    else:
        arr_ktc = np.where(landuse_parcels.arr == -6, ktc_low, arr_ktc)

    return arr_ktc, grass


def scale_ktc_gdf_grass_strips(gdf_grass_strips, ktc_low, ktc_high):
    """Scale the ktc values for grass strips in the grass strips dataframe

    Parameters
    ----------
    gdf_grass_strips: geopandas.GeoDataFrame
        Grass strips geodataframe, 'width' and 'scale_ktc' should be present as
        columns.
    ktc_low: float
    ktc_high: float
        See :func:`pywatemsedem.grasstrips.scale_ktc_linear` and
        :func:`pywatemsedem.grasstrips.scale_ktc_zhang`.

    Returns
    -------
    gdf_grass_strips: geopandas.GeoDataFrame
        Updated with the KTC value and the linear sediment trapping efficiency
        (STE_linear).
        For definition STE_linear,
        :func:`pywatemsedem.grasstrips.scale_ktc_with_grass_strip_width`.

    Notes
    -----
    Whether the kTC is scaled for the grass strips depends on the grass strip
    attribute "scale_ktc". If it is not scaled, the ktc_low-value is assigned.
    """
    if ("width" not in gdf_grass_strips.columns) or (
        "scale_ktc" not in gdf_grass_strips.columns
    ):
        msg = "Columns 'BREEDTE' and 'scale_ktc' should be in grass strips dataframe"
        return KeyError(msg)

    arr_ktc_grass, arr_ste = scale_ktc_with_grass_strip_width(
        gdf_grass_strips["width"].values,
        scale_ktc_zhang,
        ktc_high=ktc_high,
    )

    try:
        arr_scale_mask = np.array(gdf_grass_strips["scale_ktc"], dtype=bool)
    except TypeError:
        msg = (
            "Type of 'scale_ktc' column cannot be converted to boolean. Cannot "
            "mask 'KTC' column."
        )
        raise TypeError(msg)

    arr_ktc_grass[~arr_scale_mask] = ktc_low
    arr_ste[~arr_scale_mask] = np.nan

    gdf_grass_strips["KTC"] = arr_ktc_grass
    gdf_grass_strips["STE_linear"] = arr_ste

    return gdf_grass_strips
