from dataclasses import dataclass

import numpy as np


@dataclass
class ParcelsLanduse:
    """Class to generate parcels land-use raster.

    This parcels land-use raster is used as raster input for WaTEM/SEDEM pywatemsedem.

    Parameters
    ----------
    landuse_core: numpy.ndarray
        Core landuse raster
    rivers: numpy.ndarray
        River raster (-1)
    water: numpy.ndarray
        Water raster (-3)
    infrastructure: numpy.ndarray
        Infrastructure (-2)
    mask: numpy.ndarray
        Mask array ???
    landuse_parcels: numpy.ndarray, default None
        Landuse parcels (-1, -2, -3, -4, -5, -6)
    parcels: numpy.ndarray, default None
        Pacels (>0)
    grass_strips: numpy.ndarray, default None
        Grass (-6)
    """

    landuse_core: np.ndarray
    river: np.ndarray
    water: np.ndarray
    infrastructure: np.ndarray
    mask: np.ndarray
    nodata: float
    landuse_parcels: np.ndarray = None
    parcels: np.ndarray = None
    grass_strips: np.ndarray = None

    def create_parcels_landuse_raster(self, scheme="Degerickx2015_adjusted"):
        """Create parcels landuse raster with a defined scheme.

        Parameters
        ----------
        scheme: str, default 'Degerickx2015_adjusted'

        Returns
        -------
        numpy.ndarray
            Parcels landuse raster
        """
        if scheme == "Degerickx2015_adjusted":
            return create_parcels_landuse_degerick2015(
                self.landuse_core,
                self.river,
                self.water,
                self.infrastructure,
                self.mask,
                self.nodata,
                landuse_parcels=self.landuse_parcels,
                parcels=self.parcels,
                grass_strips=self.grass_strips,
            )
        else:
            msg = f"Scheme '{scheme}' for creating parcels landuse raster is not known."
            raise NotImplementedError(msg)


def create_parcels_landuse_degerick2015(
    landuse_core,
    river,
    water,
    infrastructure,
    mask,
    nodata,
    landuse_parcels=None,
    parcels=None,
    grass_strips=None,
):
    """Create parcels landuse raster as with Degerickx and Van Den Broeck [1] scheme
    (version VPO).

    This schemes map rasters from top to bottom : rivers, water, infrastructure,
    grass strips, landuse from parcels data source, parcelsand finally pywatemsedem landuse.
    Incemental mapping to the parcels landuse raster is done by mapping pixels from the
    input raster to empty pixels in the landuse raster
    (see also :func:`pywatemsedem.scenario.map_input_array_on_array`). The pywatemsedem landuse
    raster is used to fill gaps.

    Parameters
    ----------
    landuse_core: numpy.ndarray
        See :class:`pywatemsedem.scenario.ParcelsLanduse`
    river: numpy.ndarray
        See :class:`pywatemsedem.scenario.ParcelsLanduse`
    water: numpy.ndarray
        See :class:`pywatemsedem.scenario.ParcelsLanduse`
    infrastructure: numpy.ndarray
        See :class:`pywatemsedem.scenario.ParcelsLanduse`
    mask: numpy.ndarray
        See :class:`pywatemsedem.scenario.ParcelsLanduse`
    landuse_parcels: numpy.ndarray, default None
        See :class:`pywatemsedem.scenario.ParcelsLanduse`
    parcels: numpy.ndarray, default None
        See :class:`pywatemsedem.scenario.ParcelsLanduse`
    grass_strips: numpy.ndarray, default None
        See :class:`pywatemsedem.scenario.ParcelsLanduse`

    Returns
    -------
    arr: numpy.ndarray
        Parcels landuse raster

    References
    ----------
    [1] Degerickx, J., Van Den Broeck, M., 2015. Handleiding CN_WS.KU Leuven, Leuven,
        Belgium.
    """

    arr = river.copy()
    if water is not None:
        arr = map_input_array_on_array(arr, water, nodata)
    if infrastructure is not None:
        arr = map_input_array_on_array(arr, infrastructure, nodata)
    if grass_strips is not None:
        arr = map_input_array_on_array(arr, grass_strips, nodata)
    if landuse_parcels is not None:
        arr = map_input_array_on_array(arr, landuse_parcels, nodata)
    if parcels is not None:
        # avoid too many parcel ids in integer 16 raster
        parcels = np.where(parcels != nodata, (parcels % 32757), nodata)
        arr = map_input_array_on_array(arr, parcels, nodata)
    if landuse_core is not None:
        arr = map_input_array_on_array(arr, landuse_core, nodata)

    arr = np.where(mask == 1, arr, 0).astype("float64")

    return arr


def map_input_array_on_array(arr, arr_input, nodata, method="only_empty"):
    """Map an input array on an other array with a method

    Parameters
    ----------
    arr: numpy.ndarray
        To map to array
    arr_input: numpy.ndarray
        To map array
    nodata: float
        No data value in arr_input array
    method: str, default "only_empty"
        Mappig method:

        - "only_empty": only map values from input array to empty (nodata) items in
          array.

    Returns
    -------
    numpy.ndarray
    """
    if arr_input.shape != arr.shape:
        msg = "Dimension to map array for are different from to map to array."
        raise ValueError(msg)
    if method == "only_empty":
        cond = arr == nodata
        return np.where(cond, arr_input, arr).copy()


def get_source_landuse(
    landuse,
    maxprc_id,
    rasterio_profile,
    arr_mask,
):
    """Get landuse raster

    Parameters
    ----------
    landuse: pywatemsedem.geo.vector.AbstractVectors

    maxprc_id : int
        Maximum perceelskaart id.
    rasterio_profile : dict
        Gdal dictionary holding all metadata for idrisi rasters.
    arr_mask : numpy.ndarray
        Binaire array defining model domain (1 else 0).
    """
    # landgebruik
    land_arr = np.where(landuse.arr == 10, maxprc_id, landuse.arr).astype("int16")
    nolanduse = np.logical_and(land_arr == rasterio_profile["nodata"], arr_mask == 1)
    land_arr = np.where(nolanduse, maxprc_id, land_arr).astype("int16")

    return land_arr
