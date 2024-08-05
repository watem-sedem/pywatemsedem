"""Test functions for postprocessing functions"""
import numpy as np
import pandas as pd
import pytest
from conftest import postprocess
from numpy.testing import assert_almost_equal

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
        with pytest.raises(KeyError) as excinfo:
            read_filestructure(sep=sep)
        assert "DataFrame should contain " in str(excinfo.value)
    else:
        df = read_filestructure(sep=sep)
        assert len(df) > 0


def test_get_grass_strips_statistics():
    """Test function for get_gras_strips_statistics for individual grass strips.
    This test function compares the arrays gras id, and coupled sedi in and out."""

    # run function
    _, _, df = compute_efficiency_grass_strips(
        postprocess.txt_routing,
        postprocess.rst_grasstrips_id,
        postprocess.rst_prclskrt,
        postprocess.rst_sediout,
    )

    df_test = pd.read_csv(postprocess.txt_gras_efficiency)

    assert_almost_equal(df["gras_id_target"].values, df_test["gras_id_target"].values)
    assert_almost_equal(df["gras_id_source"].values, df_test["gras_id_source"].values)
    assert_almost_equal(df["npixels_t"].values, df_test["npixels_t"].values)
    assert_almost_equal(df["eSTE"].values, df_test["STE"].values)
    assert_almost_equal(df["sediin"].values, df_test["sediin"].values)


def test_compute_netto_erosion_parcels():
    """Test function for computing netto erosion for individual parcels. It
    used two parcels rasters, one with a int16 codation (limited number of
    parcels) and one with a float64. The assert will test whether the sum, average
    and standard deviation on the netto erosion per parcel is equal for all parcels
    in the input data."""

    # script
    df_output, _ = compute_netto_erosion_parcels(
        postprocess.rst_prclskrt,
        postprocess.rst_watereros,
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
