import functools
import logging

import matplotlib.colors as mplcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..geo.utils import mask_array_with_val

logger = logging.getLogger(__name__)


def plot_continuous_raster(
    fig,
    ax,
    arr,
    bounds,
    cmap="cividis",
    norm=None,
    colorbar=True,
    ticks=None,
    *args,
    **kwargs,
):
    """
    Parameters
    ----------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis

    arr: numpy.ndarray
        Contains raster data
    bounds: list
        [left, bottom, right, upper] as obtained from RasterProperties.bounds
        (See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`)
    cmap: string or matplotlib.colors.Colormap, default = 'cividis'

    norm: matplotlib.colors.Normalize, optional
        normalisation function for colormapping
    colorbar: bool, default = True
                Choice of displaying a colorbar
    ticks: list, optional
        Supply [min, 25th percentile, 50th percentile ,75th percentile, max]
        when norm is used!

    Returns
    -------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis

    """
    im = ax.imshow(
        arr,
        cmap=cmap,
        norm=norm,
        extent=np.array(bounds)[[0, 2, 1, 3]],
        *args,
        **kwargs,
        interpolation="nearest",
    )
    if colorbar:
        fig.colorbar(im, orientation="vertical", shrink=0.5, ticks=ticks)
    else:  # allows custom colorbar
        fig = im
    return fig, ax


def plot_discrete_raster(
    fig, ax, arr, bounds, labels, cmap="cividis", norm=None, *args, **kwargs
):
    """
    Parameters
    ----------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis

    arr: numpy.ndarray
        Contains raster data
    bounds: list
        [left, bottom, right, upper] as obtained from RasterProperties.bounds
        (See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`)
    labels: list
        Supply unique string for each value
    cmap: string or matplotlib.colors.Colormap, default = 'cividis

    norm: matplotlib.colors.Normalize, optional
        normalisation function for colormapping
    Returns
    -------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis

    """
    im = ax.imshow(
        arr,
        cmap=cmap,
        norm=norm,
        extent=np.array(bounds)[[0, 2, 1, 3]],
        interpolation="nearest",
        *args,
        **kwargs,
    )
    values = np.unique(arr)
    colours = [im.cmap(im.norm(value)) for value in values]
    # create a patch (proxy artist) for every color
    patches = [
        mpatches.Patch(
            color=colours[i],
            label=labels[
                np.where(values[i] == np.arange(np.min(values), np.max(values) + 1))[0][
                    0
                ]
            ],
        )
        for i in range(len(values) - 1)
    ]
    ax.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    return fig, ax


def plot_output_raster(
    fig, ax, arr, mask, bounds, title="none", ticks=None, *args, **kwargs
):
    """Standard non-linear continuous raster plot for output raster

    Parameters
    ----------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis

    arr: numpy.ndarray
        Contains raster data
    mask: numpy.ndarray
        Contains raster data, 0 outside of domain
    bounds: list
        [left, bottom, right, upper] as obtained from RasterProperties.bounds
        (See :class:`pywatemsedem.geo.rasterproperties.RasterProperties`)
    cmap: string or matplotlib.colors.Colormap, default = 'cividis'

    ticks: list, optional
        When no list is given, 0th, 25th, 50th, 75th and 100th percentile are used

    Returns
    -------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis
    """
    fig, ax = axes_creator(fig, ax)
    arr = mask_array_with_val(arr, mask, 0)
    arr = np.ma.filled(arr, np.nan)
    if not ticks:
        ticks = np.nanpercentile(arr, [0, 25, 50, 75, 100])
    norm = normalising_function(ticks[0], ticks[1], ticks[2], ticks[3], ticks[4])
    fig, ax = plot_continuous_raster(
        fig,
        ax,
        arr=arr,
        bounds=bounds,
        norm=norm,
        ticks=ticks,
        *args,
        **kwargs,
    )
    ax.set_title(title)
    return fig, ax


def log_scale_enabler(arr, cnorm):
    """Checks if log scale is supplied.
    If minimum is lower or equal to zero,
    changes lower bound to smallest value above zero.

    Parameters
    ----------
    arr: numpy.ndarray
        rastervalues
    cnorm: str
        cnorm used for hvplot

    Returns
    -------
    lower: float
        lower value for colorscale
    """
    if cnorm == "log":
        if np.nanmin(arr) <= 0:
            lower = np.nanmin(arr[arr > 0])
        else:
            lower = np.nanmin(arr)
    else:
        lower = np.nanmin(arr)
    return lower


def axes_creator(fig, ax):
    """Creates fig and ax object if none ar given

    Parameters
    ----------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis

    Returns
    --------
    fig: matplotlib.figure.Figure

    ax: matplotlib.pyplot.axis

    """
    if not ax:
        fig, ax = plt.subplots(figsize=[10, 10])
    return fig, ax


def normalising_function(mini, Q25, Q50, Q75, maxi):
    """Custom normalisation function for maptlotlib plotting

    Parameters
    ----------
    mini
        minimum of the colorscale
    Q25
        25th percentile
    Q50
        50th percentile
    Q75
        75th percentile
    maxi
        maximum of the colorscale

    Returns
    -------
    norm: matplotlib.colors.Normalize


    """
    _forward_custom = functools.partial(
        _forward, mini=mini, Q25=Q25, Q50=Q50, Q75=Q75, maxi=maxi
    )
    _inverse_custom = functools.partial(
        _inverse, mini=mini, Q25=Q25, Q50=Q50, Q75=Q75, maxi=maxi
    )
    norm = mplcolors.FuncNorm((_forward_custom, _inverse_custom), vmin=mini, vmax=maxi)
    return norm


def _forward(x, mini, Q25, Q50, Q75, maxi):
    """Custom forward normalisation function
    performs uniform interpolation between percentiles

    Parameters
    ----------
    x: numpy.ndarray

    mini
        minimum of the colorscale
    Q25
        25th percentile
    Q50
        50th percentile
    Q75
        75th percentile
    maxi
        maximum of the colorscale

    Returns
    -------
    y: numpy.ndarray

    """
    y = x.copy()
    y = y * np.nan
    cond = (x <= Q25) * (x >= mini)
    y[cond] = 0.25 / (Q25 - mini) * (x[cond] - mini)
    cond2 = (x > Q25) * (x <= Q50)
    y[cond2] = (0.5 - 0.25) / (Q50 - Q25) * (x[cond2] - Q25) + 0.25
    cond3 = (x <= Q75) * (x > Q50)
    y[cond3] = (0.75 - 0.5) / (Q75 - Q50) * (x[cond3] - Q50) + 0.5
    cond4 = (x <= maxi) * (x > Q75)
    y[cond4] = (1 - 0.75) / (maxi - Q75) * (x[cond4] - Q75) + 0.75
    return y


def _inverse(y, mini, Q25, Q50, Q75, maxi):
    """Custom inverse normalisation function
    performs uniform interpolation between percentiles

    Parameters
    ----------
    x: numpy.ndarray

    min
        minimum of the colorscale
    Q25
        25th percentile
    Q50
        50th percentile
    Q75
        75th percentile
    max
        maximum of the colorscale

    Returns
    -------
    y: numpy.ndarray
    """

    x = y.copy()
    x = x * np.nan
    cond = (y >= 0) * (y <= 0.25)
    x[cond] = (Q25 - mini) / 0.25 * y[cond] + mini
    cond2 = (y >= 0.25) * (y <= 0.5)
    x[cond2] = (Q50 - Q25) / 0.25 * (y[cond2] - 0.25) + Q25
    cond3 = (y <= 0.75) * (y > 0.5)
    x[cond3] = (Q75 - Q50) / 0.25 * (y[cond3] - 0.5) + Q50
    cond4 = (y <= 1) * (y > 0.75)
    x[cond4] = (maxi - Q75) / 0.25 * (y[cond4] - 0.75) + Q75
    return x


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

    cmap = mplcolors.ListedColormap(
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
    norm = mplcolors.BoundaryNorm(bounds, cmap.N)
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
