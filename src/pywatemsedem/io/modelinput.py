from dataclasses import dataclass

import matplotlib as mpl
import numpy as np
import pandas as pd

# hvplot functionalities
from matplotlib import colors

from pywatemsedem.geo.factory import Factory
from pywatemsedem.geo.utils import (
    check_raster_properties_raster_with_template,
    mask_array_with_val,
)
from pywatemsedem.io.plots import (
    axes_creator,
    plot_continuous_raster,
    plot_discrete_raster,
)
from pywatemsedem.io.valid import (
    valid_array_type,
    valid_boundaries,
    valid_nodata,
    valid_non_nan,
    valid_values,
)

IMPLEMENTED_RASTER_TYPES = [np.int16, np.int32, np.int64, np.float32, np.float64]
COLORMAP = "cividis"


def valid_segments(func):
    """Check if you have defined a river segments raster."""

    def wrapper(self, *args, **kwargs):
        if self._riversegments.is_empty():
            msg = (
                f"Please first define WaTEM/SEDEM river segments, see "
                f"{Modelinput.riversegments}!"
            )
            raise IOError(msg)
        return func(self, *args, **kwargs)

    return wrapper


@dataclass
class Modelinput(Factory):
    def __init__(self, template, resolution, epsg, nodata):
        """AbstractRaster class with model inputs as attributes. Modelinput class
        serves the goal of automating the reading in, checking and visualisation
        of the input data of the WaTEM/SEDEM model.

        Parameters
        ----------
        template: pathlib.Path | str
            Template raster needed to extract raster properties.
            Raster contains values in [0,1]. Values in ]0,1] define the catchment.
        resolution: int
            See :class:`pywatemsedem.geo.RasterProperties`
        epsg: int
            See :class:`pywatemsedem.geo.RasterProperties`.
        nodata: int
            See :class:`pywatemsedem.geo.RasterProperties`.
        """
        # apply factory and set mask
        super().__init__(resolution, epsg, nodata, template.parent)
        self.mask = template

        # DATA
        self._cfactor = None  # attribute
        self._buffers = None
        self._dtm = None
        self._kfactor = None
        self._ktc = None
        self._outlet = None
        self._pfactor = None
        self._compositelanduse = None
        self._ptef = None
        self._riversegments = None
        self._riverrouting = None
        self._sewers = None
        self._upstreamsegments = None
        self._adjacentsegments = None

    @property
    def cfactor(self):
        """Getter cfactor attribute.

        For documentation, see :ref:`here <watemsedem:cmap>`
        """
        return self._cfactor

    @cfactor.setter
    def cfactor(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._cfactor = self.raster_factory(raster, flag_mask=False)
        # checks on raw raster data
        valid_non_nan(self.cfactor.arr)
        valid_array_type(self.cfactor.arr, required_type=np.float32)
        lower, upper = 0, 1
        valid_boundaries(
            self.cfactor.arr[self.cfactor.arr != self.rp.nodata],
            lower=lower,
            upper=upper,
        )
        check_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for _cfactor with cividis as colormap

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.cfactor.arr, self.mask.arr, 0)
            fig, ax = plot_continuous_raster(
                fig, ax, arr, self.rp.bounds, vmin=lower, vmax=upper, *args, **kwargs
            )
            ax.set_title("C-factor [-]")
            return fig, ax

        self._cfactor.plot = plot

    @property
    def buffers(self):
        """Getter buffers attribute.

        For documentation, see :ref:`here <watemsedem:buffermap>`
        """
        return self._buffers

    @buffers.setter
    def buffers(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._buffers = self.raster_factory(raster, flag_mask=False)
        # checks on raster data
        valid_non_nan(self.buffers.arr)
        valid_array_type(self.buffers.arr, required_type=np.int16)
        valid_boundaries(self.buffers.arr, lower=0, upper=None)
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        labels = ["No buffer", "Buffer"]

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for buffers

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.buffers.arr, self.mask.arr, 0)
            # binary plotting: if larger than 0, it is a buffer id!
            arr[arr > 0] = 1  # binary plotting!
            fig, ax = plot_discrete_raster(
                fig, ax, arr, self.rp.bounds, labels, *args, **kwargs
            )
            ax.set_title("Buffers")
            return fig, ax

        self._buffers.plot = plot

    @property
    def dtm(self):
        """Getter dtm attribute.

        For documentation, see :ref:`here <watemsedem:dtmmap>`
        """
        return self._dtm

    @dtm.setter
    def dtm(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._dtm = self.raster_factory(raster, flag_mask=False)
        # checks on raster data
        valid_non_nan(self.dtm.arr)
        valid_array_type(self.dtm.arr, required_type=np.float32)
        # crucial that code does NOT run when nodata values detected!
        valid_nodata(self.dtm.arr, nodata_value=-9999)
        valid_nodata(self.dtm.arr, nodata_value=-99999)
        valid_boundaries(self.dtm.arr, lower=-431, upper=9000)
        # +- lowest and highest points on earth
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for DTM with cividis as colormap

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.dtm.arr, self.mask.arr, 0)
            fig, ax = plot_continuous_raster(
                fig, ax, arr, self.rp.bounds, *args, **kwargs
            )
            ax.set_title("DTM [m MSL]")
            return fig, ax

        self._dtm.plot = plot

    @property
    def kfactor(self):
        """Getter kfactor attribute.
        For documentation, see :ref:`here <watemsedem:kmap>`
        """
        return self._kfactor

    @kfactor.setter
    def kfactor(self, raster_input):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        raster = self.raster_factory(raster_input, flag_mask=False)
        # checks on raster data
        valid_non_nan(raster.arr)
        # NO need for checking no data, deal with this in plotting!
        valid_array_type(raster.arr, required_type=np.int16)
        valid_boundaries(
            raster.arr[raster.arr != -9999], lower=0, upper=None
        )  # No data value excluded from check
        valid_raster_properties_raster_with_template(
            self.rp, raster_input, epsg=self.rp.epsg
        )
        self._kfactor = raster

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for K-factor with cividis as colormap

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.kfactor.arr, self.mask.arr, 0)
            fig, ax = plot_continuous_raster(
                fig, ax, arr, self.rp.bounds, *args, **kwargs
            )
            ax.set_title("K-factor [kg.h]/[MJ.mm]")
            return fig, ax

        self._kfactor.plot = plot

    @property
    def ktc(self):
        """Getter kTC parameter attribute.

        For documentation, see :ref:`here <watemsedem:ktcmap>`
        """
        return self._ktc

    @ktc.setter
    def ktc(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._ktc = self.raster_factory(raster, flag_mask=False)
        # checks on raster data
        valid_non_nan(self.ktc.arr)
        valid_array_type(self.ktc.arr, required_type=np.float32)
        valid_boundaries(
            self.ktc.arr[self.ktc.arr != 9999], lower=0, upper=20
        )  # 0 to 20 if not nodata
        valid_values(self.ktc.arr[self._ktc.arr > 20], [9999])
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        label = ["9999"]

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for kTC parameter with cividis as colormap

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.ktc.arr, self.mask.arr, 0)
            arr_nodata = mask_array_with_val(arr, arr, 9999)
            fig, ax = plot_continuous_raster(
                fig, ax, arr_nodata, self.rp.bounds, *args, **kwargs
            )
            arr_only_nodata = np.ma.masked_where(arr != 9999, arr)
            fig, ax = plot_discrete_raster(
                fig, ax, arr_only_nodata, self.rp.bounds, label, "Set1"
            )
            ax.set_title("kTC [m]")
            return fig, ax

        self._ktc.plot = plot

    @property
    def outlet(self):
        """Getter outlet attribute.

        For documentation, see :ref:`here <watemsedem:outletmap>`
        """
        return self._outlet

    @outlet.setter
    def outlet(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._outlet = self.raster_factory(raster, flag_mask=False)
        # checks on raster data
        valid_non_nan(self.outlet.arr)
        valid_nodata(self.outlet.arr)
        valid_array_type(self.outlet.arr, required_type=np.int16)
        valid_values(self.outlet.arr, unique_values=[0, 1])
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

    @property
    def pfactor(self):
        """Getter P-factor attribute.

        For documentation, see :ref:`here <watemsedem:pmap>`
        """
        return self._pfactor

    @pfactor.setter
    def pfactor(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._pfactor = self.raster_factory(raster, flag_mask=False)
        # checks on raster data
        valid_non_nan(self.pfactor.arr)
        valid_nodata(self.pfactor.arr)  # since only binary values of use!
        lower, upper = 0, 1
        valid_boundaries(self.pfactor.arr, lower=lower, upper=upper)
        valid_array_type(self.pfactor.arr, required_type=np.float32)
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for P-factor

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.pfactor.arr, self.mask.arr, None)
            fig, ax = plot_continuous_raster(
                fig, ax, arr, self.rp.bounds, vmin=lower, vmax=upper, *args, **kwargs
            )
            ax.set_title("P-factor [-]")
            return fig, ax

        self._pfactor.plot = plot

    @property
    def compositelanduse(self):
        """Getter landuseparcels attribute.

        For documentation, see :ref:`here <watemsedem:prcmap>`
        """
        return self._compositelanduse

    @compositelanduse.setter
    def compositelanduse(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._compositelanduse = self.raster_factory(raster, flag_mask=False)

        # checks
        valid_non_nan(self.compositelanduse.arr)
        valid_array_type(self.compositelanduse.arr, required_type=np.int16)
        valid_boundaries(self.compositelanduse.arr, lower=-32757, upper=32757)
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        # custom plotting features
        colormap = colors.ListedColormap(
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
        labels = [
            "Grass strips (-6)",
            "Pools (-5)",
            "Meadow (-4)",
            "Forest (-3)",
            "Infrastructure (-2)",
            "River (-1)",
            "Outside boundaries (0)",
            "Agriculture (>0)",
        ]

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for Landuseparecles

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.compositelanduse.arr, self.mask.arr, 0)
            arr[arr > 0] = 1
            fig, ax = plot_discrete_raster(
                fig, ax, arr, self.rp.bounds, labels, colormap, *args, **kwargs
            )
            ax.set_title("Land use parcels")
            return fig, ax

        self._compositelanduse.plot = plot

    @property
    def ptef(self):
        """Getter ptef attribute.

        For documentation, see :ref:`here <watemsedem:parceltrapppingcrop>`
        """
        return self._ptef

    @ptef.setter
    def ptef(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._ptef = self.raster_factory(raster, flag_mask=False)
        # checks on raster data
        valid_non_nan(self.ptef.arr)
        valid_array_type(self.ptef.arr, required_type=np.int16)
        # int16, maar waarom niet float32?
        lower, upper = 0, 100
        valid_boundaries(self.ptef.arr, lower=lower, upper=upper)
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for PTEF

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.ptef.arr, self.mask.arr, 0)
            fig, ax = plot_continuous_raster(
                fig, ax, arr, self.rp.bounds, vmin=lower, vmax=upper, *args, **kwargs
            )
            ax.set_title("PTEF [%]")
            return fig, ax

        self._ptef.plot = plot

    @property
    def riversegments(self):
        """Getter riversegments attribute.

        For documentation, see :ref:`here <watemsedem:riversegmentfile>`
        """
        return self._riversegments

    @riversegments.setter
    def riversegments(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._riversegments = self.raster_factory(raster, flag_mask=False)

        # checks
        valid_non_nan(self.ptef.arr)
        valid_array_type(self.ptef.arr, required_type=np.int16)
        valid_boundaries(self.ptef.arr, lower=0, upper=None)
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for riversegments

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.riversegments.arr, self.mask.arr, 0)
            arr_only_rivers = np.ma.masked_where(arr == 0, arr)
            fig, ax = plot_continuous_raster(
                fig, ax, arr_only_rivers, self.rp.bounds, *args, **kwargs
            )
            arr_only_norivers = np.ma.masked_where(arr != 0, arr)
            fig, ax = plot_continuous_raster(
                fig,
                ax,
                arr_only_norivers,
                self.rp.bounds,
                cmap="summer",
                colorbar=False,
                alpha=0.8,
            )
            ax.set_title("Riversegments")

            return fig, ax

        self._riversegments.plot = plot

    @property
    def riverrouting(self):
        """Getter riverrouting attribute.

        For documentation, see :ref:`here <watemsedem:routingmap>`
        """
        return self._riverrouting

    @riverrouting.setter
    def riverrouting(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._riverrouting = self.raster_factory(raster, flag_mask=False)

        # checks
        valid_non_nan(self.riverrouting.arr)
        valid_array_type(self.riverrouting.arr, required_type=np.int16)
        valid_values(
            self.riverrouting.arr[self.riverrouting.arr != -9999],
            unique_values=np.arange(0, 9).tolist(),
        )
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)
        colormap_start = mpl.cm.get_cmap("tab10")
        colorlist = []
        for i in range(0, 9):
            color = mpl.colors.rgb2hex(colormap_start(i))
            colorlist.append(color)
        colormap_routing = colors.ListedColormap(colorlist)
        labels = [
            "0 (no routing)",
            "1 (North)",
            "2 (NorthEast)",
            "3 (East)",
            "4 (SouthEast)",
            "5 (South)",
            "6 (SouthWest)",
            "7 (West)",
            "8 (NorthWest)",
        ]
        np.arange(0, 9).tolist()

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for riverrouting

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.riverrouting.arr, self.mask.arr, 0)
            arr[arr == -9999] = 0  # no routing
            fig, ax = plot_discrete_raster(
                fig, ax, arr, self.rp.bounds, labels, colormap_routing, *args, **kwargs
            )
            ax.set_title("Riverrouting")
            return fig, ax

        self._riverrouting.plot = plot

    @property
    def sewers(self):
        """Getter sewers attribute.

        For documentation, see :ref:`here <watemsedem:sewermapfile>`
        """
        return self._sewers

    @sewers.setter
    def sewers(self, raster):
        """Setter

        Parameters
        ----------
        raster: pathlib.Path | str
        """
        self._sewers = self.raster_factory(raster, flag_mask=False)

        # checks
        valid_non_nan(self.sewers.arr)
        valid_array_type(self.sewers.arr, required_type=np.float32)
        lower, upper = 0, 1
        valid_boundaries(self.sewers.arr, lower=lower, upper=upper)
        valid_raster_properties_raster_with_template(self.rp, raster, epsg=self.rp.epsg)

        def plot(fig=None, ax=None, *args, **kwargs):
            """Plot for sewers

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
            fig, ax = axes_creator(fig, ax)
            arr = mask_array_with_val(self.sewers.arr, self.mask.arr, 0)
            fig, ax = plot_continuous_raster(
                fig, ax, arr, self.rp.bounds, vmin=lower, vmax=upper, *args, **kwargs
            )
            ax.set_title("Fraction of sediment in sewers")

            return fig, ax

        self._sewers.plot = plot

    @property
    def upstreamsegments(self):
        """Getter upstreamsegments dataframe.

        For documentation, see :ref:`here <watemsedem:upstrsegments>`
        """
        return self._upstreamsegments

    @upstreamsegments.setter
    @valid_segments
    def upstreamsegments(self, text):
        """Setter

        Parameters
        ----------
        text: pathlib.Path | str
        """
        self._upstreamsegments = pd.read_table(text)
        # checks
        array = self.upstreamsegments[["line_id", "upstream_line"]].values
        valid_non_nan(array)
        valid_values(array, unique_values=np.unique(self.riversegments.arr).tolist())
        valid_array_type(array, required_type=np.int64)

    @property
    def adjacentsegments(self):
        """Getter adjacentsegments dataframe.

        For documentation, see :ref:`here <watemsedem:adjsegments>`
        """
        return self._adjacentsegments

    @adjacentsegments.setter
    @valid_segments
    def adjacentsegments(self, text):
        """Setter

        Parameters
        ----------
        text: pathlib.Path | str
        """
        self._adjacentsegments = pd.read_table(text)
        # checks
        array = self.adjacentsegments.values
        valid_non_nan(array)
        valid_values(array, unique_values=np.unique(self.riversegments.arr).tolist())
        valid_array_type(array, required_type=np.int64)
