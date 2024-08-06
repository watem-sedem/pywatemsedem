import warnings
from typing import List

import fiona
import numpy as np
from pyproj import CRS
from pyproj.exceptions import CRSError
from rasterio import Affine


class RasterProperties:
    """Raster properties class

    Pywatemsedem makes use of rasterio and gdal for loading, writing and processing
    rasters/vectors. A small class is implemented to easily switch between raster
    geographic references of gdal and rasterio, respectively names *gdal_profile*
    and *rasterio_profile*. Assuming you start with loading a raster with rasterio:

    .. code-block::

        from pywatemsedem.geo.utils import load_raster
        from pywatemsedem.geo.rasterproperties import RasterProperties
        arr, _, rasterio_profile = load_raster("test.tif")
        rp = RasterProperties.from_rasterio(rasterio_profile)
        rp.gdal_profile
        ...

    Note that ``rasterio_profile`` is of type dictionary, as such one can start from
    a profile definition in a dictionary format, for instance for gdal:

    .. code-block::

        from pywatemsedem.geo.utils import load_raster
        from pywatemsedem.geo.rasterproperties import RasterProperties
        gdal_profile = {
            "nodata": -9999.0,
            "epsg": "EPSG:31370",
            "res": 20.0,
            "minmax": [201620.0, 153880.0, 207500.0, 164060.0],
            "ncols": 294,
            "nrows": 509,
        }
        rp = RasterProperties.from_gdal(gdal_profile)
        rp.rasterio_profile
        ...

    In addition, a ``RasterProfile`` instance can be generated from known raster
    bounds and a raster resolution
    (this can be useful for generating raster geographical references when
    no rasterio or gdal profile definition is available):

    .. code-block::

        from pywatemsedem.geo.rasterproperties import RasterProperties

        bounds = [201620.0, 153880.0, 207500.0, 164060.0]
        resolution = 20
        nodata= -9999
        epsg = 31370
        rp = RasterProperties(bounds, resolution, nodata, epsg)

    Notes
    -----
    1. Current implementation support storing of raster properties, yet is does not aim
       to provide functionalities to adapt raster properties (as these functionalities
       are present in rasterio).
    2. Current implementation does not support tiled rasters. In addition,
       it only support bands-interleaving as only single-band raster are used.
    3. Definition interleaving: the way multiple bands of a raster are saved to the
       raster (e.g. pixel-based, line-based, band-based)
    4. The coordinate reference system (crs) is defined in EPSG.
    5. Note that dtype in gdal operation is typically derived from input raster
       dtype that is used to execute the gdal operation. As such dtype is not
       defined as a key in the gdal_profile property.
    """

    def __init__(
        self,
        bounds: List[float],
        resolution: int,
        nodata: float,
        epsg: int,
        driver: str = "GTiff",
    ):
        """Initialize a RasterProperties instance

        Parameters
        ----------
        bounds: list
            The **first** entry is **x_left**, the **second** entry is **y_lower**, the
            **third** entry is **x_right** and the **fourth** entry is **y_upper**
            [x_left, y_lower, x_right, y_upper].
        resolution: int
            Spatial resolution.
        nodata: float
            No data values.
        epsg: int
            EPSG code should be a numeric value, see https://epsg.io/.
        dtype: str, default "float64"
            Raster type
        driver : GTiff | RST | SAGA
            Name of GDAL driver, see https://gdal.org/drivers/raster/index.html; only
            GTiff | RST | SAGA are supported.
        """
        self._bounds = bounds
        self._resolution = resolution

        self._ncols = None
        self._nrows = None
        self._set_ncols_nrows()

        self._nodata = nodata

        self._check_epsg(epsg)
        self._epsg = epsg

        self._check_driver(driver)
        self._driver = driver

        self._xcoord = None
        self._ycoord = None

    @classmethod
    def from_gdal(cls, gdal_profile: dict):
        """Set RasterProperties from a gdal profile

        Parameters
        -----------
        gdal_profile: dict
        """
        if not {"res", "ncols", "nrows", "minmax", "nodata", "epsg"}.issubset(
            gdal_profile.keys()
        ):
            msg = "Function input is not a gdal profile instance!"
            raise IOError(msg)

        return cls(
            bounds=gdal_profile["minmax"],
            resolution=gdal_profile["res"],
            nodata=gdal_profile["nodata"],
            epsg=int(gdal_profile["epsg"].split(":")[1]),
        )

    @property
    def gdal_profile(self) -> dict:
        """Return gdal profile

        Returns
        -------
        gdal_profile: dict
            See definition in this function.
        """
        gdal_profile = dict()
        gdal_profile["nodata"] = self._nodata
        gdal_profile["epsg"] = f"EPSG:{self._epsg}"
        # gdal_profile["epsg"] = f"{self._epsg}"
        gdal_profile["res"] = self._resolution
        gdal_profile["minmax"] = self._bounds
        gdal_profile["ncols"] = self._ncols
        gdal_profile["nrows"] = self._nrows

        return gdal_profile

    @classmethod
    def from_rasterio(cls, rasterio_profile: dict, epsg: int = None):
        """Set RasterProperties with a rasterio profile

        Parameters
        -----------
        rasterio_profile: dict
        epsg: int, default None
            EPSG code should be a numeric value, see https://epsg.io/.
        """
        if not {"transform", "width", "height", "crs", "nodata"}.issubset(
            rasterio_profile.keys()
        ):
            msg = "Function input is not a rasterio profile instance!"
            raise IOError(msg)

        bounds = [
            rasterio_profile["transform"][2],
            rasterio_profile["transform"][5]
            - rasterio_profile["height"] * rasterio_profile["transform"][0],
            rasterio_profile["transform"][2]
            + rasterio_profile["width"] * rasterio_profile["transform"][0],
            rasterio_profile["transform"][5],
        ]
        if epsg is None:
            epsg = rasterio_profile["crs"].to_epsg()
        return cls(
            bounds=bounds,
            resolution=rasterio_profile["transform"][0],
            nodata=rasterio_profile["nodata"],
            epsg=epsg,
        )

    @property
    def rasterio_profile(self) -> dict:
        """Return rasterio profile

        Returns
        -------
        rasterio_profile: dict
            See definition in this function.
        """
        rasterio_profile = dict()
        rasterio_profile["driver"] = self._driver
        rasterio_profile["height"] = self._nrows
        rasterio_profile["width"] = self._ncols
        rasterio_profile["crs"] = CRS.from_epsg(self._epsg)
        rasterio_profile["transform"] = Affine(
            int(self._resolution),
            0,
            int(self._bounds[0]),
            0,
            -int(self._resolution),
            int(self._bounds[3]),
        )
        rasterio_profile["count"] = 1
        rasterio_profile["nodata"] = self._nodata
        if self._driver == "GTiff":
            rasterio_profile["compress"] = "deflate"

        return rasterio_profile

    @property
    def bounds(self) -> List[float]:
        """Raster boundary coordinates.

        Returns
        -------
        list : [x_left, y_lower, x_right, y_upper]
            The **first** entry is **x_left**, the **second** entry is **y_lower**, the
            **third** entry is **x_right** and the **fourth** entry is **y_upper**.
        """
        return self._bounds

    @property
    def resolution(self) -> int:
        """Raster resolution"""
        return self._resolution

    def _set_ncols_nrows(self):
        """Set the number of columns and rows based on the bounds and the resolution"""
        self._ncols = int(round((self._bounds[2] - self._bounds[0]) / self._resolution))
        self._nrows = int(round((self._bounds[3] - self._bounds[1]) / self._resolution))

    @property
    def nodata(self) -> float:
        """No data value used in raster."""
        return self._nodata

    @staticmethod
    def _check_epsg(epsg: int):
        """Check EPSG code

        Parameters
        ----------
        epsg: int
            EPSG code should be a numeric value, see https://epsg.io/.
        """
        if type(epsg) is not int:
            msg = f"EPSG-code '{epsg}' need to be an integer code."
            raise TypeError(msg)
        try:
            CRS.from_epsg(epsg)
        except CRSError:
            msg = f"EPSG-code '{epsg}' is an unknown epsg-code."
            raise CRSError(msg)

    @property
    def epsg(self) -> int:
        """int: EPSG code of the raster projection should be a numeric value,
        see https://epsg.io/"""
        return self._epsg

    @property
    def nrows(self) -> int:
        """Number of rows in the raster

        Returns
        -------
        int
        """
        return self._nrows

    @property
    def ncols(self) -> int:
        """Number of columns in the raster

        Returns
        -------
        int
        """
        return self._ncols

    @staticmethod
    def _check_driver(driver: str):
        """Check if the defined driver is known to pywatemsedem."""
        if driver not in ["GTiff", "RST", "SAGA"]:
            msg = f"Raster property driver '{driver}' not supported in pywatemsedem."
            raise IOError(msg)

    @property
    def driver(self) -> str:
        """Name of GDAL driver

        see https://gdal.org/drivers/raster/index.html;
        only GTiff | RST | SAGA are supported."""
        return self._driver

    @property
    def xcoord(self):
        """Returns 1D-vector array of x-coordinates

        Returns
        --------
        numpy.ndarray
        """
        return np.linspace(self.bounds[0], self.bounds[2], self.ncols)

    @property
    def ycoord(self):
        """Returns 1D-vector array of y-coordinates

        Returns
        --------
        numpy.ndarray
        """
        return np.linspace(self.bounds[1], self.bounds[3], self.nrows)


def get_bounds_from_vct(vct_catchment, resolution, n_pixels_buffer=5):
    """Get bounds from vector catchment.

    Parameters
    ----------
    vct_catchment: pathlib.Path
        Vector file of catchment.
    resolution: int
        Spatial resolution, see :class:`pywatemsedem.geo.rasterproperties.RasterProperties`
    n_pixels_buffer: int, default 5
        Number of pixels that have to be taken into account to expand boundaries

    Returns
    -------
    bounds: list
        See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`
    """
    with fiona.open(vct_catchment) as c:
        # Get spatial extent of catchment.
        bounds = c.bounds
        bounds = [
            round(bounds[0]) - n_pixels_buffer * resolution,
            round(bounds[1]) - n_pixels_buffer * resolution,
            round(bounds[2]) + n_pixels_buffer * resolution,
            round(bounds[3]) + n_pixels_buffer * resolution,
        ]

    return bounds


def synchronize_bounds(target, source, resolution):
    """Synchronize target geographical bounds of a raster with source bounds given a
     raster resolution.

    Bounds are defined as a list of  xmin, ymin, xmax and ymax-values of a raster. The
    boundaries leading to the smallest geographical model are selected as new
    boundaries.

    Parameters
    ----------
    target: list
        To check target boundaries, see
        :class:`pywatemsedem.geo.rasterproperties.RasterProperties`.
    source: pathlib.Path
        Source boundaries to which target boundaries have to be checked, see
        :class:`pywatemsedem.geo.rasterproperties.RasterProperties`.
    resolution: int
        See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`

    Returns
    -------
    bounds: list
        Updated bounds
    """
    check = False
    for i in range(4):
        if i < 2:  # xmin en ymin
            rest = (target[i] - source[i]) % resolution
            if rest != 0:
                check = True
                target[i] = target[i] - rest

        else:  # xmax en ymax
            rest = (target[i] - source[i - 2]) % resolution
            if rest != 0:
                check = True
                target[i] = target[i] - rest + resolution
    if check:
        msg = (
            f"Synchronizing x/y-axis model boundaries with input raster `{source.stem}`"
        )
        warnings.warn(msg)
    return target
