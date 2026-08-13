from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio

from pywatemsedem.defaults import ALLOWED_RASTER_FORMATS
from pywatemsedem.geo.rasterproperties import RasterProperties
from pywatemsedem.geo.utils import (
    clean_up_tempfiles,
    clip_rst,
    create_filename,
    load_raster,
    mask_array_with_val,
    set_no_data_arr,
    tiff_to_idrisi,
    write_arr_as_rst,
)


class AbstractRaster:
    """Abstract raster class based on numpy arrays and raster properties.

    Attributes
    ----------
    arr : numpy.ndarray
        Raster array.
    rp : pywatemsedem.geo.rasterproperties.RasterProperties
        Raster properties instance.

    Notes
    -----
    If an array mask is provided to the initialize method, the array is
    automatically masked.
    """

    def __init__(self):

        self._arr = None
        self._rp = None

    def initialize(self, arr, rp, arr_mask=None, allow_nodata_array=False):
        """Initialize array and raster properties.

        Parameters
        ----------
        arr : numpy.ndarray
            Raster array.
        rp : pywatemsedem.geo.rasterproperties.RasterProperties
            Raster properties instance.
        arr_mask : numpy.ndarray, default None
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.
        allow_nodata_array : bool, default False
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.
        """
        if len(arr.shape) < 2:
            msg = "Dimensionality of input raster array should be larger than 1."
            raise ValueError(msg)
        self._arr = arr
        self._rp = rp
        if arr_mask is not None:
            self.mask(arr_mask, allow_nodata_array)

    @property
    def arr(self):
        """Return array.

        Returns
        -------
        numpy.ndarray
            Raster array.
        """
        return self._arr

    @arr.setter
    def arr(self, input):
        """Set array.

        Parameters
        ----------
        input : numpy.ndarray
            Raster array.
        """
        self._arr = input

    @property
    def rp(self):
        """Return raster properties.

        Returns
        -------
        pywatemsedem.geo.rasterproperties.RasterProperties
            Raster properties instance.
        """
        return self._rp

    def update_nodata_value(self, to):
        """Update the nodata value.

        Parameters
        ----------
        to : float
            New nodata value.
        """
        self._arr[self._arr == self.rp.nodata] = to
        self._rp._nodata = to

    def clip(self):
        """Clip function (not implemented).

        Raises
        ------
        NotImplementedError
            This method is not implemented in the abstract class.
        """
        raise NotImplementedError

    def mask(self, arr_mask, allow_nodata_array=False):
        """Mask the raster array.

        Parameters
        ----------
        arr_mask : numpy.ndarray
            Array mask (1, nodata). Note that array mask should have same nodata
            value as raster array.
        allow_nodata_array : bool, default False
            Allow to return a nodata-array.
        """
        try:
            self._arr = set_no_data_arr(self._arr, arr_mask, self.rp.nodata)
        except ValueError:
            if allow_nodata_array:
                self._arr = self.rp.nodata * np.ones(self._arr.shape)
            else:
                self._arr = set_no_data_arr(self._arr, arr_mask, self.rp.nodata)

    def write(self, outfile_path, format="idrisi", dtype=None, nodata=None):
        """Write raster data to disk.

        Parameters
        ----------
        outfile_path : pathlib.Path or str
            File path output.
        format : str, default "idrisi"
            Output format, either "idrisi" or "tiff".
        dtype : numpy.dtype, default None
            Output raster type. If None, dtype of array is used.
        nodata : float, default None
            Nodata value for output raster. If None, nodata of rasterproperties
            is used.

        Returns
        -------
        bool
            True if write was successful.

        Raises
        ------
        NotImplementedError
            If format is not supported.
        TypeError
            If file extension does not match format.
        """
        outfile_path = Path(outfile_path)

        if format not in ALLOWED_RASTER_FORMATS:
            msg = (
                f"Format '{format}' not implemented in pywatemsedem. Use "
                f"{' or '.join(ALLOWED_RASTER_FORMATS)}"
            )
            raise NotImplementedError(msg)

        # check for extension and format
        if format == "idrisi":
            if outfile_path.suffix != ".rst":
                msg = (
                    f"Can not write file ('{outfile_path}')  in format 'idrisi'"
                    f" with '{outfile_path.suffix}' extension."
                )
                raise TypeError(msg)
        elif format == "tiff":
            if outfile_path.suffix != ".tif":
                msg = (
                    f"Can not write file ('{outfile_path}')  in format "
                    f"'tiff'"
                    f" with '{outfile_path.suffix}' extension."
                )
                raise TypeError(msg)

        if dtype is None:
            dtype = self._arr.dtype

        profile = self.rp.rasterio_profile.copy()
        if nodata is not None:
            profile["nodata"] = nodata

        if format == "tiff":
            write_arr_as_rst(
                self._arr,
                outfile_path,
                dtype,
                profile,
            )
        elif format == "idrisi":
            tiff_temp = create_filename(".tif")
            write_arr_as_rst(self._arr, tiff_temp, dtype, profile)
            tiff_to_idrisi(tiff_temp, outfile_path, dtype=dtype)
            clean_up_tempfiles(tiff_temp, "tiff")

        return True

    def plot(self, fig=None, ax=None, nodata=None, *args, **kwargs):
        """Plot raster array with imshow.

        Parameters
        ----------
        fig : matplotlib.figure.Figure, default None
            If not given, defaults to generating new figure.
        ax : matplotlib.axes.Axes, default None
            If not given, defaults to generating new axis.
        nodata : float, default None
            Used to mask certain values present in arr which represent
            nodata (e.g. -9999).
        *args
            Additional positional arguments passed to imshow.
        **kwargs
            Additional keyword arguments passed to imshow.

        Returns
        -------
        fig : matplotlib.figure.Figure
            Figure object.
        ax : matplotlib.axes.Axes
            Axes object.
        """

        if not ax:
            fig, ax = plt.subplots(figsize=[10, 10])
        arr = mask_array_with_val(self.arr, self.arr, nodata)
        im = ax.imshow(arr, *args, **kwargs)
        plt.colorbar(im, ax=ax, orientation="vertical", shrink=0.5)

        return fig, ax

    def histogram(
        self, fig=None, ax=None, nodata=None, ylogscale=False, *args, **kwargs
    ):
        """Plot density histogram of raster data values.

        Plots histogram with 25th, 50th and 75th percentiles.

        Parameters
        ----------
        fig : matplotlib.figure.Figure, default None
            If not given, defaults to generating new figure.
        ax : matplotlib.axes.Axes, default None
            If not given, defaults to generating new axis.
        nodata : float, default None
            Used to mask no data values.
        ylogscale : bool, default False
            Log transformation on density axis if True.
        *args
            Additional positional arguments passed to hist.
        **kwargs
            Additional keyword arguments passed to hist.

        Returns
        -------
        fig : matplotlib.figure.Figure
            Figure object.
        ax : matplotlib.axes.Axes
            Axes object.
        """
        if not ax:
            fig, ax = plt.subplots(figsize=[10, 10])
        arr = self.arr.copy()
        if nodata is not None:
            arr = np.ma.masked_where(arr == nodata, arr)
            arr = np.ma.compressed(arr)  # fixes histogram
        arr_flat = arr.flatten()
        y, x, _ = ax.hist(arr_flat, bins="doane", density=True, *args, **kwargs)
        if ylogscale:
            ax.set_yscale("log")
        colors = ["green", "orange", "red"]
        for i, p in enumerate([25, 50, 75]):
            ax.vlines(
                np.percentile(arr.flatten(), p),
                ymin=0,
                ymax=np.max(y),
                label="p" + str(p),
                colors=colors[i],
            )
        ax.legend()
        ax.set_ylabel("density")
        return fig, ax

    def is_empty(self):
        """Check if array (raster) is None (empty).

        Returns
        -------
        bool
            True if array is None, False otherwise.
        """
        return self._arr is None


@dataclass
class RasterMemory(AbstractRaster):
    """Raster stored in memory from a numpy array.

    Attributes
    ----------
    arr : numpy.ndarray
        Raster array.
    rp : pywatemsedem.geo.rasterproperties.RasterProperties
        Raster properties instance.

    Notes
    -----
    Inherits from :class:`pywatemsedem.geo.rasters.AbstractRaster`.
    """

    def __init__(self, arr, rp, arr_mask=None, allow_nodata_array=False):
        """Initialize RasterMemory.

        Parameters
        ----------
        arr : numpy.ndarray
            Raster array.
        rp : pywatemsedem.geo.rasterproperties.RasterProperties
            Raster properties instance.
        arr_mask : numpy.ndarray, default None
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.
        allow_nodata_array : bool, default False
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.
        """
        super().initialize(
            arr, rp, arr_mask=arr_mask, allow_nodata_array=allow_nodata_array
        )

    def clip(self):
        """Clip function (not implemented for RasterMemory).

        Raises
        ------
        NotImplementedError
            Clipping is not implemented for RasterMemory class.
        """
        raise NotImplementedError("Clipping not implemented for RasterMemory class")


class RasterFile(AbstractRaster):
    """Raster loaded from an input raster file.

    Attributes
    ----------
    arr : numpy.ndarray
        Raster array.
    rp : pywatemsedem.geo.rasterproperties.RasterProperties
        Raster properties instance.
    file_path : pathlib.Path
        File path to user input raster.

    Notes
    -----
    If rasterproperties are provided by the user, clipping is automatically done.
    Inherits from :class:`pywatemsedem.geo.rasters.AbstractRaster`.
    """

    def __init__(self, file_path, rp=None, arr_mask=None, allow_nodata_array=False):
        """Initialize RasterFile.

        Parameters
        ----------
        file_path : pathlib.Path
            File path to user input raster.
        rp : pywatemsedem.geo.rasterproperties.RasterProperties, default None
            Raster properties instance. If None, rasterproperties from input
            file are used.
        arr_mask : numpy.ndarray, default None
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.
        allow_nodata_array : bool, default False
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.
        """

        self.file_path = Path(file_path)

        if rp:
            with rasterio.open(file_path) as src:
                rst_profile = src.profile
            if rst_profile["driver"] == "RST":
                rst_profile["crs"] = None
            if rst_profile["crs"] is not None:
                if rst_profile["crs"].to_epsg() != rp.epsg:
                    msg = (
                        f"EPSG-code of {file_path} ({rst_profile['crs']}) should "
                        f"be same as epsg of input raster properties ({rp.epsg})."
                    )
                    raise IOError(msg)
            arr = self.clip(file_path, rp)
        else:
            if file_path.suffix == ".sgrd":
                file_path = file_path.with_suffix(".sdat")
            arr, profile = load_raster(file_path)
            rp = RasterProperties.from_rasterio(profile)

        super().initialize(arr, rp, arr_mask, allow_nodata_array)

    @staticmethod
    def clip(file_path, rp, resample="mode"):
        """Clip raster to specified extent.

        Parameters
        ----------
        file_path : pathlib.Path
            File path to user input raster.
        rp : pywatemsedem.geo.rasterproperties.RasterProperties
            Raster properties instance defining the clip extent.
        resample : str, default "mode"
            Resampling method, either "near" or "mode".
            See :func:`pywatemsedem.geo.utils.clip_rst`.

        Returns
        -------
        numpy.ndarray
            Clipped array.

        Raises
        ------
        IOError
            If clipped output raster is empty.

        Notes
        -----
        Clipping also provides resampling to another resolution.
        See :func:`pywatemsedem.geo.utils.clip_rst`.
        """
        rst_temp = create_filename(".rst")
        clip_rst(
            file_path,
            rst_temp,
            rp.gdal_profile,
            resampling=resample,
        )
        arr, profile = load_raster(rst_temp)
        shape = arr[arr != profile["nodata"]].shape
        clean_up_tempfiles(rst_temp, "rst")

        if shape == (0,):
            msg = (
                f"Clipped output raster is empty. Make sure your input raster covers "
                f"your defined spatial extent (bounds: {rp.bounds}, resolution:"
                f" {rp.resolution}, espg: {rp.epsg})."
            )
            raise IOError(msg)

        return arr


class TemporalRaster:
    """3-D raster with spatial x and y dimensions and a temporal dimension.

    The first two dimensions are spatial (x, y), and the third dimension is
    temporal.

    Attributes
    ----------
    arr : numpy.ndarray
        3D raster array.
    rp : pywatemsedem.geo.rasterproperties.RasterProperties
        Raster properties instance.

    Notes
    -----
    This class only works with array inputs.
    """

    def __init__(self, arr, rp, arr_mask=None):
        """Initialize TemporalRaster.

        Parameters
        ----------
        arr : numpy.ndarray
            3D raster array.
        rp : pywatemsedem.geo.rasterproperties.RasterProperties
            Raster properties instance.
        arr_mask : numpy.ndarray, default None
            See :func:`pywatemsedem.geo.rasters.AbstractRaster.mask`.
        """
        if len(arr.shape) != 3:
            msg = "Dimensionality of temporal raster array should be equal to 3."
            raise ValueError(msg)
        self._arr = arr
        self._rp = rp
        self._arr_mask = arr_mask

    @property
    def arr(self):
        """Return array.

        Returns
        -------
        numpy.ndarray
            3D raster array.
        """
        return self._arr

    def write(self, outfiles, format="idrisi", dtype=None):
        """Write temporal raster data to disk.

        Parameters
        ----------
        outfiles : list or tuple of pathlib.Path or str
            List of output files, one for each temporal slice.
        format : str, default "idrisi"
            Output format. See :func:`pywatemsedem.geo.rasters.AbstractRaster.write`.
        dtype : numpy.dtype, default None
            Output raster type. See
            :func:`pywatemsedem.geo.rasters.AbstractRaster.write`.

        Returns
        -------
        bool
            True if write was successful.

        Raises
        ------
        ValueError
            If number of output files does not match temporal dimension.
        """
        if len(outfiles) != self._arr.shape[-1]:
            msg = (
                f"Number of outputfiles ('{outfiles}') should be equal to number of "
                f"arrays in the third dimension('{self._arr.shape[2]}')."
            )
            raise ValueError(msg)

        for i in range(self._arr.shape[-1]):
            rm = RasterMemory(self._arr[:, :, i], self._rp, arr_mask=self._arr_mask)
            rm.write(outfiles[i], format, dtype)

        return True

    def plot(self, nodata=None, *args, **kwargs):
        """Plot raster sequentially in columns.

        Parameters
        ----------
        nodata : float, default None
            Used to mask no data values.
        *args
            Additional positional arguments passed to plot.
        **kwargs
            Additional keyword arguments passed to plot.
        """
        shape = self._arr.shape[-1]
        fig, ax = plt.subplots(ncols=shape, figsize=[10, 5 * shape])
        for i in range(shape):
            rm = RasterMemory(self._arr[:, :, i], self._rp, arr_mask=self._arr_mask)
            ax_i = ax[i] if shape > 1 else ax
            rm.plot(ax_i, nodata=nodata, *args, **kwargs)
