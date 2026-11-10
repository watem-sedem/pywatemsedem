import geopandas as gpd
import pytest
from conftest import geodata

from pywatemsedem.geo.utils import get_geometry_type
from pywatemsedem.geo.vectors import (
    VectorFile,
    VectorMemory,
    delete_vector,
    infer_id_column,
)


def test_vectorfile():
    """Test functionalities of VectorFile class."""

    vector = VectorFile(geodata.vct_example)
    assert len(vector.geodata) == 19


def test_vectorfile_clip():
    """Test functionalities of VectorFile class, with clip."""

    # clip
    vector = VectorFile(geodata.vct_example, vct_clip=geodata.catchment)
    assert len(vector.geodata) == 18


def _copy_example_vector(folder, columns=None):
    """Write (a column selection of) the example vector to ``folder``.

    Parameters
    ----------
    folder: pathlib.Path
        Output folder.
    columns: list, default None
        Columns to keep besides the geometry. If None, all are kept.

    Returns
    -------
    pathlib.Path
        File path of the written shapefile.
    """
    gdf = gpd.read_file(geodata.vct_example)
    if columns is not None:
        gdf = gdf[columns + ["geometry"]]
    folder.mkdir(parents=True, exist_ok=True)
    vct = folder / "vector.shp"
    gdf.to_file(vct, spatial_index="YES")
    return vct


def test_vectorfile_relocate(tmp_path):
    """Test moving a VectorFile to another folder, with renaming.

    Parameters
    ----------
    tmp_path: pathlib.Path
        Temporary folder.
    """
    vector = VectorFile(_copy_example_vector(tmp_path / "src"))
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    new_path = vector.relocate(dst_dir, filename="moved.shp")

    assert new_path == dst_dir / "moved.shp"
    assert vector.file_path == new_path
    assert not list((tmp_path / "src").iterdir())
    assert len(gpd.read_file(new_path)) == len(vector.geodata)

    # Relocating to the current location leaves the file untouched.
    assert vector.relocate(dst_dir, filename="moved.shp") == new_path
    assert new_path.exists()


def test_vectorfile_ensure_id_column(tmp_path):
    """Test adding an ``id`` column to a VectorFile, in memory and on disk.

    Parameters
    ----------
    tmp_path: pathlib.Path
        Temporary folder.
    """
    vct = _copy_example_vector(tmp_path, columns=[])
    vector = VectorFile(vct)
    assert "id" not in vector.geodata.columns

    vector.ensure_id_column(persist=False)
    assert vector.geodata["id"].tolist() == list(range(1, len(vector.geodata) + 1))
    assert "id" not in gpd.read_file(vct).columns

    vector = VectorFile(vct)
    vector.ensure_id_column()
    assert "id" in gpd.read_file(vct).columns


def test_infer_id_column():
    """Test inferring the id column of a GeoDataFrame."""
    gdf = gpd.GeoDataFrame({"NR": [1], "ID": [2], "name": ["a"]}, geometry=[None])

    assert infer_id_column(gdf) == "ID"
    assert infer_id_column(gdf, requested="name") == "name"
    assert infer_id_column(gdf[["name", "geometry"]]) is None

    with pytest.raises(ValueError, match="Requested id column 'x' not found"):
        infer_id_column(gdf, requested="x")
    with pytest.raises(ValueError, match="No id column found"):
        infer_id_column(gdf[["name", "geometry"]], required=True)


def test_delete_vector(tmp_path):
    """Test deleting a shapefile including its sidecar files.

    Parameters
    ----------
    tmp_path: pathlib.Path
        Temporary folder.
    """
    vct = _copy_example_vector(tmp_path)
    other = tmp_path / "other.txt"
    other.write_text("keep")

    delete_vector(vct)

    assert list(tmp_path.iterdir()) == [other]
    # Deleting a non-existing vector is a no-op.
    delete_vector(vct)


@pytest.mark.parametrize("unknwon_type", ["Line", "CurvePolygon"])
def test_vectormemory_unknown_geometry_type(unknwon_type):
    """Test loading a vector with a different geometry type than required."""
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


def test_vectormemory_wrong_required_geometry_type():
    """Test loading a vector with a different geometry type than required."""
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
    """Test loading an empty dataframe."""
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
    """Test loading a vector, without clipping."""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    geometry_type = get_geometry_type(geodata.vct_example)
    req_geometry_type = "LineString"
    # correct input
    vector = VectorMemory(gdf, geometry_type, req_geometry_type)
    assert len(vector.geodata) == 19


def test_vectormemory_clip():
    """Test loading a vector, with clipping."""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    geometry_type = get_geometry_type(geodata.vct_example)
    req_geometry_type = "LineString"

    # clip
    gdf_mask = gpd.read_file(geodata.catchment)
    vector = VectorMemory(gdf, geometry_type, req_geometry_type, clip_mask=gdf_mask)
    assert len(vector.geodata) == 18


def test_vectormemory_wrong_epsg():
    """Test loading a vector with a different epsg than required."""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    req_epsg = 4326

    vector = VectorMemory(gdf, "LineString", "LineString", epsg=req_epsg)
    assert vector.geodata.crs.to_epsg() == req_epsg


def test_vectormemory_correct_epsg():
    """Test loading a vector with a required epsg"""
    # load
    gdf = gpd.read_file(geodata.vct_example)
    req_epsg = 31370

    vector = VectorMemory(gdf, "LineString", "LineString", epsg=req_epsg)
    assert vector.geodata.crs.to_epsg() == req_epsg
