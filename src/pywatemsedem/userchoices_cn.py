import datetime
import logging

# Standard libraries
import pathlib
from pathlib import Path

import pandas as pd

from pywatemsedem.tools import check_courant_criterium

logger = logging.getLogger(__name__)


def set_userchoices_curvenumber(
    type_cn_storage,
    txt_rainfall_filename,
    rainfall_depth_antecedent,
    begin_date,
    end_date,
    time_step_event,
    days_antecedent,
    resolution,
    stream_velocity,
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
    stream_velocity: float
        Stream velocity (m/s)
    """
    if txt_rainfall_filename is not None:
        type_cn_storage = "filestorage"

    userchoices_curvenumber = UserChoicesCurveNumber(type_cn_storage, resolution)

    (
        txt_rainfall_filename,
        rainfall_depth_antecedent,
        begin_date,
        end_date,
        days_antecedent,
        time_step_event,
    ) = userchoices_curvenumber.check(
        txt_rainfall_filename,
        rainfall_depth_antecedent,
        begin_date,
        end_date,
        time_step_event,
        days_antecedent,
        stream_velocity=stream_velocity,
    )


class UserChoicesCurveNumber:
    """User choices for Curve-Number model."""

    def __init__(self, type_cn_storage, resolution):
        """Initialise UserChoicesCurveNumber."""
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
