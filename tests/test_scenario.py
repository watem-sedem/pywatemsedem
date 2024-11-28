from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from conftest import scenario_data
from numpy.testing import assert_almost_equal

from pywatemsedem.errors import (
    PywatemsedemVectorAttributeError,
    PywatemsedemVectorAttributeValueError,
)
from pywatemsedem.geo.vectors import AbstractVector


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
    def test_all(self, scenario):
        """Create WaTEM/SEDEM parcels raster with all possible input vectors/rasters"""
        scenario.vct_parcels = scenario_data.parcels
        scenario.composite_landuse = scenario.create_composite_landuse()
        scenario.cfactor = scenario.create_cfactor(
            bool(scenario.choices.dict_ecm_options["UseTeelttechn"])
        )
        scenario.ktc = scenario.create_ktc(
            scenario.choices.dict_variables["ktc low"],
            scenario.choices.dict_variables["ktc high"],
            scenario.choices.dict_variables["ktc limit"],
            scenario.choices.dict_model_options["UserProvidedKTC"],
        )

        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [53, 4030, 1107, 3947, 534, 28236, 11537])

        # c-factor
        un, counts = np.unique(scenario.cfactor.arr, return_counts=True)

        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32737, 1111, 4056, 11540]))

        # kTC
        un, counts = np.unique(scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28236, 5137, 11537, 4534])

    @pytest.mark.saga
    def test_omit_water(self, scenario):
        """Omit water to create WaTEM/SEDEM parcels raster. This scenario is used standard
        in the initial development of pywatemsedem in Flanders."""
        scenario.vct_parcels = scenario_data.parcels
        scenario.catchm._vct_water = AbstractVector()

        # test prepare model input on C-factor, ktc and landuse-raster
        scenario.composite_landuse = scenario.create_composite_landuse()
        scenario.cfactor = scenario.create_cfactor(
            bool(scenario.choices.dict_ecm_options["UseTeelttechn"])
        )
        scenario.ktc = scenario.create_ktc(
            scenario.choices.dict_variables["ktc low"],
            scenario.choices.dict_variables["ktc high"],
            scenario.choices.dict_variables["ktc limit"],
            scenario.choices.dict_model_options["UserProvidedKTC"],
        )
        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [2, 4056, 1111, 3965, 534, 28236, 11540])

        # c-factor
        un, counts = np.unique(scenario.cfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32737, 1111, 4056, 11540]))

        # kTC
        un, counts = np.unique(scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28236, 5167, 11540, 4501])

    @pytest.mark.saga
    def test_omit_parcels(self, scenario):
        """Omit parcels to create WaTEM/SEDEM parcels raster."""
        scenario.composite_landuse = scenario.create_composite_landuse()
        scenario.cfactor = scenario.create_cfactor(
            bool(scenario.choices.dict_ecm_options["UseTeelttechn"])
        )
        scenario.ktc = scenario.create_ktc(
            scenario.choices.dict_variables["ktc low"],
            scenario.choices.dict_variables["ktc high"],
            scenario.choices.dict_variables["ktc limit"],
            scenario.choices.dict_model_options["UserProvidedKTC"],
        )

        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(counts, [2, 4056, 1111, 3965, 534, 28236, 11540])

        # c-factor
        un, counts = np.unique(scenario.cfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0.0, 0.001, 0.01, 0.37]))
        np.testing.assert_allclose(counts, np.array([32737, 1111, 4056, 11540]))

        # kTC
        un, counts = np.unique(scenario.ktc.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9.999e03, 1.000e00, 9.000e00, 9.999e03])
        np.testing.assert_allclose(counts, [28236, 5167, 11540, 4501])

    @pytest.mark.saga
    def test_add_grass_strips(self, scenario):
        """Test creating composite landuse-, C-factor-, kTC-raster for case without
        water, but with adding grass strips."""
        scenario.vct_parcels = scenario_data.parcels
        scenario.catchm._vct_water = AbstractVector()

        scenario.vct_grass_strips = scenario_data.grass_strips
        scenario.choices.dict_ecm_options["UseGras"] = 1

        # test prepare model input on C-factor, ktc and landuse-raster
        scenario.composite_landuse = scenario.create_composite_landuse()
        scenario.cfactor = scenario.create_cfactor(
            bool(scenario.choices.dict_ecm_options["UseTeelttechn"])
        )
        scenario.ktc = scenario.create_ktc(
            scenario.choices.dict_variables["ktc low"],
            scenario.choices.dict_variables["ktc high"],
            scenario.choices.dict_variables["ktc limit"],
            scenario.choices.dict_model_options["UserProvidedKTC"],
        )

        # Composite land-use (test number of parcels pixels, and not unique id's)
        arr = scenario.composite_landuse.arr
        arr[arr > 0] = 1
        un, counts = np.unique(arr, return_counts=True)
        np.testing.assert_allclose(un, [-6, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0])
        np.testing.assert_allclose(
            counts, [1529, 2, 3844, 1011, 3965, 534, 28236, 10323]
        )

        # c-factor
        un, counts = np.unique(scenario.cfactor.arr, return_counts=True)

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
                [32737, 1011, 4164, 39, 199, 43, 201, 19, 433, 2, 15, 245, 13, 10323]
            ),
        )

        # kTC
        un, counts = np.unique(scenario.ktc.arr, return_counts=True)
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
                    28236,
                    66,
                    27,
                    17,
                    189,
                    21,
                    39,
                    199,
                    43,
                    201,
                    19,
                    433,
                    2,
                    15,
                    4855,
                    245,
                    13,
                    10323,
                    4501,
                ]
            ),
        )

    @pytest.mark.saga
    def test_omit_river(self, scenario):
        """Omit river to create WaTEM/SEDEM inputs."""
        # TODO

        assert True

    @pytest.mark.saga
    def test_omit_infrastructure(self, scenario):
        """Omit infrastructure to create WaTEM/SEDEM parcels raster."""
        # TODO
        assert True

    @pytest.mark.saga
    def test_ommit_all(self, scenario):
        """Ommit all input sources to create WaTEM/SEDEM parcels raster, except base land-use
        raster"""
        # TODO
        assert True


class TestEndpoints:
    """Tests functionalities for endpoints"""

    @pytest.mark.saga
    def test_vct_endpoints(self, scenario):
        """Test vector endpoints assignment"""

        # test unique records and counts
        scenario.choices.dict_model_options["Include sewers"] = 1
        scenario.choices.dict_variables["SewerInletEff"] = 1
        scenario.vct_endpoints = scenario_data.endpoints

        # endpoints
        un, counts = np.unique(scenario.endpoints.arr, return_counts=True)
        np.testing.assert_allclose(un, [0.0, 1])
        np.testing.assert_allclose(counts, [49040, 404])

        # endpoints_ids
        un, counts = np.unique(scenario.endpoints_id.arr, return_counts=True)
        np.testing.assert_allclose(un, [0, 1.0, 2.0])
        np.testing.assert_allclose(counts, [48970, 394, 80])

    @pytest.mark.saga
    def test_vct_endpoints_efficiency(self, scenario, recwarn):
        """Test vector endpoints assignment with user-defined 'efficiency' column"""
        # feed a self-defined efficiency column (with 10 linestring to 75 %, remaining
        # NaN)
        df = gpd.read_file(scenario_data.endpoints)
        df["efficiency"] = 0.75
        scenario.choices.dict_variables["SewerInletEff"] = 1
        scenario.choices.dict_model_options["Include sewers"] = 1
        scenario.vct_endpoints = df
        un, counts = np.unique(scenario.endpoints.arr, return_counts=True)

        np.testing.assert_allclose(un, [0.0, 0.75])
        np.testing.assert_allclose(counts, [49040, 404])

        # feed a self-defined efficiency column (with all NaN)
        df = gpd.read_file(scenario_data.endpoints)
        df["efficiency"] = np.nan
        scenario.vct_endpoints = df
        un, counts = np.unique(scenario.endpoints.arr, return_counts=True)
        np.testing.assert_allclose(un, [0.0, 1.0])
        np.testing.assert_allclose(counts, [49040, 404])

        # catch warning from inputting all NaN-values to efficiency column
        w = recwarn.pop(UserWarning)
        assert (
            "The efficiency is not defined for all sewer line strings, assigning "
            "'SewerInletEff'-value" in str(w.message)
        )

    @pytest.mark.saga
    def test_vct_endpoints_efficiency_value_error(self, scenario):
        """Test wrong value in 'efficiency' attribute"""
        # feed negative efficiency values
        df = gpd.read_file(scenario_data.endpoints)
        df["efficiency"] = -0.1
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            scenario.vct_endpoints = df

        df["efficiency"] = 10
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            scenario.vct_endpoints = df

    @pytest.mark.saga
    def test_vct_endpoints_type_id_value_error(self, scenario):
        """Test wrong value in 'type_id' attribute"""
        # feed invalid type_id
        df = gpd.read_file(scenario_data.endpoints)
        df["type_id"] = np.nan
        with pytest.raises(
            ValueError, match="Please define a 'type_id' for every record."
        ):
            scenario.vct_endpoints = df


class TestParcels:
    @pytest.mark.saga
    def test_vct_parcels(self, scenario, recwarn):
        """Test assigment parcels"""
        # test assigment property
        scenario.vct_parcels = scenario_data.parcels

        # test type
        assert scenario.parcels.arr.dtype == np.int16
        assert scenario.parcels_ids.arr.dtype == np.float64

        # test number of values
        un = np.unique(scenario.parcels_ids.arr)
        np.testing.assert_allclose(len(un), 384)

        # test if parcels and parcels ids is equal IN CASE max id <= 32767
        np.testing.assert_allclose(scenario.parcels.arr, scenario.parcels_ids.arr)

        # manipulate parcels_ids and set above 32757 to test difference parcels_ids
        # and parcels getter
        df = gpd.read_file(scenario_data.parcels)
        df["NR"] = 1000**2

        scenario.vct_parcels = df
        assert np.max(scenario.parcels.arr) == 32767
        assert np.max(scenario.parcels_ids.arr) == 1000**2

        # catch warning
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message) == "Parcels raster has values higher than the maximum "
            "allowed number for WaTEM/SEDEM definition (i.e. 32767). "
            "Setting values above 32767 to 32767."
        )

    @pytest.mark.saga
    def test_vct_parcels_value_error_landuse(self, scenario):
        """Test wrong value in 'LANDUSE' attribute parcels vector"""
        # feed incorrect values for column "LANDUSE"
        df = gpd.read_file(scenario_data.parcels)
        df["LANDUSE"] = -10
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector can only contain values",
        ):
            scenario.vct_parcels = df

    @pytest.mark.saga
    def test_vct_parcels_attribute_error_landuse(self, scenario):
        """Test wrong attributes in parcels vector"""
        df = gpd.read_file(scenario_data.parcels)
        df = df.drop(columns="LANDUSE")
        with pytest.raises(
            PywatemsedemVectorAttributeError, match="input vector should contain"
        ):
            scenario.vct_parcels = df

    @pytest.mark.saga
    def test_vct_parcels_value_error_cfactor(self, scenario):
        """Test wrong value in 'C_crop' attribute parcels vector"""
        df = gpd.read_file(scenario_data.parcels)
        df["C_crop"] = -0.1
        with pytest.raises(
            PywatemsedemVectorAttributeValueError, match="vector should contain values"
        ):
            scenario.vct_parcels = df

    @pytest.mark.saga
    def test_vct_parcels_nan_value_cfactor(self, scenario):
        """Test if all nan in 'C_crop' is allowed"""
        df = gpd.read_file(scenario_data.parcels)
        df["C_crop"] = np.nan
        scenario.vct_parcels = df
        assert True


class TestGrassStrips:
    """Tests functionalities for grass strips:

    - source-oriented (grass strips, buffers)
    - symptom-oriented (tillage)
    """

    @pytest.mark.saga
    def test_vct_grass_strips(self, scenario, recwarn):
        """Test vector assignment"""
        scenario.choices.dict_ecm_options["UseGras"] = 0
        scenario.vct_grass_strips = scenario_data.grass_strips

        # set use gras to 1
        scenario.choices.dict_ecm_options["UseGras"] = 1

        # test output
        un, counts = np.unique(scenario.grass_strips.arr, return_counts=True)

        np.testing.assert_allclose(un, [-9999.0] + list(range(0, 115)))
        np.testing.assert_allclose(
            counts,
            np.array(
                [
                    47318,
                    7,
                    14,
                    27,
                    37,
                    26,
                    15,
                    3,
                    8,
                    13,
                    15,
                    27,
                    4,
                    10,
                    3,
                    28,
                    27,
                    15,
                    7,
                    11,
                    13,
                    22,
                    23,
                    20,
                    28,
                    14,
                    7,
                    6,
                    9,
                    5,
                    17,
                    5,
                    30,
                    20,
                    7,
                    4,
                    19,
                    108,
                    13,
                    25,
                    6,
                    10,
                    4,
                    15,
                    13,
                    10,
                    29,
                    26,
                    22,
                    8,
                    43,
                    12,
                    4,
                    11,
                    16,
                    1,
                    8,
                    8,
                    5,
                    7,
                    20,
                    12,
                    18,
                    19,
                    8,
                    29,
                    36,
                    5,
                    5,
                    16,
                    12,
                    29,
                    25,
                    32,
                    21,
                    25,
                    7,
                    8,
                    5,
                    30,
                    28,
                    23,
                    22,
                    17,
                    30,
                    3,
                    27,
                    11,
                    11,
                    23,
                    20,
                    10,
                    13,
                    25,
                    38,
                    2,
                    2,
                    15,
                    52,
                    26,
                    33,
                    10,
                    30,
                    32,
                    21,
                    18,
                    39,
                    9,
                    58,
                    53,
                    22,
                    25,
                    16,
                    20,
                    14,
                    16,
                ]
            ),
        )

        # Test if option 'UseGras' is set off
        scenario.choices.dict_ecm_options["UseGras"] = 0
        scenario.vct_grass_strips = scenario_data.grass_strips
        scenario.choices.dict_ecm_options["UseGras"] = 1

    @pytest.mark.saga
    def test_vct_grass_strips_width_value_error(self, scenario, tmp_path):
        """Test wrong value in 'width' attribute"""
        fname = Path(tmp_path) / "temp.shp"
        df = gpd.read_file(scenario_data.grass_strips)
        df["width"] = -10
        df.to_file(fname)
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            scenario.vct_grass_strips = fname

    @pytest.mark.saga
    def test_vct_grass_strips_attribute_error(self, scenario, tmp_path):
        """Test wrong attributes"""
        fname = Path(tmp_path) / "temp.shp"
        df = gpd.read_file(scenario_data.grass_strips)
        df = df.drop(columns="width")
        df.to_file(fname)
        with pytest.raises(
            PywatemsedemVectorAttributeError, match="input vector should contain"
        ):
            scenario.vct_grass_strips = fname


class TestBuffers:
    """Tests functionalities for buffers
    #TODO: write test for buffer outlet
    """

    @pytest.mark.saga
    def test_vct_buffers(self, scenario, recwarn):
        """Test vector assignment"""
        scenario.choices.dict_ecm_options["Include buffers"] = 0
        scenario.vct_buffers = scenario_data.buffers
        # catch warning
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message) == "Include buffers' in 'dict_ecm_options' is equal to 0. "
            "Will not include buffers."
        )

        # set include buffers on
        scenario.choices.dict_ecm_options["Include buffers"] = 1
        # test output
        un, counts = np.unique(scenario.buffers.arr, return_counts=True)
        np.testing.assert_allclose(un, [0, 1, 2, 16385, 16386])
        np.testing.assert_allclose(counts, [49437, 1, 1, 3, 2])

        # Test if option 'Include buffers' is set off
        scenario.choices.dict_ecm_options["Include buffers"] = 0
        scenario.vct_buffers = scenario_data.buffers
        w = recwarn.pop(UserWarning)  # make sure prev waring is popped
        assert scenario.buffers.is_empty()  # calling buffers raises warning
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message) == "Option 'Include buffers' in erosion control measure"
            " options is 0, returning None"
        )
        scenario.choices.dict_ecm_options["Include buffers"] = 1

    def test_warning_buffers_overlap_rivers(self):
        """#TODO"""
        assert True

    @pytest.mark.saga
    def test_vct_buffers_eff_value_error(self, scenario):
        """Test wrong value in 'eff' attribute"""
        df = gpd.read_file(scenario_data.buffers)
        df["eff"] = -10
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector should contain values in",
        ):
            scenario.vct_buffers = df

    @pytest.mark.saga
    def test_vct_buffers_attribute_error(self, scenario):
        """Test wrong attribute"""
        df = gpd.read_file(scenario_data.buffers)
        df = df.drop(columns="eff")
        with pytest.raises(
            PywatemsedemVectorAttributeError, match="input vector should contain"
        ):
            scenario.vct_buffers = df


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
    def test_outlets(self, scenario):
        """Test vector assignment"""
        scenario.vct_outlets = scenario_data.outlets
        arr, counts = np.unique(scenario.outlets.arr, return_counts=True)
        np.testing.assert_allclose(arr, [-9999, 1, 2])
        np.testing.assert_allclose(counts, [49442, 1, 1])


class TestForceRouting:
    """Tests functionalities for force routing"""

    @pytest.mark.saga
    def test_forcerouting(self, scenario):
        """Test vector assignment"""
        scenario.force_routing = scenario_data.force_routing
        df = scenario.force_routing
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
