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
        with pytest.raises(PywatemsedemInputError) as excinfo:
            f.vector_factory(geodata.rst_mask, "Polygon")
        assert (
            f"First create a mask with {Factory.create_mask.__name__}-function"
            in str(excinfo.value)
        )

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
        with pytest.raises(IOError) as excinfo:
            f.vector_factory(geodata.rst_mask, "Polygon")
        assert (
            f"Input vector file '{geodata.rst_mask}' should be a valid "
            f"vector file (e.g. ESRI shape file)." in str(excinfo.value)
        )

        # feed numpy array to vector factory
        with pytest.raises(IOError) as excinfo:
            f.vector_factory(array([]), "Polygon")
        assert "Input vector should be a geopandas GeoDataFrame or vector file." in str(
            excinfo.value
        )

        # feed vector file to raster factory
        with pytest.raises(IOError) as excinfo:
            f.raster_factory(geodata.catchment)
        assert (
            f"Input raster file '{geodata.catchment}' should be a valid raster file "
            f"(e.g. IDRISI raster, geotiff, SAGA-GRID, ..)" in str(excinfo.value)
        )

        # feed geopandas dataframe to raster factory
        with pytest.raises(IOError) as excinfo:
            f.raster_factory(GeoDataFrame())
        assert "Input raster should be a numpy array or raster file," in str(
            excinfo.value
        )
