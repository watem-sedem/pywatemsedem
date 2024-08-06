from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pytest import approx

from pywatemsedem.io.modeloutput import (
    Modeloutput,
    check_segment_edges,
    compute_efficiency_buffers,
    identify_rank_sediment_loads,
)


@pytest.mark.skip(
    reason="test gives saga-issues in conda pipeline, ommited, raised as"
    " issue in saga"
)
def test_modelouput():
    """Testing the modeloutput class"""
    folder = Path(r"tests/io/data")
    filepath_out = folder / "model_out"
    filepath_in = folder / "model_in"
    P_ex = filepath_in / "pfactor.rst"
    example = Modeloutput(P_ex, resolution=20, epsg=31370, nodata=-9999)
    # sediout
    example.sediout = filepath_out / "SediOut_kg.rst"
    example.sediout.plot()
    # example.sediout.hv_plot()
    # routing
    example.routing = filepath_out / "routing.txt"
    landuse_path = filepath_in / "perceelskaart.rst"
    sediout_path = filepath_out / "SediOut_kg.rst"
    example.make_routing_vector(landuse_path, sediout_path)
    # example.routing.plot()
    # routing_missing
    example.routing_missing = filepath_out / "routing_missing.txt"
    example.make_routing_vector(landuse_path, sediout_path, routing_missing=True)
    example.routing_missing.plot()
    # ls
    example.ls = filepath_out / "LS.rst"
    example.ls.plot()
    # example.ls.hv_plot()
    # slope
    example.slope = filepath_out / "SLOPE.rst"
    example.slope.plot()
    # example.slope.hv_plot()
    # uparea
    example.uparea = filepath_out / "UPAREA.rst"
    example.uparea.plot()
    # example.uparea.hv_plot()
    # total sediment
    example.total_sediment = filepath_out / "Total sediment.txt"
    # sewer in
    example.sewer_in = filepath_out / "sewer_in.rst"
    example.sewer_in.plot()
    # example.sewer_in.hv_plot()
    # SediExport
    example.sedi_export = filepath_out / "SediExport_kg.rst"
    example.sedi_export.plot()
    # example.sedi_export.hv_plot()
    # SediIn
    example.sedi_in = filepath_out / "SediIn_kg.rst"
    example.sedi_in.plot()
    # example.sedi_in.hv_plot()
    # Capacity
    example.capacity = filepath_out / "Capacity.rst"
    example.capacity.plot()
    # example.capacity.hv_plot()
    # RUSLE
    example.rusle = filepath_out / "RUSLE.rst"
    example.rusle.plot()
    # example.rusle.hv_plot()


def test_compute_efficiency_buffers():
    """Compute efficiency buffers"""

    exp_sediin = np.array([5928.877930, 4209.729492])
    exp_sediout = np.array([1482.219482, 1052.4324])
    buff_sed = np.array([4446.658203, 3157.297])

    folder = Path(r"tests/io/data")
    filepath_out = folder / "model_out"
    filepath_in = folder / "model_in"

    df = compute_efficiency_buffers(
        filepath_in / "buffers.rst",
        filepath_out / "SediIn_kg.rst",
        filepath_out / "SediOut_kg.rst",
    )

    np.testing.assert_allclose(df["sediout"], exp_sediout, atol=1e-2)
    np.testing.assert_allclose(df["sediin"], exp_sediin, atol=1e-2)
    np.testing.assert_allclose(df["buff_sed"], buff_sed, atol=1e-2)


@pytest.mark.parametrize(
    "threshold,n_ranks,sum_sediment_load,mean_sediment_load",
    [
        (50, 12, 337717.72, 28143.142578125),
        (20, 2, 100766.0, 50383.0),
    ],
)
def test_identify_rank_sediment_loads(
    threshold, n_ranks, sum_sediment_load, mean_sediment_load, tmp_path
):
    """Test function for :func:`pywatemsedem.pywatemsedem.process_output.map_rank_sediment_loads``

    Parameters
    ----------
    threshold: float
        See :func:`pywatemsedem.pywatemsedem.process_output.analyse_cumulative_sediexport`
    n_ranks: float
        Number of records (ranks) for threshold.
    sum_sediment_load: float
        Total sediment load for number of records.
    mean_sediment_load: float
        Mean sediment load for number of records
    tmp_path
    """
    tag = "rank"
    folder = Path(r"tests/io/data")

    filepath_out = folder / "model_out" / "SediExport_kg.rst"

    df_export, _ = identify_rank_sediment_loads(
        filepath_out,
        threshold,
        tmp_path / (tag + ".rst"),
        rst_endpoints=folder / "model_out" / "sewer_in.rst",
    )
    df_export = df_export[df_export["class"] != -9999]

    assert df_export.shape[0] == n_ranks
    assert np.sum(df_export["sediexport"]) == approx(sum_sediment_load, abs=1)
    assert np.mean(df_export["sediexport"]) == approx(mean_sediment_load, abs=1)


def test_check_segment_edges():
    """Test function for check test_check_segment_edges."""

    # normal, valid input: from the documentation
    arr = np.array(
        [
            [0, 0, 0, 0, 0, 5, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 5, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 5, 0, 0, 7, 0],
            [0, 0, 0, 0, 4, 3, 7, 7, 0, 0],
            [0, 0, 0, 4, 0, 3, 0, 0, 0, 0],
            [0, 0, 4, 0, 0, 3, 0, 0, 0, 0],
            [0, 4, 0, 0, 0, 3, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 2, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 2, 0, 0],
            [0, 0, 0, 1, 0, 0, 2, 0, 0, 0],
            [0, 0, 1, 0, 0, 6, 2, 0, 0, 0],
        ]
    )

    up_edges = pd.DataFrame(
        {
            "line_id": [3, 3, 5, 5, 5, 5, 5, 5, 6, 5],
            "upstream_line": [1, 2, 4, 3, 2, 1, 6, 7, 2, 1],
            "proportion": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )

    adj_edges = pd.DataFrame({"from": [1, 2, 3, 4, 6, 7], "to": [3, 3, 5, 5, 2, 5]})

    # test 1: not expected any warnings or filtering!
    adj_edges_adj, up_edges_adj, filt = check_segment_edges(adj_edges, up_edges, arr)
    np.testing.assert_equal(filt, False)
    np.testing.assert_allclose(
        adj_edges_adj["from"],
        adj_edges["from"],
    )
    np.testing.assert_allclose(
        adj_edges_adj["to"],
        adj_edges["to"],
    )
    np.testing.assert_allclose(up_edges_adj["line_id"], up_edges["line_id"])
    np.testing.assert_allclose(up_edges_adj["upstream_line"], up_edges["upstream_line"])

    # test 2: add non valid edges in adj_edges in from series
    add = pd.DataFrame.from_dict({"from": [9], "to": [1]})
    adj_edges_frombis = pd.concat([adj_edges, add], ignore_index=True)
    adj_edges_adj, up_edges_adj, filt = check_segment_edges(
        adj_edges_frombis, up_edges, arr
    )
    np.testing.assert_equal(filt, True)
    # expeced to filter out what is not desired!
    np.testing.assert_allclose(
        adj_edges_adj["from"],
        adj_edges["from"],
    )
    np.testing.assert_allclose(
        adj_edges_adj["to"],
        adj_edges["to"],
    )
    np.testing.assert_allclose(up_edges_adj["line_id"], up_edges["line_id"])
    np.testing.assert_allclose(up_edges_adj["upstream_line"], up_edges["upstream_line"])

    # test 3: add non valid edges in adj_edges in to series
    add = pd.DataFrame.from_dict({"from": [1], "to": [9]})
    adj_edges_tobis = pd.concat([adj_edges, add], ignore_index=True)
    adj_edges_adj, up_edges_adj, filt = check_segment_edges(
        adj_edges_tobis, up_edges, arr
    )
    np.testing.assert_equal(filt, True)
    # expeced to filter out what is not desired!
    np.testing.assert_allclose(
        adj_edges_adj["from"],
        adj_edges["from"],
    )
    np.testing.assert_allclose(
        adj_edges_adj["to"],
        adj_edges["to"],
    )
    np.testing.assert_allclose(up_edges_adj["line_id"], up_edges["line_id"])
    np.testing.assert_allclose(up_edges_adj["upstream_line"], up_edges["upstream_line"])

    # est 4: add no valid edge in up_edges in edge series
    add = pd.DataFrame.from_dict({"line_id": [9], "upstream_line": [1]})
    up_edges_edgebis = pd.concat([up_edges, add], ignore_index=True)

    adj_edges_adj, up_edges_adj, filt = check_segment_edges(
        adj_edges, up_edges_edgebis, arr
    )
    np.testing.assert_equal(filt, True)
    # expeced to filter out what is not desired!
    np.testing.assert_allclose(
        adj_edges_adj["from"],
        adj_edges["from"],
    )
    np.testing.assert_allclose(
        adj_edges_adj["to"],
        adj_edges["to"],
    )
    np.testing.assert_allclose(up_edges_adj["line_id"], up_edges["line_id"])
    np.testing.assert_allclose(up_edges_adj["upstream_line"], up_edges["upstream_line"])

    # test 5: add no valid edge in up_edges in upstream_edge series
    add = pd.DataFrame.from_dict({"line_id": [1], "upstream_line": [9]})
    up_edges_upedgebis = pd.concat([up_edges, add], ignore_index=True)

    adj_edges_adj, up_edges_adj, filt = check_segment_edges(
        adj_edges, up_edges_upedgebis, arr
    )
    np.testing.assert_equal(filt, True)
    # expeced to filter out what is not desired!
    np.testing.assert_allclose(
        adj_edges_adj["from"],
        adj_edges["from"],
    )
    np.testing.assert_allclose(
        adj_edges_adj["to"],
        adj_edges["to"],
    )
    np.testing.assert_allclose(up_edges_adj["line_id"], up_edges["line_id"])
    np.testing.assert_allclose(up_edges_adj["upstream_line"], up_edges["upstream_line"])

    # test 6: a nan input
    up_edges_nan = pd.DataFrame(
        {
            "line_id": [3, 3, 5, 5, 5, 5, 5, 5, 6, np.nan],
            "upstream_line": [1, 2, 4, 3, 2, 1, 6, 7, 2, 1],
            "proportion": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    # expected to delete the last row
    up_edges_nan_exp = pd.DataFrame(
        {
            "line_id": [3, 3, 5, 5, 5, 5, 5, 5, 6],
            "upstream_line": [1, 2, 4, 3, 2, 1, 6, 7, 2],
            "proportion": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    adj_edges_adj, up_edges_adj, filt = check_segment_edges(
        adj_edges, up_edges_nan, arr
    )
    np.testing.assert_equal(filt, True)
    # expeced to filter out what is not desired!
    np.testing.assert_allclose(
        adj_edges_adj["from"],
        adj_edges["from"],
    )
    np.testing.assert_allclose(
        adj_edges_adj["to"],
        adj_edges["to"],
    )
    np.testing.assert_allclose(up_edges_adj["line_id"], up_edges_nan_exp["line_id"])
    np.testing.assert_allclose(
        up_edges_adj["upstream_line"], up_edges_nan_exp["upstream_line"]
    )

    # test 7: a string input
    up_edges_string = pd.DataFrame(
        {
            "line_id": [3, 3, 5, 5, 5, 5, 5, 5, 6, "what, a string?"],
            "upstream_line": [1, 2, 4, 3, 2, 1, 6, 7, 2, 1],
            "proportion": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    adj_edges_adj, up_edges_adj, filt = check_segment_edges(
        adj_edges, up_edges_string, arr
    )
    up_edges_adj = up_edges_adj.astype("int64")  # change to this to compare values!!
    # otherwise dtype = object when string is used as input!
    np.testing.assert_equal(filt, True)
    # expeced to filter out what is not desired!
    np.testing.assert_allclose(
        adj_edges_adj["from"],
        adj_edges["from"],
    )
    np.testing.assert_allclose(
        adj_edges_adj["to"],
        adj_edges["to"],
    )
    np.testing.assert_allclose(up_edges_adj["line_id"], up_edges_nan_exp["line_id"])
    np.testing.assert_allclose(
        up_edges_adj["upstream_line"], up_edges_nan_exp["upstream_line"]
    )
