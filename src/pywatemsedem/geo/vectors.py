from pathlib import Path

import geopandas as gpd
import numpy as np

from pywatemsedem.geo.rasterproperties import RasterProperties
from pywatemsedem.geo.utils import (
    clean_up_tempfiles,
    create_filename,
    get_geometry_type,
    lines_to_direction,
    lines_to_raster,
    load_raster,
    points_to_raster,
    polygons_to_raster,
    read_rasterio_profile,
    vct_to_rst_field,
)


class AbstractVector:
    """Abstract vector class based on geopandas GeoDataFrame.

    Attributes
    ----------
    geodata : geopandas.GeoDataFrame
        Vector data.
    """

    def __init__(self):
        """Initialize AbstractVector."""
        self._geodata = None
        self._geometry_type = None

    def initialize(
        self,
        geodata,
        geometry_type,
        req_geometry_type=None,
        allow_empty=False,
        req_epsg=None,
    ):
        """Initialize vector with geodata and geometry type.

        Parameters
        ----------
        geodata : geopandas.GeoDataFrame
            Input data set.
        geometry_type : str
            Geometry type of input dataset.
        req_geometry_type : str, default None
            Geometry type, for implemented types, see
            :func:`pywatemsedem.geo.vectors.AbstractVector.check_type`.
        allow_empty : bool, default False
            Allow an empty geodataframe.
        req_epsg : int, default None
            Required EPSG code.
        """
        self._geodata = geodata
        self._geometry_type = geometry_type
        self.check_type(geometry_type, req_geometry_type)
        self.check_crs(req_epsg)
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
        """Check geometry types of vector to the required type.

        Parameters
        ----------
        geometry_type : str
            Geometry type of input dataset.
        req_geometry : str
            The required geometry type.
        implemented_types : list, default ["LineString", "Polygon", "Point"]
            List of implemented geometry types.

        Raises
        ------
        TypeError
            If required geometry type is not implemented or does not match.
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

    def check_crs(self, req_epsg):
        """Check if CRS matches the required EPSG code.

        Parameters
        ----------
        req_epsg : int
            Required EPSG code.
        """
        if req_epsg is not None:
            if self._geodata.crs.to_epsg() != req_epsg:
                if self._geodata.crs is None:
                    self._geodata = self._geodata.set_crs(epsg=f"EPSG:{req_epsg}")
                else:
                    self._geodata = self._geodata.to_crs(epsg=req_epsg)

    def check_if_empty(self):
        """Check if input geodataframe is empty.

        Raises
        ------
        ValueError
            If the geodataframe is empty.
        """
        if self._geodata.empty:
            msg = "Input vector cannot be empty!"
            raise ValueError(msg)

    def plot(self, color=None, column=None):
        """Plot vector with geopandas plot.

        Parameters
        ----------
        color : str, default None
            Color for plotting.
        column : str, default None
            Column name for color mapping.

        Returns
        -------
        matplotlib.axes.Axes
            Axes object.
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
        """Return geodata.

        Returns
        -------
        geopandas.GeoDataFrame
            Vector data.
        """
        return self._geodata

    @geodata.setter
    def geodata(self, input):
        """Set geodata.

        Parameters
        ----------
        input : geopandas.GeoDataFrame
            Vector data.
        """
        self._geodata = input

    def write(self, outfile_path):
        """Write vector data to disk.

        Parameters
        ----------
        outfile_path : pathlib.Path or str
            File path output.

        Returns
        -------
        bool
            True if write was successful.

        Raises
        ------
        TypeError
            If file extension is not supported.
        """
        if outfile_path is not None:
            outfile_path = Path(outfile_path)
        if outfile_path.suffix == ".shp":
            self._geodata.to_file(
                outfile_path, driver="ESRI Shapefile", spatial_index="YES"
            )
        elif outfile_path.suffix == "":
            self._geodata.to_file(
                outfile_path, driver="ESRI Shapefile", spatial_index="YES"
            )
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
        """Rasterize vector to array.

        Parameters
        ----------
        rst_reference : str or pathlib.Path
            File path to reference file for raster output.
        epsg : int
            EPSG code, should be a numeric value. See https://epsg.io/.
        col : str, default "NR"
            Column name to map.
        nodata : float, default None
            Values within dataframe 'col' that have to be considered as nodata
            in raster.
        dtype_raster : str, default "float"
            Output raster type.
        convert_lines_to_direction : bool, default False
            Convert lines to directions.
        gdal : bool, default False
            Use gdal (True) or saga (False) engine for mapping.

        Returns
        -------
        numpy.ndarray
            Rasterized array.
        """
        # convert lines to directions only be done with saga
        if gdal & convert_lines_to_direction:
            gdal = False

        if (col == "NR") & ("NR" not in self._geodata.columns):
            self._geodata["NR"] = np.arange(0, len(self._geodata), 1)
        if nodata is not None:
            self._geodata.loc[self._geodata[col] == nodata, col] = -99999.0
        vct_temp = create_filename(".shp")
        self.write(vct_temp)

        rp = RasterProperties.from_rasterio(
            read_rasterio_profile(rst_reference), epsg=epsg
        )
        if gdal:
            tf_rst = create_filename(".sgrd")
            vct_to_rst_field(
                vct_temp, tf_rst.with_suffix(".sdat"), rp.gdal_profile, col
            )
            arr, _ = load_raster(tf_rst)
            clean_up_tempfiles(tf_rst, "sgrd")

        else:
            tf_rst = create_filename(".sgrd")
            if self._geometry_type == "LineString":
                if convert_lines_to_direction:
                    lines_to_direction(vct_temp, tf_rst, rst_reference)
                else:
                    lines_to_raster(vct_temp, tf_rst, rst_reference, col, dtype_raster)
            elif self._geometry_type == "Polygon":
                if convert_lines_to_direction:
                    msg = "Cannot convert polygons to directions"
                    raise IOError(msg)
                polygons_to_raster(vct_temp, tf_rst, rst_reference, col, dtype_raster)
            elif self._geometry_type == "Point":
                if convert_lines_to_direction:
                    msg = "Cannot convert polygons to directions"
                    raise IOError(msg)
                points_to_raster(vct_temp, tf_rst, rst_reference, col, dtype_raster)

            arr, profile = load_raster(tf_rst.with_suffix(".sdat"))
            # correct no data value if necessary
            if profile["nodata"] != rp.nodata:
                arr[arr == profile["nodata"]] = rp.nodata
            clean_up_tempfiles(tf_rst, "tiff")
            clean_up_tempfiles(tf_rst, "saga")

        clean_up_tempfiles(vct_temp, "shp")

        return arr

    def is_empty(self):
        """Check if geodata (vector) is None (empty).

        Returns
        -------
        bool
            True if geodata is None, False otherwise.
        """
        empty = False

        if self._geodata is None:
            empty = True
        elif len(self._geodata) == 0:
            empty = True

        return empty


class VectorMemory(AbstractVector):
    """Vector stored in memory from a geopandas GeoDataFrame.

    Attributes
    ----------
    geodata : geopandas.GeoDataFrame
        Vector data.

    Notes
    -----
    Inherits from :class:`pywatemsedem.geo.vectors.AbstractVector`.
    """

    def __init__(
        self,
        geodata,
        geometry_type,
        req_geometry_type=None,
        clip_mask=None,
        allow_empty=False,
        epsg=None,
    ):
        """Initialize VectorMemory.

        Parameters
        ----------
        geodata : geopandas.GeoDataFrame
            Input geodataframe.
        geometry_type : str
            Geometry type of input dataset.
        req_geometry_type : str, default None
            Required geometry type.
        clip_mask : geopandas.GeoDataFrame, default None
            Mask vector for clipping.
        allow_empty : bool, default False
            Allow an empty geodataframe.
        epsg : int, default None
            Required EPSG code.
        """
        if clip_mask is not None:
            geodata = self.clip(geodata, clip_mask)

        super().initialize(
            geodata,
            geometry_type,
            req_geometry_type,
            allow_empty=allow_empty,
            req_epsg=epsg,
        )

    def clip(self, geodata, clip_mask):
        """Clip input geodata with clip_mask.

        Parameters
        ----------
        geodata : geopandas.GeoDataFrame
            Geodataframe of input data.
        clip_mask : geopandas.GeoDataFrame
            Mask vector.

        Returns
        -------
        geopandas.GeoDataFrame
            Clipped geodataframe.
        """
        gdf = gpd.clip(geodata, clip_mask, keep_geom_type=True)
        return gdf


class VectorFile(AbstractVector):
    """Vector loaded from an input vector file.

    Attributes
    ----------
    geodata : geopandas.GeoDataFrame
        Vector data.
    file_path : pathlib.Path
        File path to input vector file.

    Notes
    -----
    Inherits from :class:`pywatemsedem.geo.vectors.AbstractVector`.
    """

    def __init__(
        self,
        file_path,
        req_geometry_type=None,
        vct_clip=None,
        allow_empty=False,
        epsg=None,
    ):
        """Initialize VectorFile.

        Parameters
        ----------
        file_path : pathlib.Path
            File path to user input vector.
        req_geometry_type : str, default None
            Required type of geometry, see implemented geometries in
            :func:`pywatemsedem.geo.vectors.AbstractVector.check_type`.
        vct_clip : pathlib.Path, default None
            Mask vector for clipping.
        allow_empty : bool, default False
            Allow an empty geodataframe.
        epsg : int, default None
            Required EPSG code.
        """
        self.file_path = file_path

        geometry_type = get_geometry_type(file_path)

        if vct_clip is not None:
            geodata = self.clip(vct_clip)
        else:
            geodata = gpd.read_file(file_path)

        super().initialize(
            geodata,
            geometry_type,
            req_geometry_type=req_geometry_type,
            allow_empty=allow_empty,
            req_epsg=epsg,
        )

    def clip(self, vct_clip):
        """Clip input file path with vct_clip.

        Parameters
        ----------
        vct_clip : pathlib.Path
            Mask vector.

        Returns
        -------
        geopandas.GeoDataFrame
            Clipped geodataframe.
        """
        gdf_mask = gpd.read_file(vct_clip)
        gdf_mask = gdf_mask.dissolve()
        mask = gdf_mask.geometry[0]
        geodata = gpd.read_file(self.file_path, bbox=mask)
        geodata = gpd.clip(geodata, mask, keep_geom_type=True)
        return geodata
