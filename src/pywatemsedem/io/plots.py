import functools

import matplotlib.colors as mplcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from ..geo.utils import mask_array_with_val


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
    **kwargs
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
