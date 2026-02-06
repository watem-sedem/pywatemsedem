import pytest
from conftest import geodata
from geopandas import GeoDataFrame
from numpy import array

from pywatemsedem.geo.factory import Factory
from pywatemsedem.geo.valid import PywatemsedemInputError


class TestFactory:
    """Test class for factory

    Parameters
    ----------
    nodata: -9999
    epsg_code: 31370 (Lambert)
    resolution: 20 (m)

    """

    nodata = -9999
    epsg_code = 31370
    resolution = 20

    @pytest.mark.saga
    def test_raster_mask(self, tmp_path):
        """Test factory with raster

        ----------
        tmp_path
        """
        f = Factory(self.resolution, self.epsg_code, self.nodata, tmp_path)
        assert f.create_mask(geodata.rst_mask)

    def test_vector_mask(self, tmp_path):
        """Test factory with vector

        ----------
        tmp_path
        """
        f = Factory(self.resolution, self.epsg_code, self.nodata, tmp_path)
        assert f.create_mask(geodata.catchment)

    @pytest.mark.saga
    def test_error_no_mask(self, tmp_path):
        """Test error when no mask is created

        Parameters
        ----------
        tmp_path
        """
        f = Factory(self.resolution, self.epsg_code, self.nodata, tmp_path)

        # feed raster to vector factory
        with pytest.raises(
            PywatemsedemInputError,
            match=(
                rf"First create a mask with " f"{Factory.create_mask.__name__}-function"
            ),
        ):
            f.vector_factory(geodata.rst_mask, "Polygon")

    @pytest.mark.saga
    def test_error_input_to_factory(self, tmp_path):
        """Test error in input to factory

        Parameters
        ----------
        tmp_path
        """
        f = Factory(self.resolution, self.epsg_code, self.nodata, tmp_path)
        f.create_mask(geodata.rst_mask)

        # feed raster to vector factory
        with pytest.raises(
            IOError,
            match=(
                rf"Input vector file '{geodata.rst_mask}' should be "
                rf"a valid vector file (e.g. ESRI shape file)."
            ),
        ):
            f.vector_factory(geodata.rst_mask, "Polygon")

        # feed numpy array to vector factory
        with pytest.raises(
            IOError,
            match=(r"Input '\[\]' should be a geopandas GeoDataFrame or vector file."),
        ):
            f.vector_factory(array([]), "Polygon")

        # feed vector file to raster factory
        with pytest.raises(
            IOError,
            match=(
                rf"Input raster file '{geodata.catchment}' should be "
                rf"a valid raster file (e.g. IDRISI raster, geotiff, SAGA-GRID, ..)"
            ),
        ):
            f.raster_factory(geodata.catchment)

        # feed geopandas dataframe to raster factory
        with pytest.raises(
            IOError,
            match=(
                r"Input 'Empty GeoDataFrame\nColumns: \[\]\nIndex: \[\]' "
                r"should be a numpy array or raster file,"
            ),
        ):
            f.raster_factory(GeoDataFrame())
