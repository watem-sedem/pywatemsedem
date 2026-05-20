"""Test functions for utils scripts"""

import geopandas as gpd
import pandas as pd
from numpy.testing import assert_almost_equal
from shapely import LineString

from pywatemsedem.tools import (
    format_forced_routing,
    reformat_LineString_to_source_targetf,
)


class TestReformatRouting:
    """Test class for reformat LineString to Source/target dataframe"""

    coor = [(1, 1), (1, 2), (2, 1), (4, 8), (5, 6)]
    ls = LineString(coor)
    res = 1
    minmax = [0, 0, 10, 10]

    def test_trajectory_routing(self):
        """Test trajectory routing, see function for definition"""
        exp = pd.DataFrame(
            data={
                "fromX": [1, 1, 2, 4],
                "fromY": [1, 2, 1, 8],
                "toX": [1, 2, 4, 5],
                "toY": [2, 1, 8, 6],
            }
        )

        out = reformat_LineString_to_source_targetf(self.coor, trajectory_routing=True)

        assert_almost_equal(out["fromX"].values, exp["fromX"].values)
        assert_almost_equal(out["toX"].values, exp["toX"].values)
        assert_almost_equal(out["fromY"].values, exp["fromY"].values)
        assert_almost_equal(out["toY"].values, exp["toY"].values)

    def test_jump_routing(self):
        """Test jump routing, see function for definition"""
        exp = pd.DataFrame(data={"fromX": [1], "fromY": [1], "toX": [5], "toY": [6]})

        out = reformat_LineString_to_source_targetf(self.coor, trajectory_routing=False)

        assert_almost_equal(out["fromX"].values, exp["fromX"].values)
        assert_almost_equal(out["toX"].values, exp["toX"].values)
        assert_almost_equal(out["fromY"].values, exp["fromY"].values)
        assert_almost_equal(out["toY"].values, exp["toY"].values)

    def format_forced_routing(self):
        """Test reformat forced routing

        Test it with standard jump trajectory and assert output column and row
        """
        out = format_forced_routing(
            gpd.GeoDataFrame([1], geometry=[self.ls]),
            resolution=self.res,
            minmax=self.minmax,
        )

        assert_almost_equal(out["fromcol"].values, 2)
        assert_almost_equal(out["fromrow"].values, 10)
        assert_almost_equal(out["tocol"].values, 6)
        assert_almost_equal(out["torow"].values, 5)
