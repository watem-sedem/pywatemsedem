import inspect
import tempfile
from functools import wraps
from pathlib import Path

import fiona
import geopandas as gpd
import numpy as np
import rasterio
from fiona.collection import DriverError
from rasterio import RasterioIOError

from ..defaults import PREFIX_TEMP
from .rasterproperties import RasterProperties
from .rasters import RasterFile, RasterMemory, TemporalRaster
from .utils import (
    clean_up_tempfiles,
    define_extent_from_vct,
    generate_vct_mask_from_raster_mask,
    load_raster,
    vct_to_rst_value,
)
from .valid import PywatemsedemInputError, valid_exists
from .vectors import VectorFile, VectorMemory


def valid_mask_factory(func):
    """Check valid mask inputted when using raster or vectofactory"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """Wrapper fun"""
        if self.mask is None:
            msg = (
                f"First create a mask with " f"{Factory.create_mask.__name__}-function"
            )
            raise PywatemsedemInputError(msg)
        return func(self, *args, **kwargs)

    return wrapper


class Factory:
    """Factory class

    Used to enable functions to generate vectors and rasters.

    Notes
    -----
    By default a rasterproperties instance is made in the initialisation
    See :func:`pywatemsedem.geo.factory.create_mask`-function. This can be toggled of by
    setting :const:`pywatemsedem.geo.factory.Factory.create_rasterproperties` to False
    """

    def __init__(self, resolution, epsg_code, nodata, resmap, bounds=None):
        """See class docs

        Parameters
        ---------
        resolution:int
            Model spatial resolution
        epsg_code: int
            EPSG code should be a numeric value, see https://epsg.io/.
        nodata: float
            See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`
        resmap: pathlib.Path | str
            Folder path to write factory files to
        bounds: list, default None
            Raster boundaries which you wish for model.
            See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`
        """
        self._resolution = resolution
        self._epsg_code = epsg_code
        self._nodata = nodata
        self._bounds = bounds
        self._rp = None
        self._mask = None
        self._bounds = None
        resmap = Path(resmap) / "factory"
        if not resmap.exists():
            resmap.mkdir(exist_ok=True)
        self.mask_vector = resmap / "mask.shp"
        self.mask_raster = resmap / "mask.rst"
        # standard rasterproperties are generated in mask pahe from vector or raster
        # input
        self.create_rasterproperties = True

    @property
    def rp(self):
        "RasterProperties. See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`"
        return self._rp

    @rp.setter
    def rp(self, rasterproperties):
        "RasterProperties. See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`"
        self._rp = rasterproperties

    @property
    def mask(self):
        "AbstractRaster mask"
        return self._mask

    @property
    def vct_mask(self):
        "AbstractVector mask, See :class:`pywatemsedem.geo.vectors.AbstractVector`"
        return self._vct_mask

    @mask.setter
    def mask(self, mask):
        """Set mask with an numpy array

        Parameters
        ----------
        mask : str or pathlib.Path
            Either a valid raster of vector file
        """
        self.create_mask(mask)

    def create_mask(self, mask):
        """Create mask based on a mask template (raster or vector)

        Parameters
        ----
        file_path: pathlib.Path | str
            File path to mask vector raster file

        Notes
        -----
        If :const:`pywatemsedem.geo.factory.Factory.create_rasterproperties` is set
        to False, one needs to self-define a RasterProperties instance.
        """
        valid_exists(mask, None)
        if self.create_rasterproperties is False:
            if self.rp is None:
                msg = (
                    f"Define a 'RasterProperties'-instance for the "
                    f"'{self.__class__.__name__}'-instance "
                    f"({self.__class__.__name__}.rp = RasterProperties(...)) or set "
                    f"'{self.__class__.__name__}.create_rasterproperties' to True."
                )
                raise IOError(msg)

        try:
            rasterio.open(mask)
        except RasterioIOError:
            try:
                fiona.open(mask)
            except DriverError:
                msg = "Input mask should be raster or vector polygon file."
                raise IOError(msg)
            else:
                if self.create_rasterproperties:
                    self.rp = define_extent_from_vct(
                        mask,
                        self._resolution,
                        self._nodata,
                        self._epsg_code,
                        self._bounds,
                    )
                tf_rst = tempfile.NamedTemporaryFile(
                    suffix=".tif", prefix=PREFIX_TEMP, delete=False
                )
                vct_to_rst_value(mask, tf_rst.name, 1, self.rp.gdal_profile)
                arr, _ = load_raster(tf_rst.name)
                clean_up_tempfiles(tf_rst, "tiff")
                self._vct_mask = VectorFile(mask)
        else:
            arr, rp = load_raster(mask)
            if self.create_rasterproperties:
                self.rp = RasterProperties.from_rasterio(rp, epsg=self._epsg_code)
            vct_mask = mask.with_suffix(".shp")
            generate_vct_mask_from_raster_mask(mask, vct_mask, self._resolution)
            self._vct_mask = VectorFile(vct_mask)
            self._vct_mask._geodata = self._vct_mask._geodata.set_crs(self.rp.epsg)

        self._mask = RasterMemory(arr, self.rp)
        self.vct_mask.write(self.mask_vector)
        self._mask.write(self.mask_raster, "idrisi")
        self._mask.arr_bin = np.where(
            self._mask.arr == self.rp.nodata, 0, self._mask.arr
        )

        return True

    @valid_mask_factory
    def raster_factory(
        self, raster_input, flag_clip=True, flag_mask=True, allow_nodata_array=False
    ):
        """Raster factory to load rasters in memory

        Parameters
        ----------
        raster_input: str, pathlib.Path or numpy.ndarray
            Input raster file or numpy array
        flag_clip: bool, default True
            Clip raster (True)
        flag_mask: bool, default True
            Mask raster (True)
        allow_nodata_array: default False
            Allow the returned array to only contian nodata-values,
            see :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.

        Returns
        -------
        raster: pywatemsedem.geo.rasters.AbstractRaster
            See :class:`pywatemsedem.geo.rasters.AbstractRaster`

        """
        arr_mask = self.mask.arr_bin if flag_mask else None
        if isinstance(raster_input, str):
            raster_input = Path(raster_input)
        if isinstance(raster_input, Path):
            try:
                rasterio.open(raster_input)
            except IOError:
                msg = (
                    f"Input raster file '{raster_input}' should be a valid raster "
                    f"file (e.g. IDRISI raster, geotiff, SAGA-GRID, ..)"
                )
                raise IOError(msg)
            rp = self.rp if flag_clip else None
            raster = RasterFile(
                raster_input, rp, arr_mask, allow_nodata_array=allow_nodata_array
            )
        elif isinstance(raster_input, np.ndarray):
            if raster_input.ndim == 2:
                raster = RasterMemory(
                    raster_input,
                    self.rp,
                    arr_mask,
                    allow_nodata_array=allow_nodata_array,
                )
            else:
                raster = TemporalRaster(raster_input, self.rp, arr_mask)
        else:
            print(type(raster_input))
            print(raster_input)
            m = inspect.currentframe()
            calframe = inspect.getouterframes(m, 2)
            [cal.function for cal in calframe]
            msg = (
                f"Input raster should be a numpy array or raster file, current type"
                f" is '{type(raster_input)}'"
            )
            raise IOError(msg)

        return raster

    @valid_mask_factory
    def vector_factory(self, vector_input, geometry_type, allow_empty=False):
        """Vector factory to load rasters in memory

        Parameters
        ----------
        vector_input: str, pathlib.Path or geopandas.GeoDataFrame
            Input vector file or geopandas dataframe
        mask: bool, default True
            Mask vector (True), nodata value will be that one of
            `pywatemsedem.geo.factory.Factory.rp`.
        allow_empty: bool, default False
            Allow vector to be empty, see :class:`pywatemsedem.geo.vectors.AbstractVector`

        Returns
        -------
        vector: pywatemsedem.geo.rasters.AbstractRaster
            See :class:`pywatemsedem.geo.rasters.AbstractRaster`
        """

        if isinstance(vector_input, str):
            vector_input = Path(vector_input)
        if isinstance(vector_input, Path):
            try:
                fiona.open(vector_input)
            except fiona.errors.DriverError:
                msg = (
                    f"Input vector file '{vector_input}' should be a valid "
                    f"vector file (e.g. ESRI shape file)."
                )
                raise IOError(msg)
            vector = VectorFile(
                vector_input, geometry_type, self.mask_vector, allow_empty=allow_empty
            )
        elif isinstance(vector_input, gpd.GeoDataFrame):
            vector = VectorMemory(vector_input, geometry_type, allow_empty=allow_empty)
        else:
            msg = "Input vector should be a geopandas GeoDataFrame or vector file."
            raise IOError(msg)

        return vector
