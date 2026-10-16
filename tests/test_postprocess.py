"""Test functions for postprocessing functions"""

import shutil
import warnings
from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from conftest import folder_core, ini_file, postprocess, scenario_data

from pywatemsedem.geo.utils import load_raster
from pywatemsedem.postprocess import (
    PostProcess,
    compute_netto_erosion_parcels,
    read_filestructure,
)


@pytest.mark.parametrize("sep", [",", ";"])
def test_read_filestructure(sep):
    """Test function for reading filestructure file from pywatemsedem package

    The function is tested by using a correct delimiter (sep=",") which leads to a
    succesfull load of the text file (","-delimited), and by using a wrong delimiter
    (sep=";") which leads to a fail of loading the text file.

    Parameters
    ----------
    sep: str
        Delimiter.
    """
    if sep == ";":
        with pytest.raises(KeyError, match="DataFrame should contain "):
            read_filestructure(sep=sep)
    else:
        df = read_filestructure(sep=sep)
        assert len(df) > 0


def test_compute_netto_erosion_parcels():
    """Test function for computing netto erosion for individual parcels. It
    used two parcels rasters, one with a int16 codation (limited number of
    parcels) and one with a float64. The assert will test whether the sum, average
    and standard deviation on the netto erosion per parcel is equal for all parcels
    in the input data."""

    # script
    df_output, _ = compute_netto_erosion_parcels(
        postprocess.rst_compositelanduse,
        postprocess.rst_watereros_kg,
        postprocess.rst_rasterized_prc_shp,
        flag_write=True,
    )
    file_name = "average_netto_erosion"
    np.testing.assert_allclose(
        df_output[file_name],
        np.loadtxt(postprocess.txt_average_netto_erosion),
        atol=1e-2,
        rtol=1e-02,
    )
    file_name = "std_dev_netto_erosion"
    np.testing.assert_allclose(
        df_output[file_name],
        np.loadtxt(postprocess.txt_std_dev_netto_erosion),
        atol=1e-2,
        rtol=1e-02,
    )
    file_name = "sum_netto_erosion"
    np.testing.assert_allclose(
        df_output[file_name],
        np.loadtxt(postprocess.txt_sum_netto_erosion),
        atol=1e-2,
        rtol=1e-02,
    )
    file_name = "area_parcel"
    np.testing.assert_allclose(
        df_output[file_name],
        np.loadtxt(postprocess.txt_area_parcel),
        atol=1e-2,
        rtol=1e-02,
    )


def _synthetic_postprocess():
    """Create a PostProcess object on a synthetic 1x4 grid.

    Pixel 1 routes to pixel 2, pixel 2 routes to pixel 3 (60%) and pixel 4
    (40%) and pixel 3 routes to river pixel 4. In pixel 2, 5 kg enters the
    sewer, in pixel 4, all incoming sediment is exported to the river.
    """
    pp = object.__new__(PostProcess)
    pp._rp = SimpleNamespace(resolution=20, nodata=-9999.0)
    pp.modelinput = SimpleNamespace()
    pp.modeloutput = SimpleNamespace(
        routing=pd.DataFrame(
            {
                "col": [1, 2, 3],
                "row": [1, 1, 1],
                "target1col": [2, 3, 4],
                "target1row": [1, 1, 1],
                "part1": [1.0, 0.6, 1.0],
                "target2col": [-99, 4, -99],
                "target2row": [-99, 1, -99],
                "part2": [0.0, 0.4, 0.0],
            }
        ),
        sedi_out=SimpleNamespace(arr=np.array([[10.0, 25.0, 12.0, 0.0]])),
        sewer_in=SimpleNamespace(arr=np.array([[0.0, 5.0, 0.0, 0.0]])),
        sedi_export=SimpleNamespace(arr=np.array([[0.0, 0.0, 0.0, 22.0]])),
    )
    return pp


def test_calculate_sediment_balance_synthetic():
    """Test the sediment balance on a synthetic 1x4 grid.

    Pixels 1 and 2 form element 1, pixels 3 and 4 form element 2.
    """
    pp = _synthetic_postprocess()
    elements = SimpleNamespace(arr=np.array([[1, 1, 2, 2]]))

    df = pp.calculate_sediment_balance(elements)

    assert df.columns.tolist() == [
        "id",
        "npixels",
        "area",
        "sedi_in",
        "sedi_out",
        "sewer_in",
        "sedi_exp",
        "deposition",
        "erosion",
        "eSTE",
    ]
    assert df["id"].tolist() == [1, 2]
    assert df["npixels"].tolist() == [2, 2]
    np.testing.assert_allclose(df["area"], [800.0, 800.0])
    # element 1: no inflow, 25 kg leaves via pixel 2 (the arrow from pixel 1 to
    # pixel 2 stays within the element) and 5 kg enters the sewer
    # element 2: 25 kg flows in from pixel 2 (15 kg to pixel 3 and 10 kg to
    # pixel 4), the arrow from pixel 3 to 4 stays within the element, so no
    # sediment leaves via routing, and 22 kg is exported to the river
    np.testing.assert_allclose(df["sedi_in"], [0.0, 25.0])
    np.testing.assert_allclose(df["sedi_out"], [25.0, 0.0])
    np.testing.assert_allclose(df["sewer_in"], [5.0, 0.0])
    np.testing.assert_allclose(df["sedi_exp"], [0.0, 22.0])
    np.testing.assert_allclose(df["deposition"], [0.0, 3.0])
    np.testing.assert_allclose(df["erosion"], [30.0, 0.0])
    # no inflow in element 1, so no trapping efficiency
    np.testing.assert_allclose(df["eSTE"], [np.nan, 100.0])
    # for a raster, the sediment balance is stored on the raster object
    pd.testing.assert_frame_equal(elements.df_sediment_balance, df)


def test_calculate_sediment_balance_priority():
    """Test sorting the sediment balance on a sediment balance variable."""
    pp = _synthetic_postprocess()
    elements = SimpleNamespace(arr=np.array([[1, 1, 2, 2]]))

    df = pp.calculate_sediment_balance(elements)
    assert "cum_sum" not in df.columns
    assert "cdf" not in df.columns

    df = pp.calculate_sediment_balance(elements, compute_priority="erosion")
    assert df["id"].tolist() == [1, 2]
    # only positive values contribute to the cumulative distribution
    np.testing.assert_allclose(df["cum_sum"], [30.0, np.nan])
    np.testing.assert_allclose(df["cdf"], [100.0, np.nan])

    df = pp.calculate_sediment_balance(elements, compute_priority="sedi_in")
    assert df["id"].tolist() == [2, 1]
    np.testing.assert_allclose(df["cum_sum"], [25.0, np.nan])
    np.testing.assert_allclose(df["cdf"], [100.0, np.nan])

    with pytest.raises(ValueError, match="compute_priority"):
        pp.calculate_sediment_balance(elements, compute_priority="unknown")


def test_calculate_sediment_balance_positive_ids():
    """Test that only positive ids are considered as elements."""
    pp = _synthetic_postprocess()
    elements = SimpleNamespace(arr=np.array([[0, -1, 2, 2]]))

    df = pp.calculate_sediment_balance(elements)
    assert df["id"].tolist() == [2]
    # the sediment from pixel 2 (id -1) flows into element 2
    np.testing.assert_allclose(df["sedi_in"], [25.0])

    elements = SimpleNamespace(arr=np.array([[0, -1, -9999, 0]]))
    with pytest.raises(ValueError, match="No elements"):
        pp.calculate_sediment_balance(elements)


def test_calculate_sediment_balance_parcel_id_recycling():
    """Test the warning if the maximum parcel id (int16) is reached in the
    composite landuse raster."""
    pp = _synthetic_postprocess()
    compositelanduse = SimpleNamespace(arr=np.array([[1, 1, 2, 32767]]))
    pp.modelinput = SimpleNamespace(_compositelanduse=compositelanduse)

    with pytest.warns(UserWarning, match="probably not trustworthy"):
        pp.calculate_sediment_balance(compositelanduse)

    # the check is only done for the composite landuse raster
    other = SimpleNamespace(arr=np.array([[1, 1, 2, 32767]]))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pp.calculate_sediment_balance(other)


def test_calculate_sediment_balance_invalid_input():
    """Test that the elements must be a raster or vector factory object."""
    pp = _synthetic_postprocess()
    with pytest.raises(TypeError, match="must be a raster"):
        pp.calculate_sediment_balance(np.array([[1, 1, 2, 2]]))


def _copy_shapefile(file_path, folder):
    """Copy a shapefile (with its sidecar files) to a folder, so it can be
    overwritten by the sediment balance."""
    file_path = Path(file_path)
    for f in file_path.parent.glob(f"{file_path.stem}.*"):
        shutil.copy(f, folder / f.name)
    return folder / file_path.name


def _assert_sediment_balance_closes(df):
    """Assert that netto deposition = inflow - outflow - sewer - export."""
    np.testing.assert_allclose(
        df["deposition"] - df["erosion"],
        df["sedi_in"] - df["sedi_out"] - df["sewer_in"] - df["sedi_exp"],
    )
    assert ((df["deposition"] == 0) | (df["erosion"] == 0)).all()


def test_calculate_sediment_balance_raster(postprocess_obj):
    """Test the sediment balance on a raster factory object (parcels)."""
    compositelanduse = postprocess_obj.modelinput.compositelanduse
    df = postprocess_obj.calculate_sediment_balance(compositelanduse)

    assert df is compositelanduse.df_sediment_balance
    arr = compositelanduse.arr
    assert df["id"].tolist() == np.unique(arr[arr > 0]).tolist()

    # area (m²) equals the number of parcel pixels times the pixel area
    resolution = postprocess_obj.rp.resolution
    n_pixels = pd.Series(arr[arr > 0]).value_counts()
    np.testing.assert_allclose(
        df.set_index("id")["area"].sort_index(),
        n_pixels.sort_index() * resolution**2,
    )
    _assert_sediment_balance_closes(df)


def test_postprocess_init(postprocess_obj):
    """Test PostProcess initialization with a function-scoped fixture."""

    assert postprocess_obj.ini == ini_file
    assert postprocess_obj.postprocessing_folder.name == "postprocess"
    assert postprocess_obj.epsg == 31370
    assert postprocess_obj.postprocessing_folder.exists()


def test_routing_non_river_property(postprocess_obj):
    """Test routing_non_river removes river-source rows from real test data."""

    routing = postprocess_obj.modeloutput.routing
    rows, cols = np.where(postprocess_obj.modelinput.compositelanduse.arr == -1)
    river_coords = set(zip(rows + 1, cols + 1))
    routing_coords = set(zip(routing["row"], routing["col"]))
    expected_removed = routing_coords.intersection(river_coords)

    routing_non_river = postprocess_obj.routing_non_river
    filtered_coords = set(zip(routing_non_river["row"], routing_non_river["col"]))

    assert expected_removed
    assert filtered_coords.isdisjoint(river_coords)
    assert len(routing_non_river) < len(routing)
    assert routing_non_river is postprocess_obj.routing_non_river
    assert routing_non_river.file_path.exists()


def test_routing_river_property(postprocess_obj):
    """Test routing_river keeps only river-source rows from real test data."""

    routing = postprocess_obj.modeloutput.routing
    rows, cols = np.where(postprocess_obj.modelinput.compositelanduse.arr == -1)
    river_coords = set(zip(rows + 1, cols + 1))
    routing_coords = set(zip(routing["row"], routing["col"]))
    expected_kept = routing_coords.intersection(river_coords)

    routing_river = postprocess_obj.routing_river
    kept_coords = set(zip(routing_river["row"], routing_river["col"]))

    assert expected_kept
    assert kept_coords.issubset(river_coords)
    assert kept_coords == expected_kept
    assert len(routing_river) + len(postprocess_obj.routing_non_river) == len(routing)
    assert routing_river is postprocess_obj.routing_river
    assert routing_river.file_path.exists()


def test_vct_routing_property(postprocess_obj):
    """Test vct_routing property access and resulting vector object."""

    routing = postprocess_obj.vct_routing

    assert routing is postprocess_obj.vct_routing
    assert routing.file_path.exists()
    assert routing.file_path.suffix == ".shp"
    assert not routing.geodata.empty
    assert "sedi_out" in routing.geodata.columns
    ax = routing.plot(
        show_mask=True,
        show_river=True,
        show_labels=False,
    )
    assert ax is not None


def test_vct_routing_missing_property(postprocess_obj):
    """Test vct_routing_missing property; None when routing_missing is empty."""

    if postprocess_obj.modeloutput.routing_missing.empty:
        assert postprocess_obj.vct_routing_missing is None
        return

    missing = postprocess_obj.vct_routing_missing

    assert missing is postprocess_obj.vct_routing_missing
    assert missing.file_path.exists()
    assert missing.file_path.suffix == ".shp"
    assert not missing.geodata.empty
    assert "sedi_out" in missing.geodata.columns


def test_vct_routing_non_river_property(postprocess_obj):
    """Test vct_routing_non_river property; sources are land pixels only."""

    non_river = postprocess_obj.vct_routing_non_river

    assert non_river is postprocess_obj.vct_routing_non_river
    assert non_river.file_path.exists()
    assert non_river.file_path.suffix == ".shp"
    assert not non_river.geodata.empty
    assert "sedi_out" in non_river.geodata.columns
    # every source pixel must be a land pixel (lnduSource != -1)
    assert (non_river.geodata["lnduSource"] != -1).all()


def test_vct_routing_river_property(postprocess_obj):
    """Test vct_routing_river property; sources are river pixels only."""

    river = postprocess_obj.vct_routing_river

    assert river is postprocess_obj.vct_routing_river
    assert river.file_path.exists()
    assert river.file_path.suffix == ".shp"
    assert not river.geodata.empty
    assert "sedi_out" in river.geodata.columns
    # every source pixel must be a river pixel (lnduSource == -1)
    assert (river.geodata["lnduSource"] == -1).all()


def _assert_sink_vector_properties(vector_obj, raster_path, expected_type):
    """Assert sink vector values and metadata against source raster."""

    assert vector_obj.file_path.exists()
    assert vector_obj.file_path.suffix == ".shp"
    assert not vector_obj.geodata.empty

    gdf = vector_obj.geodata.sort_values("sediment", ascending=False).reset_index(
        drop=True
    )
    arr_sink, profile = load_raster(raster_path)

    nodata = profile["nodata"]
    if pd.isna(nodata):
        arr_valid = arr_sink[~np.isnan(arr_sink) & (arr_sink != 0)]
    else:
        arr_valid = arr_sink[
            (~np.isnan(arr_sink)) & (arr_sink != nodata) & (arr_sink != 0)
        ]

    expected_sediment_pool = np.round(arr_valid / 1000, 3)
    expected_sediment_pool = expected_sediment_pool[expected_sediment_pool >= 0.001]

    actual_sediment = gdf["sediment"].to_numpy()
    for value in actual_sediment:
        assert np.any(np.isclose(expected_sediment_pool, value, atol=1e-3))

    assert (actual_sediment >= 0.001).all()
    assert len(actual_sediment) <= len(expected_sediment_pool)
    assert (gdf["type"] == expected_type).all()
    np.testing.assert_allclose(gdf["cumsum"].to_numpy(), np.cumsum(actual_sediment))
    np.testing.assert_allclose(gdf["cumperc"].iloc[-1], 100.0)


def test_vct_sedi_export_property(postprocess_obj):
    """Test vct_sedi_export property access and resulting vector object."""

    sedi_export = postprocess_obj.vct_sedi_export

    assert sedi_export is postprocess_obj.vct_sedi_export
    _assert_sink_vector_properties(
        sedi_export,
        postprocess_obj.modeloutput.sedi_export.file_path,
        "river",
    )


def test_vct_sewer_in_property(postprocess_obj):
    """Test vct_sewer_in property access and resulting vector values."""

    sewer_in = postprocess_obj.vct_sewer_in

    assert sewer_in is postprocess_obj.vct_sewer_in
    _assert_sink_vector_properties(
        sewer_in,
        postprocess_obj.modeloutput.sewer_in.file_path,
        "sewer",
    )


def test_vct_sinks_property(postprocess_obj):
    """Test vct_sinks property access and merged sink consistency."""

    sinks = postprocess_obj.vct_sinks

    assert sinks is postprocess_obj.vct_sinks
    assert sinks.file_path.exists()
    assert sinks.file_path.suffix == ".shp"
    assert not sinks.geodata.empty

    gdf = sinks.geodata.sort_values("sediment", ascending=False).reset_index(drop=True)
    expected = pd.concat(
        [
            postprocess_obj.vct_sedi_export.geodata,
            postprocess_obj.vct_sewer_in.geodata,
        ],
        ignore_index=True,
    )
    expected = expected.sort_values("sediment", ascending=False).reset_index(drop=True)

    np.testing.assert_allclose(
        np.sort(gdf["sediment"].to_numpy()),
        np.sort(expected["sediment"].to_numpy()),
        atol=1e-3,
    )
    assert (gdf["sediment"] >= 0.001).all()
    assert set(gdf["type"].unique()) == {"river", "sewer"}
    assert gdf["sediment"].is_monotonic_decreasing
    np.testing.assert_allclose(
        gdf["cumsum"].to_numpy(), np.cumsum(gdf["sediment"].to_numpy())
    )
    np.testing.assert_allclose(gdf["cumperc"].iloc[-1], 100.0)


def test_convert_output_rsts_to_ton(postprocess_obj):
    """Test convert_output_rsts_to_ton writes ton rasters and exposes them on self."""

    result = postprocess_obj.convert_output_rsts_to_ton()

    assert result is None

    expected_attrs = {
        "sedi_out_ton": postprocess_obj.modeloutput.sedi_out,
        "sedi_in_ton": postprocess_obj.modeloutput.sedi_in,
        "watereros_ton": postprocess_obj.modeloutput.watereros_kg,
        "sedi_export_ton": postprocess_obj.modeloutput.sedi_export,
    }

    for attr_name, src in expected_attrs.items():
        assert hasattr(postprocess_obj, attr_name)
        ton_raster = getattr(postprocess_obj, attr_name)

        assert ton_raster.file_path.exists()
        assert ton_raster.file_path.parent == postprocess_obj.postprocessing_folder

        src_stem = src.file_path.stem
        if "_kg" in src_stem:
            assert ton_raster.file_path.name == src.file_path.name.replace(
                "_kg", "_ton"
            )
        else:
            assert ton_raster.file_path.stem == f"{src_stem}_ton"

        nodata = postprocess_obj.rp.nodata
        arr_src = src.arr
        arr_ton = ton_raster.arr
        valid = arr_src != nodata
        np.testing.assert_allclose(arr_ton[valid], arr_src[valid] / 1000.0, atol=1e-6)


def test_write_erosion_deposition_raster(postprocess_obj):
    """Test write_erosion_deposition_raster splits watereros in erosion/deposition."""

    result = postprocess_obj.write_erosion_deposition_raster()

    assert result is None

    erosion = postprocess_obj.erosion
    deposition = postprocess_obj.deposition
    assert erosion.file_path == postprocess_obj.postprocessing_folder / "Erosion_kg.rst"
    assert deposition.file_path == (
        postprocess_obj.postprocessing_folder / "Deposition_kg.rst"
    )
    assert erosion.file_path.exists()
    assert deposition.file_path.exists()

    nodata = postprocess_obj.rp.nodata
    arr_watereros = postprocess_obj.modeloutput.watereros_kg.arr
    valid = arr_watereros != nodata

    # nodata is retained
    np.testing.assert_array_equal(erosion.arr[~valid], nodata)
    np.testing.assert_array_equal(deposition.arr[~valid], nodata)

    # both rasters are positive and split watereros
    assert np.all(erosion.arr[valid] >= 0)
    assert np.all(deposition.arr[valid] >= 0)
    assert np.any(erosion.arr[valid] > 0)
    assert np.any(deposition.arr[valid] > 0)
    np.testing.assert_allclose(
        deposition.arr[valid] - erosion.arr[valid], arr_watereros[valid], rtol=1e-6
    )
    np.testing.assert_allclose(
        erosion.arr[valid], np.where(arr_watereros < 0, -arr_watereros, 0)[valid]
    )


def test_calculate_sediment_balance_vector(postprocess_obj):
    """Test the sediment balance on a vector factory object (grass strips)."""
    postprocess_obj.vct_grass_strips = _copy_shapefile(
        scenario_data.grass_strips, postprocess_obj.postprocessing_folder
    )
    vct_grass_strips = postprocess_obj.vct_grass_strips
    n_grass_strips = len(vct_grass_strips.geodata)

    df = postprocess_obj.calculate_sediment_balance(
        vct_grass_strips, compute_priority="eSTE"
    )

    assert df["eSTE"].dropna().is_monotonic_decreasing
    _assert_sediment_balance_closes(df)

    # for a vector, the sediment balance columns are added to the geodata
    gdf = vct_grass_strips.geodata
    assert len(gdf) == n_grass_strips
    assert set(df.columns).issubset(gdf.columns)
    pd.testing.assert_frame_equal(
        gdf.set_index("id").loc[df["id"], df.columns[1:]],
        df.set_index("id"),
        check_dtype=False,
    )

    # the geodata with the sediment balance is written to the vector file
    gdf_file = gpd.read_file(vct_grass_strips.file_path)
    assert len(gdf_file) == n_grass_strips
    assert {"sedi_in", "sedi_out", "deposition", "eSTE", "cdf"}.issubset(
        gdf_file.columns
    )

    # a second run replaces the sediment balance columns
    postprocess_obj.calculate_sediment_balance(vct_grass_strips)
    columns = vct_grass_strips.geodata.columns
    assert len(columns) == len(gdf.columns) - 2
    assert "cum_sum" not in columns
    assert "cdf" not in columns


@pytest.mark.parametrize(
    "x_coord, y_coord, poi_id, filename, should_raise, expected_ids",
    [
        pytest.param(
            [165570.4, 164464.4],
            [168768, 166967.9],
            [7, 8],
            "poi_test.shp",
            False,
            [7, 8],
            id="multiple_points_with_matching_ids",
        ),
        pytest.param(
            [165570.4],
            [168768],
            [7],
            "poi_single_test.shp",
            False,
            [7],
            id="single_point",
        ),
        pytest.param(
            [165570.4, 164464.4],
            [168768, 166967.9],
            [7],
            "poi_invalid_ids.shp",
            True,
            None,
            id="invalid_id_count",
        ),
    ],
)
def test_add_poi(
    postprocess_obj,
    x_coord,
    y_coord,
    poi_id,
    filename,
    should_raise,
    expected_ids,
):
    """Test add_poi with valid and invalid coordinate/id argument combinations.

    Parameters
    ----------
    postprocess_obj: pywatemsedem.postprocess.PostProcess
        Function-scoped PostProcess fixture configured on test data.
    x_coord: list[float]
        X coordinate values passed to ``add_poi``.
    y_coord: list[float]
        Y coordinate values passed to ``add_poi``.
    poi_id: list[int]
        POI identifiers passed to ``add_poi``.
    filename: str
        Output shapefile name passed to ``add_poi``.
    should_raise: bool
        If ``True``, the call is expected to raise ``ValueError``.
    expected_ids: list[int] | None
        Expected ids in output vector for valid scenarios.
    """

    if should_raise:
        with pytest.raises(ValueError, match="must have the same length"):
            postprocess_obj.add_poi(
                x_coord,
                y_coord,
                id=poi_id,
                filename=filename,
            )
        return

    poi_path = postprocess_obj.add_poi(
        x_coord,
        y_coord,
        id=poi_id,
        filename=filename,
    )

    assert poi_path.exists()
    assert poi_path.parent == postprocess_obj.postprocessing_folder

    poi_vector = postprocess_obj.vct_poi
    assert poi_vector.file_path == poi_path
    assert len(poi_vector.geodata) == len(expected_ids)
    assert sorted(poi_vector.geodata["id"].astype(int).tolist()) == expected_ids


def test_vct_buffers_property(postprocess_obj):
    """Test vct_buffers property access and resulting vector object."""

    buffers = postprocess_obj.vct_buffers

    assert buffers is postprocess_obj.vct_buffers
    assert buffers.file_path.exists()
    assert buffers.file_path.suffix == ".shp"
    assert not buffers.geodata.empty
    assert "id" in buffers.geodata.columns
    assert hasattr(buffers, "vct_subcatchments")
    assert buffers.vct_subcatchments is None


def test_identify_subcatchments_to_buffers(postprocess_obj):
    """Test identify_subcatchments_to_buffers workflow and coupled output."""

    out = postprocess_obj.identify_subcatchments_to_buffers()

    assert out.exists()
    assert out.parent == postprocess_obj.postprocessing_folder
    assert out.name == f"{postprocess_obj.vct_buffers.file_path.stem}_subcatchments.shp"
    # The "buffers" working subfolder only ever held intermediate
    # delineation helper files and is removed once the final result has
    # been copied to the main postprocessing folder.
    assert not (postprocess_obj.postprocessing_folder / "buffers").exists()

    subcatchments = postprocess_obj.vct_buffers.vct_subcatchments
    assert subcatchments.file_path == out
    assert not subcatchments.geodata.empty
    assert "id" in subcatchments.geodata.columns
    assert "VALUE" not in subcatchments.geodata.columns
    assert len(subcatchments.geodata) == len(postprocess_obj.vct_buffers.geodata)
    assert sorted(subcatchments.geodata["id"].astype(int).tolist()) == sorted(
        postprocess_obj.vct_buffers.geodata["id"].astype(int).tolist()
    )


def test_calculate_sediment_balance_buffers_raster(postprocess_obj):
    """Test the sediment balance on the modelinput buffers raster.

    Every buffer consists of its outlet pixel (buffer id) and its body pixels
    (buffer id + 2^14).
    """
    buffers = postprocess_obj.modelinput.buffers
    df = postprocess_obj.calculate_sediment_balance(buffers)

    arr_buffers = buffers.arr
    arr_buffers = arr_buffers[arr_buffers > 0].astype(int)
    arr_buffers = np.where(arr_buffers > 2**14, arr_buffers - 2**14, arr_buffers)
    n_pixels = pd.Series(arr_buffers).value_counts().sort_index()
    assert df["id"].tolist() == n_pixels.index.tolist()
    assert df["npixels"].tolist() == n_pixels.tolist()
    _assert_sediment_balance_closes(df)


def test_calculate_sediment_balance_buffers_vector(postprocess_obj):
    """Test the sediment balance on a buffers shapefile."""
    postprocess_obj.vct_buffers = _copy_shapefile(
        folder_core / "buffers.shp", postprocess_obj.postprocessing_folder
    )
    df = postprocess_obj.calculate_sediment_balance(postprocess_obj.vct_buffers)

    gdf_buffers = postprocess_obj.vct_buffers.geodata
    assert set(df.columns).issubset(gdf_buffers.columns)
    _assert_sediment_balance_closes(df)


def test_identify_subcatchments_multiple_poi(postprocess_obj):
    """Test identify_subcatchments workflow for multiple POIs.

    This test validates argument usage for
    ``identify_subcatchments(target_input, id_column)``:
    - ``target_input="vct_poi"`` to use the POI vector
    - ``id_column="id"`` to map each delineated polygon to input POI ids
    - the output is always named ``<points vector stem>_subcatchments.shp``
    """

    postprocess_obj.add_poi(
        [165570.4, 164464.4],
        [168768, 166967.9],
        id=[11, 12],
        filename="poi_subcatchments_test.shp",
    )

    out = postprocess_obj.identify_subcatchments(
        "vct_poi",
        id_column="id",
    )

    assert out.exists()
    assert out.name == "poi_subcatchments_test_subcatchments.shp"
    assert out.parent == postprocess_obj.postprocessing_folder
    # The "poi" working subfolder only ever held intermediate delineation
    # helper files and is removed once the final result has been copied
    # to the main postprocessing folder.
    assert not (postprocess_obj.postprocessing_folder / "poi").exists()

    subcatchments = postprocess_obj.vct_poi.vct_subcatchments
    assert subcatchments.file_path == out
    assert len(subcatchments.geodata) == 2
    assert sorted(subcatchments.geodata["id"].astype(int).tolist()) == [11, 12]
    assert "target_id" not in subcatchments.geodata.columns
    assert "VALUE" not in subcatchments.geodata.columns


@pytest.mark.parametrize(
    "source, approach, nmax, threshold",
    [
        pytest.param("sedi_out", "n", 2, None, id="top2_from_sedi_out"),
        pytest.param("sedi_export", "n", 2, None, id="top2_from_sedi_export"),
        pytest.param(
            "sedi_export + sewer_in",
            "percentage",
            None,
            5,
            id="percentage_5",
        ),
        pytest.param(
            "sedi_export + sewer_in",
            "percentage",
            None,
            10,
            id="percentage_10",
        ),
    ],
)
def test_identify_priority_areas(
    postprocess_obj,
    source,
    approach,
    nmax,
    threshold,
):
    """Test identify_priority_areas across supported input scenarios.

    Parameters
    ----------
    postprocess_obj: pywatemsedem.postprocess.PostProcess
        Function-scoped PostProcess fixture configured on test data.
    source: str
        Raster source used to rank priorities. Scenarios cover
        ``sedi_out``, ``sedi_export``, and combined
        ``sedi_export + sewer_in``.
    approach: str
        Selection strategy. ``n`` selects a fixed number, ``percentage`` keeps
        priorities until cumulative contribution exceeds ``threshold``.
    nmax: int | None
        Maximum number of selected priorities for ``approach="n"``.
    threshold: float | None
        Cumulative percentage target for ``approach="percentage"``.
    """

    kwargs = {
        "source": source,
        "approach": approach,
    }
    if nmax is not None:
        kwargs["nmax"] = nmax
    if threshold is not None:
        kwargs["threshold"] = threshold

    out = postprocess_obj.identify_priority_areas(**kwargs)

    assert out is None

    priority_points = postprocess_obj.vct_priority_points
    priority_subcatchments = postprocess_obj.vct_priority_points.vct_subcatchments

    assert priority_points.file_path.exists()
    assert priority_points.file_path.name == "priority_points.shp"
    assert not priority_points.geodata.empty
    assert "id" in priority_points.geodata.columns
    assert "source_val" in priority_points.geodata.columns
    assert "target_id" not in priority_points.geodata.columns
    assert "priority_i" not in priority_points.geodata.columns
    assert "priority_id" not in priority_points.geodata.columns

    assert priority_subcatchments.file_path.exists()
    assert priority_subcatchments.file_path.name == "priority_points_subcatchments.shp"
    assert not priority_subcatchments.geodata.empty
    assert "id" in priority_subcatchments.geodata.columns
    assert "source_val" in priority_subcatchments.geodata.columns
    assert "target_id" not in priority_subcatchments.geodata.columns
    assert "VALUE" not in priority_subcatchments.geodata.columns

    point_ids = sorted(priority_points.geodata["id"].astype(int).tolist())
    subcatchment_ids = sorted(priority_subcatchments.geodata["id"].astype(int).tolist())
    assert subcatchment_ids == point_ids

    # Both outputs are sorted from highest to lowest selection value.
    point_values = priority_points.geodata["source_val"].astype(float).tolist()
    assert point_values == sorted(point_values, reverse=True)
    subcatchment_values = (
        priority_subcatchments.geodata["source_val"].astype(float).tolist()
    )
    assert subcatchment_values == sorted(subcatchment_values, reverse=True)

    if approach == "n":
        assert len(priority_points.geodata) == nmax
        assert len(priority_subcatchments.geodata) == nmax
        assert priority_points.geodata["id"].nunique() == nmax
        assert sorted(priority_points.geodata["id"].astype(int).tolist()) == list(
            range(1, nmax + 1)
        )
    else:
        assert len(priority_points.geodata) >= 1
        assert len(priority_subcatchments.geodata) >= 1
        assert "cumperc" in priority_points.geodata.columns
        assert "cumperc" in priority_subcatchments.geodata.columns

        cumperc = pd.to_numeric(
            priority_points.geodata["cumperc"], errors="coerce"
        ).dropna()
        assert not cumperc.empty
        assert (cumperc >= 0).all()
        assert (cumperc <= 100).all()
        assert bool((cumperc > float(threshold)).any())
