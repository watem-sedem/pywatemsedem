import tempfile

import numpy as np
import pytest
from conftest import geodata

from pywatemsedem.geo.rasterproperties import RasterProperties
from pywatemsedem.geo.rasters import RasterFile, RasterMemory, TemporalRaster
from pywatemsedem.geo.utils import load_raster


def test_rastermemory():
    """Test functionalities of RasterMemory class"""

    # mask a certain part of the raster.
    arr, profile = load_raster(geodata.rst_example)
    arr_mask, profile_mask = load_raster(geodata.rst_mask)

    # rasterproperties
    rp = RasterProperties.from_rasterio(profile)
    raster = RasterMemory(arr, rp)

    # test write
    tiff_temp = tempfile.NamedTemporaryFile(suffix=".tif").name
    assert raster.write(tiff_temp, format="tiff", dtype=np.float64)
    tiff_temp = tempfile.NamedTemporaryFile(suffix=".rst").name
    assert raster.write(tiff_temp, dtype=np.int32)
    assert raster.write(tiff_temp, dtype="int32")
    with pytest.raises(NotImplementedError) as excinfo:
        raster.write(tiff_temp, format="test")
    assert "Format 'test' not implemented in pywatemsedem." in str(excinfo.value)
    # enable mask to be in same nodata
    arr_mask = arr_mask.astype(np.float64)
    # feed wrong format
    with pytest.raises(TypeError) as excinfo:
        raster.write(tiff_temp, format="tiff")
    assert "in format 'tiff' with '.rst' extension." in str(excinfo.value)

    assert raster.arr.shape[0] == 286
    assert raster.arr.shape[1] == 458
    raster.mask(arr_mask)
    assert rp.nodata in raster.arr

    # mask array has wrong size
    arr_mask_w = np.vstack([arr_mask, arr_mask[-1, :]])
    with pytest.raises(IOError) as excinfo:
        raster = RasterMemory(arr, rp)
        raster.mask(arr_mask_w)
    assert "Mask array has different size from input array" in str(excinfo.value)

    # wrong values in mask
    arr_mask[arr_mask == 1] = 2
    arr_mask[arr_mask == rp.nodata] = 100
    with pytest.raises(ValueError) as excinfo:
        raster = RasterMemory(arr, rp)
        raster.mask(arr_mask)
    assert "Mask array should have values 1 (no mask) and" in str(excinfo.value)

    # mask leads to a nodata raster
    arr_mask = np.zeros(raster.arr.shape, dtype=np.float32)
    arr_mask[0, 0] = 1
    arr = raster.arr
    arr[0, 0] = rp.nodata
    with pytest.raises(ValueError) as excinfo:
        raster = RasterMemory(arr, rp)
        raster.mask(arr_mask)
    assert (
        "Array after masking has only nodata values/is empty. Please check your "
        "mask/input array." in str(excinfo.value)
    )

    # feed wrong number of dimensions
    arr = raster.arr.flatten()  # flatten to make raster 2 to 1-D.
    with pytest.raises(ValueError) as excinfo:
        RasterMemory(arr, rp)
    assert "Dimensionality of input raster array should be larger than 1" in str(
        excinfo.value
    )


def test_rasterfile():
    """Test functionalities of RasterFile class"""

    # clip
    rp = RasterProperties([162300, 165760, 167560, 169520], 20, -9999, 31370)
    raster = RasterFile(geodata.rst_example, rp=rp)
    assert raster.arr.shape[0] == 188
    assert raster.arr.shape[1] == 263

    # clip with extent outside rasters extent
    rp = RasterProperties([230, 760, 560, 1000], 20, -9999, 31370)
    with pytest.raises(Exception) as excinfo:
        RasterFile(geodata.rst_example, rp=rp)
    assert "Clipped output raster is empty" in str(excinfo.value)

    # do not clip
    raster = RasterFile(geodata.rst_example)
    assert raster.arr.shape[0] == 286
    assert raster.arr.shape[1] == 458

    # check for wrong coordinate system
    rp = RasterProperties([162300, 165760, 167560, 169520], 20, -9999, 3395)
    with pytest.raises(Exception) as excinfo:
        RasterFile(geodata.rst_example, rp=rp)
    assert "should be same as epsg of input raster properties " in str(excinfo.value)


def test_temporalraster():
    """Test functionalities of RasterProperties class"""

    # load raster
    arr, profile = load_raster(geodata.rst_example)
    rp = RasterProperties.from_rasterio(profile)

    # fail when generate with 2D-array
    with pytest.raises(ValueError) as excinfo:
        TemporalRaster(arr, rp)
    assert "Dimensionality of temporal raster array should be equal to 3." in str(
        excinfo.value
    )

    # fail when number of write outputs is
    arr = np.dstack([arr, arr])
    tr = TemporalRaster(arr, rp)
    tiff_temp1 = tempfile.NamedTemporaryFile(suffix=".tif").name
    tiff_temp2 = tempfile.NamedTemporaryFile(suffix=".tif").name

    with pytest.raises(ValueError) as excinfo:
        tr.write([tiff_temp1])
    assert "should be equal to number of arrays in the third dimension" in str(
        excinfo.value
    )

    assert tr.write([tiff_temp1, tiff_temp2], format="tiff")
