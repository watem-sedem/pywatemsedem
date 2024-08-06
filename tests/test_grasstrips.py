import numpy as np
import pytest
from conftest import grassstripsdata

from pywatemsedem.grasstrips import (
    _check_grass_strip_width,
    expand_grass_strips_with_triggers,
    get_width_grass_strips,
    scale_cfactor_linear,
    scale_cfactor_with_grass_strips_width,
    scale_ktc_linear,
    scale_ktc_with_grass_strip_width,
    scale_ktc_zhang,
)


def test_expand_grass_strips_with_triggers():
    """Test function for expand grass strips with triggers"""

    # triggers, for instance road pixels
    arr_triggers = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    # parcel ids
    arr_parcels_id = np.array([[0, 3, 3, 3], [1, 0, 2, 2], [1, 1, 0, 2], [1, 1, 1, 0]])
    # input
    arr_grass_strips = np.array(
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 1], [0, 0, 0, 1]]
    )
    # output
    arr_grass_strips_expanded = np.array(
        [[0, 0, 0, 0], [0, 0, 1, 1], [0, 0, 0, 1], [0, 0, 0, 1]]
    )
    # test 1
    arr_out = expand_grass_strips_with_triggers(
        arr_grass_strips, arr_triggers, arr_parcels_id
    )

    np.testing.assert_allclose(
        arr_out.astype(int), arr_grass_strips_expanded.astype(int)
    )

    # test 2
    arr_grass_strips = np.array(
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 1], [0, 0, 0, 1]]
    )
    arr_grass_strips_expanded = np.array(
        [[0, 0, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1], [0, 0, 0, 1]]
    )

    arr_out = expand_grass_strips_with_triggers(
        arr_grass_strips, arr_triggers, arr_parcels_id
    )

    np.testing.assert_allclose(
        arr_out.astype(int), arr_grass_strips_expanded.astype(int)
    )

    # test 3
    arr_grass_strips = np.array(
        [[0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 1]]
    )
    arr_grass_strips_expanded = np.array(
        [[0, 0, 0, 0], [0, 0, 1, 1], [0, 0, 0, 1], [0, 0, 0, 1]]
    )

    arr_out = expand_grass_strips_with_triggers(
        arr_grass_strips, arr_triggers, arr_parcels_id
    )

    np.testing.assert_allclose(
        arr_out.astype(int), arr_grass_strips_expanded.astype(int)
    )

    # test 4
    arr_grass_strips = np.array(
        [[0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 1, 1]]
    )
    arr_grass_strips_expanded = np.array(
        [[0, 0, 0, 0], [0, 0, 1, 1], [0, 1, 0, 1], [0, 1, 1, 1]]
    )

    arr_out = expand_grass_strips_with_triggers(
        arr_grass_strips, arr_triggers, arr_parcels_id
    )

    np.testing.assert_allclose(
        arr_out.astype(int), arr_grass_strips_expanded.astype(int)
    )

    # format of trigger is wrong
    arr_triggers = np.array([[1, 2, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    with pytest.raises(Exception) as excinfo:
        expand_grass_strips_with_triggers(
            arr_grass_strips, arr_triggers, arr_parcels_id
        )
    assert "Input trigger can only contain 0's and 1's (and no data) values." in str(
        excinfo.value
    )

    # test error message, size not equal
    arr_triggers = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])

    arr_grass_strips = np.array([[0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 1, 1]])

    with pytest.raises(IOError) as excinfo:
        expand_grass_strips_with_triggers(
            arr_grass_strips, arr_triggers, arr_parcels_id
        )
    assert " has a different size than the input triggers array " in str(excinfo.value)

    # test mode
    arr_triggers = np.array(
        [
            [1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1],
        ]
    )
    arr_grass = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )

    # expand grass strips in ordinal + cardinal direction
    arr = expand_grass_strips_with_triggers(arr_grass, arr_triggers, mode=1)
    arr_test = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )

    np.testing.assert_allclose(arr, arr_test)

    # only in cardinal direction
    arr = expand_grass_strips_with_triggers(arr_grass, arr_triggers, mode=2)
    arr_test = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )

    np.testing.assert_allclose(arr, arr_test)

    # only in ordinal direction
    arr = expand_grass_strips_with_triggers(arr_grass, arr_triggers, mode=3)
    arr_test = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )

    np.testing.assert_allclose(arr, arr_test)


@pytest.mark.parametrize(
    "arr_width,message",
    [
        (np.array([np.nan]), "(nan) are not allowed"),
        (np.array([np.nan, 3.0, 2.0]), "(nan) are not allowed"),
        (np.array(["a", "b"]), "should be a numerical array"),
    ],
)
def test_check_grass_strip_width_wrong_input(arr_width, message):
    """Input widths shouldbe numbers and not contain any Nan values"""
    with pytest.raises(ValueError) as exc_info:
        _check_grass_strip_width(arr_width)
    assert message in str(exc_info.value)


def test_check_grass_strip_contains_lower_1():
    """Input widths shouldbe numbers and not contain any Nan values"""
    width_updated = _check_grass_strip_width(np.array([1.0, 2.0, 0.5]))
    np.testing.assert_allclose(np.array([1.0, 2.0, 1.0]), width_updated)


def test_scaling_functions():
    """ "Test scaling function"""

    arr_ktc, arr_sve = scale_ktc_with_grass_strip_width(
        grassstripsdata.df_ktc["width"], scale_ktc_zhang, ktc_high=12
    )

    np.testing.assert_allclose(arr_ktc, grassstripsdata.df_ktc["ktc_zhang"])
    np.testing.assert_allclose(arr_sve, grassstripsdata.df_ktc["ste_zhang"])

    arr_ktc, arr_sve = scale_ktc_with_grass_strip_width(
        grassstripsdata.df_ktc["width"],
        scale_ktc_linear,
        ktc_high=12,
        ktc_low=3,
        resolution=20,
    )

    np.testing.assert_allclose(arr_ktc, grassstripsdata.df_ktc["ktc_linear"])
    np.testing.assert_allclose(arr_sve, grassstripsdata.df_ktc["ste_linear"])


def test_get_width_grass_strips():
    """Test function for  estimating width gras strips"""
    arr = np.array(
        [
            [0, 307.8639941, 768.7768236, 5.167752687],
            [0, 385.0256183, 4500.58521, 27.22952422],
            [9, 203.4975203, 850.8988838, 9],
            [8, 138.2777618, 825.7831474, 8],
            [15, 1495.734103, 9629.81158, 15],
            [21, 571.9997959, 5332.482918, 21],
            [9, 546.3757948, 2718.030001, 9],
            [3, 189.8090261, 114.3070344, 3],
            [0, 45.63486343, 54.31478505, 2.699869064],
            [0, 832.5668865, 23223.4029, 66.36875741],
            [0, 1282.346203, 31752.06523, 54.08388417],
            [3, 283.6296509, 565.4525936, 3],
            [10, 75.04867666, 296.8826299, 10],
            [40, 582.1224539, 7511.109669, 40],
            [4, 116.6362692, 216.818456, 4],
            [0, 705.7933573, 6361.216782, 19.05456668],
            [0, 924.2065313, 6695.056121, 14.97340414],
            [0, 231.7988316, 2547.380504, 29.47536609],
            [0, 256.7227604, 3253.917023, 34.76566064],
            [12, 470.5881752, 2786.526555, 12],
            [12, 211.4470854, 936.01158, 12],
            [12, 247.7048717, 1111.922637, 12],
            [0, 482.7932918, 679.9801339, 2.850518435],
            [9, 262.1769642, 364.5964782, 9],
        ]
    )

    resolution = 20

    # script
    arr_width_gras_strips = get_width_grass_strips(
        arr[:, 0],
        arr[:, 1],
        arr[:, 2],
        resolution,
    )

    np.testing.assert_allclose(arr_width_gras_strips, arr[:, 3], atol=1e-2)


def test_scaling_functions_cfactor():
    """ "Test scaling function"""
    arr_cfactor = scale_cfactor_with_grass_strips_width(
        grassstripsdata.df_ktc["width"],
        scale_cfactor_linear,
        resolution=20,
    )

    np.testing.assert_allclose(arr_cfactor, grassstripsdata.df_ktc["cfactor_linear"])
