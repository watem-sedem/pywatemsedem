# seperate plotting funcion
import warnings
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

# hvplot functionalities
from matplotlib import colors
from shapely.geometry import LineString

from pywatemsedem.geo.factory import Factory
from pywatemsedem.geo.utils import (
    check_raster_properties_raster_with_template,
    clean_up_tempfiles,
    create_filename,
    create_spatial_index,
    execute_saga,
    get_rstparams,
    load_raster,
    mask_array_with_val,
    raster_array_to_pandas_dataframe,
    raster_dataframe_to_arr,
    raster_to_polygon,
    rst_to_vct_points,
    write_arr_as_rst,
)
from pywatemsedem.io.ini import get_item_from_ini
from pywatemsedem.io.plots import (
    axes_creator,
    log_scale_enabler,
    plot_continuous_raster,
    plot_cumulative_sedimentload,
    plot_output_raster,
)
from pywatemsedem.io.valid import valid_array_type, valid_boundaries, valid_non_nan

IMPLEMENTED_RASTER_TYPES = [np.int16, np.int32, np.int64, np.float32, np.float64]
COLORMAP = "cividis"
COLORMAP_SEDI_OUT = colors.LinearSegmentedColormap.from_list(
    "sedi_outcmap", ["#ffffff", "#fecc5c", "#ff8c00", "#d7191c", "#bd0026"]
)
COLORMAP_WATEREROS = colors.LinearSegmentedColormap.from_list(
    "watereroscmap", ["#bd0026", "#ff8c00", "#ffffff", "#4292c6", "#08306b"]
)


@dataclass
class Modeloutput(Factory):
    def __init__(self, ini, resolution, epsg, nodata):
        """Initialize model outputs and validation for a WaTEM/SEDEM setup.

        Parameters
        ----------
        ini: pathlib.Path
            ini file
        resolution: int
            See :class:`pywatemsedem.geo.RasterProperties`
        epsg: int
            See :class:`pywatemsedem.geo.RasterProperties`.
        nodata: int
            See :class:`pywatemsedem.geo.RasterProperties`.
        """

        # arguments
        self.resolution = resolution
        self.epsg = epsg
        self.nodata = nodata

        # inifile and modeloutput folder
        self.ini = ini
        self.rstparams, self.rp = get_rstparams(self.ini, epsg=self.epsg)
        self.modelinputfolder = Path(
            get_item_from_ini(ini, "Working directories", "input directory", str)
        )
        self.modeloutputfolder = Path(
            get_item_from_ini(ini, "Working directories", "output directory", str)
        )

        # apply factory and set mask
        super().__init__(resolution, epsg, nodata, self.modeloutputfolder)
        self.mask = self.modelinputfolder / get_item_from_ini(
            ini, "Files", "shapefile catchment", str
        )

        # DATA
        self._aspect = None
        self._routing = None
        self._routing_missing = None
        self._ls = None
        self._slope = None
        self._uparea = None
        self._total_sediment = None
        self._total_sediment_segments = None
        self._cumulative_sediment_segments = None
        self._sewer_in = None
        self._sedi_export = None
        self._sedi_in = None
        self._sedi_out = None
        self._sedtil_in = None
        self._sedtil_out = None
        self._cumulative = None
        self._watereros_kg = None
        self._watereros_mm = None
        self._tileros_kg = None
        self._tileros_mm = None
        self._capacity = None
        self._rusle = None
        self._sinks = None

    @property
    def aspect(self):
        """Return the aspect raster.

        For documentation, see :ref:`here <watemsedem:aspectmap>`
        """
        if self._aspect is None:
            self.aspect = self.modeloutputfolder / "AspectMap.rst"
        return self._aspect

    @aspect.setter
    def aspect(self, raster):
        """Set the aspect raster.

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._aspect = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.aspect.arr, required_type=np.float32)
        valid_boundaries(self.aspect.arr, lower=0, upper=2 * np.pi)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "Aspect [rad]"

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot the aspect raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            arr = mask_array_with_val(self.aspect.arr, self.mask.arr, self.nodata)
            ticks = [0, np.pi / 2, np.pi, 3 / 2 * np.pi, 2 * np.pi]
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")
            return fig, ax

        self._aspect.plot = plot
        self._aspect.file_path = raster

    @property
    def routing(self):
        """Return the routing table.

        For documentation, see :ref:`here <watemsedem:routingtxt>`
        """
        if self._routing is None:
            self.routing = self.modeloutputfolder / "routing.txt"
        return self._routing

    @routing.setter
    def routing(self, text):
        """Set the routing table.

        Parameters
        ----------
        text: pathlib.Path | str
        """

        self._routing = pd.read_table(text)
        self._txt_routing = text
        self.gdf_routing = None
        # checks
        valid_boundaries(self.routing["col"].values, lower=0, upper=self.rp.ncols)
        valid_boundaries(self.routing["row"].values, lower=0, upper=self.rp.nrows)

        arr_target1col = self.routing.loc[
            self.routing["target1col"] != -99, "target1col"
        ].values
        valid_boundaries(arr_target1col, lower=0, upper=self.rp.ncols)
        arr_target1row = self.routing.loc[
            self.routing["target1row"] != -99, "target1row"
        ].values
        valid_boundaries(arr_target1row, lower=0, upper=self.rp.nrows)
        valid_boundaries(self.routing["part1"].values, lower=0, upper=1)
        valid_boundaries(self.routing["distance1"], lower=0)

        arr_target2col = self.routing.loc[
            self.routing["target2col"] != -99, "target2col"
        ].values
        valid_boundaries(arr_target2col, lower=0, upper=self.rp.ncols)
        arr_target2row = self.routing.loc[
            self.routing["target2row"] != -99, "target2row"
        ].values
        valid_boundaries(arr_target2row, lower=0, upper=self.rp.nrows)
        valid_boundaries(self.routing["part2"].values, lower=0, upper=1)
        valid_boundaries(self.routing["distance2"].values, lower=0)

        def plot():
            """Plot the routing table interactively.

            Returns
            --------
            folium.folium.Map
            """
            if self.gdf_routing is None:
                msg = "Apply .make_routing_vector(...) on"
                msg1 = " Modeloutput before calling .plot()"
                raise IOError(msg + msg1)
            else:
                return self.gdf_routing.explore()
            # Future implementation: try to draw arrow in correct direction

        self._routing.plot = plot
        self._routing.file_path = text

    @property
    def routing_missing(self):
        """Return the routing_missing table.

        For documentation, see :ref:`here <watemsedem:missingroutingtxt>`
        """
        if self._routing_missing is None:
            self.routing_missing = self.modeloutputfolder / "routing_missing.txt"
        return self._routing_missing

    @routing_missing.setter
    def routing_missing(self, text):
        """Set the routing_missing table.

        Parameters
        ---------
        text: pathlib.Path | str
        """
        self._routing_missing = pd.read_table(text)
        self._txt_routing_missing = text
        self.gdf_routing_missing = None

        if self.routing_missing.empty:
            warnings.warn("routing_missing is empty")
        else:
            # checks like routing
            valid_boundaries(
                self.routing_missing["col"].values, lower=0, upper=self.rp.ncols
            )
            valid_boundaries(
                self.routing_missing["row"].values, lower=0, upper=self.rp.nrows
            )

            arr_target1col = self.routing_missing.loc[
                self.routing["target1col"] != -99, "target1col"
            ].values
            valid_boundaries(arr_target1col, lower=0, upper=self.rp.ncols)
            arr_target1row = self.routing_missing.loc[
                self.routing["target1row"] != -99, "target1row"
            ].values
            valid_boundaries(arr_target1row, lower=0, upper=self.rp.nrows)
            valid_boundaries(self.routing_missing["part1"].values, lower=0, upper=1)
            valid_boundaries(self.routing_missing["distance1"], lower=0)

            arr_target2col = self.routing_missing.loc[
                self.routing["target2col"] != -99, "target2col"
            ].values
            valid_boundaries(arr_target2col, lower=0, upper=self.rp.ncols)
            arr_target2row = self.routing_missing.loc[
                self.routing["target2row"] != -99, "target2row"
            ].values
            valid_boundaries(arr_target2row, lower=0, upper=self.rp.nrows)
            valid_boundaries(self.routing_missing["part2"].values, lower=0, upper=1)
            valid_boundaries(self.routing_missing["distance2"].values, lower=0)

        def plot():
            """Plot the routing_missing table interactively.

            Returns
            --------
            folium.folium.Map
            """
            if self.routing_missing.empty:
                warnings.warn("routing_missing is empty, no plot is generated")
            else:
                if self.gdf_routing_missing is None:
                    msg = (
                        "Apply .make_routing_vector(...,routing_missing = True) on"
                        " Modeloutput before calling .plot()"
                    )
                    raise IOError(msg)
                else:
                    return self.gdf_routing_missing.explore()

        self._routing_missing.plot = plot
        self._routing_missing.file_path = text

    @property
    def ls(self):
        """Return the LS raster.

        For documentation, see :ref:`here <watemsedem:lsmap>`
        """
        if self._ls is None:
            self.ls = self.modeloutputfolder / "LS.rst"
        return self._ls

    @ls.setter
    def ls(self, raster):
        """Set the LS raster.

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._ls = self.raster_factory(raster, flag_mask=False)

        segments = self.raster_factory(
            self.modelinputfolder
            / get_item_from_ini(self.ini, "Files", "river segment filename", str),
            flag_mask=True,
        )

        valid_array_type(self.ls.arr, required_type=np.float32)
        valid_boundaries(
            self.ls.arr[(self.mask.arr != self.nodata) & (segments.arr < 1)],
            lower=0,
            upper=None,
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "LS [-]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the LS raster with a non-linear colormap.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            arr = mask_array_with_val(self.ls.arr, self.ls.arr, self.nodata)
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")
            return fig, ax

        self._ls.plot = plot
        self._ls.file_path = raster

    @property
    def slope(self):
        """Return the slope raster.

        For documentation, see :ref:`here <watemsedem:slopemap>`
        """
        if self._slope is None:
            self.slope = self.modeloutputfolder / "SLOPE.rst"
        return self._slope

    @slope.setter
    def slope(self, raster):
        """Set the slope raster.

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._slope = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.slope.arr, required_type=np.float32)
        valid_boundaries(
            self.slope.arr[self.mask.arr != self.nodata], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "Slope [rad]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the slope raster with a non-linear colormap.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile of the data

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            arr = mask_array_with_val(self.slope.arr, self.slope.arr, self.nodata)
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")
            return fig, ax

        self._slope.plot = plot
        self._slope.file_path = raster

    @property
    def uparea(self):
        """Return the uparea raster.

        For documentation, see :ref:`here <watemsedem:upareamap>`
        """
        if self._uparea is None:
            self.uparea = self.modeloutputfolder / "UPAREA.rst"
        return self._uparea

    @uparea.setter
    def uparea(self, raster):
        """Set the uparea raster.

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._uparea = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.uparea.arr, required_type=np.float32)
        valid_boundaries(
            self.uparea.arr[self.mask.arr != self.nodata], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "uparea [m²]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the uparea raster with a non-linear colormap.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            # masks out river based on ls
            if not self.ls:
                msg = "Assign ls to Modeloutput before plotting uparea"
                raise NotImplementedError(msg)
            else:
                arr = mask_array_with_val(self.uparea.arr, self.ls.arr, self.nodata)
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")
            return fig, ax

        self._uparea.plot = plot
        self._uparea.file_path = raster

    @property
    def total_sediment(self):
        """Return the total_sediment table.

        For documentation, see :ref:`here <watemsedem:totalsedimenttxt>`.
        For explanation on column variables of dataframe: see
        :func:`pywatemsedem.io.modeloutput.load_total_sediment_file`.
        """
        if self._total_sediment is None:
            self.total_sediment = self.modeloutputfolder / "Total sediment.txt"
        return self._total_sediment

    @total_sediment.setter
    def total_sediment(self, text):
        """Set the total_sediment table.

        Parameters
        ----------
        text: pathlib.Path | str
        """
        dict = load_total_sediment_file(text)
        self._total_sediment = pd.DataFrame(dict, index=[0])
        self._total_sediment.file_path = text

    @property
    def total_sediment_segments(self):
        """Return the total_sediment_segments table.

        For documentation, see :ref:`here <watemsedem:totalsedimentsegmentstxt>`.
        For explanation on column variables of dataframe: see
        :func:`pywatemsedem.io.modeloutput.load_total_sediment_segments_file`.
        """
        if self._total_sediment_segments is None:
            self.total_sediment_segments = (
                self.modeloutputfolder / "Total sediment segments.txt"
            )
        return self._total_sediment_segments

    @total_sediment_segments.setter
    def total_sediment_segments(self, text):
        """Set the total_sediment_segments table.

        Parameters
        ----------
        text: pathlib.Path | str
        """
        df_total_sediment_segments = load_sediment_segments_file(text)
        self._total_sediment_segments = df_total_sediment_segments
        self._total_sediment_segments.file_path = text

        segment_ids = df_total_sediment_segments.index.values
        sediment_values = df_total_sediment_segments["Sediment"].values
        valid_non_nan(segment_ids)
        valid_non_nan(sediment_values)
        valid_array_type(segment_ids, required_type=np.int64)
        valid_array_type(sediment_values, required_type=np.float64)
        valid_boundaries(segment_ids, lower=1, upper=None)
        valid_boundaries(sediment_values, lower=0, upper=None)

    @property
    def cumulative_sediment_segments(self):
        """Return the cumulative_sediment_segments table.

        For documentation, see :ref:`here <watemsedem:cumulativesedimentsegmentstxt>`.
        For explanation on column variables of dataframe: see
        :func:`pywatemsedem.io.modeloutput.load_cumulative_sediment_segments_file`.
        """
        if self._cumulative_sediment_segments is None:
            self.cumulative_sediment_segments = (
                self.modeloutputfolder / "Cumulative sediment segments.txt"
            )
        return self._cumulative_sediment_segments

    @cumulative_sediment_segments.setter
    def cumulative_sediment_segments(self, text):
        """Set the cumulative_sediment_segments table.

        Parameters
        ----------
        text: pathlib.Path | str
        """
        df_cumulative_sediment_segments = load_sediment_segments_file(text)
        self._cumulative_sediment_segments = df_cumulative_sediment_segments
        self._cumulative_sediment_segments.file_path = text

        segment_ids = df_cumulative_sediment_segments.index.values
        sediment_values = df_cumulative_sediment_segments["Sediment"].values
        valid_non_nan(segment_ids)
        valid_non_nan(sediment_values)
        valid_array_type(segment_ids, required_type=np.int64)
        valid_array_type(sediment_values, required_type=np.float64)
        valid_boundaries(segment_ids, lower=1, upper=None)
        valid_boundaries(sediment_values, lower=0, upper=None)

    @property
    def sewer_in(self):
        """Return the sewer_in raster.

        For documentation, see :ref:`here <watemsedem:sewerinrst>`
        """
        if self._sewer_in is None:
            self.sewer_in = self.modeloutputfolder / "sewer_in.rst"
        return self._sewer_in

    @sewer_in.setter
    def sewer_in(self, raster):
        """Set the sewer_in raster.

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._sewer_in = self.raster_factory(raster, flag_mask=True)

        valid_array_type(self.sewer_in.arr, required_type=np.float32)
        valid_boundaries(
            self.sewer_in.arr[self.mask.arr != self.nodata],
            lower=0,
            upper=None,
            tolerance=0.001,
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "sewer in [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the sewer_in raster with a non-linear colormap.

            Zeros are filtered out.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile of
                    the data excluding zero values

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            arr = mask_array_with_val(self.sewer_in.arr, self.sewer_in.arr, self.nodata)
            arr = mask_array_with_val(arr, self.sewer_in.arr, 0)
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                cmap=COLORMAP_SEDI_OUT,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")
            return fig, ax

        self._sewer_in.plot = plot
        self._sewer_in.file_path = raster

    @property
    def sedi_export(self):
        """Return the sedi_export raster.

        For documentation, see :ref:`here <watemsedem:sediexportrst>`
        """
        if self._sedi_export is None:
            self.sedi_export = self.modeloutputfolder / "SediExport_kg.rst"
        return self._sedi_export

    @sedi_export.setter
    def sedi_export(self, raster):
        """Set the sedi_export raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sedi_export = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_export.arr, required_type=np.float32)
        valid_boundaries(
            self.sedi_export.arr[self.mask.arr != self.nodata],
            lower=0,
            upper=None,
            tolerance=0.001,
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "sedi_export [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the sedi_export raster with a non-linear colormap.

            Zeros are filtered out.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile of the data
                    available in the rivercells excluding zeros

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.sedi_export.arr, self.mask.arr, 0)
            arr = mask_array_with_val(
                self.sedi_export.arr, self.sedi_export.arr, self.nodata
            )
            # mask where the river is not present
            if not self.ls:
                msg = "Assign ls to Modeloutput before plotting sedi_export"
                raise NotImplementedError(msg)
            else:
                arr = np.ma.masked_where(self.ls.arr != self.nodata, arr)
            if not ticks:
                arr_nozeros = mask_array_with_val(arr, arr, 0)
                arr_nozeros = np.ma.filled(arr_nozeros, np.nan)
                ticks = np.nanpercentile(arr_nozeros, [0, 25, 50, 75, 100])
                ticks = np.round(
                    ticks
                ).tolist()  # avoids problems with invalid vmin or vmax
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                cmap=COLORMAP_SEDI_OUT,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")
            return fig, ax

        self._sedi_export.plot = plot
        self._sedi_export.file_path = raster

    @property
    def sinks(self):
        """Return the sinks raster.

        Sinks is computed as the sum of sewer_in and sedi_export.
        This represents the total sediment load reaching sink points.
        """
        if self._sinks is None:
            self.sinks = None
        return self._sinks

    @sinks.setter
    def sinks(self, raster):
        """Set the sinks raster.

        If raster is None, sinks is computed from sewer_in and sedi_export,
        written to a temporary GeoTIFF, and loaded as a raster factory object.
        Otherwise, sinks is loaded from the provided raster path.

        Parameters
        ----------
        raster: pathlib.Path | str | None
            Path to a sinks raster file, or None to compute from sewer_in +
            sedi_export.
        """

        if raster is None:
            # Sum endpoints (for now only sewer_in) and sedi_export
            arr_sewer_in = np.where(
                self.sewer_in.arr == self.nodata, 0, self.sewer_in.arr
            )
            arr_sedi_export = np.where(
                self.sedi_export.arr == self.nodata, 0, self.sedi_export.arr
            )
            arr_sinks = arr_sewer_in + arr_sedi_export
            arr_sinks[self.mask.arr == self.nodata] = self.nodata

            rst_sinks = self.modeloutputfolder / "sinks.rst"
            write_arr_as_rst(arr_sinks, rst_sinks, np.float32, self.rstparams)
            self._sinks = self.raster_factory(rst_sinks, flag_mask=False)
            raster_used = rst_sinks
        else:
            self._sinks = self.raster_factory(raster, flag_mask=False)
            raster_used = raster

        valid_array_type(self.sinks.arr, required_type=np.float32)
        valid_boundaries(
            self.sinks.arr[self.mask.arr != self.nodata],
            lower=0,
            upper=None,
            tolerance=0.001,
        )
        check_raster_properties_raster_with_template(
            self.rp, raster_used, epsg=self.rp.epsg
        )

        title = "sinks [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the sinks raster with a non-linear colormap.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                Possibility to supply a list of 5 values for ticks of colorscale.
                Default is 0th, 25th, 50th, 75th and 100th percentile

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.sinks.arr, self.mask.arr, 0)
            arr = mask_array_with_val(self.sinks.arr, self.sinks.arr, self.nodata)
            if not ticks:
                arr_nozeros = mask_array_with_val(arr, arr, 0)
                arr_nozeros = np.ma.filled(arr_nozeros, np.nan)
                ticks = np.nanpercentile(arr_nozeros, [0, 25, 50, 75, 100])
                ticks = np.round(ticks).tolist()
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                cmap=COLORMAP_SEDI_OUT,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")
            return fig, ax

        self._sinks.plot = plot
        self._sinks.file_path = raster_used

    @property
    def sedi_in(self):
        """Return the sedi_in raster.

        For documentation, see :ref:`here <watemsedem:sediinrst>`
        """
        if self._sedi_in is None:
            self.sedi_in = self.modeloutputfolder / "SediIn_kg.rst"
        return self._sedi_in

    @sedi_in.setter
    def sedi_in(self, raster):
        """Set the sedi_in raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sedi_in = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_in.arr, required_type=np.float32)
        valid_boundaries(
            self.sedi_in.arr[self.mask.arr != self.nodata],
            lower=0,
            upper=None,
            tolerance=1e-3,
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "sedi_in [kg/year]"

        def plot(
            fig=None, ax=None, ticks=[0, 10000, 20000, 40000, 80000], *args, **kwargs
        ):
            """Plot the sedi_in raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [0,10000,20000,40000,80000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.sedi_in.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_SEDI_OUT,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._sedi_in.plot = plot
        self._sedi_in.file_path = raster

    @property
    def sedi_out(self):
        """Return the sedi_out raster.

        For documentation, see :ref:`here <watemsedem:sedioutrst>`
        """
        if self._sedi_out is None:
            self.sedi_out = self.modeloutputfolder / "SediOut_kg.rst"
        return self._sedi_out

    @sedi_out.setter
    def sedi_out(self, raster):
        """Set the sedi_out raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sedi_out = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_out.arr, required_type=np.float32)
        valid_boundaries(
            self.sedi_out.arr[self.mask.arr != self.nodata],
            lower=0,
            upper=None,
            tolerance=1e-3,
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "sedi_out [kg/year]"

        def plot(
            fig=None, ax=None, ticks=[0, 10000, 20000, 40000, 80000], *args, **kwargs
        ):
            """Plot the sedi_out raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [0,10000,20000,40000,80000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.sedi_out.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_SEDI_OUT,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._sedi_out.plot = plot
        self._sedi_out.file_path = raster

    @property
    def sedtil_in(self):
        """Return the sedtil_in raster.

        For documentation, see :ref:`here <watemsedem:sedtilinrst>`
        """
        if self._sedtil_in is None:
            self.sedtil_in = self.modeloutputfolder / "SEDTIL_IN.rst"
        return self._sedtil_in

    @sedtil_in.setter
    def sedtil_in(self, raster):
        """Set the sedtil_in raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sedtil_in = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedtil_in.arr, required_type=np.float32)
        valid_boundaries(
            self.sedtil_in.arr[self.mask.arr != self.nodata], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "sedtil_in [kg/year]"

        def plot(
            fig=None, ax=None, ticks=[0, 10000, 20000, 40000, 80000], *args, **kwargs
        ):
            """Plot the sedtil_in raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [0,10000,20000,40000,80000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.sedtil_in.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_SEDI_OUT,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._sedtil_in.plot = plot
        self._sedtil_in.file_path = raster

    @property
    def sedtil_out(self):
        """Return the sedtil_out raster.

        For documentation, see :ref:`here <watemsedem:sedtiloutrst>`
        """
        if self._sedtil_out is None:
            self.sedtil_out = self.modeloutputfolder / "SEDTIL_OUT.rst"
        return self._sedtil_out

    @sedtil_out.setter
    def sedtil_out(self, raster):
        """Set the sedtil_out raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sedtil_out = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedtil_out.arr, required_type=np.float32)
        valid_boundaries(
            self.sedtil_out.arr[self.mask.arr != self.nodata], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "sedtil_out [kg/year]"

        def plot(
            fig=None, ax=None, ticks=[0, 10000, 20000, 40000, 80000], *args, **kwargs
        ):
            """Plot the sedtil_out raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [0,10000,20000,40000,80000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.sedtil_out.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_SEDI_OUT,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._sedtil_out.plot = plot
        self._sedtil_out.file_path = raster

    @property
    def cumulative(self):
        """Return the cumulative raster.

        For documentation, see :ref:`here <watemsedem:cumulativerst>`
        """
        if self._cumulative is None:
            self.cumulative = self.modeloutputfolder / "cumulative.rst"
        return self._cumulative

    @cumulative.setter
    def cumulative(self, raster):
        """Set the cumulative raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._cumulative = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_out.arr, required_type=np.float32)
        valid_boundaries(
            self.cumulative.arr[self.mask.arr != self.nodata], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "cumulative [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the cumulative raster with a logarithmic colormap.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.cumulative.arr, self.mask.arr, self.nodata)
            lower = log_scale_enabler(arr, cnorm="log")
            norm = colors.LogNorm(vmin=lower, vmax=np.nanmax(arr))
            fig, ax = plot_continuous_raster(
                fig,
                ax,
                arr=arr,
                bounds=self.rp.bounds,
                norm=norm,
                colorbar=True,
                ticks=ticks,
                *args,
                **kwargs,
            )
            ax.set_title(title)
            ax.set_facecolor("lightgray")
            return fig, ax

        self._cumulative.plot = plot
        self._cumulative.file_path = raster

    @property
    def watereros_kg(self):
        """Return the watereros_kg raster.

        For documentation, see :ref:`here <watemsedem:watereroskgrst>`
        """
        if self._watereros_kg is None:
            self.watereros_kg = (
                self.modeloutputfolder / "WATEREROS (kg per gridcel).rst"
            )
        return self._watereros_kg

    @watereros_kg.setter
    def watereros_kg(self, raster):
        """Set the watereros_kg raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._watereros_kg = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_out.arr, required_type=np.float32)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "watereros_kg [kg per year per gridcell]"

        def plot(
            fig=None, ax=None, ticks=[-2000, -1000, 0, 1000, 2000], *args, **kwargs
        ):
            """Plot the watereros_kg raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [-2000, -1000, 0, 1000, 2000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.watereros_kg.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_WATEREROS,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._watereros_kg.plot = plot
        self._watereros_kg.file_path = raster

    @property
    def watereros_mm(self):
        """Return the watereros_mm raster.

        For documentation, see :ref:`here <watemsedem:watererosmmrst>`
        """
        if self._watereros_mm is None:
            self.watereros_mm = (
                self.modeloutputfolder / "WATEREROS (mm per gridcel).rst"
            )
        return self._watereros_mm

    @watereros_mm.setter
    def watereros_mm(self, raster):
        """Set the watereros_mm raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._watereros_mm = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_out.arr, required_type=np.float32)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "watereros_mm [mm per year per gridcell]"

        def plot(fig=None, ax=None, ticks=[-2, -1, 0, 1, 2], *args, **kwargs):
            """Plot the watereros_mm raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [-20000, -10000, 0, 10000, 20000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.watereros_mm.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_WATEREROS,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._watereros_mm.plot = plot
        self._watereros_mm.file_path = raster

    @property
    def tileros_kg(self):
        """Return the tileros_kg raster.

        For documentation, see :ref:`here <watemsedem:tileroskgrst>`
        """
        if self._tileros_kg is None:
            self.tileros_kg = self.modeloutputfolder / "TILEROS (kg per gridcel).rst"
        return self._tileros_kg

    @tileros_kg.setter
    def tileros_kg(self, raster):
        """Set the tileros_kg raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._tileros_kg = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_out.arr, required_type=np.float32)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "tileros_kg [kg per year per gridcell]"

        def plot(
            fig=None, ax=None, ticks=[-10000, -5000, 0, 5000, 10000], *args, **kwargs
        ):
            """Plot the tileros_kg raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [-20000, -10000, 0, 10000, 20000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.tileros_kg.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_WATEREROS,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._tileros_kg.plot = plot
        self._tileros_kg.file_path = raster

    @property
    def tileros_mm(self):
        """Return the tileros_mm raster.

        For documentation, see :ref:`here <watemsedem:tilerosmmrst>`
        """
        if self._tileros_mm is None:
            self.tileros_mm = self.modeloutputfolder / "TILEROS (mm per gridcel).rst"
        return self._tileros_mm

    @tileros_mm.setter
    def tileros_mm(self, raster):
        """Set the tileros_mm raster.

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._tileros_mm = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_out.arr, required_type=np.float32)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "tileros_mm [mm per year per gridcell]"

        def plot(fig=None, ax=None, ticks=[-2, -1, 0, 1, 2], *args, **kwargs):
            """Plot the tileros_mm raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [-20000, -10000, 0, 10000, 20000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks =None, 0th, 25th, 50th, 75th and 100th percentile
                    of the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=self.tileros_mm.arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                cmap=COLORMAP_WATEREROS,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._tileros_mm.plot = plot
        self._tileros_mm.file_path = raster

    @property
    def capacity(self):
        """Return the capacity raster.

        For documentation, see :ref:`here <watemsedem:capacityrst>`
        """
        if self._capacity is None:
            self.capacity = self.modeloutputfolder / "Capacity.rst"
        return self._capacity

    @capacity.setter
    def capacity(self, raster):
        """Set the capacity raster.

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._capacity = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.capacity.arr, required_type=np.float32)
        valid_boundaries(
            self.capacity.arr[self.mask.arr != self.nodata], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "Capacity [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the capacity raster with a logarithmic colormap.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.capacity.arr, self.mask.arr, self.nodata)
            lower = log_scale_enabler(arr, cnorm="log")
            norm = colors.LogNorm(vmin=lower, vmax=np.nanmax(arr))
            fig, ax = plot_continuous_raster(
                fig,
                ax,
                arr=arr,
                bounds=self.rp.bounds,
                norm=norm,
                colorbar=True,
                ticks=ticks,
                *args,
                **kwargs,
            )
            ax.set_title(title)
            ax.set_facecolor("lightgray")
            return fig, ax

        self._capacity.plot = plot
        self._capacity.file_path = raster

    @property
    def rusle(self):
        """Return the RUSLE raster.

        For documentation, see :ref:`here <watemsedem:ruslerst>`
        """
        if self._rusle is None:
            self.rusle = self.modeloutputfolder / "RUSLE.rst"
        return self._rusle

    @rusle.setter
    def rusle(self, raster):
        """Set the RUSLE raster.

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._rusle = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.capacity.arr, required_type=np.float32)
        valid_boundaries(
            self.rusle.arr[self.mask.arr != self.nodata], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "RUSLE [kg/(year.m²)]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot the RUSLE raster.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = None
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    Default is 0th, 25th, 50th, 75th and 100th percentile of the data
                    excluding zero values

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            arr = mask_array_with_val(self.rusle.arr, self.mask.arr, self.nodata)
            fig, ax = plot_output_raster(
                fig=fig,
                ax=ax,
                arr=arr,
                mask=self.mask.arr,
                title=title,
                bounds=self.rp.bounds,
                ticks=ticks,
                *args,
                **kwargs,
            )
            ax.set_facecolor("lightgray")

        self._rusle.plot = plot
        self._rusle.file_path = raster

    def make_routing_vector(self, modelinput, percentile=90, routing_missing=False):
        """Converts pandas dataframe of routing or routing_missing to a geopandas
        dataframe

        Parameters
        ----------
        modelinput: Object
            instance of Modelinput class (see pywatemsedem/io/modelinput.py)
        percentile: int, default = 90
            Only vectors belonging to sedi_outdata percentile and higher is kept
        routing_missing: bool, default = False
                        set to True to apply function to routing_missing instead
                        of routing

        Returns
        --------
        geopandas.GeoDataFrame
        """
        arr_compositelanduse = modelinput.compositelanduse.arr

        # checks op raster
        valid_non_nan(arr_compositelanduse)
        valid_array_type(arr_compositelanduse, required_type=np.int16)
        valid_boundaries(arr_compositelanduse, lower=-32757, upper=32757)

        # selecting what to vectorise
        raster = self.modeloutputfolder / "SediOut_kg.rst"
        arr_sedi_out, profile_sedi_out = load_raster(raster)
        df_sedi_out = raster_array_to_pandas_dataframe(arr_sedi_out, profile_sedi_out)
        df_sedi_out_sel = df_sedi_out.loc[
            df_sedi_out["val"] > np.percentile(df_sedi_out["val"], percentile)
        ]
        if routing_missing:
            df = self.routing_missing
        else:
            df = self.routing
        df_temp = df.rename(
            columns={
                "target1col": "targetcol1",
                "target1row": "targetrow1",
                "target2col": "targetcol2",
                "target2row": "targetrow2",
            }
        )
        df_temp = pd.wide_to_long(
            df_temp,
            i=["col", "row"],
            stubnames=["targetcol", "targetrow", "distance", "part"],
            j="cell",
        ).reset_index()
        df_comb = df_sedi_out_sel.merge(df_temp, how="left", on=["row", "col"])
        # filter out data where part = 0 of None/NaN
        df_comb = df_comb[df_comb["part"] != 0]
        df_comb = df_comb[np.invert(pd.isnull(df_comb["part"]).values)]

        # + and - self.rp.resolution/2 for correction of vectors
        # being in center of cell
        df_comb["sourceX"] = (
            df_comb["col"] * self.rp.resolution
            + self.rp.bounds[0]
            - self.rp.resolution / 2
        )  # bounds[0] = xmin
        df_comb["sourceY"] = (
            -df_comb["row"] * self.rp.resolution
            + self.rp.bounds[3]
            + self.rp.resolution / 2
        )  # bounds[3] = ymax
        df_comb["targetX"] = (
            df_comb["targetcol"] * self.rp.resolution
            + self.rp.bounds[0]
            - self.rp.resolution / 2
        )
        df_comb["targetY"] = (
            -df_comb["targetrow"] * self.rp.resolution
            + self.rp.bounds[3]
            + self.rp.resolution / 2
        )
        geometry = [
            LineString(
                [
                    (df_comb.sourceX.iloc[i], df_comb.sourceY.iloc[i]),
                    (df_comb.targetX.iloc[i], df_comb.targetY.iloc[i]),
                ]
            )
            for i in range(len(df_comb))
        ]
        if routing_missing:
            self.gdf_routing_missing = gpd.GeoDataFrame(
                df_comb, geometry=geometry, crs=self.rp.epsg
            )
            return self.gdf_routing_missing
        else:
            self.gdf_routing = gpd.GeoDataFrame(
                df_comb, geometry=geometry, crs=self.rp.epsg
            )
            return self.gdf_routing


def get_prckrt_statistics(rst_prckrt, unit="ha", resolution=20):
    """Get the statistics of the WaTEM/SEDEM perceelskaart

    Load the WaTEM/SEDEM perceelskaart and compute for every unique id the area
    (ha or m2).

    Parameters
    ----------
    rst_prckrt: str or pathlib.Path | str
        File path ofWaTEM/SEDEM perceelskaart
    unit: str
        The unit of the output, currently pixel, m2 and ha implemented
    resolution: int
        Resolution of the rasters

    Returns
    -------
    out: dict,
        Area for each class, keys:

            - *agriculture* (float): area (ha/m2)
            - *river* (float): area (ha/m2)
            - *infrastructure* (float): area (ha/m2)
            - *forest* (float): area (ha/m2)
            - *meadow* (float): area (ha/m2)
            - *open_water* (float): area (ha/m2)
            - *gras_strip* (float): area (ha/m2)
    """
    arr_prckrt, profile = load_raster(rst_prckrt, list_format=False)
    arr_prckrt = arr_prckrt[arr_prckrt != profile["nodata"]]
    arr_prckrt[arr_prckrt > 0] = 1
    unique, counts = np.unique(arr_prckrt, return_counts=True)

    if unit in ["ha", "pixel", "m2"]:
        if unit == "ha":
            convert_unit = resolution**2 / 100**2
        elif unit == "pixel":
            convert_unit = 1
        elif unit == "m2":
            convert_unit = resolution**2
    else:
        msg = (
            f"Unit '{unit}' not defined, cannot convert unit from pixel to "
            "unit. Please select pixel, ha or m2"
        )
        return IOError(msg)

    out = {}

    out["agriculture"] = counts[unique == 1][0] if 1 in unique else 0
    out["river"] = counts[unique == -1][0] if -1 in unique else 0
    out["infrastructure"] = counts[unique == -2][0] if -2 in unique else 0
    out["forest"] = counts[unique == -3][0] if -3 in unique else 0
    out["meadow"] = counts[unique == -4][0] if -4 in unique else 0
    out["open_water"] = counts[unique == -5][0] if -5 in unique else 0
    out["gras_strip"] = counts[unique == -6][0] if -6 in unique else 0

    for i in list(out.keys()):
        if convert_unit != 1:
            out[i] = out[i] * convert_unit

    return out


def make_routing_vct_saga(
    txt_routing, rst_prckrt, vct_out, rstparams, extent=None, tile_number=None
):
    """Generate a routing vct routing file (added with WaTEM/SEDEM landuse) based on
    the routing table
    extent and tilenumber are defined to make a routing file only for a
    certain extent

    Parameters
    ----------
    txt_routing: str or pathlib.Path | str
        File path of the WaTEM/SEDEM routing tabl
    rst_prckrt: str
        name of WaTEM/SEDEM input 'perceelskaart'
    vct_out:
        name of the shape outputfile
    rstparams: dict
        gdal dictionary holding all metadata for idrisi rasters
    extent: list, default None
        list holding value of extent to consider, xmin,ymin,xmax,ymax
    tile_number: int, optional, default None
        number of the tile, used to add to filename

    Returns
    -------
    vct_out: str
        The resulting vector file will contain following features:

        - *col* (int): source column number.
        - *row* (int): source row number.
        - *targetcol* (int): target column number.
        - *targetcol* (int): source column number.
        - *part* (float): fraction of source that flows to target (between 0 and 1).
        - *distance* (float): distance of routing (m)
        - *landuSource* (int): landuse code of source pixel
        - *landuTarg* (int): landuse code of target pixel
        - *jump* (int): yes (1) or no (0)
        - *targetX* (float): x coor value of target
        - *targetY* (float): y coor value of target
        - *sourceX* (float): x coor value of source
        - *sourceY* (float): y coor value of source
    """

    # condition tag for making routing shape
    if txt_routing.exists():
        # check if file is tab seperated
        with open(txt_routing) as f:
            first_line = f.readline()
        seperator = ";" if "\t" not in first_line else "\t"
        # prepare the txt_file for conversion to routing shape
        vct_temp, condition = prepare_make_routing_vct_saga(
            txt_routing, vct_out, seperator, rstparams, extent, tile_number
        )

        # if condition True, run, if False (no routing segments available in
        # routing table) don't run
        if condition:
            run_saga_make_routing_shp_cmd(
                txt_routing,
                rst_prckrt,
                vct_temp,
                rstparams=rstparams,
            )
            return vct_temp
        else:
            msg = "No valid extent to clip routing "
            raise Warning(msg)
    else:
        msg = f"'{txt_routing}' does not exist!"
        raise IOError(msg)


def prepare_make_routing_vct_saga(
    txt_routing, vct_out, seperator, rstparams, extent, tile_number
):
    """
    Prepare the input files for make routing vct_saga
    If an extension is defined, then this function will clip the file to
    this rectangular geographical extent

    Parameters
    ----------
    txt_routing_nonriver: str or pathlib.Path | str
        File path of the WaTEM/SEDEM routing tabl
    vct_out: str
        name of output shapefile for 'run_saga_make_routing_shp_cmd' fuction
    seperator: str
        current delimited of txt_routing
    rstparams: dict
        gdal dictionary holding all metadata for idrisi rasters
    extent: list
        min and max of rectangular frame to clip df [xmin, xmax, ymin, ymax]
    tile_number: int
        number of tile

    Returns
    -------
    vct_temp: str
        The resulting vector file will contain following features:

        - *col* (int): source column number.
        - *row* (int): source row number.
        - *targetcol* (int): target column number.
        - *targetcol* (int): source column number.
        - *part* (float): fraction of source that flows to target (between 0 and 1).
        - *distance* (float): distance of routing (m)
        - *landuSource* (int): landuse code of source pixel
        - *landuTarg* (int): landuse code of target pixel
        - *jump* (int): yes (1) or no (0)
        - *targetX* (float): x coor value of target
        - *targetY* (float): y coor value of target
        - *sourceX* (float): x coor value of source
        - *sourceY* (float): y coor value of source
    condition: boolean
        True if make_routing_shp has to be run

    """
    # check if an extent is defined for conversion to shape file, if not,
    # take whole domain txt_routing
    condition = True

    if extent is not None:
        df_routing = open_txt_routing_file(txt_routing)
        df_routing = condition_routing_dataframe_on_extent(
            df_routing, rstparams, extent
        )
        # rename files
        tag = f"_selected_{(0 if tile_number is None else tile_number)}"
        txt_routing = txt_routing.parent / txt_routing.stem + tag + ".txt"
        vct_temp = vct_out.parent / vct_out.stem + tag + ".shp"
        if seperator != "\t":
            df_routing.to_csv(txt_routing, sep="\t", index=False)
        # condition true if routing directions are found within extent
        condition = False if len(df_routing) == 0 else True

    else:
        # condition = True if no extent given
        vct_temp = vct_out
        condition = True
        df_routing = open_txt_routing_file(txt_routing)
        if seperator != "\t":
            df_routing.to_csv(txt_routing, sep="\t", index=False)

    return vct_temp, condition


def condition_routing_dataframe_on_extent(df_routing, rstparams, extent):
    """
    Clip routing_dataframe on defined extent

    Parameters
    ----------
    df_routing: pandas.DataFrame
        See :func:`pywatemsedem.io.modeloutput.open_txt_routing_file`
    rstparams: dict
        gdal dictionary holding all metadata for idrisi rasters
    extent: list
        min and max of rectangular frame to clip df [xmin, xmax, ymin, ymax]

    Returns
    -------
    df_routing: pandas.DataFrame
        See :func:`pywatemsedem.io.modeloutput.open_txt_routing_file`

    """
    # get xmin and ymin from rasterproperties
    xmin, ymin = (
        rstparams["minmax"][0],
        rstparams["minmax"][1],
    )
    # compile x and y's of source points in df
    df_routing["x"] = xmin + df_routing["col"] * rstparams["res"]
    df_routing["y"] = ymin + (rstparams["nrows"] - df_routing["row"]) * rstparams["res"]
    # condition
    cond = (
        (df_routing["x"] > extent[0])
        & (df_routing["x"] < extent[1])
        & (df_routing["y"] > extent[2])
        & (df_routing["y"] < extent[3])
    )
    df_routing = df_routing.loc[cond]

    return df_routing


def _parse_epsg_from_value(crs_value):
    """Extract EPSG code as int from multiple CRS representations."""
    if crs_value is None:
        return None

    if isinstance(crs_value, int):
        return crs_value

    if hasattr(crs_value, "to_epsg"):
        epsg = crs_value.to_epsg()
        if epsg is not None:
            return int(epsg)

    if isinstance(crs_value, str):
        value = crs_value.upper().strip()
        if "EPSG:" in value:
            value = value.split(":")[-1]
        if value.isdigit():
            return int(value)

    return None


def _get_epsg_for_routing_vector(rstparams=None, rst_prckrt=None):
    """Resolve the EPSG code for routing vectors."""
    if isinstance(rstparams, dict):
        epsg = _parse_epsg_from_value(rstparams.get("crs"))
        if epsg is not None:
            return epsg
        epsg = _parse_epsg_from_value(rstparams.get("epsg"))
        if epsg is not None:
            return epsg

    if rst_prckrt is not None:
        _, profile = load_raster(rst_prckrt)
        return _parse_epsg_from_value(profile.get("crs"))

    return None


def _set_vector_epsg(vct_out, epsg):
    """Set CRS on a vector file and overwrite with explicit EPSG metadata."""
    if epsg is None:
        warnings.warn(f"Could not determine EPSG for routing vector '{vct_out}'.")
        return

    gdf_out = gpd.read_file(vct_out)
    current_epsg = (
        gdf_out.crs.to_epsg()
        if (gdf_out.crs is not None and hasattr(gdf_out.crs, "to_epsg"))
        else None
    )
    if current_epsg != epsg:
        gdf_out = gdf_out.set_crs(epsg=epsg, allow_override=True)
        gdf_out.to_file(vct_out, spatial_index="YES")


def run_saga_make_routing_shp_cmd(txt_routing, rst_prckrt, vct_out, rstparams=None):
    """
    Run the saga make routing shape command. This command makes from a pywatemsedem
    routing table and a pywatemsedem 'perceelskaart' a routing shapfile
    representation.

    The resulting vector file will contain following features:

    - *col* (int): source column number.
    - *row* (int): source row number.
    - *targetcol* (int): target column number.
    - *targetcol* (int): source column number.
    - *part* (float): fraction of source that flows to target (between 0 and 1).
    - *distance* (float): distance of routing (m)
    - *landuSource* (int): landuse code of source pixel
    - *landuTarg* (int): landuse code of target pixel
    - *jump* (int): yes (1) or no (0)
    - *targetX* (float): x coor value of target
    - *targetY* (float): y coor value of target
    - *sourceX* (float): x coor value of source
    - *sourceY* (float): y coor value of source

    Parameters
    ----------
    txt_routing_nonriver: str or pathlib.Path | str
        File path of the WaTEM/SEDEM routing table
    rst_prckrt: str
        File path of the WaTEM/SEDEM 'perceelskaart' raster
    vct_out: str
        File path of the output file


    """
    cmd_args = ["saga_cmd", "-f=s", "topology", "2"]
    cmd_args += ["-ROUTING", str(txt_routing)]
    cmd_args += [
        "-LANDUSE",
        str(rst_prckrt),
    ]
    cmd_args += ["-OUTPUTLINES", str(vct_out)]
    execute_saga(cmd_args)

    epsg = _get_epsg_for_routing_vector(rstparams=rstparams, rst_prckrt=rst_prckrt)
    _set_vector_epsg(vct_out, epsg)

    create_spatial_index(vct_out)


def define_subcatchments_saga(
    rst_in,
    txt_routing,
    resmap,
    rasterprop,
    tag="",
):
    """
    Define subcatchment for several points defined with a unique id in the
    raster

    Parameters
    ----------
    rst_in:
        Raster with single-pixels for which subcatchment should be determined
        > 0: determine subcatchment
        = 0: don't determine subcatchments
    txt_routing_nonriver: str or pathlib.Path | str
        File path of the WaTEM/SEDEMrouting table
    resmap: str or pathlib.Path | str
        Folder path where results should be saved
    rasterprop: dict
        rasterio profile dictionary holding all metadata for geotiff rasters
    tag: str or pathlib.Path | str
        File path of output shape and raster
    catchment_name: str
        Name of catchment, default ""
    scenario_label: str, default ""
        Scenario number or letter.

    Returns
    -------
    rst_subcatchments: str or pathlib.Path | str
        File path of raster with pixels beloging to a subcatchment having id
        equal to id sink in rst_in
    vct_subcatchments: str or pathlib.Path | str:
        File path of shapefile with polygon being the subcatchment having an
        id equal         to id sink in rst_in
    """
    # txt = os.path.join(self.scenario.outfolder, 'routing.txt')
    rst_subcatchments = resmap / f"subcatchments_{tag}.sdat"
    vct_subcatchments = rst_subcatchments.with_suffix(".shp")

    startvals = np.unique(load_raster(rst_in)[0])
    if len(startvals) <= 1:
        msg = "No values in input grid to define subcatchments!"
        raise ValueError(msg)

    cmd_args = ["saga_cmd", "-f=s", "topology", "3", "-ROUTING", str(txt_routing)]
    cmd_args += ["-SEGMENTS", str(rst_in)]
    cmd_args += ["-CATCH", str(rst_subcatchments)]

    execute_saga(cmd_args)
    raster_to_polygon(rst_subcatchments, vct_subcatchments)
    create_spatial_index(vct_subcatchments)
    gdf_subcatchments = gpd.read_file(vct_subcatchments)
    gdf_subcatchments.drop(columns=["ID", "NAME"], inplace=True)
    gdf_subcatchments["VALUE"] = gdf_subcatchments["VALUE"].astype("int32")
    gdf_subcatchments["AREA_HA"] = gdf_subcatchments.area / 10000.0
    gdf_subcatchments = gdf_subcatchments.set_crs(rasterprop["epsg"])
    gdf_subcatchments.to_file(vct_subcatchments, spatial_index="YES")

    return (
        (rst_subcatchments.parent / (rst_subcatchments.stem + ".sdat")),
        vct_subcatchments,
    )


def remove_river_routing(df_routing):
    """Remove river routing from routing dataframe

    Parameters
    ----------
    df_routing: pandas.DataFrame
        Long format of routing table

    Returns
    -------
    df_routing
        Long format of routing table, with river routing removed
    """
    df_routing = df_routing.loc[(df_routing["lnduSource"] != -1)]
    cols = [
        "lnduSource",
        "lnduTarg",
        "jump",
        "geometry",
        "targetX",
        "targetY",
        "sourceX",
        "sourceY",
    ]
    df_routing.drop(columns=cols, inplace=True)

    return df_routing


def compute_efficiency_buffers(rst_buffer, rst_sedi_in, rst_sedi_out):
    """Compute efficiency per buffer

    This function calculates the incoming and outgoing sediment per buffer.
    The deposition is computed by substracting the outgoing from the ingoing
    sediment.

    Parameters
    ----------
    rst_buffer: str or pathlib.Path | str
        File path of buffer raster with buffer id's
    rst_sedi_in: str or ppathlib.Path | str
        File path of WaTEM/SEDEM sedi_in raster, incoming sediment per pixel
    rst_sedi_out: str or pathlib.Path | str
        File path of WaTEM/SEDEM sedi_out raster, outgoing sediment per pixel

    Returns
    -------
    df_output: pandas.DataFrame
        Holding results of mass balance of buffers.

        - *buf_id* (float): id of the buffer (as in the buffer raster)
        - *sedi_in* (float): total incoming sediment in the buffer.
        - *sedi_out* (float): total outgoing sediment in the buffer.
        - *buff_sed* (float): amount sediment deposited in the buffer.
    """
    arr_buffers, profile = load_raster(rst_buffer)
    arr_sedi_in, _ = load_raster(rst_sedi_in)
    arr_sedi_out, _ = load_raster(rst_sedi_out)

    df_out = pd.DataFrame(columns=["NR", "sedi_in", "sedi_out", "buff_sed"])
    condition = (arr_buffers < 2**14) & (arr_buffers > 0)
    arr_unique_buffer = np.unique(arr_buffers[condition])
    for buf_id in arr_unique_buffer:
        arr_sedi_in_buffer = np.sum(arr_sedi_in[arr_buffers == buf_id])
        arr_sedi_out_buffer = np.sum(arr_sedi_out[arr_buffers == buf_id])
        arr_deposition = arr_sedi_in_buffer - arr_sedi_out_buffer
        df_out.loc[df_out.shape[0] + 1] = [
            buf_id,
            arr_sedi_in_buffer,
            arr_sedi_out_buffer,
            arr_deposition,
        ]
    return df_out


def open_txt_routing_file(txt_routing):
    """
    Returns
    -------
    pandas.DataFrame
        Routing table if successful

    Raises
    ------
    FileNotFoundError
        If file does not exist
    ValueError
        If file exists but is empty or invalid
    RuntimeError
        For other reading/parsing issues
    """

    txt_routing = Path(txt_routing)

    # 1. File does not exist
    if not txt_routing.exists():
        raise FileNotFoundError(f"Routing file does not exist: '{txt_routing}'")

    try:
        # 2. Check if empty
        with open(txt_routing) as f:
            first_line = f.readline().strip()

        if first_line == "":
            raise ValueError(f"Routing file is empty: '{txt_routing}'")

        separator = ";" if "\t" not in first_line else "\t"

        df_routing = pd.read_csv(txt_routing, sep=separator)

        if df_routing.empty:
            raise ValueError(f"Routing file has no data rows: '{txt_routing}'")

        return df_routing

    except pd.errors.EmptyDataError:
        raise ValueError(f"Routing file contains no readable data: '{txt_routing}'")

    except Exception as e:
        raise RuntimeError(f"Error reading routing file '{txt_routing}': {e}") from e


def create_erosion_raster(rst_watereros):
    """Create erosion raster from watereros.

    Extract negative values from Watereros raster and set positives to 0. Erosion
    values in this raster are positive (inverse of watereros)

    Parameters
    ----------
    rst_watereros: str or pathlib.Path | str
        File path to WaTEM/SEDEM watereros raster.

    Returns
    -------
    rst_erosion: pathlib.Path | str
        File path to pywatemsedem erosion raster.
    """
    rst_erosion = Path(rst_watereros).parent / "Erosion (kg).rst"
    if not rst_erosion.exists():
        arr_watereros, profile = load_raster(rst_watereros)
        arr_watereros[arr_watereros > 0] = 0
        arr_watereros[arr_watereros != profile["nodata"]] = -arr_watereros[
            arr_watereros != profile["nodata"]
        ]
        write_arr_as_rst(arr_watereros, rst_erosion, arr_watereros.dtype, profile)

    return rst_erosion


def create_deposition_raster(rst_watereros):
    """Create deposition raster from watereros.

    Extract positve values from Watereros raster and set negatives to 0

    Parameters
    ----------
    rst_watereros: str or pathlib.Path | str
        File path to WaTEM/SEDEM watereros raster.

    Returns
    -------
    rst_deposition: pathlib.Path | str
        File path to pywatemsedem erosion raster.
    """
    rst_deposition = Path(rst_watereros).parent / "Deposition (kg).rst"
    if not rst_deposition.exists():
        arr_watereros, profile = load_raster(rst_watereros)
        arr_watereros[arr_watereros < 0] = 0
        arr_watereros[arr_watereros != profile["nodata"]] = arr_watereros[
            arr_watereros != profile["nodata"]
        ]
        write_arr_as_rst(arr_watereros, rst_deposition, arr_watereros.dtype, profile)

    return rst_deposition


def map_rank_sediment_loads(
    rst_sedi_export, threshold, epsg, vct_out="rank.shp", rst_endpoints=None, unit="kg"
):
    """Rank the sediment loads in sedi_export (and sewer_in) from high to low

    This function uses the rank output raster/dataframe of
    :func:`pywatemsedem.io.modeloutput.identify_rank_sediment_loads`
    to map a vector point file with information on rank, sediment output.

    For computation details, see
    :func:`pywatemsedem.io.modeloutput.identify_rank_sediment_loads`

    Parameters
    ----------
    rst_sedi_export: str or pathlib.Path | str
        File path of WaTEM/SEDEM sedi_export raster.
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`
    epsg: int
        EPSG code
    vct_out: str or pathlib.Path | str
        File path of output vector.
    rst_endpoints: str or pathlib.Path | str, default None
        File path to WaTEM/SEDEM sewer_in raster (endpoints in pywatemsedem).
    unit: str
        "kg" or "ton"

    Note
    ----
    Only points are taken into account that account for x of the highest sediment loads.
    x is determined by threshold.
    """
    if unit not in ["kg", "ton"]:
        f"Unit '{unit}' should be either 'kg' op 'ton'."

    rst_out = create_filename(".rst")
    df_sedi_export, threshold = identify_rank_sediment_loads(
        rst_sedi_export, threshold, rst_out, rst_endpoints
    )
    rst_to_vct_points(rst_out, vct_out)
    gdf_out = gpd.read_file(vct_out)
    gdf_out["rank"] = gdf_out[gdf_out.columns[0]]
    gdf_out = gdf_out.merge(df_sedi_export, on="rank")
    if unit == "ton":
        gdf_out["sedi_export"] = gdf_out["sedi_export"] / 1000

    gdf_out = gdf_out.dropna()
    gdf_out = gdf_out.set_crs(epsg=epsg)
    gdf_out.to_file(vct_out)
    clean_up_tempfiles(Path(rst_out), "rst")


def identify_rank_sediment_loads(
    rst_sedi_export, threshold, rst_out, rst_endpoints=None
):
    """Identify the highest ``threshold`` percentage sediment loads.

    This functions identifies the cumulative distribution of the sedi_export
    (and sewer_in, optional) raster:

    - (optional) map sewer_in  raster to sedi_export raster
    - convert sedi_export raster to a list-format
    - sort from high to low
    - compute cumulative distribution
    - classify

    Parameters
    ----------
    rst_sedi_export: str or pathlib.Path | str
        File path to WaTEM/SEDEM sedi_export raster.
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`
    rst_out: str of pathlib.Path | str
        Output raster containing ranks of highest sediment loads (1: highest,
        2: second highest, ..)
    rst_endpoints: str or pathlib.Path | str
        File path to WaTEM/SEDEM sewer_in raster.

    Returns
    -------
    df_sedi_export: pandas.DataFrame
        Data Frame format of sedi_export raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`)
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`
    """
    arr_sedi_export, profile = load_raster(rst_sedi_export)
    arr_sedi_export = np.where(arr_sedi_export == profile["nodata"], 0, arr_sedi_export)

    if rst_endpoints is not None:
        arr_sewer_in, _ = load_raster(rst_endpoints)
        arr_sewer_in = np.where(arr_sewer_in == profile["nodata"], 0, arr_sewer_in)
        arr_sedi_export += arr_sewer_in

    df_sedi_export = raster_array_to_pandas_dataframe(arr_sedi_export, profile)
    profile["driver"] = "GTiff"

    # sort and select points
    df_sedi_export, threshold = compute_cumulative_loads_in_sinks(
        df_sedi_export, profile, threshold, plot=False
    )
    arr_sedi_export = raster_dataframe_to_arr(
        df_sedi_export, profile, "rank", np.float32
    )

    write_arr_as_rst(
        arr_sedi_export,
        rst_out,
        "float32",
        profile,
    )

    return df_sedi_export, threshold


def compute_cumulative_loads_in_sinks(
    df_sedi_export, profile, threshold, delta=10, plot=False
):
    """Analyse cumulative sediment load by sorting sedi_export values
    from high to low

    Parameters
    ----------
    df_sedi_export: pandas.DataFrame
        Data Frame format of sedi_export raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`)
    profile: rasterio.profiles
        See :func:`rasterio.open`
    threshold: int
        x percentage highest load that the user wants to analyse
    delta: int
        Delta used to iterate percentage
    plot: bool, default False
        True if you want a cumulative sedi_export plot

    Returns
    -------
    df_sedi_export: pandas.DataFrame
        Data Frame format of sedi_export raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`) added
        with:

        - *cum_perc* (float): cumulative highest load
        - *perc* (float): percentage highest load
        - *class* (int): class as defined by `delta_perc`

    percentage: str
        updated percentage
    """

    # sort according to values of sediment load into river
    df_sedi_export["sedi_export"] = df_sedi_export["val"]
    df_sedi_export = df_sedi_export.sort_values("sedi_export", ascending=False)

    # calculate cumulative sum, in percentage
    cond = (df_sedi_export["sedi_export"] != profile["nodata"]) & (
        df_sedi_export["val"] != 0.0
    )
    df_sedi_export.loc[cond, "cum_sum"] = df_sedi_export.loc[
        cond, "sedi_export"
    ].cumsum()
    df_sedi_export.loc[cond, "cum_perc"] = (
        100
        * df_sedi_export.loc[cond, "cum_sum"]
        / df_sedi_export.loc[cond, "sedi_export"].sum()
    )

    if plot:
        plot_cumulative_sedimentload(
            df_sedi_export.loc[cond],
            threshold,
            "cumulative_sedi_export.png",
        )

    # hotfix on percentage: if the first percentage is higher than the
    # user-predefined percentage, adjust it (small catchments)!
    threshold = verify_highest_load_with_threshold(df_sedi_export, threshold)

    # prepare ids for subcatchment delineation
    df_sedi_export["rank"] = profile["nodata"]
    df_sedi_export["class"] = profile["nodata"]

    # assign unique id's - in order of importance - to records
    cond = (df_sedi_export["cum_perc"] <= threshold) & (
        ~df_sedi_export["cum_perc"].isnull()
    )
    df_sedi_export.loc[cond, "rank"] = np.arange(np.sum(cond)) + 1

    # calculate percentage
    df_sedi_export["perc"] = [
        (
            df_sedi_export["cum_perc"].iloc[i] - df_sedi_export["cum_perc"].iloc[i - 1]
            if i != 0
            else df_sedi_export["cum_perc"].iloc[i]
        )
        for i in range(0, len(df_sedi_export))
    ]

    # chekc if begin percentage is below delta_perc
    bperc = delta
    eperc = int(threshold + 1)
    if df_sedi_export["cum_perc"].iloc[0] > bperc:
        bperc = int(np.ceil(df_sedi_export["cum_perc"].iloc[0] / 10) * 10)

    for i in range(bperc, eperc, delta):
        cond = (
            (df_sedi_export["cum_perc"] > i - delta)
            & (df_sedi_export["cum_perc"] <= i)
            & (~df_sedi_export["cum_perc"].isnull())
        )
        df_sedi_export.loc[cond, "class"] = i

    return (
        df_sedi_export[
            ["col", "row", "rank", "perc", "cum_perc", "class", "sedi_export"]
        ],
        int(threshold),
    )


def verify_highest_load_with_threshold(df_sedi_export, threshold):
    """Verify whether that the highest load is not accountable for more than 50 percent
    of all the load in a catchment. If this is true, adapt threshold.

    Parameters
    ----------
    df_sedi_export: pandas.DataFrame
        Data Frame format of sedi_export raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`)
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`

    Returns
    -------
    threshold_: float
        Adapted threshold (depending on if-else clause).
    """
    cum_sum_sinks0 = df_sedi_export["cum_perc"].iloc[0]

    if cum_sum_sinks0 > threshold:
        threshold_ = np.ceil(cum_sum_sinks0)
        msg = (
            f"Highest load is accountable for more than {threshold} percent of the "
            f"total sediment load. Adapting percentage to {threshold_}."
        )
        raise Warning(msg)
    else:
        threshold_ = threshold
    return threshold_


def load_total_sediment_file(txt_total_sediment_file):
    """Load the total sediment file of WaTEM/SEDEM written in WaTEM/SEDEM
    dict_output map

    Parameters
    ----------
    txt_total_sediment_file: str or pathlib.Path | str
        File Path of the sediment file

    Returns
    -------
    dict_output: dict
        The dict_output sediment data dictionary contains the following data:

        - *erosion* (float): total amount of erosion (kg)
        - *deposition* (float): total amount of deposition (kg)
        - *river* (float): total amount of sediment run-off to the river (kg)
        - *outside_domain* (float): total amount of sediment run-off out of the \
        catchment (kg)
        - *buffers* (float): total amount of sediment trapped in buffers (kg)
        - *endpoints* (float): total sewer of sediment trapped in sewers and \
        ditches (kg)

    """
    file = open(txt_total_sediment_file, "r")
    Lines = file.readlines()

    dict_output = {}

    for line in Lines:

        line = line.split(" ")
        # hardcode
        tag = " ".join(line[:-2])
        if tag == "Total erosion:":
            dict_output["erosion"] = float(line[-2])
        elif tag == "Total deposition:":
            dict_output["deposition"] = float(line[-2])
        elif tag == "Sediment leaving the catchment, via the river:":
            dict_output["river"] = float(line[-2])
        elif tag == "Sediment leaving the catchment, not via the river:":
            dict_output["outside_domain"] = float(line[-2])
        elif tag == "Sediment trapped in buffers:":
            dict_output["buffers"] = float(line[-2])
        elif tag == "Sediment entering sewer system:":
            dict_output["endpoints"] = float(line[-2])

    return dict_output


def load_sediment_segments_file(txt_sediment_segments_file):
    """Load the WaTEM/SEDEM total/cumulative sediment per segment file.

    Parameters
    ----------
    txt_sediment_segments_file : str or pathlib.Path
        Path to the text file containing sediment values for each segment.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the sediment data per segment. The table contains:

        - first column: segment identifiers (integer)
        - second column: sediment values associated with each segment (float)

    """
    df_sediment_segments = pd.read_table(txt_sediment_segments_file, skiprows=1)

    return df_sediment_segments.set_index("segment_id")


def check_segment_edges(adj_edges, up_edges, arr):
    """Check river segment their edges. All the segments present in adj_edges
    and up_edges must be present in the array from the segments raster.

    Parameters
    ----------
    adj_edges: pandas.DataFrame
        Loaded adjacent edges text file, see :ref:`here <watemsedem:adjsegments>`
    up_edges: pandas.DataFrame
        Loaded up edges text file, see :ref:`here <watemsedem:upstrsegments>`
    arr: numpy.ndarray
        Segment raster array

    Returns
    --------
    adj_edges: pandas.DataFrame
        Filtered
    up_edges: pandas.DataFrame
        Filtered
    filt: bool
        Flag indicating filtering of dataframes
    """
    uniq_segm_rst = set(np.unique(arr))
    uniq_segm_ue = set(up_edges["upstream_line"].unique())
    uniq_segm_e = set(up_edges["line_id"].unique())
    uniq_segm_from = set(adj_edges["from"].unique())
    uniq_segm_to = set(adj_edges["to"].unique())
    filt = False

    if not uniq_segm_ue.issubset(uniq_segm_rst):
        msg = (
            "More segments in the up edges table than in the raster, filtering" "table."
        )
        warnings.warn(msg)
        up_edges = up_edges.loc[up_edges["upstream_line"].isin(uniq_segm_rst)]
        filt = True

    if not uniq_segm_e.issubset(uniq_segm_rst):
        msg = (
            "More segments in the up edges table than in the raster, filtering" "table."
        )
        warnings.warn(msg)
        up_edges = up_edges.loc[up_edges["line_id"].isin(uniq_segm_rst)]
        filt = True

    if not uniq_segm_from.issubset(uniq_segm_rst):
        msg = (
            "More segments in the adjacent edges table than in the raster, "
            "filtering table."
        )
        warnings.warn(msg)
        adj_edges = adj_edges.loc[adj_edges["from"].isin(uniq_segm_rst)]
        filt = True

    if not uniq_segm_to.issubset(uniq_segm_rst):
        msg = (
            "More segments in the adjacent edges table than in the raster, "
            "filtering table."
        )
        adj_edges = adj_edges.loc[adj_edges["to"].isin(uniq_segm_rst)]
        warnings.warn(msg)
        filt = True

    return adj_edges, up_edges, filt
