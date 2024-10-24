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
    choices: pywatemsedem.pywatemsedem.chocies.UserChoices
        See :class:`pywatemsedem.pywatemsedem.userchoices.UserChoices`
    version: str
        Model version
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
    >>> inifile.add_user_choices()
    >>> inifile.add_output_maps()
    >>> inifile.add_variables(buffers, forced_routing, river_underground)
    >>> inifile.write("modelinput/ini_file.ini")
    """

    def __init__(self, choices, version, inputfolder, outputfolder):
        """Creates an ini-file for the scenario"""

        self.cnwsinput_folder = inputfolder
        self.cnwsoutput_folder = outputfolder
        self.choices = choices
        self.version = version
        self.cfg = configparser.ConfigParser()

    def write(self, ini):
        """Write ini file to disk"""
        with open(ini, "w") as f:
            self.cfg.write(f)
            f.close()

    def add_model_information(self):
        """Add section model information to config file"""
        self.cfg.add_section("Model information")
        self.cfg.set(
            "Model information",
            "Date",
            datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        )

    def add_working_directories(self):
        """Add section working directory to config file"""
        self.cfg.add_section("Working directories")
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
        self.cfg.add_section("Files")
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
        if self.version != "Only Routing":
            self.cfg.set(
                "Files",
                "C factor map filename",
                (self.cnwsinput_folder / inputfilename.cfactor_file).name,
            )
        else:
            msg = "Ini-file for version 'Only Routing' not implemented."
            raise IOError(msg)

    def add_user_choices(self):
        """Add section user choices to config file"""
        self.cfg.add_section("User Choices")
        self.cfg.set(
            "User Choices", "Max kernel", str(self.choices.dict_variables["Max kernel"])
        )
        self.cfg.set(
            "User Choices",
            "Max kernel river",
            str(self.choices.dict_variables["Max kernel river"]),
        )

    def add_output_maps(self):
        """Add section outputs config file"""
        self.cfg.add_section("Output maps")
        self.cfg.set(
            "Output maps", "Write aspect", str(self.choices.dict_output["Write aspect"])
        )
        self.cfg.set(
            "Output maps",
            "Write LS factor",
            str(self.choices.dict_output["Write LS factor"]),
        )
        self.cfg.set(
            "Output maps",
            "Write rainfall excess",
            str(self.choices.dict_output["Write rainfall excess"]),
        )
        self.cfg.set(
            "Output maps", "Write RUSLE", str(self.choices.dict_output["Write RUSLE"])
        )
        self.cfg.set(
            "Output maps",
            "Write sediment export",
            str(self.choices.dict_output["Write sediment export"]),
        )
        self.cfg.set(
            "Output maps", "Write slope", str(self.choices.dict_output["Write slope"])
        )
        self.cfg.set(
            "Output maps",
            "Write total runoff",
            str(self.choices.dict_output["Write total runoff"]),
        )
        self.cfg.set(
            "Output maps",
            "Write upstream area",
            str(self.choices.dict_output["Write upstream area"]),
        )
        self.cfg.set(
            "Output maps",
            "Write water erosion",
            str(self.choices.dict_output["Write water erosion"]),
        )
        self.cfg.set(
            "Output maps",
            "Write routing table",
            str(self.choices.dict_output["Write routing table"]),
        )

        self.cfg.set(
            "Output maps",
            "Write routing column/row",
            str(self.choices.dict_output["Write routing table"]),
        )

    def add_variables(self, buffers, forced_routing, river_underground):
        """Add section variables to config file

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
            Forced routing table with columns, see :ref:`here <watemsedem:forcedroutingdata>`

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
        self.cfg.add_section("Variables")
        self.cfg.set(
            "Variables",
            "Parcel connectivity grasstrips",
            str(int(self.choices.dict_variables["Parcel connectivity grasstrips"])),
        )
        self.cfg.set(
            "Variables",
            "Parcel connectivity cropland",
            str(int(self.choices.dict_variables["Parcel connectivity cropland"])),
        )
        self.cfg.set(
            "Variables",
            "Parcel connectivity forest",
            str(int(self.choices.dict_variables["Parcel connectivity forest"])),
        )
        self.cfg.set(
            "Variables",
            "Parcel trapping efficiency cropland",
            str(
                int(self.choices.dict_variables["Parcel trapping efficiency cropland"])
            ),
        )
        self.cfg.set(
            "Variables",
            "Parcel trapping efficiency forest",
            str(int(self.choices.dict_variables["Parcel trapping efficiency forest"])),
        )
        self.cfg.set(
            "Variables",
            "Parcel trapping efficiency pasture",
            str(int(self.choices.dict_variables["Parcel trapping efficiency pasture"])),
        )
        self.cfg.set(
            "Variables",
            "LS correction",
            str(self.choices.dict_variables["LS correction"]),
        )

        self.set_cfg_model_version()

        # output per rivier segment?
        self.cfg.set(
            "User Choices",
            "Output per river segment",
            str(self.choices.dict_output["Output per river segment"]),
        )
        # if self.choices.dict_output["Output per river segment"] == 1:
        self.cfg.set(
            "Files",
            "River segment filename",
            (self.cnwsinput_folder / inputfilename.segments_file).name,
        )

        # manual outlet
        self.cfg.set(
            "User Choices",
            "Manual outlet selection",
            str(self.choices.dict_model_options["Manual outlet selection"]),
        )
        if self.choices.dict_model_options["Manual outlet selection"] == 1:
            self.cfg.set(
                "Files",
                "Outlet map filename",
                (self.cnwsinput_folder / inputfilename.outlet_file).name,
            )

        self.set_cfg_only_routing()

        # Grachten gebruiken?
        self.cfg.set(
            "User Choices",
            "Include ditches",
            str(self.choices.dict_ecm_options["Include ditches"]),
        )
        if self.choices.dict_ecm_options["Include ditches"] == 1:
            self.cfg.set(
                "Files",
                "Ditch map filename",
                (self.cnwsinput_folder / inputfilename.ditches_files).name,
            )

        # Geleidende dammen gebruiken?
        self.cfg.set(
            "User Choices",
            "Include dams",
            str(self.choices.dict_ecm_options["Include dams"]),
        )
        if self.choices.dict_ecm_options["Include dams"] == 1:
            self.cfg.set(
                "Files",
                "Dam map filename",
                (self.cnwsinput_folder / inputfilename.conductivedams_file).name,
            )

        # Using sewers
        self.cfg.set(
            "User Choices",
            "Include sewers",
            str(self.choices.dict_model_options["Include sewers"]),
        )
        if self.choices.dict_model_options["Include sewers"] == 1:
            self.cfg.set(
                "Variables",
                "Sewer exit",
                str(self.choices.dict_variables["Sewer exit"]),
            )
            self.cfg.set(
                "Files",
                "Sewer map filename",
                (self.cnwsinput_folder / inputfilename.endpoints_file).name,
            )

        # Using buffers in model?
        self.cfg.set(
            "User Choices",
            "Include buffers",
            str(self.choices.dict_ecm_options["Include buffers"]),
        )
        if self.choices.dict_ecm_options["Include buffers"] == 1:
            buffers = [] if buffers is None else buffers
            self.cfg.set(
                "Files",
                "Buffer map filename",
                (self.cnwsinput_folder / inputfilename.buffers_file).name,
            )
            self.cfg.set("Variables", "Number of buffers", str(len(buffers)))
            if len(buffers) != 0:
                for row in buffers.iterrows():
                    sectie = f"Buffer {row[1]['buf_id']}"
                    self.cfg.add_section(sectie)
                    self.cfg.set(sectie, "Volume", f"{row[1]['buffercap']}")
                    self.cfg.set(sectie, "Height dam", f"{row[1]['hdam']}")
                    self.cfg.set(sectie, "Height opening", f"{row[1]['hknijp']}")
                    self.cfg.set(sectie, "Opening area", f"{row[1]['dknijp']}")
                    self.cfg.set(sectie, "Discharge coefficient", f" {row[1]['qcoef']}")
                    self.cfg.set(sectie, "Width dam", f"{row[1]['boverl']}")
                    self.cfg.set(sectie, "Trapping efficiency", f"{row[1]['eff']}")
                    self.cfg.set(sectie, "Extension ID", f"{row[1]['buf_exid']}")

        # force routing
        self.cfg.set(
            "User Choices",
            "Force Routing",
            str(self.choices.dict_model_options["Force Routing"]),
        )
        if self.choices.dict_model_options["Force Routing"] == 1:
            forced_routing = [] if forced_routing is None else forced_routing
            river_underground = [] if river_underground is None else river_underground
            n_fr = len(forced_routing)
            n_ru = len(river_underground)
            n = n_ru + n_fr
            if n > 0:
                self.cfg.set(
                    "Variables",
                    "Number of Forced Routing",
                    str(n),
                )
            if n_fr > 0:
                for nr, row in enumerate(forced_routing.itertuples()):
                    sectie = f"Forced Routing {nr+1}"
                    self.cfg.add_section(sectie)
                    self.cfg.set(sectie, "from col", f"{int(row.fromcol)}")
                    self.cfg.set(sectie, "from row", f"{int(row.fromrow)}")
                    self.cfg.set(sectie, "target col", f"{int(row.tocol)}")
                    self.cfg.set(sectie, "target row", f"{int(row.torow)}")
            elif n_ru > 0:
                for nr, row in enumerate(river_underground.itertuples()):
                    sectie = f"Forced Routing {nr + 1}"
                    self.cfg.add_section(sectie)
                    self.cfg.set(sectie, "from col", f"{int(row.fromcol)}")
                    self.cfg.set(sectie, "from row", f"{int(row.fromrow)}")
                    self.cfg.set(sectie, "target col", f"{int(row.tocol)}")
                    self.cfg.set(sectie, "target row", f"{int(row.torow)}")
            else:
                msg = (
                    "'Force Routing' in 'dict_model_options' is equal to 1, but no "
                    "forced routing or underground or river vectors defined."
                )
                warnings.warn(msg)
        # river routing
        if self.choices.dict_model_options["River Routing"] == 1:
            self.cfg.set(
                "User Choices",
                "river routing",
                str(self.choices.dict_model_options["River Routing"]),
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

        # Advanced settings
        if "L model" in self.choices.dict_model_options.keys():
            self.cfg.set(
                "User Choices", "L model", self.choices.dict_model_options["L model"]
            )
        if "S model" in self.choices.dict_model_options.keys():
            self.cfg.set(
                "User Choices", "S model", self.choices.dict_model_options["S model"]
            )
        if "TC model" in self.choices.dict_model_options.keys():
            self.cfg.set(
                "User Choices", "TC model", self.choices.dict_model_options["TC model"]
            )

        self.cfg.set(
            "User Choices",
            "Adjusted Slope",
            str(self.choices.dict_model_options["Adjusted Slope"]),
        )
        self.cfg.set(
            "User Choices",
            "Buffer reduce Area",
            str(self.choices.dict_model_options["Buffer reduce Area"]),
        )

    def set_cfg_model_version(self):
        """Add model version to self.cfg."""
        if self.version == "CN-WS":
            self.cfg.set("User Choices", "Only WS", "0")
            self.cfg.set(
                "Variables", "Alpha", str(self.choices.dict_variables["Alpha"])
            )
            self.cfg.set("Variables", "Beta", str(self.choices.dict_variables["Beta"]))
            self.cfg.set(
                "Variables",
                "Stream velocity",
                str(self.choices.dict_variables["Stream velocity"]),
            )
            self.cfg.set(
                "Files",
                "CN map filename",
                (self.cnwsinput_folder / inputfilename.cn_file).name,
            )

        else:  # WS-model
            self.cfg.set("User Choices", "Only WS", "1")
            if self.version == "Only Routing":
                self.cfg.set("User Choices", "Only Routing", "1")

    def set_cfg_only_routing(self):
        """Add variables for only routing version of WaTEM/SEDEM."""
        if self.version != "Only Routing":
            self.cfg.set(
                "Files",
                "K factor filename",
                (self.cnwsinput_folder / inputfilename.kfactor_file).name,
            )
            self.cfg.set(
                "Variables",
                "Bulk density",
                str(int(self.choices.dict_variables["Bulk density"])),
            )

            # R-factor of regenvalfile?
            self.cfg.set(
                "Variables",
                "R factor",
                str(self.choices.dict_variables["R factor"]),
            )
            self.cfg.set("Variables", "Endtime model", "0")  # Aan te passen in model?
            if self.version == "CN-WS":
                self.cfg.set(
                    "Files",
                    "Rainfall filename",
                    "Rainfall.txt",  # TODO: define in templates
                )
                self.cfg.set(
                    "Variables",
                    "5-day antecedent rainfall",
                    str(self.choices.dict_variables["5-day antecedent rainfall"]),
                )
                self.cfg.set(
                    "Variables",
                    "Desired timestep for model",
                    str(self.choices.dict_variables["Desired timestep for model"]),
                )
                self.cfg.set(
                    "Variables",
                    "Endtime model",
                    str(self.choices.dict_variables["Endtime model"]),
                )
                if self.choices.dict_model_options["Convert output"] == 1:
                    self.cfg.set(
                        "User Choices",
                        "Convert output",
                        str(self.choices.dict_model_options["Convert output"]),
                    )
                    self.cfg.set(
                        "Variables",
                        "Final timestep output",
                        str(self.choices.dict_variables["Final timestep output"]),
                    )

            # KTC and calibration KTC
            if self.choices.dict_model_options["Calibrate"] == 1:
                self.cfg.add_section("Calibration")
                self.cfg.set(
                    "Calibration",
                    "Calibrate",
                    str(self.choices.dict_model_options["Calibrate"]),
                )
                self.cfg.set(
                    "Calibration",
                    "KTcHigh_lower",
                    str(self.choices.dict_variables["KTcHigh_lower"]),
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
                    "Variables",
                    "ktc limit",
                    str(self.choices.dict_variables["ktc limit"]),
                )
            elif self.choices.dict_model_options["UserProvidedKTC"] == 1:
                self.cfg.set("User Choices", "Create ktc map", "0")
                self.cfg.set(
                    "Files",
                    "ktc map filename",
                    (self.cnwsinput_folder / inputfilename.ktc_file).name,
                )

            else:
                self.cfg.set("User Choices", "Create ktc map", "1")
                self.cfg.set(
                    "Variables", "ktc low", str(self.choices.dict_variables["ktc low"])
                )
                self.cfg.set(
                    "Variables",
                    "ktc high",
                    str(self.choices.dict_variables["ktc high"]),
                )
                self.cfg.set(
                    "Variables",
                    "ktc limit",
                    str(self.choices.dict_variables["ktc limit"]),
                )

            # KTIL
            self.cfg.set(
                "User Choices",
                "Calculate Tillage Erosion",
                str(self.choices.dict_model_options["Calculate Tillage Erosion"]),
            )
            if self.choices.dict_model_options["Calculate Tillage Erosion"] == 1:
                self.cfg.set(
                    "User Choices",
                    "Create ktil map",
                    str(self.choices.dict_model_options["Create ktil map"]),
                )
                if self.choices.dict_model_options["Create ktil map"] == 1:
                    self.cfg.set(
                        "Variables",
                        "ktil default",
                        str(self.choices.dict_variables["ktil default"]),
                    )
                    self.cfg.set(
                        "Variables",
                        "ktil threshold",
                        str(self.choices.dict_variables["ktil threshold"]),
                    )

            self.cfg.set(
                "User Choices",
                "Estimate clay content",
                str(self.choices.dict_model_options["Estimate clay content"]),
            )
            if self.choices.dict_model_options["Estimate clay content"] == 1:
                self.cfg.set(
                    "Variables",
                    "Clay content parent material",
                    str(
                        int(self.choices.dict_variables["Clay content parent material"])
                    ),
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

    Cfg = configparser.ConfigParser()
    if ini.exists():
        Cfg.read(ini)
        try:
            if dtype == str:
                a = Cfg.get(section, option)
            elif dtype == int:
                a = Cfg.getint(section, option)
            elif dtype == float:
                a = Cfg.getfloat(section, option)
            elif dtype == bool:
                a = Cfg.getboolean(section, option)
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
