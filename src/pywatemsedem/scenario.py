import logging

# Standard libraries
import subprocess
import warnings
from copy import deepcopy
from functools import wraps

import geopandas as gpd
import numpy as np
import pandas as pd

from pywatemsedem.cfactor import create_cfactor_cnws
from pywatemsedem.cn import process_cn_raster
from pywatemsedem.geo.rasters import RasterMemory
from pywatemsedem.geo.utils import nearly_identical, saga_intersection
from pywatemsedem.io.folders import ScenarioFolders
from pywatemsedem.io.ini import IniFile
from pywatemsedem.ktc import create_ktc_cnws
from pywatemsedem.parcelslanduse import ParcelsLanduse, get_source_landuse

from .buffers import (
    filter_outlets_in_arr_extension_id,
    process_buffer_outlets,
    process_buffers_in_river,
)
from .errors import (
    attribute_continuous_value_error,
    attribute_discrete_value_error,
    missing_attribute_error_in_vct,
)
from .grasstrips import create_grassstrips_cnws
from .templates import InputFileName
from .tools import format_forced_routing, zip_folder

inputfilename = InputFileName()
DEFAULT_CFACTOR = 0.37
logger = logging.getLogger(__name__)


def valid_vct_endpoints(func):
    """Check if endpoints vector are defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.choices.dict_model_options["Include sewers"] == 1:
            if self._vct_endpoints is None:
                msg = (
                    "Please define endpoints line vector (see "
                    "vct_endpoints-property) or set 'Include sewers' in "
                    "'dict_model_options' to 0!!"
                )
                raise IOError(msg)

            elif "SewerInletEff" not in self.choices.dict_variables:
                msg = "Please define a 'SewerInletEff' in 'dict_variables'."
                raise KeyError(msg)
            return func(self, *args, **kwargs)
        else:
            msg = "Please define 'Include sewers' in 'dict_model_options' to 1."
            raise IOError(msg)

    return wrapper


def valid_vct_parcels(func):
    """Check if parcels vector are defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self._vct_parcels is None:
            msg = "Please define parcels polygon vector (see vct_parcels-property)!"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_source_measure(func):
    """Check if source measure vector are defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self._vct_source_measure is None:
            msg = (
                "Please define source measure polygon vector (see "
                "vct_source_measure-property)!"
            )
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_grass_strips(func):
    """Check if grass strips vector is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.choices.dict_ecm_options["UseGras"] == 1:
            if self._vct_grass_strips is None:
                msg = "No grass strips defined, but option 'UseGras' equal to 1."
                raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_buffers(func):
    """Check if buffers vector is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.choices.dict_ecm_options["Include buffers"] == 1:
            if self._vct_buffers is None:
                msg = "No buffers defined, but option 'Include buffers' equal to 1."
                warnings.warn(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_outlets(func):
    """Check if outlet vector is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self._vct_outlets is None:
            msg = "Please define outlets point vector (see vct_outlets-property)!"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_dtm(func):
    """Check if you have defined a DTM."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm.dtm is None:
            msg = "Please first define a DTM!"
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


def valid_kfactor(func):
    """Check if you have defined a K-factor raster."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm.kfactor is None:
            msg = "Please first define a K-factor raster!"
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


def valid_pfactor(func):
    """Check if you have defined a P-factor raster."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm.pfactor is None:
            msg = "Please first define a P-factor raster!"
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


def valid_cnws_input(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.choices.version == "CN-WS":
            if self.cn is None:
                msg = (
                    "Please create a valid CN-raster with *prepare_cnws_model_input*"
                    " for a WaTEM/SEDEM run."
                )
                raise IOError(msg)

        if self.ktc is None:
            if self.choices.dict_model_options["UserProvidedKTC"] == 1:
                msg = (
                    "Please create a valid kTC-raster with *prepare_cnws_model_input*."
                )
                raise IOError(msg)

        if self.cfactor is None:
            msg = (
                "Please create a valid c-factor-raster with "
                "*prepare_cnws_model_input*."
            )
            raise IOError(msg)

        if self.composite_landuse is None:
            msg = (
                "Please define a WaTEM/SEDEM-landuse-raster with "
                "*prepare_cnws_model_input*."
            )
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


def valid_ini(func):
    """Check if you have defined a valid ini-file."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.ini is None:
            msg = "Please define an ini-file with *create_ini_file*."
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


class CNWSException(Exception):
    """Exception from WaTEM/SEDEM pre- and postprocessing scripts"""


class Scenario:
    """Construct a new Scenario instance

    The catchment class holds all dynamic information for a scenario, for a given year.
    The class considers all data of which the content is user-option-dependent (i.e.
    :class:`pywatemsedem.userchoices.UserChoices`.

    - *vct_parcels*: polygon vector of parcels with obligated columns 'LANDUSE',
      'C_crop' and 'CODE'.
    - *vct_grass_strips*: polygon vector of grass stips with obligated columns
      'scale_ktc' and 'width'.
    - *vct_buffers*: polygon vector of grass stips with obligated columns 'buffercap'
      (CN), 'hdam' (CN), 'hknijp' (CN), 'dknijp' (CN), 'qcoef' (CN), 'boverl' (CN),
      'eff' (WS).
    - *vct_bufferoutlets*: #TODO
    - *vct_outlets*: point vector.
    - *vct_ditches*: #TODO
    - *vct_conductive_dams*: #TODO
    - *vct_force_routing*: line vector.
    - *vct_endpoints*: line vector, with optional columns 'efficiency' and 'type_id'.
    """

    def __init__(self, catchm, year, scenario_nr, userchoices):
        """Generate scenario instance with catchment, year, scenario number and user
        choices.

        Parameters
        ----------
        catchm: pywatemsedem.core.catchment.Catchment
            Instance of :class:`pywatemsedem catchment <pywatemsedem.catchment.Catchment>`
            containing the catchment characteristics.
        year: int
            Simulation year
        scenario_nr: int
            Identifier number of the scenario.
        userchoices : pywatemsedem.core.userchoices.UserChoices
            Containing the pywatemsedem model settings.
        """
        # Init factories from catchm instance
        self.catchm = catchm
        self.rp = self.catchm.rp

        # Initalize
        self.vector_factory = self.catchm.vector_factory
        self.raster_factory = self.catchm.raster_factory

        # properties
        self._grass_strips = None  # raster
        self._vct_grass_strips = None  # vector
        self._vct_buffers = None  # vector
        self._vct_bufferoutlets = None  # vector
        self._vct_ditches = None
        self._vct_condictive_dams = None
        self._vct_source_measures = None
        self._vct_endpoints = None
        self._endpoints = None
        self._endpoints_id = None
        self._vct_force_routing = None
        self._vct_outlets = None
        self._outlets = None
        self._vct_parcels = None

        # derivate properties
        self._ktc = None
        self._cn = None
        self._cn_table = None
        self._cfactor = None
        self._composite_landuse = None

        # assign scenario number and user choices
        self.scenario_nr = scenario_nr
        self.year = year
        self.choices = deepcopy(userchoices)
        self.rst_outlet = None
        self.ini = None

        # initialisation functionalities
        self.temporal_resolution()
        self.create_folder_structure()
        self.copy_data_layers_to_scenario_folder()

    def create_folder_structure(self):
        """#TODO"""

        self.scenario_folder_init = (
            self.catchm.folder.home_folder / f"scenario_" f"{self.scenario_nr}"
        )

        self.sfolder = ScenarioFolders(self.catchm.folder, self.scenario_nr, self.year)
        self.sfolder.create_all()

    @valid_kfactor
    @valid_dtm
    @valid_pfactor
    def copy_data_layers_to_scenario_folder(self):
        """#TODO"""
        self.catchm.kfactor.write(
            self.sfolder.cnwsinput_folder / inputfilename.kfactor_file
        )
        self.catchm.dtm.write(
            self.sfolder.cnwsinput_folder / inputfilename.dtm_file, nodata=-99999
        )
        self.catchm.pfactor.write(
            self.sfolder.cnwsinput_folder / inputfilename.pfactor_file
        )
        self.catchm.adjacent_edges.to_csv(
            self.sfolder.cnwsinput_folder / inputfilename.adjacentedges_file,
            sep="\t",
            index=False,
        )
        self.catchm.up_edges.to_csv(
            self.sfolder.cnwsinput_folder / inputfilename.upedges_file,
            sep="\t",
            index=False,
        )

        if self.choices.dict_model_options["River Routing"] == 1:
            self.choices.dict_output["Output per river segment"] = 1
            self.catchm.routing.write(
                self.sfolder.cnwsinput_folder / inputfilename.routing_file
            )
        # if self.choices.dict_output["Output per river segment"] == 1:
        self.catchm.segments.write(
            self.sfolder.cnwsinput_folder / inputfilename.segments_file
        )

        self.catchm.mask.write(self.sfolder.cnwsinput_folder / inputfilename.mask_file)

    def temporal_resolution(self):
        """Calculates for which years and seasons the scenario needs data.

        Based on the defined choices in the
        :py:class:`CNWS.UserChoices <pywatemsedem.CNWS.UserChoices>` 'begin_jaar',
        'begin_maand' and, in case of CNWS, 'Endtime model'.
        """
        if (self.choices.version == "WS") or self.choices.version == "Only Routing":
            self.season = "spring"
        else:
            if self.choices.dict_variables["begin_maand"] in [1, 2, 3]:
                self.season = "winter"
            elif self.choices.dict_variables["begin_maand"] in [4, 5, 6]:
                self.season = "spring"
            elif self.choices.dict_variables["begin_maand"] in [7, 8, 9]:
                self.season = "summer"
            elif self.choices.dict_variables["begin_maand"] in [10, 11, 12]:
                self.season = "fall"

    @property
    def vct_parcels(self):
        """Getter parcels polygon vector"""

        return self._vct_parcels

    @vct_parcels.setter
    def vct_parcels(self, vector_input):
        """Assign parcels polygon vector

        The parcels vector should be polygon vector. Should contain a definition of
        land-use (column "LANDUSE"):

            - *-4*: grass land
            - *-3*: forest
            - *-2*: infrastructure (farms)
            - *-9999*: agricultural land

        Should contain a definition of crop code (column "CODE").

        Should contain a definition of the crop C-factor (column 'C_crop', see
        :ref:`here <watemsedem:cmap>`.):

            - *[0,1]*: C-factor for crop.
            - *NULL*: no C-factor defined.

        Should contain a defiction of the C-reduction (column 'C_reduction'), used
        in case of source-oriented measures.

        Can contain a 'NR' column which is the identification ID of the individual
        parcel.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Polygon vector

            - *LANDUSE* (int): landuse value (-4: grass land, -3: forest,
               -2: infrastructure (farms), -9999: agricultural land).
            - *C_crop* (float): C-factor for crop, valid for considered time period
              ([0,1], NULL-values allowed).
            - *NR* (int, optional): id.
            - *C_reduction* (float): C-reduction values,  C-factor is reduced with this
              percentage when source-oriented measures are used.

        Notes
        -----
        The C-value for crops are defined as the C-factor that is valid as value for
        the coupled crop given a time period (e.g. average C-factor for potato for one
        year, or average C-factor for potato for the month April).
        """
        self._vct_parcels = self.vector_factory(
            vector_input, "Polygon", allow_empty=True
        )

        missing_attribute_error_in_vct(
            self._vct_parcels.geodata,
            "Parcels",
            {"C_crop", "CODE", "LANDUSE", "C_reduct"},
        )
        attribute_continuous_value_error(
            self._vct_parcels.geodata, "Parcels", "C_crop", lower=0, upper=1
        )
        attribute_continuous_value_error(
            self._vct_parcels.geodata, "Parcels", "C_reduct", lower=0, upper=1
        )
        attribute_discrete_value_error(
            self._vct_parcels.geodata,
            "Parcels",
            "LANDUSE",
            {-9999, -2, -3, -4, -5},
            classes={"agriculture", "infrastructure", "forest", "grass land", "water"},
        )

        if "NR" not in self._vct_parcels.geodata.columns:
            self._vct_parcels.geodata["NR"] = range(
                0, len(self._vct_parcels.geodata), 1
            )

        self._vct_parcels.geodata["LANDUSE"] = self._vct_parcels.geodata[
            "LANDUSE"
        ].astype(float)

    @property
    def parcels(self):
        """Get parcels raster

        Raster contains id's (defined in "NR", if not defined: according to
        id sequence in vector). The parcel raster is limited by the value of 32767
        (int16). If values are higher, then these are limited to 32767.

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Int16 raster with values:

            - *>0 and <=32767*: parcel id
            - *-9999*: nodata
        """
        if self.parcels_ids is not None:
            arr = self.parcels_ids.arr.copy()
            if np.any(arr > 32767):
                msg = (
                    "Parcels raster has values higher than the maximum allowed number "
                    "for WaTEM/SEDEM definition (i.e. 32767). Setting values above "
                    "32767 to 32767."
                )
                warnings.warn(msg)
            arr = np.where(arr > 32767, 32767, arr)
            arr = arr.astype(np.int16)

            return self.raster_factory(arr)
        else:
            return None

    @property
    def parcels_ids(self):
        """Getter rasterized parcels polygon vector

        Raster contains id's (defined in "NR", if not defined: according to
        id sequence in vector).

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster, else None
            Float64 raster with values:

            - *>0*: parcel id
            - *-9999*: nodata
        """
        if self._vct_parcels is not None:
            arr = self._vct_parcels.rasterize(
                self.catchm.mask_raster, self.rp.epsg, col="NR", gdal=True
            )
            return self.raster_factory(arr)
        else:
            return None

    @property
    def parcels_landuse(self):
        """Getter rasterized parcels polygon vector

        Raster contains landuse (defined in column "LANDUSE")

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster, else None
            Float64 raster with values:

            - *-4*: grass land
            - *-3*: forest
            - *-2*: infrastructure (farms)
            - *-9999*: agricultural land

        Notes
        -----
        If all parcels have a landuse code of -9999, then a None is returned
        (no addition to landuse).
        """
        if self._vct_parcels is not None:
            arr = self.vct_parcels.rasterize(
                self.catchm.mask_raster, self.rp.epsg, col="LANDUSE", gdal=True
            )
            if np.all(arr == self.rp.nodata):
                return None
            else:
                return self.raster_factory(arr)
        else:
            return None

    @property
    def vct_grass_strips(self):
        """Getter grass strips polygon vector"""

        return self._vct_grass_strips

    @vct_grass_strips.setter
    def vct_grass_strips(self, vector_input):
        """Assign grass strips polygon vector

        Grass strips are appointed the value -6 in the WaTEM/SEDEM parcels landuse
        raster. In addition, C-factors and kTC-values are assigned to grass strips
        pixels according to their width, see also
        :func:`pywatemsedem.cfactor.create_cfactor_cnws` and
        :func:`pywatemsedem.ktc.create_ktc_cnws`

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Polygon vector

            - *width* (int): meter width of grass strip (shortest side!)
            - *scale_ktc* (int): either 0 (scale or 1), if not kTC is not scaled, then
              the ktc_low (see :class:`pywatemsedem.userchoices.UserChoices`) is used,
              see :func:`pywatemsedem.ktc.scale_ktc_gdf_grass_strips`

        Notes
        -----
        Grass strips are defined by a length and a width, the width is considered to be
        the shortest side, whereas the length is considerd to be the longest side.
        """
        self._vct_grass_strips = self.vector_factory(vector_input, "Polygon")
        missing_attribute_error_in_vct(
            self._vct_grass_strips.geodata, "Grass strips", {"width", "scale_ktc"}
        )
        attribute_continuous_value_error(
            self._vct_grass_strips.geodata, "Grass strips", "width", lower=0
        )
        attribute_discrete_value_error(
            self._vct_grass_strips.geodata,
            "Grass strips",
            "scale_ktc",
            {0, 1},
            classes={
                "do not scale ktc grass strip according to width",
                "scale ktc according to width",
            },
        )

        if "NR" not in self._vct_grass_strips.geodata.columns:
            self._vct_grass_strips._geodata["NR"] = np.arange(
                0, len(self._vct_grass_strips._geodata), 1
            )
        self._vct_grass_strips.geodata["NR"] = self._vct_grass_strips.geodata[
            "NR"
        ].astype(float)
        arr = self.vct_grass_strips.rasterize(
            self.catchm.mask_raster,
            self.rp.epsg,
            col="NR",
            nodata=-9999,
            gdal=True,
        )
        self._grass_strips = self.raster_factory(arr)

    @property
    @valid_vct_grass_strips
    def grass_strips(self):
        """Grass strips raster getter"""
        if self.choices.dict_ecm_options["UseGras"] == 0:

            msg = (
                "'UseGras' in 'dict_ecm_options' is equal to 0. Will not include grass"
                " strips."
            )
            warnings.warn(msg)
            return None
        else:
            return self._grass_strips

    @grass_strips.setter
    def grass_strips(self, raster_input):
        """Grass strips raster setter

        Parameters
        ----------
        raster_input: Pathlib.Path, str or numpy.ndarray
            See :func:`pywatemsedem.catchment.raster_factory`.
        """
        self._grass_strips = self.raster_factory(raster_input)

    @property
    def vct_buffers(self):
        """Getter buffers polygon vector"""
        return self._vct_buffers

    @vct_buffers.setter
    def vct_buffers(self, vector_input):
        """Assign buffers polygon vector

        Buffers are considered in WaTEM/SEDEM as a raster defined by an id (outlet) and
        extension id (buffer extent, i.e. number of pixels surrounding the outlet). In
        addition, a number of properties of the buffers are assigned (i.e. 'buffercap',
        'hdam', 'hknijp', 'dknijp', 'qcoef', 'boverl', 'eff').

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Polygon vector, with columns

            - *id* (WS)
            - *buffercap* (CN)
            - *hdam* (CN)
            - *hknijp* (CN)
            - *dknijp* (CN)
            - *qcoef* (CN)
            - *boverl* (CN)
            - *eff* (WS)

            For an explanation of the columns, see :ref:`here <watemsedem:buffermap>`
        """

        req_col = {
            "buffercap",
            "hdam",
            "hknijp",
            "dknijp",
            "qcoef",
            "boverl",
            "eff",
        }
        self._vct_buffers = self.vector_factory(vector_input, "Polygon")
        missing_attribute_error_in_vct(self._vct_buffers.geodata, "Buffers", req_col)
        attribute_continuous_value_error(
            self._vct_buffers.geodata, "Buffers", "eff", lower=0, upper=100
        )
        self._vct_buffers.geodata["id"] = np.arange(
            1.0, len(self.vct_buffers.geodata) + 1, 1
        )

        if self.choices.dict_ecm_options["Include buffers"] == 0:
            msg = (
                "Include buffers' in 'dict_ecm_options' is equal to 0. Will not "
                "include buffers."
            )
            warnings.warn(msg)

    @property
    def vct_bufferoutlets(self):
        """Getter infrastructure polygon vector"""
        return self._vct_bufferoutlets

    @vct_bufferoutlets.setter
    def vct_bufferoutlets(self, vector_input):
        """Assign buffer outlets vector

        #TODO

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            See :func:`pywatemsedem.catchment.vector_factory`.
        """
        self._vct_bufferoutlets = self.vector_factory(vector_input, "Polygon")

    @property
    @valid_vct_buffers
    def buffers_exid(self):
        """Getter buffer extension Id raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
        """
        arr = self.vct_buffers.rasterize(
            self.catchm.mask_raster, 31370, "buf_exid", gdal=True
        )

        return self.raster_factory(arr)

    @property
    def bufferoutlet(self):
        """Getter buffer outlet raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
        """
        if self.vct_bufferoutlets is not None:
            self.vct_bufferoutlets.geodata = process_buffer_outlets(
                self.vct_bufferoutlets.geodata, self.vct_buffers.geodata
            )
            arr = np.where(self.catchm.vct_river.arr == -1, 0, self.bufferoutlet)
        else:
            arr = np.zeros(self.catchm.dtm.arr.shape)

        return self.raster_factory(arr)

    @property
    @valid_vct_buffers
    def buffers(self):
        """Getter for buffer

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster

        Notes
        -----
        1. Overlapping buffers with rivers (complete overlap) are removed.
        2. Buffer outlet vector can be used to define the buffer outlets, if not used
           then the pixel with the lowest DTM height value is used as outlet for a
           buffer.
        """
        arr = None
        if self.choices.dict_ecm_options["Include buffers"] == 0:
            msg = (
                "Option 'Include buffers' in erosion control measure options is 0, "
                "returning None"
            )
            warnings.warn(msg)
        elif self.vct_buffers is None:
            self.choices.dict_ecm_options["Include buffers"] = 0
        else:
            self.vct_buffers.geodata = assign_buffer_id_to_df_buffer(
                self.vct_buffers.geodata
            )
            if self.catchm.vct_river is not None:
                arr, self.vct_buffers.geodata = process_buffers_in_river(
                    self.vct_buffers.geodata,
                    self.buffers_exid.arr,
                    self.catchm.river.arr,
                    self.rp.gdal_profile["nodata"],
                )
                if self.vct_buffers.geodata.empty:  # if all buffers are removed
                    msg = (
                        "All buffers pixels overlap with the river, removing and not "
                        "including buffers in simulation."
                    )
                    logger.warning(msg)
                    self.choices.dict_ecm_options["Include buffers"] = 0
                    arr = None
            if arr is not None:
                arr = filter_outlets_in_arr_extension_id(
                    self.vct_buffers.geodata, arr, self.catchm.dtm.arr, None
                )
                arr = np.where(arr == self.catchm.rp.nodata, 0, arr).astype("int16")
                arr = self.raster_factory(arr, flag_mask=False)

        return arr

    @property
    def vct_ditches(self):
        """Getter ditches lines vector"""
        return self._vct_ditches

    @vct_ditches.setter
    def vct_ditches(self, vector_input):
        """Setter ditches lines vector

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            See :func:`pywatemsedem.catchment.vector_factory`.
        """
        self._vct_ditches = self.vector_factory(vector_input, "Polygon")

    @property
    def vct_conductive_dams(self):
        """Getter conductive dams vector"""
        return self._vct_condictive_dams

    @vct_conductive_dams.setter
    def vct_conductive_dams(self, vector_input):
        """Setter conductive dams lines vector

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            See :func:`pywatemsedem.catchment.vector_factory`.
        """
        self._vct_condictive_dams = self.vector_factory(vector_input, "Polygon")

    def conductive_dams(self):
        """Getter conductive dams

        Returns
        -------
        pywatemsedem.geo.raster.AbstractRaster
        """
        arr = self.vct_conductive_dams.rasterize(
            self.catchm.mask_raster,
            self.rp.epsg,
            convert_lines_to_direction=True,
            gdal=True,
        )
        if self.buffers is not None:
            # if there is a buffer on the same pixel of a ditch, remove the ditch
            arr = np.where(self.buffers.arr != 0, 0, arr)
        if self.catchm.vct_river is not None:
            arr = np.where(self.river.arr == -1, 0, arr)

        return self.raster_factory(arr)

    def ditches(self):
        """Getter ditches

        Returns
        -------
        pywatemsedem.geo.raster.AbstractRaster
        """
        arr = self.vct_ditches.rasterize(
            self.catchm.mask_raster,
            self.rp.epsg,
            convert_lines_to_direction=True,
            gdal=True,
        )
        if self.buffers is not None:
            # if there is a buffer on the same pixel of a ditch, remove the ditch
            arr = np.where(self.buffers.arr != 0, 0, arr)
        if self.catchm.vct_river is not None:
            arr = np.where(self.river.arr == -1, 0, arr)

        return self.raster_factory(arr)

    @property
    def vct_outlets(self):
        """Getter outlets vector

        Returns
        -------
        object
        """
        return self._vct_outlets

    @vct_outlets.setter
    def vct_outlets(self, vector_input):
        """Set vector outlet point

        With this setter, one can define the outlet point of a catchment. This outlet
        is reflected in the output of WaTEM/SEDEM (see
        :ref:`here <watemsedem:totalsedimenttxt>`).

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Point vector, with optional column 'NR'.
        """
        self._vct_outlets = self.vector_factory(vector_input, "Point")

        if len(self._vct_outlets.geodata) == 0:
            msg = r"Defined outlets are not in catchment."
            logger.warning(msg)
            self._vct_outlets = None
        else:
            if "NR" not in self.vct_outlets.geodata:
                self._vct_outlets.geodata["NR"] = np.arange(
                    1.0, len(self.vct_outlets.geodata) + 1, 1
                )
            self._vct_outlets.geodata["NR"] = self._vct_outlets.geodata["NR"].astype(
                float
            )

    @property
    @valid_vct_outlets
    def outlets(self):
        """Getter outlets

        Returns
        -------
        pywatemsedem.geo.raster.AbstractRaster
        """

        arr = self.vct_outlets.rasterize(
            self.catchm.mask_raster, self.rp.epsg, col="NR", gdal=True
        )
        self._outlets = self.raster_factory(arr)
        self._outlets.arr = self._outlets.arr.astype(np.int16)
        return self._outlets

    @property
    def vct_force_routing(self):
        """#todo

        Returns
        -------

        """
        return self._vct_force_routing

    @vct_force_routing.setter
    def vct_force_routing(self, vector_input):
        """Appoint force routing

        Parameters
        ----------
        vector_input: str | pathlib.Path | geopandas.GeoDataFrame
            See :func:`pywatemsedem.catchment.vector_factory`.
        """
        vct_forced_routing = self.vector_factory(
            vector_input, "LineString", allow_empty=True
        )
        self._vct_force_routing = format_forced_routing(
            vct_forced_routing.geodata,
            self.catchm.rp.gdal_profile["minmax"],
            self.catchm.rp.resolution,
        )

    @property
    def vct_endpoints(self):
        """Getter endpoints lines vector"""
        return self._vct_endpoints

    @vct_endpoints.setter
    def vct_endpoints(self, vector_input):
        """Assign endpoints line vector

        Endpoints are defined as sink objects, in which sediment is captured and not
        transported further. The endpoints should be line vector.

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            Line vector with optional column

            - *type_id* (int): describes the different classes of endpoints (e.g. 1:
              sewers, 2: ditches, ...)
            - *efficiency* (float): sediment trap efficiency (%) .

        Notes
        -----
        1. In the WaTEM/SEDEM pywatemsedem engine, endpoints are named "sewers", see also
           :ref:`here <watemsedem:sewermapfile>`. Note that in pywatemsedem, type of endpoints can
           be defined (ditches, sewers).
        """
        self._vct_endpoints = self.vector_factory(
            vector_input, "LineString", allow_empty=True
        )

        if "type_id" not in self._vct_endpoints.geodata.columns:
            msg = "No 'type_id' assigned, assuming one type of endpoint with id 1."
            warnings.warn(msg)
            self._vct_endpoints["type_id"] = 1
        else:
            if np.any(self._vct_endpoints.geodata["type_id"].isnull()):
                msg = "Please define a 'type_id' for every record."
                raise ValueError(msg)

        if "efficiency" not in self._vct_endpoints.geodata.columns:
            self._vct_endpoints.geodata["efficiency"] = np.nan
        else:
            attribute_continuous_value_error(
                self._vct_endpoints.geodata, "Endpoints", "efficiency", 0, 1
            )

        self._vct_endpoints.geodata["efficiency"] = self._vct_endpoints.geodata[
            "efficiency"
        ].astype(np.float64)

    @property
    @valid_vct_endpoints
    def endpoints_id(self):
        """Getter endpoints id raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Float64 raster with values:

            - *0*: no endpoint
            - *not equal to 0*: id.
        """
        arr_id = self.vct_endpoints.rasterize(
            self.catchm.mask_raster, 31370, col="type_id", gdal=True
        )
        arr_id[arr_id == self.rp.nodata] = 0

        return self.raster_factory(arr_id, flag_mask=False, flag_clip=False)

    @property
    @valid_vct_endpoints
    def endpoints(self):
        """Getter endpoints efficiency raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
            Float64 raster with values in [0,1] efficiency (in decimal).

        Notes
        -----
        Id's equal to one are converted to 0 when
        self.choices.dict_model_options["OnlyInfraSewers"] is equal to 1.
        """
        cond = self._vct_endpoints.geodata["efficiency"].isnull()
        if np.any(cond):
            # in decimals
            self._vct_endpoints.geodata.loc[cond, "efficiency"] = float(
                self.choices.dict_variables["SewerInletEff"]
            )
            msg = (
                "The efficiency is not defined for all sewer line strings, assigning"
                f" 'SewerInletEff'-value defined in user choices 'variables' "
                f"({self.choices.dict_variables['SewerInletEff']*100} %)."
            )
            warnings.warn(msg)

        self.vct_endpoints.geodata["efficiency"] = self.vct_endpoints.geodata[
            "efficiency"
        ].astype(float)
        arr = self.vct_endpoints.rasterize(
            self.catchm.mask_raster,
            31370,
            nodata=self.rp.nodata,
            col="efficiency",
            gdal=False,
        )

        arr[arr == self.rp.nodata] = 0
        if self.choices.dict_model_options["OnlyInfraSewers"] == 1:
            cond = (self.catchm.infrastructure.arr != -2) & (self.endpoints_id.arr == 1)
            cond_mask = (cond) & (self.catchm.mask.arr != 0)
            arr[cond_mask] = 0
        arr[self.catchm.river.arr == -1] = 0
        return self.raster_factory(arr, flag_mask=False, flag_clip=False)

    @property
    def cn_table(self):
        """Set/getter CN-table

        Returns
        -------
        pandas.DataFrame
            with columns:

            - CNmaxID (int): unique identifier, compiled from CN type id (1-11,
              associated to crop), contour plowing measures (0/1/2), hydrological
              conditions ({0,1->3}, {unknown, poor to good}), contour_id (0/1).
            - CNmax_1 (int): CNmax for soil class 1
            - CNmax_2 (int): CNmax for soil class 2
            - CNmax_3 (int): CNmax for soil class 3
            - CNmax_4 (int): CNmax for soil class 4
        """
        return self._cn_table

    @cn_table.setter
    def cn_table(self, df):
        """Set/getter CN-table

        Returns
        -------
        pandas.DataFrame
            with columns:

            - CNmaxID (int): unique identifier, compiled from CN type id (1-11,
              associated to crop), contour plowing measures (0/1/2), hydrological
              conditions ({0,1->3}, {unknown, poor to good}), contour_id (0/1).
            - CNmax_1 (int): CNmax for soil class 1
            - CNmax_2 (int): CNmax for soil class 2
            - CNmax_3 (int): CNmax for soil class 3
            - CNmax_4 (int): CNmax for soil class 4
        """
        if not {"CNmaxID", "CNmax_1", "CNmax_2", "CNmax_3", "CNmax_4"}.issubset(df):
            msg = (
                "Dataframe should have columns 'CNmaxID', 'CNmax_1', 'CNmax_2', "
                "'CNmax_3', 'CNmax_4'."
            )
            raise IOError(msg)
        self._cn_table = df

    @property
    def composite_landuse(self):
        """Getter infrastructure polygon vector"""
        return self._composite_landuse

    @composite_landuse.setter
    def composite_landuse(self, raster_input):
        """Assign parcels polygon vector

        Parameters
        ----------
        vector_input: Pathlib.Path, str or geopandas.GeoDataFrame
            See :func:`pywatemsedem.catchment.vector_factory`.
        """
        self._composite_landuse = self.raster_factory(
            raster_input, flag_mask=False, flag_clip=False
        )

    @property
    def cfactor(self):
        """Getter cfactor 3-D raster"""
        return self._cfactor

    @cfactor.setter
    def cfactor(self, raster_input):
        """Setter cfactor 3-D raster

        Parameters
        ----------
        raster_input:
            3-D raster: x,y raster for every season.
        """
        raster = self.raster_factory(raster_input)
        raster.arr = np.where(raster.arr == raster.rp.nodata, 0, raster.arr)
        self._cfactor = raster

    @property
    def ktc(self):
        """Getter ktc 3-D raster"""

        return self._ktc

    @ktc.setter
    def ktc(self, raster_input):
        """Setter ktc 3-D raster

        Parameters
        ----------
        raster_input:
            3-D raster: x,y raster for every season.
        """
        self._ktc = self.raster_factory(raster_input)

    @property
    def cn(self):
        """Getter cn 3-D raster"""
        return self._cn

    @cn.setter
    def cn(self, raster_input):
        """Setter cn 3-D raster

        Parameters
        ----------
        raster_input:
            3-D raster: x,y raster for every season.
        """
        self._cn = self.raster_factory(raster_input, flag_clip=False, flag_mask=False)

    def prepare_grass_strips(self, maximize_grass_strips=False):
        """Prepare grass strips array

        Parameters
        ----------
        maximize_grass_strips: bool, default False

        """
        if self.grass_strips is not None:
            arr_parcels = None if self.parcels is None else self.parcels.arr
            arr_grass_ids, arr_grass = create_grassstrips_cnws(
                self.grass_strips.arr,
                self.catchm.river.arr,
                self.catchm.infrastructure.arr,
                self.rp.rasterio_profile,
                arr_parcels=arr_parcels,
                expand_grass_strips=maximize_grass_strips,
            )

            # write_ids
            grass_ids = RasterMemory(arr_grass_ids, self.rp)
            grass_ids.write(
                self.sfolder.scenarioyear_folder
                / (
                    f"grasstripsID_{self.year}_{self.catchm.name}_s"
                    f"{self.scenario_nr}.tif"
                ),
                format="tiff",
                dtype=np.int16,
            )
            # grass
            self.grass_strips = arr_grass
            self.grass_strips.write(
                self.sfolder.scenarioyear_folder
                / (f"gras_{self.year}_{self.catchm.name}_s{self.scenario_nr}.tif"),
                format="tiff",
                dtype=np.int16,
            )

    def create_perceelskaart_cnws(
        self,
        rivers,
        water,
        infrastructure,
        landuse,
        mask,
        yearfolder,
        rp,
        grass_strips=None,
        parcels=None,
        landuse_parcels=None,
    ):
        """Create CN_WS perceelskaart according to format of :ref:`here <watemsedem:prcmap>`.

        Parameters
        ----------
        rivers: numpy.ndarray
            River raster, should only contain nodata-value and -1 (river), see
            :ref:`here <watemsedem:prcmap>`.
        water: numpy.ndarray
            Water raster, should only contain nodata-value and -3 (), see
            :ref:`here <watemsedem:prcmap>`.
        infrastructure: numpy.ndarray
            Infrastructure raster, should only contain -2 (paved) and -7 (non-paved)
            and nodata-value. #TODO: check if we can only use -7
        landuse: numpy.ndarray
            Landuse raster. This raster should be formatted according to the composite
            landuse / WaTEM/SEDEM parcels raster (see :ref:`here <watemsedem:prcmap>`).
        mask: numpy.ndarray
            Mask raster,
        yearfolder: pathlib.Path
            #TODO: try to ditch this
        rp: pywatemsedem.geo.rasterproperties.RasterProperties
            Raster properties, see :class:`pywatemsedem.geo.rasterproperties.RasterProperties`
        grass_strips: numpy.ndarray
            Grass strips raster, can only contain nodata-value and -6 (see
            :ref:`here <watemsedem:prcmap>`).
        parcels: numpy.ndarray
            Parcels ids raster, can only containt nodata-value and >0 (see
            :ref:`here <watemsedem:prcmap>`)

        Notes
        -----
        The infrastructur value -7 does not follow the definition of
        :ref:`here <watemsedem:prcmap>`. This value is converted in subfunctionalities of
        this function to -2.
        """
        # parcels)
        # TODO
        if self.parcels is not None:
            maxprc_id = np.max(self.parcels.arr)
        else:
            maxprc_id = 1

        # landuse
        landuse_core = get_source_landuse(
            landuse,
            maxprc_id,
            rp.rasterio_profile,
            mask,
            yearfolder,
            self.catchm.name,
        )
        pl = ParcelsLanduse(
            landuse_core,
            rivers,
            water,
            infrastructure,
            mask,
            rp.nodata,
            landuse_parcels=landuse_parcels,
            parcels=parcels,
            grass_strips=grass_strips,
        )
        arr = pl.create_parcels_landuse_raster()
        arr = np.where(arr == -7, -2, arr)  # aardewegen infstructuur maken
        # safety check, fill last empty gaps with 32767
        arr[(mask == 1) & (arr == 0)] = 32767
        composite_landuse = np.where(mask == 1, arr, 0).astype("float64")

        return composite_landuse

    def prepare_cnws_model_input(self, maximize_grass_strips=False):
        """Create model input for a scenario

        Parameters
        ----------
        maximize_grass_strips: bool, default False
            See :func:`pywatemsedem.scenario.create_perceelskaart_cnws`
        """
        logger.info("Aanmaken van alle nodige modelinput...")
        self.prepare_grass_strips(maximize_grass_strips=maximize_grass_strips)

        arr_parcels_lu = (
            None if self.parcels_landuse is None else self.parcels_landuse.arr
        )

        # todo: how could we fix following lines?
        if self.grass_strips is None:
            arr_grass_strips = None
        else:
            arr_grass_strips = self.grass_strips.arr
            arr_grass_strips[arr_grass_strips != self.grass_strips.rp.nodata] = -6

        arr_water = None if self.catchm.vct_water is None else self.catchm.water.arr

        arr_parcels = None if self.parcels is None else self.parcels.arr
        self.composite_landuse = self.create_perceelskaart_cnws(
            self.catchm.river.arr,
            arr_water,
            self.catchm.infrastructure.arr,
            self.catchm.landuse,
            self.catchm.mask.arr_bin,
            self.sfolder.scenarioyear_folder,
            self.catchm.rp,
            grass_strips=arr_grass_strips,
            parcels=arr_parcels,
            landuse_parcels=arr_parcels_lu,
        )

        self.composite_landuse.write(
            self.sfolder.cnwsinput_folder / inputfilename.parcelmosaic_file,
            dtype=np.int32,
        )

        if self.choices.version != "Only Routing":

            self.update_seasonal_data(
                self.composite_landuse,
                self.catchm.river,
                self.catchm.infrastructure,
                self.catchm.landuse,
                self.catchm.mask,
                vct_parcels=self.vct_parcels,
                vct_grass_strips=self.vct_grass_strips,
            )

        if self.choices.dict_model_options["Manual outlet selection"] == 1:
            self.outlets.write(
                self.sfolder.cnwsinput_folder / inputfilename.outlet_file
            )
        if self.choices.version != "Only Routing":
            if self.choices.dict_model_options["Calibrate"] == 1:
                for key in [
                    "Write sediment export",
                    "Write water erosion",
                    "Output per river segment",
                ]:
                    self.choices.dict_output[key] = 0
        if (self.choices.dict_ecm_options["Include buffers"] == 1) & (
            self.buffers is not None
        ):
            self.buffers.write(
                self.sfolder.cnwsinput_folder / inputfilename.buffers_file
            )

        if self.choices.dict_ecm_options["Include ditches"] == 1:
            self.ditches.write(
                self.sfolder.cnwsinput_folder / inputfilename.ditches_file
            )

        if self.choices.dict_ecm_options["Include dams"] == 1:
            self.conductive_dams.write(
                self.sfolder.cnwsinput_folder / inputfilename.conductivedams_file
            )

        if self.choices.dict_model_options["FilterDTM"] == 1:
            msg = "Filtering DTM within boundaries of parcels."
            logger.info(msg)
            self.catchm.dtm.filter()
            self.catchm.dtm.write(
                self.sfolder.cnwsinput_folder / inputfilename.dtm_file
            )

        if self.choices.dict_model_options["Include sewers"] == 1:
            if self.endpoints is not None:
                self.endpoints.write(
                    self.sfolder.cnwsinput_folder / inputfilename.endpoints_file,
                    format="idrisi",
                    dtype=np.float64,
                )
                self.endpoints_id.write(
                    self.sfolder.cnwsinput_folder / inputfilename.endpoints_id_file,
                    format="idrisi",
                    dtype=np.float64,
                )

    def update_seasonal_data(
        self,
        composite_landuse,
        river,
        infrastructure,
        landuse,
        mask,
        vct_parcels=None,
        vct_grass_strips=None,
    ):
        """Update seasonal data for prepare_cnws_model_input

        Parameters
        ----------
        year: int
            Simulation year.
        cn_table:
            File path to CN table.
        """
        # C-factor
        vct_grass_strips, cfactor = create_cfactor_cnws(
            river,
            infrastructure,
            landuse,
            mask,
            self.sfolder,
            vct_parcels=vct_parcels,
            vct_grass_strips=vct_grass_strips,
            use_source_oriented_measures=bool(
                self.choices.dict_ecm_options["UseTeelttechn"]
            ),
        )
        self.cfactor = cfactor
        self.cfactor.write(self.sfolder.cnwsinput_folder / inputfilename.cfactor_file)

        # CN
        if self.choices.version == "CN-WS":
            self.cn, gdf = process_cn_raster(
                self.catchm.hydrological_soil_group.arr,
                self.vct_parcels.geodata,
                self.season,
                self.composite_landuse.arr,
                self.parcels_ids.arr,
                self.cn_table,
                self.rp.nodata,
            )
            gdf.to_file(self.sfolder.cnwsinput_folder / "CN_table_parcels.shp")
            self.cn.write(self.sfolder.cnwsinput_folder / inputfilename.cn_file)
        # kTC
        if self.choices.dict_model_options["UserProvidedKTC"] == 1:
            out, vct_grass_strips = create_ktc_cnws(
                composite_landuse,
                cfactor,
                mask,
                self.choices.dict_variables["ktc low"],
                self.choices.dict_variables["ktc high"],
                self.choices.dict_variables["ktc limit"],
                self.sfolder,
                grass=vct_grass_strips,
            )
            # write results
            self.ktc = out
            self.ktc.write(self.sfolder.cnwsinput_folder / inputfilename.ktc_file)
            # write grass strips
            if vct_grass_strips is not None:
                vct_grass_strips.write(
                    self.sfolder.scenarioyear_folder
                    / f"gras_{self.year}_{self.catchm.name}_s{self.scenario_nr}.shp"
                )

    @valid_cnws_input
    def create_ini_file(self):
        """Creates an ini-file for the scenario"""
        logger.info("Aanmaken ini-file...")
        self.ini = self.sfolder.cnwsinput_folder / "inifile.ini"
        ini = IniFile(
            self.choices,
            self.choices.version,
            self.sfolder.cnwsinput_folder,
            self.sfolder.cnwsoutput_folder,
        )
        ini.add_model_information()
        ini.add_working_directories()
        ini.add_files()
        ini.add_user_choices()
        ini.add_output_maps()
        ini.add_variables(
            self.vct_buffers.geodata if self.vct_buffers is not None else None,
            self.vct_force_routing,
            self.catchm.vct_tubed_river,
        )
        ini.write(self.ini)

    @valid_ini
    def run_model(self, cnws_binary):
        """Run the WaTEM/SEDEM model

        Parameters
        ----------
        cnws_binary : str
            Name of CN_WS pascal compiled executable.

        """
        logger.info(f"Modeling scenario {self.scenario_nr}")
        try:
            cmd_args = [cnws_binary, str(self.ini)]
            run = subprocess.run(cmd_args, capture_output=True)
            for line in run.stdout.splitlines():
                logger.info(line.decode("utf-8"))
            logger.info("Modelrun finished!")
        except subprocess.CalledProcessError as e:
            msg = "Failed to run CNWS-model"
            logger.exception(msg)
            logger.exception(e.cmd)
            raise IOError(e)

    def zip(self):

        zip_folder(self.sfolder.scenario_folder)


def remove_known_grass_strips_from_parcels_vct_saga(parcels, vct_grass_strips):
    """Remove parcels with overlap above 75%

    Remove the parcels in vct_parcels that overlap with grass strips
    in vct_grass_strips if the overlap for both features is at least 75%.

    The function updates the vct_parcels input layer

    The amount of intersection or overlap between a parcel is caluclated as
    area_intersect(grass strips, parcel)/area(parcel).

    Parameters
    ----------
    parcels: geopandas.GeoDataFrame
        Can have any column, should have geometries
    vct_grass_strips: str or pathlib.Path
        File path of parcel shapefile
    """
    cond = (vct_grass_strips is not None) and (parcels is not None)
    fname_temp = vct_grass_strips.parents[0] / "temp_intersect.shp"
    fname_parcels = vct_grass_strips.parents[0] / "temp_parcels.shp"

    if cond:
        # check if NR is in vct_parcels
        if "NR" not in parcels:
            parcels["NR"] = np.arange(1, len(parcels) + 1, 1)
        parcels.to_file(fname_parcels)
        saga_intersection(
            str(fname_parcels),
            str(vct_grass_strips),
            fname_temp,
        )

        # intersect
        parcels_intersection = gpd.read_file(fname_temp)

        # couple considered parcels from this year and prior year (only consider
        # largest intersect)
        parcels_intersection["area_inter"] = parcels_intersection["geometry"].area

        # find largest interesecting parcel and select only those
        parcels_intersection["area_inter_max"] = parcels_intersection.groupby("NR")[
            "area_inter"
        ].transform(np.max)
        cond = (
            parcels_intersection["area_inter_max"] == parcels_intersection["area_inter"]
        )
        parcels_intersection = parcels_intersection[cond]

        # load parcels
        parcels.loc[:, "area"] = parcels["geometry"].area.values

        parcels = parcels.merge(
            parcels_intersection[["NR", "area_inter"]],
            on="NR",
            how="left",
        )

        # normalize area intersction  with area of parcel of considered year
        parcels["norm_over"] = parcels["area_inter"] / parcels["area"] * 100

        # define condition
        cond = (parcels["norm_over"].isnull()) | (parcels["norm_over"] <= 75)
        parcels = parcels.loc[cond]
        parcels = parcels.drop(
            columns=["area_inter_max", "norm_over", "area_inter"], errors="ignore"
        )

    return parcels


def convert_grass_strips_to_agricultural_fields(parcels, vct_grass_strips):
    """Convert known grass strips to agricultural fields in the parcels shape file.

    If a parcel in vct_parcels intersects for 75% or more with a grass strip in
    vct_grass_strips, the attributes of the parcel are changed: "LANDUSE" is set
    to -9999 (agriculture), "GWSCOD_H" is set to "9999" (unknown crop) and
    "C-factor" is set to 0.37. This function updates the input vct_parcels.

    The amount of intersection or overlap between a parcel is caluclated as
    area_intersect(grasstri, parcel)/area(parcel).

    Parameters
    ----------
    parcels: geopandas.GeoDataFrame
        Can have any column, should have geometries

    vct_grass_strips: str or pathlib.Path
        File path of parcel shapefiles

    Returns
    -------
    parcels: geopandas.GeoDataFrame
        With added column:

        - *default_cfactor* (bool): convert to default C-factor (and landuse).

    """

    if vct_grass_strips is not None and parcels is not None:
        if "C_factor" not in parcels:
            parcels["C_factor"] = np.nan
        gdf_grass = gpd.read_file(vct_grass_strips)
        matches = parcels.geometry.apply(lambda x: nearly_identical(gdf_grass, x))
        matches = matches.unstack().reset_index(0, drop=True).dropna()
        gdf_grass_matched = gdf_grass.reindex(index=matches.values)
        gdf_grass_matched.index = matches.index
        gdf_grass_matched["grasstrip"] = 1
        gdf_grass_matched = gdf_grass_matched[["grasstrip"]]
        parcels = pd.merge(
            parcels,
            gdf_grass_matched,
            how="left",
            left_index=True,
            right_index=True,
        )
        parcels.loc[parcels["grasstrip"] == 1, "LANDUSE"] = -9999
        parcels.loc[parcels["grasstrip"] == 1, "GWSCOD_H"] = 9999
        parcels.loc[parcels["grasstrip"] == 1, "C_factor"] = 0.37

    return parcels


def assign_buffer_id_to_df_buffer(df):
    """Assign buffer id and extention id to buffer dataframe.

    Parameters
    ----------
    df: pandas.DataFrame
        Buffer dataframe with columns

    Returns
    ----------
    df: pandas.DataFrame
        Updated with:

        - *buf_id* (int): buffer id.
        - *buf_exid* (int): buffer extension id.
    """
    df["buf_id"] = range(1, df.shape[0] + 1)
    df["buf_exid"] = df["buf_id"] + 2**14

    return df


def add_tillage_technical_measures_to_parcels(gdf_parcels, gdf_tillage_technical):
    """Add crop technical measures to parcels vector data.

    An overlap between the target parcel polygons and source technical polygons is
    computed to determine for which parcels a tillage technical measure should be
    applied.

    Parameters
    ----------
    gdf_parcels: geopandas.GeoDataFrame
        Parcels polygon vector
    gdf_tillage_technical: geopandas.GeoDataFrame
        Tillage technical polygon vector
    overlap: int
        Minimal required overlap between polygons to select the implementation of a
        tillage technical measure to be applied for the parcel.
    """

    matches = gdf_parcels.geometry.apply(
        lambda x: nearly_identical(gdf_tillage_technical, x, 0.75)
    )
    matches2 = matches.unstack().reset_index(0, drop=True).dropna()
    df_teelttech_matched = gdf_tillage_technical.reindex(index=matches2.values)
    df_teelttech_matched.index = matches2.index

    df_teelttech_matched = df_teelttech_matched[["category"]]

    df_merged = pd.merge(
        gdf_parcels, df_teelttech_matched, how="left", left_index=True, right_index=True
    )
    df_merged.loc[df_merged["category"] == "ntkerend", "ntkerend"] = 1
    df_merged.loc[df_merged["category"] == "drempels", "drempels"] = 1
    df_merged.loc[df_merged["category"] == "contourzaaien", "contour"] = 1
    df_merged.loc[df_merged["category"] == "gewasrest", "gewasrest"] = 1
    df_merged.loc[df_merged["category"] == "groenbedekker", "groenbedek"] = 1
    df_merged.loc[df_merged["category"] == "default", "ntkerend"] = 1
    df_merged.drop("category", axis=1, inplace=True)

    return df_merged
