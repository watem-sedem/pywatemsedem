"""Extra functions that can be used for plotting"""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors

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
        base_title = "Debiet in "
        ylable = "Debiet [m^3/s]"
    elif variable == "Sedigram":
        base_name = "Sediment concentration"
        base_title = "Sedigram "
        ylable = "Sediment concentratie [g/l]"
    elif variable == "Sediment":
        base_name = "Sediment"
        base_title = "Sediment aanvoer in "
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
            title = base_title + f"segment {col[12:]}"
        else:
            title = base_title + f"outlet {col[7:]}"
        plt.title(title)
        df[col].plot()
        plt.savefig(resmap / title + ".png")
        plt.close(i)


def plot_landuse(arr, nodata, *args, **kwargs):
    """
    Plot landuse maps with standardized colors for the different classes

    Parameters
    ----------
    arr: numpy array
        the landuse raster
    nodata: int
        the nodata value
    """
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
    arr = arr.copy().astype(np.float32)
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
