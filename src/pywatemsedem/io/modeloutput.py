# seperate plotting funcion
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

# hvplot functionalities
from matplotlib import colors
from shapely.geometry import LineString

from pywatemsedem.plots import plot_cumulative_sedimentload

from ..geo.factory import Factory
from ..geo.utils import (
    check_raster_properties_raster_with_template,
    clean_up_tempfiles,
    create_spatial_index,
    execute_saga,
    load_raster,
    mask_array_with_val,
    raster_array_to_pandas_dataframe,
    raster_dataframe_to_arr,
    raster_to_polygon,
    rst_to_vct_points,
    write_arr_as_rst,
)
from ..io.plots import axes_creator  # hvplot_continuous_raster,
from ..io.plots import log_scale_enabler, plot_continuous_raster, plot_output_raster
from ..io.valid import valid_array_type, valid_boundaries, valid_non_nan

IMPLEMENTED_RASTER_TYPES = [np.int16, np.int32, np.int64, np.float32, np.float64]
COLORMAP = "cividis"
COLORMAP_SEDIOUT = colors.LinearSegmentedColormap.from_list(
    "SediOutcmap", ["#ffffff", "#fecc5c", "#ff8c00", "#d7191c", "#bd0026"]
)


@dataclass
class Modeloutput(Factory):
    def __init__(self, template, resolution, epsg, nodata):
        """AbstractRaster class with model outputs as attributes. Modeloutput class
        serves the goal of automating the reading in, checking and visualisation
        of the output data of the CNWS model.

        Parameters
        ----------
        template: pathlib.Path | str
            Template raster needed to extract raster properties.
            Raster contains values in [0,1]. Values in ]0,1] define the catchment.
        resolution: int
            See :class:`pywatemsedem.geo.RasterProperties`.
        epsg: int
            See :class:`pywatemsedem.geo.RasterProperties`.
        nodata: float
            See :class:`pywatemsedem.geo.RasterProperties`.
        """
        super().__init__(resolution, epsg, nodata, template.parent)
        self.mask = template

        # DATA
        self._sediout = None
        self._routing = None
        self._routing_missing = None
        self._ls = None
        self._slope = None
        self._uparea = None
        self._total_sediment = None
        self._sewer_in = None
        self._sedi_export = None
        self._sedi_in = None
        self._capacity = None
        self._rusle = None

    @property
    def sediout(self):
        """Getter SediOut attribute.

        For documentation, see :ref:`here <watemsedem:sedioutrst>`
        """
        return self._sediout

    @sediout.setter
    def sediout(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sediout = self.raster_factory(raster, flag_mask=False)
        # checks on raster data
        valid_non_nan(self.sediout.arr)
        valid_array_type(self.sediout.arr, required_type=np.float32)
        valid_boundaries(
            self.sediout.arr[self.sediout.arr != -9999], lower=0, upper=None
        )

        title = "SediOut [kg/year]"

        def plot(
            fig=None, ax=None, ticks=[0, 10000, 20000, 40000, 80000], *args, **kwargs
        ):
            """Plot for SediOut with nonlinear colorscale. Masked under 100 kg/year.

            Parameters
            ----------
            fig: matplotlib.figure.Figure, default = None
                if not given, defaults to generating new figure
            ax: matplotlib.pyplot.axis, default = None
                if not given, defaults to generating new axis
            ticks: list, default = [0,10000,20000,40000,80000]
                    Possibility to supply a list of 5 values for ticks of colorscale.
                    If ticks = None, 0th, 25th, 50th, 75th and 100th percentile of
                    the data are used as ticks

            Returns
            -------
            fig: matplotlib.figure.Figure

            ax: matplotlib.axes.Axes
            """
            arr = np.ma.masked_where(self.sediout.arr < 100, self.sediout.arr)
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                cmap=COLORMAP_SEDIOUT,
                *args,
                **kwargs,
            )
            return fig, ax

        self._sediout.plot = plot

    @property
    def routing(self):
        """Getter routing attribute.
        For documentation, see :ref:`here <watemsedem:routingtxt>`
        """
        return self._routing

    @routing.setter
    def routing(self, text):
        """Setter

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
            """Interactive plot for routing

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

    @property
    def routing_missing(self):
        """Getter routing_missing attribute.
        For documentation, see :ref:`here <watemsedem:missingroutingtxt>`
        """
        return self._routing_missing

    @routing_missing.setter
    def routing_missing(self, text):
        """Setter

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
            """Interactive plot for routing_missing

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

    @property
    def ls(self):
        """Getter LS (length-slope) attribute.

        For documentation, see :ref:`here <watemsedem:lsmap>`
        """
        return self._ls

    @ls.setter
    def ls(self, raster):
        """Setter

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._ls = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.ls.arr, required_type=np.float32)
        valid_boundaries(self.ls.arr[self.ls.arr != -9999], lower=0, upper=None)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "LS [-]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot for LS with non-linear colormap

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
            arr = mask_array_with_val(self.ls.arr, self.ls.arr, -9999)
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
            return fig, ax

        self._ls.plot = plot

    @property
    def slope(self):
        """Getter slope attribute.

        For documentation, see :ref:`here <watemsedem:slopemap>`
        """
        return self._slope

    @slope.setter
    def slope(self, raster):
        """Setter

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._slope = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.slope.arr, required_type=np.float32)
        valid_boundaries(self.slope.arr[self.slope.arr != -9999], lower=0, upper=None)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "Slope [rad]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot for Slope with non-linear colormap

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
            arr = mask_array_with_val(self.slope.arr, self.slope.arr, -9999)
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
            return fig, ax

        self._slope.plot = plot

    @property
    def uparea(self):
        """Getter uparea attribute.

        For documentation, see :ref:`here <watemsedem:upareamap>`
        """
        return self._uparea

    @uparea.setter
    def uparea(self, raster):
        """Setter

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._uparea = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.uparea.arr, required_type=np.float32)
        valid_boundaries(self.uparea.arr[self.uparea.arr != -9999], lower=0, upper=None)
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "uparea [m²]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot for uparea with non-linear colormap

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
                arr = mask_array_with_val(self.uparea.arr, self.ls.arr, -9999)
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
            return fig, ax

        self._uparea.plot = plot

    @property
    def total_sediment(self):
        """Getter total sediment attribute.

        For documentation, see :ref:`here <watemsedem:totalsedimenttxt>`.
        For explanation on colmun variables of dataframe: see
        :func:`pywatemsedem.pywatemsedem.cnwsoutput.load_total_sediment_file`.
        """
        return self._total_sediment

    @total_sediment.setter
    def total_sediment(self, text):
        """Setter

        Parameters
        ----------
        text: pathlib.Path | str
        """
        dict = load_total_sediment_file(text)
        self._total_sediment = pd.DataFrame(dict, index=[0])

    @property
    def sewer_in(self):
        """Getter sewer_in attribute.

        For documentation, see :ref:`here <watemsedem:sewerinrst>`
        """
        return self._sewer_in

    @sewer_in.setter
    def sewer_in(self, raster):
        """Setter

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._sewer_in = self.raster_factory(raster, flag_mask=True)

        valid_array_type(self.sewer_in.arr, required_type=np.float32)
        valid_boundaries(
            self.sewer_in.arr[self.sewer_in.arr != -9999], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "sewer in [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot for sewer_in with non-linear colormap. Zeros are filtered out

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
            arr = mask_array_with_val(self.sewer_in.arr, self.sewer_in.arr, -9999)
            arr = mask_array_with_val(arr, self.sewer_in.arr, 0)
            fig, ax = plot_output_raster(
                fig,
                ax,
                arr,
                self.mask.arr,
                self.rp.bounds,
                title,
                ticks,
                cmap=COLORMAP_SEDIOUT,
                *args,
                **kwargs,
            )
            return fig, ax

        self._sewer_in.plot = plot

    @property
    def sedi_export(self):
        """Getter SediExport attribute.

        For documentation, see :ref:`here <watemsedem:sediexportrst>`
        """
        return self._sedi_export

    @sedi_export.setter
    def sedi_export(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sedi_export = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sewer_in.arr, required_type=np.float32)
        valid_boundaries(
            self.sedi_export.arr[self.sedi_export.arr != -9999], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "SediExport [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot for SediExport with non-linear colormap. Zeros are filtered out

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
            arr = mask_array_with_val(self.sedi_export.arr, self.sedi_export.arr, -9999)
            # mask where the river is not present
            if not self.ls:
                msg = "Assign ls to Modeloutput before plotting SediExport"
                raise NotImplementedError(msg)
            else:
                arr = np.ma.masked_where(self.ls.arr != -9999, arr)
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
                cmap=COLORMAP_SEDIOUT,
                *args,
                **kwargs,
            )
            return fig, ax

        self._sedi_export.plot = plot

    @property
    def sedi_in(self):
        """Getter SediIn attribute.

        For documentation, see :ref:`here <watemsedem:sediinrst>`
        """
        return self._sedi_in

    @sedi_in.setter
    def sedi_in(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sedi_in = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.sedi_in.arr, required_type=np.float32)
        valid_boundaries(
            self.sedi_in.arr[self.sedi_in.arr != -9999], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        title = "SediIn [kg/year]"

        def plot(
            fig=None, ax=None, ticks=[0, 10000, 20000, 40000, 80000], *args, **kwargs
        ):
            """Plot for SediIn

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
                cmap=COLORMAP_SEDIOUT,
                *args,
                **kwargs,
            )

        self._sedi_in.plot = plot

    @property
    def capacity(self):
        """Getter capacity attribute.

        For documentation, see :ref:`here <watemsedem:capacityrst>`
        """
        return self._capacity

    @capacity.setter
    def capacity(self, raster):
        """Setter

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._capacity = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.capacity.arr, required_type=np.float32)
        valid_boundaries(
            self.capacity.arr[self.capacity.arr != -9999], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "Capacity [kg/year]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot for Capacity with logarithmic colormap

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
            if not self.ls:
                msg = "Assign ls to Modeloutput before plotting Capacity"
                raise NotImplementedError(msg)
            else:
                arr = mask_array_with_val(self.capacity.arr, self.ls.arr, -9999)
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(arr, self.mask.arr, 0)
            arr = np.ma.filled(arr, np.nan)
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
            return fig, ax

        self._capacity.plot = plot

    @property
    def rusle(self):
        """Getter rusle attribute.


        For documentation, see :ref:`here <watemsedem:ruslerst>`
        """
        return self._rusle

    @rusle.setter
    def rusle(self, raster):
        """Setter

        Parameters
        ---------
        raster: pathlib.Path | str
        """
        self._rusle = self.raster_factory(raster, flag_mask=False)

        valid_array_type(self.capacity.arr, required_type=np.float32)
        valid_boundaries(
            self.capacity.arr[self.capacity.arr != -9999], lower=0, upper=None
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        title = "RUSLE [kg/(year.m²)]"

        def plot(fig=None, ax=None, ticks=None, *args, **kwargs):
            """Plot for RUSLE

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
            arr = mask_array_with_val(self.rusle.arr, self.rusle.arr, 0)
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

        self._rusle.plot = plot

    def make_routing_vector(
        self, landuse, sediout, percentile=90, routing_missing=False
    ):
        """Converts pandas dataframe of routing or routing_missing to a geopandas
        dataframe

        Parameters
        ----------
        landuse: pathlib.Path | str | str
                Path of landuse raster
        sediout: pathlib.Path | str | str
                Path of sediout raster
        percentile: int, default = 90
            Only vectors belonging to SediOutdata percentile and higher is kept
        routing_missing: bool, default = False
                        set to True to apply function to routing_missing instead
                        of routing

        Returns
        --------
        geopandas.GeoDataFrame
        """
        raster, landuse_rasterio_profile = load_raster(landuse)
        # cheks op raster
        valid_non_nan(raster)
        valid_array_type(raster, required_type=np.int16)
        valid_boundaries(raster, lower=-32757, upper=32757)
        check_raster_properties_raster_with_template(
            landuse, landuse, epsg=self.rp.epsg
        )

        # selecting what to vectorise
        sediout_arr, sediout_profile = load_raster(sediout)
        sediout_df = raster_array_to_pandas_dataframe(sediout_arr, sediout_profile)
        seditout_df_sel = sediout_df.loc[
            sediout_df["val"] > np.percentile(sediout_df["val"], percentile)
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
        df_comb = seditout_df_sel.merge(df_temp, how="left", on=["row", "col"])
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
    """Generate a routing vct routing file (added with CNWS landuse) based on
    the routing table
    extent and tilenumber are defined to make a routing file only for a
    certain extent

    Parameters
    ----------
    txt_routing: str or pathlib.Path | str
        File path of the WaTEM/SEDEM routing tabl
    rst_prckrt: str
        name of CNWS input 'perceelskaart'
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
            run_saga_make_routing_shp_cmd(txt_routing, rst_prckrt, vct_out)
            return vct_out
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
        if df_routing.empty:
            msg = f"{txt_routing.name} is empty"
            raise IOError(msg)
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
        if df_routing.empty:
            msg = f"{txt_routing.name} is empty"
            raise IOError(msg)
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


def run_saga_make_routing_shp_cmd(txt_routing, rst_prckrt, vct_out):
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
    gdf_subcatchments.to_file(vct_subcatchments)
    create_spatial_index(vct_subcatchments)

    return (
        (rst_subcatchments.parent / (rst_subcatchments.stem + ".sdat")),
        vct_subcatchments,
    )


def identify_individual_priority_catchments(
    arr_sediout,
    rst_profile,
    txt_routing_non_river,
    nmax,
    resmap=Path.cwd(),
    epsg="",
):
    """
    identify the individual priority catchments and add them to a raster
    and shapes dictionary

    Parameters
    ----------
    arr_sediout: numpy.ndarray
        numpy array format of sedout raster
    rst_profile: rasterio profile
        rasterio profile of the sedout raster
    txt_routing_nonriver: str or pathlib.Path | str
        File path of the WaTEM/SEDEM routing table
    nmax: int
        maximum number of catchment

    Returns
    -------
    subcatchmentpriority: geopandas.GeoDataFrame
        catchment shapes with number of catchment
    """

    n = 1
    id_ = 0
    # loop until break is encountered (no more pixels to cluster,
    # or a maximum number of clusters is reached)
    while True:

        # identify point with highest sediment load
        id_, max_sediout = create_id_raster_for_highest_value_arr(
            arr_sediout, id_, rst_profile, resmap=resmap / "priority_catchments"
        )

        # identify subcatchment/cluster coupled to this point
        template_name = (
            resmap / "priority_catchments" / f"subcatchments_priority_{n}.shp"
        )
        if not template_name.exists():
            rst_subcatch, vct_subcatch = define_subcatchments_saga(
                id_, txt_routing_non_river, tag=template_name
            )
            # assign sediout value to self.subcatchmprioritSHP
            gdf = gpd.read_file(vct_subcatch)
            gdf["sediout"] = max_sediout
            gdf.to_file(vct_subcatch)
        else:
            vct_subcatch = template_name
            rst_subcatch = vct_subcatch.with_suffix(".sdat")

        # condition: if a max number of clusters is identified
        # OR all pixels are classified: stop
        if (n >= nmax) | (np.sum(arr_sediout != rst_profile["nodata"]) == 0):
            nmax = n
            break
        else:
            arr_subcatch, _ = load_raster(rst_subcatch)
            arr_sediout[arr_subcatch != -99999.0] = rst_profile["nodata"]
            n += 1

    # merge different subcatchments to one file
    lst_gdf = []
    for i in Path("priority_catchments").iterdir():
        if i.suffix == ".shp":
            lst_gdf.append(gpd.read_file(i))
    gdf_subcatchmpriority = pd.concat(lst_gdf)

    gdf_subcatchmpriority.crs = {"init": epsg}
    dst = resmap / "priority_catchments.shp"
    gdf_subcatchmpriority.to_file(dst)
    create_spatial_index(dst)

    return gdf_subcatchmpriority


def create_id_raster_for_highest_value_arr(arr, id_, profile, resmap):
    """Create a raster with an id value assigned to the highest value in the raster"

    Parameters
    ----------
    arr: str or pathlib.Path | str
        with floats
    id_: int
        Sequential number of the catchment
    profile: rasterio profile
        Rasterio profile of the sedout raster
    resmap: str or pathlib.Path | str, optional
        Folder path to write results to

    Returns
    -------
    rst_id: str
        File path of the raster with id for highest value in raster
    val: float
        Maximum value in raster
    """
    resmap = Path(resmap)
    if not resmap.exists():
        (resmap).mkdir(parents=True, exist_ok=True)

    arr_id = arr.copy()
    max_val = np.max(arr)
    cond = arr == max_val
    arr_id[cond] = id_
    arr_id[~cond] = profile["nodata"]

    # write to disk
    rst_id = resmap / f"id_{id_}.rst"
    write_arr_as_rst(arr_id, rst_id, "int32", profile)

    return rst_id, max_val


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


def compute_efficiency_buffers(rst_buffer, rst_sediin, rst_sediout):
    """Compute efficiency per buffer

    This function calculates the incoming and outgoing sediment per buffer.
    The deposition is computed by substracting the outgoing from the ingoing
    sediment.

    Parameters
    ----------
    rst_buffer: str or pathlib.Path | str
        File path of buffer raster with buffer id's
    rst_sediin: str or ppathlib.Path | str
        File path of CNWS SediIn raster, incoming sediment per pixel
    rst_sediout: str or pathlib.Path | str
        File path of CNWS SediOut raster, outgoing sediment per pixel

    Returns
    -------
    df_output: pandas.DataFrame
        Holding results of mass balance of buffers.

        - *buf_id* (float): id of the buffer (as in the buffer raster)
        - *sediin* (float): total incoming sediment in the buffer.
        - *sediout* (float): total outgoing sediment in the buffer.
        - *buff_sed* (float): amount sediment deposited in the buffer.
    """
    arr_buffers, profile = load_raster(rst_buffer)
    arr_sediin, _ = load_raster(rst_sediin)
    arr_sediout, _ = load_raster(rst_sediout)

    df_out = pd.DataFrame(columns=["NR", "sediin", "sediout", "buff_sed"])
    condition = (arr_buffers < 2**14) & (arr_buffers > 0)
    arr_unique_buffer = np.unique(arr_buffers[condition])
    for buf_id in arr_unique_buffer:
        arr_sediin_buffer = np.sum(arr_sediin[arr_buffers == buf_id])
        arr_sediout_buffer = np.sum(arr_sediout[arr_buffers == buf_id])
        arr_deposition = arr_sediin_buffer - arr_sediout_buffer
        df_out.loc[df_out.shape[0] + 1] = [
            buf_id,
            arr_sediin_buffer,
            arr_sediout_buffer,
            arr_deposition,
        ]
    return df_out


def open_txt_routing_file(txt_routing):
    """Open routing file with exceptions and seperators as needed

    Parameters
    ----------
    txt_routing: str or pathlib.Path | str
        File path of the WaTEM/SEDEM routing table

    Returns
    -------
    df_routing: pandas.DataFrame
        The routing DataFrame contains the following columns:

        - *col* (int): source column in rasters
        - *row* (int): source row in rasters
        - *target1col* (int): first target column in rasters
        - *target1row* (int): first target row in rasters
        - *part1* (float): Part that flows to target1
        - *distance1* (float): Distance of 1st vector
        - *target2col* (int): second target column in rasters
        - *target2row* (int): second target row in rasters
        - *part2* (float): Part that flows to target2
        - *distance2* (float): Distance of 2nd vector
    """
    try:
        with open(txt_routing) as f:
            first_line = f.readline()
        seperator = ";" if "\t" not in first_line else "\t"
        df_routing = pd.read_csv(txt_routing, sep=seperator)
        if df_routing.empty:
            msg = f"{txt_routing.name} is empty"
            raise IOError(msg)
    except IOError:
        msg = f"'{txt_routing}' does not exist"
        return IOError(msg)

    return df_routing


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
    rst_sediexport, threshold, vct_out="rank.shp", rst_endpoints=None, unit="kg"
):
    """Rank the sediment loads in sediexport (and sewerin) from high to low

    This function uses the rank output raster/dataframe of
    :func:`pywatemsedem.io.modeloutput.identify_rank_sediment_loads`
    to map a vector point file with information on rank, sediment output.

    For computation details, see
    :func:`pywatemsedem.io.modeloutput.identify_rank_sediment_loads`

    Parameters
    ----------
    rst_sediexport: str or pathlib.Path | str
        File path of WaTEM/SEDEM sediexport raster.
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`
    vct_out: str or pathlib.Path | str
        File path of output vector.
    rst_endpoints: str or pathlib.Path | str, default None
        File path to WaTEM/SEDEM sewerin raster (endpoints in pywatemsedem).
    unit: str
        "kg" or "ton"

    Note
    ----
    Only points are taken into account that account for x of the highest sediment loads.
    x is determined by threshold.
    """
    if unit not in ["kg", "ton"]:
        f"Unit '{unit}' should be either 'kg' op 'ton'."

    rst_out = tempfile.NamedTemporaryFile(suffix=".rst").name
    df_sediexport, threshold = identify_rank_sediment_loads(
        rst_sediexport, threshold, rst_out, rst_endpoints
    )
    rst_to_vct_points(rst_out, vct_out)
    gdf_out = gpd.read_file(vct_out)
    gdf_out["rank"] = gdf_out[Path(rst_out).stem]
    gdf_out = gdf_out.merge(df_sediexport, on="rank")
    if unit == "ton":
        gdf_out["sediexport"] = gdf_out["sediexport"] / 1000
    clean_up_tempfiles(Path(rst_out), "rst")

    return gdf_out


def identify_rank_sediment_loads(
    rst_sediexport, threshold, rst_out, rst_endpoints=None
):
    """Identify the highest ``threshold`` percentage sediment loads.

    This functions identifies the cumulative distribution of the sediexport
    (and sewerin, optional) raster:

    - (optional) map sewerin  raster to sediexport raster
    - convert sediexport raster to a list-format
    - sort from high to low
    - compute cumulative distribution
    - classify

    Parameters
    ----------
    rst_sediexport: str or pathlib.Path | str
        File path to WaTEM/SEDEM sediexport raster.
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`
    rst_out: str of pathlib.Path | str
        Output raster containing ranks of highest sediment loads (1: highest,
        2: second highest, ..)
    rst_endpoints: str or pathlib.Path | str
        File path to WaTEM/SEDEM sewerin raster.

    Returns
    -------
    df_sediexport: pandas.DataFrame
        Data Frame format of SediExport raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`)
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`
    """
    arr_sediexport, profile = load_raster(rst_sediexport)
    arr_sediexport = np.where(arr_sediexport == profile["nodata"], 0, arr_sediexport)

    if rst_endpoints is not None:
        arr_sewerin, _ = load_raster(rst_endpoints)
        arr_sewerin = np.where(arr_sewerin == profile["nodata"], 0, arr_sewerin)
        arr_sediexport += arr_sewerin

    df_sediexport = raster_array_to_pandas_dataframe(arr_sediexport, profile)
    profile["driver"] = "GTiff"

    # sort and select points
    df_sediexport, threshold = compute_cumulative_loads_in_sinks(
        df_sediexport, profile, threshold, plot=False
    )
    arr_sediexport = raster_dataframe_to_arr(df_sediexport, profile, "rank", np.float32)

    write_arr_as_rst(
        arr_sediexport,
        rst_out,
        "float32",
        profile,
    )

    return df_sediexport, threshold


def compute_cumulative_loads_in_sinks(
    df_sediexport, profile, threshold, delta=10, plot=False
):
    """Analyse cumulative sediment load by sorting SediExport values
    from high to low

    Parameters
    ----------
    df_sediexport: pandas.DataFrame
        Data Frame format of SediExport raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`)
    profile: rasterio.profiles
        See :func:`rasterio.open`
    threshold: int
        x percentage highest load that the user wants to analyse
    delta: int
        Delta used to iterate percentage
    plot: bool, default False
        True if you want a cumulative SediExport plot

    Returns
    -------
    df_sediexport: pandas.DataFrame
        Data Frame format of SediExport raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`) added
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
    df_sediexport.loc[cond, "cum_sum"] = df_sediexport.loc[cond, "sediexport"].cumsum()
    df_sediexport.loc[cond, "cum_perc"] = (
        100
        * df_sediexport.loc[cond, "cum_sum"]
        / df_sediexport.loc[cond, "sediexport"].sum()
    )

    if plot:
        plot_cumulative_sedimentload(
            df_sediexport.loc[cond],
            threshold,
            "cumulative_sediexport.png",
        )

    # hotfix on percentage: if the first percentage is higher than the
    # user-predefined percentage, adjust it (small catchments)!
    threshold = verify_highest_load_with_threshold(df_sediexport, threshold)

    # prepare ids for subcatchment delineation
    df_sediexport["rank"] = profile["nodata"]
    df_sediexport["class"] = profile["nodata"]

    # assign unique id's - in order of importance - to records
    cond = (df_sediexport["cum_perc"] <= threshold) & (
        ~df_sediexport["cum_perc"].isnull()
    )
    df_sediexport.loc[cond, "rank"] = np.arange(np.sum(cond)) + 1

    # calculate percentage
    df_sediexport["perc"] = [
        df_sediexport["cum_perc"].iloc[i] - df_sediexport["cum_perc"].iloc[i - 1]
        if i != 0
        else df_sediexport["cum_perc"].iloc[i]
        for i in range(0, len(df_sediexport))
    ]

    # chekc if begin percentage is below delta_perc
    bperc = delta
    eperc = int(threshold + 1)
    if df_sediexport["cum_perc"].iloc[0] > bperc:
        bperc = int(np.ceil(df_sediexport["cum_perc"].iloc[0] / 10) * 10)

    for i in range(bperc, eperc, delta):
        cond = (
            (df_sediexport["cum_perc"] > i - delta)
            & (df_sediexport["cum_perc"] <= i)
            & (~df_sediexport["cum_perc"].isnull())
        )
        df_sediexport.loc[cond, "class"] = i

    return (
        df_sediexport[
            ["col", "row", "rank", "perc", "cum_perc", "class", "sediexport"]
        ],
        int(threshold),
    )


def verify_highest_load_with_threshold(df_sediexport, threshold):
    """Verify whether that the highest load is not accountable for more than 50 percent
    of all the load in a catchment. If this is true, adapt threshold.

    Parameters
    ----------
    df_sediexport: pandas.DataFrame
        Data Frame format of SediExport raster (format: see
        :func:`pywatemsedem.pywatemsedem.utils.raster_array_to_pandas_dataframe`)
    threshold: float
        See :func:`pywatemsedem.io.modeloutput.compute_cumulative_loads_in_sinks`

    Returns
    -------
    threshold_: float
        Adapted threshold (depending on if-else clause).
    """
    cum_sum_sinks0 = df_sediexport["cum_perc"].iloc[0]

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
    """Load the total sediment file of CNWS written in CNWS dict_output map

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
