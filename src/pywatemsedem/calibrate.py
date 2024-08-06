import logging
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm, colors
from sklearn import linear_model
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)


@dataclass
class Calibration:
    """Data class for calibration parameters.

    Data class used to store all commonly used variables for a calibration run.

    Parameters
    ----------
    ktc_low_min: float
        Lower boundary for ktc low value
    ktc_low_max: float
        Upper boundary for ktc low value
    ktc_high_min: float
        Lower boundary for ktc high value
    ktch_high_max: float
        Upper boundary for ktc high value
    steps: int
        Amount of steps between lower and upper ktc low/high values

    """

    ktc_low_min: float
    ktc_low_max: float
    ktc_high_min: float
    ktc_high_max: float
    steps: int

    def __post_init__(self):

        self.check_input()
        self.define_parameter_grid_resolution()
        self.define_parameter_grid()
        self.df_template = _make_template_df(self.arr_ktc_low, self.arr_ktc_high)

    def check_input(self):
        """Run a number of checks on input data of data class"""
        if self.ktc_low_min > self.ktc_low_max:
            msg = "ktc low min > ktc low max"
            raise ValueError(msg)

        if self.ktc_high_min > self.ktc_high_max:
            msg = "ktc high min > ktc high max"
            raise ValueError(msg)

        if self.steps <= 0:
            msg = "the amount of steps must be larger than zero"
            raise ValueError(msg)

        if self.ktc_low_min < 0:
            msg = "ktc low min must be higher than 0"
            raise ValueError(msg)

        if self.ktc_high_min < 0:
            msg = "ktc high min must be higher than 0"
            raise ValueError(msg)

    def define_parameter_grid_resolution(self):
        """Define the resolution of the parameter grid (2D, x and y resolution)."""
        self.stepresolution_high = (self.ktc_high_max - self.ktc_high_min) / self.steps
        self.stepresolution_low = (self.ktc_low_max - self.ktc_low_min) / self.steps

    def define_parameter_grid(self):
        """Defne parameter grid for ktc low and high"""
        self.arr_ktc_low = np.arange(
            self.ktc_low_min,
            self.ktc_low_max + self.stepresolution_low,
            self.stepresolution_low,
        )
        self.arr_ktc_high = np.arange(
            self.ktc_high_min,
            self.ktc_high_max + self.stepresolution_high,
            self.stepresolution_high,
        )


def _make_template_df(arr_ktc_low, arr_ktc_high):
    """Create a pandas.DataFrame with all combinations of ktc_low and ktc_high

    Parameters
    ----------
    arr_ktc_low: numpy.array
    arr_ktc_high: numpy.array

    Returns
    -------
    df_cal_template: pandas.DataFrame. The DataFrame contains following columns:

        - *ktc_high* (float): high transport capacity coefficient
        - *ktc_low* (float); low transport capacity coefficient

    """
    df_cal_template = pd.DataFrame()
    x = np.unique(arr_ktc_low)
    y = np.unique(arr_ktc_high)
    arr_x, arr_y = np.meshgrid(x, y)
    df_cal_template["ktc_high"] = arr_x.flatten()
    df_cal_template["ktc_low"] = arr_y.flatten()

    return df_cal_template


def process_calibrationrun_output(
    txt_calibration,
    observed_sy,
    catchment_name,
    catchment_area,
    endpoint_coefficient=0.0,
):
    """Processes the output-file of a calibration run for a given catchment

    This function reads the calibration output file for a given catchement and
    calculates for every combination of ktc values the predicted specific
    sediment yield (P ssy) and calculates the squared difference between the
    observed and predicted (specific) sediment yield.

    Parameters
    ----------
    txt_calibration: str or pathlib.Path
        Path to the calibration-output file of a WaTEM/SEDEM model run, see
        :ref:`here <watemsedem:calibrationtxt>`.
    observed_sy: float
        The observed sediment yield for the catchment (in ton).
    catchment_name: str
        The name of the catchment.
    catchment_area: float
        The area of the catchment in ha.
    endpoint_coefficient: float, default 0.
        This coefficient determines the percentual amount of the sediment load
        that is captured in endpoints (sewers and ditches).
        In percentage (% - e.g. 80%). See also
        :func:`pywatemsedem.calibrate.check_endpoint_throughput_coefficient`.

    Returns
    -------
    df_cal: pandas.DataFrame
        DataFrame with all modelled sediment yields for different combinations
        of ktc-values. The DataFrame contains following columns:

        - *name* (string): name of the catchment.
        - *O_sy* (float): observed sediment yield (in ton).
        - *O_ssy* (float): observed specific sediment yield (ton/m$^2$).
        - *P_sy* (float): predicted sediment yield (in ton).
        - *P_ssy* (float): predicted specific sediment yield (ton/m$^2$).
        - *(O_sy-P_sy)* (float): difference between observed and predicted sy.
        - *|O_sy-P_sy|* (float): absolute difference between observed and predicted sy.
        - *(O_sy-P_sy)²* (float): squared difference between observed and predicted sy.
        - *(O_ssy-P_ssy)* (float): difference between observed and predicted ssy.
        - *|O_ssy-P_ssy|* (float): absolute difference between observed and predicted
          ssy.
        - *(O_ssy-P_ssy)²* (float): squared difference between observed and predicted
          ssy.
        - *ktc_low* (float): ktc low value used in the model run.
        - *ktc_high* (float): ktc high value used in the model run.

    """
    check_endpoint_throughput_coefficient(endpoint_coefficient)

    df_cal = pd.read_csv(txt_calibration, sep=";")
    df_cal.drop_duplicates(subset=["ktc_low", "ktc_high"], inplace=True)
    df_cal_template = _make_template_df(df_cal["ktc_low"], df_cal["ktc_high"])

    df_cal = pd.merge(df_cal, df_cal_template, how="right", on=["ktc_low", "ktc_high"])
    df_cal["name"] = catchment_name
    df_cal["O_sy"] = observed_sy
    df_cal["O_ssy"] = observed_sy / catchment_area
    df_cal["P_sy"] = (df_cal["outlet_1"]) / 1000

    if endpoint_coefficient != 0:
        if "sed_sewerin" in df_cal.columns:
            df_cal["P_sy"] = (
                df_cal["P_sy"]
                + df_cal["sed_sewerin"] / 1000 * endpoint_coefficient / 100
            )
        else:
            msg = (
                "No endpoints (sewerin-file) included in pywatemsedem model run, can not add"
                " percentage to estimated sediment yield (P_sy)."
            )
            logger.warning(msg)
    # convert kg to tons
    df_cal["P_ssy"] = df_cal["P_sy"] / catchment_area
    df_cal = compute_model_errors_sy(df_cal, "sy")
    df_cal = compute_model_errors_sy(df_cal, "ssy")

    return df_cal


def compute_model_errors_sy(df_cal, variable):
    """Compute model errors based on simulations and observations.

    - *Errors*: observation-prediction
    - *Absolute errors*: `|observation-prediction|`
    - *Squared errors*: `(observation-prediction)$^2$`

    Parameters
    ----------
    df_cal: pandas.DataFrame
        Definition, see :func:`pywatemsedem.calibrate.process_calibrationrun_output`.
    variable: str
        Name of output variable 'sy' or 'ssy'.

    Returns
    -------
    df_cal: pandas.DataFrame
        Updated with errors between simulation and observations.
    """
    if variable not in ["sy", "ssy"]:
        msg = (
            "Only model error based on sediment yield 'sy' and specific sediment"
            " yield 'ssy' can be computed."
        )
        raise IOError(msg)

    tag = f"O_{variable}-P_{variable}"
    df_cal[f"({tag})"] = df_cal[f"O_{variable}"] - df_cal[f"P_{variable}"]
    df_cal[f"|{tag}|"] = np.abs(df_cal[f"({tag})"])
    df_cal[f"({tag})²"] = df_cal[f"({tag})"] ** 2
    df_cal[f"({tag})²"] = np.where(
        df_cal["ktc_low"] > df_cal["ktc_high"], np.nan, df_cal[f"({tag})²"]
    )

    return df_cal


def check_endpoint_throughput_coefficient(endpoint_coefficient: float):
    """Check the endpoint (sewers and ditches) throughput coefficient used in
    :func:`pywatemsedem.calibrate.process_calibrationrun_output`.

    Raise error if the throughput coefficient is not within the defined ranges.

    Parameters
    ----------
    endpoint_coefficient: float
        Percentage of sediment load to captured in the endpoints (sewers and ditches)
        to consider for the computed predicted sediment load (see also column non river
        in scenario_x/modeloutput/calibration.txt).
    """
    cond = 0 <= endpoint_coefficient <= 100
    if not cond:
        msg = "Defined sewer throughput coefficient of"
        f"`{endpoint_coefficient}` for does not fall within allowed range [0,100]"
        raise IOError(msg)
    else:
        return endpoint_coefficient


def merge_calibration_results(lst_df_calibration, caldata):
    """Check if dimension of calibration space are equal to the one defined in
    the caldata instance (see :class:`pywatemsedem.calibrate.Calibration`)

    Merges a list of pandas.DataFrame with processed calibration model output

    Parameters
    ----------
    lst_df_calibration: list
        Every item in the list is a pandas.DataFrame. For the definition of the
        dataframe, see :func:`pywatemsedem.calibrate.process_calibrationrun_output`.
    caldata: pywatemsedem.core.calibrate.Calibration
        See :class:`pywatemsedem.calibrate.Calibration`

    Returns
    -------
    df_calibration_results: pandas.DataFrame
        DataFrame with all modelled sediment yields for different combinations
        of ktc-values. The DataFrame contains following columns:

        - *name* (string): name of the catchment.
        - *O_sy* (float): observed sediment yield.
        - *O_ssy* (float): observed specific sediment yield.
        - *P_sy* (float): predicted sediment yield.
        - *P_ssy* (float): predicted specific sediment yield.
        - *(O_sy-P_sy)²* (float): squared difference between observed and predicted sy.
        - *(O_ssy-P_ssy)²* (float): squared difference between observed and predicted
          ssy.
        - *ktc_low* (float): ktc low value used in the model run.
        - *ktc_high* (float): ktc high value used in the model run.
    """

    for df in lst_df_calibration:

        name = df["name"].iloc[0]
        msg = (
            f"Not all required calibration sets in the calibration are simulated"
            f" for `{name}`, please check you `calibration.txt` file in"
            f" scenario_x/modeloutput."
        )

        arr_ktc_low_exp = df["ktc_low"].values.astype(float)
        arr_ktc_high_exp = df["ktc_high"].values.astype(float)
        arr_ktc_low = np.arange(
            caldata.ktc_low_min, caldata.ktc_low_max, caldata.steps, dtype=float
        )
        arr_ktc_high = np.arange(
            caldata.ktc_high_min, caldata.ktc_high_max, caldata.steps, dtype=float
        )
        if np.array_equal(np.sort(arr_ktc_low), np.sort(arr_ktc_low_exp)):
            raise ValueError(msg)
        if np.array_equal(np.sort(arr_ktc_high), np.sort(arr_ktc_high_exp)):
            raise ValueError(msg)

    df_calibration_results = pd.concat(lst_df_calibration)

    return df_calibration_results


def linear_regression_evaluation_calibration(arr_observed, arr_predicted):
    """Compute linear regression between observed and predicted values.

    Parameters
    ----------
    arr_observed: np.ndarray or pandas.Series
        Observed (specific) sediment yield.
    arr_predicted: np.ndarray or pandas.Series
        Predicted (specific) sediment yield

    Returns
    -------
    p_reg: float
        See :class:`sklearn.linear_model.LinearRegression`
    r2: float
        See :func:`sklearn.metrics.r2_score`
    rico: float
        First order regression coefficient. See also
        :class:`sklearn.linear_model.LinearRegression`
    """
    regr = linear_model.LinearRegression(fit_intercept=False)
    arr_observed = arr_observed.values.reshape(-1, 1)
    arr_predicted = arr_predicted.values.reshape(-1, 1)
    regr.fit(arr_observed, arr_predicted)
    p_regr = regr.predict(arr_observed)
    r2 = r2_score(arr_predicted, p_regr)
    rico = regr.coef_[0][0]
    return p_regr, r2, rico


def calculate_model_efficiency(df_calibration_data, df_calibration_results):
    """Calculates the model efficiency (ME) for a calibration data set.

    The model efficiency calculations are for now based on the Nash-Sutcliff efficiency
    criterion (NSE).

    Parameters
    ----------
    df_calibration_data: pandas.DataFrame
        DataFrame with all necessary data for a calibration. It contains at
        least the following columns:

        - *name* (str): the name of a catchment.
        - *sy* (float): the sediment yield (ton).
        - *area* (float): the area of the catchment (ha).
        - *ssy* (float): the specific sediment yield (ton/ha).

    df_calibration_results: pandas.DataFrame
        DataFrame with all modelled sediment yields for different combinations
        of ktc-values and different catchments. For the definition of the
        dataframe, see :func:`pywatemsedem.calibrate.merge_calibration_results`.

    Returns
    -------
    df_me: pandas.DataFrame
        DataFrame with calculated model efficiencies for all different
        combinations of ktc-values. Contains following
        columns:

        - *ktc_low* (float): ktc low value used in the model run.
        - *ktc_high* (float): ktc high value used in the model run.
        - *ME sy* (float): model efficiency computed based on sediment yield.
        - *ME ssy* (float): model efficiency computed based on specific sediment yield.

    Notes
    -----
    Model efficiencies are computed based on observed and simulated yearly totals.

    """

    denominator_sy = compute_denomitor_nash_sutcliffe(
        df_calibration_data, "sy", squared_error=True
    )
    denominator_ssy = compute_denomitor_nash_sutcliffe(
        df_calibration_data, "ssy", squared_error=True
    )

    df_me_sy = compute_nash_sutcliffe(
        df_calibration_results, denominator_sy, "sy", squared_error=True
    )
    df_me_ssy = compute_nash_sutcliffe(
        df_calibration_results, denominator_ssy, "ssy", squared_error=True
    )

    df_me = df_me_sy.merge(df_me_ssy, on=["ktc_low", "ktc_high"])

    df_me = df_me.rename(columns={"NS sy": "ME sy", "NS ssy": "ME ssy"})

    return df_me


def compute_nash_sutcliffe(
    df_calibration_results, denominator, variable, squared_error=True
):
    """Compute Nash-Sutcliffe model efficiency for calibration results of WaTEM/SEDEM for a
    variable

    Parameters
    ----------
    df_calibration_results: pandas.DataFrame
        See :func:`pywatemsedem.calibrate.calculate_model_efficiency`.
    denominator: float
        See :func:`pywatemsedem.calibrate.compute_denomitor_nash_sutcliffe`.
    variable: str
        Name of output variable 'sy' or 'ssy'.
    squared_error: bool, default True
        Make use of squared errors to compute Nash-Sutcliffe (True/False).

    Returns
    -------
    df_me: pandas.DataFrame
        DataFrame with calculated model efficiencies for all different
        combinations of ktc-values. Contains following columns:

        - *ktc_low* (float): ktc low value used in the model run.
        - *ktc_high* (float): ktc high value used in the model run.
        - *NS sy* (float): Nash-Sutcliffe model efficiency computed based on sediment
          yield.
        - *NS ssy* (float): Nash-Sutcliffe model efficiency computed based on specific
          sediment yield.
    """
    if variable not in ["sy", "ssy"]:
        msg = (
            "Only model error based on sediment yield 'sy' and specific sediment"
            " yield 'ssy' can be computed."
        )
        raise IOError(msg)

    if squared_error:
        col = f"(O_{variable}-P_{variable})²"
    else:
        col = f"|O_{variable}-P_{variable}|"
    df_me = df_calibration_results.groupby(["ktc_low", "ktc_high"]).aggregate(
        {col: np.sum}
    )
    df_me[f"NS {variable}"] = 1 - (df_me[col] / denominator)
    df_me = df_me.reset_index()
    df_me[f"NS {variable}"] = np.where(
        df_me["ktc_high"] > df_me["ktc_low"], df_me[f"NS {variable}"], np.NaN
    )

    return df_me


def compute_denomitor_nash_sutcliffe(df_calibration_data, variable, squared_error):
    """Compute the denomitor for the Nash-Sutcliffe model efficiency.

    You can make use of squared or absolute errors to compute the denominator.

    Parameters
    ----------
    df_calibration_data: pandas.DataFrame
        See :func:`pywatemsedem.calibrate.calculate_model_efficiency`.
    variable: str, default 'sy'
        Name of output variable 'sy' or 'ssy'.
    squared_error: bool
        Make use of squared errors to compute denominator (True/False).

    Returns
    -------
    denominator: float
        Denominator of the Nash-Sutcliffe criterion.
    """

    if variable not in ["sy", "ssy"]:
        msg = (
            "Only model error based on sediment yield 'sy' and specific sediment"
            " yield 'ssy' can be computed."
        )
        raise IOError(msg)

    omean = df_calibration_data[variable].mean()
    df_calibration_data[f"(O_{variable} - O_{variable}_mean)"] = (
        df_calibration_data[f"{variable}"] - omean
    )

    if squared_error:
        denominator = (
            df_calibration_data[f"(O_{variable} - O_{variable}_mean)"] ** 2
        ).sum()
    else:
        denominator = (
            np.abs(df_calibration_data[f"(O_{variable} - O_{variable}_mean)"])
        ).sum()

    return denominator


def plot_model_efficiency(
    df_me, caldata, sy=True, contours=[-0.15, 0, 0.15, 0.3, 0.45, 0.6, 0.75]
):
    """This function plots the calculated model efficiency as a function of
    ktc-low and ktc-high.

    Parameters
    ----------
    df_me: pandas.DataFrame
        Dataframe with the calculated model efficiencies for all combinations
        of ktc-values. See :func:`pywatemsedem.calibrate.calculate_modelefficiency`
        for the defintion of the dataframe.
    caldata: pywatemsedem.core.calibrate.Calibration
        See :class:`pywatemsedem.calibrate.Calibration`.
    sy: bool, default True
        Plot the sediment yield (sy=True) or the specific sediment yield (sy=False).
    contours: list, default [-0.15, 0, 0.15, 0.3, 0.45, 0.6, 0.75]
        List with values for contour lines.

    Returns
    -------
    fig:  matplotlib.pyplot.figure
    ax:  matplotlib.pyplot.axes
    """

    field = "ME sy" if sy else "ME ssy"

    arr_me = np.reshape(
        df_me[field].values, (len(caldata.arr_ktc_low), len(caldata.arr_ktc_high))
    )
    extent = (
        caldata.ktc_high_min,
        caldata.ktc_high_max,
        caldata.ktc_low_min,
        caldata.ktc_low_max,
    )

    fig, ax = plt.subplots()

    norm = colors.Normalize(vmin=-1, vmax=1)
    cax = ax.imshow(
        arr_me, origin="lower", interpolation="none", extent=extent, cmap=cm.coolwarm
    )
    cax.set_norm(norm)

    arr_x, arr_y = np.meshgrid(caldata.arr_ktc_low, caldata.arr_ktc_high)
    CS = ax.contour(arr_x, arr_y, arr_me, contours, colors="k")

    ax.clabel(CS, inline=1, fontsize=10)

    # ax.plot([0, 1, 40], [0, 0.3, 12], color='k')
    # ax.plot([0, 1, 40], [0, 0.25, 10], color='b')
    # ax.plot([0, 1, 40], [0, 0.35, 14], color='b')

    xlabels = np.arange(
        caldata.ktc_high_min,
        caldata.ktc_high_max + caldata.stepresolution_high,
        round(caldata.steps / 4),
    )
    ylabels = np.arange(
        caldata.ktc_low_min,
        caldata.ktc_low_max + caldata.stepresolution_low,
        round(caldata.steps / 4),
    )
    plt.xticks(xlabels)
    plt.yticks(ylabels)
    plt.xlabel("ktc high (1/m)")
    plt.ylabel("ktc low (1/m)")
    fig.colorbar(cax)
    return fig, ax


def calculate_regressions(df_calibration_results, calibration):
    """Compute regression for plots

    Parameters
    ----------
    df_calibration_results: pandas.DataFrame
        DataFrame with all modelled sediment yields for different combinations
        of ktc-values and different catchments. For the definition of the
        dataframe, see :func:`pywatemsedem.calibrate.merge_calibration_results`.

    calibration: pywatemsedem.core.calibrate.Calibration
        See :class:`pywatemsedem.calibrate.Calibration`.

    Returns
    -------
    df_regressions: pandas.DataFrame
        DataFrame with the regression parameters for all combinations of ktc-values.
        The DataFrame contains following columns:

        - *ktc_low* (float): ktc low value used in the model run.
        - *ktc_high* (float): ktc high value used in the model run.
        - *R2 sy* (float): see
          :func:`pywatemsedem.calibrate.linear_regression_evaluation_calibration`.
        - *R2 ssy* (float): see
          :func:`pywatemsedem.calibrate.linear_regression_evaluation_calibration`.
        - *rico_sy* (float): see
          :func:`pywatemsedem.calibrate.linear_regression_evaluation_calibration`.
        - *rico_ssy* (float): see
          :func:`pywatemsedem.calibrate.linear_regression_evaluation_calibration`.

    """

    df_regressions = calibration.df_template.copy()
    df_regressions["R2_sy"] = np.nan
    df_regressions["R2_ssy"] = np.nan
    df_regressions["rico_sy"] = np.nan
    df_regressions["rico_ssy"] = np.nan

    for ktc_low in calibration.arr_ktc_low:
        for ktc_high in calibration.arr_ktc_high:
            sel = (df_regressions["ktc_low"] == ktc_low) & (
                df_regressions["ktc_high"] == ktc_high
            )

            if ktc_high >= ktc_low:
                selection = df_calibration_results.loc[
                    (df_calibration_results["ktc_low"] == ktc_low)
                    & (df_calibration_results["ktc_high"] == ktc_high)
                ]
                p_regr_sy, r2_sy, rico_sy = linear_regression_evaluation_calibration(
                    selection["O_sy"], selection["P_sy"]
                )
                p_regr_ssy, r2_ssy, rico_ssy = linear_regression_evaluation_calibration(
                    selection["O_ssy"], selection["P_ssy"]
                )

                df_regressions.loc[sel, "R2_sy"] = r2_sy
                df_regressions.loc[sel, "R2_ssy"] = r2_ssy
                df_regressions.loc[sel, "rico_sy"] = rico_sy
                df_regressions.loc[sel, "rico_ssy"] = rico_ssy
    return df_regressions


def calculate_ratio_ktc(df_ktc):
    """Calculates the ratio between ktc low and ktc high

    Parameters
    ----------
    df_ktc: pandas.DataFrame
        DataFrame with different comibinations of ktc-values. The DataFrame
        contains at least following columns:

        - *ktc_low* (float): ktc low value used in the model run.
        - *ktc_high* (float): ktc high value used in the model run.

    Returns
    -------
    df_ktc: pandas.DataFrame
        Identical DataFrame as the input DataFrame, but with an extra column:
        ratio_ktc (float).

    """
    df_ktc["ratio_ktc"] = df_ktc["ktc_low"] / df_ktc["ktc_high"]
    return df_ktc


def plot_regression(
    df, ktc_low, ktc_high, kind="sy", label_outliers=False, labels=False
):
    """Generate regression plot for calibration

    Parameters
    ----------
    df: pandas.DataFrame
        See :func:`pywatemsedem.calibrate.calculate_model_efficiency`.
    ktc_low: float
        Low transport capacity coefficient.
    ktc_high: float
        High transport capacity coefficient.
    kind: str
        "ssy" or "sy".
    label_outliers: bool, default False
        Flag if you want to label outliers in regression plot.
    labels: bool, default False
        Flag if you want to label all datapoints in regression plot.

    Returns
    -------
    fig: matplotlib.pyplot.figure
    ax1: matplotlib.pyplot.figure
    """
    selection = df.loc[(df["ktc_low"] == ktc_low) & (df["ktc_high"] == ktc_high)]
    if kind not in ["sy", "ssy"]:
        msg = f"kind `{kind}` is not a known pywatemsedem calibration plot type."
        raise IOError(msg)
    if kind == "sy":
        observed = selection["O_sy"]
        predicted = selection["P_sy"]
        title = "observed vs. predicted sediment yield"
    elif kind == "ssy":
        observed = selection["O_ssy"]
        predicted = selection["P_ssy"]
        title = "observed vs. predicted specific sediment yield"

    p_regr, r2, rico = linear_regression_evaluation_calibration(observed, predicted)

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.set_title(f"ktc-low:{ktc_low}, ktc-high:{ktc_high}\n{title}")

    if kind == "sy":
        unit = "ton"
    elif kind == "ssy":
        unit = "ton/ha"

    ax1.set_xlabel(f"Observed ({unit})")
    ax1.set_ylabel(f"Modelled ({unit})")
    ax1.scatter(x=observed, y=predicted, marker="o", s=13)
    ax_max = np.max([np.max(observed), np.max(predicted)])
    ax1.plot(
        [0, ax_max * 1.1], [0, ax_max * 1.1], color="grey", linewidth=0.75, ls="--"
    )
    ax1.plot(observed, p_regr, color="black", linewidth=0.75, label="Regression")

    if label_outliers:
        ax1 = add_outlier_names_to_calibration_plot(selection, ax1, kind)

    if labels:
        for i, txt in enumerate(selection["name"]):
            xpos = observed.iloc[i] + ax_max / 100
            ypos = predicted.iloc[i] + ax_max / 100
            ax1.annotate(txt, (xpos, ypos))

    txt = f"y = {round(rico, 2)}\n"
    txt += f"R2 ={round(r2_score(predicted, p_regr), 2)}"
    ax1.text(
        0.98,
        0.02,
        txt,
        horizontalalignment="right",
        verticalalignment="bottom",
        transform=ax1.transAxes,
    )
    ax1.set_xlim([0, ax_max * 1.1])
    ax1.set_ylim([0, ax_max * 1.1])
    plt.show()

    return fig, ax1


def add_outlier_names_to_calibration_plot(df, ax, kind, lq=50, uq=150):
    """Add `outlier id` or `catchment name` to outliers in evaluation plots.

    Outlier names are plotted when the quotient of observed to predicted is lower or
    higher than respectively the lower or upper quotient (lq and uq). For description
    of plots see :func:`pywatemsedem.calibrate.plot_regression`.

    Parameters
    ----------
    df: pandas.DataFrame

        Results of one set of ktc values with columns:

        - *O_sy* (float): observed (specific) sediment yield (ton).
        - *P_sy* (float): predicted (specific) sediment yield (ton/ha).

    ax: matplotlib.pyplot.axis.
    kind: str
        "ssy" or "sy".
    lq: str
        Lower quotient limit.
    uq: str
        Upper quotient limit.

    Returns
    -------
    ax: matplotlib.pyplot.axis.
    """
    df = df.reset_index()

    for index in df.index:
        x = df.loc[index, f"O_{kind}"]
        y = df.loc[index, f"P_{kind}"]
        col = df.loc[index, "name"] if "name" in df.columns else index
        quotient = x / y * 100
        if (quotient > uq) or (quotient < lq):
            ax.text(x, y, col)

    return ax
