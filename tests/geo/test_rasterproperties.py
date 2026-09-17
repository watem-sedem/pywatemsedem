from pathlib import Path

import numpy as np
import pytest
import rasterio
from pyproj import CRS
from pyproj.exceptions import CRSError
from rasterio import Affine
from rasterio.transform import from_origin

from pywatemsedem.geo.rasterproperties import RasterProperties


def test_rasterproperties():
    """Test roundtrip between gdal and rasterio raster profile."""
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

    with pytest.raises(
        IOError, match="Function input is not a rasterio profile instance!"
    ):
        RasterProperties.from_rasterio(rasterio_profile_incompl)

    # test with incomplete gdal profile
    gdal_profile_incompl = {
        "nodata": -9999.0,
        "epsg": "EPSG:31370",
        "res": 20.0,
        "ncols": 294,
        "nrows": 509,
    }
    with pytest.raises(IOError, match="Function input is not a gdal profile instance!"):
        RasterProperties.from_gdal(gdal_profile_incompl)

    # test unknown epsg
    epsg = -11000
    with pytest.raises(CRSError, match="is an unknown "):
        RasterProperties(bounds, resolution, nodata, epsg)

    # test wrong format epsg
    epsg = "-11000"
    with pytest.raises(TypeError, match="need to be an integer code."):
        RasterProperties(bounds, resolution, nodata, epsg)

    # test not supported driver
    epsg = 31370  # change epsg back to valid format!

    with pytest.raises(IOError, match="Raster property driver"):
        RasterProperties(bounds, resolution, nodata, epsg, driver="tsjaarbomb32")


RST_TEMPLATE = Path("tests/io/data/modelinput/pfactor.rst")
MISSING_TEMPLATE = Path("tests/io/data/modelinput/does_not_exist.rst")


@pytest.mark.parametrize(
    "kind, epsg, expected_exception, match",
    [
        pytest.param("rst", 31370, None, None, id="rst_with_epsg"),
        pytest.param(
            "rst",
            None,
            TypeError,
            "missing the required argument 'epsg'",
            id="rst_no_epsg",
        ),
        pytest.param(
            "missing",
            31370,
            IOError,
            "not found for getting spatial metadata",
            id="missing_file",
        ),
        pytest.param(
            "non_rst", None, TypeError, "got a '.sdat' file", id="non_rst_no_epsg"
        ),
        pytest.param(
            "non_rst", 31370, TypeError, "got a '.sdat' file", id="non_rst_with_epsg"
        ),
    ],
)
def test_rasterproperties_from_template(
    kind, epsg, expected_exception, match, tmp_path
):
    """Test RasterProperties.from_template across its input cases.

    Parameters
    ----------
    kind: str
        Which template to pass: an existing ".rst" file, a non-existing
        file, or a freshly-written non-".rst" (SAGA ".sdat") file.
    epsg: int or None
        Value passed for ``epsg``.
    expected_exception: type or None
        Exception class expected to be raised, or ``None`` if the call
        should succeed.
    match: str or None
        Expected substring in the raised exception's message.
    """
    if kind == "rst":
        template = RST_TEMPLATE
    elif kind == "missing":
        template = MISSING_TEMPLATE
    else:
        template = tmp_path / "template.sdat"
        with rasterio.open(
            template,
            "w",
            driver="SAGA",
            height=10,
            width=10,
            count=1,
            dtype="float32",
            crs="EPSG:31370",
            transform=from_origin(162300, 169520, 20, 20),
            nodata=-9999.0,
        ) as dst:
            dst.write(np.zeros((10, 10), dtype="float32"), 1)

    if expected_exception is not None:
        with pytest.raises(expected_exception, match=match):
            RasterProperties.from_template(template, epsg=epsg)
        return

    rp = RasterProperties.from_template(template, epsg=epsg)

    assert rp.bounds == [162300.0, 165760.0, 167560.0, 169520.0]
    assert rp.resolution == 20.0
    assert rp.nodata == -9999.0
    assert rp.epsg == epsg
    assert rp.gdal_profile == {
        "nodata": -9999.0,
        "epsg": "EPSG:31370",
        "res": 20.0,
        "minmax": [162300.0, 165760.0, 167560.0, 169520.0],
        "ncols": 263,
        "nrows": 188,
    }
