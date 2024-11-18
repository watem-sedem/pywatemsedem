import logging
import platform
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def format_forced_routing(gdf, minmax, resolution, trajectory_routing=False):
    """Format forced routing LineString geometry in a dataframe writable to the ini-file

    Parameters
    ----------
    gdf: GeoPandas.GeoDataFrame
        Should contain geometry-proprety with LineStrings
    minmax: list
        [x_left, y_lower, x_right, y_upper]. The **first** entry is **x_left**, the
        **second** entry is **y_lower**, the **third** entry is **x_right** and the
        **fourth** entry is **y_upper**.
    resolution: int
        In m
    trajectory_routing: bool, default False
        Use routing via trajectory (True) or via jump (False)

    Returns
    -------
    df: pandas.DataFrame
        Each row is one routing element, with columns:

        - fromX (float): source X-coordinate
        - fromY (float): source Y-coordinate
        - toX (float): target X-coordinate
        - toY (float): target Y-coordinate
        - fromcol (int): source column
        - fromrow (int): source row
        - tocol (int): target column
        - torow (int): target row
    """

    lst_df = []
    for it in gdf.geometry:
        lst_df.append(
            reformat_LineString_to_source_targetf(
                it.coords, trajectory_routing=trajectory_routing
            )
        )
    df = pd.concat(lst_df, ignore_index=True)
    df["fromcol"] = (np.floor((df["fromX"] - minmax[0]) / resolution) + 1).astype(int)
    df["fromrow"] = (np.floor((minmax[3] - df["fromY"]) / resolution) + 1).astype(int)
    df["tocol"] = (np.floor((df["toX"] - minmax[0]) / resolution) + 1).astype(int)
    df["torow"] = (np.floor(minmax[3] - df["toY"]) / resolution + 1).astype(int)
    cond = (df["fromcol"] == df["tocol"]) & (df["fromrow"] == df["torow"])
    df = df.loc[~cond]
    return df


def reformat_LineString_to_source_targetf(coordinates, trajectory_routing=False):
    """Reformat single LineString-routing to source/target dataframe format

    The routing can be organised via a trajectory or a jump:

    - trajectory: the routing follows the sequential coordinates of the elements in the
      LineString.
    - jump: the routing goes from the start to the end of the LineString.

    Parameters
    ----------
    coordinates: list
        List of tuples (x,y)
    trajectory_routing: bool, default False
        Use routing via trajectory (True) or via jump (False)

    Returns
    -------
    df: pandas.DataFrame
        Each row is one routing element, with columns:

        - fromX (float): source X-coordinate
        - fromY (float): source Y-coordinate
        - toX (float): target X-coordinate
        - toY (float): target Y-coordinate
    """
    df = pd.DataFrame()
    if trajectory_routing:
        df[["fromX", "fromY"]] = [(x, y) for x, y in coordinates]
        df["toX"] = np.nan
        df["toY"] = np.nan
        df["toX"].iloc[0:-1] = df["fromX"].iloc[1:]
        df["toY"].iloc[0:-1] = df["fromY"].iloc[1:]
        df = df.iloc[:-1]
    else:
        df = pd.DataFrame(columns=["fromX", "fromY", "toX", "toY"], index=[0])
        df.loc[0, ["fromX", "fromY"]] = coordinates[0]
        df.loc[0, ["toX", "toY"]] = coordinates[-1]

    return df


def zip_folder(folder2zip, outfile=None):
    """Zip a folder

    Parameters
    ----------
    folder2zip: str
        File path of the folder to be zipped
    outfile: str
        File path and name of the output zip-file (optional). If not given the zip
        file will have the same name as the folder and it will be stored in
        the same place.
    """
    if outfile is None:
        outfile = folder2zip
    shutil.make_archive(outfile, "zip", folder2zip)


def extract_tags_from_template_file(template):
    """Extract tags (scenario, catchment, year from the WaTEM/SEDEM perceelskaart template
    file.


    Parameters
    ----------
    template: pathlib.Path or str
        File path to CN-WS perceelskaart template file.

    Returns
    -------
    catchment_name: str
        Catchment name
    scenario: str
        Scenario number (in string!)
    year: int
        Simulation year.
    valid: bool
        Tag that indicate whether template format agrees with defined template format.

    Note
    ----
    The template format should be

    """
    # take first template file and drop extension
    template_, _, _ = Path(template).name.partition(".")

    # split template name on "_"
    template_ = template_.split("_")

    # valid if template conveys with define template format
    if len(template_) != 4:
        msg = (
            f"Template {template} does not convey with defined template format "
            "`fname_%year_%catchmentname_s%scenariolabel.rst`."
        )
        logger.warning(msg)
        valid = False
    else:
        valid = True

    # get catchment name which is on the third position (index 2)
    catchment_name = template_[2]
    # get scenario number (str) from last position and drop "s"
    scenario = template_[-1].replace("s", "")
    # get year (int) from second position (index 1)
    year = int(template_[1])

    return catchment_name, scenario, year, valid


def get_df_area_unique_values_array(arr, resolution):
    """Calculate the total area for every value in an array

    The area for a value is calculated as the amount of cells with
    a certain value * cellsize * cellsize.

    Parameters
    ----------
    arr: numpy.ndarray
        Input array
    resolution: int
        The spatial resolution of the raster

    Returns
    -------
    df: pandas.DataFrame
        With two columns:

        - *values* (float): all values within the raster
        - *area* (float): the area of every value in the raster

    """
    vals, counts = np.unique(arr, return_counts=True)
    areas = np.multiply(counts, resolution**2)
    df = pd.DataFrame()
    df["values"] = vals
    df["area"] = areas
    return df


def check_cn_ws_binary(cn_ws_binary=None, fixed_name_cmd="cn_ws"):
    """
    Check if the compiled CN_WS program is known in the environment,
    or if the path reference exists

    Parameters
    ----------
    cn_ws_binary: str, default None
        File Path of compiled cn_ws Pascal code. If None, check environment.
    fixed_name_cmd: str, default 'cn_ws'
        Name of exe/program.

    Returns
    -------
    cn_ws_exe: str
        File path of compiled cn_ws Pascal code.
    """
    if cn_ws_binary is None:
        cn_ws_defined_in_path = shutil.which(fixed_name_cmd)
        if cn_ws_defined_in_path is None:
            try_location = Path.home() / "GitHub" / "cn_ws" / "cn_ws" / "cn_ws"
            if try_location.exists():
                cn_ws_binary = try_location
            else:
                msg = (
                    "CN_WSmodel exe/program not found in environment, make sure you "
                    "have defined a compiled version of cn_ws in your "
                    "environment correctly!"
                )
                raise FileNotFoundError(msg)
        else:
            cn_ws_binary = fixed_name_cmd
    else:
        if (platform.system() == "Windows") and (Path(cn_ws_binary).suffix is None):
            cn_ws_binary = cn_ws_binary + ".exe"
        if not Path(cn_ws_binary).exists():
            msg = (
                f"The custom-path defined for the CN_WSmodel exe/program "
                f"{cn_ws_binary} is incorrect, please check you refer "
                f"to a compiled CN_WSmodel."
            )
            raise FileNotFoundError(msg)

    return cn_ws_binary


def check_courant_criterium(velocity, time_step, resolution, factor=0.75):
    """Check the courant criterium, see
    https://en.wikipedia.org/wiki/Courant%E2%80%93Friedrichs%E2%80%93Lewy_condition

    Parameters
    ----------
    velocity: float
        Stream velocity (m/s)
    time_step: float
        Time step of calculations (s)
    resolution: float
        Grid resolution (m)
    factor: float
        Correction factor to avoid that CN-WS Pascal does crash if the distance water
        covers in a timestep that is equal to +-0.75 times the pixel resolution
        (temporary fix).

    Returns
    -------
    time_step_posterior: float
        Posterior time step of calculations (s)
    """
    dist_per_calc_step = velocity * time_step
    if dist_per_calc_step > factor * resolution:
        time_step_posterior = int(np.floor(factor * resolution / velocity))
        msg = (
            f"Time step of {time_step} seconds too large for a"
            f"stream velocity of {velocity} "
            f"m/s (Courant criterium) lowering to resolution divided by "
            f"the velocity ({time_step_posterior})."
        )
        logger.warning(msg)
    else:
        time_step_posterior = time_step
    return time_step_posterior
