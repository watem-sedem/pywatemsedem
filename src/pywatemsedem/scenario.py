import logging

# Standard libraries
import subprocess
import warnings
from copy import deepcopy
from functools import wraps

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors

from pywatemsedem.cfactor import create_cfactor_degerick2015
from pywatemsedem.geo.rasters import AbstractRaster
from pywatemsedem.geo.utils import nearly_identical, saga_intersection
from pywatemsedem.geo.vectors import AbstractVector
from pywatemsedem.io.folders import ScenarioFolders
from pywatemsedem.io.ini import IniFile
from pywatemsedem.ktc import create_ktc
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
from .grasstrips import process_grass_strips
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
            if self._vct_endpoints.is_empty():
                msg = (
                    "Please define a non-empty endpoints line vector (see "
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


def valid_composite_landuse(func):
    """Check if composite landuse is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self._composite_landuse.is_empty():
            msg = (
                "Please define a non-empty composite landuse (see also "
                "self.create_composite_landuse)!"
            )
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_cfactor(func):
    """Check if composite landuse is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self._cfactor.is_empty():
            msg = (
                "Please define a non-empty C-factor raster (see also "
                "self.create_composite_landuse)!"
            )
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_ktc(func):
    """Check if composite landuse is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self._ktc.is_empty():
            msg = (
                "Please define a non-empty ktc raster (see also "
                "self.create_composite_landuse)!"
            )
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_river(func):
    """Check if river is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm._river.is_empty():
            msg = (
                "Please define a non-empty river raster (see also "
                "self.create_composite_landuse)!"
            )
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_landuse(func):
    """Check if infrastructure is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm._landuse.is_empty():
            msg = "Please define a non-empty landuse raster"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_infrastructure(func):
    """Check if infrastructure is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm._infrastructure.is_empty():
            msg = "Please define a non-empty infrastructure raster"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_grass_strips(func):
    """Check if grass strips vector is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.choices.dict_ecm_options["UseGras"] == 1:
            if self._vct_grass_strips.is_empty():
                msg = "No (or empty) grass strips defined, but option 'UseGras' equal to 1."
                raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_buffers(func):
    """Check if buffers vector is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.choices.dict_ecm_options["Include buffers"] == 1:
            if self._vct_buffers.is_empty():
                msg = "No (or empty) buffers defined, but option 'Include buffers' equal to 1."
                warnings.warn(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_vct_outlets(func):
    """Check if outlet vector is defined"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self._vct_outlets.is_empty():
            msg = "Please define non-empty outlets point vector (see vct_outlets-property)!"
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


def valid_dtm(func):
    """Check if you have defined a K-factor raster."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm.dtm.is_empty():
            msg = "Please first define a (non-empty) DTM raster!"
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


def valid_kfactor(func):
    """Check if you have defined a K-factor raster."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm.kfactor.is_empty():
            msg = "Please first define a (non-empty) K-factor raster!"
            raise IOError(msg)

        return func(self, *args, **kwargs)

    return wrapper


def valid_pfactor(func):
    """Check if you have defined a P-factor raster."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.catchm.pfactor.is_empty():
            msg = "Please first define a (non-empty) P-factor raster!"
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

    The scenario class holds all dynamic information for a scenario.
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
        self._vct_grass_strips = AbstractVector()  # vector
        self._vct_buffers = AbstractVector()  # vector
        self._vct_bufferoutlets = AbstractVector()  # vector
        self._vct_ditches = AbstractVector()
        self._vct_condictive_dams = AbstractVector()
        self._vct_source_measures = AbstractVector()
        self._vct_endpoints = AbstractVector()
        self._endpoints = AbstractRaster()
        self._endpoints_id = AbstractRaster()
        self._force_routing = pd.DataFrame()
        self._vct_outlets = AbstractVector()
        self._outlets = AbstractRaster()
        self._vct_parcels = AbstractVector()

        # API rasters
        self._grass_strips = AbstractRaster()  # raster
        self._parcels = AbstractRaster()

        # WaTEM/SEDEM input
        self._ktc = AbstractRaster()
        self._cn = AbstractRaster()
        self._cn_table = None
        self._cfactor = AbstractRaster()
        self._composite_landuse = AbstractRaster()

        # assign scenario number and user choices
        self.scenario_nr = scenario_nr
        self.year = year
        self.choices = deepcopy(userchoices)
        self.rst_outlet = AbstractRaster()
        self.ini = None

        # initialisation functionalities
        self.temporal_resolution()

        # Create folder structure
        self.scenario_folder_init = (
            self.catchm.folder.home_folder / f"scenario_" f"{self.scenario_nr}"
        )
        self.sfolder = ScenarioFolders(self.catchm.folder, self.scenario_nr, self.year)
        self.sfolder.create_all()

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
        if not self.parcels_ids.is_empty():
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

            return self.raster_factory(arr, allow_nodata_array=True)
        else:
            return AbstractRaster()

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
        if not self._vct_parcels.is_empty():
            arr = self._vct_parcels.rasterize(
                self.catchm.mask_raster, self.rp.epsg, col="NR", gdal=True
            )
            return self.raster_factory(arr, allow_nodata_array=True)
        else:
            return AbstractRaster()

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
        if not self._vct_parcels.is_empty():
            arr = self.vct_parcels.rasterize(
                self.catchm.mask_raster, self.rp.epsg, col="LANDUSE", gdal=True
            )
            if np.all(arr == self.rp.nodata):
                return AbstractRaster()
            else:
                return self.raster_factory(arr)
        else:
            return AbstractRaster()

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
            return AbstractRaster()
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
        if not self.vct_buffers.is_empty():
            arr = self.vct_buffers.rasterize(
                self.catchm.mask_raster, 31370, "buf_exid", gdal=True
            )
            raster = self.raster_factory(arr)
        else:
            raster = AbstractRaster()
        return raster

    @property
    def bufferoutlet(self):
        """Getter buffer outlet raster

        Returns
        -------
        pywatemsedem.geo.rasters.AbstractRaster
        """
        if not self.vct_bufferoutlets.is_empty():
            self.vct_bufferoutlets.geodata = process_buffer_outlets(
                self.vct_bufferoutlets.geodata, self.vct_buffers.geodata
            )
            arr = np.where(self.catchm.vct_river.arr == -1, 0, self.bufferoutlet)
            raster = self.raster_factory(arr)
        else:
            raster = AbstractRaster()

        return raster

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
            raster = AbstractRaster()
        elif self.vct_buffers.is_empty():
            msg = "Either define buffer vector of set 'Include buffers' to zero."
            raise IOError(msg)
        else:
            self.vct_buffers.geodata = assign_buffer_id_to_df_buffer(
                self.vct_buffers.geodata
            )
            if not self.catchm.vct_river.is_empty():
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
                raster = self.raster_factory(arr, flag_mask=False)

        return raster

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
        if not self.buffers.is_empty():
            # if there is a buffer on the same pixel of a ditch, remove the ditch
            arr = np.where(self.buffers.arr != 0, 0, arr)
        if not self.catchm.vct_river.is_empty():
            arr = np.where(self.river.arr == -1, 0, arr)
        raster = self.raster_factory(arr)
        return raster

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
        if not self.buffers.is_empty():
            # if there is a buffer on the same pixel of a ditch, remove the ditch
            arr = np.where(self.buffers.arr != 0, 0, arr)
        if not self.catchm.vct_river.is_empty():
            arr = np.where(self.river.arr == -1, 0, arr)
        raster = self.raster_factory(arr)
        return raster

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
            self._vct_outlets = AbstractVector()
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
    def force_routing(self):
        """#todo

        Returns
        -------

        """
        return self._force_routing

    @force_routing.setter
    def force_routing(self, vector_input):
        """Appoint force routing

        Parameters
        ----------
        vector_input: str | pathlib.Path | geopandas.GeoDataFrame
            See :func:`pywatemsedem.catchment.vector_factory`.
        """
        self._vct_forced_routing = self.vector_factory(
            vector_input, "LineString", allow_empty=True
        )
        self._force_routing = format_forced_routing(
            self._vct_forced_routing.geodata,
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
                f"({self.choices.dict_variables['SewerInletEff'] * 100} %)."
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
            arr = self._composite_landuse.arr.copy().astype(np.float32)
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

        self._composite_landuse.plot = plot

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

    @valid_landuse
    @valid_river
    def create_composite_landuse(
        self,
        maximize_grass_strips=False,
    ):
        """Create composite landuse to format of :ref:`here <watemsedem:prcmap>`.

        Uses specific algorithm of Degerick (2015)

        Requires at least a defined landuse and river raster

        Parameters
        ----------
        maximize_grass_strips: bool, default False
            Expand grass strips using rivers and infrastructure as boundary conditions.
            Requires definition of infrastructure and rivers.

        Returns
        -------
        composite_landuse: numpy.ndarray

        Notes
        -----
        The infrastructur value -7 does not follow the definition of
        :ref:`here <watemsedem:prcmap>`. This value is converted in subfunctionalities
        of this function to -2.
        """
        # preprocess grass strips
        if self.grass_strips.is_empty():
            msg = "Will not include grass strips in composite landuse."
            warnings.warn(msg)
            grass_strips = None
        else:
            if self.catchm.river.is_empty() or self.catchm.infrastructure.is_empty():
                msg = (
                    "The 'expand grass strips'-module needs defined rivers and"
                    " infrastructure, skipping."
                )
                warnings.warn(msg)
                grass_strips = None
            else:
                grass_strips = process_grass_strips(
                    self.grass_strips.arr,
                    self.catchm.river.arr,
                    self.catchm.infrastructure.arr,
                    self.rp.rasterio_profile["nodata"],
                    self.parcels.arr,
                    expand_grass_strips=maximize_grass_strips,
                )
                grass_strips[grass_strips != self.rp.rasterio_profile["nodata"]] = -6

        # landuse
        maxprc_id = np.max(self.parcels.arr) if not self.parcels.is_empty() else 1
        landuse_core = get_source_landuse(
            self.catchm.landuse,
            maxprc_id,
            self.rp.rasterio_profile,
            self.catchm.mask.arr,
        )

        pl = ParcelsLanduse(
            landuse_core,
            self.catchm.river.arr,
            self.catchm.water.arr,
            self.catchm.infrastructure.arr,
            self.catchm.mask.arr,
            self.rp.nodata,
            landuse_parcels=self.parcels_landuse.arr,
            parcels=self.parcels.arr,
            grass_strips=grass_strips,
        )
        arr = pl.create_parcels_landuse_raster()
        arr = np.where(arr == -7, -2, arr)  # aardewegen infstructuur maken
        # safety check, fill last empty gaps with 32767
        arr[(self.catchm.mask.arr == 1) & (arr == 0)] = 32767
        composite_landuse = np.where(self.catchm.mask.arr == 1, arr, 0).astype(
            "float64"
        )

        return composite_landuse

    @valid_landuse
    @valid_infrastructure
    @valid_river
    def create_cfactor(self, use_source_oriented_measures=False):
        """Creates the C-factor raster based on river, infrastructure and landuse.

        Uses specific algorithm of Degerick (2015)

        Requires landuse, infrastructure and river raster

        The C-factor is set to (in order)

        - 0 if the landuse is river or infrastructure.
        - scaled according to the width of the grass strips.
        - C-factor of the crop for parcels (any model possible).
        - 0.001 if the landuse is forest
        - 0.01 if the landuse is grass land
        - 0 if the landuse is pond
        - 0.01 if the landuse is grass strip (where not grass strip vector is defined)

        Left-over pixels are set to 0.37

        Returns
        -------
        cfactor: numpy.ndarray
        """
        if self.choices.version == "Only Routing":
            msg = "C-factor raster is not generated for 'Only Routing'-mode."
            warnings.warn(msg)
            cfactor = np.ndarray()
        else:
            _, cfactor = create_cfactor_degerick2015(
                self.catchm.river,
                self.catchm.infrastructure,
                self.catchm.landuse,
                self.catchm.mask,
                vct_parcels=self.vct_parcels,
                vct_grass_strips=self.vct_grass_strips,
                use_source_oriented_measures=use_source_oriented_measures,
            )
        return cfactor

    @valid_composite_landuse
    @valid_cfactor
    def create_ktc(self, ktc_low, ktc_high, ktc_limit, user_provided_ktc=1):
        """Create ktc raster based on C-factor raster

        The ktc raster is generated by classifying low and high erosion potential based
        on the C-factor and ktc_limit (i.e. C_factor < ktc_high -> ktc_low, C_factor
        > ktc_limit -> ktc_high).

        The ktc value for landuse rivers, infrastructure and ponds is set to 9999
        (all sediment is routed downwards).

        Parameters
        ---------
        ktc_low: float
            Transport coefficient for land covers with low erosion potential
        ktc_high: float
            Transport coefficient for land covers with high erosion potential
        ktc_limit: float
            C-factor to make distinction between ktc_low and ktc_high
        user_provided_ktc: int, default 1
            Define KTC raster by user.

        Return
        ------
        ktc: numpy.ndarray
            Raster with ktc-values, returns an empty user_provided_ktc is 0.

        Notes
        -----
        1. Requires assignment of C-factor and composite land-use raster.
        2. The ktc values for grass strips are scaled according to their width (see
        :func:`pywatemsedem.ktc.scale_ktc_gdf_grass_strips`) if grass strips are used.
        """
        if user_provided_ktc == 1:
            ktc, _ = create_ktc(
                self.composite_landuse,
                self.cfactor.arr,
                self.catchm.mask,
                ktc_low,
                ktc_high,
                ktc_limit,
                grass=self.vct_grass_strips,
            )
        else:
            ktc = np.ndarray()
        return ktc

    @valid_kfactor
    @valid_dtm
    @valid_pfactor
    @valid_composite_landuse
    @valid_cfactor
    def prepare_input_files(self):
        """Prepare all files (write to disk)"""
        self.catchm.kfactor.write(
            self.sfolder.cnwsinput_folder / inputfilename.kfactor_file
        )
        self.catchm.dtm.write(
            self.sfolder.cnwsinput_folder / inputfilename.dtm_file, nodata=-99999
        )
        self.catchm.pfactor.write(
            self.sfolder.cnwsinput_folder / inputfilename.pfactor_file
        )
        if self.choices.dict_model_options["River Routing"] == 1:
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
            self.choices.dict_output["Output per river segment"] = 1
            self.catchm.routing.write(
                self.sfolder.cnwsinput_folder / inputfilename.routing_file
            )
            # if self.choices.dict_output["Output per river segment"] == 1:
            self.catchm.segments.write(
                self.sfolder.cnwsinput_folder / inputfilename.segments_file
            )

        self.catchm.mask.write(self.sfolder.cnwsinput_folder / inputfilename.mask_file)

        self.composite_landuse.write(
            self.sfolder.cnwsinput_folder / inputfilename.parcelmosaic_file,
            dtype=np.int32,
        )
        if self.choices.version == "CN-WS":
            if self.cn is not None:
                self.cn.write(self.sfolder.cnwsinput_folder / inputfilename.cn_file)
            else:
                msg = "Model version in 'CN-WS', define a CN raster to run CN."
                raise IOError(msg)

        if self.choices.dict_model_options["UserProvidedKTC"] == 1:
            if not self.ktc.is_empty():
                self.ktc.write(self.sfolder.cnwsinput_folder / inputfilename.ktc_file)
            else:
                msg = "UserProvidedKTC is 1 (True), provide ktc-raster."
                raise IOError(msg)

        self.cfactor.write(self.sfolder.cnwsinput_folder / inputfilename.cfactor_file)

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
            self.buffers.is_empty()
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
            if not self.endpoints.is_empty():
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
        self.create_ini_file()

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
            self.vct_buffers.geodata,
            self.force_routing,
            self.catchm.tubed_river,
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
