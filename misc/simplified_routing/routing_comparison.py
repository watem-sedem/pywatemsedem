"""Helper functions to compare the regular and simplified routing of WaTEM/SEDEM.

Used in ``20260817_test_simplified_routing.ipynb``.
"""

import numpy as np
import pandas as pd
from IPython.display import Markdown, display

from pywatemsedem.postprocess import PostProcess

landuse_group_names = {
    -1: "river",
    -2: "infrastructure",
    -3: "forest",
    -4: "grass land",
    -5: "open water",
    -6: "grass strips",
}


def valid_raster_values(raster, nodata):
    """Return the raster values and a mask of the valid (data) pixels.

    Parameters
    ----------
    raster : object
        Raster object with an ``arr`` attribute.
    nodata : float
        Nodata value of the raster.

    Returns
    -------
    arr : numpy.ndarray
        Raster values as float64.
    valid : numpy.ndarray
        Boolean mask, ``True`` for finite pixels that are not nodata.
    """
    arr = np.asarray(raster.arr, dtype="float64")
    if pd.isna(nodata):
        valid = np.isfinite(arr)
    else:
        valid = np.isfinite(arr) & (arr != nodata)
    return arr, valid


def raster_sum(raster, nodata):
    """Sum all valid pixel values of a raster.

    Parameters
    ----------
    raster : object
        Raster object with an ``arr`` attribute.
    nodata : float
        Nodata value of the raster.

    Returns
    -------
    float
        Sum of the valid pixel values.
    """
    arr, valid = valid_raster_values(raster, nodata)
    return arr[valid].sum()


def total_sediment_summary(modeloutput):
    """Summarise the sediment balance of one model run for the whole catchment.

    ``sedi_in``, ``sedi_out`` and ``sinks`` are sums over all pixels of the
    corresponding rasters, so sediment is counted in every pixel it passes.
    ``sedi_export`` and ``sewers`` are taken from the total sediment output
    of the model.

    Parameters
    ----------
    modeloutput : pywatemsedem.io.modeloutput.Modeloutput
        Output of the model run.

    Returns
    -------
    pandas.Series
        Sediment totals (kg) indexed by ``sedi_out``, ``sedi_in``,
        ``sedi_export``, ``sewers`` and ``sinks``.
    """
    total_sediment = modeloutput.total_sediment.iloc[0]
    return pd.Series(
        {
            "sedi_out": raster_sum(modeloutput.sedi_out, modeloutput.nodata),
            "sedi_in": raster_sum(modeloutput.sedi_in, modeloutput.nodata),
            "sedi_export": total_sediment.get("river", np.nan),
            "sewers": total_sediment.get("endpoints", np.nan),
            "sinks": raster_sum(modeloutput.sinks, modeloutput.nodata),
        }
    )


def compare_scenarios(df):
    """Add the difference between the simplified and regular routing scenario.

    Parameters
    ----------
    df : pandas.DataFrame
        Table with (at least) the columns ``regular`` and ``simplified``.

    Returns
    -------
    pandas.DataFrame
        Copy of `df` with the extra columns ``absolute_difference``
        (simplified - regular) and ``relative_difference_pct`` (difference in
        % of regular; NaN where regular is 0).
    """
    comparison = df.copy()
    comparison["absolute_difference"] = comparison["simplified"] - comparison["regular"]
    comparison["relative_difference_pct"] = (
        100
        * comparison["absolute_difference"]
        / comparison["regular"].replace(0, np.nan)
    )
    comparison.columns.name = None
    return comparison


def landuse_group(value):
    """Translate a composite land-use value to a land-use group name.

    Parameters
    ----------
    value : int or float
        Composite land-use value. Positive values are parcel ids, negative
        values are land-use classes (see ``landuse_group_names``).

    Returns
    -------
    str
        ``"parcel"`` for positive values, the name in ``landuse_group_names``
        for known negative values, or ``"unknown (<value>)"`` otherwise.
    """
    if value > 0:
        return "parcel"
    return landuse_group_names.get(int(value), f"unknown ({int(value)})")


def sediment_by_landuse(modelinput, modeloutput):
    """Sum the incoming and outgoing sediment per land-use group.

    Only pixels that are valid in both the composite land-use raster and the
    sediment raster are taken into account.

    Parameters
    ----------
    modelinput : pywatemsedem.io.modelinput.Modelinput
        Input of the model run (composite land-use raster).
    modeloutput : pywatemsedem.io.modeloutput.Modeloutput
        Output of the model run (``sedi_in`` and ``sedi_out`` rasters).

    Returns
    -------
    pandas.DataFrame
        Long table with the columns ``landuse_group``, ``sediment_kg`` and
        ``sediment_variable`` (``"sedi_in"`` or ``"sedi_out"``).
    """
    compositelanduse = modelinput.compositelanduse
    landuse, landuse_valid = valid_raster_values(
        compositelanduse, compositelanduse.rp.nodata
    )

    rows = []
    for sediment_name in ["sedi_in", "sedi_out"]:
        sediment = getattr(modeloutput, sediment_name)
        sediment_arr, sediment_valid = valid_raster_values(sediment, modeloutput.nodata)
        valid = landuse_valid & sediment_valid
        df = pd.DataFrame(
            {
                "landuse": landuse[valid].astype("int64"),
                "sediment_kg": sediment_arr[valid],
            }
        )
        df["landuse_group"] = df["landuse"].map(landuse_group)
        grouped = df.groupby("landuse_group", as_index=False)["sediment_kg"].sum()
        grouped["sediment_variable"] = sediment_name
        rows.append(grouped)

    return pd.concat(rows, ignore_index=True)


def postprocess_grass_strips(scenario, modeloutput):
    """Compute the sediment balance per grass strip with PostProcess.

    Parameters
    ----------
    scenario : pywatemsedem.scenario.Scenario
        Scenario that was run, used for the ini file, postprocessing folder
        and grass strips vector.
    modeloutput : pywatemsedem.io.modeloutput.Modeloutput
        Output of the model run, used for the EPSG code.

    Returns
    -------
    pandas.DataFrame
        Attribute table of the postprocessed grass strips (without geometry),
        a.o. with ``sedi_in`` and ``sedi_out`` per grass strip.
    """
    postprocess = PostProcess(
        scenario.ini,
        scenario.sfolder.postprocessing_folder,
        modeloutput.epsg,
    )
    postprocess.vct_grass_strips = scenario.vct_grass_strips.file_path
    postprocess.process_grass_strips()
    return postprocess.vct_grass_strips.geodata.drop(columns="geometry")


def routing_arrows(modelinput, modeloutput):
    """Return one row per routing arrow with land use and sediment of source and target.

    Each pixel in the routing table can route to two targets. Every target
    with a positive part and a valid column becomes one arrow. The sediment
    carried by an arrow is the ``sedi_out`` of the source pixel multiplied by
    the part of that target.

    Parameters
    ----------
    modelinput : pywatemsedem.io.modelinput.Modelinput
        Input of the model run (composite land-use and DTM raster).
    modeloutput : pywatemsedem.io.modeloutput.Modeloutput
        Output of the model run (routing table and ``sedi_out`` raster).

    Returns
    -------
    pandas.DataFrame
        Table with the columns ``row``, ``col``, ``target_row``,
        ``target_col`` (1-based, as in the routing table), ``part``,
        ``landuse_source``, ``landuse_target``, ``sediment_kg``,
        ``elevation_drop`` (m, source - target), ``group_source`` and
        ``group_target``.
    """
    landuse = np.asarray(modelinput.compositelanduse.arr)
    dtm = np.asarray(modelinput.dtm.arr, dtype="float64")
    sedi_out, sedi_out_valid = valid_raster_values(
        modeloutput.sedi_out, modeloutput.nodata
    )
    sedi_out = np.where(sedi_out_valid, sedi_out, 0.0)
    routing = modeloutput.routing

    arrows = []
    for target in [1, 2]:
        df = routing.loc[
            (routing[f"part{target}"] > 0) & (routing[f"target{target}col"] > 0)
        ]
        src = (df["row"].values - 1, df["col"].values - 1)
        tgt = (df[f"target{target}row"].values - 1, df[f"target{target}col"].values - 1)
        arrows.append(
            pd.DataFrame(
                {
                    "row": df["row"].values,
                    "col": df["col"].values,
                    "target_row": df[f"target{target}row"].values,
                    "target_col": df[f"target{target}col"].values,
                    "part": df[f"part{target}"].values,
                    "landuse_source": landuse[src],
                    "landuse_target": landuse[tgt],
                    "sediment_kg": sedi_out[src] * df[f"part{target}"].values,
                    "elevation_drop": dtm[src] - dtm[tgt],
                }
            )
        )
    arrows = pd.concat(arrows, ignore_index=True)
    arrows["group_source"] = arrows["landuse_source"].map(landuse_group)
    arrows["group_target"] = arrows["landuse_target"].map(landuse_group)
    return arrows


def infrastructure_path_length(arrows, infrastructure=-2):
    """Number of infrastructure pixels passed before sediment leaves the infrastructure.

    The path is followed along the main target (largest part) of every pixel.
    The path stops when the target is not infrastructure, has no outgoing
    arrow, or was already visited (loop).

    Parameters
    ----------
    arrows : pandas.DataFrame
        Routing arrows, see :func:`routing_arrows`.
    infrastructure : int, default -2
        Composite land-use value of infrastructure.

    Returns
    -------
    numpy.ndarray
        Path length (number of pixels) for every infrastructure pixel with an
        outgoing arrow.
    """
    main = arrows.sort_values("part", ascending=False).drop_duplicates(["row", "col"])
    target = {
        (r, c): (tr, tc)
        for r, c, tr, tc in main[["row", "col", "target_row", "target_col"]].itertuples(
            index=False
        )
    }
    landuse = dict(zip(zip(main["row"], main["col"]), main["landuse_source"]))
    infra_pixels = [
        pixel for pixel, value in landuse.items() if value == infrastructure
    ]

    lengths = []
    for pixel in infra_pixels:
        n, visited = 0, set()
        while (
            pixel in target
            and landuse.get(pixel) == infrastructure
            and pixel not in visited
        ):
            visited.add(pixel)
            pixel = target[pixel]
            n += 1
        lengths.append(n)
    return np.array(lengths)


def pct_background(value, clim=10):
    """Return a CSS background colour for a percentage value.

    Negative values are coloured red, positive values green. The opacity
    scales linearly with the absolute value up to `clim`.

    Parameters
    ----------
    value : float
        Percentage value.
    clim : float, default 10
        Absolute value (%) at which the maximum opacity is reached.

    Returns
    -------
    str
        CSS style string, or an empty string for NaN or 0.
    """
    if pd.isna(value) or value == 0:
        return ""
    alpha = min(abs(value), clim) / clim * 0.75
    if value < 0:
        return f"background-color: rgba(176, 0, 32, {alpha:.3f})"
    return f"background-color: rgba(0, 132, 61, {alpha:.3f})"


def display_table(title, df):
    """Display a table with a title in the notebook.

    Numbers are shown with two decimals and percentage columns (ending on
    ``_pct``) are coloured with :func:`pct_background`.

    Parameters
    ----------
    title : str
        Title, shown as markdown header above the table.
    df : pandas.DataFrame
        Table to display.
    """
    display(Markdown(f"### {title}"))
    pct_columns = [
        column
        for column in df.columns
        if str(column).endswith("_pct") or str(column) == "relative_difference_pct"
    ]
    styler = df.style.format(precision=2, na_rep="")
    if pct_columns:
        if hasattr(styler, "map"):
            styler = styler.map(pct_background, subset=pct_columns)
        else:
            styler = styler.applymap(pct_background, subset=pct_columns)
    display(styler)
