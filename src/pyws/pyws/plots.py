"""Extra functions that can be used for plotting"""

import logging
import sys

# GIS and datahandling libraries
try:
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as e:
    logging.error("not all necessary libraries are available for import!")
    logging.error(e)
    sys.exit()

logger = logging.getLogger(__name__)


def plot_cumulative_sedimentload(df, fname):
    """Make a cumulative plot of the ordered sediment load values (high to low)

    Parameters
    ----------
    df: pandas.DataFrame
        Data with cumulative sediment load
        - *value* (float): sediment load value
        - *cum_perc* (float): cumulative percentage
        - *rank* (float): rank
    percentage: int
        Percentage (%) of cumulative sediment load that is to be analysed
    fname: str or pathlib Path
        File path of output figure
    """

    fig, ax = plt.subplots(2, 1, figsize=[10, 7.5])

    x = df.loc[:, "value"]
    y = df.loc[:, "cdf"]
    ax[0].plot(
        x, y, color=[0.2] * 3, label=r"Cumulative percentage of sediment load (%)"
    )
    ax[1].plot(
        df.loc[:, "rank"],
        y,
        color=[0.2] * 3,
        label=r"Cumulative percentage of sediment load (%)",
    )
    ax[0].set_xlabel("Sediment load (-)")
    ax[0].set_ylabel("CDF (%)")
    ax[1].set_xlabel("Ranked id (-)")
    ax[1].set_ylabel("CDF (%)")
    ax[1].legend()
    plt.savefig(fname, bbox_inches="tight")
    plt.close()


def plot_time_series_for_in_river_points(
    variable, folder, resmap="", convert_output=True, output_per_segment=False
):
    """
    Plot timeseries. All timeseries are stored in the postprocesfolder as a png-file.

    Parameters
    ----------
    variable: string
        'Q': plot with discharge and rainfall vs time
        'Sedigram': plot with sediment concentration vs time
        'Sediment': plot with total sediment mass vs time
    folder: pathlib Path, optional
        path to folder where CNWS results are saved
    resmap: pathlib Path, optional
        path to folder to save pngs
    convert_output: bool, optional
        True if units in minutes
    output_per_segment: bool, optional
        True if plot has to be per segment
    """
    if variable == "Q":
        base_name = "Discharge"  # TO DO: ook neerslag!
        baseTitle = "Debiet in "
        ylable = "Debiet [m^3/s]"
    elif variable == "Sedigram":
        base_name = "Sediment concentration"
        baseTitle = "Sedigram "
        ylable = "Sediment concentratie [g/l]"
    elif variable == "Sediment":
        base_name = "Sediment"
        baseTitle = "Sediment aanvoer in "
        ylable = "Sedimentvracht [kg]"
    else:
        msg = "No valable type defined for plotting timeseries"
        logger.warning(msg)
        return

    if convert_output:
        indexcol = "Time (min)"
    else:
        indexcol = "Time (sec)"

    txt_out = folder / f"{base_name}.txt"
    if txt_out.exists():
        df_out = pd.read_csv(txt_out, sep="\t", header=1)
        df_out.index = df_out[indexcol]
        df_out = df_out.drop(indexcol, 1)
    else:
        msg = f"{base_name}.txt not found in modelresults!"
        raise logging.error(msg)

    if output_per_segment:
        txt_segm = folder / f"{base_name}_VHA.txt"
        if txt_segm.exists():
            df_segm = pd.read_csv(txt_segm, sep="\t", header=1)
            df_segm.index = df_segm[indexcol]
            df_segm = df_segm.drop(indexcol, 1)
        else:
            msg = f"{base_name}_VHA.txt not found in modelresults!"
            raise logging.error(msg)
        df = pd.concat([df_out, df_segm], axis=1, join="inner")
    else:
        df = df_out.copy()

    for col in df.columns:
        if col.startswith("Unnamed"):
            df = df.drop(col, 1)

    for i, col in enumerate(df.columns):
        plt.figure(i)
        plt.ylabel(ylable)
        if col.startswith("VHA "):
            title = baseTitle + f"segment {col[12:]}"
        else:
            title = baseTitle + f"outlet {col[7:]}"
        plt.title(title)
        df[col].plot()
        plt.savefig(resmap / title + ".png")
        plt.close(i)
