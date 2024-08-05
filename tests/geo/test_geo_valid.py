import tempfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from shapely.geometry import LineString, Polygon

from pywatemsedem.geo.valid import (
    PywatemsedemInputError,
    PywatemsedemTypeError,
    valid_exists,
    valid_linesvector,
    valid_pointvector,
    valid_polygonvector,
    valid_raster,
    valid_rasterlist,
    valid_vector,
    valid_vectorlist,
)


def dummy_vector_data(vct, geometry_type):
    """Generate dummy vector data and safe to file

    Parameters
    ----------
    vct: str
        File path to temporary vector file
    geometry_type: str
        Either 'Polygon' or 'Point' dummy data
    """
    df = pd.DataFrame(
        {"City": ["Buenos Aires", "Salzburg"], "Country": ["Argentina", "Austria"]}
    )

    if geometry_type == "Polygon":
        p1 = Polygon([(0, 0), (1, 0), (1, 1)])
        p2 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        geometry = [p1, p2]
    elif geometry_type == "Point":
        p1 = [-34.58, -15.78]
        p2 = [-58.66, -47.91]
        geometry = gpd.points_from_xy(p1, p2)
    elif geometry_type == "LineString":
        p1 = LineString([(2, 0), (2, 4), (3, 4)])
        p2 = LineString([(2, 1), (4, 4), (2, 4)])
        geometry = [p1, p2]
    gdf = gpd.GeoDataFrame(df, geometry=geometry)
    gdf.to_file(vct)


def generate_raster(rst):
    """Generate dummy raster data and save to file

    Parameters
    ----------
    rst: str
        File path to temporary raster file
    """
    X, Y = np.meshgrid(np.linspace(-4.0, 4.0, 2), np.linspace(-3.0, 3.0, 2))
    Z = 10.0 * np.ones(X.shape)

    new_dataset = rasterio.open(
        rst,
        "w",
        driver="GTiff",
        height=Z.shape[0],
        width=Z.shape[1],
        count=1,
        dtype=Z.dtype,
        crs="+proj=latlong",
    )
    new_dataset.write(Z, 1)
    new_dataset.close()


def dummy_fun():
    """Dummy function for printing name errors"""


def test_valid():
    """Test valid seprate operators for
    :func:`pywatemsedem.geo.valid.valid_input`-decorator."""
    # test valid exists
    rst = tempfile.NamedTemporaryFile(suffix=".tif").name
    with pytest.raises(PywatemsedemInputError) as excinfo:
        valid_exists(rst, dummy_fun)
    assert "does not exist, cannot execute" in str(excinfo.value)

    # check if valid exists
    generate_raster(rst)
    assert valid_exists(rst, dummy_fun)

    # test valid raster
    assert valid_raster(rst, dummy_fun)

    # test feed wrong file format in valid raster
    log = tempfile.NamedTemporaryFile(suffix=".txt").name
    f = open(log, "w")
    f.write("test")
    f.close()
    with pytest.raises(PywatemsedemTypeError) as excinfo:
        valid_raster(log, dummy_fun)
    assert "The rasterio engine in pywatemsedem cannot open" in str(excinfo.value)

    # test if valid rasterlist not works when inputting wrong input
    assert valid_rasterlist([rst, rst], dummy_fun)

    with pytest.raises(PywatemsedemInputError) as excinfo:
        valid_rasterlist(rst, dummy_fun)
    assert "is not a valid list of rasters input," in str(excinfo.value)

    # test if polygonvector works
    vct = tempfile.NamedTemporaryFile(suffix=".shp").name
    dummy_vector_data(vct, "Polygon")
    assert valid_polygonvector(vct, dummy_fun)

    # test if pointvector works
    vct = tempfile.NamedTemporaryFile(suffix=".shp").name
    dummy_vector_data(vct, "Point")
    assert valid_pointvector(vct, dummy_fun)

    # test if linesvector works
    vct = tempfile.NamedTemporaryFile(suffix=".shp").name
    dummy_vector_data(vct, "LineString")
    assert valid_linesvector(vct, dummy_fun)

    # test if valid vectorlist not works when inputting wrong input
    assert valid_vectorlist([vct, vct], dummy_fun, "LineString")

    with pytest.raises(PywatemsedemInputError) as excinfo:
        valid_vectorlist(rst, dummy_fun, "LineString")
    assert "is not a valid list of vectors input," in str(excinfo.value)

    # test feed wrong file format in valid vector
    with pytest.raises(PywatemsedemTypeError) as excinfo:
        valid_vector(rst, dummy_fun, "Polygon")
    assert "The fiona engine in pywatemsedem cannot open" in str(excinfo.value)

    # test not known required type
    with pytest.raises(IOError) as excinfo:
        valid_vector(rst, dummy_fun, "test")
    assert "Geomtry type 'test' not known." in str(excinfo.value)

    # test feed wrong type of vector  (vct = line, see test above) to valid polygonshape
    with pytest.raises(PywatemsedemTypeError) as excinfo:
        valid_polygonvector(vct, dummy_fun)
    assert "Geometry input type" in str(excinfo.value)
