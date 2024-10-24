import datetime
import logging

# Standard libraries
import pathlib
from pathlib import Path

import pandas as pd

from pywatemsedem.io.ini import get_item_from_ini
from pywatemsedem.tools import check_courant_criterium

logger = logging.getLogger(__name__)


class UserChoices:
    def __init__(self):
        self.version = None
        self.dict_ecm_options = {}
        self.dict_model_options = {}
        self.dict_variables = {}
        self.dict_output = {}

    def set_ecm_options(self, defaultini=None):
        """Set the erosion control options for the scenario.

        The possible keys are:

        - 'Include buffers': use bufferbasins
        - 'UseGras': use grasstrips
        - 'Include dams': use dams
        - 'Include ditches': use ditches
        - 'UseTeelttechn': use culture specific measures (like strip till,...)

        Parameters
        ----------
        defaultini : str or pathlib.Path, optional
            ini-file with section 'ECMOptions' and one or more of the above
            mentioned keys as parameters
        """
        lst_mandatory_keys = [
            "Include buffers",
            "UseGras",
            "Include dams",
            "Include ditches",
            "UseTeelttechn",
        ]

        for key in lst_mandatory_keys:
            if key not in self.dict_ecm_options:
                # read key from default values
                if defaultini is not None:
                    defaultvalue = get_item_from_ini(defaultini, "ECMOptions", key, int)
                    msg = (
                        f"{key} is not given in the ECM options, "
                        f"default value ({defaultvalue}) is used"
                    )
                    logger.warning(msg)
                else:
                    defaultvalue = None

                if defaultvalue is not None:
                    self.dict_ecm_options[key] = defaultvalue
                else:
                    msg = f"No defaultvalue for ECMOption {key} given"
                    raise ValueError(msg)

    def set_model_version(self, version):
        """Set the model version to be used in the scenario.

        The model-version will be stored in the variables.

        Parameters
        ----------
        version: str
            'CN-WS' or 'WS' or 'Only Routing'
        """
        if version == "WS":
            self.version = version
            self.dict_variables["Only WS"] = 1
        elif version == "CN-WS":
            self.version = version
            self.dict_variables["Only WS"] = 0
        elif version == "Only Routing":
            self.version = "Only Routing"
            self.dict_variables["Only WS"] = 1
        else:
            msg = "No correct model version is chosen, please select 'WS' of 'CN-WS'"
            raise ValueError(msg)

    def set_transport_capacity_equation(self, TC="VanOost2000"):
        """Set the transport capacity equation model for the scenario.

        The chosen values will be stored in the ``ModelOptions``.

        Parameters
        ----------
        TC: 'VanOost2000' or 'Verstraeten2007', optional, default 'VanOost2000'
            Name of the transport capacity equation model.
        """
        self.set_model_equation("TC model", TC, ["VanOost2000", "Verstraeten2007"])

    def set_LS_equation(self, L="Desmet1996_Vanoost2003", S="Nearing1997"):
        """Set the L and S-model for the scenario.

        The chosen values will be stored in the ``ModelOptions``.

        Parameters
        ----------
        L: 'Desmet1996_Vanoost2003' or 'Desmet1996_McCool', optional, default
            'Desmet1996_Vanoost2003'
            Name of the L model.
        S: 'Nearing1997' or 'McCool1987', optional, default 'Nearing1997'
            Name of the S model.
        """
        self.set_model_equation(
            "L model", L, ["Desmet1996_Vanoost2003", "Desmet1996_McCool"]
        )
        self.set_model_equation("S model", S, ["Nearing1997", "McCool1987"])

    def set_model_equation(self, type_model, model_equation, lst_possible_equations):
        """Set the equation for a specific model according to a reference

        Parameters
        ----------
        type_model: str
            Name type of model.
        model_equation: str
            Specific reference for model equation, e.g. L according to
            "Desmet1996_Vanoost2003".
        lst_possible_equations: list
            Possible references to equation

        Note
        ----
        See example use in :func:`pywatemsedem.CNWS.UserChoices.set_LS_equation`.
        """
        if model_equation in lst_possible_equations:
            self.dict_model_options[type_model] = model_equation
        else:
            msg = (
                f"No correct {type_model} was given! please choose "
                f"{', '.join(lst_possible_equations)}."
            )
            raise KeyError(msg)

    def set_model_options(self, defaultini=None):
        """Set the ModelOptions for the scenario.

        The possible keys are:

        - 'Convert output'
        - 'CreateKTIL'
        - 'Estimate clay content'
        - 'Manual outlet selection'
        - 'Calibrate'
        - 'Adjusted Slope'
        - 'Buffer reduce Area'
        - 'Force Routing'
        - 'FilterDTM'
        - 'River Routing'

        When the modelversion is 'WS' one can also define 'UseR' as a key.

        Parameters
        ----------
        defaultini : str or pathlib.Path, optional
            ini-file with section 'Options' and one or more of the above
            mentioned keys as parameters
        """

        lst_mandatory_keys = [
            "Convert output",
            "Manual outlet selection",
            "Include sewers",
            "UserProvidedKTC",
            "Adjusted Slope",
            "Buffer reduce Area",
            "Force Routing",
            "FilterDTM",
            "River Routing",
            "OnlyInfraSewers",
            "Maximize grass strips",
        ]

        lst_extra_keys = [
            "Estimate clay content",
            "Calculate Tillage Erosion",
            "Create ktil map",
            "Calibrate",
        ]

        # if self.version == 'WS':
        #    lst_mandatory_keys.append('UseR')

        if self.version != "Only Routing":
            lst_mandatory_keys = lst_mandatory_keys + lst_extra_keys

        for key in lst_mandatory_keys:
            if key not in self.dict_model_options:
                if defaultini is not None:
                    # read key from default values
                    defaultvalue = get_item_from_ini(defaultini, "Options", key, int)
                else:
                    defaultvalue = None

                if defaultvalue is not None:
                    msg = (
                        f"`{key}` is not given in the model options, default "
                        f"value `{defaultvalue}` is used."
                    )
                    logger.warning(msg)
                    self.dict_model_options[key] = defaultvalue
                else:
                    msg = f"No default value for Model Option {key} given"
                    raise ValueError(msg)

        if self.version == "Only Routing":
            for key in lst_extra_keys:
                self.dict_model_options[key] = 0

        return

    def set_model_variables(self, defaultini=None):
        """Set the ModelVariables for the scenario.

        Parameters
        ----------
        defaultini : str or pathlib.Path, optional
            ini-file with section 'Variables' and one or more of the above
            mentioned keys as parameters

        Notes
        -----
        The possible keys are: 'Bulk density', 'ktc limit',
        'Parcel connectivity cropland', 'Parcel connectivity forest',
        'Parcel trapping efficiency cropland', 'Parcel trapping efficiency forest',
        'Parcel trapping efficiency pasture', 'begin_jaar', 'begin_maand',
        'Max kernel', 'Max kernel river'/

        When the CN-module is used, additional variables are needed: 'Alpha',
        'Beta', 'Stream velocity', 'CNTable'.

        When Rainfalldata is used (i.e. WS and UseR=0 or CNWS), additional variables
        are needed: '5-day antecedent rainfall', 'Desired timestep for model',
        'Endtime model', 'Final timestep output', 'Rainfall filename'.

        If no Rainfalldata is used (i.e. WS using a general R-factor) add the 'R'
        variable.

        When calibrating the WS model, define 'KTcHigh_lower', 'KTcHigh_upper',
        'KTcLow_lower', 'KTcLow_upper' and 'steps'.

        Without calibrating, define 'ktc low', 'ktc high'.

        When the ModelOption['CreateKTIL'] is 1, define 'ktil default' and
        'ktil threshold'.

        When the ModelOption['Estimate clay content'] is 1, define
        'Clay content parent material'.

        When the ModelOption['Manual outlet selection']  is 1, define 'Outletshp'.

        When the ModelOption['Force Routing'] is 1, define 'Routingshp'.
        """
        lst_mandatory_keys = [
            "Parcel connectivity cropland",
            "Parcel connectivity forest",
            "Parcel connectivity grasstrips",
            "Parcel trapping efficiency cropland",
            "Parcel trapping efficiency forest",
            "Parcel trapping efficiency pasture",
            "begin_jaar",
            "begin_maand",
            "Max kernel",
            "Max kernel river",
            "Bulk density",
            "LS correction",
        ]

        lst_cn_keys = ["Alpha", "Beta", "Stream velocity"]

        lst_rainfall_keys = [
            "5-day antecedent rainfall",
            "Desired timestep for model",
            "Endtime model",
            "Final timestep output",
        ]

        if self.dict_model_options["Calibrate"] == 1:
            lst_ktc_keys = [
                "KTcHigh_lower",
                "KTcHigh_upper",
                "KTcLow_lower",
                "KTcLow_upper",
                "steps",
                "ktc limit",
            ]
        else:
            lst_ktc_keys = ["ktc low", "ktc high", "ktc limit"]

        lst_mandatory_keys += lst_ktc_keys

        if self.dict_model_options["Create ktil map"] == 1:
            lst_ktil_keys = ["ktil default", "ktil threshold"]
            lst_mandatory_keys += lst_ktil_keys

        if self.version == "CN-WS":
            lst_mandatory_keys += lst_cn_keys
            lst_mandatory_keys += lst_rainfall_keys

        lst_mandatory_keys.append("R factor")

        if self.dict_model_options["Estimate clay content"] == 1:
            lst_mandatory_keys.append("Clay content parent material")

        # if self.dict_model_options["Manual outlet selection"] == 1:
        #    lst_mandatory_keys.append("Outletshp")

        # if self.dict_model_options["Force Routing"] == 1:
        #    lst_mandatory_keys.append("Routingshp")

        if self.dict_model_options["Include sewers"] == 1:
            lst_sewer_keys = ["SewerInletEff", "Sewer exit"]
            lst_mandatory_keys += lst_sewer_keys

        for key in lst_mandatory_keys:
            if key not in self.dict_variables:
                if defaultini is not None:
                    if key in [
                        "ktc limit",
                        "ktc low",
                        "ktc high",
                        "ktil threshold",
                        "Alpha",
                        "Beta",
                        "Stream velocity",
                        "LS correction",
                    ]:
                        T = float
                    elif key in [
                        "Outletshp",
                        "Routingshp",
                    ]:
                        T = str
                    else:
                        T = int

                    # read key from default values
                    defaultvalue = get_item_from_ini(defaultini, "Variables", key, T)
                    msg = (
                        f"`{key}` is not given in the model variables, default"
                        f" value ({defaultvalue}) is used."
                    )
                    logger.warning(msg)
                else:
                    defaultvalue = None

                if defaultvalue is not None:
                    self.dict_variables[key] = defaultvalue
                else:
                    msg = f"No value for variable {key} given in default values"
                    raise ValueError(msg)
        return

    def set_output(self, defaultini=None):
        """Set the modeloutput for the scenario.

        The possible keys are:
        'Write aspect', 'Write LS factor', 'Write RUSLE', 'Write sediment export',
        'Write slope', 'WriteTotalRunof', 'Write upstream area', 'Write water erosion'

        Parameters
        ----------
        defaultini : str or pathlib.Path, optional
            ini-file with section 'Output' and one or more of the above
            mentioned keys as parameters
        """

        lst_mandatory_keys = [
            "Write aspect",
            "Write LS factor",
            "Write slope",
            "Write upstream area",
            "Output per river segment",
            "Write routing table",
        ]

        lst_ws_keys = ["Write RUSLE", "Write sediment export", "Write water erosion"]
        lst_cn_keys = ["Write rainfall excess", "Write total runoff"]

        if self.version == "WS" or self.version == "CN-WS":
            lst_mandatory_keys = lst_mandatory_keys + lst_ws_keys
        else:  # Only Routing
            for key in lst_ws_keys:
                self.dict_output[key] = 0

        if self.version == "CN-WS":
            lst_mandatory_keys += lst_cn_keys
        else:  # WS en Only Routing
            for key in lst_cn_keys:
                self.dict_output[key] = 0

        for key in lst_mandatory_keys:
            if key not in self.dict_output:
                if defaultini is not None:
                    # read key from default values
                    defaultvalue = get_item_from_ini(defaultini, "Output", key, int)
                    msg = (
                        f"`{key}` is not given in the model options, default "
                        f"value ({defaultvalue}) is used."
                    )
                    logger.warning(msg)
                else:
                    defaultvalue = None

                if defaultvalue is not None:
                    self.dict_output[key] = defaultvalue
                else:
                    msg = (
                        f"No value for Model Output {key} given in default " f"values."
                    )
                    raise ValueError(msg)
        return

    def set_userchoices_curvenumber(
        self,
        type_cn_storage,
        txt_rainfall_filename,
        rainfall_depth_antecedent,
        begin_date,
        end_date,
        time_step_event,
        days_antecedent,
        resolution,
    ):
        """Set userchoices for Curve-Number model.

        Parameters
        ----------
        type_cn_storage: str
            "filestorage" or "database" storage.
        txt_rainfall_filename: str
            See :func:`pywatemsedem.CNWS.UserChoicesCurveNumber.check`
        rainfall_depth_antecedent: int
            Antecedent rainfall depth (mm).
        begin_date: pandas.DateTime
            See :func:`pywatemsedem.userchoices.UserChoicesCurveNumber.check`
        end_date: pandas.DateTime
            See :func:`pywatemsedem.userchoices.UserChoicesCurveNumber.check`
        time_step_event: int
            See :func:`pywatemsedem.userchoices.UserChoicesCurveNumber.check`
        days_antecedent: int
            See :func:`pywatemsedem.userchoices.UserChoicesCurveNumber.check`
        resolution: int
            Spatial resolution.
        """
        if txt_rainfall_filename is not None:
            type_cn_storage = "filestorage"

        userchoices_curvenumber = UserChoicesCurveNumber(type_cn_storage, resolution)
        (
            self.txt_rainfall_filename,
            self.rainfall_depth_antecedent,
            self.begin_date,
            self.end_date,
            self.days_antecedent,
            self.time_step_event,
        ) = userchoices_curvenumber.check(
            txt_rainfall_filename,
            rainfall_depth_antecedent,
            begin_date,
            end_date,
            time_step_event,
            days_antecedent,
            stream_velocity=self.dict_variables["Stream velocity"],
        )
        self.dict_variables["Desired timestep for model"] = self.time_step_event


class UserChoicesCurveNumber:
    def __init__(self, type_cn_storage, resolution):

        self.type_cn_storage = type_cn_storage
        self.resolution = resolution

    def check(
        self,
        txt_rainfall_filename=None,
        rainfall_depth_antecedent=None,
        begin_date=None,
        end_date=None,
        time_step_event=None,
        days_antecedent=None,
        stream_velocity=None,
    ):
        """Set the settings for an event based on whether a filesystem or database
        storage system is used. In a filebased system, a reference to a rainfall
        data file has to be given, with an amount of antecedent rainfall. In the
        other case the begin and end date have to be given, along with the days of
        antecedent, and the time step of an event.

        Parameters
        ----------
        txt_rainfall_filename: pathlib.Path or str, optional
            File path to rainfall input data file. This file is a headerless text
            file with two columns. The first column contains the time in minutes
            (starting from 0), the second column contains the rainfall in mm.
        rainfall_depth_antecedent: int or float
            Cumulative amount of rainfall in days_antecedent.
        begin_date: pandas.Timestamp, optional
            Begin rainfall timerseries, in UTC, make use of pd.Timestamp, see Note 1.
        end_date: pandas.Timestamp, optional
            End rainfall timerseries, in UTC, make use of pd.Timestamp, see Note 1.
        time_step_event: int
            Time step event.
        days_antecedent: int or float, optional
            Number of days for antecedent
        stream_velocity: float
            Stream velocity (m/s)

        Returns
        -------
        See `Parameters`.

        Note
        ----
        1. Use of begin_date_event and end_date_event is for example, with UTC as
        timezone:

        .. code-block:: python

            begin_date = pandas..to_datetime("2018-01-01", utc=True)
            end_date = pandas.to_datetime("2018-01-15", utc=True)

        """
        self.rainfall_filename = txt_rainfall_filename
        self.rainfall_depth_antecedent = rainfall_depth_antecedent

        if not isinstance(begin_date, pd.Timestamp) or not isinstance(
            end_date, pd.Timestamp
        ):
            msg = (
                "Begin date and end date should be a pandas.Timestamp object in UTC, "
                "use `begin_date = pd.to_datetime('YYYY-MM-DD' utc=True)`."
            )
            raise TypeError(msg)
        if (str(begin_date.tz) == "UTC") and (str(end_date.tz) == "UTC"):
            self.begin_date = begin_date
            self.end_date = end_date
        else:
            msg = (
                "Use timezone-UTC to define begin and end date, "
                "use `begin_date = pd.to_datetime('YYYY-MM-DD' utc=True)`."
            )
            raise IOError(msg)

        self.days_antecedent = days_antecedent
        self.time_step_event = time_step_event

        if self.type_cn_storage == "filestorage":

            self.check_choices_cn_filestorage()

        elif self.type_cn_storage == "databasestorage":

            self.check_choices_cn_databasestorage()

        if stream_velocity is not None:
            self.time_step_event = check_courant_criterium(
                stream_velocity, self.time_step_event, self.resolution
            )

        return (
            self.rainfall_filename,
            self.rainfall_depth_antecedent,
            self.begin_date,
            self.end_date,
            self.days_antecedent,
            self.time_step_event,
        )

    def check_choices_cn_filestorage(self):
        """Set the settings for an event for a filesystem storage system is used."""
        self.begin_date = None
        self.end_date = None
        self.days_antecedent = None

        if not (
            isinstance(self.rainfall_filename, str)
            or isinstance(self.rainfall_filename, pathlib.Path)
        ):
            msg = "Rainfall filename is not of type `str` or `pathlib.Path`."
            raise TypeError(msg)

        if not (
            isinstance(self.rainfall_depth_antecedent, int)
            or isinstance(self.rainfall_depth_antecedent, float)
        ):
            msg = "Rainfall depth antecedent is not or type `int` or `float`."
            raise TypeError(msg)

        if not Path(self.rainfall_filename).exists():
            msg = f"Rainfall filename {self.rainfall_filename} does not exist."
            raise IOError(msg)

    def check_choices_cn_databasestorage(self):
        """Set the settings for an event for a database storage system is used."""
        self.rainfall_filename = None
        self.rainfall_depth_antecedent = None

        if not (isinstance(self.begin_date, datetime.datetime)):
            msg = "Begin date is not of type `datetime.datetime`."
            raise TypeError(msg)

        if not (isinstance(self.end_date, datetime.datetime)):
            msg = "End date is not of type `datetime.datetime`."
            raise TypeError(msg)

        if not (self.end_date > self.begin_date):
            msg = "End date of the event should be later that begin date of the event."
            raise ValueError(msg)

        if not (
            isinstance(self.days_antecedent, int)
            or isinstance(self.days_antecedent, float)
        ):
            msg = "Days antecedent is not of type `float` or `int`."
            raise TypeError(msg)

        if not (
            isinstance(self.time_step_event, int)
            or isinstance(self.time_step_event, float)
        ):
            msg = "Time step event is not of type `float` or `int`."
            raise TypeError(msg)
