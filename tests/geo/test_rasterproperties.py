import pytest
from pyproj import CRS
from pyproj.exceptions import CRSError
from rasterio import Affine

from pywatemsedem.geo.rasterproperties import RasterProperties


def test_rasterproperties():
    """Test roundtrip between gdal and rasterio raster profile"""
    rasterio_profile = {
        "driver": "GTiff",
        "nodata": -9999.0,
        "width": 294,
        "height": 509,
        "count": 1,
        "crs": CRS.from_epsg(31370),
        "transform": Affine(20.0, 0.0, 201620.0, 0.0, -20.0, 164060.0),
        "compress": "deflate",
    }
    gdal_profile = {
        "nodata": -9999.0,
        "epsg": "EPSG:31370",
        "res": 20.0,
        "minmax": [201620.0, 153880.0, 207500.0, 164060.0],
        "ncols": 294,
        "nrows": 509,
    }

    # compare gdal profile
    rp1 = RasterProperties.from_rasterio(rasterio_profile)
    assert rp1.gdal_profile == gdal_profile

    # compare rasterio profile
    rp2 = RasterProperties.from_gdal(gdal_profile)
    assert rp2.rasterio_profile == rasterio_profile

    # test from bounds
    bounds = [201620.0, 153880.0, 207500.0, 164060.0]
    resolution = 20
    nodata = -9999
    epsg = 31370
    rp4 = RasterProperties(bounds, resolution, nodata, epsg)
    assert rp4.rasterio_profile == rasterio_profile

    # test with incomplete rasterio profile
    rasterio_profile_incompl = {
        "driver": "GTiff",
        "nodata": -9999.0,
        "width": 294,
        "height": 509,
        "count": 1,
        "transform": Affine(20.0, 0.0, 201620.0, 0.0, -20.0, 164060.0),
    }

    with pytest.raises(IOError) as excinfo:
        RasterProperties.from_rasterio(rasterio_profile_incompl)
    assert "Function input is not a rasterio profile instance!" in str(excinfo.value)

    # test with incomplete gdal profile
    gdal_profile_incompl = {
        "nodata": -9999.0,
        "epsg": "EPSG:31370",
        "res": 20.0,
        "ncols": 294,
        "nrows": 509,
    }
    with pytest.raises(IOError) as excinfo:
        RasterProperties.from_gdal(gdal_profile_incompl)
    assert "Function input is not a gdal profile instance!" in str(excinfo.value)

    # test unknown epsg
    epsg = -11000
    with pytest.raises(CRSError) as excinfo:
        RasterProperties(bounds, resolution, nodata, epsg)
    assert "is an unknown " in str(excinfo.value)

    # test wrong format epsg
    epsg = "-11000"
    with pytest.raises(TypeError) as excinfo:
        RasterProperties(bounds, resolution, nodata, epsg)
    assert "need to be an integer code." in str(excinfo.value)

    # test not supported driver
    epsg = 31370  # change epsg back to valid format!

    with pytest.raises(IOError) as excinfo:
        RasterProperties(bounds, resolution, nodata, epsg, driver="tsjaarbomb32")
    assert "Raster property driver" in str(excinfo.value)
