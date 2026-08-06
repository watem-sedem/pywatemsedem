"""Test functions for postprocessing functions"""

import numpy as np
import pandas as pd
import pytest
from conftest import ini_file, postprocess, scenario_data
from numpy.testing import assert_almost_equal

from pywatemsedem.geo.utils import load_raster
from pywatemsedem.postprocess import (
    compute_efficiency_grass_strips,
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


def test_get_grass_strips_statistics():
    """Test function for get_gras_strips_statistics for individual grass strips.
    This test function compares the arrays gras id, and coupled sedi in and out."""

    # run function
    _, _, df = compute_efficiency_grass_strips(
        postprocess.txt_routing,
        postprocess.rst_grass_strips_id,
        postprocess.rst_compositelanduse,
        postprocess.rst_sedi_out,
    )

    df_test = pd.read_csv(postprocess.txt_grass_strips_efficiency)

    assert_almost_equal(df["gras_id_target"].values, df_test["gras_id_target"].values)
    assert_almost_equal(df["gras_id_source"].values, df_test["gras_id_source"].values)
    assert_almost_equal(df["npixels_t"].values, df_test["npixels_t"].values)
    assert_almost_equal(df["eSTE"].values, df_test["STE"].values)
    assert_almost_equal(df["sedi_in"].values, df_test["sediin"].values)


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


def test_vct_routing_property(postprocess_obj):
    """Test vct_routing property access and resulting vector object."""

    routing = postprocess_obj.vct_routing

    assert routing is postprocess_obj.vct_routing
    assert routing.file_path.exists()
    assert routing.file_path.suffix == ".shp"
    assert not routing.geodata.empty


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


@pytest.mark.parametrize(
    "compute_priority",
    [
        pytest.param(True, id="with_priority_metrics"),
        pytest.param(False, id="without_priority_metrics"),
    ],
)
def test_process_grass_strips(postprocess_obj, compute_priority):
    """Test process_grass_strips for both compute_priority argument values.

    Parameters
    ----------
    postprocess_obj: pywatemsedem.postprocess.PostProcess
        Function-scoped PostProcess fixture configured on test data.
    compute_priority: bool
        If ``True``, the method should append cumulative priority metrics
        (``cum_sum``, ``cdf``). If ``False``, only efficiency metrics are
        expected.
    """

    postprocess_obj.vct_grass_strips = scenario_data.grass_strips

    gdf_grass = postprocess_obj.process_grass_strips(
        compute_priority=compute_priority,
    )

    assert not gdf_grass.empty
    expected_columns = {
        "gras_id_target",
        "gras_id_source",
        "npixels_t",
        "sedi_in",
        "sedi_out",
        "eSTE",
        "sed",
    }
    assert expected_columns.issubset(gdf_grass.columns)

    rst_grass_ids = (
        postprocess_obj.postprocessing_folder / "grass_strips" / "grass_strips_id.rst"
    )
    assert rst_grass_ids.exists()

    if compute_priority:
        for col in ["cum_sum", "cdf"]:
            assert col in gdf_grass.columns

        cdf = pd.to_numeric(gdf_grass["cdf"], errors="coerce").dropna()
        if not cdf.empty:
            assert (cdf >= 0).all()
            assert (cdf <= 100).all()
    else:
        assert "cum_sum" not in gdf_grass.columns
        assert "cdf" not in gdf_grass.columns


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
                poi_id=poi_id,
                filename=filename,
            )
        return

    poi_path = postprocess_obj.add_poi(
        x_coord,
        y_coord,
        poi_id=poi_id,
        filename=filename,
    )

    assert poi_path.exists()
    assert poi_path.parent.name == "poi"

    poi_vector = postprocess_obj.vct_poi
    assert poi_vector.file_path == poi_path
    assert len(poi_vector.geodata) == len(expected_ids)
    assert sorted(poi_vector.geodata["poi_id"].astype(int).tolist()) == expected_ids


def test_vct_buffers_property(postprocess_obj):
    """Test vct_buffers property access and resulting vector object."""

    buffers = postprocess_obj.vct_buffers

    assert buffers is postprocess_obj.vct_buffers
    assert buffers.file_path.exists()
    assert buffers.file_path.suffix == ".shp"
    assert not buffers.geodata.empty
    assert "buffer_id" in buffers.geodata.columns
    assert hasattr(buffers, "vct_subcatchments")
    assert buffers.vct_subcatchments is None


def test_identify_subcatchments_to_buffers(postprocess_obj):
    """Test identify_subcatchments_to_buffers workflow and coupled output."""

    out = postprocess_obj.identify_subcatchments_to_buffers()

    assert out.exists()
    assert out.parent.name == "buffers"
    assert out.name.endswith("_subcatchments_to_buffers.shp")

    subcatchments = postprocess_obj.vct_buffers.vct_subcatchments
    assert subcatchments.file_path == out
    assert not subcatchments.geodata.empty
    assert "id" in subcatchments.geodata.columns
    assert len(subcatchments.geodata) == len(postprocess_obj.vct_buffers.geodata)


def test_identify_subcatchments_multiple_poi(postprocess_obj):
    """Test identify_subcatchments workflow for multiple POIs.

    This test validates argument usage for
    ``identify_subcatchments(target_input, id_column, tag)``:
    - ``target_input="vct_poi"`` to use the POI vector
    - ``id_column="poi_id"`` to map each delineated polygon to input POI ids
    - ``tag="subcatchments"`` for deterministic output naming
    """

    postprocess_obj.add_poi(
        [165570.4, 164464.4],
        [168768, 166967.9],
        poi_id=[11, 12],
        filename="poi_subcatchments_test.shp",
    )

    out = postprocess_obj.identify_subcatchments(
        "vct_poi",
        id_column="poi_id",
        tag="subcatchments",
    )

    assert out.exists()
    assert out.name == "vct_poi_subcatchments.shp"
    assert out.parent.name == "poi"

    subcatchments = postprocess_obj.vct_poi.vct_subcatchments
    assert subcatchments.file_path == out
    assert len(subcatchments.geodata) == 2
    if "target_id" in subcatchments.geodata.columns:
        assert sorted(subcatchments.geodata["target_id"].astype(int).tolist()) == [
            11,
            12,
        ]


@pytest.mark.parametrize(
    "source, approach, nmax, threshold, flag_merge",
    [
        pytest.param("sedi_out", "n", 2, None, False, id="top2_from_sedi_out"),
        pytest.param("sedi_export", "n", 2, None, True, id="top2_from_sedi_export"),
        pytest.param(
            "sedi_export + sewer_in",
            "percentage",
            None,
            5,
            True,
            id="percentage_5_merge",
        ),
        pytest.param(
            "sedi_export + sewer_in",
            "percentage",
            None,
            10,
            False,
            id="percentage_10_no_merge",
        ),
    ],
)
def test_identify_priority_subcatchments(
    postprocess_obj,
    source,
    approach,
    nmax,
    threshold,
    flag_merge,
):
    """Test identify_priority_subcatchments across supported input scenarios.

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
    flag_merge: bool
        Controls creation of merged overlapping priority subcatchments
        (``priority_subcatchments_merged.shp``).
    """

    kwargs = {
        "source": source,
        "approach": approach,
        "flag_merge": flag_merge,
    }
    if nmax is not None:
        kwargs["nmax"] = nmax
    if threshold is not None:
        kwargs["threshold"] = threshold

    out = postprocess_obj.identify_priority_subcatchments(**kwargs)

    assert out is None

    priority_points = postprocess_obj.vct_priority_points
    priority_subcatchments = postprocess_obj.vct_priority_points.vct_subcatchments

    assert priority_points.file_path.exists()
    assert priority_points.file_path.name == "priority_points_of_interest.shp"
    assert not priority_points.geodata.empty
    assert "target_id" in priority_points.geodata.columns

    assert priority_subcatchments.file_path.exists()
    assert priority_subcatchments.file_path.name.endswith("priority_subcatchments.shp")
    assert not priority_subcatchments.geodata.empty
    assert "target_id" in priority_subcatchments.geodata.columns

    point_ids = sorted(priority_points.geodata["target_id"].astype(int).tolist())
    subcatchment_ids = sorted(
        priority_subcatchments.geodata["target_id"].astype(int).tolist()
    )
    assert subcatchment_ids == point_ids

    if approach == "n":
        assert len(priority_points.geodata) == nmax
        assert len(priority_subcatchments.geodata) == nmax
        assert priority_points.geodata["target_id"].nunique() == nmax
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
