import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np

from ..defaults import PREFIX_TEMP
from .rasterproperties import RasterProperties
from .utils import (
    clean_up_tempfiles,
    clip_vct,
    create_spatial_index,
    get_geometry_type,
    lines_to_direction,
    lines_to_raster,
    load_raster,
    polygons_to_raster,
    read_rasterio_profile,
    vct_to_rst_field,
)


class AbstractVector:
    """Abstract Vector class based on geopandas GeoDataFrame"""

    def __init__(self):
        self._geodata = None
        self._geometry_type = None

    def initialize(
        self, geodata, geometry_type, req_geometry_type=None, allow_empty=False
    ):
        """Abstract vector class

        Parameters
        ----------
        geodata: geopandas.GeoDataFrame
            Input data set.
        geometry_type: str
            Geometry type of input dataset
        req_geometry_type: str, default None
            Geometry type, for implemented types, see
            :func:`pywatemsedem.geo.vectors.AbstractVector.check_type`
        allow_empty: bool, default False
            Allow an empty geodataframe
        """
        self._geodata = geodata
        self._geometry_type = geometry_type
        self.check_type(geometry_type, req_geometry_type)
        if not allow_empty:
            try:
                self.check_if_empty()
            except ValueError:
                msg = (
                    "Input vector is empty. If you wish to "
                    "return an empty vector, please use 'allow_empty'."
                )
                raise ValueError(msg)

    def check_type(
        self,
        geometry_type,
        req_geometry,
        implemented_types=["LineString", "Polygon", "Point"],
    ):
        """Check geometry types of vector to the required type

        Parameters
        ----------
        geometry_type: str
            Geometry type of input dataset.
        req_geometry: str
            The required geometry types
        implemented_types: list, default "LineString", "Polygon", "Point"
            List of implemented geometry types.
        """
        if req_geometry is not None:
            if req_geometry not in implemented_types:
                msg = (
                    f"Required geometry item type '{req_geometry}' not known to "
                    f"pywatemsedem. Please select '{' or '.join(implemented_types)}'"
                )
                raise TypeError(msg)
            if req_geometry is not geometry_type:
                msg = (
                    f"Input vector should have geometry item type "
                    f"'{req_geometry}', not '{geometry_type}'."
                )
                raise TypeError(msg)

    def check_if_empty(self):
        """Check if input is empty"""
        if self._geodata.empty:
            msg = "Input vector cannot be empty!"
            raise ValueError(msg)

    def plot(self, color=None, column=None):
        """Plot shape vector with geopandas plot

        Parameters
        ----------
        color

        Returns
        -------
        ax: matplotlib.pyplot.axis
        """
        df = self.geodata.to_crs(epsg=3857)
        kwargs = {}
        if column is not None:
            kwargs = {**kwargs, "cmap": "viridis", "legend": True}
        ax = df.plot(
            alpha=0.8, lw=2, figsize=[10, 10], color=color, column=column, **kwargs
        )

        return ax

    @property
    def geodata(self):
        """Property to override"""
        return self._geodata

    @geodata.setter
    def geodata(self, input):
        """Setter"""
        self._geodata = input

    def clip(self):
        """NotImplemented clip function"""
        raise NotImplementedError

    def write(self, outfile_path):
        """Write raster data to disk.

        Parameters
        ----------
        outfile_path: pathlib.Path or str, default None
            File path output
        """
        if outfile_path is not None:
            outfile_path = Path(outfile_path)
        if outfile_path.suffix == ".shp":
            self._geodata.to_file(outfile_path)
            create_spatial_index(outfile_path)
        elif outfile_path.suffix == "":
            self._geodata.to_file(outfile_path, driver="ESRI Shapefile")  # esri
            create_spatial_index(outfile_path)
        else:
            msg = f"Extension of  {outfile_path} not support in pywatemsedem"
            raise TypeError(msg)
        return True

    def rasterize(
        self,
        rst_reference,
        epsg,
        col="NR",
        nodata=None,
        dtype_raster="float",
        convert_lines_to_direction=False,
        gdal=False,
    ):
        """Rasterize function for shape file

        Parameters
        ----------
        rst_reference: str or  pathlib.Path
            File path to reference file for raster output.
        epsg: int
            EPSG code should be a numeric value, see https://epsg.io/.
        col: str, default "NR"
            Column name to map
        nodata: float, default None
            Values within dataframe 'col' that have to be considered as nodata in
            raster.
        dtype_raster: str, default "float"
            Output raster type
            convert_lines_to_direction:
        convert_lines_to_direction: bool, default "False"
            Convert lines to directions
        gdal: bool, default False
            Use gdal(true) / saga (false)-enige for mapping.

        Returns
        -------
        arr: numpy.ndarray
            Return numpy array
        """
        # convert lines to directions only be done with saga
        if gdal & convert_lines_to_direction:
            gdal = False

        if (col == "NR") & ("NR" not in self._geodata.columns):
            self._geodata["NR"] = np.arange(0, len(self._geodata), 1)
        if nodata is not None:
            self._geodata.loc[self._geodata[col] == nodata, col] = -99999.0
        vct_temp = tempfile.NamedTemporaryFile(prefix=PREFIX_TEMP, suffix=".shp").name
        self.write(vct_temp)

        rp = RasterProperties.from_rasterio(
            read_rasterio_profile(rst_reference), epsg=epsg
        )
        if gdal:
            tf_rst = tempfile.NamedTemporaryFile(
                suffix=".tif", prefix=PREFIX_TEMP, delete=False, mode="w"
            )
            vct_to_rst_field(vct_temp, tf_rst.name, rp.gdal_profile, col)
            arr, _ = load_raster(tf_rst.name)
            clean_up_tempfiles(tf_rst, "tiff")

        else:
            tf_rst = tempfile.NamedTemporaryFile(
                suffix=".sgrid", prefix=PREFIX_TEMP, delete=False
            )
            if self._geometry_type == "LineString":
                if convert_lines_to_direction:
                    lines_to_direction(vct_temp, Path(tf_rst.name), rst_reference)
                else:
                    lines_to_raster(
                        vct_temp, Path(tf_rst.name), rst_reference, col, dtype_raster
                    )
            elif self._geometry_type == "Polygon":
                if convert_lines_to_direction:
                    msg = "Cannot convert polygons to directions"
                    raise IOError(msg)
                polygons_to_raster(
                    vct_temp, Path(tf_rst.name), rst_reference, col, dtype_raster
                )
            elif self._geometry_type == "Point":
                msg = "Rasterisation of points is not implemented."
                raise NotImplementedError(msg)

            arr, profile = load_raster(Path(tf_rst.name).with_suffix(".sdat"))
            # correct no data value if necessary
            if profile["nodata"] != rp.nodata:
                arr[arr == profile["nodata"]] = rp.nodata
            tf_rst.close()
            clean_up_tempfiles(tf_rst, "tiff")
            clean_up_tempfiles(tf_rst, "saga")

        clean_up_tempfiles(vct_temp, "shp")

        return arr

    def is_empty(self):
        """check if geodata (vector) is None (empty)

        Returns
        -------
        True/False
        """
        return self._geodata is None


class VectorMemory(AbstractVector):
    """Geopandas vector

    Parameters
    ----------
    geodata: geopandas.GeoDataFrame
        See :class:`pywatemsedem.geo.vectors.AbstractVector`
    geometry_type: str
        See :class:`pywatemsedem.geo.vectors.AbstractVector`
    req_geometry_type: str, default None
        See :class:`pywatemsedem.geo.vectors.AbstractVector`
    allow_empty: bool, default False
        See :class:`pywatemsedem.geo.vectors.AbstractVector`
    """

    def __init__(
        self, geodata, geometry_type, req_geometry_type=None, allow_empty=False
    ):
        """Initialize RasterMemory"""
        super().initialize(
            geodata, geometry_type, req_geometry_type, allow_empty=allow_empty
        )

    def clip(self):
        """NotImplemented clip function"""
        raise NotImplementedError


class VectorFile(AbstractVector):
    """clipped Vector based on input vector file"""

    def __init__(
        self, file_path, req_geometry_type=None, vct_clip=None, allow_empty=False
    ):
        """Initialize RasterFile class

        Parameters
        ----------
        file_path: pathlib.Path
            File path to user input raster.
        vct_clip: pathlib.Path
            Mask vector
        req_geometry_type: str
            Required type of geometry, see implemented geometries in
            :func:`pywatemsedem.geo.vectors.AbstractVector.check_type`
        allow_empty: bool, default False
            See :class:`pywatemsedem.geo.vectors.AbstractVector`
        """
        geometry_type = get_geometry_type(file_path)

        if vct_clip is not None:
            geodata = self.clip(file_path, vct_clip)
        else:
            geodata = gpd.read_file(file_path)

        super().initialize(
            geodata,
            geometry_type,
            req_geometry_type=req_geometry_type,
            allow_empty=allow_empty,
        )

    def clip(self, file_path, vct_clip):
        """Clip input file path with vct_clip

        Parameters
        ----------
        file_path: pathlib.Path
            File path to user input raster.
        vct_clip: pathlib.Path
            Mask vector
        geometry_type: str
            Required type of geometry, see implemented geometries in
            :func:`pywatemsedem.geo.vectors.AbstractVector.check_type`

        Returns
        -------
        geopandas.GeoDataFrame
        """
        vct_temp = Path(
            tempfile.NamedTemporaryFile(suffix=".shp", prefix=PREFIX_TEMP).name
        )
        clip_vct(file_path, vct_temp, vct_clip)
        geodata = gpd.read_file(vct_temp)
        clean_up_tempfiles(vct_temp, "shp")

        return geodata
