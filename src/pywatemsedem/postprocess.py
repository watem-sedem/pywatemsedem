import logging
import os
import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pkg_resources
import shapely

from pywatemsedem.defaults import SAGA_FLAGS
from pywatemsedem.geo.factory import Factory
from pywatemsedem.geo.utils import (
    clean_up_tempfiles,
    compute_statistics_rasters_per_polygon_vector,
    create_spatial_index,
    execute_saga,
    get_mask_template,
    get_rstparams,
    load_raster,
    raster_array_to_pandas_dataframe,
    raster_dataframe_to_arr,
    rasterprofile_to_rstparams,
    set_no_data_rst,
    write_arr_as_rst,
)
from pywatemsedem.grasstrips import estimate_ste
from pywatemsedem.io.folders import CatchmentFolder, ScenarioFolders
from pywatemsedem.io.modeloutput import (
    compute_efficiency_buffers,
    create_deposition_raster,
    create_erosion_raster,
    define_subcatchments_saga,
    identify_individual_priority_catchments,
    load_total_sediment_file,
    make_routing_vct_saga,
    open_txt_routing_file,
)

from .plots import plot_cumulative_sedimentload
from .scenario import CNWSException
from .tools import zip_folder

logger = logging.getLogger(__name__)


def valid_ditches_sewers(
    func,
):
    """Decorator to check if DTM raster is defined."""

    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.files["rst_ditches_in"] is None:
            self.write_sedimentload_sewers_and_ditches()
        return func(self, *args, **kwargs)

    return wrapper


def valid_erosion_deposition(func):
    """Decorator to check if DTM raster is defined."""

    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.files["rst_erosion"] is None:
            self.files["rst_erosion"] = create_erosion_raster(
                self.files["rst_watereros"]
            )
            self.files["rst_deposition"] = create_deposition_raster(
                self.files["rst_watereros"]
            )
        func(self, *args, **kwargs)

    return wrapper


def valid_routing_vector(self):
    """Check if routing vector is defined"""
    if self.vct_routing is None:
        msg = "No routing vector created, please first run 'make_routing_vct'."
        raise IOError(msg)


def valid_routing_sediout_vector(self):
    """Check if routing vector is defined"""
    if self.vct_routing is None:
        msg = (
            "No routing vector (with sediout) created, please rirst run "
            "'couple_sediout_routing."
        )
        raise IOError(msg)


def valid_endpoints(self):
    """Check if endpoints are in available"""
    if self.files["rst_endpoints"] is None:
        msg = "No endpoints in catchments."
        raise IOError(msg)


def valid_rivers(self):
    """Check if rivers are available"""
    if self.files["rst_riverrouting"] is None:
        msg = "No rivers in catchments."
        raise IOError(msg)


def valid_sinks(self):
    """Check if any sinks present in catchment"""
    if (self.files["rst_endpoints"] is None) and (
        self.files["rst_riverrouting"] is None
    ):
        msg = "No sinks (rivers and endpoints) in catchments."
        raise IOError(msg)


class PostProcess(Factory):
    """Initialisation of the postprocess class.

    This class is used to process output data layers of data processing
    pywatemsedem.

    Parameters
    ----------
    name: str
        Name of catchment to which results of scenario run are written too
    scenario_nr: int
        scenario number
    year: int
        simulation year
    resolution: int
        model resolution
    epsg: int, default 31370
        epsg-code


    Examples
    --------
    >>> from pywatemsedem.postprocess import PostProcess()
    >>> pp = PostProcess(r"molenbeek", 1, 2019, 20, 31370) # note that the folder
    >>> #modelbeek/scenario_1 and molenbeek/scenario_1/2019 must exist
    >>> pp.make_routing_vct() #make a vector file of the text routig file.

    """

    def __init__(self, name, resolution, scenario_label, year, epsg):

        # general
        self.epsg = epsg
        self.catchment_name = Path(name).stem
        self.subcatchments_name = None
        self.scenario = f"scenario_{scenario_label}"
        self.scenario_label = scenario_label
        self.year = year

        # test if fmap_results is found
        self.cfolder = CatchmentFolder(name, resolution)
        self.sfolder = ScenarioFolders(self.cfolder, scenario_label, year)
        self.cfolder.check_home_folder()
        self.cfolder.check_catchment_folder()
        self.sfolder.check_scenario()
        self.sfolder.check_years()
        self.sfolder.check_cnwsinput()
        self.sfolder.check_cnwsoutput(error_if_empty=True)
        self.sfolder.check_postprocessing(create=True)

        # get raster properties based on DTM .tif file in Data_Bekken
        self.rstparams, self.rasterprop = get_rstparams(
            self.sfolder.cnwsinput_folder,
            catchmentname=self.catchment_name,
            epsg=self.epsg,
        )
        # intialize functionalities factory
        super().__init__(
            resolution, self.epsg, -9999, name, bounds=self.rasterprop["minmax"]
        )

        self.mask = self.sfolder.cnwsinput_folder / "mask.rst"

        self.resolution = resolution
        self.arr_bindomain = get_mask_template(
            self.sfolder.cnwsinput_folder, self.catchment_name
        )

        # regenerate user choices based on generated files
        self.dict_ecm_options = {}
        self.dict_model_options = {}
        self.dict_output_options = {}

        # automatically assign
        self.assign_filenames(self.sfolder.scenario_folder)

        # initialize path postprocessing files
        self.vct_routing = None
        self._routing = pd.read_csv(self.files["txt_routing"], sep="\t")
        self.vct_routing_missing = None
        self.txt_routing_nonriver = None
        self.vct_sediexport = None
        self.vct_sewerin = None
        self.rst_endpoints_sewer = None
        self.rst_endpoints_ditch = None
        self.rst_sinks = None
        self.vct_routing_sediout = None
        self.rst_subcatchment_sinks = None
        self.vct_subcatchment_sinks = None
        self.vct_subcatchment_priority = None
        self.vct_subcatchment_priority = None

    @property
    def sinks(self):
        """Getter Sinks attribute."""
        return self._sinks

    @sinks.setter
    def sinks(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sinks = self.raster_factory(raster, flag_mask=True)

    def assign_filenames(self, fmap_results):
        """Use filestructure defined in the package to appoint names of files

        Parameters
        ----------
        fmap_results: str or pathlib.Path
            Folder path (scenario_XX)
        """
        files = {}

        df_datastructure_files = read_filestructure()

        for index in df_datastructure_files.index:
            f = get_tuple_datastructure(df_datastructure_files, index)
            argument_inputs = {
                "year": self.year,
                "catchment_name": self.catchment_name,
                "scenario": self.scenario_label,
            }
            filename = self.process_and_check_filename(
                fmap_results, *f, argument_inputs
            )
            tag_variable = df_datastructure_files.loc[index, "tag_variable"]
            prefix_variable = df_datastructure_files.loc[index, "prefix_variable"]
            files[prefix_variable + "_" + tag_variable] = filename

        self.files = files

    def process_and_check_filename(
        self,
        fmap_results,
        subfolder,
        filename,
        extension,
        arguments,
        mandatory,
        condition,
        arguments_input,
    ):
        """
        Build full filename and set conditions coupled to the presence of a
        file

        Parameters
        ----------
        fmap_results: str or pathlib.Path
            Folder path (scenario_XX)
        subfolder: str or pathlib.Path
            Folder path in which a specific file 'filename' resides
        filename: str
            File path (without full path, without extension, with string
            formatting %)
        extension: str
            Extension of the file (e.g. .tif, .shp, ..)
        arguments:
            Argument for the string formatting
        mandatory: int
            Indicate whether file is a mandatory file (0/1)
        condition
            Condition coupled when file is present (e.g. `Include buffers`,
            `Include sewers`, ..)

        Returns
        -------
        full_filename: pathlib.Path
            File path
        """
        full_filename = process_filename(
            fmap_results, subfolder, filename, extension, arguments, arguments_input
        )
        exists = check_if_file_exists(full_filename, mandatory)
        self.check_condition_files(condition, exists)

        if int(mandatory) == 1:
            try:
                open(full_filename)
            except IOError:
                msg = f"Mandatory file '{filename}' not found"
                logging.error(msg)
        else:
            try:
                open(full_filename)
            except IOError:
                msg = f"Optional file '{filename}' not found, ignoring"
                logging.warning(msg)

        return full_filename

    def check_condition_files(self, condition, exists):
        """Set conditions coupled to the presence of a file

        Parameters
        ----------
        condition: str
            Specific condition coupled to the presence of a file
        exists: bool
            File exist (True/False)

        Notes
        -----
        The condition defines which pywatemsedem option
        (see :func:pywatemsedem.CNWS.UserChoices) should be considered as
        True/False given that a file (exists) is present in the pywatemsedem
        filesystem. For example: the presence of the buffers.rst raster in the
        modeloutput indicates that the Include buffers option was set to True in
        the pywatemsedem data processing.

        """
        lst_output_options = [
            "Write aspect",
            "Write LS factor",
            "Write slope",
            "Write upstream area",
            "Write routing table",
            "Write RUSLE",
            "Write sediment export",
            "Write water erosion",
            "Output per river segment",
        ]

        lst_ecm_options = ["Include buffers", "UseGras"]

        if condition != "":
            if condition == "Include sewers":
                if exists:
                    self.dict_model_options["Include sewers"] = True
                else:
                    self.dict_model_options["Include sewers"] = False

            elif condition in lst_ecm_options:
                if exists:
                    self.dict_ecm_options[condition] = True
                else:
                    self.dict_ecm_options[condition] = False

            elif condition in lst_output_options:
                if exists:
                    self.dict_output_options[condition] = True
                else:
                    self.dict_output_options[condition] = False

            else:
                msg = (
                    f"Condition '{condition}' not know, check implementation in "
                    f"datamodel'"
                )
                logger.info(msg)
                raise IOError(msg)

    def zip_folder(self):
        """Zip output folder of scenario_x"""
        zip_folder(self.sfolder.scenario_folder)

    def compute_statistics_rasters_per_polygon_vector(self, vct):
        """Compute statistics for raster for an input polygon vector



        Parameters
        ----------
        vct: pathlib.Path
            Polygon vector file

        Returns
        -------
        geopandas.GeoDataFrame
            Geopandas dataframe of vct with statistics per polygon.
        """
        dict_operators = {"SUM": True}
        vct_out = self.sfolder.postprocess_folder / Path(f"{vct.stem}_statistics.shp")
        self.files["rst_erosion"] = create_erosion_raster(self.files["rst_watereros"])
        self.files["rst_deposition"] = create_deposition_raster(
            self.files["rst_watereros"]
        )
        lst_rasters = [
            self.files["rst_erosion"].absolute(),
            self.files["rst_deposition"].absolute(),
            self.files["rst_sediexport"].absolute(),
            self.files["rst_sewers_in"].absolute(),
            self.files["rst_ditches_in"].absolute(),
        ]
        lst_names = [
            "Erosion (kg)",
            "Deposition (kg)",
            "River (kg)",
            "Sewers (kg)",
            "Ditches (kg)",
        ]

        compute_statistics_rasters_per_polygon_vector(
            lst_rasters,
            Path(vct).absolute(),
            vct_out.absolute(),
            lst_names,
            dict_operators,
            normalize=True,
            ton=False,
        )

    def identify_subcatchments_to_buffers(self):
        """Define the seperate subcatchments to the buffer outlets

        See :func:`pywatemsedem.postprocess.identify_subcatchments_to_buffers`
        """
        logger.info("Defining catchments to buffers...")
        if self.dict_ecm_options["Include buffers"] == 1:
            if self.txt_routing_nonriver is None:
                self.remove_river_routing()
            elif not Path(self.txt_routing_nonriver).exists():
                self.remove_river_routing()
            self.txt_routing_nonriver
            identify_subcatchments_to_buffers(
                self.files["rst_buffers"],
                self.files["vct_buffers"],
                self.txt_routing_nonriver,
                self.sfolder.postprocess_folder,
                self.rasterprop,
                self.catchment_name,
                self.scenario_label,
            )
        else:
            msg = (
                "No buffers simulated in model. Can not identify "
                "subcatchments to buffer."
            )
            logger.warning(msg)

    def identify_priority_areas(self, nmax=10, flag_merge=True):
        """Identify priority areas

        Parameters
        ----------
        nmax: str
            Maximum number of priority areas.
        flag_merge: bool
            Merge the separate priority areas to one shapefile.

        Note
        ----
        Algorithm to identify priority areas:

        1. Load sediout raster as an array
        2. Identify pixel with highest sediout value i.
        3. Identify subcatchment j coupled to this highest sediout value i.
        4. Set all sediment values within subcathcment j to no_value.
        5. Repeat 2 until 4, for a number of iterations (nmax).
        """
        # Generate temporary folder to write maps
        tempfolder = self.sfolder.postprocess_folder / "priority_areas"
        if not tempfolder.exists():
            os.makedirs(tempfolder)

        # load SediOut_kg file
        arr_sediout, profile = load_raster(self.files["rst_sediout"])

        # delineate individual catchments based on highest values in sediout
        gdf_subcatchmpriority = self.identify_individual_priority_catchments(
            arr_sediout, profile, self.vct_routing, nmax
        )
        # merge overlapping catchments into joint catchments
        self.merge_overlapping_catchments(gdf_subcatchmpriority, merge=flag_merge)

    @property
    def routing(self):
        """Set modeloutput routing

        Parameters
        ----------
        routing_file: pathlib.Path
            See :ref:`here <watemsedem:routingtxt>`

        Returns
        -------
        pandas.DataFrame:
            with columns:

            - *row* (float)
            - *col* (float)
            - *targetcol1* (float): target 1 col
            - *targetrow1* (float): target 1 row
            - *targetcol2* (float): target 2 col
            - *targetrow2* (float): target 2 row
            - *part1*: share (in [0,1])
            - *part2*: share (in [0,1])
        """
        return self._routing

    @property
    def routing_non_river(self):
        """Getter routing (no river routing) long format

        River routing is removed from the routing table

        Returns
        -------
        pandas.DataFrame:
            with columns:

            - *row* (float)
            - *col* (float)
            - *targetcol* (float): target col
            - *targetrow* (float): target row
            - *part*: share (in [0,1])
        """
        valid_routing_vector(self)
        df = gpd.read_file(
            self.vct_routing, include_fields=["col", "row", "lnduSource"]
        )
        df = df.loc[(df["lnduSource"] != -1), ["col", "row"]]
        cond = (df["col"].astype(str) + "-" + df["row"].astype(str)).tolist()
        return self.routing[
            (
                self.routing["col"].astype(str) + "-" + self.routing["row"].astype(str)
            ).isin(cond)
        ]

    def identify_priority_catchments_based_on_highest_loads(self, nmax=10):
        """Identify the priority catchments.

        Identify the pixels with the highest loads in the sediout raster,
        sort them from high too low, and delineate the subcatchment for these
        pixels up until nmax catchments. See
        :func:`pywatemsedem.postprocess.identify_individual_priority_catchments`.

        Parameters
        ----------
        nmax: int
            Maximum number of catchment to identify
        """
        arr_sediout, profile = load_raster(self.files["rst_sediout"])
        temp_routing_wide = tempfile.NamedTemporaryFile(suffix=".txt").name
        self.routing_non_river_wide.to_csv(temp_routing_wide, sep="\t", index=False)
        identify_individual_priority_catchments(
            arr_sediout,
            profile,
            temp_routing_wide,
            nmax,
            resmap=self.sfolder.postprocess_folder,
            epsg=self.epsg,
        )
        clean_up_tempfiles(Path(temp_routing_wide), "txt")

    def merge_overlapping_catchments(self, gdf_subcatchmpriority, merge=True):
        """Merge overlapping catchments and reassign priorities for
        overlapping catchments.

        Parameters
        ----------
        gdf_subcatchmpriority: geopandas.GeoDataFrame
            Catchment shapes with number of catchment.
        merge: bool, default True
            Merge the separate priority areas to one shapefile.

        """
        if merge:

            # fix formatting
            gdf_subcatchmpriority["VALUE"] = gdf_subcatchmpriority["VALUE"].astype(int)
            gdf_subcatchmpriority = gdf_subcatchmpriority.sort_values(
                "VALUE", ascending=True
            )

            # Merge overlapping shapes together and assign how many times it
            # was identified
            gdf_subcatchmpriority["cond"] = False

            # make a new dataframe with overlapping shapes together
            l_priorities = []
            l_polygons = []
            l_sediout_low = []
            l_sediout_high = []

            ind = 1
            cond = True

            while cond:

                # identify intersects
                gdf_subcatchmpriority["cond"] = [
                    gdf_subcatchmpriority["geometry"]
                    .iloc[0]
                    .intersects(gdf_subcatchmpriority["geometry"].iloc[j])
                    for j in range(len(gdf_subcatchmpriority))
                ]

                # get union of these intersecting polygons and their
                # priority id
                gdf_polygons = gdf_subcatchmpriority.loc[
                    gdf_subcatchmpriority["cond"], "geometry"
                ].tolist()
                gdf_sediout_intersect = gdf_subcatchmpriority.loc[
                    gdf_subcatchmpriority["cond"], "sediout"
                ].tolist()

                l_polygons.append(shapely.ops.cascaded_union(gdf_polygons))
                l_sediout_low.append(np.min(gdf_sediout_intersect))
                l_sediout_high.append(np.max(gdf_sediout_intersect))
                l_priorities.append(ind)
                ind += 1

                # remove records from dataframe so no duplicates are analyzed
                gdf_subcatchmpriority = gdf_subcatchmpriority.loc[
                    not gdf_subcatchmpriority["cond"]
                ]

                if len(gdf_subcatchmpriority) == 0:
                    break

            # generate new dataframe with
            gpd_priorities = gpd.GeoDataFrame(
                np.transpose(np.array([l_priorities, l_sediout_low, l_sediout_high])),
                geometry=l_polygons,
                columns=["priority", "sediout_min", "sediout_max"],
                index=range(len(l_priorities)),
            )

            gpd_priorities = gpd_priorities.to_crs(
                self.rasterprop["epsg"], allow_override=True
            )
            vct_out = self.sfolder.postprocess_folder / "priority_catchments_merged.shp"
            gpd_priorities.to_file(vct_out)

    def convert_rst_sediexport_to_vct(self):
        """Convert the sediexport raster to a vector file."""
        vct_out = self.files["rst_sediexport"].stem + ".shp"
        vct_out = self.sfolder.postprocess_folder / vct_out
        self.vct_sediexport = convert_rst_sinks_to_vct(
            self.files["rst_sediexport"], vct_out, "river", self.rasterprop["epsg"]
        )

    def convert_rst_sewerin_to_vct(self):
        """Convert the sewerin raster to a vector file."""
        vct_out = self.files["rst_sewerin"].stem + ".shp"
        vct_out = self.sfolder.postprocess_folder / vct_out
        self.vct_sewerin = convert_rst_sinks_to_vct(
            self.files["rst_sewerin"], vct_out, "sewer", self.rasterprop["epsg"]
        )

    def merge_vct_sinks(self):
        """Merge vct_sewerin and vct_sediexport to one sinks shapefile."""
        if self.vct_sewerin is not None and self.vct_sediexport is not None:
            gdf_sewerin = gpd.read_file(self.vct_sewerin)
            gdf_sewerin = gdf_sewerin.append(
                gpd.read_file(self.files["vct_sediexport"]), ignore_index=True
            )
            gdf_sewerin = gdf_sewerin.sort_values("sediment", ascending=False)
            gdf_sewerin["cumsum"] = gdf_sewerin["sediment"].cumsum()
            gdf_sewerin["cumperc"] = (
                gdf_sewerin["cumsum"] / (gdf_sewerin["sediment"].sum())
            ) * 100
            gdf_sewerin = gdf_sewerin.reset_index()
            vct_out = (
                f"sewer_and_riversinks_{self.catchment_name}_s{self.scenario_label}.shp"
            )
            vct_out = self.sfolder.postprocess_folder / vct_out
            gdf_sewerin.to_file(vct_out)

    def compute_source_sinks(self, percentage=50):
        """Source-sink algorithm to identify sources of erosion
        (parcels or subcatchments) that lead to sediment sinks in the river
        (or sewer).

        Parameters
        ----------
        percentage: int
            X % highest load that the user wants to analyse
        """
        valid_sinks(self)
        df_sediexport, percentage = self.identify_sinks(percentage)
        dict_rst_subcatchmsinks = {}
        dict_vct_subcatchmsinks = {}
        temp = tempfile.NamedTemporaryFile(suffix=".txt").name
        self.routing_non_river.to_csv(temp, sep="\t", index=False)
        (
            dict_rst_subcatchmsinks[percentage],
            dict_vct_subcatchmsinks[percentage],
        ) = define_subcatchments_saga(
            self.rst_sinks,
            temp,
            self.sfolder.postprocess_folder,
            self.rasterprop,
            f"sourcesink_perc_{percentage}",
        )
        # assign cumulative percentage, percentage and class
        df_subcatchments = gpd.read_file(dict_vct_subcatchmsinks[percentage])
        df_subcatchments = df_subcatchments.merge(
            df_sediexport, left_on="VALUE", right_on="id", how="left"
        )
        df_subcatchments.drop(columns=["id"], inplace=True)
        df_subcatchments = df_subcatchments.set_crs(
            self.rasterprop["epsg"], allow_override=True
        )
        # check lijn hieronder
        df_subcatchments.to_file(dict_vct_subcatchmsinks[percentage])
        clean_up_tempfiles(Path(temp), "txt")

    def identify_sinks(self, percentage):
        """Identify X % highest sinks of sediment.

        Analyse cumulative sediment load by sorting SediExport
        from high to low, and identify sediment sinks.

        Parameters
        ----------
        percentage: int
            x percentage highest load that the user wants to analyse
        rst_sinks: str
            filename of raster that contains sink point (values in raster
            should be between 0 and 100 %)

        Returns
        -------
        df_sediexport: pandas.DataFrame
            Data Frame format of SediExport raster (format: see
            :func:`pywatemsedem.utils.raster_array_to_pandas_dataframe`)
        percentage: int
            Updated x percentage highest load that the user want to analyse
        """
        arr_sediexport, profile = load_raster(self.files["rst_sediexport"])
        arr_sediexport = np.where(
            arr_sediexport == profile["nodata"], 0, arr_sediexport
        )

        # if self.dict_model_options["Include sewers"]:
        #    arr_endpoints, _ = load_raster(self.files["rst_endpoints"])
        #    arr_endpoints = np.where(arr_endpoints == -9999, 0, arr_endpoints)
        #    arr_sediexport += arr_endpoints

        df_sediexport = raster_array_to_pandas_dataframe(
            arr_sediexport, self.rp.rasterio_profile
        )
        profile["driver"] = "GTiff"

        # sort and select points
        df_sediexport, percentage = self.analyse_cumulative_sediexport(
            df_sediexport, profile, percentage, plot=False
        )
        arr_sediexport = raster_dataframe_to_arr(
            df_sediexport, self.rp.rasterio_profile, "id", np.float32
        )
        self.rst_sinks = self.sfolder.postprocess_folder / "sinks.tif"
        self.sinks = arr_sediexport
        self.sinks.write(self.rst_sinks, "tiff", nodata=-9999)

        return df_sediexport, percentage

    def analyse_cumulative_sediexport(
        self, df_sediexport, profile, percentage, delta_perc=10, plot=False
    ):
        """Analyse cumulative sediment load by sorting SediExport values
        from high to low

        Parameters
        ----------
        df_sediexport: pandas.DataFrame
            Data Frame format of SediExport raster (format: see
            :func:`pywatemsedem.utils.raster_array_to_pandas_dataframe`)
        profile: rasterio.profiles
            see :func:`rasterio.open`
        percentage: int
            x percentage highest load that the user wants to analyse
        delta_perc: int
            delta used to iterate percentage
        plot: bool, default False
            True if you want a cumulative SediExport plot

        Returns
        -------
        df_sediexport: pandas.DataFrame
            Data Frame format of SediExport raster (format: see
            :func:`pywatemsedem.utils.raster_array_to_pandas_dataframe`) added
            with:

            - *cum_perc* (float): cumulative highest load
            - *perc* (float): percentage highest load
            - *class* (int): class as defined by `delta_perc`

        percentage: str
            updated percentage
        """

        # sort according to values of sediment load into river
        df_sediexport["sediexport"] = df_sediexport["val"]
        df_sediexport = df_sediexport.sort_values("sediexport", ascending=False)

        # calculate cumulative sum, in percentage
        cond = (df_sediexport["sediexport"] != profile["nodata"]) & (
            df_sediexport["val"] != 0.0
        )
        df_sediexport.loc[cond, "cum_sum"] = df_sediexport.loc[
            cond, "sediexport"
        ].cumsum()
        df_sediexport.loc[cond, "cum_perc"] = (
            100
            * df_sediexport.loc[cond, "cum_sum"]
            / df_sediexport.loc[cond, "sediexport"].sum()
        )

        if plot:
            plot_cumulative_sedimentload(
                df_sediexport.loc[cond],
                percentage,
                self.sfolder.postprocess_folder / "cumulative_sediexport.png",
            )

        # hotfix on percentage: if the first percentage is higher than the
        # user-predefined percentage, adjust it (small catchments)!
        cum_sum_sinks0 = df_sediexport["cum_perc"].iloc[0]
        if cum_sum_sinks0 > percentage:
            msg = (
                f"Sinks receiving most sediment has a cumulative relative "
                f"sediment load higher than {percentage}%, "
            )
            msg += (
                f"changing percentage {percentage}% " f"to {np.ceil(cum_sum_sinks0)}%"
            )

            logger.warning(msg)
            percentage = np.ceil(cum_sum_sinks0)

        # prepare ids for subcatchment delineation
        df_sediexport["id"] = profile["nodata"]
        df_sediexport["class"] = profile["nodata"]

        # assign unique id's - in order of importance - to records
        cond = (df_sediexport["cum_perc"] <= percentage) & (
            ~df_sediexport["cum_perc"].isnull()
        )
        df_sediexport.loc[cond, "id"] = np.arange(np.sum(cond)) + 1

        # calculate percentage
        df_sediexport["perc"] = [
            df_sediexport["cum_perc"].iloc[i] - df_sediexport["cum_perc"].iloc[i - 1]
            if i != 0
            else df_sediexport["cum_perc"].iloc[i]
            for i in range(0, len(df_sediexport))
        ]

        # chekc if begin percentage is below delta_perc
        bperc = delta_perc
        eperc = int(percentage + 1)
        if df_sediexport["cum_perc"].iloc[0] > bperc:
            bperc = int(np.ceil(df_sediexport["cum_perc"].iloc[0] / 10) * 10)

        for i in range(bperc, eperc, delta_perc):
            cond = (
                (df_sediexport["cum_perc"] > i - delta_perc)
                & (df_sediexport["cum_perc"] <= i)
                & (~df_sediexport["cum_perc"].isnull())
            )
            df_sediexport.loc[cond, "class"] = i

        return (
            df_sediexport[
                ["col", "row", "id", "perc", "cum_perc", "class", "sediexport"]
            ],
            int(percentage),
        )

    def identify_export_parcel(self):
        """Identify total sediment leaving a parcel.

        Returns
        -------
        df_prckrt: geopandas.GeoDataFrame
            See
            :func:`pywatemsedem.postprocess.PostProcess.aggregate_sedout_parcel`

        """
        # couple sediment out to routing file
        valid_routing_sediout_vector(self)
        gdf_routing_sediout = gpd.read_file(self.vct_routing_sediout)
        gdf_routing_out_of_parcel = select_routing_out_of_parcel(gdf_routing_sediout)
        out_shp = self.sfolder.postprocess_folder / "routing_out_of_parcel.shp"
        gdf_routing_out_of_parcel.to_file(out_shp)
        create_spatial_index(out_shp)
        df_prckrt = self.aggregate_sedout_parcel(gdf_routing_out_of_parcel)

        return df_prckrt

    def aggregate_sedout_parcel(self, gdf_routing):
        """Aggregate sediment leaving on the scale of single parcels.

        Parameters
        ----------
        gdf_routing: pandas.DataFrame
            dataframe format of routing file, indicating which target cells
            flor in which source cells.

        Returns
        -------
        df_prckrt: pandas.DataFrame
            prckrt added with sediout for every pixel defined per parcel
        """

        # load perceelskaart in dataframe format
        arr_prckrt, profile = load_raster(self.files["rst_prckrt"])
        df_prckrt = raster_array_to_pandas_dataframe(arr_prckrt, profile)

        for i in ["col", "row"]:
            df_prckrt[i] = df_prckrt[i].astype(np.float64)

        # aggregate sediout of routing to parcel scale
        gdf_routing = (
            gdf_routing.groupby(["lnduSource"])
            .aggregate({"sediout": np.sum})
            .reset_index()
        )
        # merge routing to 'perceelskaart'
        gdf_routing["lnduSource"] = gdf_routing["lnduSource"].astype(np.float64)
        df_prckrt = df_prckrt.merge(
            gdf_routing[["sediout", "lnduSource"]],
            left_on="val",
            right_on="lnduSource",
            how="left",
        )
        df_prckrt.loc[df_prckrt["sediout"].isnull(), "sediout"] = profile["nodata"]
        df_prckrt = df_prckrt.drop(["val"], axis=1)

        return df_prckrt

    def couple_sediout_routing(self, cols_out=None):
        """Couple sediout of raster map values to routing file.

        See :func:`pywatemsedem.postprocess.couple_sediout_routing`

        Returns
        -------
        gdf_routing_sediout: geopandas.GeoDataFrame
            See :func:`pywatemsedem.postprocess.couple_sediout_routing`
        """
        logger.info("Coupling amount of sediment to routing vectors...")
        valid_routing_vector(self)
        gdf_routing_sediout = couple_sediout_routing(
            self.vct_routing, self.files["rst_sediout"], self.epsg, cols_out
        )
        self.vct_routing_sediout = self.vct_routing.parent / Path(
            self.vct_routing.stem + "_sediout.shp"
        )
        gdf_routing_sediout.to_file(self.vct_routing_sediout)
        create_spatial_index(self.vct_routing_sediout)

        return gdf_routing_sediout

    def intersect_sedioutparcels_with_subcatchments(
        self, rst_subcatchment_sinks, df_sediout_parcel
    ):
        """Find the intersection between the subcatchments of the sinks and the
        parcels that lie within these subcatchments.

        The sediout_parcel map is used to identify the sediment exported out
        of a parcel.

        Parameters
        ----------
        rst_subcatchment_sinks: str or pathlib.Path
            File path of the subcatcmsinks raster
        df_sediout_parcel: pandas.DataFrame
            DataFrame of the sediout parcel map. This map holds
            for every pixel the total amount of sediment
            that is transported outside the parcel in which the parcel lies.
        """
        arr_subcatchments, profile = load_raster(rst_subcatchment_sinks)
        df_subcatchments = raster_array_to_pandas_dataframe(arr_subcatchments, profile)

        # remove pixels with value nodata and zero
        cond = (df_subcatchments["val"] != profile["nodata"]) & (
            df_subcatchments["val"] != 0
        )
        df_subcatchments = df_subcatchments[cond]
        # merge with sediout defined per parcel
        df_subcatchments = df_subcatchments.merge(
            df_sediout_parcel[["col", "row", "lnduSource"]],
            on=["col", "row"],
            how="left",
        )
        # get ids of parcels (lndSource, not equal to none, np.nan)
        cond = ~df_subcatchments["lnduSource"].isnull()
        unique_ids = df_subcatchments.loc[cond, "lnduSource"].unique()

        #  set pixels that have no parcel_id (lnduSource) wihtin the
        #  unique_ids list to nodata
        cond = df_sediout_parcel["lnduSource"].isin(unique_ids)
        df_sediout_parcel.loc[~cond, "SediOut"] = profile["nodata"]

        # write to disk
        self.sfolder.postprocess_folder / "SedoutSinks.tif"
        profile["driver"] = "GTiff"

        arr_sediout = raster_dataframe_to_arr(
            df_sediout_parcel, profile, "SediOut", np.float32
        )

        write_arr_as_rst(
            arr_sediout,
            self.rst_sinks,
            "float32",
            profile,
        )

    def select_routing_to_outsidecatchment(self):
        """Exports all routing vectors to the outside of the catchment"""
        valid_routing_sediout_vector(self)

        logger.info("Determining routing out of the catchment...")

        vct_out = (
            self.sfolder.postprocess_folder
            / f"routing_to_outside_{self.catchment_name}.shp"
        )
        if not vct_out.exists():
            gdf_routingsediout = gpd.read_file(self.vct_routingsediout)
            gdf_routingsediout = gdf_routingsediout[gdf_routingsediout["lnduTarg"] == 0]
            gdf_routingsediout.to_file(vct_out)
            create_spatial_index(vct_out)

    def get_total_sediment(self):
        """Make nice output table

        Returns
        -------
        pandas.DataFrame
            Sum statistic (columns `value`) for variables (indices).
        """
        out = self.read_total_sediment()
        df = pd.DataFrame.from_dict(out, orient="index", columns=["value (kg)"])
        return df

    def read_total_sediment(self):
        """Load the total sediment file

        See :func:`pywatemsedem.utils.load_total_sediment_file`

        Returns
        -------
        dict_total_sediment: dict
            See :func:`pywatemsedem.utils.load_total_sediment_file`
        """
        dict_total_sediment = load_total_sediment_file(self.files["txt_total_sediment"])
        return dict_total_sediment

    def assign_values_df_summary(
        self, df_summary, index, bekken, bekken_id, summary_values, unit="ton"
    ):
        """Assign values of summary to the summary dataframe

        Parameters
        ----------
        df_summary: pandas.DataFrame
            Dataframe holding all summary values
        index: int
            Row index to write summary values to
        bekken: str
            Name of the (sub)catchemnt
        bekken_id: int
            Id of the bekken
        summary_values: dict

            - *erosion* (float): amount of netto erosion (watererosion < 0)
            - *deposition* (float): amount of netto deposition (watererosion >
              0)
            - *river* (float): amount of sediment load to river.
            - *outside_domain* (float): amount of sediment routed out of
              boundaries catchment
            - *buffers* (float): amount of sediment trapped in buffers.
            - *endpoints* (float): amount of sediment load to endpoints.

        unit: str, optional
            'ton' or 'kg'

        Returns
        -------
        df_summary: pandas.DataFrame
            updated dataframe holding all summary values
        """
        if unit == "kg":
            unit = 1
        if unit == "ton":
            unit = 1000

        df_summary.loc[index, "erosie"] = -summary_values["erosion"] / unit
        df_summary.loc[index, "sedimentatie"] = summary_values["deposition"] / unit
        df_summary.loc[index, "rivier"] = summary_values["river"] / unit
        df_summary.loc[index, "waterloop"] = summary_values["river"] / unit
        df_summary.loc[index, "doorvoerratio"] = (
            -summary_values["river"] / summary_values["erosion"]
        )
        df_summary.loc[index, "buiten_domein"] = summary_values["outside_domain"] / unit
        df_summary.loc[index, "buffers"] = summary_values["buffers"] / unit
        df_summary.loc[index, "bekken"] = bekken
        df_summary.loc[index, "bekken_id"] = bekken_id

        return df_summary

    def process_buffers(self, **kwargs):
        """Overwrite function"""
        self._process_buffers(**kwargs)

    def _process_buffers(self, compute_priority=True, cols=None, vct_out=None):
        """Compute the ingoing, outgoing and depositing sediment in buffers.

        This function computes the efficiency (deposition = ingoing -
        outgoing) sediment per buffer. In addition, this result is
        mapped to a shape file. See
        :func:`pywatemsedem.postprocess.compute_efficiency_buffers` for an
        explanation of the algorithm.

        Parameters
        ----------
        compute_priority: bool, optional
            Compute priorities for buffers based on deposition
        cols: list
            List of geopandas.GeoDataFrame output columns.
        vct_out: str or pathlib.Path, default None
            File path to export. If none, exported to standard name
        """
        logger.info("Calculating how much sediment is trapped in each buffer...")
        if self.dict_ecm_options["Include buffers"] == 1:

            df_out = compute_efficiency_buffers(
                self.files["rst_buffers"],
                self.files["rst_sediin"],
                self.files["rst_sediout"],
            )

            gdf_buffer = gpd.read_file(self.files["vct_buffers"])
            gdf_buffer = gdf_buffer.merge(
                df_out, left_on="id", right_on="NR", how="left"
            )
            gdf_buffer["area"] = gdf_buffer.area
            if compute_priority:
                gdf_buffer = compute_cdf_sediment_load(
                    gdf_buffer,
                    "buff_sed",
                    self.sfolder.postprocess_folder,
                    tag="buffers",
                    plot=True,
                )
            if vct_out is None:
                vct_out = (
                    self.sfolder.postprocess_folder / self.files["vct_buffers"].name
                )

            if cols:
                gdf_buffer = gdf_buffer[cols]
            gdf_buffer.to_file(vct_out)

            return gdf_buffer

    def compute_netto_erosion_parcels(self, join=True):
        """Compute the netto erosion per parcel.

        For an explanation of the definition of netto erosion,
        see :func:`pywatemsedem.postprocess.compute_netto_erosion_parcels`

        Parameters
        ----------
        join: bool, optional
            Join the results of the netto erosion raster calculations to the
            parcel shape file.
        """
        logger.info("Calculating netto erosion for every parcel...")
        compute_netto_erosion_parcels(
            self.files["rst_prckrt"],
            self.files["rst_watereros"],
            self.files["rst_percelen_prcid"],
            resolution=self.resolution,
            fmap=self.sfolder.postprocess_folder,
            flag_write=True,
            flag_join_vct_parcels=join,
        )

    def _process_grass_strips(self, compute_priority=True):
        """Compute graass strips efficiency and compute priority

        Parameters
        ----------
        compute_priority: bool, optional
            Compute priorities for grass strips based on deposition in grass strip.

        Returns
        -------
        gdf_grass_strips: geopandas.GeoDataFrame
            See :func:`pywatemsedem.postprocess.compute_efficiency_grass_strips` added
            with columns (if compute_priority=True)
                - *gras_id_target* (float): grass_id
                - *gras_id_source* (float): grass_id
                - *npixels_t* (float: number of pixels of target grass strip
                - *sediin* (float): total incoming sediment in grass strip (kg)
                - *sediout* (float): total outgoing sediment out of grass strip (kg)
                - *eSTE* (float): estimated sediment trapping efficiency, see
                  :func:`pywatemsedem.grasstrips.estimate_ste` (%)
                - sed (float): amount of sedimentation (kg)
                - *column_value* (float): deposition in grass strip.
                - *cum_sum* (float): cumulative sum of deposition in grass strips
                - *cdf* (float): cumulative distribution estimate.
        """
        logger.info("Calculating in- and output of sediment for every grass strip...")
        if self.dict_ecm_options["UseGras"] == 1:

            _, _, df_grass_strips_eff = compute_efficiency_grass_strips(
                self.files["txt_routing"],
                self.files["rst_grass_strips_id"],
                self.files["rst_prckrt"],
                self.files["rst_sediout"],
            )

            gdf_grass_strips = gpd.read_file(self.files["vct_grass_strips"])
            gdf_grass_strips = gdf_grass_strips.merge(
                df_grass_strips_eff, left_on="NR", right_on="gras_id_target", how="left"
            )
            if compute_priority:
                gdf_grass_strips = compute_cdf_sediment_load(
                    gdf_grass_strips,
                    "sed",
                    self.sfolder.postprocess_folder,
                    ignore_negative_values=True,
                    tag="grass_strips",
                    plot=True,
                )

        else:
            msg = "Can not process grass strips, 'UseGras'-option is set off."
            logger.warning(msg)
            gdf_grass_strips = gpd.GeoDataFrame()
        return gdf_grass_strips

    def merge_sediout_and_cumulative(self, segments_to_retain=None):
        """Merge SediOut.rst (sediment output on every land pixel) and
        Cumulative.rst (sediment output in every
        river pixel).

        It is possible to retain only certain river segments
        in the merged raster. Therefore a list with
        all segmentnumbers must be given to the parameter
        segements_to_retain. The segements not retained will get value
        0 in the resulting raster.

        Parameters
        ----------
        segments_to_retain: list
            list of ids of segments one wishes to retain in analysis
        """
        arr_sediout_nonriver, profile = load_raster(self.files["rst_sediout"])
        arr_sediout_nonriver = np.where(
            arr_sediout_nonriver != profile["nodata"], arr_sediout_nonriver, 0
        )

        arr_sediout_river, profile = load_raster(self.files["rst_cumulative"])
        if segments_to_retain is None:
            # take all river segments, i.e. everything not nodata
            arr_sediout_river = np.where(
                arr_sediout_river != profile["nodata"], arr_sediout_river, 0
            )
        else:
            # take only river segments in list
            arr_riversegm, _ = load_raster(self.files["rst_riviersegm"])
            mask = np.in1d(arr_riversegm, segments_to_retain).reshape(
                arr_riversegm.shape
            )
            arr_sediout_river = np.where(mask, arr_sediout_river, 0)
        arr_sediout_total = np.where(
            self.arr_bindomain == 1,
            arr_sediout_river + arr_sediout_nonriver,
            profile["nodata"],
        )
        rst_out = (
            self.sfolder.postprocess_folder
            / f"SediOut_merged_{self.catchment_name}.tif"
        )
        write_arr_as_rst(arr_sediout_total, rst_out, "float32", self.rstparams)

    def convert_output_rsts_to_ton(self):
        """Convert the units for rasters sediout, sediin, sediexport and
        watereros from kg to ton.
        """
        rsts = [
            self.files["rst_sediout"],
            self.files["rst_sediin"],
            self.files["rst_watereros"],
            self.files["rst_sediexport"],
        ]
        new_rsts = [Path(str(x).replace("_kg", "_ton")) for x in rsts]

        for i in range(0, len(rsts)):
            if rsts[i].exists():
                convert_arr_from_kg_to_ton(rsts[i], new_rsts[i])

    def add_sediment_to_subcatchments(self, vct_subcatchments):
        """Adds the sediment input of every river segment to the corresponding
        subcatchment.

        For every subcatchment the attribute sedar is calculated. Sedar is
        calculated as sedimentinput/area subcatchment

        Parameters
        ----------
        vct_subcatchments: str or pathlib.Path
            File path of vectorfile which holds the subcatchments subject to
            inspection.

        """
        logger.info("Coupling results to subcatchments...")
        vct_subcatchments = Path(vct_subcatchments)

        df_segments = pd.read_csv(
            self.files["txt_total_sediment_segments"],
            sep="\t",
            skiprows=2,
            names=["NR", "sediment"],
        )
        df_segments["sediment"] = np.round(
            df_segments["sediment"] / 1000, 3
        )  # kg to tonnes

        try:
            gdf_subcatchments = gpd.read_file(vct_subcatchments)
        except Exception:
            msg = f"could not open {vct_subcatchments}"
            logger.error(msg)
        else:
            gdf_subcatchments["NR"] = gdf_subcatchments["VALUE"]
            gdf_subcatchments = gdf_subcatchments.merge(
                df_segments, on="NR", how="left"
            )
            gdf_subcatchments["area"] = gdf_subcatchments.area
            gdf_subcatchments["sedar"] = (
                gdf_subcatchments["sediment"] / gdf_subcatchments["area"]
            )
            gdf_subcatchments["sedar_ha"] = gdf_subcatchments["sedar"] * 10000.0
            gdf_subcatchments.drop(columns=["VALUE"], inplace=True)
            gdf_subcatchments.to_file(vct_subcatchments)

    def add_segment_results_to_vct(self):
        """Adds the sedimentinput to every riversegment and calculates the
        sedlen-argument.

        Sedlen is calculated as sedimentinput/length river segment.

        The resulting shapefile is stored in self.segmShp.
        """
        logger.info("Coupling results to segments...")

        if (
            self.files["txt_total_sediment_segments"] is not None
            and self.files["vct_waterline"] is not None
        ):
            df_total_sediment_segments = pd.read_csv(
                self.files["txt_total_sediment_segments"],
                sep="\t",
                skiprows=2,
                names=["NR", "Sediment"],
            )
            df_total_sediment_segments["Sediment"] = np.round(
                df_total_sediment_segments.Sediment / 1000, 3
            )  # kg to tonnes
            df_waterline = gpd.read_file(self.files["vct_waterline"])
            df_waterline = df_waterline.merge(
                df_total_sediment_segments, on="NR", how="left"
            )
            df_waterline["sedlen"] = df_waterline["Sediment"] / df_waterline.length

            self.vct_riversegment = (
                self.sfolder.postprocess_folder
                / f"Sedimentexport2Segments_{self.catchment_name}_"
                f"s{self.scenario_label}.shp"
            )

            df_waterline.to_file(self.vct_riversegment)
            create_spatial_index(self.vct_riversegment)
        else:
            msg = (
                f"{self.files['txt_total_sediment_segments']} or "
                f"{self.files['vct_waterline']} does not exist!"
            )
            raise IOError(msg)

    def compute_sewer_in_per_catchment(self, vct_subcatchments):
        """Compute sewer in per subcatchment

        Parameters
        ----------
        vct_subcatchments: str or pathlib.Path
            File path of vectorfile which holds the subcatchments subject to
            inspection

        """
        vct_subcatchments = Path(vct_subcatchments)
        rst_subcatchment = vct_subcatchments.parent / Path(
            vct_subcatchments.stem + ".sdat"
        )
        arr_sewerin, _ = load_raster(self.files["rst_sewerin"])
        arr_subcatchment, _ = load_raster(rst_subcatchment)
        sewer_in = []
        catchids = np.unique(arr_subcatchment)
        for catchid in catchids:
            sewerinsum = np.where(arr_subcatchment == catchid, arr_sewerin, 0).sum()
            sewer_in.append(sewerinsum)
        data = {"ids": catchids, "sewer_in": sewer_in}
        df_sewerin = pd.DataFrame.from_dict(data)
        df_sewerin["sewer_in"] = np.round(
            df_sewerin["sewer_in"] / 1000, 3
        )  # kg to tonnes
        gdf_subcatchments = gpd.read_file(vct_subcatchments)
        gdf_subcatchments = gdf_subcatchments.merge(
            df_sewerin, left_on="NR", right_on="ids", how="left"
        )
        gdf_subcatchments.drop(columns=["ids"], inplace=True)
        gdf_subcatchments.to_file(vct_subcatchments)

    def make_routing_vct(self, extent=None, tile_number=None, tag=""):
        """Make a routing vector file based on routingfile

        Parameters
        ----------
        extent: list
            list holding value of extent to consider, xmin,ymin,xmax,ymax
        tilenumber: int
            id of tile
        tag: str
            tag to add to filename
        """
        txt_routing = self.files["txt_routing"]
        self.vct_routing = self.sfolder.postprocess_folder / (
            self.files["txt_routing"].stem + tag + ".shp"
        )
        make_routing_vct_saga(
            txt_routing,
            self.files["rst_prckrt"],
            self.vct_routing,
            self.rstparams,
            extent=extent,
            tile_number=tile_number,
        )

    def make_missing_routing_vct_saga(self):
        """Make a routing vector file based on routingfile with missing"""
        txt = self.txt_routing_missing
        if txt.exists():
            self.vct_routing_missing = make_routing_vct_saga(txt, "missing_routing")

    def identify_sinks_in_routing(self):
        """Identify sinks based on whether more than one routing vector goes to
        a pixel.
        """

        logger.info("Looking for sinks in routing...")
        txt = self.files["txt_routing"]
        if txt.exists():
            # check if file is tab seperated
            with open(txt) as f:
                first_line = f.readline()
            if "\t" not in first_line:
                df_routing = pd.read_csv(
                    txt, sep=";"
                )  # old model runs used ; as seperator in routing file
            else:
                df_routing = pd.read_csv(txt, sep="\t")

            Cnst = self.rasterprop
            # df_route = df_route.loc[(df_route.target1row != -99) & (
            # df_route.target2row != -99)].copy()
            # punten -99 zijn buiten modeldomein

            arr_pfactor, profile = load_raster(self.files["rst_pkaart"])
            df_pkaart = raster_array_to_pandas_dataframe(arr_pfactor, profile)
            df_pkaart = df_pkaart[(df_pkaart["val"] == 1)]
            df_routing = df_routing[["col", "row"]].copy()
            df_routing.drop_duplicates(inplace=True)
            df_routing["source"] = 1
            df_pkaart = df_pkaart.merge(df_routing, on=["col", "row"], how="outer")
            df_pkaart = df_pkaart.loc[df_pkaart["source"] != 1]

            if not df_pkaart.empty:
                df_pkaart["sourceX"] = (Cnst["minmax"][0] + (Cnst["res"] / 2)) + Cnst[
                    "res"
                ] * (df_pkaart["col"] - 1)
                df_pkaart["sourceY"] = (Cnst["minmax"][1] + (Cnst["res"] / 2)) + Cnst[
                    "res"
                ] * (Cnst["nrows"] - df_pkaart["row"])
                df_pkaart["geometry"] = df_pkaart.apply(
                    lambda x: shapely.geometry.Point(
                        float(x.sourceX), float(x.sourceY)
                    ),
                    axis=1,
                )
                CRS = {"init": Cnst["epsg"]}
                gpd_bindomain = gpd.GeoDataFrame(
                    df_pkaart, geometry="geometry", crs=CRS
                )
                vct_out = (
                    f"sinks_in_routing_{self.catchment_name}_s{self.scenario_label}.shp"
                )

                vct_out = self.sfolder.postprocess_folder / vct_out
                gpd_bindomain.to_file(vct_out)
                msg = f"{gpd_bindomain.shape[0]} sinks in routing!"
                logger.info(msg)

                """
                cmd_args = ['saga_cmd', 'shapes_grid', '0', '-SHAPES',
                str(outshp)]
                cmd_args += ['-GRIDS', str(self.perceelRST[
                self.scenario.years[0]])]
                cmd_args += ['-RESULT', str(outshp)]
                cmd_args += ['-RESAMPLING', '0']
                print(cmd_args)
                execute_subprocess(cmd_args)
                """

            else:
                logger.info("No sinks in routing")
        else:
            msg = "routing.txt does not exist!"
            logger.error(msg)

    def set_prckrt_nodata(self):
        """Set nodata to 'WaTEM/SEDEM perceelskaart'"""
        try:
            rst_prckrt_nodata = self.files["rst_prckrt"].stem + "_nodata.tif"
            set_no_data_rst(self.files["rst_prckrt"], rst_prckrt_nodata)
        except KeyError:
            msg = "'set_no_data_rst' failed for WaTEM/SEDEM perceelskaart."
            logger.error(msg)
            raise CNWSException(msg)
        except TypeError:
            msg = "check if scenario is defined correctly"
            logger.warning(msg)
            raise CNWSException(msg)

    def calculate_areas_prckrt(self):
        """Calculates the areas and relative areas of all landuse classes in
        the parcelmap
        """

        if self.files["rst_prckrt"] is None:
            self.set_prckrt_nodata()

        arr_prckrt, _ = load_raster(self.files["rst_prckrt"])

        res = self.rasterprop["res"]
        arr_prckrt = np.where(arr_prckrt >= 1, 1, arr_prckrt)
        vals, counts = np.unique(arr_prckrt, return_counts=True)
        areas = np.multiply(counts, res**2)
        mask = np.where(vals == 0, True, False)
        vals = np.ma.array(vals, mask=mask)
        areas = np.ma.array(areas, mask=mask)
        total_area = np.sum(areas)
        rel_areas = areas / total_area

        df = pd.DataFrame()
        df["lnduse_class"] = vals
        df["area"] = areas
        df["rel_area"] = rel_areas * 100
        f = self.sfolder.postprocess_folder / (
            f"opp_perceelskaart_{self.year}_{self.catchment_name}_"
            f"s{self.scenario_label}.csv"
        )
        df.to_csv(f, sep=";")

    def make_facts(self):
        """Make a textfile with a number of stats about the simulation"""
        factsfile = self.sfolder.postprocess_folder / (
            f"facts_{self.catchment_name}_s{self.scenario_label}.csv"
        )
        with open(factsfile, "w") as f:
            f.write(f";{self.catchment_name}\n")

            opp_catch = np.sum(
                self.arr_bindomain[self.arr_bindomain != self.rstparams["nodata"]]
            ) * (self.rasterprop["res"] ** 2)
            opp_catch_ha = opp_catch / 10000.0

            f.write(f"Oppervlakte bekken (ha);{opp_catch_ha}\n")

            df_parcel = gpd.read_file(self.files["vct_percelen"])
            n_parcels = df_parcel.shape[0]
            f.write(f"Aantal landbouwpercelen {self.year};{n_parcels}\n")
            df_parcel["opp"] = df_parcel.area
            opp_parcels = df_parcel.opp.sum()
            opp_parcels_ha = opp_parcels / 10000.0
            f.write(f"Oppervlakte landbouwpercelen (ha) {self.year};{opp_parcels_ha}\n")
            # (SG/DR) share of agricultural parcels
            aandeel_landbouw = (opp_parcels_ha / opp_catch_ha) * 100
            f.write(
                f"relatieve opp landbouwpercelen (%) {self.year};{aandeel_landbouw}\n"
            )

            if "Lndgbrk" in df_parcel.columns:
                n_nt_kerend = df_parcel[df_parcel.ntkerend == 1].shape[0]
                f.write(
                    f"Aantal nt-kerend bewerkte percelen {self.year};{n_nt_kerend}\n"
                )
            df_grass = gpd.read_file(self.files["vct_grass_strips"])
            n_grass = df_grass.shape[0]
            f.write(f"Aantal grasstroken {self.year};{n_grass}\n")

    def split_sewerin(self):
        """Split the sewerin raster with the sewer_id raster.

        See :func:`pywatemsedem.postprocess.split_endpoints_in_raster`
        """

        rst_sewers = (
            Path(self.sfolder.postprocess_folder)
            / f"endpoints_in_sewers_s{self.scenario_label}.rst"
        )
        rst_ditches = (
            Path(self.sfolder.postprocess_folder)
            / f"endpoints_in_ditches_s{self.scenario_label}.rst"
        )

        split_endpoints_in_raster(
            self.files["rst_endpoints_id"],
            self.files["rst_endpoints"],
            rst_sewers,
            rst_ditches,
        )
        return rst_sewers, rst_ditches

    def write_erosion_deposition_raster(self):
        """Write erosion and deposition ratser based on watereros"""
        self.files["rst_erosion"] = create_erosion_raster(self.files["rst_watereros"])
        self.files["rst_deposition"] = create_deposition_raster(
            self.files["rst_watereros"]
        )


def check_if_file_exists(full_filename, mandatory):
    """
    Check if the specified file exist on disk

    Parameters
    ----------
    full_filename: str or pathlib.Path
        File path of the to check file
    mandatory: bool
        Indicate whether the file is mandatory or not

    Returns
    -------
    bool
        File exists (True/False)
    """
    try:
        f = open(full_filename)
        f.close()
        return True
    except IOError:
        if mandatory == 1:
            msg = f"Mandatory file '{full_filename}' does not exist"
            raise IOError(msg)

        else:
            return False


def split_endpoints_in_raster(
    rst_endpoints_id, rst_endpoints_in, rst_id1, rst_id2, ton=False
):
    """Split the endpoints raster (sewer_in WaTEM/SEDEM definition) file for each
    endpoints id present in the endpoints_id raster.

    The endpoints are split according to 1: the sewers and 2: the ditches.

    Parameters
    ----------
    rst_endpoints_id: str or pathlib.Path
        File path of sewer_id raster. This raster holds the values 1 and 2
    rst_endpoints_in: str or pathlib.Path
        File path of sewer_in raster. This raster holds the sediment transport values
        for every pixel defined with a 1 or 2.
    rst_id1: str of pathlib.Path
        File path of output raster with id equal to one.
    rst_id2: str of pathlib.Path
        File path of output raster with id equal to two.
    ton: bool, default False
        Convert to ton (True)

    Returns
    -------
    sum_id1: float
        Total sediment load in id1
    sum_id2: float
        Total sediment load in id2

    Note
    ----
    Note that sewers in WaTEM/SEDEM are endpoints in pywatemsedem, such to make a distinction
    between sewers and ditches in pywatemsedem.
    """

    # load sewer id's and sewer in (kg per pixel)
    arr_sewer_id, profile = load_raster(rst_endpoints_id)
    arr_sewer_in, _ = load_raster(rst_endpoints_in)

    # sewers
    arr = np.where(arr_sewer_id == 1, arr_sewer_in, float(profile["nodata"])).astype(
        np.float32
    )
    if ton:
        arr[arr != profile["nodata"]] = arr[arr != profile["nodata"]] / 1000
    write_arr_as_rst(arr, rst_id1, "float32", profile)
    sum_id1 = np.sum(arr[arr != profile["nodata"]])

    # ditches
    arr = np.where(arr_sewer_id == 2, arr_sewer_in, float(profile["nodata"])).astype(
        np.float32
    )
    if ton:
        arr[arr != profile["nodata"]] = arr[arr != profile["nodata"]] / 1000
    write_arr_as_rst(arr, rst_id2, "float32", profile)
    sum_id2 = np.sum(arr[arr != profile["nodata"]])

    return sum_id1, sum_id2


def compute_efficiency_grass_strips(
    txt_routing, rst_grass_strips, rst_prckrt, rst_sediout
):
    """Compute statistics for grass strips:

    1. Compute the individual sediment input and output per routing element
    2. Compute the incoming and outgoing sediment per gras_id
    3. Compute the total incoming and outgoing sediment aggregated over all
       grass strips

    Parameters
    ----------
    txt_routing: str or pathlib.Path
        File path of the WaTEM/SEDEM routing table
    rst_grass_strips: str or ppathlib.Path
        raster grass strips with id's filename
    rst_prckrt: str or pathlib.Path
        raster CNWS perceelskaart
    rst_sediout: str or pathlib.Path
        File path WaTEM/SEDEM output raster 'SediOut_kg.rst'

    Returns
    -------
    sediment_load_grass_strips_in: float
        Total sediment load streaming into all gras strips (kg)
    sediment_load_grass_strips_out: float
        Total sediment load streaming out of all gras strips (kg)
    df_efficiency: pandas.DataFrame

        Sediment load flowing in and flowing out grass strip with the columns:

        - *gras_id_target* (float): grass_id
        - *gras_id_source* (float): grass_id
        - *npixels_t* (float: number of pixels of target grass strip
        - *sediin* (float): total incoming sediment in grass strip (kg)
        - *sediout* (float): total outgoing sediment out of grass strip (kg)
        - *eSTE* (float): estimated sediment trapping efficiency, see
          :func:`pywatemsedem.grasstrips.estimate_ste` (%)
        - sed (float): amount of sedimentation (kg)

    Note
    ----
    *gras_id_target* and *gras_id_source* are equal and refers to the gras_id.
    """
    # load files
    arr_prckrt, profile = load_raster(rst_prckrt)
    df_prckrt = raster_array_to_pandas_dataframe(arr_prckrt, profile)
    arr_grass_strips_id, profile = load_raster(rst_grass_strips)
    df_grass_strips = raster_array_to_pandas_dataframe(arr_grass_strips_id, profile)

    arr_sediout, profile_sediout = load_raster(rst_sediout)
    df_sediout = raster_array_to_pandas_dataframe(arr_sediout, profile_sediout)
    df_routing = open_txt_routing_file(txt_routing)

    # filter grass strips that are actually modelled as grass strips in
    # pywatemsedem
    df_grass_strips = filter_grass_strips_with_prckrt(
        df_grass_strips, df_prckrt, profile
    )
    df_grass_strips["val"] = df_grass_strips["val"].astype(np.float64)

    # merge grass strips with sediout raster
    df_routing_grasid = merge_grass_strip_id_and_sediout_to_routing(
        df_grass_strips, df_sediout, df_routing
    )

    # format df_routing_grass to a list format
    df_routing_grass_T = reformat_routing_grass(df_routing_grasid)

    # aggregate per grass strip
    df_efficiency = aggregate_sediin_and_sediout_grass_strips(df_routing_grass_T)

    # compute counts
    arr_id, arr_npixels_t = np.unique(arr_grass_strips_id, return_counts=True)
    df_counts = pd.DataFrame()
    df_counts["gras_id_target"] = arr_id
    df_counts["npixels_t"] = arr_npixels_t
    df_efficiency = df_efficiency.merge(df_counts)
    sediment_load_grass_strips_in = np.sum(df_efficiency["sediin"])
    sediment_load_grass_strips_out = np.sum(df_efficiency["sediout"])

    return sediment_load_grass_strips_in, sediment_load_grass_strips_out, df_efficiency


def aggregate_sediin_and_sediout_grass_strips(df_routing_grass):
    """
    Compute the load in and out of a grass strips, so efficiencies can be
    computed.

    Parameters
    ----------
    df_routing_grass: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`:

        - *targetrow* (float): target row of pixel
        - *targetcol* (float) target column of pixel
        - *sediin* (float): incoming sediment pixel
        - *sediout* (float): outgoing sediment pixel
        - *gras_id_source* (float): grass strip id for source, -9999 if not a grass
          strip.
        - *gras_id_target* (float): grass strip id for target, -9999 if not a grass
          strip.

    Returns
    -------
    df_efficiency: pandas.DataFrame
        Sediment load flowing in and flowing out grass strip with the columns:

        - *gras_id_target* (float): target grass_id
        - *gras_id_source* (float): target grass_id
        - *sediin* (float): incoming sediment in grass strip
        - *sediout* (float): outgoing sediment out of grass strip
        - *eSTE* (float): estimated sediment trapping efficiency, see
          :func:`pywatemsedem.grasstrips.estimate_ste`
        - *sed* (float): amount of sedimentation

    Notes
    -----
    *gras_id_target* and *gras_id_source* are equal and refers to the gras_id (target).
    """

    condition = df_routing_grass["gras_id_source"] != df_routing_grass["gras_id_target"]
    df_sediout_grass = (
        df_routing_grass.loc[condition]
        .groupby("gras_id_source")
        .aggregate({"sediout": np.sum})
        .reset_index()
    )
    df_sediin_grass = (
        df_routing_grass.loc[condition]
        .groupby("gras_id_target")
        .aggregate({"sediout": np.sum})
        .reset_index()
    )
    df_sediin_grass = df_sediin_grass.rename(columns={"sediout": "sediin"})
    df_npixels = (
        df_routing_grass[["targetrow", "targetcol", "gras_id_target"]]
        .drop_duplicates()
        .groupby("gras_id_target")
        .size()
        .reset_index()
    )
    df_efficiency = df_sediin_grass[["gras_id_target", "sediin"]].merge(
        df_sediout_grass, left_on="gras_id_target", right_on="gras_id_source"
    )
    df_npixels.columns = ["gras_id_target", "npixels_r"]
    df_efficiency = df_efficiency.merge(df_npixels)
    df_efficiency["eSTE"] = estimate_ste(
        df_efficiency["sediin"], df_efficiency["sediout"]
    )
    df_efficiency["sed"] = df_efficiency["sediin"] - df_efficiency["sediout"]
    df_efficiency = df_efficiency[df_efficiency["gras_id_target"] != -9999]

    return df_efficiency


def merge_grass_strip_id_and_sediout_to_routing(
    df_grass_strips,
    df_sediout,
    df_routing,
):
    """Merge the id of the grass strips and the sediout (also pd list-format)
     to routing df.

    Filter grass strips which are not of landuse type -6 ('weide') with 'WaTEM/SEDEM
    perceelskaart'

    Parameters
    ----------
    df_grass_strips: pandas.DataFrame
        - *col* (int): col
        - *row* (int): row
        - *val* (int): gras_id

    df_sediout: pandas.DataFrame
        - *col* (int): col
        - *row* (int): row
        - *val* (fload): outgoing sediment

    df_routing: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`

    Returns
    -------
    df_routing_grass_id: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`,
        holding columns of df_routing and additional columns:

        - *gras_id_source* (int): gras_id value of the source pixel
        - *gras_id_target1* (int): gras_id value of the target1 pixel
        - *gras_id_target2* (int): gras_id value of the target2 pixel
    """
    # prepare merge
    for i in ["source", "target1", "target2"]:
        df_grass_strips[f"gras_id_{i}"] = df_grass_strips["val"]

    for target_id in [1, 2]:
        df_grass_strips[
            [f"target{target_id}row", f"target{target_id}col"]
        ] = df_grass_strips[["row", "col"]]

    # define sedout and index cols to join on
    df_sediout["sediout"] = df_sediout["val"]
    df_sediout = df_sediout.set_index(["col", "row"])

    # join gras_id sources
    df_routing_grass_id = merge_grass_id_to_routing(
        df_routing, df_grass_strips, ["col", "row"], ["gras_id_source"]
    )

    # join sediout
    df_routing_grass_id = df_routing_grass_id.join(
        df_sediout[["sediout"]], how="left"
    ).reset_index()
    df_routing_grass_id = merge_grass_id_to_routing(
        df_routing_grass_id,
        df_grass_strips,
        ["target1col", "target1row"],
        ["gras_id_target1"],
    ).reset_index()

    # joint gras ids targets
    df_routing_grass_id = merge_grass_id_to_routing(
        df_routing_grass_id,
        df_grass_strips,
        ["target2col", "target2row"],
        ["gras_id_target2"],
    ).reset_index()

    return df_routing_grass_id


def reformat_routing_grass(df_routing_grass):
    """Reformat the routing_gras DataFrame

    Reformat the routing_gras dataframe so targets 1 and 2 are reported in
    the same column target.

    Parameters
    ----------
    df_routing_grass: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`

    Returns
    -------
    df_routing_grass_T: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`

        - *gras_id_target* (float): id of the routing target
        - *sediout* (float): sediment output pixel

    """
    df_routing_grass["sediout1"] = (
        df_routing_grass["sediout"] * df_routing_grass["part1"]
    )
    df_routing_grass["sediout2"] = df_routing_grass["sediout"] * (
        1 - df_routing_grass["part1"]
    )

    df1 = select_and_rename_cols_grass_routing(df_routing_grass, 1)
    df2 = select_and_rename_cols_grass_routing(df_routing_grass, 2)

    df_routing_grass_T = pd.concat([df1, df2])

    return df_routing_grass_T


def select_and_rename_cols_grass_routing(df_routing_grass, target_id):
    """Select and rename columns of grass strip routing geodataframe.

    Parameters
    ----------
    df_routing_grass: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`
    target_id: int
        The number of the targets, can only be 1 or 2

    Returns
    -------
    df_routing_grass: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`,
        selected and renamed after target1 or target2
    """

    cols = {
        f"target{target_id}row": "targetrow",
        f"target{target_id}col": "targetcol",
        f"sediout{target_id}": "sediout",
        f"gras_id_target{target_id}": "gras_id_target",
    }
    cond = df_routing_grass[f"part{target_id}"] != 0
    df_routing_grass = df_routing_grass.loc[
        cond, ["row", "col", "gras_id_source"] + list(cols.keys())
    ].rename(columns=cols)

    return df_routing_grass


def filter_grass_strips_with_prckrt(df_grass_strips, df_prckrt, profile_grass_strips):
    """
    Use the CNWS 'perceelskaart' to filter grass strips (lay-over infr. and
    river cells over gras_buffer_id)

    Parameters
    ----------
    df_grass_strips: pandas.DataFrame
        see
        :func:`pywatemsedem.postprocess.merge_grass_strip_id_and_sediout_to_routing`
    df_prckrt: pandas.DataFrame

        - *col* (int): col
        - *row* (int): row
        - *val* (float): WaTEM/SEDEM perceelskaart id.

    profile_grass_strips: rasterio.profiles
        see :func:`rasterio.open`

    Returns
    -------
    df_grass_strips: pandas.DataFrame
        filtered data, see
        :func:`pywatemsedem.postprocess.merge_grass_strip_id_and_sediout_to_routing`
    """

    df_grass_strips.loc[df_prckrt["val"] != -6, "val"] = profile_grass_strips["nodata"]

    return df_grass_strips


def merge_grass_id_to_routing(df_routing, df_grass_strips, cols, field):
    """
    Merge the gras_id with the source, target1 and target2 pixels

    Parameters
    ----------
    df_routing: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`
    df_grass_strips: pandas.DataFrame
        See :func:`pywatemsedem.postprocess.merge_grass_strip_id_and_sediout_to_routing`
    cols: list
        Cols to consider for join
    field: str
        Column to use of df_grass_strips to do join

    Returns
    -------
    df_routing_merged: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file` with

        TO DO

    """
    df_routing = df_routing.set_index(cols)
    df_grass_strips = df_grass_strips.set_index(cols)
    df_routing_merged = df_routing.join(df_grass_strips[field], how="left")

    return df_routing_merged


def get_stats_ktc(rst_ktc, rst_prckrt):
    """Get statistics ktc-raster for specific land-uses

    The mean and  standard deviation of the ktc raster is computed,
    for the lande-use 'agriculture' and 'grass strips'.

    Parameters
    ----------
    rst_ktc: str or pathlib.Path
        File path of ktc raster.
    rst_prckrt: str or pathlib.Path
        File path WaTEM/SEDEM 'perceelskaart' raster

    Returns
    -------
    output: dictionary
        Dictionary with statistics of ktc for all agriculture and grass strip (gs)
        pixels. Keys:

        - *mean_ktc_agr* (float): mean ktc value of all agriculture pixels.
        - *std_ktc_agr* (float): standard deviation of all agriculture pixels.
        - *mean_ktc_gs* (float): median ktc value of all grass strip pixels.
        - *std_ktc_gs* (float): standard deviation of all grass strip pixels.
    """
    output = {}

    arr_prckrt, _ = load_raster(rst_prckrt)
    arr_ktc, _ = load_raster(rst_ktc)

    cond = arr_prckrt > 0
    output["mean_ktc_agr"] = np.median(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan
    output["std_ktc_agr"] = np.std(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan

    cond = arr_prckrt == -6
    output["mean_ktc_gs"] = np.mean(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan
    output["std_ktc_gs"] = np.std(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan

    return output


def get_stats_cfactor(rst_cfactor, rst_prckrt):
    """Get statistics ktc-raster for specific land-uses

    The mean and standard deviation of the cfactor raster is computed,
    for the lande-use 'agriculture' and 'grass strips.

    Parameters
    ----------
    rst_cfactor: str or pathlib.Path
        File path of ktc raster.
    rst_prckrt: str or pathlib.Path
        File path of WaTEM/SEDEM 'perceelskaart' raster

    Returns
    -------
    output: dictionary
        Dictionary with statistics of ktc for all agriculture and grass strip (gs)
        pixels. Keys:

        - *mean_cfactor_agr* (float): mean ktc value of all agriculture pixels.
        - *std_cfactor_agr* (float): standard deviation of all agriculture pixels.
        - *mean_cfactor_gs* (float): median ktc value of all grass strip pixels.
        - *std_cfactor_gs* (float): standard deviation of all grass strip pixels.
    """
    output = {}

    arr_prckrt, _ = load_raster(rst_prckrt)
    arr_ktc, _ = load_raster(rst_cfactor)

    cond = arr_prckrt > 0
    output["mean_cfactor_agr"] = np.mean(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan
    output["std_cfactor_agr"] = np.std(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan

    cond = arr_prckrt == -6
    output["mean_cfactor_gs"] = np.mean(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan
    output["std_cfactor_gs"] = np.std(arr_ktc[cond]) if np.sum(cond) != 0 else np.nan

    return output


def compute_netto_erosion_parcels(
    rst_prckrt,
    rst_watereros,
    rst_parcels_ids,
    resolution=20,
    fmap="results",
    flag_write=False,
    flag_join_vct_parcels=True,
):
    """Calculates the netto erosion for every parcel.

    Computes the netto erosion for every parcel by identifying the pixels
    netto erosion in a parcel and summing up these values. Netto erosion
    values are defined in the watereros raster, in which netto erosion is
    defined as a negative number, and netto deposition is defined as a
    positive number. Only negative numbers are considered for the
    computation of netto erosion.

    Parameters
    ----------
    rst_prckrt: string or pathlib.Path
        File path of the CNWS modelinput perceelskaart, note that the
        parcels_ids are limited by int16 (for WaTEM/SEDEM Pascal)
    rst_watereros: string or pathlib.Path
        File path of the CNWS modelouput watereros map
    rst_parcels_ids: string or pathlib.Path
        File path of the rasterfile holding the parcels_ids, not limited by
        int16
    resolution: int, default 20
    fmap: str, optional, default 'results'
        Output map
    flag_write: bool, default False
        Flag to indicate whether results should be written to disk

    Returns
    -------
    df_netto_erosion: pandas.DataFrame
        DataFrame holding statistics for every parcel with the columns:

        - *sum_netto_erosion* (float): total netto erosion (ton/pixel/year)
        - *average_netto_erosion* (float): mean netto erosion (ton/ha/year)
        - *std_dev_netto_erosion* (float): standard deviation netto erosion
          (kg/pixel/year)
        - *arr_parcel* (float): area of parcel (ha)

    Note
    ----
    1. Two rasters of the WaTEM/SEDEM perceelskaart are feeded to this function. The
    first one is a int16, the other is float64. The float64 parcel id's are
    used over the int16, because they go higher in maximum value. This is
    relevant for doing the analysis on large catchments.

    2. For details on the computation of netto erosion per parcel, see
    :func:`pywatemsedem.postprocess.compute_netto_ero_prckrt`
    """

    # make output dir
    fmap = Path(fmap)
    fmap.mkdir(parents=True, exist_ok=True)

    # load data
    arr_prckrt, profile = load_raster(rst_prckrt)
    arr_parcels_ids, _ = load_raster(rst_parcels_ids)
    arr_watereros, _ = load_raster(rst_watereros)

    # compute netto erosion arr with statistics per parcel
    dict_netto_ero = compute_netto_ero_prckrt(
        arr_prckrt, arr_watereros, arr_parcels_ids, resolution
    )

    # transform to dataframe and write to disk
    df_netto_erosion = transform_dict_netto_erosion_to_df(dict_netto_ero)

    if flag_join_vct_parcels:
        rst_parcels_ids = Path(rst_parcels_ids)
        vct_prcln = rst_parcels_ids.parents[0] / (str(rst_parcels_ids.stem) + ".shp")
        gdf_prcln = gpd.read_file(vct_prcln)
        gdf_prcln = gdf_prcln.merge(
            df_netto_erosion, left_on="NR", right_on="prc_id", how="left"
        )
    else:
        gdf_prcln = None
    if flag_write:
        txt_out = fmap / ("netto_erosion.csv")
        df_netto_erosion.to_csv(txt_out)
        if flag_join_vct_parcels:
            vct_out = fmap / "netto_erosion_parcels.shp"
            gdf_prcln.to_file(vct_out)

    return df_netto_erosion, gdf_prcln


def compute_netto_ero_prckrt(arr_prckrt, arr_watereros, arr_parcels_ids, resolution):
    """Calculates the netto erosion for every parcel.

    Compute the netto erosion for all parcels defined in the parcel raster.

        - Set all pixels where sedimentation (arr_watereros>0) in arr_prckrt
          occurs to zero.
        - Identify all pixels in arr_prckrt with the same parcel id.
        - Compute the sum, mean and standerd deviation of the netto erosion is
          computed for all selected pixels (only where erosion occurs) in the
          considered parcel.

    Parameters
    ----------
    arr_prckrt: numpy.ndarray
        WaTEM/SEDEM modelinput perceelskaart
    arr_watereros: numpy.ndarray
        WaTEM/SEDEM modelouput watereros map
    arr_parcels_ids: numpy.ndarray
        Array of raster format of parcels shapefile
    resolution: int
        Raster resolution

    Returns
    -------
    dict_netto_ero: dict
        {key:value} = {parcel_id:lst_statistics}

        - parcel id: int
        - lst_statistics: list containing of the following elements:

            - *total_netto_erosion* (float): total netto erosion (
              ton/pixel/year)
            - *mean_netto_erosion* (float): mean netto erosion (ton/ha/year)
            - *std_dev_netto_erosion* (float): standard deviation netto
              erosion (kg/pixel/year)
            - *arr_parcel* (float): area of parcel (ha)

    Note
    ----

    1. The watereros raster defines netto erosion and deposition. There are two cases
       that exist:

        - The total available sediment :math:`S_A` is smaller (or equal)
          than the transport capacity :math:`TC`. In this case **netto erosion** will
          occur at the rate of the mean annual soil rate (computed by RUSLE).
        - The available sediment :math:`S_A` is larger than the transport capacity
          :math:`TC`. If
          the incoming sediment :math:`S_i` is higher than :math:`TC` than
          **netto deposition** will
          occur :math:`S_i-TC`. If the :math:`S_i` is lower than :math:`TC` than
          **netto erosion** will occur at :math:`TC-S_i`

    2. The id's of the percelen raster is used to loop, and not the id's in the
    WaTEM/SEDEM perceelskaart. This format is used, as the end product should make
    statements on the level of parcels raster and not the 'WaTEM/SEDEM
    perceelskaart' (the parcels raster differs from the WaTEM/SEDEM perceelskaart,
    in the way it only contains information of parcels, and not other land
    covers).
    """
    prc_ids = np.unique(arr_parcels_ids)
    dict_netto_ero = {}

    condition_1 = np.ones(arr_prckrt.shape, dtype=bool)
    for i in [-6, -5, -2, -1]:
        condition_1 = np.where(arr_prckrt == i, False, condition_1)

    for prc_id in prc_ids:
        if prc_id != 0:
            # extract all forest, agriculture and grass land pixels
            condition = np.logical_and(arr_parcels_ids == prc_id, condition_1)

            arr_netto_ero_parcel = arr_watereros[condition]
            arr_netto_ero_parcel = np.where(
                arr_netto_ero_parcel < 0, arr_netto_ero_parcel, 0
            )
            if len(arr_netto_ero_parcel) > 0:
                dict_netto_ero[prc_id] = compute_netto_ero_parcel(
                    arr_netto_ero_parcel, resolution
                )
    return dict_netto_ero


def compute_netto_ero_parcel(arr_netto_erosion_parcel, resolution):
    """Compute netto erosion for one parcel.

    Compute the netto erosion for one parcel (only zero or non negative
    values). Negative values imply that no erosion or net deposition occurs.

    Parameters
    ----------
    arr_netto_erosion_parcel: numpy.ndarray
        Numpy array with netto erosion values (<=0) for pixels of one parcel
    resolution: int

    Returns
    -------
    list
        List with total, mean, std dev netto erosion for array, and area of
        the array

    Note
    ----

    1. The formula for the netto erosion per parcel (:math:`NE_{parcel}`) is
    the following

    .. math::

        NE_{parcel} = (1/n) sum_i^n (NE_i)/res^2

    with:
        - :math:`NE_i`: netto erosion for pixel :math:`i` (:math:`n` pixels in
          parcel) (ton/year). This netto erosion is derived from the watereros
          raster, in which positive values (deposition) are set to zero.
        - :math:`res`: model resulution (m).

    2. The array arr_netto_erosion_parcel can only contain non-positive
    numbers, as it only takes into account netto erosion.
    """
    if np.sum(arr_netto_erosion_parcel > 0) > 0:
        msg = (
            "Netto erosion parcels array contains positive values, this is"
            "not possible. Please redefine the netto erosion parcels array."
        )
        raise ValueError(msg)

    # kg/cell/year to ton/cell/year
    total_netto_erosion = np.sum(arr_netto_erosion_parcel) / 1000.0
    # kg/cel/year to ton/ha/year
    mean_netto_erosion = (
        np.mean(arr_netto_erosion_parcel) * 100.0**2 / resolution**2 / 1000.0
    )
    # kg/cell
    std_dev_netto_erosion = np.std(arr_netto_erosion_parcel)

    # compute area of parcel (ha)
    area = len(arr_netto_erosion_parcel.flatten()) / 100.0**2
    area_parcel = area * resolution**2

    return [total_netto_erosion, mean_netto_erosion, std_dev_netto_erosion, area_parcel]


def transform_dict_netto_erosion_to_df(dict_netto_ero):
    """
    Transform dictionary of netto erosion to a pandas dataframe format

    Parameters
    ----------
    dict_netto_ero: dict
        {key:value} = {parcel_id:lst_statistics}

        - parcel id: int
        - lst_statistics: list containing of the following elements:

            - *total_netto_erosion* (float): total netto erosion (
              ton/pixel/year)
            - *mean_netto_erosion* (float): mean netto erosion (ton/ha/year)
            - *std_dev_netto_erosion* (float): standard deviation netto
              erosion (kg/pixel/year)
            - *arr_parcel* (float): area of parcel (ha)

    Returns
    -------
    df_netto_erosion: pandas.DataFrame
        Holding statistics for every parcel according to dict_netto_ero
    """

    lst_columns = [
        "sum_netto_erosion",
        "average_netto_erosion",
        "std_dev_netto_erosion",
        "area_parcel",
    ]
    df_netto_erosion = pd.DataFrame.from_dict(
        dict_netto_ero, orient="index", columns=lst_columns
    )
    df_netto_erosion.index.name = "prc_id"

    return df_netto_erosion


def identify_subcatchments_to_buffers(
    rst_buffers,
    vct_buffers,
    txt_routing_nonriver,
    resmap,
    profile,
):
    """Identify subcatchment to each one of the buffers

    Parameters
    ----------
    rst_buffers: str or pathlib.Path
        File path of WaTEM/SEDEM buffer raster
    vct_buffers: str or pathlib.Path
        File path of buffers polygons
    txt_routing_nonriver: str or pathlib.Path
        File path of the WaTEM/SEDEM routing table without river routing included
    resmap: str or pathlib.Path
        Folder path of results folder
    profile: rasterio.profiles
            see :func:`rasterio.open`
    """
    arr_buffer, _ = load_raster(rst_buffers)
    gdf_buffers = gpd.read_file(vct_buffers)
    outlet_ids = gdf_buffers["BUF_ID"].tolist()
    mask = np.in1d(arr_buffer, outlet_ids).reshape(arr_buffer.shape)
    arr_outlet = np.where(mask, arr_buffer, profile["nodata"]).astype(np.float32)

    rst_outlet = resmap / (str(rst_buffers.stem) + "_outlet.rst")
    rstparams = rasterprofile_to_rstparams(profile)

    write_arr_as_rst(arr_outlet, rst_outlet, arr_outlet.dtype, rstparams)

    define_subcatchments_saga(
        rst_outlet,
        txt_routing_nonriver,
        resmap,
        profile,
        tag="catchments_to_buffers",
    )


def compute_cdf_sediment_load(
    df,
    column_value,
    resmap,
    tag=None,
    no_data=None,
    ignore_negative_values=False,
    plot=False,
):
    """Compute the cdf of sediment load in 'column_value' in the dataframe df

    Parameters
    ----------
    df: pandas.DataFrame
        Dataframe to compute cdf for
        - *column_value* (float): sediment load values
    column_value: str
        Column in 'df' to compute cdf for
    resmap: str or pathlib.Path
        Folder path to which write figure to
    no_data: float, optional
        No_data value in 'column_value'
    ignore_negative_values: float, optional
        Ignore negative values in column_value
    plot: str, optional
        Write plot to disk (True/False)

    Returns
    -------
    df: pandas.DataFrame
        Updated dataframe with cdf

        - *column_value* (float): sediment load values
        - *cum_sum* (float): cumulative sum of sediment load
        - *cdf* (float): cumulative distribution estimate

    """
    # calculate cumulative sum, in percentage
    df["value"] = df[column_value]
    df = df.sort_values("value")
    df["rank"] = np.nan
    cond = df["value"] != no_data
    if ignore_negative_values:
        cond = cond & (df["value"] > 0.0)
    df.loc[cond, "rank"] = np.arange(len(df.loc[cond]))
    df.loc[cond, "cum_sum"] = df.loc[cond, "value"].cumsum()
    df.loc[cond, "cdf"] = (
        100 * df.loc[cond, "cum_sum"] / df.loc[cond, column_value].sum()
    )

    if plot:
        if tag is not None:
            fname = resmap / f"cumulative_sedimentload_{tag}.png"
        else:
            fname = resmap / "cumulative_sedimentload.png"
        plot_cumulative_sedimentload(df.loc[cond], fname)

    return df


def couple_sediout_routing(vct_routing, rst_sediout, epsg, cols_out=None):
    """Couple the sediout raster values to the vector routing file

    Parameters
    ----------
    vct_routing: str or pathlib.Path
        File path of vector routing, see
        :func:`pywatemsedem.io.modeloutput.make_routing_vct`
    rst_sediout: str or pathlib.Path
        File path WaTEM/SEDEM output raster 'SediOut_kg.rst'
    epsg: str
        Format "EPSG:XXXXX"
    cols_out: list, optional
        Columns to output

    Returns
    -------
    gdf_routing: geopandas.GeoDataFrame
        Loaded vector file, for format
        see :func:`pywatemsedem.io.modeloutput.make_routing_vct`. Columns
        added:

        - *sediout* (float): Total Sediment output (scale:parcel) from pixel
        - *sediout1* (float): Sediment output coupled to arrow current pixel
        - *sediout2* (float): Sedimout output coupled to other output arrow current
          pixel
        - *cum_sum* (float): Cumulative sediment output based on sediout1
        - *cum_perc* (float): Cumulative percentage (%)
    """
    gdf_routing = gpd.read_file(vct_routing)

    # load sedOut
    arr_sediout, profile = load_raster(rst_sediout)
    df_sediout = raster_array_to_pandas_dataframe(arr_sediout, profile)
    df_sediout["sediout"] = df_sediout["val"].values

    # merge sediout to routing
    gdf_routing = gdf_routing.merge(
        df_sediout[["col", "row", "sediout"]], on=["col", "row"], how="left"
    )

    # (DR) sediout correction with part (%): sediout is total amount that goes out a
    # pixel (derived over two pixels).
    gdf_routing["sediout1"] = gdf_routing["sediout"] * gdf_routing["part"]
    gdf_routing["sediout2"] = gdf_routing["sediout"] * (1 - gdf_routing["part"])

    # (DR) Write cumulative percentage (descending)
    gdf_routing = gdf_routing.sort_values("sediout1", ascending=False)
    gdf_routing["cum_sum"] = gdf_routing["sediout1"].cumsum().astype(int)
    gdf_routing["cum_perc"] = (
        gdf_routing.cum_sum / gdf_routing["sediout1"].sum()
    ) * 100
    gdf_routing = gdf_routing.set_crs(epsg, allow_override=True)

    if cols_out is not None:
        gdf_routing = gdf_routing[cols_out]

    return gdf_routing


def select_routing_out_of_parcel(gdf_routing):
    """Select routing vectors defined over borders parcel

    Only select the routing vector which cross the parcel border.

    Parameters
    ----------
    gdf_routing: geopandas.GeoDataFrame
        Loaded routing vector file (with or without sediout coupled to it).
        See :func:`pywatemsedem.io.modeloutput.make_routing_vct`

    Returns
    -------
    gdf_routing: geopandas.GeoDataFrame
        Selected routing vector file (with or without sediout coupled to it).
        See :func:`pywatemsedem.io.modeloutput.make_routing_vct`
    """
    cond = gdf_routing["lnduSource"] != gdf_routing["lnduTarg"]
    gdf_routing = gdf_routing.loc[cond]
    cond = (gdf_routing["lnduSource"] > 0) & (
        gdf_routing["lnduTarg"] != np.max(gdf_routing["lnduSource"])
    )
    gdf_routing = gdf_routing.loc[cond]

    return gdf_routing


def convert_arr_from_kg_to_ton(rst_in, rst_out):
    """Set values of all pixels of a raster divided by 1000 (kg -> ton)

    Parameters
    ----------
    rst_in: str or pathlib.Path
        File path of input raster to set no data values
    rst_out: str or pathlib.Path
        File path of output raster with no data values
    """

    arr_in, profile = load_raster(rst_in)
    arr_out = np.where(arr_in == profile["nodata"], arr_in, arr_in / 1000)
    profile["driver"] = "GTiff"
    profile["compress"] = "DEFLATE"
    write_arr_as_rst(arr_out, rst_out, "float32", profile)


def convert_rst_sinks_to_vct(rst_in, vct_out, kind, epsg="EPSG:31370"):
    """Convert a sinks raster to a vector file.

    A sinks raster is defined as a raster holding captured sediment loads
    (i.e. rst_sewerin, rst_sediexport).

    Parameters
    ----------
    rst_in: str or pathlib.Path
        Input raster subject to convert to shape
    kind: str
        'sewer' or 'river'

    Returns
    -------
    vct_out: pathlib.Path
        Filename of the shapefile of the sinks

    """
    if kind not in ["river", "sewer"]:
        raise KeyError(f"{kind} of sink not in known.")

    rst_in = Path(rst_in)
    basename = rst_in.stem

    cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_grid", "3"]
    cmd_args += ["-GRIDS", str(rst_in)]
    cmd_args += ["-SHAPES", str(vct_out)]
    execute_saga(cmd_args)

    gdf_out = gpd.read_file(vct_out)
    gdf_out = gdf_out.set_crs(epsg, allow_override=True)
    gdf_out["type"] = kind
    gdf_out.rename(columns={basename[:11]: "sediment"}, inplace=True)
    gdf_out["sediment"] = np.round(
        gdf_out.sediment / 1000, 3
    )  # convert from kg to tonnes
    gdf_out = gdf_out.sort_values("sediment", ascending=False)
    gdf_out["cumsum"] = gdf_out["sediment"].cumsum()
    gdf_out["cumperc"] = (gdf_out["cumsum"] / (gdf_out["sediment"].sum())) * 100
    gdf_out = gdf_out.reset_index()
    gdf_out.drop(columns=["index", "ID", "X", "Y"], inplace=True)
    gdf_out.to_file(vct_out)


def compute_statistics_sediout_outside_domain(arr_sediout, arr_id, df_routing, profile):
    """Compute amount of sediout routing outside domain.

    Parameters
    ----------
    arr_sediout: numpy.ndarray
        WaTEM/SEDEM sediout raster.
    arr_id: numpy.ndarray
        An unique array id array, sediout outside domain is grouped by these id's.
        Should be integers or floats!
    df_routing: pandas.DataFrame
        Loaded WaTEM/SEDEM routing dataframe
    profile: rasterio.profile

    Returns
    -------
    pandas.Series
        Series holding sediout outside domain per id.
    """
    df_id = raster_array_to_pandas_dataframe(arr_id, profile)
    df_id["sid"] = df_id["val"]
    df_id["tid1"] = df_id["val"]
    df_id["tid2"] = df_id["val"]
    df_id["target1col"] = df_id["col"]
    df_id["target2col"] = df_id["col"]
    df_id["target1row"] = df_id["row"]
    df_id["target2row"] = df_id["row"]

    # couple rows and cols
    df_sediout = raster_array_to_pandas_dataframe(arr_sediout, profile)
    col = ["col", "row"]
    df_routing = df_routing.merge(df_id[col + ["sid"]], on=col, how="left")
    col = ["target1col", "target1row"]
    df_routing = df_routing.merge(df_id[col + ["tid1"]], on=col, how="left")
    col = ["target2col", "target2row"]
    df_routing = df_routing.merge(df_id[col + ["tid2"]], on=col, how="left")
    # source id's that are not equal to target id's
    df_routing = df_routing[
        (df_routing["sid"] != df_routing["tid1"])
        & (df_routing["sid"] != df_routing["tid2"])
    ]
    df_routing = df_routing.merge(df_sediout, on=["col", "row"], how="left")
    df_routing["val1"] = df_routing["part1"] * df_routing["val"]
    df_routing["val2"] = df_routing["part2"] * df_routing["val"]
    # compute stats
    t1 = df_routing.groupby("tid1").aggregate({"val1": np.sum})
    t2 = df_routing.groupby("tid1").aggregate({"val2": np.sum})

    return t1["val1"] + t2["val2"]


def process_filename(
    fmap_results, subfolder, filename, extension, arguments, arguments_input
):
    """
    Format full filename

    Parameters
    ----------
    fmap_results: str or pathlib.Path
        Folder path where pywatemsedem (scenario_x) input and output is saved
    subfolder: str or pathlib.Path
        Folder path in which a specific file 'filename' (relative path) resides
    filename:  str or pathlib.Path
        File path (without full path, without extension, with string
        formatting %)
    extension: str or pathlib.Path
        Extension of the file
    arguments: str or pathlib.Path
        Argument for the string formatting of filename
    arguments_input: dict
        Holding the {"year":year, "scenario": scenario, "catchment_name":
        catchment_name}

    Returns
    -------
    full_filename: pathlib.Path
        Full filename (absolute path, with filled in string formatting)

    Note
    ----
    String formatting in the code is done with '%' as the filename variable changes of
    content and is not accesable with f-strings.
    """
    if arguments == "":
        filename = filename
    else:
        year = arguments_input["year"]
        scenario = arguments_input["scenario"]
        catchment_name = arguments_input["catchment_name"]
        if arguments == "year, catchment, scenario":
            filename = filename % (year, catchment_name, scenario)
        elif arguments == "catchment":
            filename = filename % (catchment_name)
        elif arguments == "catchment, scenario":
            filename = filename % (catchment_name, scenario)
        else:
            if arguments != "":
                msg = f"Argument {arguments} not found in if/else-clause."
                raise Exception(msg)

    if subfolder != "main":
        if subfolder == "year":
            subfolder = (
                str(arguments_input["year"]) if "year" in arguments_input else "none"
            )
        full_filename = Path(fmap_results, subfolder, filename + "." + extension)
    else:
        full_filename = Path(fmap_results, filename + "." + extension)

    return full_filename


def read_filestructure(txt_filestructure=None, sep=","):
    """Read the pywatemsedem filestructure flanders file containing an overview of the files
    used for pywatemsedem flanders.

    The filestructure contains information on files written on disk by pywatemsedem. This
    file is used by the :class:`pywatemsedem.core.postprocess.PostProcess` object and
    :class:`pywatemsedem.core.merge_scenarios.SpatialMergeScenarios`.

    The filestructure pywatemsedem file can be used for to regenerate the filenames
    in a ``scenario_x`` folder without having to have the pywatemsedem objects loaded in
    memory (i.e. handy for starting a PostProcess instance from any simulation).

    Parameters
    ----------
    txt_filestructure : str or pathlib.Path, default None
        File path of table holding all data files/folder path references used in pywatemsedem
        flanders.
    sep : str, default ","
        Delimiter of the text file.

    Returns
    -------
    df_filestructure_flanders: pandas.DataFrame

        - *tag_variable* (str): unique tag used in code to identify file.
        - *prefix_variable* (str): prefix used for unique tag (depending on whether
          the file is a raster, text file, vector).
        - *folder* (str): subfolder in which file can be found in scenario.
        - *filename* (str): filename without specified arguments
        - *argument* (str): arguments such as year (int), catchment name (str),
          scenario label (str)
        - *extension* (str): extension of the file.
        - *mandatory* (int): indicate whether file is a mandatory file to run
          WaTEM/SEDEM.
        - *condition* (str): indicates whether presence of file is related to a
          WaTEM/SEDEM option.
        - *default_value* (float): default value (only for rasters)
        - *generate_nodata* (int): indicate whether a file must be made replacing 0's
          to nan.
        - *postprocess* (int): use generating for postprocessing.
        - *consider__* (int): state whether the file has to be loaded (0) or has to be
          generated (1).

    Note
    ----
    1. When no text data set file is defined, than the default defined in this
       package is used.
    2. Although the filestructure applies to pywatemsedem flanders, it is defined in the
       pywatemsedem postprocess.py core function, as the postprocess.py script contains many
       functionalities only coupled to flanders.

    Example
    -------
    An example of how the filesystem file can be used in the pywatemsedem code is given
    below. Assume that you have a pywatemsedem process and model run in
    ``molenbeek/scenario_1``. For example, if you wish to assign the filename of the
    buffers raster file in the ``modeloutput`` subfolder of ``scenario_1`` to a
    variable in pywatemsedem, you can use it as (using pathlib.Path module):

    .. code-block:: python

        dict_filenames = {}
        dict_filename[f"{prefix}_{tag_variable}"] = Path("molenbeek") / scenario_1 /
        f"{folder}" / (filename%argument + "." + extension)

    This way, automated filename reconstruction can be guided by the use of this table.
    """
    if txt_filestructure is None:
        ds = pkg_resources.resource_stream(__name__, "data/postprocess_files.csv")
    else:
        ds = open(txt_filestructure, mode="r")
    df_filestructure_flanders = pd.read_csv(ds, sep=sep)

    ds.close()

    cols = {
        "tag_variable",
        "prefix_variable",
        "folder",
        "filename",
        "argument",
        "extension",
        "mandatory",
        "condition",
        "default_value",
        "generate_nodata",
        "postprocess",
        "consider__",
    }
    if not cols.issubset(df_filestructure_flanders.columns):
        msg = f"DataFrame should contain {', '.join(cols)}."
        raise KeyError(msg)

    df_filestructure_flanders["condition"] = df_filestructure_flanders[
        "condition"
    ].fillna("")
    df_filestructure_flanders["argument"] = df_filestructure_flanders[
        "argument"
    ].fillna("")
    df_filestructure_flanders = df_filestructure_flanders[
        df_filestructure_flanders["consider__"] == 1
    ]

    return df_filestructure_flanders


def get_tuple_datastructure(df_datastructure_files, index):
    """Get one record of filestruture

    Parameters
    ----------
    df_datastructure_files: pandas.DataFrame
        See :func:`pywatemsedem.core.postprocess.read_filestructure_flanders`
    index :

    Returns
    -------
    f: tuple
        with "folder", "filename", "extension", "argument", "mandatory",
        "condition"
    """
    f = tuple(
        df_datastructure_files.loc[
            index,
            [
                "folder",
                "filename",
                "extension",
                "argument",
                "mandatory",
                "condition",
            ],
        ].to_list()
    )

    return f


def get_filename(df_datastructure_files, index, subfolder, year, simulations, scenario):
    """
    Get filename from datastructure with year, simulation and scenario

    Parameters
    ----------
    df_datastructure_files: pandas.DataFrame
        See :func:`pywatemsedem.core.postprocess.read_filestructure_flanders`
    index: any series index
        index of position dataframe
    subfolder: str
        subfolder
    year: int
        year of the simulation
    simulations:
        name of the simulation, usually catchment name
    scenario: str
        scenario tag

    Returns
    -------
    filename : pathlib.Path
        specific filename
    mandatory : int
        indicates wheter a file is mandatory or not
    """
    g = get_tuple_datastructure(df_datastructure_files, index)

    argument_inputs = {
        "year": year,
        "catchment_name": simulations,
        "scenario": scenario,
    }

    filename = process_filename(
        subfolder / f"scenario_{scenario}",
        g[0],
        g[1],
        g[2],
        g[3],
        argument_inputs,
    )

    mandatory = g[-2]

    return filename, mandatory
