import logging

from pywatemsedem.io.ini import get_item_from_ini

# Standard libraries


logger = logging.getLogger(__name__)


class UserChoice:
    def __init__(
        self, key, section, dtype, mandatory, default_value=None, allowed_values=None
    ):
        """Initialize choice"""
        self.key = key
        self.section = section
        self.dtype = dtype
        self._value = None
        self.default_value = default_value
        self.mandatory = mandatory
        self.allowed_values = allowed_values

    def _repr_html_(self):
        """notebook/ipython representation"""
        print_ = [
            f"Key: {self.key}",
            f"Value: {self.value}",
            f"Mandatory: {self.mandatory}",
            f"Dtype: {self.dtype}",
            f"Default_value: {self.default_value}",
            f"Allowed_values: {self.allowed_values}",
            f"Section: {self.section}",
        ]
        print("\n".join(print_))

    def validate_type(self, value):
        """Validate if the value has the correct dtype"""
        if type(value) is not self.dtype:
            msg = f"Value assigned to key '{self.key}' should be dtype '{self.dtype}'."
            raise TypeError(msg)

    def validate_value(self, value):
        """Validate if the value is within the allowed values"""
        if self.allowed_values is not None:
            if value not in self.allowed_values:
                msg = f"Value should be one of: {self.allowed_values}."
                raise ValueError(msg)

    @property
    def value(self):
        """Getter of the value of the UserChoice

        Returns
        -------
        pywatemsedem.choices.UserChoice.value
        """
        return self._value

    @value.setter
    def value(self, input_value):
        """Assign value of a UserChoice

        This function assigns the value of a UserChoice after it is validated

        Parameters
        ----------
        input_value: str, int or float
        """
        if input_value is not None:
            self.validate_type(input_value)
            self.validate_value(input_value)
            self._value = input_value

    def read_value_from_ini(self, default_ini):
        """Read value from an ini-file"""
        self.value = get_item_from_ini(default_ini, self.section, self.key, self.dtype)

    def read_default_value_from_ini(self, default_ini):
        """Read default value from an ini-file"""
        self.default_value = get_item_from_ini(
            default_ini, self.section, self.key, self.dtype
        )


class WSMixin:
    def check_mandatory_values(self):
        """Check if the value of an attribute is not None when it is mandatory"""
        for key in self.__dict__:
            attribute = getattr(self, key)
            if isinstance(attribute, UserChoice):
                if attribute.mandatory and (attribute.value is None):
                    msg = f"{attribute.key} is mandatory and cannot be None"
                    raise ValueError(msg)

    def apply_defaults(self):
        """Set default value as value for every attribute"""
        for key in self.__dict__:
            attribute = getattr(self, key)
            if isinstance(attribute, UserChoice):
                if attribute.default_value is None:
                    logger.info(
                        f"No default value for {key} given, value must be given manually"
                    )
                attribute.value = attribute.default_value


class WSOptions(WSMixin):
    def __init__(self):
        """Initialise WSOptions"""
        self._l_model = UserChoice(
            "L model",
            "options",
            str,
            False,
            "Desmet1996_Vanoost2003",
            allowed_values=["Desmet1996_Vanoost2003", "Desmet1996_McCool"],
        )
        self._s_model = UserChoice(
            "S model",
            "options",
            str,
            False,
            "Nearing1997",
            allowed_values=["Nearing1997", "McCool1987"],
        )
        self._tc_model = UserChoice(
            "TC model",
            "options",
            str,
            False,
            "VanOost2000",
            allowed_values=["VanOost2000", "Verstraeten2007"],
        )
        self._only_routing = UserChoice(
            "only routing",
            "options",
            bool,
            False,
            False,
        )
        self._calculate_tillage_erosion = UserChoice(
            "calculate tillage erosion", "options", bool, False, False
        )

    @property
    def l_model(self):
        """Getter L model

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the L model
        """
        return self._l_model

    @l_model.setter
    def l_model(self, input_value):
        """Assign the l_model

        Parameters
        ---------
        input_value: str
            name of the L model
        """
        self._l_model.value = input_value

    @property
    def s_model(self):
        """Getter S model

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the S model
        """
        return self._s_model

    @s_model.setter
    def s_model(self, input_value):
        """Assign the s_model

        Parameters
        ---------
        input_value: str
            name of the S model
        """
        self._s_model.value = input_value

    @property
    def tc_model(self):
        """Getter TC model

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the TC model
        """
        return self._tc_model

    @tc_model.setter
    def tc_model(self, input_value):
        """Assign the tc_model

        Parameters
        ---------
        input_value: str
            name of the TC model
        """
        self._tc_model.value = input_value

    @property
    def only_routing(self):
        """Getter only_routing option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the only_routing option
        """
        return self._only_routing

    @only_routing.setter
    def only_routing(self, input_value):
        """Assign the only_routing option

        Parameters
        ---------
        input_value: bool
        """
        self._only_routing.value = input_value

    @property
    def calculate_tillage_erosion(self):
        """Getter calculate_tillage_erosion option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the calculate_tillage_erosion option
        """
        return self._calculate_tillage_erosion

    @calculate_tillage_erosion.setter
    def calculate_tillage_erosion(self, input_value):
        """Assign the calculate_tillage_erosion option

        Parameters
        ---------
        input_value: bool
        """
        self._calculate_tillage_erosion.value = input_value


class WSParameters(WSMixin):
    def __init__(self):
        """Initialise WSParameters"""
        self._r_factor = UserChoice("R factor", "parameters", float, True, None)
        self._parcel_connectivity_cropland = UserChoice(
            "Parcel connectivity cropland", "parameters", int, True, None
        )
        self._parcel_connectivity_grasstrips = UserChoice(
            "Parcel connectivity grasstrips", "parameters", int, True, None
        )
        self._parcel_connectivity_forest = UserChoice(
            "Parcel connectivity forest", "parameters", int, True, None
        )
        self._parcel_trapping_eff_cropland = UserChoice(
            "Parcel trapping efficiency cropland", "parameters", int, True, None
        )
        self._parcel_trapping_eff_pasture = UserChoice(
            "Parcel trapping efficiency pasture", "parameters", int, True, None
        )
        self._parcel_trapping_eff_forest = UserChoice(
            "Parcel trapping efficiency forest", "parameters", int, True, None
        )
        self._max_kernel = UserChoice("max kernel", "parameters", int, False, 50)
        self._max_kernel_river = UserChoice(
            "max kernel river", "parameters", int, False, 100
        )
        self._bulk_density = UserChoice("bulk density", "parameters", int, True, None)

    @property
    def r_factor(self):
        """Getter r_factor parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the r_factor parameter
        """
        return self._r_factor

    @r_factor.setter
    def r_factor(self, input_value):
        """Assign the r_factor parameter

        Parameters
        ----------
        input_value: float
            The R-factor value
        """
        self._r_factor.value = input_value

    @property
    def parcel_connectivity_cropland(self):
        """Getter parcel_connectivity_cropland parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the parcel_connectivity_cropland parameter
        """
        return self._parcel_connectivity_cropland

    @parcel_connectivity_cropland.setter
    def parcel_connectivity_cropland(self, input_value):
        """Assign the parcel_connectivity_cropland parameter

        Parameters
        ----------
        input_value: int
            The parcel_connectivity_cropland value
        """
        self._parcel_connectivity_cropland.value = input_value

    @property
    def parcel_connectivity_grasstrips(self):
        """Getter parcel_connectivity_grasstrips parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the parcel_connectivity_grasstrips parameter
        """
        return self._parcel_connectivity_grasstrips

    @parcel_connectivity_grasstrips.setter
    def parcel_connectivity_grasstrips(self, input_value):
        """Assign the parcel_connectivity_grasstrips parameter

        Parameters
        ----------
        input_value: int
            The parcel_connectivity_grasstrips value
        """
        self._parcel_connectivity_grasstrips.value = input_value

    @property
    def parcel_connectivity_forest(self):
        """Getter parcel_connectivity_forest parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the parcel_connectivity_forest parameter
        """
        return self._parcel_connectivity_forest

    @parcel_connectivity_forest.setter
    def parcel_connectivity_forest(self, input_value):
        """Assign the parcel_connectivity_fores parameter

        Parameters
        ----------
        input_value: int
            The parcel_connectivity_forest value
        """
        self._parcel_connectivity_forest.value = input_value

    @property
    def parcel_trapping_eff_cropland(self):
        """Getter parcel_trapping_eff_cropland parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the parcel_trapping_eff_cropland parameter
        """
        return self._parcel_trapping_eff_cropland

    @parcel_trapping_eff_cropland.setter
    def parcel_trapping_eff_cropland(self, input_value):
        """Assign the parcel_trapping_eff_cropland parameter

        Parameters
        ----------
        input_value: int
            The parcel_trapping_eff_cropland value
        """
        self._parcel_trapping_eff_cropland.value = input_value

    @property
    def parcel_trapping_eff_pasture(self):
        """Getter parcel_trapping_eff_pasture parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the parcel_trapping_eff_pasture parameter
        """
        return self._parcel_trapping_eff_pasture

    @parcel_trapping_eff_pasture.setter
    def parcel_trapping_eff_pasture(self, input_value):
        """Assign the parcel_trapping_eff_pasture parameter

        Parameters
        ----------
        input_value: int
            The parcel_trapping_eff_pasture value
        """
        self._parcel_trapping_eff_pasture.value = input_value

    @property
    def parcel_trapping_eff_forest(self):
        """Getter parcel_trapping_eff_forest parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the parcel_trapping_eff_forest parameter
        """
        return self._parcel_trapping_eff_forest

    @parcel_trapping_eff_forest.setter
    def parcel_trapping_eff_forest(self, input_value):
        """Assign the parcel_trapping_eff_forest parameter

        Parameters
        ----------
        input_value: int
            The parcel_trapping_eff_forest value
        """
        self._parcel_trapping_eff_forest.value = input_value

    @property
    def max_kernel(self):
        """Getter max_kernel parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the max_kernel parameter
        """
        return self._max_kernel

    @max_kernel.setter
    def max_kernel(self, input_value):
        """Assign the max_kernel parameter

        Parameters
        ----------
        input_value: int
            The max_kernel value
        """
        self._max_kernel.value = input_value

    @property
    def max_kernel_river(self):
        """Getter max_kernel_river parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the max_kernel_river parameter
        """
        return self._max_kernel_river

    @max_kernel_river.setter
    def max_kernel_river(self, input_value):
        """Assign the max_kernel_river parameter

        Parameters
        ----------
        input_value: int
            The max_kernel_river value
        """
        self._max_kernel_river.value = input_value

    @property
    def bulk_density(self):
        """Getter bulk_density parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the bulk_density parameter
        """
        return self._bulk_density

    @bulk_density.setter
    def bulk_density(self, input_value):
        """Assign the bulk_density parameter

        Parameters
        ----------
        input_value: int
            The bulk_density value
        """
        self._bulk_density.value = input_value


class WSExtensions(WSMixin):
    def __init__(self):
        """Initialise WSExtensions"""
        self._curve_number = UserChoice(
            "curve number", "extensions", bool, False, False
        )
        self._include_sewers = UserChoice(
            "include sewers", "extensions", bool, False, False
        )
        self._create_ktc_map = UserChoice(
            "create ktc map", "extensions", bool, False, False
        )
        self._create_ktil_map = UserChoice(
            "create ktil map", "extensions", bool, False, False
        )
        self._estimate_clay_content = UserChoice(
            "estimate clay content", "extensions", bool, False, False
        )
        self._include_tillage_direction = UserChoice(
            "include tillage directions", "extensions", bool, False, False
        )
        self._include_buffers = UserChoice(
            "include buffers", "extensions", bool, False, False
        )
        self._include_ditches = UserChoice(
            "include ditches", "extensions", bool, False, False
        )
        self._include_dams = UserChoice(
            "include dams", "extensions", bool, False, False
        )
        self._output_per_river_segment = UserChoice(
            "output per river segment", "extensions", bool, False, False
        )
        self._adjusted_slope = UserChoice(
            "adjusted slope", "extensions", bool, False, False
        )
        self._buffer_reduce_area = UserChoice(
            "buffer reduce area", "extensions", bool, False, False
        )
        self._force_routing = UserChoice(
            "force routing", "extensions", bool, False, False
        )
        self._river_routing = UserChoice(
            "river routing", "extensions", bool, False, False
        )
        self._manual_outlet_selection = UserChoice(
            "manual outlet selection", "extensions", bool, False, False
        )
        self._convert_output = UserChoice(
            "convert output", "extensions", bool, False, False
        )
        self._calibrate = UserChoice("calibrate", "extensions", bool, False, False)
        self._cardinal_routing_river = UserChoice(
            "cardinal routing river", "extensions", bool, False, False
        )

    @property
    def curve_number(self):
        """Getter curve_number extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the curve_number extension"""
        return self._curve_number

    @curve_number.setter
    def curve_number(self, input_value):
        """Set curve_number extension

        Parameters
        ----------
        input_value: bool
        """
        self._curve_number.value = input_value

    @property
    def include_sewers(self):
        """Getter include_sewers extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the include_sewers extension"""
        return self._include_sewers

    @include_sewers.setter
    def include_sewers(self, input_value):
        """Set include_sewers extension

        Parameters
        ----------
        input_value: bool
        """
        self._include_sewers.value = input_value

    @property
    def create_ktc_map(self):
        """Getter create_ktc_map extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the create_ktc_map extension"""
        return self._create_ktc_map

    @create_ktc_map.setter
    def create_ktc_map(self, input_value):
        """Set create_ktc_map extension

        Parameters
        ----------
        input_value: bool
        """
        self._create_ktc_map.value = input_value

    @property
    def create_ktil_map(self):
        """Getter create_ktil_map extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the create_ktil_map extension"""
        return self._create_ktil_map

    @create_ktil_map.setter
    def create_ktil_map(self, input_value):
        """Set create_ktil_map extension

        Parameters
        ----------
        input_value: bool
        """
        self._create_ktil_map.value = input_value

    @property
    def estimate_clay_content(self):
        """Getter estimate_clay_content extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the estimate_clay_content extension"""
        return self._estimate_clay_content

    @estimate_clay_content.setter
    def estimate_clay_content(self, input_value):
        """Set estimate_clay_content extension

        Parameters
        ----------
        input_value: bool
        """
        self._estimate_clay_content.value = input_value

    @property
    def include_tillage_direction(self):
        """Getter include_tillage_direction extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the include_tillage_direction extension"""
        return self._include_tillage_direction

    @include_tillage_direction.setter
    def include_tillage_direction(self, input_value):
        """Set include_tillage_direction extension

        Parameters
        ----------
        input_value: bool
        """
        self._include_tillage_direction.value = input_value

    @property
    def include_buffers(self):
        """Getter include_buffers extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the include_buffers extension"""
        return self._include_buffers

    @include_buffers.setter
    def include_buffers(self, input_value):
        """Set include_buffers extension

        Parameters
        ----------
        input_value: bool
        """
        self._include_buffers.value = input_value

    @property
    def include_ditches(self):
        """Getter include_ditches extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the include_ditches extension"""
        return self._include_ditches

    @include_ditches.setter
    def include_ditches(self, input_value):
        """Set include_ditches extension

        Parameters
        ----------
        input_value: bool
        """
        self._include_ditches.value = input_value

    @property
    def include_dams(self):
        """Getter include_dams extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the include_dams extension"""
        return self._include_dams

    @include_dams.setter
    def include_dams(self, input_value):
        """Set include_dams extension

        Parameters
        ----------
        input_value: bool
        """
        self._include_dams.value = input_value

    @property
    def output_per_river_segment(self):
        """Getter output_per_river_segment extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the output_per_river_segment extension"""
        return self._output_per_river_segment

    @output_per_river_segment.setter
    def output_per_river_segment(self, input_value):
        """Set output_per_river_segment extension

        Parameters
        ----------
        input_value: bool
        """
        self._output_per_river_segment.value = input_value

    @property
    def adjusted_slope(self):
        """Getter adjusted_slope extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the adjusted_slope extension"""
        return self._adjusted_slope

    @adjusted_slope.setter
    def adjusted_slope(self, input_value):
        """Set adjusted_slope extension

        Parameters
        ----------
        input_value: bool
        """
        self._adjusted_slope.value = input_value

    @property
    def buffer_reduce_area(self):
        """Getter buffer_reduce_area extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the buffer_reduce_area extension"""
        return self._buffer_reduce_area

    @buffer_reduce_area.setter
    def buffer_reduce_area(self, input_value):
        """Set buffer_reduce_area extension

        Parameters
        ----------
        input_value: bool
        """
        self._buffer_reduce_area.value = input_value

    @property
    def force_routing(self):
        """Getter force_routing extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the force_routing extension"""
        return self._force_routing

    @force_routing.setter
    def force_routing(self, input_value):
        """Set force_routing extension

        Parameters
        ----------
        input_value: bool
        """
        self._force_routing.value = input_value

    @property
    def river_routing(self):
        """Getter river_routing extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the river_routing extension"""
        return self._river_routing

    @river_routing.setter
    def river_routing(self, input_value):
        """Set river_routing extension

        Parameters
        ----------
        input_value: bool
        """
        self._river_routing.value = input_value

    @property
    def manual_outlet_selection(self):
        """Getter manual_outlet_selection extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the manual_outlet_selection extension"""
        return self._manual_outlet_selection

    @manual_outlet_selection.setter
    def manual_outlet_selection(self, input_value):
        """Set manual_outlet_selection extension

        Parameters
        ----------
        input_value: bool
        """
        self._manual_outlet_selection.value = input_value

    @property
    def convert_output(self):
        """Getter convert_output extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the convert_output extension"""
        return self._convert_output

    @convert_output.setter
    def convert_output(self, input_value):
        """Set convert_output extension

        Parameters
        ----------
        input_value: bool
        """
        self._convert_output.value = input_value

    @property
    def calibrate(self):
        """Getter calibrate extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the calibrate extension"""
        return self._calibrate

    @calibrate.setter
    def calibrate(self, input_value):
        """Set calibrate extension

        Parameters
        ----------
        input_value: bool
        """
        self._calibrate.value = input_value

    @property
    def cardinal_routing_river(self):
        """Getter cardinal_routing_river extension

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the cardinal_routing_river extension"""
        return self._cardinal_routing_river

    @cardinal_routing_river.setter
    def cardinal_routing_river(self, input_value):
        """Set cardinal_routing_river extension

        Parameters
        ----------
        input_value: bool
        """
        self._cardinal_routing_river.value = input_value


class WSExtensionsParameters(WSMixin):
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
            int,
            self._extensions.include_sewers.value,
        )
        self._clay_content_parent_material = UserChoice(
            "clay content parent material",
            "parameters extensions",
            float,
            self._extensions.estimate_clay_content.value,
        )
        self._antecedent_rainfall = UserChoice(
            "antecedent rainfall",
            "parameters extensions",
            float,
            self._extensions.curve_number.value,
        )
        self._stream_velocity = UserChoice(
            "stream velocity",
            "parameters extensions",
            float,
            self._extensions.curve_number.value,
        )
        self._alpha = UserChoice(
            "alpha",
            "parameters extensions",
            float,
            self._extensions.curve_number.value,
        )
        self._beta = UserChoice(
            "beta",
            "parameters extensions",
            float,
            self._extensions.curve_number.value,
        )
        self._ls_correction = UserChoice(
            "ls correction", "parameters extensions", None, float, False
        )
        self._ktc_low = UserChoice(
            "ktc low",
            "parameters extensions",
            float,
            self._extensions.create_ktc_map.value,
        )
        self._ktc_high = UserChoice(
            "ktc high",
            "parameters extensions",
            float,
            self._extensions.create_ktc_map.value,
        )
        self._ktc_limit = UserChoice(
            "ktc limit",
            "parameters extensions",
            float,
            (self._extensions.create_ktc_map.value or self._extensions.calibrate.value),
        )
        self._ktil_default = UserChoice(
            "ktil default",
            "parameters extensions",
            float,
            self._extensions.create_ktil_map.value,
        )
        self._ktil_threshold = UserChoice(
            "ktil threshold",
            "parameters extensions",
            float,
            self._extensions.create_ktil_map.value,
        )
        self._desired_timestep = UserChoice(
            "desired timestep",
            "parameters extensions",
            int,
            self._extensions.curve_number.value,
        )
        self._final_timestep = UserChoice(
            "final timestep",
            "parameters extensions",
            int,
            (
                self._extensions.curve_number.value
                and self._extensions.convert_output.value
            ),
        )
        self._endtime_model = UserChoice(
            "endtime model",
            "parameters extensions",
            int,
            self._extensions.curve_number.value,
        )

    @property
    def sewer_exit(self):
        """Getter sewer_exit parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the sewer_exit parameter
        """
        return self._sewer_exit

    @sewer_exit.setter
    def sewer_exit(self, input_value):
        """Assign the sewer_exit parameter

        Parameters
        ----------
        input_value: int
            The sewer_exit value
        """
        self._sewer_exit.value = input_value

    @property
    def clay_content_parent_material(self):
        """Getter clay_content_parent_material parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the clay_content_parent_material parameter
        """
        return self._clay_content_parent_material

    @clay_content_parent_material.setter
    def clay_content_parent_material(self, input_value):
        """Assign the clay_content_parent_material parameter

        Parameters
        ----------
        input_value: int
            The clay_content_parent_material value
        """
        self._clay_content_parent_material.value = input_value

    @property
    def antecedent_rainfall(self):
        """Getter antecedent_rainfall parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the antecedent_rainfall parameter
        """
        return self._antecedent_rainfall

    @antecedent_rainfall.setter
    def antecedent_rainfall(self, input_value):
        """Assign the antecedent_rainfall parameter

        Parameters
        ----------
        input_value: int
            The antecedent_rainfall value
        """
        self._antecedent_rainfall.value = input_value

    @property
    def stream_velocity(self):
        """Getter stream_velocity parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the stream_velocity parameter
        """
        return self._stream_velocity

    @stream_velocity.setter
    def stream_velocity(self, input_value):
        """Assign the stream_velocity parameter

        Parameters
        ----------
        input_value: int
            The stream_velocity value
        """
        self._stream_velocity.value = input_value

    @property
    def alpha(self):
        """Getter alpha parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the alpha parameter
        """
        return self._alpha

    @alpha.setter
    def alpha(self, input_value):
        """Assign the alpha parameter

        Parameters
        ----------
        input_value: int
            The alpha value
        """
        self._alpha.value = input_value

    @property
    def beta(self):
        """Getter beta parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the beta parameter
        """
        return self._beta

    @beta.setter
    def beta(self, input_value):
        """Assign the beta parameter

        Parameters
        ----------
        input_value: int
            The beta value
        """
        self._beta.value = input_value

    @property
    def ls_correction(self):
        """Getter ls_correction parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the ls_correction parameter
        """
        return self._ls_correction

    @ls_correction.setter
    def ls_correction(self, input_value):
        """Assign the ls_correction parameter

        Parameters
        ----------
        input_value: int
            The ls_correction value
        """
        self._ls_correction.value = input_value

    @property
    def ktc_low(self):
        """Getter ktc_low parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the ktc_low parameter
        """
        return self._ktc_low

    @ktc_low.setter
    def ktc_low(self, input_value):
        """Assign the ktc_low parameter

        Parameters
        ----------
        input_value: int
            The ktc_low value
        """
        self._ktc_low.value = input_value

    @property
    def ktc_high(self):
        """Getter ktc_high parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the ktc_high parameter
        """
        return self._ktc_high

    @ktc_high.setter
    def ktc_high(self, input_value):
        """Assign the ktc_high parameter

        Parameters
        ----------
        input_value: int
            The ktc_high value
        """
        self._ktc_high.value = input_value

    @property
    def ktc_limit(self):
        """Getter ktc_limit parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the ktc_limit parameter
        """
        return self._ktc_limit

    @ktc_limit.setter
    def ktc_limit(self, input_value):
        """Assign the ktc_limit parameter

        Parameters
        ----------
        input_value: int
            The ktc_limit value
        """
        self._ktc_limit.value = input_value

    @property
    def ktil_default(self):
        """Getter ktil_default parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the ktil_default parameter
        """
        return self._ktil_default

    @ktil_default.setter
    def ktil_default(self, input_value):
        """Assign the ktil_default parameter

        Parameters
        ----------
        input_value: int
            The ktil_default value
        """
        self._ktil_default.value = input_value

    @property
    def ktil_threshold(self):
        """Getter ktil_threshold parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the ktil_threshold parameter
        """
        return self._ktil_threshold

    @ktil_threshold.setter
    def ktil_threshold(self, input_value):
        """Assign the ktil_threshold parameter

        Parameters
        ----------
        input_value: int
            The ktil_threshold value
        """
        self._ktil_threshold.value = input_value

    @property
    def desired_timestep(self):
        """Getter desired_timestep parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the desired_timestep parameter
        """
        return self._desired_timestep

    @desired_timestep.setter
    def desired_timestep(self, input_value):
        """Assign the desired_timestep parameter

        Parameters
        ----------
        input_value: int
            The desired_timestep value
        """
        self._desired_timestep.value = input_value

    @property
    def final_timestep(self):
        """Getter final_timestep parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the final_timestep parameter
        """
        return self._final_timestep

    @final_timestep.setter
    def final_timestep(self, input_value):
        """Assign the final_timestep parameter

        Parameters
        ----------
        input_value: int
            The final_timestep value
        """
        self._final_timestep.value = input_value

    @property
    def endtime_model(self):
        """Getter endtime_model parameter

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice object of the endtime_model parameter
        """
        return self._endtime_model

    @endtime_model.setter
    def endtime_model(self, input_value):
        """Assign the endtime_model parameter

        Parameters
        ----------
        input_value: int
            The endtime_model value
        """
        self._endtime_model.value = input_value


class WSOutput(WSMixin):
    def __init__(self):
        """Initialise WSOutput"""
        self._write_aspect = UserChoice("write aspect", "output", bool, False, False)
        self._write_ls_factor = UserChoice(
            "write ls factor", "output", bool, False, False
        )
        self._write_upstream_area = UserChoice(
            "write upstream area", "output", bool, False, False
        )
        self._write_slope = UserChoice("write slope", "output", bool, False, False)
        self._write_routing_table = UserChoice(
            "write routing table", "output", bool, False, False
        )
        self._write_routing_column_row = UserChoice(
            "write routing column/row", "output", bool, False, False
        )
        self._write_rusle = UserChoice("write rusle", "output", bool, False, False)
        self._write_sediment_export = UserChoice(
            "write sediment export", "output", bool, False, False
        )
        self._write_water_erosion = UserChoice(
            "write water erosion", "output", bool, False, False
        )
        self._write_rainfall_excess = UserChoice(
            "write rainfall excess", "output", bool, False, False
        )
        self._write_total_runoff = UserChoice(
            "write total runoff", "output", bool, False, False
        )
        self._export_saga = UserChoice(
            "Export .sgrd grids", "output", bool, False, False
        )

    @property
    def write_aspect(self):
        """Getter write_aspect output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_aspect output option
        """
        return self._write_aspect

    @write_aspect.setter
    def write_aspect(self, input_value):
        """Set the write_aspect output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_aspect.value = input_value

    @property
    def write_ls_factor(self):
        """Getter write_ls_factor output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_ls_factor output option
        """
        return self._write_ls_factor

    @write_ls_factor.setter
    def write_ls_factor(self, input_value):
        """Set the write_ls_factor output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_ls_factor.value = input_value

    @property
    def write_upstream_area(self):
        """Getter write_upstream_area output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_upstream_area output option
        """
        return self._write_upstream_area

    @write_upstream_area.setter
    def write_upstream_area(self, input_value):
        """Set the write_upstream_area output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_upstream_area.value = input_value

    @property
    def write_slope(self):
        """Getter write_slope output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_slope output option
        """
        return self._write_slope

    @write_slope.setter
    def write_slope(self, input_value):
        """Set the write_slope output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_slope.value = input_value

    @property
    def write_routing_table(self):
        """Getter write_routing_table output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_routing_table output option
        """
        return self._write_routing_table

    @write_routing_table.setter
    def write_routing_table(self, input_value):
        """Set the write_routing_table output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_routing_table.value = input_value

    @property
    def write_routing_column_row(self):
        """Getter write_routing_column_row output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_routing_column_row output option
        """
        return self._write_routing_column_row

    @write_routing_column_row.setter
    def write_routing_column_row(self, input_value):
        """Set the write_routing_column_row output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_routing_column_row.value = input_value

    @property
    def write_rusle(self):
        """Getter write_rusle output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_rusle output option
        """
        return self._write_rusle

    @write_rusle.setter
    def write_rusle(self, input_value):
        """Set the write_rusle output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_rusle.value = input_value

    @property
    def write_sediment_export(self):
        """Getter write_sediment_export output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_sediment_export output option
        """
        return self._write_sediment_export

    @write_sediment_export.setter
    def write_sediment_export(self, input_value):
        """Set the write_sediment_export output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_sediment_export.value = input_value

    @property
    def write_water_erosion(self):
        """Getter write_water_erosion output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_water_erosion output option
        """
        return self.write_water_erosion

    @write_water_erosion.setter
    def write_water_erosion(self, input_value):
        """Set the write_water_erosion output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_water_erosion.value = input_value

    @property
    def write_rainfall_excess(self):
        """Getter write_rainfall_excess output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_rainfall_excess output option
        """
        return self._write_rainfall_excess

    @write_rainfall_excess.setter
    def write_rainfall_excess(self, input_value):
        """Set the write_rainfall_excess output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_rainfall_excess.value = input_value

    @property
    def write_total_runoff(self):
        """Getter write_total_runoff output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the write_total_runoff output option
        """
        return self._write_total_runoff

    @write_total_runoff.setter
    def write_total_runoff(self, input_value):
        """Set the write_total_runoff output option

        Parameters
        ----------
        input_value:bool
        """
        self._write_total_runoff.value = input_value

    @property
    def export_saga(self):
        """Getter export_saga output option

        Returns
        -------
        pywatemsedem.choices.UserChoice
            UserChoice instance of the export_saga output option
        """
        return self._export_saga

    @export_saga.setter
    def export_saga(self, input_value):
        """Set the export_saga output option

        Parameters
        ----------
        input_value:bool
        """
        self._export_saga.value = input_value


class PyVariables:
    def __init__(self):
        """Initialise PyWSVariables"""
        self._start_year = None
        self._start_month = None
        self._sewer_inlet_efficiency = None
        self._spatial_resolution = None


class PyOptions:
    def __init__(self):
        """Initialise PyWSOptions"""
        self._filter_dtm = None
        self._only_sewers_in_infrastructure = None
        self._maximize_gras_strips = None
        self._use_gras = None
        self._use_crop_management = None
