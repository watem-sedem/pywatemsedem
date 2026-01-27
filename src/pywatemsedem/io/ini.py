import configparser
import datetime
import logging
import re
import warnings

from pywatemsedem.templates import InputFileName

logger = logging.getLogger(__name__)

inputfilename = InputFileName()


class IniFile:
    """Create WaTEM/SEDEM ini-file

    Parameters
    ----------
    inputfolder: pathlib.Path
        WaTEM/SEDEM inputfolder
    outputfolder: pathlib.Path
        WaTEM/SEDEM outputfolder

    Examples
    --------
    >>> choices = Choices(...)
    >>> forced_routing = ...
    >>> buffers = ...
    >>> inifile = IniFile(choices,"WS","modelinput","modeloutput")
    >>> inifile.add_model_information()
    >>> inifile.add_working_directories()
    >>> inifile.add_files()
    >>> inifile.add_parameters()
    >>> inifile.add_options()
    >>> inifile.add_output()
    >>> inifile.add_extensions(buffers, forced_routing, river_underground)
    >>> inifile.write("modelinput/ini_file.ini")
    """

    def __init__(self, inputfolder, outputfolder, choices):
        """Creates an ini-file for the scenario"""

        self.cnwsinput_folder = inputfolder
        self.cnwsoutput_folder = outputfolder
        self.cfg = configparser.ConfigParser()
        self.choices = choices

    def write(self, ini):
        """Write ini file to disk"""
        with open(ini, "w") as f:
            self.cfg.write(f)
            f.close()

    def add_sections(self):
        self.cfg.add_section("Model information")
        self.cfg.add_section("Working directories")
        self.cfg.add_section("Files")
        self.cfg.add_section("Parameters")
        self.cfg.add_section("Output")
        self.cfg.add_section("Options")
        self.cfg.add_section("Extensions")
        self.cfg.add_section("Parameters Extensions")

    def add_model_information(self):
        """Add section model information to config file"""

        self.cfg.set(
            "Model information",
            "Date",
            datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        )

    def add_working_directories(self):
        """Add section working directory to config file"""
        self.cfg.set(
            "Working directories", "Input directory", str(self.cnwsinput_folder)
        )
        self.cfg.set(
            "Working directories",
            "Output directory",
            str(self.cnwsoutput_folder),
        )

    def add_files(self):
        """Add section files to config file"""
        self.cfg.set(
            "Files",
            "DTM filename",
            (self.cnwsinput_folder / inputfilename.dtm_file).name,
        )
        self.cfg.set(
            "Files",
            "P factor map filename",
            (self.cnwsinput_folder / inputfilename.pfactor_file).name,
        )
        self.cfg.set(
            "Files",
            "shapefile catchment",
            (self.cnwsinput_folder / inputfilename.mask_file).name,
        )

        self.cfg.set(
            "Files",
            "Parcel filename",
            (self.cnwsinput_folder / inputfilename.parcelmosaic_file).name,
        )
        if not self.choices.options.only_routing.value:
            self.cfg.set(
                "Files",
                "C factor map filename",
                (self.cnwsinput_folder / inputfilename.cfactor_file).name,
            )

            self.cfg.set(
                "Files",
                "K factor filename",
                (self.cnwsinput_folder / inputfilename.kfactor_file).name,
            )

        else:
            msg = "Ini-file for version 'Only Routing' not implemented."
            raise IOError(msg)

    def add_parameters(self):
        """Add section parameters to config file"""
        for key in self.choices.parameters.__dict__:
            attribute = getattr(self.choices.parameters, key)
            if attribute.value is not None:
                self.cfg.set("Parameters", key, str(attribute.value))

    def add_output(self):
        """Add section outputs config file"""
        for key in self.choices.output.__dict__:
            attribute = getattr(self.choices.output, key)
            if attribute.value is not None:
                self.cfg.set("Output", key, str(attribute.value))

    def add_options(self):
        """Adds specified model options to the configuration."""
        for key in self.choices.options.__dict__:
            attribute = getattr(self.choices.options, key)
            if attribute.value is not None:
                self.cfg.set("Options", key, str(attribute.value))

    def add_extensions(self, buffers, forced_routing, river_underground):
        """Add section parameters and parameters extensions to config file

        Parameters
        ----------
        buffers: pandas.DataFrame
            Holding buffer properties, with columns,

            - *buffercap* (float): Volume
            - *hdam* (float): Height dam
            - *hknijp^* (float): Height opening
            - *dknijp* (float): Opening area
            - *qcoef* (float): Discharge coefficient
            - *boverl* (float): Width dam
            - *eff* (float): Trapping efficiency
            - *BUF_EXID* (float): Extension ID
            - *BUF_ID* (float): Buffer id

        forced_routing: pandas.DataFrame
            Forced routing table with columns,
            see :ref:`here <watemsedem:forcedroutingdata>`

            - *NR* (int):
            - *from col* (int): source pixel column
            - *from row* (int): source pixel row
            - *target col* (int): target pixel column
            - *target row* (int): target pixel row

        river_underground: pandas.DataFrame
            River underground routing table with columns, see
            :ref:`here <watemsedem:forcedroutingdata>`

            - *NR* (int):
            - *from col* (int): source pixel column
            - *from row* (int): source pixel row
            - *target col* (int): target pixel column
            - *target row* (int): target pixel row
        """
        self.add_river_segment_output_extension()
        self.add_clay_content_extension()
        self.add_manual_outlet_extension()
        self.add_ditches_extension()
        self.add_dams_extensions()
        self.add_sewer_extension()
        self.add_ditches_extension()
        self.add_clay_content_extension()
        self.add_cn_extension()
        self.add_ktil_extension()
        self.add_ktc_and_calibration_extensions()
        self.add_river_routing_extension()
        self.add_include_buffer_extension(buffers)
        self.add_force_routing_extension(forced_routing, river_underground)

        self.cfg.set(
            "Parameters Extensions",
            "LS correction",
            str(self.choices.extensionparameters.ls_correction.value),
        )

        self.cfg.set(
            "Extensions",
            "Adjusted Slope",
            str(self.choices.extensions.adjusted_slope.value),
        )
        self.cfg.set(
            "Extensions",
            "Buffer reduce Area",
            str(self.choices.extensions.buffer_reduce_area.value),
        )

    def add_river_segment_output_extension(self):
        """Add output per river segment extension to config file"""
        if self.choices.extensions.output_per_river_segment.value:
            # output per rivier segment?
            self.cfg.set("Extensions", "Output per river segment", "1")

            self.cfg.set(
                "Files",
                "River segment filename",
                (self.cnwsinput_folder / inputfilename.segments_file).name,
            )

    def add_manual_outlet_extension(self):
        """Add manual outlet selection extension to config file"""
        if self.choices.extensions.manual_outlet_selection.value:
            # manual outlet
            self.cfg.set(
                "Extensions",
                "Manual outlet selection",
                "1",
            )

            self.cfg.set(
                "Files",
                "Outlet map filename",
                (self.cnwsinput_folder / inputfilename.outlet_file).name,
            )

    def add_clay_content_extension(self):
        """Add clay content estimation extension to config file"""
        if self.choices.extensions.estimate_clay_content.value:
            # estimate clay content extenison
            self.cfg.set(
                "Extensions",
                "Estimate clay content",
                "1",
            )

            self.cfg.set(
                "Parameters Extensions",
                "Clay content parent material",
                str(int(self.choices.extensionparameters.clay_content_parent_material)),
            )

    def add_ditches_extension(self):
        """Add ditches extension to config file"""
        if self.choices.extensions.include_ditches.value:
            # Include ditches
            self.cfg.set(
                "Extensions",
                "Include ditches",
                "1",
            )

            self.cfg.set(
                "Files",
                "Ditch map filename",
                (self.cnwsinput_folder / inputfilename.ditches_files).name,
            )

    def add_dams_extensions(self):
        """add dams extension to config file"""
        if self.choices.extensions.include_dams.value:
            # Include dams
            self.cfg.set("Extensions", "Include dams", "1"),

            self.cfg.set(
                "Files",
                "Dam map filename",
                (self.cnwsinput_folder / inputfilename.conductivedams_file).name,
            )

    def add_sewer_extension(self):
        """Add sewer extension to config file"""
        if self.choices.extensions.include_sewers.value:
            # Include sewers
            self.cfg.set(
                "Extensions",
                "Include sewers",
                "1",
            )
            self.cfg.set(
                "Parameters Extensions",
                "Sewer exit",
                str(self.choices.extensionparameters.sewer_exit.value),
            )
            self.cfg.set(
                "Files",
                "Sewer map filename",
                (self.cnwsinput_folder / inputfilename.endpoints_file).name,
            )

    def add_include_buffer_extension(self, buffers):
        """Add buffer extension and buffer parameters to config file

        Parameters
        ----------
        buffers: pandas.DataFrame
            Holding buffer properties, with columns,

            - *buffercap* (float): Volume
            - *hdam* (float): Height dam
            - *hknijp^* (float): Height opening
            - *dknijp* (float): Opening area
            - *qcoef* (float): Discharge coefficient
            - *boverl* (float): Width dam
            - *eff* (float): Trapping efficiency
            - *BUF_EXID* (float): Extension ID
            - *BUF_ID* (float): Buffer id
        """
        # Include buffers
        self.cfg.set(
            "Extensions",
            "Include buffers",
            str(self.choices.extensions.include_buffers.value),
        )
        if self.choices.extensions.include_buffers.value:
            buffers = [] if buffers is None else buffers
            self.cfg.set(
                "Files",
                "Buffer map filename",
                (self.cnwsinput_folder / inputfilename.buffers_file).name,
            )
            self.cfg.set(
                "Parameters Extensions", "Number of buffers", str(len(buffers))
            )
            if len(buffers) != 0:
                for row in buffers.iterrows():
                    section = f"Buffer {row[1]['buf_id']}"
                    self.cfg.add_section(section)
                    self.cfg.set(section, "Volume", f"{row[1]['buffercap']}")
                    self.cfg.set(section, "Height dam", f"{row[1]['hdam']}")
                    self.cfg.set(section, "Height opening", f"{row[1]['hknijp']}")
                    self.cfg.set(section, "Opening area", f"{row[1]['dknijp']}")
                    self.cfg.set(
                        section, "Discharge coefficient", f" {row[1]['qcoef']}"
                    )
                    self.cfg.set(section, "Width dam", f"{row[1]['boverl']}")
                    self.cfg.set(section, "Trapping efficiency", f"{row[1]['eff']}")
                    self.cfg.set(section, "Extension ID", f"{row[1]['buf_exid']}")

    def add_force_routing_extension(self, forced_routing, river_underground):
        """Add force routing extension and force routing parameters to config file

        Parameters
        ----------
        forced_routing: pandas.DataFrame
            Forced routing table with columns,
            see :ref:`here <watemsedem:forcedroutingdata>`

            - *NR* (int):
            - *from col* (int): source pixel column
            - *from row* (int): source pixel row
            - *target col* (int): target pixel column
            - *target row* (int): target pixel row

        river_underground: pandas.DataFrame
            River underground routing table with columns, see
            :ref:`here <watemsedem:forcedroutingdata>`

            - *NR* (int):
            - *from col* (int): source pixel column
            - *from row* (int): source pixel row
            - *target col* (int): target pixel column
            - *target row* (int): target pixel row
        """
        # force routing
        self.cfg.set(
            "Extensions",
            "Force Routing",
            str(self.choices.extensions.force_routing.value),
        )
        if self.choices.extensions.force_routing.value:
            forced_routing = [] if forced_routing is None else forced_routing
            river_underground = [] if river_underground is None else river_underground
            n_fr = len(forced_routing)
            n_ru = len(river_underground)
            n = n_ru + n_fr
            if n > 0:
                self.cfg.set(
                    "Parameters Extensions",
                    "Number of Forced Routing",
                    str(n),
                )
            if n_fr > 0:
                for nr, row in enumerate(forced_routing.itertuples()):
                    section = f"Forced Routing {nr + 1}"
                    self.cfg.add_section(section)
                    self.cfg.set(section, "from col", f"{int(row.fromcol)}")
                    self.cfg.set(section, "from row", f"{int(row.fromrow)}")
                    self.cfg.set(section, "target col", f"{int(row.tocol)}")
                    self.cfg.set(section, "target row", f"{int(row.torow)}")
            elif n_ru > 0:
                for nr, row in enumerate(river_underground.itertuples()):
                    section = f"Forced Routing {nr + 1}"
                    self.cfg.add_section(section)
                    self.cfg.set(section, "from col", f"{int(row.fromcol)}")
                    self.cfg.set(section, "from row", f"{int(row.fromrow)}")
                    self.cfg.set(section, "target col", f"{int(row.tocol)}")
                    self.cfg.set(section, "target row", f"{int(row.torow)}")
            else:
                msg = (
                    "'Force Routing' in 'dict_model_options' is equal to 1, but no "
                    "forced routing or underground or river vectors defined."
                )
                warnings.warn(msg)

    def add_river_routing_extension(self):
        """Add river routing extension to config file and
        the needed files for this extension"""
        if self.choices.extensions.river_routing.value:
            self.cfg.set(
                "Extensions",
                "river routing",
                str(self.choices.extensions.river_routing.value),
            )
            self.cfg.set(
                "Files",
                "adjectant segments",
                (self.cnwsinput_folder / inputfilename.adjacentedges_file).name,
            )
            self.cfg.set(
                "Files",
                "upstream segments",
                (self.cnwsinput_folder / inputfilename.upedges_file).name,
            )
            self.cfg.set(
                "Files",
                "river routing filename",
                (self.cnwsinput_folder / inputfilename.routing_file).name,
            )

    def add_ktc_and_calibration_extensions(self):
        """Add create ktc map and calibration extensions and
        their extension parameters to config file"""
        if self.choices.extensions.calibrate.value:
            self.cfg.add_section("Calibration")
            self.cfg.set(
                "Extensions",
                "Calibrate",
                str(self.choices.extensions.calibrate.value),
            )
            self.cfg.set(
                "Calibration",
                "KTcHigh_lower",
                str(self.choices.extensionparameters["KTcHigh_lower"]),
            )
            self.cfg.set(
                "Calibration",
                "KTcHigh_upper",
                str(self.choices.dict_variables["KTcHigh_upper"]),
            )
            self.cfg.set(
                "Calibration",
                "KTcLow_lower",
                str(self.choices.dict_variables["KTcLow_lower"]),
            )
            self.cfg.set(
                "Calibration",
                "KTcLow_upper",
                str(self.choices.dict_variables["KTcLow_upper"]),
            )
            self.cfg.set(
                "Calibration", "steps", str(self.choices.dict_variables["steps"])
            )
            self.cfg.set(
                "Parameters",
                "ktc limit",
                str(self.choices.parameters.ktc_limit.value),
            )
        elif (
            not self.choices.extensions.create_ktc_map.value
        ):  # pywatemsedem must provide ktc map to watem-sedem
            self.cfg.set("Extensions", "Create ktc map", "0")
            self.cfg.set(
                "Files",
                "ktc map filename",
                (self.cnwsinput_folder / inputfilename.ktc_file).name,
            )

        else:
            self.cfg.set(
                "Extensions", "Create ktc map", "1"
            )  # watem-sedem will create ktc map
            self.cfg.set(
                "Parameters Extensions",
                "ktc low",
                str(self.choices.extensionparameters.ktc_low.value),
            )
            self.cfg.set(
                "Parameters Extensions",
                "ktc high",
                str(self.choices.extensionparameters.ktc_high.value),
            )
            self.cfg.set(
                "Parameters Extensions",
                "ktc limit",
                str(self.choices.extensionparameters.ktc_limit.value),
            )

    def add_ktil_extension(self):
        """Add create ktil map extension and its extension parameters to config file"""
        if self.choices.options.calculate_tillage_erosion.value:
            self.cfg.set(
                "Extensions",
                "Create ktil map",
                str(self.choices.extensions.create_ktil_map.value),
            )
            if self.choices.extensions.create_ktil_map.value:
                self.cfg.set(
                    "Parameters Extensions",
                    "ktil default",
                    str(self.choices.extensionparameters.ktil_default.value),
                )
                self.cfg.set(
                    "Parameters Extensions",
                    "ktil threshold",
                    str(self.choices.extensionparameters.ktil_threshold.value),
                )
            else:
                self.cfg.set(
                    "Files",
                    "ktil map filename",
                    (self.cnwsinput_folder / inputfilename.ktil_file).name,
                )

    def add_cn_extension(self):
        """Add CN-extension and its extension parameters/files to config file"""
        if self.choices.extensions.curve_number.value:
            self.cfg.set("Extensions", "Curve Number", "1")
            self.cfg.set(
                "Parameters Extensions",
                "Alpha",
                str(self.choices.extensionparameters.alpha.value),
            )
            self.cfg.set(
                "Parameters Extensions",
                "Beta",
                str(self.choices.extensionparameters.beta.value),
            )
            self.cfg.set(
                "Parameters Extensions",
                "Stream velocity",
                str(self.choices.extensionparameters.stream_velocity.value),
            )
            self.cfg.set(
                "Files",
                "CN map filename",
                (self.cnwsinput_folder / inputfilename.cn_file).name,
            )
            self.cfg.set(
                "Files",
                "Rainfall filename",
                "Rainfall.txt",  # TODO: define in templates
            )
            self.cfg.set(
                "Parameters Extensions",
                "5-day antecedent rainfall",
                str(self.choices.extensionparameters.antecedent_rainfall.value),
            )
            self.cfg.set(
                "Parameters Extensions",
                "Desired timestep for model",
                str(self.choices.extensionparameters.desired_timestep.value),
            )
            self.cfg.set(
                "Parameters Extensions",
                "Endtime model",
                str(self.choices.extensionparameters.endtime_model),
            )
            if self.choices.extensions.convert_output.value:
                self.cfg.set(
                    "Extensions",
                    "Convert output",
                    str(self.choices.extensions.convert_output.value),
                )
                self.cfg.set(
                    "Parameters Extensions",
                    "Final timestep output",
                    str(self.choices.extensionparameters.final_timestep),
                )


def open_ini(ini):
    """Open ini file.

    Parameters
    ----------
    ini: pathlib.Path

    Returns
    -------
    content: list
    """
    with open(ini, "r") as file:
        content = file.readlines()
    return content


def modify_field(ini, section, key, value):
    """Add one specific key in ini-file

    Loads, writes value to key (in section) and closes file

    Parameters
    ----------
    ini: pathlib.Path
        File name
    section: str
        Section name, i.e. Model information, Working directories, Files, User Choices,
        Output , Variables, Calibration, Buffer $id and Forced Routing $id.
    key: str
        Key
    new_value: str
        New value
    ini_updated: pathlib.Path, default None
        New file to write to
    """
    # Init
    content = open_ini(ini)
    section_pattern = re.compile(rf"^\[{re.escape(section)}\]\s*$")
    key_pattern = re.compile(rf"^{re.escape(key)}\s*=")
    in_section = False
    in_key = False

    # Modify
    for i, line in enumerate(content):
        if section_pattern.match(line):
            in_section = True
        elif in_section and key_pattern.match(line):
            content[i] = f"{key} = {value}\n"
            in_key = True
            break

    # Warning
    if not in_section:
        msg = (
            f"Cannot modify '{value}' to '{key}'. Section '{section}' does not exist "
            f"in '{ini}'."
        )
        raise KeyError(msg)
    if not in_key:
        msg = (
            f"Cannot modify '{value}' to '{key}'. Key '{key}' does not exist in "
            f"'{ini}'."
        )
        raise KeyError(msg)

    # Write the modified content back to the file
    with open(ini, "w") as file:
        msg = f"Modifying '{value}' to '{key}' in file '{ini}'"
        logger.info(msg)
        file.writelines(content)


def add_field(ini, section, key, value):
    """Add one specific key in ini-file

    Loads, writes value to key (in section) and closes file

    Parameters
    ----------
    ini: pathlib.Path
        File name
    section: str
        Section name, i.e. Model information, Working directories, Files, User Choices,
        Output , Variables, Calibration, Buffer $id and Forced Routing $id.
    key: str
        Key
    value: str
        New value

    """
    # Init
    content = open_ini(ini)
    section_pattern = re.compile(rf"^\[{re.escape(section)}\]\s*$")
    key_pattern = re.compile(rf"^{re.escape(key)}\s*=")
    in_section = False

    # Modify
    for i, line in enumerate(content):
        if section_pattern.match(line):
            in_section = True
        elif in_section and line.startswith("["):
            content_before_insertion = content[: i - 1]
            content_after_insertion = content[i:]
            content = (
                content_before_insertion
                + [f"{key} = {value} \n \n"]
                + content_after_insertion
            )
            break
        elif in_section and key_pattern.match(line):
            msg = (
                f"Cannot add '{value}' to '{key}'. Key '{key}' already exist in "
                f"'{ini}'."
            )
            raise KeyError(msg)
        elif in_section and i == (len(content) - 1):
            content = content + [f"{key} = {value}\n"]

    # Warning
    if not in_section:
        msg = (
            f"Cannot add '{value}' to '{key}'. Section '{section}' does not exist "
            f"in '{ini}'."
        )
        raise KeyError(msg)

    # Write the modified content back to the file
    with open(ini, "w") as file:
        msg = f"Adding '{value}' to '{key}' in file '{ini}'"
        logger.info(msg)
        file.writelines(content)


def get_item_from_ini(ini, section, option, dtype):
    """Gets an item from an option in a certain section of an ini-file

    Parameters
    ----------
    ini: pathlib.Path
        File path of the ini-file
    section: str
        Name of the desired section
    option: str
        Name of the desired option
    dtype: dtype
        Type of parameter to be read (str, int, float or bool).
        If another string is given to this parameter, a
        TypeError is raised.

    Returns
    -------
    str or int or float or bool or None
        Settings value of ini-file. If the option or section does not exist in
        the ini-file or the value of the section-option None is returned.
    """

    cfg = configparser.ConfigParser()
    if ini.exists():
        cfg.read(ini)
        try:
            if dtype == str:
                a = cfg.get(section, option)
            elif dtype == int:
                a = cfg.getint(section, option)
            elif dtype == float:
                a = cfg.getfloat(section, option)
            elif dtype == bool:
                a = cfg.getboolean(section, option)
            else:
                raise TypeError("not a correct Type")
        except configparser.NoOptionError:
            msg = f"Option {option} does not exist in ini-file (section {section})"
            raise ValueError(msg)
        except configparser.NoSectionError:
            msg = f"Section {section} does not exist in ini-file"
            raise ValueError(msg)
        else:
            return a
    else:
        raise FileNotFoundError(f"{ini} does not exist")
