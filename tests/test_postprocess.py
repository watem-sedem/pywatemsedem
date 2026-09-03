"""Test functions for postprocessing functions"""

import numpy as np
import pandas as pd
import pytest
from conftest import ini_file, postprocess, scenario_data

from pywatemsedem.geo.utils import load_raster
from pywatemsedem.postprocess import (
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

    result = postprocess_obj.process_grass_strips(
        compute_priority=compute_priority,
    )

    assert result is None
    gdf_grass = postprocess_obj.vct_grass_strips.geodata

    assert not gdf_grass.empty
    expected_columns = {
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

        valid = gdf_grass[gdf_grass["sed"] > 0].copy()
        if not valid.empty:
            assert valid["sed"].is_monotonic_decreasing
            cdf_valid = pd.to_numeric(valid["cdf"], errors="coerce").dropna()
            if len(cdf_valid) > 1:
                assert cdf_valid.is_monotonic_increasing

            total_deposition = valid["sed"].sum()
            np.testing.assert_allclose(
                valid["cdf"].to_numpy(),
                100 * valid["cum_sum"].to_numpy() / total_deposition,
            )
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
    assert poi_path.parent.name == "poi"

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
    assert out.parent.name == "buffers"
    assert out.name.endswith("_subcatchments_to_buffers.shp")

    subcatchments = postprocess_obj.vct_buffers.vct_subcatchments
    assert subcatchments.file_path == out
    assert not subcatchments.geodata.empty
    assert "id" in subcatchments.geodata.columns
    assert "VALUE" not in subcatchments.geodata.columns
    assert len(subcatchments.geodata) == len(postprocess_obj.vct_buffers.geodata)
    assert sorted(subcatchments.geodata["id"].astype(int).tolist()) == sorted(
        postprocess_obj.vct_buffers.geodata["id"].astype(int).tolist()
    )


def test_identify_subcatchments_multiple_poi(postprocess_obj):
    """Test identify_subcatchments workflow for multiple POIs.

    This test validates argument usage for
    ``identify_subcatchments(target_input, id_column, tag)``:
    - ``target_input="vct_poi"`` to use the POI vector
    - ``id_column="id"`` to map each delineated polygon to input POI ids
    - ``tag="subcatchments"`` for deterministic output naming
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
        tag="subcatchments",
    )

    assert out.exists()
    assert out.name == "vct_poi_subcatchments.shp"
    assert out.parent.name == "poi"

    subcatchments = postprocess_obj.vct_poi.vct_subcatchments
    assert subcatchments.file_path == out
    assert len(subcatchments.geodata) == 2
    assert sorted(subcatchments.geodata["id"].astype(int).tolist()) == [11, 12]
    assert "target_id" not in subcatchments.geodata.columns
    assert "VALUE" not in subcatchments.geodata.columns


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
    assert "id" in priority_points.geodata.columns
    assert "target_id" not in priority_points.geodata.columns
    assert "priority_i" not in priority_points.geodata.columns
    assert "priority_id" not in priority_points.geodata.columns

    assert priority_subcatchments.file_path.exists()
    assert priority_subcatchments.file_path.name.endswith("priority_subcatchments.shp")
    assert not priority_subcatchments.geodata.empty
    assert "id" in priority_subcatchments.geodata.columns
    assert "target_id" not in priority_subcatchments.geodata.columns
    assert "VALUE" not in priority_subcatchments.geodata.columns

    point_ids = sorted(priority_points.geodata["id"].astype(int).tolist())
    subcatchment_ids = sorted(priority_subcatchments.geodata["id"].astype(int).tolist())
    assert subcatchment_ids == point_ids

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
