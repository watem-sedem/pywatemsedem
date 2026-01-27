from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from conftest import catchment_data

from pywatemsedem.errors import (
    PywatemsedemRasterValueError,
    PywatemsedemVectorAttributeValueError,
)
from pywatemsedem.geo.utils import load_raster, write_arr_as_rst


class TestCatchment:
    """Test Catchment properties

    Test main functionalities for Catchment class.

    Notes
    -----
    All tests in this suite do implicit testing:
    - Does the setting of a property run?
    - Are the unique values and counts equal?
    - Are data types equal?
    """

    # @pytest.mark.skip(reason="test to fix")
    def test_kfactor(self, dummy_catchment):
        """Test assignment kfactor raster"""
        # test assignment raster
        dummy_catchment.kfactor = catchment_data.k

        # test type
        assert dummy_catchment.kfactor.arr.dtype == np.int32

        # test unique values
        un, counts = np.unique(dummy_catchment.kfactor.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9999, 20, 27, 40, 42])
        np.testing.assert_allclose(counts, [28234, 1376, 72, 818, 18944])

    def test_kfactor_warning(self, recwarn, tmp_path, dummy_catchment):
        """Test warning wrong value kfactor raster"""
        tmp_path.mkdir(exist_ok=True)
        fname = Path(tmp_path) / "temp.rst"
        arr, profile = load_raster(catchment_data.k)
        arr[arr < 40] = -10
        write_arr_as_rst(arr, fname, arr.dtype, profile)
        dummy_catchment.kfactor = fname
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message) == "Negative values detected in K-factor raster, "
            "setting negative values to 0."
        )

    def test_landuse(self, dummy_catchment):
        """Test assignment landuse raster"""
        dummy_catchment.landuse = catchment_data.basemap

        # test type
        assert dummy_catchment.landuse.arr.dtype == np.int16

        # test unique values
        un, counts = np.unique(dummy_catchment.landuse.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9999, -5, -4, -3, -2, 10])
        np.testing.assert_allclose(counts, [28239, 5, 5717, 2003, 1140, 12340])

    def test_landuse_wrong_value(self, tmp_path, dummy_catchment):
        """Test wrong value in landuse raster"""
        fname = Path(tmp_path) / "temp.rst"
        arr, profile = load_raster(catchment_data.basemap)
        arr[arr == 10] = -7
        write_arr_as_rst(arr, fname, arr.dtype, profile)
        with pytest.raises(
            PywatemsedemRasterValueError, match="can only contain values"
        ):
            dummy_catchment.landuse = fname

    @pytest.mark.saga
    def test_river(self, dummy_catchment):
        """Test assignment river raster and derivative segments and routing rasters"""
        # test assign vector
        dummy_catchment.vct_river = catchment_data.river

        # test raster river type and unique values
        un, counts = np.unique(dummy_catchment.river.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([-9999, -1]))
        np.testing.assert_allclose(counts, np.array([48910, 534]))

        # test raster routing type and unique values
        un, counts = np.unique(dummy_catchment.routing.arr, return_counts=True)
        np.testing.assert_allclose(un, np.array([0, 1, 3, 5, 7]))
        np.testing.assert_allclose(counts, np.array([48911, 84, 257, 152, 40]))

        # test segments
        un, counts = np.unique(dummy_catchment.segments.arr, return_counts=True)
        np.testing.assert_allclose(
            un,
            np.array([0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]),
        )
        np.testing.assert_allclose(
            counts,
            np.array(
                [48910, 11, 5, 4, 46, 60, 3, 14, 27, 5, 41, 43, 28, 87, 43, 52, 23, 42]
            ),
        )

    def test_tubed_river(self, dummy_catchment):
        """Test tubed river and error"""
        gdf = gpd.read_file(catchment_data.river)

        tubed = gdf.iloc[0:2]
        non_tubed = gdf.iloc[2:]

        # check if functionality runs
        dummy_catchment.vct_river = non_tubed
        dummy_catchment.tubed_river = tubed

        # check for overlap
        dummy_catchment.vct_river = gdf
        with pytest.raises(IOError, match="are also present"):
            dummy_catchment.tubed_river = tubed

    def test_infrastructure(self, dummy_catchment):
        """Test assignment infrastructure vector"""
        # test assign vector
        dummy_catchment.vct_infrastructure_buildings = catchment_data.infrastructure
        dummy_catchment.vct_infrastructure_roads = catchment_data.roads

        # test type
        assert dummy_catchment.infrastructure_roads.arr.dtype == np.int16

        # test infrastructure type and unique values
        un, counts = np.unique(
            dummy_catchment.infrastructure_roads.arr, return_counts=True
        )
        np.testing.assert_allclose(un, [-9999, -7.0, -2])
        np.testing.assert_allclose(counts, [46746, 1408, 1290])

        # test type
        assert dummy_catchment.infrastructure_buildings.arr.dtype == np.int16

        un, counts = np.unique(
            dummy_catchment.infrastructure_buildings.arr, return_counts=True
        )
        np.testing.assert_allclose(un, [-9999, -2])
        np.testing.assert_allclose(counts, [46834, 2610])

        # test type
        assert dummy_catchment.infrastructure.arr.dtype == np.int16

        un, counts = np.unique(dummy_catchment.infrastructure.arr, return_counts=True)
        np.testing.assert_allclose(un, [-9999, -7, -2])
        np.testing.assert_allclose(counts, [45353, 1408, 2683])

    def test_infrastructure_wrong_value(self, dummy_catchment):
        "Test wrong value in 'paved' attribute infr roads"
        df = gpd.read_file(catchment_data.roads)
        df["paved"] = -3
        with pytest.raises(
            PywatemsedemVectorAttributeValueError,
            match="vector can only contain values",
        ):
            dummy_catchment.vct_infrastructure_roads = df
