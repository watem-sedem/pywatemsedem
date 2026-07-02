import logging
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from pywatemsedem.defaults import SAGA_FLAGS
from pywatemsedem.geo.factory import Factory
from pywatemsedem.geo.utils import (
    compute_statistics_rasters_per_polygon_vector,
    execute_saga,
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
from pywatemsedem.io.modelinput import Modelinput
from pywatemsedem.io.modeloutput import (
    Modeloutput,
    compute_efficiency_buffers,
    create_deposition_raster,
    create_erosion_raster,
    define_subcatchments_saga,
    load_total_sediment_file,
    make_routing_vct_saga,
    open_txt_routing_file,
)
from pywatemsedem.io.plots import plot_cumulative_sedimentload
from pywatemsedem.scenario import WSException
from pywatemsedem.tools import package_resource, zip_folder

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


def valid_routing_sedi_out_vector(self):
    """Check if routing vector is defined"""
    if self.vct_routing is None:
        msg = (
            "No routing vector (with sedi_out) created, please rirst run "
            "'couple_sedi_out_routing."
        )
        raise IOError(msg)


def valid_endpoints(self):
    """Check if endpoints are in available"""
    if self.files["rst_endpoints"] is None:
        msg = "No endpoints in subcatchments."
        raise IOError(msg)


def valid_rivers(self):
    """Check if rivers are available"""
    if self.files["rst_riverrouting"] is None:
        msg = "No rivers in subcatchments."
        raise IOError(msg)


class PostProcess(Factory):
    """Initialisation of the postprocess class.

    This class is used to process output data layers of data processing
    pywatemsedem.

    Parameters
    ----------
    home_folder: str or pathlib.Path
        path of folder to which results of scenario run are written too
    scenario_label: int
        scenario number
    year: int
        simulation year
    epsg: int, default 31370
        epsg-code


    Examples
    --------
    >>> from pywatemsedem.postprocess import PostProcess
    >>> pp = PostProcess(r"molenbeek", 1, 2019, 31370) # note that the folder
    >>> #molenbeek/scenario_1 and molenbeek/scenario_1/2019 must exist
    >>> pp.make_routing_vct() #make a vector file of the text routig file.

    """

    def __init__(self, home_folder, resolution, scenario_label, year, epsg):

        # DATA
        self._routing_non_river = None
        self._vct_routing = None
        self._vct_routing_missing = None
        self._vct_sedi_export = None
        self._vct_sewer_in = None
        self._vct_sinks = None
        self._vct_grass_strips = None
        self._vct_poi = None
        self._vct_buffers = None
        self._vct_priority_subcatchments = None
        self._vct_priority_points = None
        self._vct_point = None
        self._vct_points_dummy = {}
        self._sinks = None

        # general
        self.home_folder = Path(home_folder)
        self.resolution = resolution
        self.scenario_label = scenario_label
        self.year = year
        self.epsg = epsg

        self.catchment_name = self.home_folder.stem
        self.scenario = f"scenario_{self.scenario_label}"

        # test if fmap_results is found
        self.cfolder = CatchmentFolder(self.home_folder, self.resolution)
        self.sfolder = ScenarioFolders(self.cfolder, self.scenario_label, self.year)

        self.cfolder.check_all()
        self.sfolder.check_all()

        # Initialise ModelInput and ModelOutput objects
        self.ini = self.home_folder / self.scenario / "modelinput" / "inifile.ini"
        self.rstparams, self.rp = get_rstparams(self.ini, epsg=self.epsg)
        self.nodata = self.rp["nodata"]

        super().__init__(
            self.resolution,
            self.epsg,
            self.nodata,
            self.sfolder.postprocessing_folder,
        )

        self.modelinput = Modelinput(self.ini, self.resolution, self.epsg, self.nodata)
        self.modeloutput = Modeloutput(
            self.ini, self.resolution, self.epsg, self.nodata
        )

        # Enable automatic cleanup of stale postprocessing shapefiles.
        self.auto_cleanup_postprocessing_shapefiles = True

    def _workflow_subdir(self, workflow):
        """Return (and create) a dedicated workflow folder in postprocessing."""
        workflow_map = {
            "poi": "poi",
            "buffers": "buffers",
            "grass_strips": "grass_strips",
            "priority": "priority_subcatchments",
        }
        dirname = workflow_map.get(str(workflow), str(workflow))
        out_dir = self.sfolder.postprocessing_folder / dirname
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def _point_target_output_dir(self, parent_property_name):
        """Resolve output folder for point-target subcatchment workflows."""
        if parent_property_name == "vct_poi":
            return self._workflow_subdir("poi")
        if parent_property_name == "vct_priority_points":
            return self._workflow_subdir("priority")
        return self.sfolder.postprocessing_folder

    def zip_folder(self):
        """Zip output folder of scenario_x"""
        zip_folder(self.sfolder.scenario_folder)

    def _set_vector_from_input(
        self,
        vector_input,
        attr_name,
        geometry_type,
        field_name,
        plot_title=None,
        init_subcatchments=False,
    ):
        """Create a vector object from a path and store it on this instance."""
        if self.mask is None:
            self.mask = self.modelinput.mask.file_path

        if not isinstance(vector_input, (str, Path)):
            msg = f"'{field_name}' must be set with a path (str or pathlib.Path)."
            raise TypeError(msg)

        vector_obj = self.vector_factory(
            Path(vector_input),
            geometry_type,
            flag_clip=False,
        )
        self._ensure_vector_id_column(vector_obj)

        if init_subcatchments:
            vector_obj.vct_subcatchments = None

        setattr(self, attr_name, vector_obj)

        if plot_title is not None:
            self._attach_vector_plot(vector_obj, title=plot_title)

    def _ensure_id_column_on_gdf(self, gdf):
        """Ensure a GeoDataFrame has an integer ``id`` column."""
        if "id" in gdf.columns:
            return gdf, False

        gdf = gdf.copy()
        if gdf.empty:
            gdf["id"] = pd.Series(dtype=np.int64)
        else:
            gdf["id"] = np.arange(1, len(gdf) + 1, dtype=np.int64)
        return gdf, True

    def _ensure_vector_id_column(self, vector_obj, persist=True):
        """Ensure an in-memory vector object always exposes an ``id`` column."""
        if vector_obj is None or not hasattr(vector_obj, "geodata"):
            return

        gdf = vector_obj.geodata
        if gdf is None:
            return

        gdf, changed = self._ensure_id_column_on_gdf(gdf)
        vector_obj.geodata = gdf

        if changed and persist and hasattr(vector_obj, "file_path") and not gdf.empty:
            vector_path = Path(vector_obj.file_path)
            self._unlink_vector_dataset(vector_path)
            gdf.to_file(vector_path, spatial_index="YES")

    @property
    def routing_non_river(self):
        """Return the routing table without river routing."""
        if self._routing_non_river is None:
            self.remove_river_routing()
        return self._routing_non_river

    def remove_river_routing(self):
        """Remove river routing from routing file."""

        # Identify the rows and columns of the routing file
        # that are river routing (lnduSource == -1)
        rows, cols = np.where(self.modelinput.compositelanduse.arr == -1)
        river_coords = list(
            zip(rows + 1, cols + 1)
        )  # +1 as routing file is 1-based and not 0-based

        # Remove these rows and columns from the routing file
        df = self.modeloutput.routing.copy()
        to_remove = set(river_coords)
        df_filtered = df[~df[["row", "col"]].apply(tuple, axis=1).isin(to_remove)]

        self._routing_non_river = df_filtered.copy()

        # Save the filtered routing file
        self._routing_non_river.file_path = (
            self.sfolder.postprocessing_folder / "routing_non_river.txt"
        )
        self._routing_non_river.to_csv(
            self._routing_non_river.file_path,
            sep="\t",
            index=False,
        )

    @property
    def vct_routing(self):
        """Return the routing vector object.

        If the routing vector does not exist yet, it is created with default
        settings (full extent, no tile selection, no tag) via
        :meth:`make_routing_vct`.
        """
        if self._vct_routing is None:
            self.vct_routing = self.make_routing_vct()
        return self._vct_routing

    @vct_routing.setter
    def vct_routing(self, vector_input):
        """Set the routing vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing routing vector shapefile. The file is loaded
            via :meth:`vector_factory` so the result exposes ``.file_path``
            and ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_routing",
            "LineString",
            "vct_routing",
            plot_title="Catchment mask + rivers + routing",
        )

    def make_routing_vct(self, extent=None, tile_number=None, tag=""):
        """Make a routing vector file based on routingfile

        Parameters
        ----------
        extent: list
            list holding value of extent to consider, xmin,ymin,xmax,ymax
        tile_number: int
            id of tile
        tag: str
            tag to add to filename

        Returns
        -------
        file_path: pathlib.Path
            Path to the created routing vector shapefile.
        """
        file_path = self.sfolder.postprocessing_folder / (
            self.modeloutput.routing.file_path.stem + tag + ".shp"
        )

        make_routing_vct_saga(
            self.modeloutput.routing.file_path,
            self.modelinput.compositelanduse.file_path,
            file_path,
            self.rstparams,
            extent=extent,
            tile_number=tile_number,
        )

        # Set EPSG code to the shapefile
        gdf = gpd.read_file(file_path)
        gdf = gdf.set_crs(self.epsg)
        gdf.to_file(file_path)

        return file_path

    @property
    def vct_routing_missing(self):
        """Return the routing missing vector object.

        If the routing missing vector does not exist yet, it is created with default
        settings (full extent, no tile selection, no tag) via
        :meth:`make_routing_missing_vct`.
        """
        if self._vct_routing_missing is None:
            self.vct_routing_missing = self.make_routing_missing_vct()
        return self._vct_routing_missing

    @vct_routing_missing.setter
    def vct_routing_missing(self, vector_input):
        """Set the routing missing vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing routing missing vector shapefile. The file is loaded
            via :meth:`vector_factory` so the result exposes ``.file_path``
            and ``.geodata`.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_routing_missing",
            "LineString",
            "vct_routing_missing",
            plot_title="Catchment mask + rivers + missing routing",
        )

    def make_routing_missing_vct(self, extent=None, tile_number=None, tag=""):
        """Make a routing missing vector file based on routing missing file

        Parameters
        ----------
        extent: list
            list holding value of extent to consider, xmin,ymin,xmax,ymax
        tile_number: int
            id of tile
        tag: str
            tag to add to filename

        Returns
        -------
        file_path: pathlib.Path
            Path to the created routing missing vector shapefile.
        """
        file_path = self.sfolder.postprocessing_folder / (
            self.modeloutput.routing_missing.file_path.stem + tag + ".shp"
        )

        make_routing_vct_saga(
            self.modeloutput.routing_missing.file_path,
            self.modelinput.compositelanduse.file_path,
            file_path,
            self.rstparams,
            extent=extent,
            tile_number=tile_number,
        )

        # Set EPSG code to the shapefile
        gdf = gpd.read_file(file_path)
        gdf = gdf.set_crs(self.epsg)
        gdf.to_file(file_path)

        return file_path

    @property
    def vct_sedi_export(self):
        """Return the sedi_export vector file path.

        If the sedi_export vector does not exist yet, it is created via
        :meth:`make_sedi_export_vct`.
        """
        if self._vct_sedi_export is None:
            self.vct_sedi_export = self.make_sedi_export_vct()
        return self._vct_sedi_export

    @vct_sedi_export.setter
    def vct_sedi_export(self, vector_input):
        """Set the sedi_export vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing sedi_export vector shapefile. The file is loaded
            via :meth:`vector_factory` so the result exposes ``.file_path``
            and ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_sedi_export",
            "Point",
            "vct_sedi_export",
            plot_title="Catchment mask + rivers + sediment export",
        )

    def make_sedi_export_vct(self):
        """Make a sedi_export vector file from the raster.

        Returns
        -------
        file_path: pathlib.Path
            Path to the created sedi_export vector shapefile.
        """
        vct_out = (
            self.sfolder.postprocessing_folder
            / f"{self.modeloutput.sedi_export.file_path.stem}.shp"
        )
        convert_rst_sinks_to_vct(
            self.modeloutput.sedi_export.file_path, vct_out, "river", self.epsg
        )
        return vct_out

    @property
    def vct_sewer_in(self):
        """Return the sewer_in vector file path.

        If the sewer_in vector does not exist yet, it is created via
        :meth:`make_sewer_in_vct`.
        """
        if self._vct_sewer_in is None:
            self.vct_sewer_in = self.make_sewer_in_vct()
        return self._vct_sewer_in

    @vct_sewer_in.setter
    def vct_sewer_in(self, vector_input):
        """Set the sewer_in vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing sewer_in vector shapefile. The file is loaded
            via :meth:`vector_factory` so the result exposes ``.file_path``
            and ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_sewer_in",
            "Point",
            "vct_sewer_in",
            plot_title="Catchment mask + rivers + sewer inflow",
        )

    def make_sewer_in_vct(self):
        """Make a sewer_in vector file from the raster.

        Returns
        -------
        file_path: pathlib.Path
            Path to the created sewer_in vector shapefile.
        """
        vct_out = (
            self.sfolder.postprocessing_folder
            / f"{self.modeloutput.sewer_in.file_path.stem}.shp"
        )
        convert_rst_sinks_to_vct(
            self.modeloutput.sewer_in.file_path, vct_out, "sewer", self.epsg
        )
        return vct_out

    @property
    def vct_sinks(self):
        """Return the sinks vector object.

        If the sinks vector does not exist yet, it is created via
        :meth:`merge_vct_sinks`.
        """
        if self._vct_sinks is None:
            self.merge_vct_sinks()
        return self._vct_sinks

    @vct_sinks.setter
    def vct_sinks(self, vector_input):
        """Set the sinks vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing sinks vector shapefile. The file is loaded
            via :meth:`vector_factory` so the result exposes ``.file_path``
            and ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_sinks",
            "Point",
            "vct_sinks",
            plot_title="Catchment mask + rivers + sinks",
        )

    def merge_vct_sinks(self):
        """
        Merge sewer and river sink shapefiles into a single output shapefile.

        This method combines the features from ``vct_sewer_in`` and
        ``vct_sedi_export`` into one GeoDataFrame. The merged dataset is then:

        1. Sorted by the ``sediment`` field in descending order.
        2. Enriched with a cumulative sediment load column (``cumsum``).
        3. Enriched with a cumulative percentage column (``cumperc``).
        4. Written to a new shapefile in the post-processing folder.

        The output file is named:

        ``sinks.shp``

        Notes
        -----
        If either ``vct_sewer_in`` or ``vct_sedi_export`` is not available,
        no output file is created and a warning is logged.
        """
        if self.vct_sewer_in is None or self.vct_sedi_export is None:
            logger.error(
                "Cannot merge sinks: vct_sewer_in (%s) or "
                "vct_sedi_export (%s) is missing.",
                self.vct_sewer_in,
                self.vct_sedi_export,
            )
            return

        gdf_sinks = pd.concat(
            [
                self.vct_sewer_in.geodata,
                self.vct_sedi_export.geodata,
            ],
            ignore_index=True,
        )

        gdf_sinks = gdf_sinks.sort_values("sediment", ascending=False)
        gdf_sinks["cumsum"] = gdf_sinks["sediment"].cumsum()
        gdf_sinks["cumperc"] = (gdf_sinks["cumsum"] / gdf_sinks["sediment"].sum()) * 100

        gdf_sinks = gdf_sinks.reset_index(drop=True)

        vct_out = self.sfolder.postprocessing_folder / "sinks.shp"

        gdf_sinks.to_file(vct_out, spatial_index="YES")

        self.vct_sinks = vct_out
        self._auto_cleanup_postprocessing_shapefiles()

    @property
    def vct_grass_strips(self):
        """Return the grass strips vector object."""
        return self._vct_grass_strips

    @vct_grass_strips.setter
    def vct_grass_strips(self, vector_input):
        """Set the grass strips vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing grass strips vector shapefile. The file is loaded
            via :meth:`vector_factory` so the result exposes ``.file_path``
            and ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_grass_strips",
            "Polygon",
            "vct_grass_strips",
            plot_title="Catchment mask + rivers + grass strips",
        )

    def valid_grass_strips(self):
        """Validate the grass strips vector against compositelanduse.

        The vector is valid when:

        1. Polygon overlap only occurs on compositelanduse pixels with value
           -1 (water), -2 (roads) or -6 (grass strips).
        2. Every compositelanduse pixel with value -6 has polygon overlap.
        """
        if self._vct_grass_strips is None:
            return

        arr_compositelanduse = self.modelinput.compositelanduse.arr
        rows_grass, cols_grass = np.where(arr_compositelanduse == -6)

        gdf_grass = self._vct_grass_strips.geodata
        if gdf_grass is None or gdf_grass.empty:
            if len(rows_grass) == 0:
                return
            msg = (
                "Grass strips vector is empty, but compositelanduse contains "
                f"{len(rows_grass)} pixel(s) with value -6."
            )
            raise ValueError(msg)

        gdf_grass = gdf_grass[gdf_grass.geometry.notnull()].copy()
        gdf_grass = gdf_grass[~gdf_grass.geometry.is_empty]
        if gdf_grass.empty:
            if len(rows_grass) == 0:
                return
            msg = (
                "Grass strips vector has no valid geometries, but "
                "compositelanduse contains -6 pixels."
            )
            raise ValueError(msg)

        target_crs = f"EPSG:{self.epsg}"
        if gdf_grass.crs is not None and str(gdf_grass.crs) != target_crs:
            gdf_grass = gdf_grass.to_crs(target_crs)

        minx, miny, _, _ = self.rp["minmax"]
        res = self.rp["res"]
        nrows = self.rp["nrows"]

        def _build_pixel_geometries(rows, cols):
            return np.array(
                [
                    shapely.box(
                        minx + col * res,
                        miny + (nrows - row - 1) * res,
                        minx + (col + 1) * res,
                        miny + (nrows - row) * res,
                    )
                    for row, col in zip(rows, cols)
                ],
                dtype=object,
            )

        grass_union = shapely.union_all(gdf_grass.geometry.to_numpy())
        if grass_union.is_empty:
            if len(rows_grass) == 0:
                return
            msg = (
                "Grass strips vector has empty union geometry, but "
                "compositelanduse contains -6 pixels."
            )
            raise ValueError(msg)

        # Rule 1: polygon overlap is only allowed on -1, -2 or -6 pixels.
        allowed_values = np.array([-1, -2, -6])
        allowed_mask = np.isin(arr_compositelanduse, allowed_values)
        rows_disallowed, cols_disallowed = np.where(~allowed_mask)
        if len(rows_disallowed) > 0:
            disallowed_geometries = _build_pixel_geometries(
                rows_disallowed, cols_disallowed
            )
            disallowed_overlap = (
                shapely.area(shapely.intersection(disallowed_geometries, grass_union))
                > 0
            )
            invalid_idx = np.where(disallowed_overlap)[0]

            if invalid_idx.size > 0:
                preview = ", ".join(
                    [
                        (
                            f"(row={int(rows_disallowed[i]) + 1}, "
                            f"col={int(cols_disallowed[i]) + 1}, "
                            f"""value={int(arr_compositelanduse[
                                rows_disallowed[i],
                                cols_disallowed[i]
                          ])})"""
                        )
                        for i in invalid_idx[:10]
                    ]
                )
                msg = (
                    "Invalid grass strips vector: polygon overlap is only allowed "
                    "on compositelanduse values -1, -2 and -6. "
                    f"Found overlap in {invalid_idx.size} disallowed pixel(s). "
                    f"Examples: {preview}."
                )
                raise ValueError(msg)

        # Rule 2: every -6 pixel must have overlap with a grass strip polygon.
        if len(rows_grass) > 0:
            grass_pixel_geometries = _build_pixel_geometries(rows_grass, cols_grass)
            grass_overlap = (
                shapely.area(shapely.intersection(grass_pixel_geometries, grass_union))
                > 0
            )
            missing_idx = np.where(~grass_overlap)[0]

            if missing_idx.size > 0:
                preview = ", ".join(
                    [
                        f"(row={int(rows_grass[i]) + 1}, col={int(cols_grass[i]) + 1})"
                        for i in missing_idx[:10]
                    ]
                )
                msg = (
                    "Invalid grass strips vector: every compositelanduse pixel "
                    "with value -6 must have polygon overlap. "
                    f"Missing coverage for {missing_idx.size} pixel(s). "
                    f"Examples: {preview}."
                )
                raise ValueError(msg)

    def process_grass_strips(self, compute_priority=True):
        """Compute grass strips efficiency and compute priority

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
                - *sedi_in* (float): total incoming sediment in grass strip (kg)
                - *sedi_out* (float): total outgoing sediment out of grass strip (kg)
                - *eSTE* (float): estimated sediment trapping efficiency, see
                  :func:`pywatemsedem.grasstrips.estimate_ste` (%)
                - sed (float): amount of sedimentation (kg)
                - *column_value* (float): deposition in grass strip.
                - *cum_sum* (float): cumulative sum of deposition in grass strips
                - *cdf* (float): cumulative distribution estimate.
        """
        logger.info("Calculating in- and output of sediment for every grass strip...")

        if self.vct_grass_strips is None:
            msg = (
                "No grass strips vector available. Set 'vct_grass_strips' "
                "first with a path."
            )
            raise ValueError(msg)

        grass_dir = self._workflow_subdir("grass_strips")
        rst_grass_strips_id = grass_dir / "grass_strips_id.rst"

        arr_grass_strips_id = self.vct_grass_strips.rasterize(
            self.modelinput.compositelanduse.file_path,
            self.epsg,
            col="NR",
            dtype_raster="integer",
            nodata=-9999,
            gdal=False,
        )

        write_arr_as_rst(
            arr_grass_strips_id,
            rst_grass_strips_id,
            np.int32,
            self.rstparams,
        )

        _, _, df_grass_strips_eff = compute_efficiency_grass_strips(
            self.modeloutput.routing.file_path,
            rst_grass_strips_id,
            self.modelinput.compositelanduse.file_path,
            self.modeloutput.sedi_out.file_path,
        )

        gdf_grass_strips = self.vct_grass_strips.geodata.copy()
        gdf_grass_strips = gdf_grass_strips.merge(
            df_grass_strips_eff, left_on="NR", right_on="gras_id_target", how="left"
        )
        if compute_priority:
            gdf_grass_strips = compute_cdf_sediment_load(
                gdf_grass_strips,
                "sed",
                grass_dir,
                ignore_negative_values=True,
                tag="grass_strips",
                plot=True,
            )

        return gdf_grass_strips

    def add_poi(
        self,
        x_coord,
        y_coord,
        poi_id=1,
        filename="poi.shp",
        lonlat=False,
    ):
        """Add one or more points-of-interest (POI) to the PostProcess object.

        Parameters
        ----------
        x_coord: float or array-like
                        X coordinate(s) of one or more POIs.

                        - Default: interpreted in ``self.epsg``.
                        - If ``lonlat=True``: interpreted as decimal longitude(s)
                            in ``EPSG:4326``.
        y_coord: float or array-like
                        Y coordinate(s) of one or more POIs.

                        - Default: interpreted in ``self.epsg``.
                        - If ``lonlat=True``: interpreted as decimal latitude(s)
                            in ``EPSG:4326``.
        poi_id: int or array-like, default 1
            Identifier(s) written to field ``poi_id``.

            - For a single POI, pass an integer.
            - For multiple POIs, pass a list/array with one id per coordinate pair.
            - If multiple POIs are given and ``poi_id`` is a single integer,
              sequential ids are generated starting from that value.
        filename: str, default "poi.shp"
            Name of the POI vector written in the postprocessing folder.
        lonlat: bool, default False
            If ``True``, interpret coordinates as decimal longitude/latitude
            in ``EPSG:4326``. Otherwise, coordinates are interpreted in
            ``self.epsg``.

        Returns
        -------
        pathlib.Path
            File path of the written POI vector containing one or more POIs.
        """
        x_vals = np.atleast_1d(x_coord).astype(float)
        y_vals = np.atleast_1d(y_coord).astype(float)

        if x_vals.size != y_vals.size:
            msg = "'x_coord' and 'y_coord' must have the same number of values."
            raise ValueError(msg)

        npoi = x_vals.size

        if np.isscalar(poi_id):
            poi_start = int(poi_id)
            if npoi == 1:
                poi_ids = [poi_start]
            else:
                poi_ids = list(range(poi_start, poi_start + npoi))
        else:
            poi_ids = [int(i) for i in np.atleast_1d(poi_id)]
            if len(poi_ids) != npoi:
                msg = (
                    "If 'poi_id' is array-like, it must have the same length "
                    "as coordinates."
                )
                raise ValueError(msg)

        source_epsg = 4326 if lonlat else int(self.epsg)

        gdf_poi = gpd.GeoDataFrame(
            {"poi_id": poi_ids},
            geometry=[
                shapely.geometry.Point(float(x), float(y))
                for x, y in zip(x_vals, y_vals)
            ],
            crs=f"EPSG:{source_epsg}",
        )

        if source_epsg != int(self.epsg):
            gdf_poi = gdf_poi.to_crs(epsg=int(self.epsg))

        mask_geodata = self.modelinput.vct_mask.geodata
        if hasattr(mask_geodata, "union_all"):
            catchment_geom = mask_geodata.union_all()
        else:
            catchment_geom = mask_geodata.unary_union
        outside_pois = []
        for pid, point in zip(poi_ids, gdf_poi.geometry):
            if not catchment_geom.covers(point):
                outside_pois.append((int(pid), float(point.x), float(point.y)))

        if outside_pois:
            bounds = self.modelinput.vct_mask.geodata.total_bounds
            outside_txt = "; ".join(
                [f"poi_id={pid} at ({x:.3f}, {y:.3f})" for pid, x, y in outside_pois]
            )
            msg = (
                "POI coordinates must be inside the catchment mask. "
                f"Outside POI(s): {outside_txt}. "
                f"Catchment bounds in EPSG:{int(self.epsg)} are "
                f"(xmin={bounds[0]:.3f}, ymin={bounds[1]:.3f}, "
                f"xmax={bounds[2]:.3f}, ymax={bounds[3]:.3f})."
            )
            raise ValueError(msg)

        poi_dir = self._workflow_subdir("poi")
        vct_poi = poi_dir / Path(filename).name
        if vct_poi.suffix.lower() == ".shp":
            for suffix in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                part = vct_poi.with_suffix(suffix)
                if part.exists():
                    part.unlink()
        elif vct_poi.exists():
            vct_poi.unlink()

        gdf_poi.to_file(vct_poi)
        self.vct_poi = vct_poi
        self._auto_cleanup_postprocessing_shapefiles()

        return vct_poi

    @property
    def vct_poi(self):
        """Return the point-of-interest vector object.

        If it does not exist yet, an error is raised.
        """
        if self._vct_poi is None:
            raise IOError("No POI vector available.")
        return self._vct_poi

    @vct_poi.setter
    def vct_poi(self, vector_input):
        """Set the point-of-interest vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing POI vector shapefile. The file is loaded via
            :meth:`vector_factory` so the result exposes ``.file_path`` and
            ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_poi",
            "Point",
            "vct_poi",
            plot_title="Catchment mask + rivers + points of interest",
            init_subcatchments=True,
        )

    @property
    def vct_priority_points(self):
        """Return the points-of-interest vector object.

        If it does not exist yet, an error is raised.
        """
        if self._vct_priority_points is None:
            raise IOError("No priority points-of-interest vector available.")
        return self._vct_priority_points

    @vct_priority_points.setter
    def vct_priority_points(self, vector_input):
        """Set the points-of-interest vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing POI vector shapefile. The file is loaded via
            :meth:`vector_factory` so the result exposes ``.file_path`` and
            ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_priority_points",
            "Point",
            "vct_priority_points",
            plot_title="Catchment mask + rivers + priority points",
            init_subcatchments=True,
        )

    @property
    def vct_priority_subcatchments(self):
        """Return the priority subcatchments vector object.

        Primary storage is on ``vct_priority_points.vct_subcatchments``.
        This property is retained as a compatibility alias.
        """
        if (
            self._vct_priority_points is not None
            and getattr(self._vct_priority_points, "vct_subcatchments", None)
            is not None
        ):
            return self._vct_priority_points.vct_subcatchments

        if self._vct_priority_subcatchments is None:
            raise IOError("No priority subcatchments vector available.")
        return self._vct_priority_subcatchments

    @vct_priority_subcatchments.setter
    def vct_priority_subcatchments(self, vector_input):
        """Set the priority subcatchments vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing priority subcatchments vector shapefile. The file
            is loaded via :meth:`vector_factory` so the result exposes
            ``.file_path`` and ``.geodata``.
        """
        if self.mask is None:
            self.mask = self.modelinput.mask.file_path

        if not isinstance(vector_input, (str, Path)):
            msg = (
                "'vct_priority_subcatchments' must be set with a path "
                "(str or pathlib.Path)."
            )
            raise TypeError(msg)

        self._vct_priority_subcatchments = self.vector_factory(
            Path(vector_input),
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(self._vct_priority_subcatchments)

        if self._vct_priority_points is not None:
            self._vct_priority_points.vct_subcatchments = (
                self._vct_priority_subcatchments
            )
            self._attach_subcatchments_plot(self._vct_priority_points)

    @property
    def vct_buffers(self):
        """Return the buffers vector object.

        If the buffers vector does not exist yet, it is created with default
        settings via :meth:`add_buffers`.
        """
        if self._vct_buffers is None:
            self.vct_buffers = self.add_buffers()
        return self._vct_buffers

    @vct_buffers.setter
    def vct_buffers(self, vector_input):
        """Set the buffers vector object from a file path.

        Parameters
        ----------
        vector_input: pathlib.Path or str
            Path to an existing buffers vector shapefile. The file is loaded via
            :meth:`vector_factory` so the result exposes ``.file_path`` and
            ``.geodata``.
        """
        self._set_vector_from_input(
            vector_input,
            "_vct_buffers",
            "Polygon",
            "vct_buffers",
            plot_title="Catchment mask + rivers + buffers",
            init_subcatchments=True,
        )

    def add_buffers(self, filename="buffers.shp"):
        """Create a buffers vector from ``modelinput.buffers``.

        Buffers are always derived by vectorizing
        ``self.modelinput.buffers.arr`` with nodata-aware masking.
        A ``buffer_id`` field is created and used as stable identifier for
        downstream subcatchment delineation.

        Parameters
        ----------
        filename: str, default "buffers.shp"
            Name of the output buffers vector in the postprocessing folder.

        Returns
        -------
        pathlib.Path
            File path of the written buffers vector.
        """
        from rasterio.features import shapes
        from shapely.geometry import shape

        buffers_obj = self.modelinput.buffers

        arr_buffers = np.asarray(buffers_obj.arr)
        nodata = self.rstparams["nodata"]

        if pd.isna(nodata):
            valid_mask = ~np.isnan(arr_buffers)
        else:
            valid_mask = arr_buffers != nodata
        valid_mask = valid_mask & (arr_buffers > 0)

        if not np.any(valid_mask):
            msg = "No positive buffer cells found in modelinput.buffers.arr."
            raise ValueError(msg)

        shape_generator = shapes(
            arr_buffers.astype(np.int32),
            mask=valid_mask,
            transform=self.rstparams["transform"],
        )
        records = [
            {"VALUE": int(value), "geometry": shape(geom)}
            for geom, value in shape_generator
            if int(value) > 0
        ]
        gdf_buffers = gpd.GeoDataFrame(records, geometry="geometry", crs=self.epsg)

        if gdf_buffers.crs is None:
            gdf_buffers = gdf_buffers.set_crs(self.epsg)
        else:
            gdf_buffers = gdf_buffers.to_crs(self.epsg)

        id_column = self._infer_polygon_id_column(gdf_buffers)
        if id_column is not None:
            gdf_buffers = gdf_buffers[gdf_buffers[id_column] > 0].copy()
            exid_offset = 2**14
            raw_ids = gdf_buffers[id_column].astype(int)
            gdf_buffers["buffer_id"] = np.where(
                raw_ids > exid_offset,
                raw_ids - exid_offset,
                raw_ids,
            ).astype(int)
            # Merge all polygon parts belonging to one logical buffer id.
            gdf_buffers = gdf_buffers[["buffer_id", "geometry"]].dissolve(
                by="buffer_id",
                as_index=False,
            )
        else:
            gdf_buffers = gdf_buffers.copy()
            gdf_buffers["buffer_id"] = np.arange(1, len(gdf_buffers) + 1)

        buffer_dir = self._workflow_subdir("buffers")
        vct_buffers = buffer_dir / Path(filename).name
        self._unlink_vector_dataset(vct_buffers)
        gdf_buffers.to_file(vct_buffers, spatial_index="YES")

        self.vct_buffers = vct_buffers
        self._auto_cleanup_postprocessing_shapefiles()
        return vct_buffers

    def identify_subcatchments_to_buffers(self):
        """Define the separate subcatchments to the buffer outlets.

        See :func:`pywatemsedem.postprocess.identify_subcatchments_to_target_ids`
        """
        vct_buffers = self.vct_buffers

        routing_nonriver = self.routing_non_river.file_path
        if not routing_nonriver.exists():
            self.remove_river_routing()

        arr_buffers = self.modelinput.buffers.arr.astype(np.int64)
        unique_ids = np.unique(arr_buffers[arr_buffers > 0])
        exid_offset = 2**14

        # WaTEM/SEDEM buffer maps can encode buffer body as id+2**14 and
        # outlet cells as plain id; for delineation we need the outlet ids.
        if np.any(unique_ids > exid_offset):
            outlet_ids = unique_ids[(unique_ids > 0) & (unique_ids <= exid_offset)]
        else:
            outlet_ids = unique_ids

        if outlet_ids.size == 0:
            msg = "No buffer outlet ids found in modelinput buffers raster."
            raise ValueError(msg)

        nodata = self.rstparams["nodata"]
        arr_buffer_outlets = np.where(
            np.isin(arr_buffers, outlet_ids),
            arr_buffers,
            nodata,
        ).astype(np.float32)

        buffer_dir = self._workflow_subdir("buffers")
        rst_buffer_outlets = buffer_dir / "buffers_outlet_ids.rst"
        write_arr_as_rst(
            arr_buffer_outlets,
            rst_buffer_outlets,
            arr_buffer_outlets.dtype,
            self.rstparams,
        )

        _, vct_subcatchments = identify_subcatchments_to_target_ids(
            rst_buffer_outlets,
            routing_nonriver,
            buffer_dir,
            self.rp,
            tag="subcatchments_to_buffers",
        )

        vct_buffers.vct_subcatchments = self.vector_factory(
            Path(vct_subcatchments),
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(vct_buffers.vct_subcatchments)
        self._attach_buffer_subcatchments_plot(vct_buffers)
        self._remove_individual_subcatchment_shapefiles(
            buffer_dir,
            keep_paths=[vct_subcatchments],
        )
        self._auto_cleanup_postprocessing_shapefiles()

        return vct_subcatchments

    def _infer_point_id_column(self, gdf, requested=None):
        """Infer a point id column from a point GeoDataFrame."""
        if requested is not None:
            if requested not in gdf.columns:
                msg = f"Requested id_column '{requested}' not found in point vector."
                raise ValueError(msg)
            return requested

        for candidate in [
            "target_id",
            "poi_id",
            "priority_id",
            "priority_i",
            "id",
            "ID",
            "NR",
            "nr",
        ]:
            if candidate in gdf.columns:
                return candidate

        msg = "No id column found in point vector. Please provide 'id_column'."
        raise ValueError(msg)

    def _infer_polygon_id_column(self, gdf):
        """Infer an id column from a polygon GeoDataFrame."""
        for candidate in ["buffer_id", "NR", "nr", "id", "ID", "VALUE"]:
            if candidate in gdf.columns:
                return candidate
        return None

    def _add_river_overlay(self, ax, river_color="#1f78b4"):
        """Plot river raster cells as a fixed-color overlay."""
        import rasterio
        from matplotlib.colors import ListedColormap
        from rasterio.plot import show

        with rasterio.open(self.modelinput.riverrouting.file_path) as src:
            arr = src.read(1)
            nodata = src.nodata
            river_cells = arr > 0
            if nodata is not None:
                river_cells = river_cells & (arr != nodata)

            river_mask = np.ma.masked_where(
                ~river_cells,
                np.ones_like(arr, dtype=np.uint8),
            )
            show(
                river_mask,
                transform=src.transform,
                ax=ax,
                cmap=ListedColormap([river_color]),
                alpha=0.9,
            )

    def _default_vector_plot_kwargs(self, vector_obj):
        """Return default plot kwargs based on geometry type."""
        gdf = getattr(vector_obj, "geodata", None)
        if gdf is None or gdf.empty:
            return {}

        geom_types = set(gdf.geometry.geom_type.dropna().unique().tolist())
        if geom_types & {"Point", "MultiPoint"}:
            return {
                "color": "#d73027",
                "markersize": 25,
                "alpha": 0.9,
            }
        if geom_types & {"LineString", "MultiLineString"}:
            return {
                "color": "#d73027",
                "linewidth": 1.4,
                "alpha": 0.9,
            }
        return {
            "color": "#d73027",
            "alpha": 0.55,
            "edgecolor": "white",
            "linewidth": 0.5,
        }

    def _attach_vector_plot(self, vector_obj, title="Vector"):
        """Attach plot() with catchment mask and river context to a vector."""
        if vector_obj is None:
            return

        default_kwargs = self._default_vector_plot_kwargs(vector_obj)

        def plot(
            ax=None,
            show_mask=True,
            show_river=True,
            show_labels=True,
            label_column="id",
            label_color="black",
            label_fontsize=8,
            label_weight="normal",
            river_color="#1f78b4",
            title=title,
            **kwargs,
        ):
            import matplotlib.pyplot as plt

            if ax is None:
                _, ax = plt.subplots(figsize=(8, 8))

            if show_mask:
                self.vct_mask.geodata.plot(
                    ax=ax,
                    facecolor="none",
                    edgecolor="black",
                    linewidth=1,
                )

            if show_river:
                self._add_river_overlay(ax, river_color=river_color)

            gdf = vector_obj.geodata
            if gdf is not None and not gdf.empty:
                plot_kwargs = dict(default_kwargs)
                plot_kwargs.update(kwargs)
                plot_kwargs["ax"] = ax
                gdf.plot(**plot_kwargs)

                if show_labels and label_column in gdf.columns:
                    for _, row in gdf.iterrows():
                        geom = row.geometry
                        if geom is None or geom.is_empty:
                            continue
                        point = (
                            geom
                            if geom.geom_type == "Point"
                            else geom.representative_point()
                        )
                        ax.annotate(
                            str(row[label_column]),
                            (point.x, point.y),
                            xytext=(3, 3),
                            textcoords="offset points",
                            fontsize=label_fontsize,
                            color=label_color,
                            weight=label_weight,
                        )

            ax.set_aspect("equal")
            ax.set_title(title)
            plt.tight_layout()
            return ax

        vector_obj.plot = plot

    def _infer_subcatchment_label_column(self, gdf, preferred=None):
        """Infer a label column for subcatchment polygons."""
        if preferred is not None and preferred in gdf.columns:
            return preferred

        for candidate in [
            "target_id",
            "VALUE",
            "buffer_id",
            "poi_id",
            "priority_id",
            "id",
            "ID",
            "NR",
            "nr",
        ]:
            if candidate in gdf.columns:
                return candidate
        return None

    def _annotate_subcatchment_labels(
        self,
        ax,
        subcatchments_obj,
        label_column,
        label_color="black",
        label_fontsize=9,
        label_weight="bold",
    ):
        """Place labels in the middle of each subcatchment polygon."""
        if (
            label_column is None
            or label_column not in subcatchments_obj.geodata.columns
        ):
            return

        for _, row in subcatchments_obj.geodata.iterrows():
            point = row.geometry.representative_point()
            ax.annotate(
                str(row[label_column]),
                (point.x, point.y),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=label_fontsize,
                color=label_color,
                weight=label_weight,
            )

    def _plot_subcatchments_base(
        self,
        subcatchments_obj,
        ax=None,
        column="VALUE",
        show_river=True,
        river_color="#1f78b4",
        alpha=0.6,
        edgecolor="white",
        linewidth=0.5,
        **kwargs,
    ):
        """Plot catchment boundary + subcatchments (+ optional river overlay)."""
        import matplotlib.pyplot as plt

        if ax is None:
            _, ax = plt.subplots(figsize=(8, 8))

        self.vct_mask.geodata.plot(
            ax=ax,
            facecolor="none",
            edgecolor="black",
            linewidth=1,
        )

        plot_kwargs = {
            "ax": ax,
            "alpha": alpha,
            "edgecolor": edgecolor,
            "linewidth": linewidth,
            "legend": False,
        }
        if column is not None and column in subcatchments_obj.geodata.columns:
            plot_kwargs["column"] = column
        plot_kwargs.update(kwargs)
        subcatchments_obj.geodata.plot(**plot_kwargs)

        if show_river:
            self._add_river_overlay(ax, river_color=river_color)

        return ax

    def _plot_overlay_with_labels(
        self,
        ax,
        overlay_obj,
        show_overlay=True,
        show_labels=True,
        id_column=None,
        point_labels=False,
        label_color="black",
        label_fontsize=9,
        label_weight="bold",
        **plot_kwargs,
    ):
        """Plot an overlay vector and optionally annotate feature labels."""
        if not show_overlay:
            return

        overlay_obj.geodata.plot(ax=ax, **plot_kwargs)

        if not show_labels:
            return

        if id_column is None:
            return

        for _, row in overlay_obj.geodata.iterrows():
            if point_labels:
                x, y = row.geometry.x, row.geometry.y
                offset = (4, 4)
            else:
                point = row.geometry.representative_point()
                x, y = point.x, point.y
                offset = (3, 3)

            ax.annotate(
                str(row[id_column]),
                (x, y),
                xytext=offset,
                textcoords="offset points",
                fontsize=label_fontsize,
                color=label_color,
                weight=label_weight,
            )

    def _get_buffers_overlay_vector(self):
        """Return a polygon vector object for plotting buffers overlay."""
        if self._vct_buffers is None:
            msg = "No buffers vector available. Call 'add_buffers()' first."
            raise ValueError(msg)
        return self.vct_buffers

    def _plot_coupled_subcatchments(
        self,
        subcatchments_obj,
        ax=None,
        column="VALUE",
        show_river=True,
        show_labels=True,
        river_color="#1f78b4",
        alpha=0.6,
        edgecolor="white",
        linewidth=0.5,
        title="Subcatchments",
        overlay_obj=None,
        overlay_kwargs=None,
        **kwargs,
    ):
        """Shared plot pipeline for coupled subcatchment vectors."""
        import matplotlib.pyplot as plt

        ax = self._plot_subcatchments_base(
            subcatchments_obj,
            ax=ax,
            column=column,
            show_river=show_river,
            river_color=river_color,
            alpha=alpha,
            edgecolor=edgecolor,
            linewidth=linewidth,
            **kwargs,
        )

        if overlay_obj is not None:
            self._plot_overlay_with_labels(
                ax,
                overlay_obj,
                **(overlay_kwargs or {}),
            )

        if show_labels:
            if "id" in subcatchments_obj.geodata.columns:
                label_column = "id"
            else:
                label_column = self._infer_subcatchment_label_column(
                    subcatchments_obj.geodata,
                    preferred=column,
                )
            self._annotate_subcatchment_labels(
                ax,
                subcatchments_obj,
                label_column,
                label_color="black",
                label_fontsize=9,
                label_weight="bold",
            )

        ax.set_aspect("equal")
        ax.set_title(title)
        plt.tight_layout()
        return ax

    def _attach_buffer_subcatchments_plot(self, buffers_vector_obj):
        """Attach a convenience plot() to ``vct_buffers.vct_subcatchments``."""
        subcatchments_obj = getattr(buffers_vector_obj, "vct_subcatchments", None)
        if subcatchments_obj is None:
            return

        def plot(
            ax=None,
            column="VALUE",
            show_river=True,
            show_buffers=True,
            show_labels=True,
            fill_subcatchments=True,
            hide_largest=False,
            zoom_to_subcatchments=False,
            river_color="#1f78b4",
            buffer_edgecolor="#0b8043",
            buffer_linewidth=1.0,
            alpha=0.6,
            edgecolor="white",
            linewidth=0.5,
            title="Catchment mask + rivers + buffer subcatchments",
            **kwargs,
        ):
            from types import SimpleNamespace

            subcatchments_for_plot = subcatchments_obj
            if hide_largest and len(subcatchments_obj.geodata) > 1:
                gdf_plot = subcatchments_obj.geodata.copy()
                if "AREA_HA" in gdf_plot.columns:
                    areas = gdf_plot["AREA_HA"]
                else:
                    areas = gdf_plot.geometry.area / 10000.0
                gdf_plot = gdf_plot.loc[areas < areas.max()].copy()
                if not gdf_plot.empty:
                    subcatchments_for_plot = SimpleNamespace(geodata=gdf_plot)

            plot_column = column
            if not fill_subcatchments:
                plot_column = None
                kwargs.setdefault("facecolor", "none")
                kwargs.pop("cmap", None)
                kwargs.pop("categorical", None)
            elif (
                column is not None and column in subcatchments_for_plot.geodata.columns
            ):
                kwargs.setdefault("categorical", True)
                kwargs.setdefault("cmap", "tab20")

            overlay_obj = self._get_buffers_overlay_vector() if show_buffers else None
            overlay_kwargs = {
                "show_overlay": show_buffers,
                "show_labels": False,
                "id_column": None,
                "point_labels": False,
                "label_color": "black",
                "label_fontsize": 9,
                "label_weight": "bold",
                "facecolor": "none",
                "alpha": 1.0,
                "edgecolor": buffer_edgecolor,
                "linewidth": buffer_linewidth,
                "zorder": 3,
            }

            ax = self._plot_coupled_subcatchments(
                subcatchments_for_plot,
                ax=ax,
                column=plot_column,
                show_river=show_river,
                show_labels=show_labels,
                river_color=river_color,
                alpha=alpha,
                edgecolor=edgecolor,
                linewidth=linewidth,
                title=title,
                overlay_obj=overlay_obj,
                overlay_kwargs=overlay_kwargs,
                **kwargs,
            )

            if zoom_to_subcatchments and not subcatchments_for_plot.geodata.empty:
                xmin, ymin, xmax, ymax = subcatchments_for_plot.geodata.total_bounds
                width = xmax - xmin
                height = ymax - ymin
                margin_x = max(width * 0.2, float(self.resolution) * 10.0)
                margin_y = max(height * 0.2, float(self.resolution) * 10.0)
                ax.set_xlim(xmin - margin_x, xmax + margin_x)
                ax.set_ylim(ymin - margin_y, ymax + margin_y)

            return ax

        subcatchments_obj.plot = plot

    def _resolve_point_vector_target(self, target_input):
        """Resolve a target input to a point vector object and metadata."""
        parent_property_name = None
        if isinstance(target_input, str) and target_input.startswith("vct_"):
            if not hasattr(self, target_input):
                msg = f"Unknown vector property '{target_input}'."
                raise ValueError(msg)
            target_vector_obj = getattr(self, target_input)
            target_name = target_input
            parent_property_name = target_input
        elif hasattr(target_input, "geodata") and hasattr(target_input, "file_path"):
            target_vector_obj = target_input
            target_name = Path(target_vector_obj.file_path).stem
        else:
            target_vector_obj = self.vector_factory(
                Path(target_input),
                "Point",
                flag_clip=False,
            )
            self._ensure_vector_id_column(target_vector_obj)
            target_name = Path(target_input).stem

        gdf = target_vector_obj.geodata
        if gdf is None or gdf.empty:
            msg = "Point vector contains no features."
            raise ValueError(msg)

        if "geometry" not in gdf.columns:
            msg = "Point vector has no geometry column."
            raise ValueError(msg)

        geom_types = gdf.geometry.geom_type.dropna().unique().tolist()
        if any(gt not in ["Point", "MultiPoint"] for gt in geom_types):
            msg = "Target vector must contain only point geometries."
            raise ValueError(msg)

        return target_vector_obj, target_name, parent_property_name

    def _register_dummy_point_on_self(
        self,
        parent_property_name,
        point_id,
        vct_point,
    ):
        """Register a one-point dummy vector as a property on self."""
        parent_name = parent_property_name or "points"
        attr_name = f"vct_point_{parent_name}_{int(point_id)}"
        setattr(self, attr_name, vct_point)
        self._vct_point = vct_point
        self._vct_points_dummy[attr_name] = vct_point

    def _ensure_unique_priority_target_ids(self):
        """Ensure priority points have a unique integer ``target_id`` column."""
        points_obj = self.vct_priority_points
        gdf_points = points_obj.geodata.copy().reset_index(drop=True)

        gdf_points["target_id"] = np.arange(1, len(gdf_points) + 1, dtype=int)

        points_path = Path(points_obj.file_path)
        self._unlink_vector_dataset(points_path)
        gdf_points.to_file(points_path, spatial_index="YES")

        self.vct_priority_points = points_path

    def _aggregate_dummy_point_subcatchments(
        self,
        points_vector_obj,
        target_name,
        tag,
        point_vectors=None,
        output_dir=None,
    ):
        """Aggregate individual point subcatchments and attach to parent points."""
        if point_vectors is None:
            point_vectors = getattr(points_vector_obj, "vct_points_individual", [])

        if not point_vectors:
            msg = "No dummy point vectors available to aggregate subcatchments."
            raise ValueError(msg)

        subcatchment_gdfs = []
        for vct_point in point_vectors:
            if getattr(vct_point, "vct_subcatchments", None) is None:
                continue
            gdf_point_sub = vct_point.vct_subcatchments.geodata.copy()
            point_id = getattr(vct_point, "point_id", None)
            if point_id is None:
                point_id_column = self._infer_point_id_column(vct_point.geodata)
                point_id = int(vct_point.geodata.iloc[0][point_id_column])

            # Persist a stable coupling key between point and subcatchment.
            gdf_point_sub["target_id"] = int(point_id)
            gdf_point_sub["VALUE"] = int(point_id)
            subcatchment_gdfs.append(gdf_point_sub)

        if not subcatchment_gdfs:
            msg = "No subcatchments found on dummy point vectors to aggregate."
            raise ValueError(msg)

        gdf_subcatchments = gpd.GeoDataFrame(
            pd.concat(subcatchment_gdfs, ignore_index=True),
            geometry="geometry",
            crs=subcatchment_gdfs[0].crs,
        )

        # One target id can produce multiple polygon parts; dissolve by id so
        # each target appears only once in the coupled subcatchments vector.
        dissolve_column = "target_id"
        if dissolve_column in gdf_subcatchments.columns:
            gdf_subcatchments = gdf_subcatchments.dissolve(
                by=dissolve_column,
                as_index=False,
            )

        out_dir = output_dir or self.sfolder.postprocessing_folder
        vct_subcatchments = out_dir / f"{target_name}_{tag}.shp"
        self._unlink_vector_dataset(vct_subcatchments)
        gdf_subcatchments.to_file(vct_subcatchments, spatial_index="YES")

        points_vector_obj.vct_subcatchments = self.vector_factory(
            Path(vct_subcatchments),
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(points_vector_obj.vct_subcatchments)
        self._attach_subcatchments_plot(points_vector_obj)

        # Keep only the aggregated subcatchments output: remove per-point
        # individual subcatchment shapefiles created during delineation.
        for vct_point in point_vectors:
            sub_obj = getattr(vct_point, "vct_subcatchments", None)
            if sub_obj is None or not hasattr(sub_obj, "file_path"):
                continue
            self._unlink_vector_dataset(Path(sub_obj.file_path))
            vct_point.vct_subcatchments = None

        # Remove stale individual subcatchment outputs from previous runs,
        # while keeping the aggregated result.
        self._remove_individual_subcatchment_shapefiles(
            out_dir,
            keep_paths=[vct_subcatchments],
        )

        return vct_subcatchments

    def _attach_subcatchments_plot(self, points_vector_obj):
        """Attach a convenience plot() to the coupled subcatchments vector."""
        subcatchments_obj = getattr(points_vector_obj, "vct_subcatchments", None)
        if subcatchments_obj is None:
            return

        def plot(
            ax=None,
            column="VALUE",
            show_river=True,
            show_labels=True,
            river_color="#1f78b4",
            poi_color="red",
            poi_markersize=35,
            alpha=0.6,
            edgecolor="white",
            linewidth=0.5,
            title="Catchment mask + rivers + POI subcatchments",
            **kwargs,
        ):
            overlay_kwargs = {
                "show_overlay": True,
                "show_labels": False,
                "id_column": None,
                "point_labels": True,
                "label_color": "black",
                "label_fontsize": 9,
                "label_weight": "bold",
                "color": poi_color,
                "markersize": poi_markersize,
                "zorder": 3,
            }

            return self._plot_coupled_subcatchments(
                subcatchments_obj,
                ax=ax,
                column=column,
                show_river=show_river,
                show_labels=show_labels,
                river_color=river_color,
                alpha=alpha,
                edgecolor=edgecolor,
                linewidth=linewidth,
                title=title,
                overlay_obj=points_vector_obj,
                overlay_kwargs=overlay_kwargs,
                **kwargs,
            )

        subcatchments_obj.plot = plot

    def aggregate_subcatchments_for_points(
        self, target_input, tag="subcatchments_to_targets"
    ):
        """Aggregate already computed dummy-point subcatchments to parent points.

        This supports gradual workflows where points become available over time
        and their subcatchments are delineated one-by-one.
        """
        points_vector_obj, target_name, _ = self._resolve_point_vector_target(
            target_input
        )
        parent_property_name = (
            target_input
            if isinstance(target_input, str) and target_input.startswith("vct_")
            else None
        )
        output_dir = self._point_target_output_dir(parent_property_name)
        return self._aggregate_dummy_point_subcatchments(
            points_vector_obj,
            target_name,
            tag,
            output_dir=output_dir,
        )

    def _unlink_vector_dataset(self, vector_path):
        """Remove an existing vector dataset before re-writing it."""
        vector_path = Path(vector_path)
        if vector_path.suffix.lower() == ".shp":
            for suffix in [".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix"]:
                part = vector_path.with_suffix(suffix)
                if part.exists():
                    part.unlink()
        elif vector_path.exists():
            vector_path.unlink()

    def _remove_individual_subcatchment_shapefiles(self, folder, keep_paths=None):
        """Remove individual ``subcatchments_*.shp`` files in a folder."""
        folder = Path(folder)
        if not folder.exists():
            return

        keep_resolved = set()
        if keep_paths is not None:
            for keep in keep_paths:
                if keep is None:
                    continue
                try:
                    keep_resolved.add(Path(keep).resolve())
                except Exception:
                    continue

        for shp in folder.glob("subcatchments_*.shp"):
            shp_resolved = shp.resolve()
            if shp_resolved in keep_resolved:
                continue
            self._unlink_vector_dataset(shp)

    def _collect_notebook_vector_paths(self):
        """Collect active vector paths that are typically shown in notebooks."""
        postproc_root = self.sfolder.postprocessing_folder.resolve()

        def _as_path(vector_obj):
            if vector_obj is None or not hasattr(vector_obj, "file_path"):
                return None
            try:
                p = Path(vector_obj.file_path).resolve()
            except Exception:
                return None
            return p

        keep_paths = set()
        top_level_vectors = [
            self._vct_routing,
            self._vct_routing_missing,
            self._vct_sedi_export,
            self._vct_sewer_in,
            self._vct_sinks,
            self._vct_grass_strips,
            self._vct_poi,
            self._vct_buffers,
            self._vct_priority_points,
            self._vct_priority_subcatchments,
        ]

        for vector_obj in top_level_vectors:
            p = _as_path(vector_obj)
            if (
                p is not None
                and p.suffix.lower() == ".shp"
                and postproc_root in p.parents
            ):
                keep_paths.add(p)

            if vector_obj is not None and hasattr(vector_obj, "vct_subcatchments"):
                p_sub = _as_path(getattr(vector_obj, "vct_subcatchments", None))
                if (
                    p_sub is not None
                    and p_sub.suffix.lower() == ".shp"
                    and postproc_root in p_sub.parents
                ):
                    keep_paths.add(p_sub)

        return keep_paths

    def cleanup_postprocessing_shapefiles(self, dry_run=False, include_subfolders=True):
        """Keep only active notebook shapefiles in postprocessing folder.

        Parameters
        ----------
        dry_run: bool, default False
            If True, do not delete files; only report what would be removed.
        include_subfolders: bool, default True
            Also scan subfolders (e.g. temporary priority folders).

        Returns
        -------
        dict
            Summary with keys ``kept`` and ``removed``.
        """
        root = self.sfolder.postprocessing_folder
        keep_paths = self._collect_notebook_vector_paths()

        if include_subfolders:
            candidates = list(root.rglob("*.shp"))
        else:
            candidates = list(root.glob("*.shp"))

        removed = []
        kept = []
        for shp in candidates:
            shp_resolved = shp.resolve()
            if shp_resolved in keep_paths:
                kept.append(str(shp_resolved))
                continue

            removed.append(str(shp_resolved))
            if not dry_run:
                self._unlink_vector_dataset(shp_resolved)

        return {
            "kept": sorted(kept),
            "removed": sorted(removed),
        }

    def _auto_cleanup_postprocessing_shapefiles(self):
        """Run automatic postprocessing shapefile cleanup when enabled."""
        if not getattr(self, "auto_cleanup_postprocessing_shapefiles", False):
            return

        try:
            self.cleanup_postprocessing_shapefiles(
                dry_run=False,
                include_subfolders=True,
            )
        except Exception as exc:
            logger.warning(
                "Automatic postprocessing cleanup skipped due to error: %s",
                exc,
            )

    def _make_dummy_point_vector(
        self,
        points_vector_obj,
        point_index,
        id_column,
        tag,
        output_dir=None,
    ):
        """Create a one-point vector object used for single-point delineation."""
        gdf_point = points_vector_obj.geodata.iloc[[point_index]].copy()
        point_id = int(gdf_point.iloc[0][id_column])

        output_root = output_dir or self.sfolder.postprocessing_folder
        tempfolder = output_root / "point_targets"
        tempfolder.mkdir(parents=True, exist_ok=True)

        point_name = Path(points_vector_obj.file_path).stem
        point_path = tempfolder / f"{point_name}_{tag}_point_{point_id}.shp"
        self._unlink_vector_dataset(point_path)
        gdf_point.to_file(point_path, spatial_index="YES")

        vct_point = self.vector_factory(
            point_path,
            "Point",
            flag_clip=False,
        )
        self._ensure_vector_id_column(vct_point)
        vct_point.vct_subcatchments = None
        vct_point.point_id = point_id

        return vct_point

    def identify_subcatchment(
        self,
        target_input,
        id_column=None,
        tag="subcatchment_to_target",
        output_dir=None,
    ):
        """Identify one subcatchment draining to one point target.

        Parameters
        ----------
        target_input: str, pathlib.Path or vector object
            Point vector input that must contain exactly one point.
            A ``vct_*`` property name is supported as well.
        id_column: str, optional
            Field name in the point vector containing the target id.
        tag: str, default "subcatchment_to_target"
            Output tag used for naming intermediate and output files.

        Returns
        -------
        pathlib.Path
            Path to ``vct_subcatchments``.
        """
        routing_nonriver = self.routing_non_river.file_path
        if not routing_nonriver.exists():
            self.remove_river_routing()

        target_vector_obj, target_name, _ = self._resolve_point_vector_target(
            target_input
        )
        target_id_column = self._infer_point_id_column(
            target_vector_obj.geodata, id_column
        )

        if len(target_vector_obj.geodata) != 1:
            msg = (
                "'identify_subcatchment' expects exactly one point. "
                "Use 'identify_subcatchments' for point collections."
            )
            raise ValueError(msg)

        out_dir = output_dir or self.sfolder.postprocessing_folder

        arr_target_ids = target_vector_obj.rasterize(
            self.modelinput.compositelanduse.file_path,
            self.epsg,
            col=target_id_column,
            dtype_raster="integer",
            nodata=self.rstparams["nodata"],
            gdal=False,
        )
        rst_target_ids = out_dir / f"{target_name}_{tag}_ids.rst"
        write_arr_as_rst(
            arr_target_ids,
            rst_target_ids,
            np.int32,
            self.rstparams,
        )

        _, vct_subcatchments = identify_subcatchments_to_target_ids(
            rst_target_ids,
            routing_nonriver,
            out_dir,
            self.rp,
            tag=tag,
        )

        target_vector_obj.vct_subcatchments = self.vector_factory(
            Path(vct_subcatchments),
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(target_vector_obj.vct_subcatchments)
        self._attach_subcatchments_plot(target_vector_obj)

        return vct_subcatchments

    def identify_subcatchments(
        self,
        target_input,
        target_type="points",
        id_column=None,
        tag="subcatchments_to_targets",
    ):
        """Identify subcatchments draining to point targets.

        Parameters
        ----------
        target_input: str, pathlib.Path or vector object
            Point vector input. Preferred usage is a ``vct_*`` property name,
            for example ``"vct_poi"`` or ``"vct_priority_points"``.
        target_type: str, default "points"
            Legacy argument retained for compatibility. Only ``"points"`` is
            supported in this method.
        id_column: str, optional
            Field name in point vector used as subcatchment id.
        tag: str, default "subcatchments_to_targets"
            Base output tag.

        Returns
        -------
        pathlib.Path
            Path to ``vct_subcatchments``. For multi-point input this is the
            aggregated vector path.

        Notes
        -----
        This method is the multi-point orchestrator and creates a one-point
        dummy vector per input point. Each dummy point receives its own
        ``vct_subcatchments`` attribute. All individual
        subcatchments are then aggregated and attached to the input points
        vector object as ``vct_subcatchments``.
        """
        target_type_key = str(target_type).strip().lower()
        if target_type_key != "points":
            msg = (
                "'identify_subcatchments' now only supports point targets. "
                "Use 'identify_subcatchments_to_buffers' for buffer-based flow."
            )
            raise ValueError(msg)

        points_vector_obj, target_name, parent_property_name = (
            self._resolve_point_vector_target(target_input)
        )
        output_dir = self._point_target_output_dir(parent_property_name)
        target_id_column = self._infer_point_id_column(
            points_vector_obj.geodata, id_column
        )

        if len(points_vector_obj.geodata) == 1:
            return self.identify_subcatchment(
                points_vector_obj,
                id_column=target_id_column,
                tag=tag,
                output_dir=output_dir,
            )

        point_vectors = []

        for point_index in range(len(points_vector_obj.geodata)):
            vct_point = self._make_dummy_point_vector(
                points_vector_obj,
                point_index,
                target_id_column,
                tag,
                output_dir=output_dir,
            )
            point_id = int(vct_point.geodata.iloc[0][target_id_column])
            point_tag = f"{tag}_{point_id}"

            self.identify_subcatchment(
                vct_point,
                id_column=target_id_column,
                tag=point_tag,
                output_dir=output_dir,
            )

            self._register_dummy_point_on_self(
                parent_property_name,
                point_id,
                vct_point,
            )
            point_vectors.append(vct_point)

        points_vector_obj.vct_points_individual = point_vectors
        vct_subcatchments = self._aggregate_dummy_point_subcatchments(
            points_vector_obj,
            target_name,
            tag,
            point_vectors=point_vectors,
            output_dir=output_dir,
        )

        self._auto_cleanup_postprocessing_shapefiles()

        return vct_subcatchments

    def _select_priority_subcatchment_raster(self, source):
        """Return raster array used to identify priority subcatchments.

        Parameters
        ----------
        source: str
            One of "sedi_out", "sedi_export" or "sedi_export + sewer_in".

        Returns
        -------
        numpy.ndarray
            Raster array with nodata defined by the active raster profile.
        """
        source_key = source.replace(" ", "").lower()

        if source_key in ["sedi_out", "sediout"]:
            return self.modeloutput.sedi_out.arr.copy()

        if source_key in ["sedi_export", "sediexport"]:
            return self.modeloutput.sedi_export.arr.copy()

        if source_key in ["sedi_export+sewer_in", "sediexport+sewerin"]:
            nodata = self.rstparams["nodata"]

            try:
                arr_sedi_export = self.modeloutput.sedi_export.arr.astype(np.float64)
                arr_sewer_in = self.modeloutput.sewer_in.arr.astype(np.float64)
            except AttributeError as exc:
                msg = (
                    "Cannot use 'sedi_export + sewer_in': required model output "
                    "rasters are missing."
                )
                raise ValueError(msg) from exc

            if pd.isna(nodata):
                valid_sedi_export = ~np.isnan(arr_sedi_export)
                valid_sewer_in = ~np.isnan(arr_sewer_in)
            else:
                valid_sedi_export = arr_sedi_export != nodata
                valid_sewer_in = arr_sewer_in != nodata

            arr_priority = np.where(valid_sedi_export, arr_sedi_export, 0.0)
            arr_priority += np.where(valid_sewer_in, arr_sewer_in, 0.0)

            valid_any = valid_sedi_export | valid_sewer_in
            arr_priority = np.where(valid_any, arr_priority, nodata)

            return arr_priority

        msg = (
            "Unknown source for priority subcatchments. "
            "Use one of: 'sedi_out', 'sedi_export', 'sedi_export + sewer_in'."
        )
        raise ValueError(msg)

    def identify_priority_subcatchments(
        self,
        nmax=10,
        flag_merge=True,
        source="sedi_out",
        approach="n",
        threshold=50,
    ):
        """Identify priority subcatchments

        Parameters
        ----------
        nmax: int, default 10
            Maximum number of priority subcatchments for approach "n".
        flag_merge: bool, default True
            Merge the separate priority subcatchments to one shapefile.
        source: str, default "sedi_out"
            Raster source used to rank priority subcatchments. Supported values:
            "sedi_out", "sedi_export", "sedi_export + sewer_in".
        approach: str, default "n"
            Selection approach for priority subcatchments.

            - "n": select top ``nmax`` subcatchments.
            - "percentage": select subcatchments until cumulative selected load
              exceeds ``threshold`` (%).
        threshold: float, default 50
            Target cumulative percentage (0-100] of total source raster load
            for approach "percentage".

        Note
        ----
        Algorithm to identify priority subcatchments:

        1. Load source raster as an array
        2. Identify pixel with highest source value i.
        3. Identify subcatchment j coupled to this highest source value i.
        4. Set all source values within subcatchment j to no_value.
                5. Stop based on ``approach``:
                     - "n": stop after ``nmax`` subcatchments.
           - "percentage": stop once cumulative selected load exceeds
             ``threshold`` (%).

                Outputs
                -------
                - Priority points-of-interest (POI) in
                    ``<postprocessing>/priority_subcatchments/priority_points_of_interest.shp``.
                    The POI vector is exposed via ``self.vct_priority_points``.
                - Coupled priority subcatchments on
                    ``self.vct_priority_points.vct_subcatchments``.
        """
        # Generate temporary folder to write maps
        tempfolder = self._workflow_subdir("priority")
        if not tempfolder.exists():
            os.makedirs(tempfolder)

        arr_priority = self._select_priority_subcatchment_raster(source)

        priority_profile = dict(self.rstparams)
        transform = priority_profile["transform"]
        res = float(abs(transform.a))
        nrows = int(priority_profile["height"])
        ncols = int(priority_profile["width"])
        minx = float(transform.c)
        ymax = float(transform.f)
        xmax = minx + ncols * res
        miny = ymax - nrows * res
        priority_profile["res"] = res
        priority_profile["nrows"] = nrows
        priority_profile["ncols"] = ncols
        priority_profile["minmax"] = [minx, miny, xmax, ymax]
        priority_profile["epsg"] = int(self.epsg)

        approach_key = approach.replace(" ", "").lower()
        if approach_key not in ["n", "percentage"]:
            msg = "Unknown approach. Use one of: 'n', 'percentage'."
            raise ValueError(msg)

        nodata = priority_profile["nodata"]
        if pd.isna(nodata):
            valid_mask = ~np.isnan(arr_priority)
        else:
            valid_mask = arr_priority != nodata

        if not np.any(valid_mask):
            msg = "No valid source values found for identifying priority subcatchments."
            raise ValueError(msg)

        max_subcatchments = None
        threshold_percentage = None
        if approach_key == "n":
            if nmax is None or int(nmax) <= 0:
                msg = "For approach 'n', 'nmax' must be a positive integer."
                raise ValueError(msg)
            max_subcatchments = int(nmax)
        else:
            threshold_percentage = float(threshold)
            if threshold_percentage <= 0 or threshold_percentage > 100:
                msg = "For approach 'percentage', 'threshold' must be in (0, 100]."
                raise ValueError(msg)

        if approach_key == "n":
            target_n = int(max_subcatchments)
            valid_cell_count = int(np.count_nonzero(valid_mask))
            max_candidates = max(target_n, valid_cell_count)
            candidate_n = target_n
            last_retained_count = -1

            while True:
                self._clear_priority_subcatchment_workspace(tempfolder)

                # Delineate individual subcatchments with an expanded candidate
                # pool until enough retained priorities remain after applying
                # the enclosure replacement rule.
                gdf_subcatchmpriority, _, _, vct_priority_points = (
                    identify_individual_priority_subcatchments(
                        arr_priority.copy(),
                        priority_profile,
                        self.rstparams,
                        self.routing_non_river.file_path,
                        nmax=candidate_n,
                        threshold_percentage=None,
                        resmap=tempfolder,
                        epsg=self.epsg,
                    )
                )

                self.vct_priority_points = vct_priority_points
                self._ensure_unique_priority_target_ids()
                self.identify_subcatchments(
                    "vct_priority_points",
                    target_type="points",
                    id_column="target_id",
                    tag="priority_subcatchments",
                )
                self._vct_priority_subcatchments = (
                    self.vct_priority_points.vct_subcatchments
                )

                self._apply_priority_enclosure_filter()
                retained_count = len(self.vct_priority_points.geodata)

                if retained_count >= target_n:
                    self._limit_priority_pairs_to_n(target_n)
                    self._renumber_priority_pair_ids()
                    break

                if (
                    candidate_n >= max_candidates
                    and retained_count == last_retained_count
                ):
                    msg = (
                        f"Unable to retain {target_n} unique priority subcatchments "
                        "after evaluating all available candidates."
                    )
                    raise ValueError(msg)

                last_retained_count = retained_count
                candidate_n = min(max_candidates, candidate_n + target_n)

                if candidate_n >= max_candidates and retained_count < target_n:
                    # One final attempt with full candidate space is allowed;
                    # failure will be handled by the stagnation guard above.
                    continue
        else:
            search_threshold = float(threshold_percentage)

            while True:
                self._clear_priority_subcatchment_workspace(tempfolder)

                # Delineate subcatchments based on top values in the source raster.
                gdf_subcatchmpriority, _, _, vct_priority_points = (
                    identify_individual_priority_subcatchments(
                        arr_priority.copy(),
                        priority_profile,
                        self.rstparams,
                        self.routing_non_river.file_path,
                        nmax=None,
                        threshold_percentage=search_threshold,
                        resmap=tempfolder,
                        epsg=self.epsg,
                    )
                )

                self.vct_priority_points = vct_priority_points
                # Couple priority points to subcatchments via per-point dummy vectors.
                # This ensures each point has its own delineation, and all resulting
                # subcatchments are aggregated on the parent points vector object.
                self._ensure_unique_priority_target_ids()
                self.identify_subcatchments(
                    "vct_priority_points",
                    target_type="points",
                    id_column="target_id",
                    tag="priority_subcatchments",
                )
                self._vct_priority_subcatchments = (
                    self.vct_priority_points.vct_subcatchments
                )

                # For percentage-based selection we keep candidate order and
                # rely on overlap-safe cumulative accounting (no double
                # counting of raster cells) instead of enclosure replacement.
                self._annotate_priority_cumulative_contribution(
                    gdf_subcatchmpriority,
                    source=source,
                )
                keep_ids = self._limit_priority_pairs_to_percentage(
                    threshold_percentage
                )
                if keep_ids:
                    sub_id_col = self._infer_subcatchment_label_column(
                        gdf_subcatchmpriority,
                        preferred="VALUE",
                    )
                    if sub_id_col is not None:
                        gdf_sub_ids = pd.to_numeric(
                            gdf_subcatchmpriority[sub_id_col],
                            errors="coerce",
                        )
                        gdf_subcatchmpriority = gdf_subcatchmpriority.loc[
                            gdf_sub_ids.isin(keep_ids)
                        ].copy()
                self._renumber_priority_pair_ids()

                gdf_points_check = self.vct_priority_points.geodata.copy()
                cumperc_check = pd.to_numeric(
                    gdf_points_check.get("cumperc", pd.Series(dtype=float)),
                    errors="coerce",
                ).dropna()
                has_crossing = bool(np.any(cumperc_check > threshold_percentage))

                if has_crossing or search_threshold >= 100:
                    break

                search_threshold = min(100.0, search_threshold + 5.0)

        # merge overlapping subcatchments into joint subcatchments
        self.merge_overlapping_subcatchments(gdf_subcatchmpriority, merge=flag_merge)
        self._auto_cleanup_postprocessing_shapefiles()

    def _select_priority_source_column(self, gdf_points):
        """Return first available source-value column for priority points."""
        for candidate in ["source_value", "source_val"]:
            if candidate in gdf_points.columns:
                return candidate
        return None

    def _compute_overlap_safe_priority_contrib(
        self,
        gdf_points,
        gdf_sub,
        point_id_column,
        sub_id_column,
        source,
    ):
        """Compute overlap-safe cumulative contribution from source raster."""
        if source is None:
            return pd.Series(dtype=np.float64)

        source_col = self._select_priority_source_column(gdf_points)
        if source_col is None:
            return pd.Series(dtype=np.float64)

        arr_priority = self._select_priority_subcatchment_raster(source).astype(
            np.float64
        )
        nodata = self.rstparams["nodata"]
        if pd.isna(nodata):
            valid_mask = ~np.isnan(arr_priority)
        else:
            valid_mask = arr_priority != nodata

        total_source_load = float(arr_priority[valid_mask].sum())
        if total_source_load <= 0:
            return pd.Series(dtype=np.float64)

        gdf_rank = gdf_points.copy()
        gdf_rank["_id"] = pd.to_numeric(gdf_rank[point_id_column], errors="coerce")
        gdf_rank["_source"] = pd.to_numeric(gdf_rank[source_col], errors="coerce")
        gdf_rank = gdf_rank.dropna(subset=["_id", "_source"]).copy()
        if gdf_rank.empty:
            return pd.Series(dtype=np.float64)

        gdf_rank["_id"] = gdf_rank["_id"].astype(int)
        gdf_rank = gdf_rank.sort_values(["_source", "_id"], ascending=[False, True])

        gdf_sub_tmp = gdf_sub.copy()
        gdf_sub_tmp["_id"] = pd.to_numeric(gdf_sub_tmp[sub_id_column], errors="coerce")
        gdf_sub_tmp = gdf_sub_tmp.dropna(subset=["_id"]).copy()
        if gdf_sub_tmp.empty:
            return pd.Series(dtype=np.float64)

        gdf_sub_tmp["_id"] = gdf_sub_tmp["_id"].astype(int)
        gdf_sub_tmp = gdf_sub_tmp.drop_duplicates(subset=["_id"])
        geom_by_id = gdf_sub_tmp.set_index("_id")["geometry"].to_dict()

        from rasterio.features import rasterize as _rasterize

        covered_mask = np.zeros(arr_priority.shape, dtype=bool)
        cumulative_source_load = 0.0
        contrib = {}

        for _, row in gdf_rank.iterrows():
            target_id = int(row["_id"])
            geom = geom_by_id.get(target_id)
            if geom is None or geom.is_empty:
                continue

            sub_mask = _rasterize(
                [(geom, 1)],
                out_shape=arr_priority.shape,
                transform=self.rstparams["transform"],
                fill=0,
                dtype="uint8",
            ).astype(bool)

            new_cells = sub_mask & valid_mask & (~covered_mask)
            selected_source_load = float(arr_priority[new_cells].sum())
            cumulative_source_load += selected_source_load
            contrib[target_id] = 100.0 * cumulative_source_load / total_source_load
            covered_mask = covered_mask | sub_mask

        if not contrib:
            return pd.Series(dtype=np.float64)

        return pd.Series(contrib, dtype=np.float64)

    def _extract_priority_cumperc_from_subcatchments(self, gdf_subcatchmpriority):
        """Extract cumulative contribution from precomputed subcatchment metadata."""
        if gdf_subcatchmpriority is None or gdf_subcatchmpriority.empty:
            return pd.Series(dtype=np.float64)

        tmp = gdf_subcatchmpriority.copy()
        tmp_id_col = self._infer_subcatchment_label_column(tmp, preferred="VALUE")
        if tmp_id_col is None or "source_load_cumperc" not in tmp.columns:
            return pd.Series(dtype=np.float64)

        tmp["_id"] = pd.to_numeric(tmp[tmp_id_col], errors="coerce")
        tmp["_cum"] = pd.to_numeric(tmp["source_load_cumperc"], errors="coerce")
        tmp = tmp.dropna(subset=["_id", "_cum"])
        if tmp.empty:
            return pd.Series(dtype=np.float64)

        return tmp.groupby("_id")["_cum"].max()

    def _compute_priority_contrib_fallback(self, gdf_points, point_id_column):
        """Estimate cumulative contribution from point source values."""
        source_col = self._select_priority_source_column(gdf_points)
        if source_col is None:
            return pd.Series(dtype=np.float64)

        gdf_rank = gdf_points.copy()
        gdf_rank["_id"] = pd.to_numeric(gdf_rank[point_id_column], errors="coerce")
        gdf_rank["_source"] = pd.to_numeric(gdf_rank[source_col], errors="coerce")
        gdf_rank = gdf_rank.dropna(subset=["_id", "_source"]).copy()
        if gdf_rank.empty:
            return pd.Series(dtype=np.float64)

        gdf_rank = gdf_rank.sort_values(["_source", "_id"], ascending=[False, True])
        source_total = gdf_rank["_source"].sum()
        if source_total == 0:
            gdf_rank["cumperc"] = np.nan
        else:
            gdf_rank["cumperc"] = 100.0 * gdf_rank["_source"].cumsum() / source_total

        return gdf_rank.set_index("_id")["cumperc"]

    def _apply_priority_cumperc_to_vectors(
        self,
        points_obj,
        subcatchments_obj,
        gdf_points,
        gdf_sub,
        point_id_column,
        sub_id_column,
        contrib_by_id,
    ):
        """Persist mapped ``cumperc`` values to points and subcatchments layers."""
        gdf_points["_map_id"] = pd.to_numeric(
            gdf_points[point_id_column], errors="coerce"
        )
        gdf_sub["_map_id"] = pd.to_numeric(gdf_sub[sub_id_column], errors="coerce")

        gdf_points["cumperc"] = gdf_points["_map_id"].map(contrib_by_id)
        gdf_sub["cumperc"] = gdf_sub["_map_id"].map(contrib_by_id)

        gdf_points = gdf_points.drop(columns=["_map_id"])
        gdf_sub = gdf_sub.drop(columns=["_map_id"])

        points_path = Path(points_obj.file_path)
        subcatchments_path = Path(subcatchments_obj.file_path)

        self._unlink_vector_dataset(points_path)
        gdf_points.to_file(points_path, spatial_index="YES")

        self._unlink_vector_dataset(subcatchments_path)
        gdf_sub.to_file(subcatchments_path, spatial_index="YES")

        self.vct_priority_points = points_path
        self.vct_priority_points.vct_subcatchments = self.vector_factory(
            subcatchments_path,
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(self.vct_priority_points.vct_subcatchments)
        self._attach_subcatchments_plot(self.vct_priority_points)
        self._vct_priority_subcatchments = self.vct_priority_points.vct_subcatchments

    def _annotate_priority_cumulative_contribution(
        self, gdf_subcatchmpriority, source=None
    ):
        """Add cumulative contribution to priority geodata.

        This annotation is intended for the percentage-based priority workflow.
        A ``cumperc`` column is added to both priority points and coupled
        priority subcatchments. Values express cumulative selected source load
        percentage in descending priority order.
        """
        points_obj = self.vct_priority_points
        subcatchments_obj = getattr(points_obj, "vct_subcatchments", None)
        if subcatchments_obj is None:
            return

        gdf_points = points_obj.geodata.copy()
        gdf_sub = subcatchments_obj.geodata.copy()
        if gdf_points.empty or gdf_sub.empty:
            return

        point_id_column = self._infer_point_id_column(gdf_points)
        sub_id_column = self._infer_subcatchment_label_column(
            gdf_sub,
            preferred="target_id",
        )
        if sub_id_column is None:
            return

        contrib_by_id = self._compute_overlap_safe_priority_contrib(
            gdf_points,
            gdf_sub,
            point_id_column,
            sub_id_column,
            source,
        )

        if contrib_by_id.empty:
            contrib_by_id = self._extract_priority_cumperc_from_subcatchments(
                gdf_subcatchmpriority
            )

        if contrib_by_id.empty:
            contrib_by_id = self._compute_priority_contrib_fallback(
                gdf_points,
                point_id_column,
            )

        if contrib_by_id.empty:
            return

        self._apply_priority_cumperc_to_vectors(
            points_obj,
            subcatchments_obj,
            gdf_points,
            gdf_sub,
            point_id_column,
            sub_id_column,
            contrib_by_id,
        )

    def _clear_priority_subcatchment_workspace(self, tempfolder):
        """Remove temporary priority delineation files from previous runs."""
        tempfolder = Path(tempfolder)
        if not tempfolder.exists():
            return

        for path in tempfolder.iterdir():
            if path.is_file() and (
                path.stem.startswith("subcatchments_")
                or path.stem.startswith("id_")
                or path.stem.startswith("priority_subcatchments")
                or path.stem.startswith("priority_points_of_interest")
            ):
                path.unlink()

    def _limit_priority_pairs_to_n(self, nmax):
        """Trim priority points and coupled subcatchments to exactly ``nmax`` rows."""
        nmax = int(nmax)
        if nmax <= 0:
            return

        points_obj = self.vct_priority_points
        subcatchments_obj = getattr(points_obj, "vct_subcatchments", None)
        if subcatchments_obj is None:
            return

        gdf_points = points_obj.geodata.copy()
        gdf_sub = subcatchments_obj.geodata.copy()
        if gdf_points.empty or gdf_sub.empty:
            return

        point_id_column = self._infer_point_id_column(gdf_points)
        sub_id_column = self._infer_subcatchment_label_column(
            gdf_sub, preferred="target_id"
        )
        if sub_id_column is None:
            return

        source_col = None
        for candidate in ["source_value", "source_val"]:
            if candidate in gdf_points.columns:
                source_col = candidate
                break

        if source_col is not None:
            order_col = pd.to_numeric(gdf_points[source_col], errors="coerce").fillna(
                -np.inf
            )
            gdf_points = gdf_points.assign(_order_val=order_col).sort_values(
                "_order_val", ascending=False
            )
        else:
            gdf_points = gdf_points.copy()

        gdf_points = gdf_points.head(nmax).copy()
        keep_ids = (
            pd.to_numeric(gdf_points[point_id_column], errors="coerce")
            .dropna()
            .astype(int)
        )
        keep_ids_set = set(keep_ids.tolist())
        if not keep_ids_set:
            return

        sub_ids = pd.to_numeric(gdf_sub[sub_id_column], errors="coerce")
        gdf_sub = gdf_sub.loc[sub_ids.isin(keep_ids_set)].copy()

        gdf_points = gdf_points.drop(
            columns=[c for c in ["_order_val"] if c in gdf_points.columns]
        )

        points_path = Path(points_obj.file_path)
        subcatchments_path = Path(subcatchments_obj.file_path)

        self._unlink_vector_dataset(points_path)
        gdf_points.to_file(points_path, spatial_index="YES")

        self._unlink_vector_dataset(subcatchments_path)
        gdf_sub.to_file(subcatchments_path, spatial_index="YES")

        self.vct_priority_points = points_path
        self.vct_priority_points.vct_subcatchments = self.vector_factory(
            subcatchments_path,
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(self.vct_priority_points.vct_subcatchments)
        self._attach_subcatchments_plot(self.vct_priority_points)
        self._vct_priority_subcatchments = self.vct_priority_points.vct_subcatchments

    def _limit_priority_pairs_to_percentage(self, threshold_percentage):
        """Trim priority pairs up to and including first threshold crossing."""
        threshold_percentage = float(threshold_percentage)

        points_obj = self.vct_priority_points
        subcatchments_obj = getattr(points_obj, "vct_subcatchments", None)
        if subcatchments_obj is None:
            return set()

        gdf_points = points_obj.geodata.copy()
        gdf_sub = subcatchments_obj.geodata.copy()
        if gdf_points.empty or gdf_sub.empty:
            return set()

        point_id_column = self._infer_point_id_column(gdf_points)
        sub_id_column = self._infer_subcatchment_label_column(
            gdf_sub, preferred="target_id"
        )
        if sub_id_column is None or "cumperc" not in gdf_points.columns:
            return set()

        gdf_points = gdf_points.copy()
        gdf_points["_id"] = pd.to_numeric(gdf_points[point_id_column], errors="coerce")
        gdf_points["_cumperc"] = pd.to_numeric(gdf_points["cumperc"], errors="coerce")
        gdf_points = gdf_points.dropna(subset=["_id", "_cumperc"]).copy()
        if gdf_points.empty:
            return set()

        gdf_points = gdf_points.sort_values(
            ["_cumperc", "_id"], ascending=[True, True]
        ).copy()

        n_le = int((gdf_points["_cumperc"] <= threshold_percentage).sum())
        if n_le == 0:
            n_keep = 1
        elif n_le < len(gdf_points):
            n_keep = n_le + 1
        else:
            n_keep = n_le

        keep_ids = set(gdf_points.head(n_keep)["_id"].astype(int).tolist())

        gdf_points = gdf_points.loc[gdf_points["_id"].astype(int).isin(keep_ids)].copy()

        sub_ids = pd.to_numeric(gdf_sub[sub_id_column], errors="coerce")
        gdf_sub = gdf_sub.loc[sub_ids.isin(keep_ids)].copy()

        gdf_points = gdf_points.drop(
            columns=[c for c in ["_id", "_cumperc"] if c in gdf_points.columns]
        )

        points_path = Path(points_obj.file_path)
        subcatchments_path = Path(subcatchments_obj.file_path)

        self._unlink_vector_dataset(points_path)
        gdf_points.to_file(points_path, spatial_index="YES")

        self._unlink_vector_dataset(subcatchments_path)
        gdf_sub.to_file(subcatchments_path, spatial_index="YES")

        self.vct_priority_points = points_path
        self.vct_priority_points.vct_subcatchments = self.vector_factory(
            subcatchments_path,
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(self.vct_priority_points.vct_subcatchments)
        self._attach_subcatchments_plot(self.vct_priority_points)
        self._vct_priority_subcatchments = self.vct_priority_points.vct_subcatchments

        return keep_ids

    def _renumber_priority_pair_ids(self):
        """Renumber retained priority ids to a contiguous 1..N sequence."""
        points_obj = self.vct_priority_points
        subcatchments_obj = getattr(points_obj, "vct_subcatchments", None)
        if subcatchments_obj is None:
            return

        gdf_points = points_obj.geodata.copy()
        gdf_sub = subcatchments_obj.geodata.copy()
        if gdf_points.empty or gdf_sub.empty:
            return

        point_id_column = self._infer_point_id_column(gdf_points)
        sub_id_column = self._infer_subcatchment_label_column(
            gdf_sub, preferred="target_id"
        )
        if sub_id_column is None:
            return

        source_col = None
        for candidate in ["source_value", "source_val"]:
            if candidate in gdf_points.columns:
                source_col = candidate
                break

        gdf_points = gdf_points.copy()
        gdf_points["_old_id"] = pd.to_numeric(
            gdf_points[point_id_column], errors="coerce"
        )
        gdf_points = gdf_points.dropna(subset=["_old_id"]).copy()
        gdf_points["_old_id"] = gdf_points["_old_id"].astype(int)

        if source_col is not None:
            gdf_points["_order"] = pd.to_numeric(
                gdf_points[source_col], errors="coerce"
            ).fillna(-np.inf)
            gdf_points = gdf_points.sort_values(
                ["_order", "_old_id"], ascending=[False, True]
            )
        else:
            gdf_points = gdf_points.sort_values("_old_id", ascending=True)

        id_map = {
            old_id: new_id
            for new_id, old_id in enumerate(gdf_points["_old_id"].tolist(), start=1)
        }
        if not id_map:
            return

        gdf_points["target_id"] = gdf_points["_old_id"].map(id_map).astype(int)

        priority_col = None
        for candidate in ["priority_i", "priority_id"]:
            if candidate in gdf_points.columns:
                priority_col = candidate
                break
        if priority_col is None:
            priority_col = "priority_id"
        gdf_points[priority_col] = gdf_points["target_id"].astype(int)

        gdf_sub = gdf_sub.copy()
        sub_ids = pd.to_numeric(gdf_sub[sub_id_column], errors="coerce")
        gdf_sub = gdf_sub.loc[sub_ids.notna()].copy()
        gdf_sub["_old_id"] = pd.to_numeric(
            gdf_sub[sub_id_column], errors="coerce"
        ).astype(int)
        gdf_sub = gdf_sub.loc[gdf_sub["_old_id"].isin(set(id_map.keys()))].copy()

        gdf_sub["target_id"] = gdf_sub["_old_id"].map(id_map).astype(int)
        gdf_sub["VALUE"] = gdf_sub["target_id"].astype(int)

        gdf_points = gdf_points.drop(
            columns=[c for c in ["_old_id", "_order"] if c in gdf_points.columns]
        )
        gdf_sub = gdf_sub.drop(columns=[c for c in ["_old_id"] if c in gdf_sub.columns])

        points_path = Path(points_obj.file_path)
        subcatchments_path = Path(subcatchments_obj.file_path)

        self._unlink_vector_dataset(points_path)
        gdf_points.to_file(points_path, spatial_index="YES")

        self._unlink_vector_dataset(subcatchments_path)
        gdf_sub.to_file(subcatchments_path, spatial_index="YES")

        self.vct_priority_points = points_path
        self.vct_priority_points.vct_subcatchments = self.vector_factory(
            subcatchments_path,
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(self.vct_priority_points.vct_subcatchments)
        self._attach_subcatchments_plot(self.vct_priority_points)
        self._vct_priority_subcatchments = self.vct_priority_points.vct_subcatchments

    def _apply_priority_enclosure_filter(self):
        """Apply overlap-then-enclosure replacement on priority pairs.

        Iterate priority points in descending source value order. For each new
        subcatchment, first test explicit positive overlap with retained
        subcatchments. A new geometry is only accepted when it can replace all
        overlapping older geometries by (near-)enclosing them and not being
        smaller. Otherwise the new geometry is discarded to keep the retained
        set overlap-free.
        """
        points_obj = self.vct_priority_points
        subcatchments_obj = getattr(points_obj, "vct_subcatchments", None)
        if subcatchments_obj is None:
            return

        gdf_points = points_obj.geodata.copy()
        gdf_sub = subcatchments_obj.geodata.copy()
        if gdf_sub.empty or gdf_points.empty:
            return

        point_id_column = self._infer_point_id_column(gdf_points)
        sub_id_column = self._infer_subcatchment_label_column(
            gdf_sub,
            preferred="target_id",
        )
        if sub_id_column is None:
            return

        gdf_sub = gdf_sub.copy()
        gdf_sub["_sub_id"] = pd.to_numeric(gdf_sub[sub_id_column], errors="coerce")
        gdf_sub = gdf_sub.dropna(subset=["_sub_id"]).copy()
        gdf_sub["_sub_id"] = gdf_sub["_sub_id"].astype(int)
        gdf_sub = gdf_sub.drop_duplicates(subset=["_sub_id"]).copy()

        gdf_points = gdf_points.copy()
        gdf_points["_point_id"] = pd.to_numeric(
            gdf_points[point_id_column], errors="coerce"
        )
        gdf_points = gdf_points.dropna(subset=["_point_id"]).copy()
        gdf_points["_point_id"] = gdf_points["_point_id"].astype(int)

        source_col = None
        for candidate in ["source_value", "source_val"]:
            if candidate in gdf_points.columns:
                source_col = candidate
                break

        if source_col is not None:
            gdf_points["_order"] = pd.to_numeric(
                gdf_points[source_col], errors="coerce"
            ).fillna(-np.inf)
            gdf_points = gdf_points.sort_values("_order", ascending=False)
        else:
            gdf_points = gdf_points.sort_values("_point_id", ascending=True)

        sub_geom_by_id = {
            int(row["_sub_id"]): row.geometry for _, row in gdf_sub.iterrows()
        }

        retained_ids = []
        retained_geom = {}
        overlap_enclosure_tolerance = 0.995

        for _, point_row in gdf_points.iterrows():
            point_id = int(point_row["_point_id"])
            if point_id not in sub_geom_by_id:
                continue

            geom_new = sub_geom_by_id[point_id]
            if geom_new is None or geom_new.is_empty:
                continue

            enclosed_ids = []
            overlap_ids = []
            area_new = float(geom_new.area)
            for old_id in retained_ids:
                geom_old = retained_geom[old_id]
                if geom_old is None or geom_old.is_empty:
                    continue

                inter = geom_new.intersection(geom_old)
                overlap_area = float(inter.area) if not inter.is_empty else 0.0
                if overlap_area <= 0.0:
                    continue

                overlap_ids.append(old_id)

                # Explicit overlap found; only replace when old is enclosed
                # (or near-enclosed because of raster polygon slivers) and
                # the new geometry is not smaller.
                area_old = float(geom_old.area)
                min_area = min(area_new, area_old)
                overlap_ratio = (overlap_area / min_area) if min_area > 0 else 0.0
                old_enclosed = geom_new.covers(geom_old) or (
                    overlap_ratio >= overlap_enclosure_tolerance
                    and area_new >= area_old
                )

                if old_enclosed and area_new >= area_old:
                    enclosed_ids.append(old_id)

            # If there is overlap but the new geometry cannot replace every
            # overlapping old geometry, discard the new one.
            if overlap_ids and set(enclosed_ids) != set(overlap_ids):
                continue

            if enclosed_ids:
                retained_ids = [
                    old_id for old_id in retained_ids if old_id not in enclosed_ids
                ]
                for old_id in enclosed_ids:
                    retained_geom.pop(old_id, None)

            retained_ids.append(point_id)
            retained_geom[point_id] = geom_new

        kept_ids_set = set(retained_ids)
        if not kept_ids_set:
            return

        gdf_sub_kept = gdf_sub.loc[gdf_sub["_sub_id"].isin(kept_ids_set)].copy()
        point_ids = pd.to_numeric(gdf_points[point_id_column], errors="coerce")
        gdf_points_kept = gdf_points.loc[point_ids.isin(kept_ids_set)].copy()

        drop_cols = ["_point_id", "_order"]
        gdf_points_kept = gdf_points_kept.drop(
            columns=[c for c in drop_cols if c in gdf_points_kept.columns]
        )
        gdf_sub_kept = gdf_sub_kept.drop(
            columns=[c for c in ["_sub_id"] if c in gdf_sub_kept.columns]
        )

        points_path = Path(points_obj.file_path)
        subcatchments_path = Path(subcatchments_obj.file_path)

        self._unlink_vector_dataset(points_path)
        gdf_points_kept.to_file(points_path, spatial_index="YES")

        self._unlink_vector_dataset(subcatchments_path)
        gdf_sub_kept.to_file(subcatchments_path, spatial_index="YES")

        # Reload and re-couple vectors so in-memory objects reflect filtered files.
        self.vct_priority_points = points_path
        self.vct_priority_points.vct_subcatchments = self.vector_factory(
            subcatchments_path,
            "Polygon",
            flag_clip=False,
        )
        self._ensure_vector_id_column(self.vct_priority_points.vct_subcatchments)
        self._attach_subcatchments_plot(self.vct_priority_points)
        self._vct_priority_subcatchments = self.vct_priority_points.vct_subcatchments

    def merge_overlapping_subcatchments(self, gdf_subcatchmpriority, merge=True):
        """Merge overlapping subcatchments and reassign priorities for
        overlapping subcatchments.

        Parameters
        ----------
        gdf_subcatchmpriority: geopandas.GeoDataFrame
            Subcatchment shapes with number of subcatchment.
        merge: bool, default True
            Merge the separate priority subcatchment areas to one shapefile.
        """
        if not merge:
            return

        # fix formatting
        gdf_subcatchmpriority["VALUE"] = gdf_subcatchmpriority["VALUE"].astype(int)
        gdf_subcatchmpriority = gdf_subcatchmpriority.sort_values(
            "VALUE", ascending=True
        ).copy()
        source_crs = gdf_subcatchmpriority.crs

        # make a new dataframe with overlapping shapes together
        l_priorities = []
        l_polygons = []
        l_sedi_out_low = []
        l_sedi_out_high = []

        ind = 1

        while not gdf_subcatchmpriority.empty:

            first_geom = gdf_subcatchmpriority.geometry.iloc[0]

            # identify intersects
            gdf_subcatchmpriority["cond"] = [
                first_geom.intersects(geom) for geom in gdf_subcatchmpriority.geometry
            ]

            subset = gdf_subcatchmpriority.loc[gdf_subcatchmpriority["cond"]]

            # get union of these intersecting polygons and their priority id
            l_polygons.append(shapely.union_all(subset.geometry))
            l_sedi_out_low.append(subset["sedi_out"].min())
            l_sedi_out_high.append(subset["sedi_out"].max())
            l_priorities.append(ind)

            ind += 1

            # remove records from dataframe so no duplicates are analyzed
            gdf_subcatchmpriority = gdf_subcatchmpriority.loc[
                ~gdf_subcatchmpriority["cond"]
            ].copy()

        # generate new dataframe
        gpd_priorities = gpd.GeoDataFrame(
            {
                "priority": l_priorities,
                "sedi_out_min": l_sedi_out_low,
                "sedi_out_max": l_sedi_out_high,
                "geometry": l_polygons,
            },
            crs=source_crs,
        )

        gpd_priorities = gpd_priorities.to_crs(epsg=int(self.epsg))

        vct_out = (
            self.sfolder.postprocessing_folder / "priority_subcatchments_merged.shp"
        )
        gpd_priorities.to_file(vct_out, spatial_index="YES")

    def identify_export_parcel(self):
        """Identify total sediment leaving a parcel.

        Returns
        -------
        df_prckrt: geopandas.GeoDataFrame
            See
            :func:`pywatemsedem.postprocess.PostProcess.aggregate_sedout_parcel`

        """
        # couple sediment out to routing file
        valid_routing_sedi_out_vector(self)
        gdf_routing_sedi_out = gpd.read_file(self.vct_routing_sedi_out)
        gdf_routing_out_of_parcel = select_routing_out_of_parcel(gdf_routing_sedi_out)
        out_shp = self.sfolder.postprocessing_folder / "routing_out_of_parcel.shp"
        gdf_routing_out_of_parcel.to_file(out_shp, spatial_index="YES")
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
            prckrt added with sedi_out for every pixel defined per parcel
        """

        # load perceelskaart in dataframe format
        arr_prckrt, profile = load_raster(self.files["rst_prckrt"])
        df_prckrt = raster_array_to_pandas_dataframe(arr_prckrt, profile)

        for i in ["col", "row"]:
            df_prckrt[i] = df_prckrt[i].astype(np.float64)

        # aggregate sedi_out of routing to parcel scale
        gdf_routing = (
            gdf_routing.groupby(["lnduSource"])
            .aggregate({"sedi_out": np.sum})
            .reset_index()
        )
        # merge routing to 'perceelskaart'
        gdf_routing["lnduSource"] = gdf_routing["lnduSource"].astype(np.float64)
        df_prckrt = df_prckrt.merge(
            gdf_routing[["sedi_out", "lnduSource"]],
            left_on="val",
            right_on="lnduSource",
            how="left",
        )
        df_prckrt.loc[df_prckrt["sedi_out"].isnull(), "sedi_out"] = profile["nodata"]
        df_prckrt = df_prckrt.drop(["val"], axis=1)

        return df_prckrt

    def couple_sedi_out_routing(self, cols_out=None):
        """Couple sedi_out of raster map values to routing file.

        See :func:`pywatemsedem.postprocess.couple_sedi_out_routing`

        Returns
        -------
        gdf_routing_sedi_out: geopandas.GeoDataFrame
            See :func:`pywatemsedem.postprocess.couple_sedi_out_routing`
        """
        logger.info("Coupling amount of sediment to routing vectors...")
        valid_routing_vector(self)
        gdf_routing_sedi_out = couple_sedi_out_routing(
            self.vct_routing, self.files["rst_sedi_out"], self.epsg, cols_out
        )
        self.vct_routing_sedi_out = self.vct_routing.parent / Path(
            self.vct_routing.stem + "_sedi_out.shp"
        )
        gdf_routing_sedi_out.to_file(self.vct_routing_sedi_out, spatial_index="YES")

        return gdf_routing_sedi_out

    def intersect_sedi_outparcels_with_subcatchments(
        self, rst_subcatchment_sinks, df_sedi_out_parcel
    ):
        """Find the intersection between the subcatchments of the sinks and the
        parcels that lie within these subcatchments.

        The sedi_out_parcel map is used to identify the sediment exported out
        of a parcel.

        Parameters
        ----------
        rst_subcatchment_sinks: str or pathlib.Path
            File path of the subcatcmsinks raster
        df_sedi_out_parcel: pandas.DataFrame
            DataFrame of the sedi_out parcel map. This map holds
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
        # merge with sedi_out defined per parcel
        df_subcatchments = df_subcatchments.merge(
            df_sedi_out_parcel[["col", "row", "lnduSource"]],
            on=["col", "row"],
            how="left",
        )
        # get ids of parcels (lndSource, not equal to none, np.nan)
        cond = ~df_subcatchments["lnduSource"].isnull()
        unique_ids = df_subcatchments.loc[cond, "lnduSource"].unique()

        #  set pixels that have no parcel_id (lnduSource) wihtin the
        #  unique_ids list to nodata
        cond = df_sedi_out_parcel["lnduSource"].isin(unique_ids)
        df_sedi_out_parcel.loc[~cond, "SediOut"] = profile["nodata"]

        # write to disk
        self.sfolder.postprocessing_folder / "SedoutSinks.tif"
        profile["driver"] = "GTiff"

        arr_sedi_out = raster_dataframe_to_arr(
            df_sedi_out_parcel, profile, "SediOut", np.float32
        )

        write_arr_as_rst(
            arr_sedi_out,
            self.rst_sinks,
            "float32",
            profile,
        )

    def select_routing_to_outsidecatchment(self):
        """Exports all routing vectors to the outside of the catchment"""
        valid_routing_sedi_out_vector(self)

        logger.info("Determining routing out of the catchment...")

        vct_out = (
            self.sfolder.postprocessing_folder
            / f"routing_to_outside_{self.catchment_name}.shp"
        )
        if not vct_out.exists():
            gdf_routingsedi_out = gpd.read_file(self.vct_routingsedi_out)
            gdf_routingsedi_out = gdf_routingsedi_out[
                gdf_routingsedi_out["lnduTarg"] == 0
            ]
            gdf_routingsedi_out.to_file(vct_out, spatial_index="YES")

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
                self.files["rst_sedi_in"],
                self.files["rst_sedi_out"],
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
                    self.sfolder.postprocessing_folder,
                    tag="buffers",
                    plot=True,
                )
            if vct_out is None:
                vct_out = (
                    self.sfolder.postprocessing_folder / self.files["vct_buffers"].name
                )

            if cols:
                gdf_buffer = gdf_buffer[cols]
            gdf_buffer.to_file(vct_out, spatial_index="YES")

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
            fmap=self.sfolder.postprocessing_folder,
            flag_write=True,
            flag_join_vct_parcels=join,
        )

    def merge_sedi_out_and_cumulative(self, segments_to_retain=None):
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
        arr_sedi_out_nonriver, profile = load_raster(self.files["rst_sedi_out"])
        arr_sedi_out_nonriver = np.where(
            arr_sedi_out_nonriver != profile["nodata"], arr_sedi_out_nonriver, 0
        )

        arr_sedi_out_river, profile = load_raster(self.files["rst_cumulative"])
        if segments_to_retain is None:
            # take all river segments, i.e. everything not nodata
            arr_sedi_out_river = np.where(
                arr_sedi_out_river != profile["nodata"], arr_sedi_out_river, 0
            )
        else:
            # take only river segments in list
            arr_riversegm, _ = load_raster(self.files["rst_riviersegm"])
            mask = np.in1d(arr_riversegm, segments_to_retain).reshape(
                arr_riversegm.shape
            )
            arr_sedi_out_river = np.where(mask, arr_sedi_out_river, 0)
        arr_sedi_out_total = np.where(
            self.arr_bindomain == 1,
            arr_sedi_out_river + arr_sedi_out_nonriver,
            profile["nodata"],
        )
        rst_out = (
            self.sfolder.postprocessing_folder
            / f"SediOut_merged_{self.catchment_name}.tif"
        )
        write_arr_as_rst(arr_sedi_out_total, rst_out, "float32", self.rstparams)

    def convert_output_rsts_to_ton(self):
        """Convert the units for rasters sedi_out, sedi_in, sediexport and
        watereros from kg to ton.
        """
        rsts = [
            self.files["rst_sedi_out"],
            self.files["rst_sedi_in"],
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
            gdf_subcatchments.to_file(vct_subcatchments, spatial_index="YES")

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
                self.sfolder.postprocessing_folder
                / f"Sedimentexport2Segments_{self.catchment_name}_"
                f"s{self.scenario_label}.shp"
            )

            df_waterline.to_file(self.vct_riversegment, spatial_index="YES")
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
        gdf_subcatchments.to_file(vct_subcatchments, spatial_index="YES")

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

            Cnst = self.rp
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

                vct_out = self.sfolder.postprocessing_folder / vct_out
                gpd_bindomain.to_file(vct_out, spatial_index="YES")
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
            raise WSException(msg)
        except TypeError:
            msg = "check if scenario is defined correctly"
            logger.warning(msg)
            raise WSException(msg)

    def calculate_areas_prckrt(self):
        """Calculates the areas and relative areas of all landuse classes in
        the parcelmap
        """

        if self.files["rst_prckrt"] is None:
            self.set_prckrt_nodata()

        arr_prckrt, _ = load_raster(self.files["rst_prckrt"])

        res = self.rp["res"]
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
        f = self.sfolder.postprocessing_folder / (
            f"opp_perceelskaart_{self.year}_{self.catchment_name}_"
            f"s{self.scenario_label}.csv"
        )
        df.to_csv(f, sep=";")

    def make_facts(self):
        """Make a textfile with a number of stats about the simulation"""
        factsfile = self.sfolder.postprocessing_folder / (
            f"facts_{self.catchment_name}_s{self.scenario_label}.csv"
        )
        with open(factsfile, "w") as f:
            f.write(f";{self.catchment_name}\n")

            opp_catch = np.sum(
                self.arr_bindomain[self.arr_bindomain != self.rstparams["nodata"]]
            ) * (self.rp["res"] ** 2)
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
            Path(self.sfolder.postprocessing_folder)
            / f"endpoints_in_sewers_s{self.scenario_label}.rst"
        )
        rst_ditches = (
            Path(self.sfolder.postprocessing_folder)
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
        vct_out = self.sfolder.postprocessing_folder / Path(
            f"{vct.stem}_statistics.shp"
        )
        rst_erosion = create_erosion_raster(self.modeloutput.watereros_kg.file_path)
        rst_deposition = create_deposition_raster(
            self.modeloutput.watereros_kg.file_path
        )
        lst_rasters = [
            rst_erosion.absolute(),
            rst_deposition.absolute(),
            self.modeloutput.sedi_export.file_path.absolute(),
            # self.modeloutput.sewers_in.file_path.absolute(),
            # self.modeloutput.ditches_in.file_path.absolute(),
        ]
        lst_names = [
            "Erosion (kg)",
            "Deposition (kg)",
            "River (kg)",
            # "Sewers (kg)",
            # "Ditches (kg)",
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


def _unlink_vector_dataset_local(vector_path):
    """Remove an existing vector dataset before re-writing it."""
    vector_path = Path(vector_path)
    if vector_path.suffix.lower() == ".shp":
        for suffix in [".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix"]:
            part = vector_path.with_suffix(suffix)
            if part.exists():
                part.unlink()
    elif vector_path.exists():
        vector_path.unlink()


def _priority_valid_mask(arr_sedi_out, nodata):
    """Return mask of valid source cells for priority selection."""
    return ~np.isnan(arr_sedi_out) if pd.isna(nodata) else arr_sedi_out != nodata


def _validate_priority_selection_inputs(
    arr_sedi_out,
    nodata,
    nmax,
    threshold_percentage,
):
    """Validate selection arguments and return valid mask."""
    if nmax is None and threshold_percentage is None:
        msg = "Either 'nmax' or 'threshold_percentage' must be provided."
        raise ValueError(msg)

    if threshold_percentage is not None and (
        threshold_percentage <= 0 or threshold_percentage > 100
    ):
        msg = "'threshold_percentage' must be in (0, 100]."
        raise ValueError(msg)

    valid_mask = _priority_valid_mask(arr_sedi_out, nodata)
    if not np.any(valid_mask):
        msg = "No valid source values available to identify priority subcatchments."
        raise ValueError(msg)

    return valid_mask


def _create_poi_records(max_rows, max_cols, rst_profile, max_sedi_out, priority_id):
    """Create POI records for all max-source pixels."""
    minx, miny, _, _ = rst_profile["minmax"]
    res = rst_profile["res"]
    nrows = rst_profile["nrows"]

    records = []
    for row, col in zip(max_rows, max_cols):
        x_coord = minx + (col + 0.5) * res
        y_coord = miny + (nrows - row - 0.5) * res
        records.append(
            {
                "priority_id": priority_id,
                "source_value": max_sedi_out,
                "row": int(row) + 1,
                "col": int(col) + 1,
                "geometry": shapely.geometry.Point(float(x_coord), float(y_coord)),
            }
        )
    return records


def _resolve_or_create_priority_subcatchment(
    rst_id,
    txt_routing_non_river,
    resmap,
    rst_profile,
    tag,
    max_sedi_out,
):
    """Return raster/vector paths for a priority subcatchment and annotate sedi_out."""
    template_name = resmap / f"subcatchments_{tag}.shp"
    if template_name.exists():
        return template_name.with_suffix(".sdat"), template_name

    rst_subcatch, vct_subcatch = identify_subcatchments_to_target_ids(
        rst_id,
        txt_routing_non_river,
        resmap,
        rst_profile,
        tag=tag,
    )
    gdf = gpd.read_file(vct_subcatch)
    gdf["sedi_out"] = max_sedi_out
    gdf.to_file(vct_subcatch, spatial_index="YES")
    return rst_subcatch, vct_subcatch


def _selected_source_load(arr_sedi_out, arr_subcatch, nodata):
    """Compute selected source load and mask for a subcatchment raster."""
    subcatch_mask = arr_subcatch != -99999.0
    valid_mask = _priority_valid_mask(arr_sedi_out, nodata)
    valid_subcatch = subcatch_mask & valid_mask
    return arr_sedi_out[valid_subcatch].sum(), subcatch_mask


def _write_priority_load_attributes(
    vct_subcatch,
    selected_source_load,
    total_source_load,
    cumulative_source_load,
):
    """Write source-load columns to a priority subcatchment vector."""
    gdf = gpd.read_file(vct_subcatch)
    gdf["source_load"] = selected_source_load
    if total_source_load != 0:
        gdf["source_load_perc"] = 100 * selected_source_load / total_source_load
        gdf["source_load_cumperc"] = 100 * cumulative_source_load / total_source_load
    else:
        gdf["source_load_perc"] = np.nan
        gdf["source_load_cumperc"] = np.nan
    gdf.to_file(vct_subcatch, spatial_index="YES")


def _stop_priority_selection(
    index,
    nmax,
    threshold_percentage,
    cumulative_source_load,
    total_source_load,
):
    """Return True if one of the priority stopping criteria is reached."""
    return (nmax is not None and index >= nmax) or (
        threshold_percentage is not None
        and total_source_load != 0
        and (100 * cumulative_source_load / total_source_load) >= threshold_percentage
    )


def _merge_priority_subcatchments(resmap, epsg):
    """Merge all subcatchments_*.shp files into priority_subcatchments.shp."""
    lst_gdf = [
        gpd.read_file(vector_path)
        for vector_path in resmap.iterdir()
        if vector_path.suffix == ".shp"
        and vector_path.stem.startswith("subcatchments_")
    ]

    gdf_subcatchmpriority = pd.concat(lst_gdf)
    gdf_subcatchmpriority.crs = epsg
    dst = resmap / "priority_subcatchments.shp"
    gdf_subcatchmpriority.to_file(dst, spatial_index="YES")
    return gdf_subcatchmpriority, dst


def _cleanup_priority_subcatchment_shapefiles(resmap, dst, individual_paths):
    """Remove intermediate subcatchments_* vectors while preserving aggregate output."""
    for vct_subcatch in {Path(path) for path in individual_paths}:
        if vct_subcatch != dst:
            _unlink_vector_dataset_local(vct_subcatch)

    for shp in Path(resmap).glob("subcatchments_*.shp"):
        if shp.resolve() != dst.resolve():
            _unlink_vector_dataset_local(shp)


def identify_individual_priority_subcatchments(
    arr_sedi_out,
    rst_profile,
    rstparams,
    txt_routing_non_river,
    nmax=None,
    threshold_percentage=None,
    resmap=Path.cwd(),
    epsg="",
):
    """
    Identify the individual priority subcatchments and add them to rasters
    and vector outputs.

    Parameters
    ----------
    arr_sedi_out: numpy.ndarray
        numpy array format of sedout raster
    rst_profile: rasterio profile
        rasterio profile of the sedout raster
    rstparams: dict
        dictionary with raster parameters (e.g. nodata value)
    txt_routing_nonriver: str or pathlib.Path | str
        File path of the WaTEM/SEDEM routing table
    nmax: int, optional
        Maximum number of subcatchments to select. Required when
        ``threshold_percentage`` is None.
    threshold_percentage: float, optional
        Stop once cumulative selected source load exceeds this percentage of
        total valid source load. Must be in (0, 100].

    Returns
    -------
    subcatchmentpriority: geopandas.GeoDataFrame
        Subcatchment shapes with number of subcatchment.
    gdf_poi: geopandas.GeoDataFrame
        Priority points-of-interest (POI) used as subcatchment seeds.
    vct_priority_subcatchments: pathlib.Path
        File path of the exported priority subcatchments shapefile.
    vct_priority_points: pathlib.Path
        File path of the exported POI shapefile.
    """
    nodata = rst_profile["nodata"]
    total_source_load = arr_sedi_out[
        _validate_priority_selection_inputs(
            arr_sedi_out,
            nodata,
            nmax,
            threshold_percentage,
        )
    ].sum()
    cumulative_source_load = 0.0
    poi_records = []
    individual_subcatchment_paths = []

    priority_id = 1
    while True:
        rst_id, max_sedi_out, max_rows, max_cols = (
            create_id_raster_for_highest_value_arr(
                arr_sedi_out,
                1,
                rstparams,
                resmap=resmap,
            )
        )

        poi_records.extend(
            _create_poi_records(
                max_rows,
                max_cols,
                rst_profile,
                max_sedi_out,
                priority_id,
            )
        )

        rst_subcatch, vct_subcatch = _resolve_or_create_priority_subcatchment(
            rst_id,
            txt_routing_non_river,
            resmap,
            rst_profile,
            tag=priority_id,
            max_sedi_out=max_sedi_out,
        )
        individual_subcatchment_paths.append(Path(vct_subcatch))

        arr_subcatch, _ = load_raster(rst_subcatch)
        selected_source_load, subcatch_mask = _selected_source_load(
            arr_sedi_out,
            arr_subcatch,
            nodata,
        )
        cumulative_source_load += selected_source_load

        _write_priority_load_attributes(
            vct_subcatch,
            selected_source_load,
            total_source_load,
            cumulative_source_load,
        )

        if _stop_priority_selection(
            priority_id,
            nmax,
            threshold_percentage,
            cumulative_source_load,
            total_source_load,
        ):
            break

        arr_sedi_out[subcatch_mask] = nodata
        if not np.any(_priority_valid_mask(arr_sedi_out, nodata)):
            break

        priority_id += 1

    gdf_subcatchmpriority, dst = _merge_priority_subcatchments(resmap, epsg)

    gdf_poi = gpd.GeoDataFrame(poi_records, geometry="geometry", crs=epsg)
    vct_priority_points = resmap / "priority_points_of_interest.shp"
    gdf_poi.to_file(vct_priority_points, spatial_index="YES")

    _cleanup_priority_subcatchment_shapefiles(
        resmap,
        dst,
        individual_subcatchment_paths,
    )

    return gdf_subcatchmpriority, gdf_poi, dst, vct_priority_points


def create_id_raster_for_highest_value_arr(arr, id_, profile, resmap):
    """Create a raster with an id value assigned to the highest value in the raster"

    Parameters
    ----------
    arr: str or pathlib.Path | str
        with floats
    id_: int
        Sequential number of the subcatchment
    profile: rasterio profile
        Rasterio profile of the sedout raster
    resmap: str or pathlib.Path | str, optional
        Folder path to write results to

    Returns
    -------
    rst_id: str
        File path of the raster with id for highest value in raster.
    val: float
        Maximum value in raster.
    rows: numpy.ndarray
        Row indices of pixels equal to the maximum value.
    cols: numpy.ndarray
        Column indices of pixels equal to the maximum value.
    """
    resmap = Path(resmap)
    if not resmap.exists():
        (resmap).mkdir(parents=True, exist_ok=True)

    arr_id = arr.copy()
    nodata = profile["nodata"]
    if pd.isna(nodata):
        valid_mask = ~np.isnan(arr)
    else:
        valid_mask = arr != nodata

    if not np.any(valid_mask):
        msg = "No valid cells available to create a priority id raster."
        raise ValueError(msg)

    max_val = np.max(arr[valid_mask])
    cond = valid_mask & (arr == max_val)
    arr_id[cond] = id_
    arr_id[~cond] = profile["nodata"]
    rows, cols = np.where(cond)

    # write to disk
    rst_id = resmap / f"id_{id_}.rst"
    write_arr_as_rst(arr_id, rst_id, np.int32, profile)

    return rst_id, max_val, rows, cols


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
    Note that sewers in WaTEM/SEDEM are endpoints in pywatemsedem, such to make a
    distinction between sewers and ditches in pywatemsedem.
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
    txt_routing, rst_grass_strips, rst_prckrt, rst_sedi_out
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
        raster WaTEM/SEDEM perceelskaart
    rst_sedi_out: str or pathlib.Path
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
        - *sedi_in* (float): total incoming sediment in grass strip (kg)
        - *sedi_out* (float): total outgoing sediment out of grass strip (kg)
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

    arr_sedi_out, profile_sedi_out = load_raster(rst_sedi_out)
    df_sedi_out = raster_array_to_pandas_dataframe(arr_sedi_out, profile_sedi_out)
    df_routing = open_txt_routing_file(txt_routing)

    # filter grass strips that are actually modelled as grass strips in
    # pywatemsedem
    df_grass_strips = filter_grass_strips_with_prckrt(
        df_grass_strips, df_prckrt, profile
    )
    df_grass_strips["val"] = df_grass_strips["val"].astype(np.float64)

    # merge grass strips with sedi_out raster
    df_routing_grasid = merge_grass_strip_id_and_sedi_out_to_routing(
        df_grass_strips, df_sedi_out, df_routing
    )

    # format df_routing_grass to a list format
    df_routing_grass_T = reformat_routing_grass(df_routing_grasid)

    # aggregate per grass strip
    df_efficiency = aggregate_sedi_in_and_sedi_out_grass_strips(df_routing_grass_T)

    # compute counts
    arr_id, arr_npixels_t = np.unique(arr_grass_strips_id, return_counts=True)
    df_counts = pd.DataFrame()
    df_counts["gras_id_target"] = arr_id
    df_counts["npixels_t"] = arr_npixels_t
    df_efficiency = df_efficiency.merge(df_counts)
    sediment_load_grass_strips_in = np.sum(df_efficiency["sedi_in"])
    sediment_load_grass_strips_out = np.sum(df_efficiency["sedi_out"])

    return sediment_load_grass_strips_in, sediment_load_grass_strips_out, df_efficiency


def aggregate_sedi_in_and_sedi_out_grass_strips(df_routing_grass):
    """
    Compute the load in and out of a grass strips, so efficiencies can be
    computed.

    Parameters
    ----------
    df_routing_grass: pandas.DataFrame
        See :func:`pywatemsedem.process_output.open_txt_routing_file`:

        - *targetrow* (float): target row of pixel
        - *targetcol* (float) target column of pixel
        - *sedi_in* (float): incoming sediment pixel
        - *sedi_out* (float): outgoing sediment pixel
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
        - *sedi_in* (float): incoming sediment in grass strip
        - *sedi_out* (float): outgoing sediment out of grass strip
        - *eSTE* (float): estimated sediment trapping efficiency, see
          :func:`pywatemsedem.grasstrips.estimate_ste`
        - *sed* (float): amount of sedimentation

    Notes
    -----
    *gras_id_target* and *gras_id_source* are equal and refers to the gras_id (target).
    """

    condition = df_routing_grass["gras_id_source"] != df_routing_grass["gras_id_target"]
    df_sedi_out_grass = (
        df_routing_grass.loc[condition]
        .groupby("gras_id_source")
        .aggregate({"sedi_out": np.sum})
        .reset_index()
    )
    df_sedi_in_grass = (
        df_routing_grass.loc[condition]
        .groupby("gras_id_target")
        .aggregate({"sedi_out": np.sum})
        .reset_index()
    )
    df_sedi_in_grass = df_sedi_in_grass.rename(columns={"sedi_out": "sedi_in"})
    df_npixels = (
        df_routing_grass[["targetrow", "targetcol", "gras_id_target"]]
        .drop_duplicates()
        .groupby("gras_id_target")
        .size()
        .reset_index()
    )
    df_efficiency = df_sedi_in_grass[["gras_id_target", "sedi_in"]].merge(
        df_sedi_out_grass, left_on="gras_id_target", right_on="gras_id_source"
    )
    df_npixels.columns = ["gras_id_target", "npixels_r"]
    df_efficiency = df_efficiency.merge(df_npixels)
    df_efficiency["eSTE"] = estimate_ste(
        df_efficiency["sedi_in"], df_efficiency["sedi_out"]
    )
    df_efficiency["sed"] = df_efficiency["sedi_in"] - df_efficiency["sedi_out"]
    df_efficiency = df_efficiency[df_efficiency["gras_id_target"] != -9999]

    return df_efficiency


def merge_grass_strip_id_and_sedi_out_to_routing(
    df_grass_strips,
    df_sedi_out,
    df_routing,
):
    """Merge the id of the grass strips and the sedi_out (also pd list-format)
     to routing df.

    Filter grass strips which are not of landuse type -6 ('weide') with 'WaTEM/SEDEM
    perceelskaart'

    Parameters
    ----------
    df_grass_strips: pandas.DataFrame
        - *col* (int): col
        - *row* (int): row
        - *val* (int): gras_id

    df_sedi_out: pandas.DataFrame
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
        df_grass_strips[[f"target{target_id}row", f"target{target_id}col"]] = (
            df_grass_strips[["row", "col"]]
        )

    # define sedout and index cols to join on
    df_sedi_out["sedi_out"] = df_sedi_out["val"]
    df_sedi_out = df_sedi_out.set_index(["col", "row"])

    # join gras_id sources
    df_routing_grass_id = merge_grass_id_to_routing(
        df_routing, df_grass_strips, ["col", "row"], ["gras_id_source"]
    )

    # join sedi_out
    df_routing_grass_id = df_routing_grass_id.join(
        df_sedi_out[["sedi_out"]], how="left"
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
        - *sedi_out* (float): sediment output pixel

    """
    df_routing_grass["sedi_out1"] = (
        df_routing_grass["sedi_out"] * df_routing_grass["part1"]
    )
    df_routing_grass["sedi_out2"] = df_routing_grass["sedi_out"] * (
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
        f"sedi_out{target_id}": "sedi_out",
        f"gras_id_target{target_id}": "gras_id_target",
    }
    cond = df_routing_grass[f"part{target_id}"] != 0
    df_routing_grass = df_routing_grass.loc[
        cond, ["row", "col", "gras_id_source"] + list(cols.keys())
    ].rename(columns=cols)

    return df_routing_grass


def filter_grass_strips_with_prckrt(df_grass_strips, df_prckrt, profile_grass_strips):
    """
    Use the WaTEM/SEDEM 'perceelskaart' to filter grass strips (lay-over infr. and
    river cells over gras_buffer_id)

    Parameters
    ----------
    df_grass_strips: pandas.DataFrame
        see
        :func:`pywatemsedem.postprocess.merge_grass_strip_id_and_sedi_out_to_routing`
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
        :func:`pywatemsedem.postprocess.merge_grass_strip_id_and_sedi_out_to_routing`
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
        See :func:
        `pywatemsedem.postprocess.merge_grass_strip_id_and_sedi_out_to_routing`
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
        File path of the WaTEM/SEDEM modelinput perceelskaart, note that the
        parcels_ids are limited by int16 (for WaTEM/SEDEM Pascal)
    rst_watereros: string or pathlib.Path
        File path of the WaTEM/SEDEM modelouput watereros map
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
            gdf_prcln.to_file(vct_out, spatial_index="YES")

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


def identify_subcatchments_to_target_ids(
    rst_target_ids,
    txt_routing_nonriver,
    resmap,
    profile,
    tag="subcatchments_to_targets",
):
    """Identify subcatchments draining to positive target ids.

    Parameters
    ----------
    rst_target_ids: str or pathlib.Path
        File path of a raster holding positive target id values
        (e.g. buffers, sinks). Non-target cells must be nodata or <= 0.
    txt_routing_nonriver: str or pathlib.Path
        File path of the WaTEM/SEDEM routing table without river routing included
    resmap: str or pathlib.Path
        Folder path of results folder
    profile: rasterio.profiles
        See :func:`rasterio.open`.
    tag: str, default "subcatchments_to_targets"
        Tag used by :func:`define_subcatchments_saga` for output naming.

    Returns
    -------
    tuple
        ``(rst_subcatchments, vct_subcatchments)`` as returned by
        :func:`define_subcatchments_saga`.
    """
    rst_target_ids = Path(rst_target_ids)
    arr_target_ids, _ = load_raster(rst_target_ids)

    # Accept both legacy dict-like profiles and RasterProperties instances.
    if isinstance(profile, dict):
        gdal_profile = profile
    elif hasattr(profile, "gdal_profile"):
        gdal_profile = profile.gdal_profile
    else:
        msg = "'profile' must be a dict or provide a 'gdal_profile' attribute."
        raise TypeError(msg)

    nodata = gdal_profile["nodata"]

    cond_valid = arr_target_ids > 0
    if pd.isna(nodata):
        cond_valid = cond_valid & (~np.isnan(arr_target_ids))
    else:
        cond_valid = cond_valid & (arr_target_ids != nodata)

    target_ids = np.unique(arr_target_ids[cond_valid])
    if target_ids.size == 0:
        msg = f"No positive target ids found in raster '{rst_target_ids}'."
        raise ValueError(msg)

    mask = np.isin(arr_target_ids, target_ids)
    arr_targets = np.where(mask, arr_target_ids, nodata).astype(np.float32)

    rst_targets = resmap / (str(rst_target_ids.stem) + "_targets.rst")
    rstparams = rasterprofile_to_rstparams(gdal_profile)

    write_arr_as_rst(arr_targets, rst_targets, arr_targets.dtype, rstparams)

    return define_subcatchments_saga(
        rst_targets,
        txt_routing_nonriver,
        resmap,
        gdal_profile,
        tag=tag,
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


def couple_sedi_out_routing(vct_routing, rst_sedi_out, epsg, cols_out=None):
    """Couple the sedi_out raster values to the vector routing file

    Parameters
    ----------
    vct_routing: str or pathlib.Path
        File path of vector routing, see
        :func:`pywatemsedem.io.modeloutput.make_routing_vct`
    rst_sedi_out: str or pathlib.Path
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

        - *sedi_out* (float): Total Sediment output (scale:parcel) from pixel
        - *sedi_out1* (float): Sediment output coupled to arrow current pixel
        - *sedi_out2* (float): Sedimout output coupled to other output arrow current
          pixel
        - *cum_sum* (float): Cumulative sediment output based on sedi_out1
        - *cum_perc* (float): Cumulative percentage (%)
    """
    gdf_routing = gpd.read_file(vct_routing)

    # load sedOut
    arr_sedi_out, profile = load_raster(rst_sedi_out)
    df_sedi_out = raster_array_to_pandas_dataframe(arr_sedi_out, profile)
    df_sedi_out["sedi_out"] = df_sedi_out["val"].values

    # merge sedi_out to routing
    gdf_routing = gdf_routing.merge(
        df_sedi_out[["col", "row", "sedi_out"]], on=["col", "row"], how="left"
    )

    # (DR) sedi_out correction with part (%): sedi_out is total amount that goes out a
    # pixel (derived over two pixels).
    gdf_routing["sedi_out1"] = gdf_routing["sedi_out"] * gdf_routing["part"]
    gdf_routing["sedi_out2"] = gdf_routing["sedi_out"] * (1 - gdf_routing["part"])

    # (DR) Write cumulative percentage (descending)
    gdf_routing = gdf_routing.sort_values("sedi_out1", ascending=False)
    gdf_routing["cum_sum"] = gdf_routing["sedi_out1"].cumsum().astype(int)
    gdf_routing["cum_perc"] = (
        gdf_routing.cum_sum / gdf_routing["sedi_out1"].sum()
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
        Loaded routing vector file (with or without sedi_out coupled to it).
        See :func:`pywatemsedem.io.modeloutput.make_routing_vct`

    Returns
    -------
    gdf_routing: geopandas.GeoDataFrame
        Selected routing vector file (with or without sedi_out coupled to it).
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
    (i.e. rst_sewer_in, rst_sedi_export).

    Parameters
    ----------
    rst_in: str or pathlib.Path
        Input raster subject to convert to shape
    kind: str
        'sewer' or 'river'

    """
    if kind not in ["river", "sewer"]:
        raise KeyError(f"{kind} of sink not in known.")

    rst_in = Path(rst_in)
    basename = rst_in.stem
    _, profile = load_raster(rst_in)
    nodata = profile["nodata"]

    cmd_args = ["saga_cmd", SAGA_FLAGS, "shapes_grid", "3"]
    cmd_args += ["-GRIDS", str(rst_in)]
    cmd_args += ["-POINTS", str(vct_out)]
    execute_saga(cmd_args)

    gdf_out = gpd.read_file(vct_out)
    value_col = basename[:11]
    if pd.isna(nodata):
        cond_valid = (~gdf_out[value_col].isna()) & (gdf_out[value_col] != 0)
    else:
        cond_valid = (
            (gdf_out[value_col] != nodata)
            & (~gdf_out[value_col].isna())
            & (gdf_out[value_col] != 0)
        )
    gdf_out = gdf_out.loc[cond_valid].copy()

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
    gdf_out.drop(columns=["index"], inplace=True)
    gdf_out.to_file(vct_out, spatial_index="YES")


def compute_statistics_sedi_out_outside_domain(
    arr_sedi_out, arr_id, df_routing, profile
):
    """Compute amount of sedi_out routing outside domain.

    Parameters
    ----------
    arr_sedi_out: numpy.ndarray
        WaTEM/SEDEM sedi_out raster.
    arr_id: numpy.ndarray
        An unique array id array, sedi_out outside domain is grouped by these id's.
        Should be integers or floats!
    df_routing: pandas.DataFrame
        Loaded WaTEM/SEDEM routing dataframe
    profile: rasterio.profile

    Returns
    -------
    pandas.Series
        Series holding sedi_out outside domain per id.
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
    df_sedi_out = raster_array_to_pandas_dataframe(arr_sedi_out, profile)
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
    df_routing = df_routing.merge(df_sedi_out, on=["col", "row"], how="left")
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
    """Read the pywatemsedem filestructure flanders file containing an overview of the
    files used for pywatemsedem flanders.

    The filestructure contains information on files written on disk by pywatemsedem.
    This file is used by the :class:`pywatemsedem.core.postprocess.PostProcess` object
    and :class:`pywatemsedem.core.merge_scenarios.SpatialMergeScenarios`.

    The filestructure pywatemsedem file can be used for to regenerate the filenames
    in a ``scenario_x`` folder without having to have the pywatemsedem objects loaded in
    memory (i.e. handy for starting a PostProcess instance from any simulation).

    Parameters
    ----------
    txt_filestructure : str or pathlib.Path, default None
        File path of table holding all data files/folder path references used in
        pywatemsedem flanders.
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
    1. When no text data set file is defined, than the default defined in this package
       is used.
    2. Although the filestructure applies to pywatemsedem flanders, it is defined in the
       pywatemsedem postprocess.py core function, as the postprocess.py script contains
       many functionalities only coupled to flanders.

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
        ds = package_resource(["data"], "postprocess_files.csv")
    else:
        ds = txt_filestructure

    df_filestructure_flanders = pd.read_csv(ds, sep=sep)

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
