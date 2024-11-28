import logging
import tempfile
import warnings
from functools import wraps
from pathlib import Path

import fiona
import geopandas as gpd
import numpy as np
import pandas as pd
from matplotlib import colors
from matplotlib import pyplot as plt

from pywatemsedem.defaults import SAGA_FLAGS
from pywatemsedem.geo.factory import Factory
from pywatemsedem.geo.rasterproperties import RasterProperties
from pywatemsedem.geo.rasters import AbstractRaster, RasterMemory
from pywatemsedem.geo.utils import (
    any_equal_element_in_vector,
    clean_up_tempfiles,
    create_spatial_index,
    define_extent_from_vct,
    execute_subprocess,
    load_raster,
    read_rasterio_profile,
)
from pywatemsedem.geo.vectors import AbstractVector
from pywatemsedem.io.folders import CatchmentFolder
from pywatemsedem.io.modeloutput import check_segment_edges
from pywatemsedem.tools import (
    format_forced_routing,
    get_df_area_unique_values_array,
    zip_folder,
)

from .errors import attribute_discrete_value_error, raster_discrete_value_error
from .valid import valid_req_property

# from .valid import valid_req_property
logger = logging.getLogger(__name__)


def valid_dtm(func):
    """Check if you have defined a DTM."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._dtm.is_empty():
            msg = "Please first define non-empty DTM!"
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_river(func):
    """Check if you have defined a river vector."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._vct_river.is_empty():
            msg = "Please define non-empty river vector!"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_infra_line(func):
    """Check if infrastructure vectors are defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._vct_infrastructure_roads.is_empty():
            msg = "Please define infrastructure line vector!"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_infra_poly(func):
    """Check if infrastructure vectors are defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._vct_infrastructure_buildings.is_empty():
            msg = "Please define non-empty infrastructure polygon vector!"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_parcels(func):
    """Check if infrastructure vectors are defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._vct_parcels.is_empty():
            msg = "Please define non_empty parcels polygon vector!"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


class Catchment(Factory):
    """Construct a new Catchment instance

    The catchment class holds all static information for a catchment.
    The class considers all data of which the content is user-option-independent (i.e.
    :class:`pywatemsedem.userchoices.UserChoices`.

    Following properties can be set:

        - *kfactor*: K-factor raster.
        - *landuse*: base landuse raster.
        - *river*: river line vector.
        - *water*: water polygon vector
        - *vct_infrastructure_buildings*: polygon vector of infrastructure
          (typically buildings).
        - *vct_infrastructure_roads*: roads line vector (with optional attribute
          'paved').
        - *cnsoil*: cn soil raster (CN-only).

    Notes
    -----
    Initialisation of mask, vector and raster handling is done with the help of the
    pywatemsedem factory class, see :class:`pywatemsedem.geo.factory.Factory`.
    """

    def __init__(
        self,
        name,
        vct_catchment,
        rst_dtm,
        resolution,
        epsg_code,
        nodata,
        results_folder=None,
    ):
        """Initialize

        Parameters
        ----------
        name: str
            Name of the catchment.
        vct_catchment: str or pathlib.Path
            Vector file of catchment outline (mask). This should be a single polygon
            vector.
        resolution: int
            Spatial resolution (m)
        epsg_code: int
            EPSG-code
        nodata: float
            Nodata-value
        results_folder: str | pathlib.Path, default None
            Folder path to write results to. If None, write to current folder
        """
        # prepare catchment
        if results_folder is None:
            results_folder = Path.cwd()
            msg = f"Setting results folder to {(results_folder / name)}"
            warnings.warn(msg)
        self.folder = CatchmentFolder(Path(results_folder) / name, resolution)
        self.folder.create_all()
        self.name = name

        # initiate factory
        super().__init__(resolution, epsg_code, nodata, results_folder / name)

        # if the binary mask of the catchment is a geopandas dataframe, map it first
        # to a file
        if type(vct_catchment) is gpd.GeoDataFrame:
            self.vct_catchment = self.folder.vct_folder / "catchment.shp"
            vct_catchment.to_file(self.vct_catchment)
        else:
            self.vct_catchment = vct_catchment
        # input your own raster properties and do not self-generate them.
        self.create_rasterproperties = False

        # get RasterProperties from catchment vector and bounds DTM
        rp = read_rasterio_profile(rst_dtm)
        bounds = RasterProperties.from_rasterio(rp).bounds
        self.rp = define_extent_from_vct(
            self.vct_catchment,
            resolution,
            nodata,
            epsg_code,
            bounds=bounds,
        )
        # set mask
        self.mask = self.vct_catchment

        # set dtm
        self.dtm = rst_dtm

        # API atttributes
        self._hydrosoilgroup = AbstractRaster()
        self._landuse = AbstractRaster()
        self._water = AbstractRaster()
        self._infrastructure = AbstractRaster()
        self._river = AbstractRaster()

        # WaTEM/SEDEM inputs
        self._pfactor = AbstractRaster()
        self._kfactor = AbstractRaster()
        self._segments = AbstractRaster()
        self._routing = AbstractRaster()

        # set name and logger
        self.name = str(name)

        # set other attributes to none

        self._vct_river = AbstractVector()
        self._tubed_river = None
        self._vct_water = AbstractVector()
        self._vct_infrastructure_buildings = AbstractVector()
        self._vct_infrastructure_roads = AbstractVector()
        self._adjacent_edges = AbstractVector()
        self._up_edges = AbstractVector()

    def zip(self):
        """Zip catchment folder"""
        zip_folder((self.folder / "Data_Bekken"))

    @property
    def dtm(self):
        """Getter dtm raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Float64 raster with DTM height values.
        """
        return self._dtm

    @dtm.setter
    def dtm(self, raster_input):
        """Assign digital elevation model raster

        The DTM input should contain valid DTM raster values in meter a.s.l.

        Parameters
        ----------
        raster_input: Pathlib.Path, str or numpy.array
            File path/array digital terrain model (m).
        """
        self._dtm = self.raster_factory(raster_input, flag_mask=False, flag_clip=True)

        def filter_within_parcels():
            """Filter dtm within parcel boundaries"""
            temp_landuse = Path(tempfile.NamedTemporaryFile(suffix=".rst").name)
            temp_dtm_in = Path(tempfile.NamedTemporaryFile(suffix=".rst").name)
            temp_dtm = Path(tempfile.NamedTemporaryFile(suffix=".sgrd").name)
            self.dtm.write(temp_dtm_in)
            self.parcels.write(temp_landuse)

            cmd_args = ["saga_cmd", "-f=s", "watem", "2"]
            cmd_args += ["-DEM", str(temp_dtm_in)]
            cmd_args += ["-PRC", str(temp_landuse)]
            cmd_args += ["-DEM_FILTER", str(temp_dtm)]
            msg = "failed to filter_within_parcels dtm"
            execute_subprocess(cmd_args, msg)
            self._dtm._arr, _ = load_raster(temp_dtm.with_suffix(".sdat"))
            clean_up_tempfiles(temp_landuse, "tiff")
            clean_up_tempfiles(temp_dtm, "saga")
            clean_up_tempfiles(temp_dtm_in, "rst")

        self._dtm.filter = filter_within_parcels

    @property
    def pfactor(self):
        """P-factor raster

        The P-factor raster holds values between 0 and 1, and is the factor in the
        RUSLE equation which takes into account erosion control. In pywatemsedem, this
        factor is always set to 1, as erosion source-oriented control measures are
        accounted for in the C-factor.

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
        """
        return self._mask

    @property
    def kfactor(self):
        """Getter K-factor raster

        The K-factor raster is a raster holding K-values for every pixel
        (:math:`\\frac{ton.h}{MJ.mm}`).

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
        """
        return self._kfactor

    @kfactor.setter
    def kfactor(self, raster_input):
        """Assign K-factor raster

        The K-factor raster is a raster holding K-values for every pixel
        (:math:`\\frac{ton.h}{MJ.mm}`). Negative no nodata values are set to zero.

        Parameters
        ----------
        raster_input: Pathlib.Path, str or numpy.array
            File path/array K-factor raster (:math:`\\frac{ton.h}{MJ.mm}`) with K-values
            (see K-factor in RUSLE equation).

        Notes
        -----
        1. The input requires as unit: :math:`\\frac{ton.h}{MJ.mm}`, whereas the output
           unit is :math:`\\frac{kg.h}{MJ.mm}`.
        2. The input data is rounded to kg (no decimals) by a conversion to int32.
        """
        self._kfactor = self.raster_factory(
            raster_input, flag_mask=True, flag_clip=True
        )
        cond = self._kfactor.arr != self._kfactor.rp.nodata
        cond_neg = cond & (self._kfactor.arr < 0)
        if np.any(cond_neg):
            msg = (
                "Negative values detected in K-factor raster, setting negative "
                "values to 0."
            )
            warnings.warn(msg, UserWarning)
            self._kfactor.arr[cond_neg] = 0.0
        self._kfactor.arr[cond] = self._kfactor.arr[cond] * 1000
        self._kfactor.arr[cond] = np.round(self._kfactor.arr[cond])
        self._kfactor.arr = self._kfactor.arr.astype(np.int32)

    @property
    def hydrological_soil_group(self):
        """CN hydrological soil group raster

        This raster (int) holds the four categories (see [2]_):

        - *A* (value 1): Soils in this group have low runoff potential when thoroughly
          wet.
        - *B* (value 2): Soils in this group have moderately low runoff potential when
          thoroughly wet.
        - *C* (value 3): Soils in this group have moderately high runoff potential when
          thoroughly wet.
        - *D* (value 4): Soils in this group have high runoff potential when thoroughly
          wet.

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
        """
        return self._hydrosoilgroup

    @hydrological_soil_group.setter
    # @valid_req_property(req_property_name="dtm", mandatory=True)
    def hydrological_soil_group(self, raster_input):
        """Assign CN soil raster

        This raster (int) holds the four categories (see [2]_):

        - *A* (value 1): Soils in this group have low runoff potential when thoroughly
          wet.
        - *B* (value 2): Soils in this group have moderately low runoff potential when
          thoroughly wet.
        - *C* (value 3): Soils in this group have moderately high runoff potential when
          thoroughly wet.
        - *D* (value 4): Soils in this group have high runoff potential when thoroughly
          wet.

        Parameters
        ----------
        raster_input: Pathlib.Path, str or numpy.array
            File path/array base landuse raster (class) with values *1*: A, *2*: B,
            *3*: C and *4*: D.

        References
        ----------
        .. [1] NRCS, 2004. Hydrologic soil-cover complexes (chapter 9).
        .. [2] NRCS, 2009. Hydrologic soil groups (chapter 7).
        """
        self._hydrosoilgroup = self.raster_factory(
            raster_input, flag_mask=False, flag_clip=True
        )
        raster_discrete_value_error(
            self._hydrosoilgroup.arr,
            "Hydrological soil group",
            [self._hydrosoilgroup.rp.nodata, 1, 2, 3, 4],
            [
                "nodata",
                "A: Soils with low runoff potential when thoroughly wet.",
                "B: Soils with moderately low runoff potential when thoroughly wet",
                "C: Soils with moderately high runoff potential when thoroughly wet",
                "D: Soils with high  runoff potential when thoroughly wet",
            ],
        )

    @property
    def landuse(self):
        """Getter background land-use raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            The raster can following values:

            - *nodata*: nodata
            - *-5*: open water
            - *-4*: grass
            - *-3*: forest
            - *-2*: infrastructure
            - *10*: agricultural fields
        """
        return self._landuse

    @landuse.setter
    # @valid_req_property(req_property_name="dtm", mandatory=True)
    def landuse(self, raster_input):
        """Assign background land-use raster

        Raster should contain:

            - *-9999*: nodata
            - *-5*: open water
            - *-4*: grass
            - *-3*: forest
            - *-2*: infrastructure
            - *10*: agricultural fields

        Rasters with values outside this range return an error.

        Parameters
        ----------
        raster_input: Pathlib.Path, str or numpy.array
            File path/array base landuse raster (class) with values *-9999*: nodata,
            *-5*: open water, *-4*: grass, *-3*: forest, *-2*: infrastructure, *10*:
            agricultural fields.

        """
        self._landuse = self.raster_factory(
            raster_input, flag_mask=True, flag_clip=True
        )
        raster_discrete_value_error(
            self._landuse.arr,
            "Landuse",
            [self._landuse.rp.nodata, -6, -5, -4, -3, -2, 10],
            [
                "nodata",
                "grass strips",
                "open water",
                "grass",
                " forest",
                "infrastructure",
                "agricultural fields",
            ],
        )

        def plot(nodata=None, *args, **kwargs):
            """Plotting fun"""
            plt.subplots(figsize=[10, 10])

            cmap = colors.ListedColormap(
                [
                    "#64cf1b",
                    "#3b7db4",
                    "#71b651",
                    "#387b00",
                    "#000000",
                    "#00bfff",
                    "#ffffff",
                    "#a47158",
                ]
            )
            bounds = [-6.5, -5.5, -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5]
            norm = colors.BoundaryNorm(bounds, cmap.N)
            arr = self._landuse.arr.copy().astype(np.float32)
            if nodata is not None:
                arr[arr == nodata] = np.nan
            img = plt.imshow(arr, cmap=cmap, norm=norm, *args, **kwargs)
            cbar = plt.colorbar(
                img,
                cmap=cmap,
                norm=norm,
                boundaries=bounds,
                ticks=[-6, -5, -4, -3, -2, -1, 0, 1],
                shrink=0.5,
            )
            cbar.ax.set_yticklabels(
                [
                    "Grass strips (-6)",
                    "Pools (-5)",
                    "Meadow (-4)",
                    "Forest (-3)",
                    "Infrastructure (-2)",
                    "River (-1)",
                    "Outside boundaries (0)",
                    "Agriculture (>0)",
                ]
            )
            plt.show()

        self._landuse.plot = plot

    @staticmethod
    def create_height_contours(rst_input, vct_output):
        """Create height contours line vector based on a DTM raster

        Parameters
        ----------
        rst_input: pathlib.Path
            Input DTM raster
        vct_output: pathlib.Path
            Output height contour line vector
        """
        if rst_input is not None:
            if not vct_output.exists():
                cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_grid", "5"]
                cmd_args += [
                    "-GRID",
                    str(rst_input),
                    "-CONTOUR",
                    str(vct_output),
                    "-ZSTEP",
                    "1",
                ]
                try:
                    execute_subprocess(cmd_args)
                except OSError as e:
                    if "corrupted size vs. prev_size in fastbins" in str(e):
                        try:
                            fiona.open(vct_output)
                        except fiona.errors.DriverError:
                            raise IOError(e)
                create_spatial_index(vct_output)
        else:
            msg = "Inputfile is not valid!"
            raise FileNotFoundError(msg)

    @property
    def catchment_area(self):
        """Total area of the catchment

        Returns
        -------
        float: :math:`m^2`
        """
        return self.vct_catchment.geodata.area

    @property
    # @valid_req_property(req_property_name="vct_river", mandatory=True)
    def river_segment_length(self):
        """Total length of all river segments in the catchment

        Returns
        -------
        float, meter
        """
        return self._vct_river.geodata.length.sum()

    @property
    # @valid_req_property(req_property_name="vct_river", mandatory=True)
    def river(self):
        """Getter river raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Raster containing following values:

            - *-1*: river
            - *0*: no river
            - *-9999*: nodata
        """
        arr = np.where(self._river.arr > 0, -1, self._river.rp.nodata)

        return RasterMemory(arr, self.rp)

    @property
    # @valid_req_property(req_property_name="vct_river", mandatory=False)
    def adjacent_edges(self):
        """Getter dataframe adjacent edges/segment property

        This property is generated by assigning a river line vector to the catchment
        class. Every row indicates a connection between two segments: segment *from*
        (column 1) flows into segment to (column 2). See :ref:`here <watemsedem:adjsegments>`

        Returns
        -------
        pandas.DataFrame
            With columns, flow

                - *from* (int): from segment
                - *to* (int): to segment
        """
        return self._adjacent_edges

    @property
    # @valid_req_property(req_property_name="vct_river", mandatory=False)
    def up_edges(self):
        """Getter dataframe upstream edges/segment property

        This property is generated by assigning a river line vector to the catchment
        class. See :ref:`here <watemsedem:upstrsegments>`

        Returns
        -------
        pandas.DataFrame
            With columns

                - *edge* (int): segment id
                - *upstream edge* (int): segment id of one of the upstream segment of
                  the edge.
                - *proportion* (float): proportion of upstream edge flowing into edge.
                  Lower than 1 when upstream edge flows into two edges.

        """
        return self._up_edges

    @property
    def vct_river(self):
        """Assign river-line vector

        The river vector should be a line-vector file. No specific attributes should be
        defined.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Line vector file.
        """
        return self._vct_river

    @vct_river.setter
    def vct_river(self, vector_input):
        """Assign river-line vector

        The river vector should be a line-vector file. No specific attributes should be
        defined.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Line vector file. With optional

                - *underground* (int): does river section run underground
        """
        # clip
        vct_river_clipped = self.folder.vct_folder / f"river_{self.name}.shp"
        # remove temporary files
        # clean_up_tempfiles(vct_river_clipped, "shp")
        self._vct_river = self.vector_factory(
            vector_input, "LineString", allow_empty=True
        )
        self._vct_river.write(vct_river_clipped)

        # set topologize
        logger.info("Preparing river topology...")
        vct_river_topo = self.folder.vct_folder / f"topology_{self.name}.shp"
        clean_up_tempfiles(vct_river_topo, "shp")
        self._adjacent_edges, self._up_edges = self.topologize_river(
            vct_river_clipped, vct_river_topo, self.mask_raster
        )

        self._vct_river = self.vector_factory(
            vct_river_topo, "LineString", allow_empty=True
        )

        river = self._vct_river.rasterize(
            self.mask_raster, self.rp.epsg, "line_id", "integer", gdal=True
        )
        self._river = self.raster_factory(river, allow_nodata_array=True)
        self._adjacent_edges, self._up_edges, flag = check_segment_edges(
            self.adjacent_edges, self.up_edges, self._river.arr
        )

        # set routing
        if self._vct_river.geodata.shape[0] > 0:
            routing = self._vct_river.rasterize(
                self.mask_raster,
                self.rp.epsg,
                convert_lines_to_direction=True,
                gdal=True,
            )
            routing[routing == self.rp.nodata] = 0
            self._routing = self.raster_factory(routing, flag_mask=False)
        else:
            msg = "River input vector is empty, setting river routing to None"
            logger.info(msg)
            self._routing = AbstractRaster()

    @property
    def tubed_river(self):
        """Assign underground river-line vector

        The river tubed vector should be a line-vector file. No specific
        attributes should be defined.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Line vector file.
        """
        return self._tubed_river

    @tubed_river.setter
    def tubed_river(self, vector_input):
        """Assign underground river-line vector

        The river tubed vector should be a line-vector file. No specific
        attributes should be defined.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Line vector file.
        """
        valid_req_property(
            self,
            current_property="vct_tubed_river",
            req_property_name="vct_river",
            mandatory=True,
        )

        msg = (
            "A vector is assigned to tubed rivers, please "
            "set 'Force Routing' in model option equal to 1."
        )
        warnings.warn(msg)
        vct_tubed_river = self.vector_factory(
            vector_input, "LineString", allow_empty=False
        )
        self._tubed_river = format_forced_routing(
            vct_tubed_river.geodata,
            self.rp.gdal_profile["minmax"],
            self.rp.resolution,
        )
        if not self.vct_river.is_empty():
            if any_equal_element_in_vector(
                self.vct_river.geodata.geometry, vct_tubed_river.geodata.geometry
            ):
                msg = (
                    "Lines in the river (tubed) vector are also present in the "
                    "river vector. Please remove overlapping vectors."
                )
                raise IOError(msg)

    @property
    def routing(self):
        """Getter river routing raster

        See :ref:`here <watemsedem:riverroutingmap>`

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster or None
            Raster containing values from 0 to 8:

            - *0*: do not route further
            - *1*: route to upper pixel
            - *2*: route to upper right pixel
            - *3*: route to right pixel
            - *4*: route to lower right pixel
            - *5*: route to lower pixel
            - *6*: route to lower left pixel
            - *7*: route to left pixel
            - *8*: route to upper left pixel
            - *-9999*: nodata
        """
        return self._routing

    @property
    # @valid_req_property(req_property_name="vct_river", mandatory=False)
    def segments(self):
        """Getter river segments raster

        See :ref:`here <watemsedem:riversegmentfile>`

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Raster containing following values:

            - *>0*: segment_id
            - *-9999*: nodata

        Notes
        -----
        The number of segments is limited to int16.
        """
        self._segments = self.raster_factory(
            self._river.arr, self._river.rp, allow_nodata_array=True
        )
        self._segments.arr = np.where(self._segments.arr < 1, 0, self._segments.arr)
        self._segments.arr = self._segments.arr.astype(np.int16)

        return self._segments

    @staticmethod
    def topologize_river(
        vct_input,
        vct_output,
        rst_mask,
        tolerance=None,
    ):
        """Prepare topology of the river segments with SAGA-GIS

        Parameters
        ----------
        vct_input: str or pathlib.Path
            Line input vector
        vct_output: str of pathlib.Path
            Topologized line output vector
        rst_mask: str or pathlib.Path
            Mask raster (used for mapping)
        tolerance: float
            If not None, the ``TOLERANCE`` command line argument of the saga topology
            command is given this value.

        Returns
        -------
        adjacent_edges: pandas.DataFrame
           See :func:`pywatemsedem.catchment.Catchment.adjacent_edges` and
           :ref:`here <watemsedem:adjsegments>`.
        up_edges: pandas.DataFrame
            See :func:`pywatemsedem.catchment.Catchment.up_edges` and
            :ref:`here <watemsedem:upstrsegments>`.
        """
        cmd_args = ["saga_cmd", SAGA_FLAGS, "topology", "0"]
        cmd_args += ["-INPUTLINES", str(vct_input)]
        cmd_args += ["-OUTPUTLINES", str(vct_output)]
        cmd_args += ["-SYSTEM", str(rst_mask)]
        if tolerance is not None:
            cmd_args += ["-TOLERANCE", str(tolerance)]

        temp_adjacent_edges = tempfile.NamedTemporaryFile(suffix=".txt").name
        temp_up_edges = tempfile.NamedTemporaryFile(suffix=".txt").name

        # temp fix
        try:
            execute_subprocess(cmd_args)
        except OSError as e:
            if "corrupted size vs. prev_size in fastbins" in str(e):
                try:
                    fiona.open(vct_output)
                except fiona.errors.DriverError:
                    raise IOError(e)

        cmd_args = ["saga_cmd", SAGA_FLAGS, "topology", "1"]
        cmd_args += ["-INPUTLINES", str(vct_output)]
        cmd_args += ["-ADJECANT_EDGES", str(temp_adjacent_edges)]
        cmd_args += ["-UPSTREAM_EDGES", str(temp_up_edges)]

        # temp fix
        try:
            execute_subprocess(cmd_args)
        except OSError as e:
            if "corrupted size vs. prev_size in fastbins" in str(e):
                try:
                    pd.read_csv(str(temp_adjacent_edges), sep="\t")
                    pd.read_csv(str(temp_up_edges), sep="\t")
                except fiona.errors.DriverError:
                    raise IOError(e)

        adjacent_edges = pd.read_csv(str(temp_adjacent_edges), sep="\t")
        up_edges = pd.read_csv(str(temp_up_edges), sep="\t")

        clean_up_tempfiles(Path(temp_up_edges), "txt")
        clean_up_tempfiles(Path(temp_adjacent_edges), "txt")

        return adjacent_edges, up_edges

    @property
    def vct_water(self):
        """Getter water polygon vector

        Returns
        -------
        pywatemsedem.geo.vectors.AbstractVector
            Polygon vector with attribute "value"
        """

        return self._vct_water

    @vct_water.setter
    def vct_water(self, vector_input):
        """Assign water polygon vector

        The water vector should be a polygon-vector file. No specific attributes should
        be defined.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Polygon vector file

        Notes
        -----
        Water is mapped to the value of -5 and considered as a sink for sediment in
        WaTEM/SEDEM.
        """
        self._vct_water = self.vector_factory(vector_input, "Polygon")
        self._vct_water.geodata["value"] = -5

    @property
    # @valid_req_property(req_property_name="vct_water", mandatory=False)
    def water(self):
        """Getter water polygon vector

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Raster containing following values:

            - *-5*: open water
            - *-9999*: nodata
        """
        if not self._vct_water.is_empty():
            self._vct_water.geodata["value"] = self._vct_water.geodata["value"].astype(
                float
            )
            water = self._vct_water.rasterize(
                self.mask_raster, self.rp.epsg, "value", "integer", gdal=True
            )
            arr = self.raster_factory(water)
        else:
            arr = AbstractRaster()
        return arr

    @property
    def vct_infrastructure_buildings(self):
        """Getter infrastructure polygon vector

        Returns
        -------
        pywatemsedem.geo.vectors.AbstractVector
            Polygon vector with attribute "paved"
        """

        return self._vct_infrastructure_buildings

    @vct_infrastructure_buildings.setter
    def vct_infrastructure_buildings(self, vector_input):
        """Assign infrastructure polygon vector

        The infrastructure buildings vector should be polygon vector. Buildings are
        defined as all non-road elements.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Polygon vector file
        """
        self._vct_infrastructure_buildings = self.vector_factory(
            vector_input, "Polygon"
        )
        self._vct_infrastructure_buildings.geodata["paved"] = -2

    @property
    # @valid_req_property(
    #    req_property_name="vct_infrastructure_buildings", mandatory=False
    # )
    def infrastructure_buildings(self):
        """Getter rasterized infrastructure polygon vector

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Raster containing following values:

            - *-2*: paved
            - *-9999*: nodata
        """
        self._vct_infrastructure_buildings.geodata[
            "paved"
        ] = self._vct_infrastructure_buildings.geodata["paved"].astype(float)

        infra = self._vct_infrastructure_buildings.rasterize(
            self.mask_raster, self.rp.epsg, col="paved", gdal=True
        )

        return self.raster_factory(infra)

    @property
    # @valid_req_property(req_property_name="vct_infrastructure_roads", mandatory=False)
    def infrastructure_roads(self):
        """Getter rasterized infrastructure polygon vector

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Raster containing following values:

            - *-2*: paved
            - *-7*: paved
            - *-9999*: nodata
        """
        self._vct_infrastructure_roads.geodata[
            "paved"
        ] = self._vct_infrastructure_roads.geodata["paved"].astype(float)

        arr = self._vct_infrastructure_roads.rasterize(
            self.mask_raster, self.rp.epsg, col="paved", gdal=True
        )
        return self.raster_factory(arr)

    @property
    def vct_infrastructure_roads(self):
        """Getter infrastructure line vector"""
        return self._vct_infrastructure_roads

    @vct_infrastructure_roads.setter
    def vct_infrastructure_roads(self, vector_input):
        """Assign infrastructure line vector

        The infrastructure roads vector should be polygon vector. Paved and non-paved
        roads can be defined:

            - *-2*: paved
            - *-7*: non-paved

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Line vector file with allowed (optional) column 'paved': allowed values -2
            (paved) and -7 (non-paved).
        """
        self._vct_infrastructure_roads = self.vector_factory(vector_input, "LineString")
        geodata = self._vct_infrastructure_roads.geodata
        if "paved" in self._vct_infrastructure_roads.geodata:
            attribute_discrete_value_error(
                geodata,
                "Infrastucture roads",
                "paved",
                {self.rp.nodata, -2, -7},
                {"nodata", "paved", " non-paved"},
            )
        else:
            geodata["paved"] = -2

        self._vct_infrastructure_roads.geodata = geodata

    @property
    def infrastructure(self):
        """Get infrastucture raster

        Get rasterized polygon and line vectors. The procedure adds the line data
        (roads) to the  polygon data (buildings). As such buildings are considered as
        the base map.

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Raster containing following values:

            - *-2*: paved
            - *-7*: paved

        Notes
        -----
        Note that current module allows to either define a roads (1), buildings (2)
        or roads and buildings (3). If no roads or buildings are defined, an error is
        thrown."""

        if not self.infrastructure_roads.is_empty():
            if not self.infrastructure_buildings.is_empty():
                arr1 = self.infrastructure_roads.arr.copy()
                arr2 = self.infrastructure_buildings.arr.copy()
                cond1 = arr1 == self.infrastructure_roads.rp.nodata
                cond2 = arr2 != self.infrastructure_buildings.rp.nodata
                arr = np.where(cond1 & cond2, arr2, arr1)
                arr = np.where(
                    arr != self.infrastructure_buildings.rp.nodata, arr, self.rp.nodata
                )
                self._infrastructure = RasterMemory(arr, self.rp)
            else:
                self._infrastructure = self.infrastructure_roads
        else:
            if not self.infrastructure_buildings.is_empty():
                self._infrastructure = self.infrastructure_buildings
            else:
                msg = (
                    "First define infrastructure lines (roads) or/and polygons "
                    "(buildings) before calling infrastructure property!"
                )
                raise IOError(msg)

        def plot(nodata=None, *args, **kwargs):
            """Plotting fun"""
            fig, ax = plt.subplots(figsize=[10, 10])
            """Plot infrastructure"""
            arr_plot = self._infrastructure.arr.copy().astype(np.float32)
            if nodata is not None:
                arr_plot = np.where(arr_plot != nodata, 1, arr_plot)
                arr_plot = np.where(arr_plot == nodata, 0, arr)

            im = ax.imshow(arr_plot, *args, **kwargs)
            fig.colorbar(im, ax=ax, shrink=0.5)

        self._infrastructure.plot = plot

        return self._infrastructure

    def _calculate_soil_statistics(self):
        """Calculate statistics of K-factor map

        Calculates the area (m²) and the relative amount of appearance of
        every K-factor in the catchment. The results are written to a csv-file
        "K_factor_stats_[resolution].csv" in ``self.cfolder.rst_folder ``.

        #TODO

        """
        fname = self.folder.rst_folder / f"K_factor_stats_{self.rp.resolution}.csv"
        if not fname.exists():
            msg = "Calculating K-factor statistics"
            logger.info(msg)
            df = get_df_area_unique_values_array(self.kfactor.arr, self.rp.resolution)
            df.drop(df[df["values"] == self.rp.nodata].index, inplace=True)
            total_area = df["area"].sum()
            df["rel_area"] = (df["area"] / total_area) * 100
            df.to_csv(fname, index=False)

    def create_folder_structure(self):
        """Creates a fixed folder structure for the model data

        The folder layout will have the following directory structure:

        ::

            ├── homefolder
            │    └── bekken folder / catchment folder
            │         ├── Rsts
            │         ├── Shps

        """
        logger.info("Aanmaken folderstructuur bekken...")
        self.folder = CatchmentFolder(Path(self.name), self.rp.resolution)
        self.folder.create_all()
