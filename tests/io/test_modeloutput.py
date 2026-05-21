from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pytest import approx

from pywatemsedem.io.modelinput import Modelinput
from pywatemsedem.io.modeloutput import (
    Modeloutput,
    check_segment_edges,
    compute_efficiency_buffers,
    identify_rank_sediment_loads,
)


def test_modeloutput_all():
    """Testing the modeloutput class"""
    # Initialization
    file_path_in = Path("tests") / "io" / "data" / "modelinput"
    Path("tests") / "io" / "data" / "modeloutput"
    ini = file_path_in / "inifile.ini"
    example_in = Modelinput(ini, resolution=20, epsg=31370, nodata=-9999)
    example_out = Modeloutput(ini, resolution=20, epsg=31370, nodata=-9999)

    # sedi_out
    example_out.sedi_out
    example_out.sedi_out.plot()
    # example_out.sedi_out.hv_plot()

    # routing
    example_out.routing
    example_out.make_routing_vector(example_in)
    # example_out.routing.plot()

    # routing_missing
    example_out.routing_missing
    example_out.make_routing_vector(example_in, routing_missing=True)
    example_out.routing_missing.plot()

    # ls
    example_out.ls
    example_out.ls.plot()
    # example_out.ls.hv_plot()

    # slope
    example_out.slope
    example_out.slope.plot()
    # example_out.slope.hv_plot()

    # uparea
    example_out.uparea
    example_out.uparea.plot()
    # example_out.uparea.hv_plot()

    # total sediment
    example_out.total_sediment

    ## sewer in
    # example_out.sewer_in = file_path_out / "sewer_in.rst"
    # example_out.sewer_in.plot()
    ## example_out.sewer_in.hv_plot()

    # sedi_export
    example_out.sedi_export
    example_out.sedi_export.plot()
    # example_out.sedi_export.hv_plot()

    # sedi_in
    example_out.sedi_in
    example_out.sedi_in.plot()
    # example_out.sedi_in.hv_plot()

    # Capacity
    example_out.capacity
    example_out.capacity.plot()
    # example_out.capacity.hv_plot()

    # RUSLE
    example_out.rusle
    example_out.rusle.plot()
    # example_out.rusle.hv_plot()


def test_compute_efficiency_buffers():
    """Compute efficiency buffers"""

    exp_sedi_in = np.array([12947.483, 17984.963])
    exp_sedi_out = np.array([3236.8708, 4496.2407])
    buff_sed = np.array([9710.612, 13488.723])

    folder = Path(r"tests/io/data")
    filepath_out = folder / "modeloutput"
    filepath_in = folder / "modelinput"

    df = compute_efficiency_buffers(
        filepath_in / "buffers.rst",
        filepath_out / "SediIn_kg.rst",
        filepath_out / "SediOut_kg.rst",
    )

    np.testing.assert_allclose(df["sedi_out"], exp_sedi_out, atol=1e-2)
    np.testing.assert_allclose(df["sedi_in"], exp_sedi_in, atol=1e-2)
    np.testing.assert_allclose(df["buff_sed"], buff_sed, atol=1e-2)


@pytest.mark.parametrize(
    "threshold,n_ranks,sum_sediment_load,mean_sediment_load",
    [
        (50, 10, 610229.44, 61022.945),
        (20, 2, 175243.22, 87621.61),
    ],
)
def test_identify_rank_sediment_loads(
    threshold, n_ranks, sum_sediment_load, mean_sediment_load, tmp_path
):
    """Test function for
    :func:`pywatemsedem.pywatemsedem.process_output.map_rank_sediment_loads``

    Parameters
    ----------
    threshold: float
        See
        :func:`pywatemsedem.pywatemsedem.process_output.analyse_cumulative_sediexport`
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

    filepath_out = folder / "modeloutput" / "SediExport_kg.rst"

    df_export, _ = identify_rank_sediment_loads(
        filepath_out,
        threshold,
        tmp_path / (tag + ".rst"),
        rst_endpoints=folder / "modeloutput" / "sewer_in.rst",
    )
    df_export = df_export[df_export["class"] != -9999]

    assert df_export.shape[0] == n_ranks
    assert np.sum(df_export["sedi_export"]) == approx(sum_sediment_load, abs=1)
    assert np.mean(df_export["sedi_export"]) == approx(mean_sediment_load, abs=1)


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
