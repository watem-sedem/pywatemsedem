from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from conftest import catchment_data, scenario_data
from numpy.testing import assert_almost_equal

from pywatemsedem.errors import (
    PywatemsedemVectorAttributeError,
    PywatemsedemVectorAttributeValueError,
)


class TestCreateModel:
    """Test class to test often used use cases in pywatemsedem model workflow.

    This class focuses on specific use cases that are assumed to be used in the API:

    - *test_all*: Create model input with base landuse, river vector, infrastructure
      vector, parcels vector and water vector.
    - *test_ommit_water* Create model input with base landuse, river vector,
      infrastructure vector, parcels vector with:
        - include grass strips vector
        - include technical tillage vector
    - *test_ommit_river* Create model input with base landuse, infrastructure vector,
       parcels vector and water vector
    - *test_ommit_inf* Create model input with base landuse, river vector, parcels
       vector and water vector
    - *test_ommit_parcels*: Create model input with base landuse, river vector,
       infrastructure vector and water vector.
    - *test_ommit_all*: Create model input with base landuse?

    The means to test equality of the rasters is the unique values and their number of
    occurence. Specically, the output C-factor, kTC and composite landuse rasters are
    tested as these are raster to which WaTEM/SEDEM is most senstive to. For the
    composite landuse raster, only number of agricultural pixels are tested, not the
    occurence of individual parcels.
    """

    @pytest.mark.saga
    def test_all(self, dummy_scenario):
        """Create WaTEM/SEDEM parcels raster with all possible input vectors/rasters"""
        dummy_scenario.vct_parcels = scenario_data.parcels
        dummy_scenario.catchm.vct_river = catchment_data.river
        dummy_scenario.catchm.vct_infrastructure_buildings = (
            catchment_data.infrastructure
        )
        dummy_scenario.catchm.vct_infrastructure_roads = catchment_data.roads
        dummy_scenario.catchm.vct_water = catchment_data.water

        dummy_scenario.composite_landuse = dummy_scenario.create_composite_landuse()
        dummy_scenario.cfactor = dummy_scenario.create_cfactor()

        dummy_scenario.ktc = dummy_scenario.create_ktc(
            dummy_scenario.choices.extensionparameters.ktc_low.value,
            dummy_scenario.choices.extensionparameters.ktc_high.value,
            dummy_scenario.choices.extensionparameters.ktc_limit.value,
            not dummy_scenario.choices.extensions.create_ktc_map.value,
        )

        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = dummy_scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [53, 4262, 1083, 3947, 534, 28234, 11331])

        # c-factor
        un, counts = np.unique(dummy_scenario.cfactor.arr, return_counts=True)

        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32735, 1087, 4288, 11334]))

        # kTC
        un, counts = np.unique(dummy_scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28234, 5345, 11331, 4534])

    @pytest.mark.saga
    def test_omit_water(self, dummy_scenario):
        """Omit water to create WaTEM/SEDEM parcels raster. This scenario is used
        standard in the initial development of pywatemsedem in Flanders."""
        dummy_scenario.vct_parcels = scenario_data.parcels
        dummy_scenario.catchm.vct_river = catchment_data.river
        dummy_scenario.catchm.vct_infrastructure_buildings = (
            catchment_data.infrastructure
        )
        dummy_scenario.catchm.vct_infrastructure_roads = catchment_data.roads

        # test prepare model input on C-factor, ktc and landuse-raster
        dummy_scenario.composite_landuse = dummy_scenario.create_composite_landuse()
        dummy_scenario.cfactor = dummy_scenario.create_cfactor()

        dummy_scenario.ktc = dummy_scenario.create_ktc(
            dummy_scenario.choices.extensionparameters.ktc_low.value,
            dummy_scenario.choices.extensionparameters.ktc_high.value,
            dummy_scenario.choices.extensionparameters.ktc_limit.value,
            not dummy_scenario.choices.extensions.create_ktc_map.value,
        )
        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = dummy_scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [2, 4288, 1087, 3965, 534, 28234, 11334])

        # c-factor
        un, counts = np.unique(dummy_scenario.cfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32735, 1087, 4288, 11334]))

        # kTC
        un, counts = np.unique(dummy_scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28234, 5375, 11334, 4501])

    @pytest.mark.saga
    def test_omit_parcels(self, dummy_scenario):
        """Omit parcels to create WaTEM/SEDEM parcels raster."""
        dummy_scenario.catchm.vct_river = catchment_data.river
        dummy_scenario.catchm.vct_infrastructure_buildings = (
            catchment_data.infrastructure
        )
        dummy_scenario.catchm.vct_infrastructure_roads = catchment_data.roads

        dummy_scenario.composite_landuse = dummy_scenario.create_composite_landuse()
        dummy_scenario.cfactor = dummy_scenario.create_cfactor()

        dummy_scenario.ktc = dummy_scenario.create_ktc(
            dummy_scenario.choices.extensionparameters.ktc_low.value,
            dummy_scenario.choices.extensionparameters.ktc_high.value,
            dummy_scenario.choices.extensionparameters.ktc_limit.value,
            not dummy_scenario.choices.extensions.create_ktc_map.value,
        )

        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = dummy_scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [4, 4139, 1315, 4047, 534, 28234, 11171])

        # c-factor
        un, counts = np.unique(dummy_scenario.cfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32819, 1315, 4139, 11171]))

        # kTC
        un, counts = np.unique(dummy_scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28234, 5454, 11171, 4585])

    @pytest.mark.saga
    def test_add_grass_strips(self, dummy_scenario):
        """Test creating composite landuse-, C-factor-, kTC-raster for case without
        parcels, but with grass strips vector."""
        dummy_scenario.vct_parcels = scenario_data.parcels
        dummy_scenario.catchm.vct_river = catchment_data.river
        dummy_scenario.catchm.vct_infrastructure_buildings = (
            catchment_data.infrastructure
        )
        dummy_scenario.catchm.vct_infrastructure_roads = catchment_data.roads
        # dummy_scenario.catchm.vct_water = catchment_data.water
        dummy_scenario.vct_grass_strips = scenario_data.grass_strips

        # test prepare model input on C-factor, ktc and landuse-raster
        dummy_scenario.composite_landuse = dummy_scenario.create_composite_landuse()
        dummy_scenario.cfactor = dummy_scenario.create_cfactor()

        dummy_scenario.ktc = dummy_scenario.create_ktc(
            dummy_scenario.choices.extensionparameters.ktc_low.value,
            dummy_scenario.choices.extensionparameters.ktc_high.value,
            dummy_scenario.choices.extensionparameters.ktc_limit.value,
            not dummy_scenario.choices.extensions.create_ktc_map.value,
        )

        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = dummy_scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-6, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(
            counts, [1529, 2, 3990, 1002, 3965, 534, 28234, 10188]
        )

        # c-factor
        un, counts = np.unique(dummy_scenario.cfactor.arr, return_counts=True)

        np.testing.assert_allclose(
            un,
            np.array(
                [
                    0.0,
                    0.001,
                    0.01,
                    0.028,
                    0.046,
                    0.082,
                    0.1,
                    0.118,
                    0.154,
                    0.19,
                    0.208,
                    0.262,
                    0.298,
                    0.37,
                ]
            ),
        )
        np.testing.assert_allclose(
            counts,
            np.array(
                [32735, 1002, 4317, 36, 198, 45, 222, 18, 425, 2, 17, 229, 10, 10188]
            ),
        )

        # kTC
        un, counts = np.unique(dummy_scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(
            un,
            np.array(
                [
                    -9.99900000e03,
                    8.19012646e-01,
                    8.19048198e-01,
                    8.19448238e-01,
                    8.19700171e-01,
                    8.20093704e-01,
                    8.20708421e-01,
                    8.21668642e-01,
                    8.25511499e-01,
                    8.29171296e-01,
                    8.34888088e-01,
                    8.57767012e-01,
                    9.13591694e-01,
                    9.66757094e-01,
                    1.0,
                    1.38216332e00,
                    2.19312119e00,
                    9.00000000e00,
                    9.99900000e03,
                ]
            ),
        )
        np.testing.assert_allclose(
            counts,
            np.array(
                [
                    28234,
                    76,
                    17,
                    17,
                    196,
                    21,
                    36,
                    198,
                    45,
                    222,
                    18,
                    425,
                    2,
                    17,
                    4992,
                    229,
                    10,
                    10188,
                    4501,
                ]
            ),
        )

    @pytest.mark.skip(reason="Test to fix later")
    @pytest.mark.saga
    def test_omit_river(self, dummy_scenario):
        """Omit river to create WaTEM/SEDEM inputs."""
        dummy_scenario.vct_parcels = scenario_data.parcels
        dummy_scenario.catchm.vct_infrastructure_buildings = (
            catchment_data.infrastructure
        )
        dummy_scenario.catchm.vct_infrastructure_roads = catchment_data.roads
        dummy_scenario.catchm.vct_water = catchment_data.water

        # test prepare model input on C-factor, ktc and landuse-raster
        dummy_scenario.composite_landuse = dummy_scenario.create_composite_landuse()
        dummy_scenario.cfactor = dummy_scenario.create_cfactor()

        dummy_scenario.ktc = dummy_scenario.create_ktc(
            dummy_scenario.choices.extensionparameters.ktc_low.value,
            dummy_scenario.choices.extensionparameters.ktc_high.value,
            dummy_scenario.choices.extensionparameters.ktc_limit.value,
            not dummy_scenario.choices.extensions.create_ktc_map.value,
        )
        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = dummy_scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [2, 4054, 1111, 3965, 534, 28234, 11544])

        # c-factor
        un, counts = np.unique(dummy_scenario.cfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32735, 1111, 4054, 11544]))

        # kTC
        un, counts = np.unique(dummy_scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28234, 5165, 11544, 4501])

    @pytest.mark.skip(reason="Test to fix later")
    @pytest.mark.saga
    def test_omit_infrastructure(self, dummy_scenario):
        """Omit infrastructure to create WaTEM/SEDEM parcels raster."""
        dummy_scenario.vct_parcels = scenario_data.parcels
        dummy_scenario.catchm.vct_river = catchment_data.river
        dummy_scenario.catchm.vct_water = catchment_data.water

        # test prepare model input on C-factor, ktc and landuse-raster
        dummy_scenario.composite_landuse = dummy_scenario.create_composite_landuse()
        dummy_scenario.cfactor = dummy_scenario.create_cfactor()

        dummy_scenario.ktc = dummy_scenario.create_ktc(
            dummy_scenario.choices.extensionparameters.ktc_low.value,
            dummy_scenario.choices.extensionparameters.ktc_high.value,
            dummy_scenario.choices.extensionparameters.ktc_limit.value,
            not dummy_scenario.choices.extensions.create_ktc_map.value,
        )
        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = dummy_scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [2, 4054, 1111, 3965, 534, 28234, 11544])

        # c-factor
        un, counts = np.unique(dummy_scenario.cfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32735, 1111, 4054, 11544]))

        # kTC
        un, counts = np.unique(dummy_scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28234, 5165, 11544, 4501])

    @pytest.mark.skip(reason="Test to fix later")
    @pytest.mark.saga
    def test_ommit_all(self, dummy_scenario):
        """Ommit all input sources to create WaTEM/SEDEM parcels raster, except base
        land-use raster"""

        # test prepare model input on C-factor, ktc and landuse-raster
        dummy_scenario.composite_landuse = dummy_scenario.create_composite_landuse()
        dummy_scenario.cfactor = dummy_scenario.create_cfactor()

        dummy_scenario.ktc = dummy_scenario.create_ktc(
            dummy_scenario.choices.extensionparameters.ktc_low.value,
            dummy_scenario.choices.extensionparameters.ktc_high.value,
            dummy_scenario.choices.extensionparameters.ktc_limit.value,
            not dummy_scenario.choices.extensions.create_ktc_map.value,
        )
        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = dummy_scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [2, 4054, 1111, 3965, 534, 28234, 11544])

        # c-factor
        un, counts = np.unique(dummy_scenario.cfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32735, 1111, 4054, 11544]))

        # kTC
        un, counts = np.unique(dummy_scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28234, 5165, 11544, 4501])


class TestEndpoints:
    """Tests functionalities for endpoints"""

    @pytest.mark.saga
    def test_vct_endpoints(self, dummy_scenario):
        """Test vector endpoints assignment"""
        dummy_scenario.catchm.vct_river = catchment_data.river
        dummy_scenario.catchm.vct_infrastructure_buildings = (
            catchment_data.infrastructure
        )
        dummy_scenario.catchm.vct_infrastructure_roads = catchment_data.roads
        dummy_scenario.catchm.vct_water = catchment_data.water

        # test unique records and counts
        dummy_scenario.choices.extensions.include_sewers = True
        dummy_scenario.vct_endpoints = scenario_data.endpoints
        dummy_scenario.remove_endpoints_not_under_infrastructure()

        # endpoints
        un, counts = np.unique(dummy_scenario.endpoints.arr, return_counts=True)
        np.testing.assert_allclose(un, [0.0, 0.75])
        np.testing.assert_allclose(counts, [49041, 403])

        # endpoints_ids
        un, counts = np.unique(dummy_scenario.endpoints_id.arr, return_counts=True)
        np.testing.assert_allclose(un, [0, 1.0, 2.0])
        np.testing.assert_allclose(counts, [48970, 394, 80])

    @pytest.mark.saga
    def test_vct_endpoints_efficiency_value_error(self, dummy_scenario):
        """Test wrong value in 'efficiency' attribute"""
        # feed negative efficiency values
        df = gpd.read_file(scenario_data.endpoints)
        df["efficiency"] = -0.1
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            dummy_scenario.vct_endpoints = df

        df["efficiency"] = 10
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            dummy_scenario.vct_endpoints = df

    @pytest.mark.saga
    def test_vct_endpoints_type_id_value_error(self, dummy_scenario):
        """Test wrong value in 'type_id' attribute"""
        # feed invalid type_id
        df = gpd.read_file(scenario_data.endpoints)
        df["type_id"] = np.nan
        with pytest.raises(
            ValueError, match="Please define a 'type_id' for every record."
        ):
            dummy_scenario.vct_endpoints = df


class TestParcels:
    @pytest.mark.saga
    def test_vct_parcels(self, recwarn, dummy_scenario):
        """Test assigment parcels"""
        # test assigment property
        dummy_scenario.vct_parcels = scenario_data.parcels

        # test type
        assert dummy_scenario.parcels.arr.dtype == np.int16
        assert dummy_scenario.parcels_ids.arr.dtype == np.int16

        # test number of values
        un = np.unique(dummy_scenario.parcels_ids.arr)
        np.testing.assert_allclose(len(un), 388)

        # test if parcels and parcels ids is equal IN CASE max id <= 32767
        np.testing.assert_allclose(
            dummy_scenario.parcels.arr, dummy_scenario.parcels_ids.arr
        )

        # manipulate parcels_ids and set above 32757 to test difference parcels_ids
        # and parcels getter
        df = gpd.read_file(scenario_data.parcels)
        df["NR"] = 1000**2

        dummy_scenario.vct_parcels = df
        # max id should be max(int16)
        assert np.max(dummy_scenario.parcels.arr) < 2**15
        # any higher id should have been reduced to fit
        assert np.max(dummy_scenario.parcels_ids.arr) == (1000**2) % (2**15)

        # catch warning
        w = recwarn.pop(UserWarning)
        assert "32767" in str(w.message)

    @pytest.mark.saga
    def test_vct_parcels_value_error_landuse(self, dummy_scenario):
        """Test wrong value in 'LANDUSE' attribute parcels vector"""
        # feed incorrect values for column "LANDUSE"
        df = gpd.read_file(scenario_data.parcels)
        df["LANDUSE"] = -10
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector can only contain values",
        ):
            dummy_scenario.vct_parcels = df

    @pytest.mark.saga
    def test_vct_parcels_attribute_error_landuse(self, dummy_scenario):
        """Test wrong attributes in parcels vector"""
        df = gpd.read_file(scenario_data.parcels)
        df = df.drop(columns="LANDUSE")
        with pytest.raises(
            PywatemsedemVectorAttributeError, match="input vector should contain"
        ):
            dummy_scenario.vct_parcels = df

    @pytest.mark.saga
    def test_vct_parcels_value_error_cfactor(self, dummy_scenario):
        """Test wrong value in 'C_crop' attribute parcels vector"""
        df = gpd.read_file(scenario_data.parcels)
        df["C_crop"] = -0.1
        with pytest.raises(
            PywatemsedemVectorAttributeValueError, match="vector should contain values"
        ):
            dummy_scenario.vct_parcels = df

    @pytest.mark.saga
    def test_vct_parcels_nan_value_cfactor(self, dummy_scenario):
        """Test if all nan in 'C_crop' is allowed"""
        df = gpd.read_file(scenario_data.parcels)
        df["C_crop"] = np.nan
        dummy_scenario.vct_parcels = df
        assert True


class TestGrassStrips:
    """Tests functionalities for grass strips:

    - source-oriented (grass strips, buffers)
    - symptom-oriented (tillage)
    """

    @pytest.mark.saga
    def test_vct_grass_strips(self, recwarn, dummy_scenario):
        """Test vector assignment"""
        dummy_scenario.vct_grass_strips = scenario_data.grass_strips

        # test output
        un, counts = np.unique(dummy_scenario.grass_strips.arr, return_counts=True)

        np.testing.assert_allclose(
            un,
            np.array(
                [
                    -9999,
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                    33,
                    34,
                    35,
                    36,
                    37,
                    38,
                    39,
                    40,
                    41,
                    42,
                    43,
                    44,
                    45,
                    46,
                    47,
                    48,
                    49,
                    50,
                    51,
                    52,
                    53,
                    54,
                    55,
                    56,
                    57,
                    58,
                    59,
                    60,
                    61,
                    63,
                    64,
                    65,
                    66,
                    67,
                    68,
                    69,
                    70,
                    71,
                    72,
                    73,
                    74,
                    75,
                    76,
                    77,
                    78,
                    79,
                    80,
                    81,
                    82,
                    83,
                    84,
                    85,
                    86,
                    87,
                    88,
                    89,
                    90,
                    91,
                    92,
                    93,
                    94,
                    95,
                    96,
                    97,
                    98,
                    99,
                    100,
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    111,
                    112,
                    113,
                    114,
                ]
            ),
        )
        np.testing.assert_allclose(
            counts,
            np.array(
                [
                    47318,
                    6,
                    16,
                    22,
                    17,
                    4,
                    9,
                    14,
                    30,
                    16,
                    28,
                    14,
                    25,
                    26,
                    13,
                    3,
                    17,
                    7,
                    24,
                    7,
                    16,
                    20,
                    32,
                    13,
                    11,
                    27,
                    5,
                    13,
                    13,
                    20,
                    15,
                    20,
                    5,
                    5,
                    6,
                    10,
                    16,
                    2,
                    19,
                    38,
                    5,
                    26,
                    14,
                    15,
                    7,
                    33,
                    11,
                    12,
                    16,
                    6,
                    20,
                    20,
                    21,
                    13,
                    28,
                    17,
                    30,
                    108,
                    43,
                    3,
                    7,
                    15,
                    8,
                    32,
                    16,
                    9,
                    33,
                    4,
                    15,
                    38,
                    28,
                    2,
                    21,
                    30,
                    51,
                    53,
                    26,
                    39,
                    11,
                    4,
                    3,
                    16,
                    14,
                    19,
                    2,
                    38,
                    29,
                    20,
                    11,
                    24,
                    16,
                    52,
                    5,
                    19,
                    30,
                    16,
                    40,
                    5,
                    14,
                    10,
                    19,
                    34,
                    8,
                    24,
                    16,
                    26,
                    22,
                    7,
                    25,
                    9,
                    20,
                    8,
                    10,
                    11,
                    10,
                ]
            ),
        )

    @pytest.mark.saga
    def test_vct_grass_strips_width_value_error(self, tmp_path, dummy_scenario):
        """Test wrong value in 'width' attribute"""
        fname = Path(tmp_path) / "temp.shp"
        df = gpd.read_file(scenario_data.grass_strips)
        df["width"] = -10
        df.to_file(fname)
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            dummy_scenario.vct_grass_strips = fname

    @pytest.mark.saga
    def test_vct_grass_strips_attribute_error(self, tmp_path, dummy_scenario):
        """Test wrong attributes"""
        fname = Path(tmp_path) / "temp.shp"
        df = gpd.read_file(scenario_data.grass_strips)
        df = df.drop(columns="width")
        df.to_file(fname)
        with pytest.raises(
            PywatemsedemVectorAttributeError, match="input vector should contain"
        ):
            dummy_scenario.vct_grass_strips = fname


class TestBuffers:
    """Tests functionalities for buffers
    #TODO: write test for buffer outlet
    """

    @pytest.mark.saga
    def test_vct_buffers(self, recwarn, dummy_scenario):
        """Test vector assignment"""
        dummy_scenario.choices.extensions.include_buffers = False
        dummy_scenario.vct_buffers = scenario_data.buffers
        dummy_scenario.catchm.vct_river = catchment_data.river
        # catch warning
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message) == "Include buffers' in 'dict_ecm_options' is equal to 0. "
            "Will not include buffers."
        )

        # set include buffers on
        dummy_scenario.choices.extensions.include_buffers = True
        # test output
        un, counts = np.unique(dummy_scenario.buffers.arr, return_counts=True)
        np.testing.assert_allclose(un, [0, 1, 2, 16385, 16386])
        np.testing.assert_allclose(counts, [49437, 1, 1, 2, 3])

        # Test if option 'Include buffers' is set off
        dummy_scenario.choices.extensions.include_buffers = False
        dummy_scenario.vct_buffers = scenario_data.buffers
        w = recwarn.pop(UserWarning)  # make sure prev waring is popped
        assert dummy_scenario.buffers.is_empty()  # calling buffers raises warning
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message) == "Option 'Include buffers' in erosion control measure"
            " options is 0, returning None"
        )
        dummy_scenario.choices.extensions.include_buffers = True

    def test_warning_buffers_overlap_rivers(self, dummy_scenario):
        """#TODO"""
        assert True

    @pytest.mark.saga
    def test_vct_buffers_eff_value_error(self, dummy_scenario):
        """Test wrong value in 'eff' attribute"""
        df = gpd.read_file(scenario_data.buffers)
        df["eff"] = -10
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            dummy_scenario.vct_buffers = df

    @pytest.mark.saga
    def test_vct_buffers_attribute_error(self, dummy_scenario):
        """Test wrong attribute"""
        df = gpd.read_file(scenario_data.buffers)
        df = df.drop(columns="eff")
        with pytest.raises(
            PywatemsedemVectorAttributeError, match="input vector should contain"
        ):
            dummy_scenario.vct_buffers = df


class TestDitches:
    """Tests functionalities for ditches"""

    def test_vct_ditches(self):
        """
        #TODO
        """
        assert True


class TestConductiveDams:
    """Tests functionalities for conductive dams"""

    def test_vct_conductive_dams(self):
        """
        #TODO
        """
        assert True


class TestOutlets:
    """Tests functionalities for outlets"""

    @pytest.mark.saga
    def test_outlets(self, dummy_scenario):
        """Test vector assignment"""
        dummy_scenario.vct_outlets = scenario_data.outlets
        arr, counts = np.unique(dummy_scenario.outlets.arr, return_counts=True)
        np.testing.assert_allclose(arr, [-9999, 1, 2])
        np.testing.assert_allclose(counts, [49442, 1, 1])


class TestForceRouting:
    """Tests functionalities for force routing"""

    @pytest.mark.saga
    def test_forcerouting(self, dummy_scenario):
        """Test vector assignment"""
        dummy_scenario.force_routing = scenario_data.force_routing
        df = dummy_scenario.force_routing
        assert_almost_equal(
            df["fromX"].values, [163891.888238, 165939.062062], decimal=0
        )
        assert_almost_equal(df["toX"].values, [164574.279513, 166268.492332], decimal=0)
        assert_almost_equal(
            df["fromY"].values, [167144.040010, 167638.185416], decimal=0
        )
        assert_almost_equal(df["toY"].values, [167449.939547, 168320.576690], decimal=0)
        assert_almost_equal(df["fromcol"].values, [80, 182])
        assert_almost_equal(df["fromrow"].values, [119, 95])
        assert_almost_equal(df["torow"].values, [104, 60])
        assert_almost_equal(df["tocol"].values, [114, 199])
