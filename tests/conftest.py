"""References to all data used for testing"""

# -*- coding: utf-8 -*-

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from dotenv import find_dotenv, load_dotenv

from pywatemsedem.catchment import Catchment
from pywatemsedem.scenario import Scenario
from pywatemsedem.userchoices import UserChoices

# Load environmental variables
## load dotenv
load_dotenv(find_dotenv())

# subfolder data
folder_core = Path("tests/data")
folder_geo = Path("tests/geo/data")
folder_io = Path("tests/io/data")
userchoices_file = folder_core / "userchoices.ini"
ini_file = folder_io / "model_in" / "ini.ini"


# class rainfall_data:
#     """Rainfall data for 'P06_014', first five days january 2018"""
#
#     rainfall = folder_flanders / "rainfall_nukerke.csv"


class io_data:

    composite_landuse = folder_io / "model_in" / "perceelskaart.rst"


class geodata:
    """Data class for geo test data"""

    rst_mask = folder_geo / "mask.tif"
    vct_mak = folder_geo / "mask.shp"
    catchment = folder_geo / "catchm_langegracht.shp"
    rst_example = folder_geo / "example_input_raster.tif"
    vct_example = folder_geo / "example_input_vector.shp"


class catchment_data:
    """Data class for catchment tests data"""

    # vectors
    catchment = geodata.catchment
    infrastructure = folder_core / "infrastructure.shp"
    river = folder_core / "river.shp"
    roads = folder_core / "roads.shp"
    water = folder_core / "water.shp"

    # rasters
    dtm = folder_core / "dtm.tif"
    k = folder_core / "K3.tif"
    basemap = folder_core / "basemap_landuse.tif"
    hsg = folder_core / "hydrological_soil_groups.tif"
    mask = folder_geo / "mask.tif"


class scenario_data:
    """Data class for scenario tests data"""

    # vectors
    grass_strips = folder_core / "grass_strips.shp"
    buffers = folder_core / "buffers.shp"
    cropinfo = folder_core / "cropinfo.csv"
    outlets = folder_core / "outlets.shp"
    endpoints = folder_core / "endpoints.shp"
    parcels = folder_core / "parcels.shp"
    force_routing = folder_core / "force_routing.shp"


# class ecm_data_flanders:
#     """Data class for ecm flanders tests data"""
#
#     folder_ecm_model = folder_flanders / "ecm_model"
#
#     vct_bo_fixed = folder_ecm_model / "BO_VLM_2018_EXTERN_aangepast_la72_demer.shp"
#     vct_bo_var = folder_ecm_model / "BO_VAR_TOEGEP_2018_EXTERN_la72_demer.shp"
#     vct_erosiebestrijdingswerken = (
#         folder_ecm_model / "erosiebestrijdingswerken_demer.shp"
#     )
#     vct_erosiebestrijding_line = (
#         folder_ecm_model / "erosiebestrijdingsplan_line_demer.shp"
#     )
#     vct_erosiebestrijding_point = (
#         folder_ecm_model / "erosiebestrijdingsplan_point_demer.shp"
#     )
#     vct_waterline = folder_ecm_model / "topology_rivers_demer.shp"
#     vct_parcels = folder_ecm_model / "percelen_2018_demer.shp"
#     dict_extra_ecm_data = {}
#     dict_extra_ecm_data["buffer"] = folder_ecm_model / "extra_buffer_demer.shp"
#     dict_extra_ecm_data["gras"] = folder_ecm_model / "extra_gras_demer.shp"
#     txt_output_ecm_model = folder_ecm_model / "results_ecm_model_flanders.csv"


class postprocess:
    """Data class for postprocess tests data"""

    folder_postprocess = folder_core / "postprocess"
    rst_prclskrt = folder_postprocess / "perceelskaart_2018_molenbeek_s1.rst"
    rst_buffers = folder_postprocess / "buffers.rst"
    txt_rainfall = folder_postprocess / "cn_synthetic_rainfall_event.txt"

    ## Outputs
    rst_sediin = folder_postprocess / "SediIn_kg.rst"
    rst_sediout = folder_postprocess / "SediOut_kg.rst"
    rst_watereros = folder_postprocess / "WATEREROS (kg per gridcel).rst"
    txt_routing = folder_postprocess / "routing.txt"
    rst_sediexport = folder_postprocess / "SediExport_kg.rst"
    rst_sewerin = folder_postprocess / "sewer_in.rst"

    ## Postprocess
    ### netto erosion
    txt_average_netto_erosion = folder_postprocess / "average_netto_erosion.txt"
    txt_std_dev_netto_erosion = folder_postprocess / "std_dev_netto_erosion.txt"
    txt_sum_netto_erosion = folder_postprocess / "sum_netto_erosion.txt"
    txt_area_parcel = folder_postprocess / "area_parcel.txt"

    ### grass strips
    txt_gras_efficiency = folder_postprocess / "grass_strips_effiency.csv"

    ## Extra data
    rst_rasterized_prc_shp = folder_postprocess / "percelen.tif"

    ### Grass strips id
    rst_grasstrips_id = folder_postprocess / "grasstrips_id.tif"


class grassstripsdata:
    """Data class for grass strips tests data"""

    folder_grass_strips = folder_core / "grass_strips"
    txt_ktc = folder_grass_strips / "ktc_scaling_gras_strips.csv"
    df_ktc = pd.read_csv(txt_ktc)


class calibratedata:
    """Data class for calibration tests data"""

    ### Calibrate
    folder_calibrate = folder_core / "calibrate"
    txt_calibrate = folder_calibrate / "calibration.csv"


class tools:
    """Data class for tools tests data"""

    folder_tools = folder_core / "tools"
    vct_prcln_mstbnk = folder_tools / "mestbank.shp"
    vct_prcln_dlv = folder_tools / "dlv.shp"
    vct_prcln_fltrd_output = folder_tools / "output.shp"
    # Next two layers are used to test self intersection dlv data layers
    vct_input_dlv_preprocess = folder_tools / "input_dlv_preprocess.shp"
    vct_output_dlv_preprocess = folder_tools / "output_dlv_preprocess.shp"


# class cfactormodelflanders:
#
#     folder_cfactor_model = folder_flanders / "cfactor_model"
#     txt_parcels = folder_cfactor_model / "parcels.csv"


@pytest.fixture
def dummy_catchment(tmp_path):
    """Create a Catchment instance for testing purposes."""
    catchment = Catchment(
        "langegracht",
        catchment_data.catchment,
        catchment_data.dtm,
        20,
        31370,
        -9999,
        tmp_path,
    )
    return catchment


class CatchmentTestBase:
    """Base test class that sets up a temporary directory and initializes Catchment."""

    name = "langegracht"  # Default name, can be overridden

    @classmethod
    def setup_class(cls):
        """Set up a temporary results folder and initialize Catchment."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.results_folder = Path(cls.temp_dir.name)
        cls.setup_catchment()
        cls.setup_scenario()  # Calls the scenario setup method

    @classmethod
    def setup_catchment(cls):
        """Initialize Catchment instance, can be overridden if needed."""
        cls.catchment = Catchment(
            cls.name,
            catchment_data.catchment,
            catchment_data.dtm,
            20,
            31370,
            -9999,
            cls.results_folder,
        )

    @classmethod
    def setup_scenario(cls):
        """Customize the catchment instance with scenario-specific modifications."""
        pass  # To be overridden in subclasses

    @classmethod
    def teardown_class(cls):
        """Clean up the temporary directory after tests."""
        cls.temp_dir.cleanup()


@pytest.fixture
def dummy_scenario(dummy_catchment):
    """Create a Scenario instance for testing purposes."""

    # Add self.scenario-specific modifications
    dummy_catchment.kfactor = catchment_data.k
    dummy_catchment.landuse = catchment_data.basemap
    dummy_catchment.cn = catchment_data.hsg

    # Add user choices
    choices = UserChoices()
    choices.set_ecm_options(userchoices_file)
    choices.set_model_version("WS")
    choices.set_model_options(userchoices_file)
    choices.set_model_variables(userchoices_file)
    choices.set_output(userchoices_file)

    scenario = Scenario(dummy_catchment, 2019, 1, choices)
    return scenario


class ScenarioTestBase(CatchmentTestBase):
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

    @classmethod
    def setup_scenario(cls):
        """Extend Catchment setup with additional self.scenario-specific attributes."""
        # Ensure base catchment is set up
        super().setup_scenario()

        # Add self.scenario-specific modifications
        cls.catchment.kfactor = catchment_data.k
        cls.catchment.landuse = catchment_data.basemap
        cls.catchment.cn = catchment_data.hsg
        cls.catchment.vct_river = catchment_data.river
        cls.catchment.vct_infrastructure_buildings = catchment_data.infrastructure
        cls.catchment.vct_infrastructure_roads = catchment_data.roads
        cls.catchment.vct_water = catchment_data.water

        # Add user choices
        choices = UserChoices()
        choices.set_ecm_options(userchoices_file)
        choices.set_model_version("WS")
        choices.set_model_options(userchoices_file)
        choices.set_model_variables(userchoices_file)
        choices.set_output(userchoices_file)

        cls.scenario = Scenario(cls.catchment, 2019, 1, choices)
