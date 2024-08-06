import geopandas as gpd
import pytest
from conftest import geodata
from shapely.geometry import Polygon

from pywatemsedem.defaults import SAGA_FLAGS
from pywatemsedem.geo.utils import any_equal_element_in_vector, execute_subprocess


@pytest.mark.skip(reason="Unvalidated")
class TestExecuteSubprocess:
    """Test execute subprocess"""

    def test_execute_subprocess(self, tmp_path):
        """Test execute subprocess

        Parameters
        ----------
        tmp_path
        """

        # input
        vct_out = tmp_path / "test.shp"

        # test if a 'random' command line runs
        cmd_args = [
            "saga_cmd",
            SAGA_FLAGS,
            "shapes_grid",
            "6",
            "-GRID",
            str(geodata.rst_mask),
        ]
        cmd_args += ["-POLYGONS", str(vct_out), "-CLASS_ALL", "1", "-SPLIT", "0"]
        assert execute_subprocess(cmd_args)

    def test_execute_subprocess_error(self, tmp_path):
        """Test execute subprocess errors

        Parameters
        ----------
        tmp_path
        """
        # input
        vct_out = tmp_path / "test.shp"

        # catch error: in this case, command file because module not found
        cmd_args = [
            "saga_cmd",
            SAGA_FLAGS,
            "shapes_gridzzzz",
            "6",
            "-GRID",
            str(geodata.rst_mask),
        ]
        cmd_args += ["-POLYGONS", str(vct_out), "-CLASS_ALL", "1", "-SPLIT", "0"]
        with pytest.raises(OSError) as excinfo:
            execute_subprocess(cmd_args)
        assert "Error: select a library" in str(excinfo.value)


class TestAnyEqualVector:
    """Test if any element in vector is equal"""

    s1 = gpd.GeoSeries(
        [Polygon([(0, 0), (2, 2), (0, 2)]), Polygon([(0, 0), (1, 2), (0, 2)])]
    )

    s2 = gpd.GeoSeries(
        [Polygon([(0, 0), (2, 2), (0, 2)]), Polygon([(0, 0), (1, 2), (0, 3)])]
    )

    s3 = gpd.GeoSeries(
        [Polygon([(0, 0), (2, 2), (0, 3)]), Polygon([(0, 0), (1, 2), (0, 3)])]
    )

    def test_any_equal_element_in_vector(self):
        """Check if any element in the left series is equal to the right element"""
        assert any_equal_element_in_vector(self.s1, self.s2) is True
        assert any_equal_element_in_vector(self.s1, self.s3) is False
