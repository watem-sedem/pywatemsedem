import geopandas as gpd
import pytest
from conftest import geodata

from pywatemsedem.geo.utils import get_geometry_type
from pywatemsedem.geo.vectors import VectorFile, VectorMemory


def test_vectorfile():
    """Test functionalities of VectorFile class"""

    vector = VectorFile(geodata.vct_example)
    assert len(vector.geodata) == 19


def test_vectorfile_clip():
    """Test functionalities of VectorFile class, with clip"""

    # clip
    vector = VectorFile(geodata.vct_example, vct_clip=geodata.catchment)
    assert len(vector.geodata) == 18


@pytest.mark.parametrize("unknwon_type", ["Line", "CurvePolygon"])
def test_vectormemory_unknown_geometry_type(unknwon_type):
    """Test loading a vector with a different geometry type than required"""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    geometry_type = get_geometry_type(geodata.vct_example)

    # unknown required geometry type
    req_geometry_type = unknwon_type
    with pytest.raises(
        TypeError,
        match=(
            f"Required geometry item type '{unknwon_type}' not known to pywatemsedem. "
            f"Please select 'LineString or Polygon or Point'"
        ),
    ):
        VectorMemory(gdf, geometry_type, req_geometry_type)


def test_vectormemory_wrong_geometry_type():
    """Test loading a vector with a different geometry type than required"""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    geometry_type = get_geometry_type(geodata.vct_example)
    # wrong required geometry type
    req_geometry_type = "Polygon"
    with pytest.raises(
        TypeError,
        match=(
            f"Input vector should have geometry item type '{req_geometry_type}', not "
            f"'{geometry_type}'."
        ),
    ):
        VectorMemory(gdf, geometry_type, req_geometry_type)


def test_vectormemory_empty_dataframe():
    """Test loading an empty dataframe"""
    gdf = gpd.GeoDataFrame(columns=["NR", "geometry"])
    # empty dataframe
    req_geometry_type = "LineString"
    with pytest.raises(
        ValueError,
        match=(
            "Input vector is empty. If you wish to return an empty vector, please use "
            "'allow_empty'"
        ),
    ):
        VectorMemory(gdf, req_geometry_type, req_geometry_type)


def test_vectormemory():
    """Test loading a vector, without clipping"""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    geometry_type = get_geometry_type(geodata.vct_example)
    req_geometry_type = "LineString"
    # correct input
    vector = VectorMemory(gdf, geometry_type, req_geometry_type)
    assert len(vector.geodata) == 19


def test_vectormemory_clip():
    """Test loading a vector, with clipping"""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    geometry_type = get_geometry_type(geodata.vct_example)
    req_geometry_type = "LineString"

    # clip
    gdf_mask = gpd.read_file(geodata.catchment)
    vector = VectorMemory(gdf, geometry_type, req_geometry_type, clip_mask=gdf_mask)
    assert len(vector.geodata) == 18
