import geopandas as gpd
import pytest
from conftest import geodata

from pywatemsedem.geo.utils import get_geometry_type
from pywatemsedem.geo.vectors import VectorFile, VectorMemory


def test_vector_file():
    """Test functionalities of VectorFile class"""

    # clip
    vector = VectorFile(geodata.vct_example, vct_clip=geodata.catchment)
    assert len(vector.geodata) == 18


def test_vector_memory():
    """Test functionalities of VectorMemory class"""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    geometry_type = get_geometry_type(geodata.vct_example)

    # unknown required geometry type
    req_geometry_type = "Line"
    with pytest.raises(TypeError) as excinfo:
        VectorMemory(gdf, geometry_type, req_geometry_type)
    assert (
        f"Required geometry item type '{req_geometry_type}' not known to pywatemsedem. "
        f"Please select 'LineString or Polygon or Point'" in str(excinfo.value)
    )

    # wrong required geometry type
    req_geometry_type = "Polygon"
    with pytest.raises(TypeError) as excinfo:
        VectorMemory(gdf, geometry_type, req_geometry_type)
    assert (
        f"Input vector should have geometry item type '{req_geometry_type}', not "
        f"'{geometry_type}'." in str(excinfo.value)
    )

    # empty dataframe
    req_geometry_type = "LineString"
    with pytest.raises(ValueError) as excinfo:
        VectorMemory(gdf[gdf["NR"] == -1], geometry_type, req_geometry_type)
    assert (
        "Input vector is empty. If you wish to return an empty vector, please use "
        "'allow_empty'" in str(excinfo.value)
    )

    # correct input
    vector = VectorMemory(gdf, geometry_type, req_geometry_type)
    assert len(vector.geodata) == 19
