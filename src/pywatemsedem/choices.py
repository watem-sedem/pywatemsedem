import datetime
import logging

# Standard libraries
import pathlib
from pathlib import Path

import pandas as pd
from pycnws.core.tools import get_item_from_ini

logger = logging.getLogger(__name__)


class UserChoice:
    def __init__(self, key, section, value, dtype, mandatory, allowed_values=None):
        """Initialize choice"""
        self.key = key
        self.section = section
        self._value = value
        self.dtype = dtype
        self.mandatory = mandatory
        self.allowed_values = allowed_values

    def _repr_html_(self):
        """notebook/ipython representation"""
        print_ = [
            f"Key: {self.key}",
            f"Value: {self.value}",
            f"Mandatory: {self.mandatory}",
            f"Dtype: {self.dtype}",
            f"Allowed_values: {self.allowed_values}",
            f"Section: {self.section}",
        ]
        print("\n".join(print_))

    def validate_type(self, value):
        if type(value) is not self.dtype:
            msg = f"Value assigned to key '{self.key}' should be dtype '{self.dtype}'."
            raise TypeError(msg)

    def validate_value(self, value):
        if self.allowed_values is not None:
            if value not in self.allowed_values:
                msg = f"Value should be one of: {self.allowed_values}."
                raise ValueError(msg)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, input_value):
        if input_value is not None:
            self.validate_type(input_value)
            self.validate_value(input_value)
            self._value = input_value

    def read_value_default_ini(self, default_ini):
        self.value = get_item_from_ini(default_ini, self.section, self.key, self.dtype)


class WSOptions:
    def __init__(self):
        self._l_model = UserChoice(
            "L model",
            "options",
            "Desmet1996_Vanoost2003",
            str,
            False,
            allowed_values=["Desmet1996_Vanoost2003", "Desmet1996_McCool"],
        )
        self._s_model = UserChoice(
            "S model",
            "options",
            "Nearing1997",
            str,
            False,
            allowed_values=["Nearing1997", "McCool1987"],
        )
        self._tc_model = UserChoice(
            "TC model",
            "options",
            "VanOost2000",
            str,
            False,
            allowed_values=["VanOost2000", "Verstraeten2007"],
        )
        self._only_routing = UserChoice(
            "only routing",
            "options",
            False,
            bool,
            False,
        )
        self._calculate_tillage_erosion = UserChoice(
            "calculate tillage erosion", "options", False, bool, False
        )

    @property
    def l_model(self):
        return self._l_model

    @l_model.setter
    def l_model(self, input_value):
        self._l_model.value = input_value

    @property
    def s_model(self):
        return self._s_model

    @s_model.setter
    def s_model(self, input_value):
        self._s_model.value = input_value

    @property
    def tc_model(self):
        return self._tc_model

    @tc_model.setter
    def tc_model(self, input_value):
        self._tc_model.value = input_value

    @property
    def only_routing(self):
        return self._only_routing

    @only_routing.setter
    def only_routing(self, input_value):
        self._only_routing.value = input_value

    @property
    def calculate_tillage_erosion(self):
        return self._calculate_tillage_erosion

    @calculate_tillage_erosion.setter
    def calculate_tillage_erosion(self, input_value):
        self._calculate_tillage_erosion.value = input_value


class WSParameters:
    def __init__(self):
        self._r_factor = UserChoice("R factor", "parameters", None, float, True)
        self._parcel_connectivity_cropland = UserChoice(
            "Parcel connectivity cropland", "parameters", None, int, True
        )
        self._parcel_connectivity_grasstrips = UserChoice(
            "Parcel connectivity grasstrips", "parameters", None, int, True
        )
        self._parcel_connectivity_forest = UserChoice(
            "Parcel connectivity forest", "parameters", None, int, True
        )
        self._parcel_trapping_eff_cropland = UserChoice(
            "Parcel trapping efficiency cropland", "parameters", None, int, True
        )
        self._parcel_trapping_eff_pasture = UserChoice(
            "Parcel trapping efficiency pasture", "parameters", None, int, True
        )
        self._parcel_trapping_eff_forest = UserChoice(
            "Parcel trapping efficiency forest", "parameters", None, int, True
        )
        self._max_kernel = UserChoice("max kernel", "parameters", 50, int, False)
        self._max_kernel_river = UserChoice(
            "max kernel river", "parameters", 100, int, False
        )
        self._bulk_density = UserChoice("bulk density", "parameters", None, int, True)

    @property
    def r_factor(self):
        return self._r_factor

    @r_factor.setter
    def r_factor(self, input_value):
        self._r_factor.value = input_value

    @property
    def parcel_connectivity_cropland(self):
        return self._parcel_connectivity_cropland

    @parcel_connectivity_cropland.setter
    def parcel_connectivity_cropland(self, input_value):
        self._parcel_connectivity_cropland.value = input_value

    @property
    def parcel_connectivity_grasstrips(self):
        return self._parcel_connectivity_grasstrips

    @parcel_connectivity_grasstrips.setter
    def parcel_connectivity_grasstrips(self, input_value):
        self._parcel_connectivity_grasstrips.value = input_value

    @property
    def parcel_connectivity_forest(self):
        return self._parcel_connectivity_forest

    @parcel_connectivity_forest.setter
    def parcel_connectivity_forest(self, input_value):
        self._parcel_connectivity_forest.value = input_value

    @property
    def parcel_trapping_eff_cropland(self):
        return self._parcel_trapping_eff_cropland

    @parcel_trapping_eff_cropland.setter
    def parcel_trapping_eff_cropland(self, input_value):
        self._parcel_trapping_eff_cropland.value = input_value

    @property
    def parcel_trapping_eff_pasture(self):
        return self._parcel_trapping_eff_pasture

    @parcel_trapping_eff_pasture.setter
    def parcel_trapping_eff_pasture(self, input_value):
        self._parcel_trapping_eff_pasture.value = input_value

    @property
    def parcel_trapping_eff_forest(self):
        return self._parcel_trapping_eff_forest

    @parcel_trapping_eff_forest.setter
    def parcel_trapping_eff_forest(self, input_value):
        self._parcel_trapping_eff_forest.value = input_value

    @property
    def max_kernel(self):
        return self._max_kernel

    @max_kernel.setter
    def max_kernel(self, input_value):
        self._max_kernel.value = input_value

    @property
    def max_kernel_river(self):
        return self._max_kernel_river

    @max_kernel_river.setter
    def max_kernel_river(self, input_value):
        self._max_kernel_river.value = input_value

    @property
    def bulk_density(self):
        return self._bulk_density

    @bulk_density.setter
    def bulk_density(self, input_value):
        self._bulk_density.value = input_value


class WSExtensions:
    def __init__(self):
        self._curve_number = UserChoice(
            "curve number", "extensions", False, bool, False
        )
        self._include_sewers = UserChoice(
            "include sewers", "extensions", False, bool, False
        )
        self._create_ktc_map = UserChoice(
            "create ktc map", "extensions", False, bool, False
        )
        self._create_ktil_map = UserChoice(
            "create ktil map", "extensions", False, bool, False
        )
        self._estimate_clay_content = UserChoice(
            "estimate clay content", "extensions", False, bool, False
        )
        self._include_tillage_direction = UserChoice(
            "include tillage directions", "extensions", False, bool, False
        )
        self._include_buffers = UserChoice(
            "include buffers", "extensions", False, bool, False
        )
        self._include_ditches = UserChoice(
            "include ditches", "extensions", False, bool, False
        )
        self._include_dams = UserChoice(
            "include dams", "extensions", False, bool, False
        )
        self._output_per_river_segment = UserChoice(
            "output per river segment", "extensions", False, bool, False
        )
        self._adjusted_slope = UserChoice(
            "adjusted slope", "extensions", False, bool, False
        )
        self._buffer_reduce_area = UserChoice(
            "buffer reduce area", "extensions", False, bool, False
        )
        self._force_routing = UserChoice(
            "force routing", "extensions", False, bool, False
        )
        self._river_routing = UserChoice(
            "river routing", "extensions", False, bool, False
        )
        self._manual_outlet_selection = UserChoice(
            "manual outlet selection", "extensions", False, bool, False
        )
        self._convert_output = UserChoice(
            "convert output", "extensions", False, bool, False
        )
        self._calibrate = UserChoice("calibrate", "extensions", False, bool, False)
        self._cardinal_routing_river = UserChoice(
            "cardinal routing river", "extensions", False, bool, False
        )

    @property
    def curve_number(self):
        return self._curve_number

    @curve_number.setter
    def curve_number(self, input_value):
        self._curve_number.value = input_value

    @property
    def include_sewers(self):
        return self._include_sewers

    @include_sewers.setter
    def include_sewers(self, input_value):
        self._include_sewers.value = input_value

    @property
    def create_ktc_map(self):
        return self._create_ktc_map

    @create_ktc_map.setter
    def create_ktc_map(self, input_value):
        self._create_ktc_map.value = input_value

    @property
    def create_ktil_map(self):
        return self._create_ktil_map

    @create_ktil_map.setter
    def create_ktil_map(self, input_value):
        self._create_ktil_map.value = input_value

    @property
    def estimate_clay_content(self):
        return self._estimate_clay_content

    @estimate_clay_content.setter
    def estimate_clay_content(self, input_value):
        self._estimate_clay_content.value = input_value

    @property
    def include_tillage_direction(self):
        return self._include_tillage_direction

    @include_tillage_direction.setter
    def include_tillage_direction(self, input_value):
        self._include_tillage_direction.value = input_value

    @property
    def include_buffers(self):
        return self._include_buffers

    @include_buffers.setter
    def include_buffers(self, input_value):
        self._include_buffers.value = input_value

    @property
    def include_ditches(self):
        return self._include_ditches

    @include_ditches.setter
    def include_ditches(self, input_value):
        self._include_ditches.value = input_value

    @property
    def include_dams(self):
        return self._include_dams

    @include_dams.setter
    def include_dams(self, input_value):
        self._include_dams.value = input_value

    @property
    def output_per_river_segment(self):
        return self._output_per_river_segment

    @output_per_river_segment.setter
    def output_per_river_segment(self, input_value):
        self._output_per_river_segment.value = input_value

    @property
    def adjusted_slope(self):
        return self._adjusted_slope

    @adjusted_slope.setter
    def adjusted_slope(self, input_value):
        self._adjusted_slope.value = input_value

    @property
    def buffer_reduce_area(self):
        return self._buffer_reduce_area

    @buffer_reduce_area.setter
    def buffer_reduce_area(self, input_value):
        self._buffer_reduce_area.value = input_value

    @property
    def force_routing(self):
        return self._force_routing

    @force_routing.setter
    def force_routing(self, input_value):
        self._force_routing.value = input_value

    @property
    def river_routing(self):
        return self._river_routing

    @river_routing.setter
    def river_routing(self, input_value):
        self._river_routing.value = input_value

    @property
    def manual_outlet_selection(self):
        return self._manual_outlet_selection

    @manual_outlet_selection.setter
    def manual_outlet_selection(self, input_value):
        self._manual_outlet_selection.value = input_value

    @property
    def convert_output(self):
        return self._convert_output

    @convert_output.setter
    def convert_output(self, input_value):
        self._convert_output.value = input_value

    @property
    def calibrate(self):
        return self._calibrate

    @calibrate.setter
    def calibrate(self, input_value):
        self._calibrate.value = input_value

    @property
    def cardinal_routing_river(self):
        return self._cardinal_routing_river

    @cardinal_routing_river.setter
    def cardinal_routing_river(self, input_value):
        self._cardinal_routing_river.value = input_value


class WSExtensionsParameters:
    def __init__(self, extensions):
        """Generate WSExtensionsParameters instance .

        Parameters
        ----------
        extensions: pycnws.core.choices.WSExtensions
            Instance of :class:`pycnws catchment <pycnws.core.choices.WSExtensions>`
            containing the settings on the used model extensions.
        """

        self._extensions = extensions
        self._sewer_exit = UserChoice(
            "sewer exit",
            "parameters extensions",
            None,
            int,
            self._extensions.include_sewers.value,
        )
        self._clay_content_parent_material = UserChoice(
            "clay content parent material",
            "parameters extensions",
            None,
            float,
            self._extensions.estimate_clay_content.value,
        )
        self._antecedent_rainfall = UserChoice(
            "antecedent rainfall",
            "parameters extensions",
            None,
            float,
            self._extensions.curve_number.value,
        )
        self._stream_velocity = UserChoice(
            "stream velocity",
            "parameters extensions",
            None,
            float,
            self._extensions.curve_number.value,
        )
        self._alpha = UserChoice(
            "alpha",
            "parameters extensions",
            None,
            float,
            self._extensions.curve_number.value,
        )
        self._beta = UserChoice(
            "beta",
            "parameters extensions",
            None,
            float,
            self._extensions.curve_number.value,
        )
        self._ls_correction = UserChoice(
            "ls correction", "parameters extensions", None, float, False
        )
        self._ktc_low = UserChoice(
            "ktc low",
            "parameters extensions",
            None,
            float,
            self._extensions.create_ktc_map.value,
        )
        self._ktc_high = UserChoice(
            "ktc high",
            "parameters extensions",
            None,
            float,
            self._extensions.create_ktc_map.value,
        )
        self._ktc_limit = UserChoice(
            "ktc limit",
            "parameters extensions",
            None,
            float,
            (self._extensions.create_ktc_map.value or self._extensions.calibrate.value),
        )
        self._ktil_default = UserChoice(
            "ktil default",
            "parameters extensions",
            None,
            float,
            self._extensions.create_ktil_map.value,
        )
        self._ktil_threshold = UserChoice(
            "ktil threshold",
            "parameters extensions",
            None,
            float,
            self._extensions.create_ktil_map.value,
        )
        self._desired_timestep = UserChoice(
            "desired timestep",
            "parameters extensions",
            None,
            float,
            self._extensions.curve_number.value,
        )
        self._final_timestep = UserChoice(
            "final timestep",
            "parameters extensions",
            None,
            float,
            (
                self._extensions.curve_number.value
                and self._extensions.convert_output.value
            ),
        )
        self._endtime_model = UserChoice(
            "endtime model",
            "parameters extensions",
            None,
            float,
            self._extensions.curve_number.value,
        )

    @property
    def sewer_exit(self):
        return self._sewer_exit

    @sewer_exit.setter
    def sewer_exit(self, input_value):
        self._sewer_exit.value = input_value

    @property
    def clay_content_parent_material(self):
        return self._clay_content_parent_material

    @clay_content_parent_material.setter
    def clay_content_parent_material(self, input_value):
        self._clay_content_parent_material.value = input_value

    @property
    def antecedent_rainfall(self):
        return self._antecedent_rainfall

    @antecedent_rainfall.setter
    def antecedent_rainfall(self, input_value):
        self._antecedent_rainfall.value = input_value

    @property
    def stream_velocity(self):
        return self._stream_velocity

    @stream_velocity.setter
    def stream_velocity(self, input_value):
        self._stream_velocity.value = input_value

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, input_value):
        self._alpha.value = input_value

    @property
    def beta(self):
        return self._beta

    @beta.setter
    def beta(self, input_value):
        self._beta.value = input_value

    @property
    def ls_correction(self):
        return self._ls_correction

    @ls_correction.setter
    def ls_correction(self, input_value):
        self._ls_correction.value = input_value

    @property
    def ktc_low(self):
        return self._ktc_low

    @ktc_low.setter
    def ktc_low(self, input_value):
        self._ktc_low.value = input_value

    @property
    def ktc_high(self):
        return self._ktc_high

    @ktc_high.setter
    def ktc_high(self, input_value):
        self._ktc_high.value = input_value

    @property
    def ktc_limit(self):
        return self._ktc_limit

    @ktc_limit.setter
    def ktc_limit(self, input_value):
        self._ktc_limit.value = input_value

    @property
    def ktil_default(self):
        return self._ktil_default

    @ktil_default.setter
    def ktil_default(self, input_value):
        self._ktil_default.value = input_value

    @property
    def ktil_threshold(self):
        return self._ktil_threshold

    @ktil_threshold.setter
    def ktil_threshold(self, input_value):
        self._ktil_threshold.value = input_value

    @property
    def desired_timestep(self):
        return self._desired_timestep

    @desired_timestep.setter
    def desired_timestep(self, input_value):
        self._desired_timestep.value = input_value

    @property
    def final_timestep(self):
        return self._final_timestep

    @final_timestep.setter
    def final_timestep(self, input_value):
        self._final_timestep.value = input_value

    @property
    def endtime_model(self):
        return self._endtime_model

    @endtime_model.setter
    def endtime_model(self, input_value):
        self._endtime_model.value = input_value


class WSOutput:
    def __init__(self):
        self._write_aspect = UserChoice("output", "write aspect", False, bool, False)
        self._write_ls_factor = UserChoice(
            "output", "write ls factor", False, bool, False
        )
        self._write_upstream_area = UserChoice(
            "output", "write upstream area", False, bool, False
        )
        self._write_slope = UserChoice("output", "write slope", False, bool, False)
        self._write_routing_table = UserChoice(
            "output", "write routing table", False, bool, False
        )
        self._write_routing_column_row = UserChoice(
            "output", "write routing column/row", False, bool, False
        )
        self._write_rusle = UserChoice("output", "write rusle", False, bool, False)
        self._write_sediment_export = UserChoice(
            "output", "write sediment export", False, bool, False
        )
        self._write_water_erosion = UserChoice(
            "output", "write water erosion", False, bool, False
        )
        self._write_rainfall_excess = UserChoice(
            "output", "write rainfall excess", False, bool, False
        )
        self._write_total_runoff = UserChoice(
            "output", "write total runoff", False, bool, False
        )
        self._export_saga = UserChoice(
            "output", "Export .sgrd grids", False, bool, False
        )

    @property
    def write_aspect(self):
        return self._write_aspect

    @write_aspect.setter
    def write_aspect(self, input_value):
        self._write_aspect.value = input_value

    @property
    def write_ls_factor(self):
        return self._write_ls_factor

    @write_ls_factor.setter
    def write_ls_factor(self, input_value):
        self._write_ls_factor.value = input_value

    @property
    def write_upstream_area(self):
        return self._write_upstream_area

    @write_upstream_area.setter
    def write_upstream_area(self, input_value):
        self._write_upstream_area.value = input_value

    @property
    def write_slope(self):
        return self._write_slope

    @write_slope.setter
    def write_slope(self, input_value):
        self._write_slope.value = input_value

    @property
    def write_routing_table(self):
        return self._write_routing_table

    @write_routing_table.setter
    def write_routing_table(self, input_value):
        self._write_routing_table.value = input_value

    @property
    def write_routing_column_row(self):
        return self._write_routing_column_row

    @write_routing_column_row.setter
    def write_routing_column_row(self, input_value):
        self._write_routing_column_row.value = input_value

    @property
    def write_rusle(self):
        return self._write_rusle

    @write_rusle.setter
    def write_rusle(self, input_value):
        self._write_rusle.value = input_value

    @property
    def write_sediment_export(self):
        return self._write_sediment_export

    @write_sediment_export.setter
    def write_sediment_export(self, input_value):
        self._write_sediment_export.value = input_value

    @property
    def write_water_erosion(self):
        return self.write_water_erosion

    @write_water_erosion.setter
    def write_water_erosion(self, input_value):
        self._write_water_erosion.value = input_value

    @property
    def write_rainfall_excess(self):
        return self._write_rainfall_excess

    @write_rainfall_excess.setter
    def write_rainfall_excess(self, input_value):
        self._write_rainfall_excess.value = input_value

    @property
    def write_total_runoff(self):
        return self._write_total_runoff

    @write_total_runoff.setter
    def write_total_runoff(self, input_value):
        self._write_total_runoff.value = input_value

    @property
    def export_saga(self):
        return self._export_saga

    @export_saga.setter
    def export_saga(self, input_value):
        self._export_saga.value = input_value


class PyVariables:
    def __init__(self):
        self._start_year = None
        self._start_month = None
        self._sewer_inlet_efficiency = None
        self._spatial_resolution = None


class PyOptions:
    def __init__(self):
        self._filter_dtm = None
        self._only_sewers_in_infrastructure = None
        self._maximize_gras_strips = None
        self._use_gras = None
        self._use_crop_management = None
