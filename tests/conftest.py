"""References to all data used for testing"""
# -*- coding: utf-8 -*-

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


@pytest.fixture(scope="session")
def scenario():
    """Initialize catchment

    Save it to cache with request.config.cache once it is made (faster rerun)
    """
    name = "langegracht"
    catchment = Catchment(
        name, catchment_data.catchment, catchment_data.dtm, 20, 31370, -9999
    )
    catchment.kfactor = catchment_data.k
    catchment.landuse = catchment_data.basemap
    catchment.cn = catchment_data.hsg
    catchment.vct_river = catchment_data.river
    catchment.vct_infrastructure_buildings = catchment_data.infrastructure
    catchment.vct_infrastructure_roads = catchment_data.roads
    catchment.vct_water = catchment_data.water

    """Initialize user choices"""
    choices = UserChoices()
    choices.set_ecm_options(userchoices_file)
    choices.set_model_version("WS")
    choices.set_model_options(userchoices_file)
    choices.set_model_variables(userchoices_file)
    choices.set_output(userchoices_file)

    val = Scenario(catchment, 2019, 1, choices)

    return val


# class non_specific_landuse_measures:
#     """Standard scenario parameters and output data for the flanders pipeline.
#
#     We encourage developers to have a look at the standard_scenarios_flanders-module
#     for an explanation of the parameters.
#
#     Used for testing benchmarks for Flanders. The output numbers in this function are
#     hardcoded and checked/adjusted manually.
#
#     This scenario covers the output data for the standard use case for Flanders:
#
#     - No specific landuse: C-factor for agricultural fields is set to 0.37, see
#       :func:`pywatemsedem.flanders.standard_scenarios.apply_specific_landuse`.
#
#     - Following symptom-oriented measures are implemented:
#
#         - 'beheerovereenkomsten'
#         - 'erosiebestrijdingswerken'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Buffers and grass strips are used, source oriented measures not.
#     """
#
#     # input choices
#     specific_landuse = False
#     c_factor_model = None
#     symptom_oriented_packages = ["beheerovereenkomsten", "erosiebestrijdingswerken"]
#     source_oriented_packages = None
#     buffers = True
#     grass_strips = True
#     source_oriented = False
#
#     # output: ton
#     erosion = -17.13
#     deposition = 14.44
#     to_river = 0.92
#     outside_domain = 0.19
#     buffers = 0.10
#     to_ditches = 0.70
#     to_sewers = 0.44
#
#
# class non_specific_landuse_no_measures:
#     """Standard scenario parameters and output data for the flanders pipeline.
#
#     We encourage developers to have a look at the standard_scenarios_flanders-module
#     for an explanation of the parameters.
#
#     Used for testing benchmarks for Flanders. The output numbers in this function are
#     hardcoded and checked/adjusted manually.
#
#     This scenario covers the output data for the standard use case for Flanders:
#
#     - No specific landuse: C-factor for agricultural fields is set to 0.37, see
#       :func:`pywatemsedem.flanders.standard_scenarios.apply_specific_landuse`.
#
#     - No symptom-oriented measures are implemented:
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - No buffers, grass strips, source oriented measures are used.
#     """
#
#     # input choices
#     specific_landuse = False
#     c_factor_model = None
#     symptom_oriented_packages = None
#     source_oriented_packages = None
#     buffers = False
#     grass_strips = False
#     source_oriented = False
#
#     # output ws Molenbeek: ton
#     erosion = -20.12
#     deposition = 15.94
#     to_river = 1.41
#     outside_domain = 0.21
#     buffers = 0.00
#     to_ditches = 1.18
#     to_sewers = 0.78
#
#     # output cnws Nukerke: m3/s ...
#     runoff_count = 3.820000e02
#     runoff_mean = 4.084430e-02
#     runoff_std = 1.101224e-01
#     runoff_min = 2.101948e-47
#     runoff_max = 8.621105e-01
#     runoff_50 = 6.997757e-04
#
#     # ... and g/L
#     concentration_count = 382.000000
#     concentration_mean = 1.546574
#     concentration_std = 1.284577
#     concentration_min = 0.355476
#     concentration_max = 3.121928
#     concentration_50 = 0.565378
#
#
# class specific_landuse_indicator_current_measures:
#     """Standard scenario parameters and output data for the flanders pipeline.
#
#     We encourage developers to have a look at the standard_scenarios_flanders-module
#     for an explanation of the parameters.
#
#     Used for testing benchmarks for Flanders. The output numbers in this function are
#     hardcoded and checked/adjusted manually.
#
#     This scenario covers the output data for the standard use case for Flanders:
#
#     - indicator: C-factors defined in the indicator are used, see
#       :func:`pywatemsedem.flanders.standard_scenarios.apply_specific_landuse`.
#
#     - Following symptom-oriented measures are implemented:
#
#         - 'beheerovereenkomsten'
#         - 'erosiebestrijdingswerken'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Following source-oriented measures are implemented:
#
#         - 'beheerovereenkomsten'
#         - 'randvoorwaarden'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Buffers, grass strips and source-oriented measures are used.
#     """
#
#     # input choices
#     specific_landuse = True
#     c_factor_model = "indicator"
#     symptom_oriented_packages = ["beheerovereenkomsten", "erosiebestrijdingswerken"]
#     source_oriented_packages = ["beheerovereenkomsten", "randvoorwaarden"]
#     buffers = True
#     grass_strips = True
#     source_oriented = True
#
#     # output: ton
#     erosion = -16.40
#     deposition = 13.95
#     to_river = 0.87
#     outside_domain = 0.18
#     buffers = 0.10
#     to_ditches = 0.66
#     to_sewers = 0.36
#
#
# class specific_landuse_indicator_erosiebestrijdingswerken_randvoorwaarden:
#     """Standard scenario parameters and output data for the flanders pipeline.
#
#     We encourage developers to have a look at the standard_scenarios_flanders-module
#     for an explanation of the parameters.
#
#     Used for testing benchmarks for Flanders. The output numbers in this function are
#     hardcoded and checked/adjusted manually.
#
#     This scenario covers the output data for the standard use case for Flanders:
#
#     - indicator: C-factors defined in the indicator are used, see
#       :func:`pywatemsedem.flanders.standard_scenarios.apply_specific_landuse`.
#
#     - Following symptom-oriented measures are implemented:
#
#         - 'erosiebestrijdingswerken'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Following source-oriented measures are implemented:
#
#         - 'randvoorwaarden'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Buffers, grass strips and source-oriented measures are used.
#     """
#
#     # input choices
#     specific_landuse = True
#     c_factor_model = "indicator"
#     symptom_oriented_packages = ["erosiebestrijdingswerken"]
#     source_oriented_packages = ["randvoorwaarden"]
#     buffers = True
#     grass_strips = True
#     source_oriented = True
#
#     # output: ton
#     erosion = -18.67
#     deposition = 14.81
#     to_river = 1.34
#     outside_domain = 0.21
#     buffers = 0.18
#     to_ditches = 1.03
#     to_sewers = 0.59
#
#
# class specific_landuse_indicator_beheerovereenkomsten_randvoorwaarden:
#     """Standard scenario parameters and output data for the flanders pipeline.
#
#     We encourage developers to have a look at the standard_scenarios_flanders-module
#     for an explanation of the parameters.
#
#     Used for testing benchmarks for Flanders. The output numbers in this function are
#     hardcoded and checked/adjusted manually.
#
#     This scenario covers the output data for the standard use case for Flanders:
#
#     - indicator: C-factors defined in the indicator are used, see
#       :func:`pywatemsedem.flanders.standard_scenarios.apply_specific_landuse`.
#
#     - Following symptom-oriented measures are implemented:
#
#         - 'beheerovereenkomsten'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Following source-oriented measures are implemented:
#
#         - 'beheerovereenkomsten'
#         - 'randvoorwaarden'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Buffers, grass strips and source-oriented measures are used.
#     """
#
#     # input choices
#     specific_landuse = True
#     c_factor_model = "indicator"
#     symptom_oriented_packages = ["beheerovereenkomsten"]
#     source_oriented_packages = ["beheerovereenkomsten", "randvoorwaarden"]
#     buffers = True
#     grass_strips = True
#     source_oriented = True
#
#     # output: ton
#     erosion = -17.47
#     deposition = 15.01
#     to_river = 0.91
#     outside_domain = 0.18
#     buffers = 0.00
#     to_ditches = 0.70
#     to_sewers = 0.38
#
#
# class specific_landuse_indicator_beheerovereenkomsten_erosiebestrijdingswerken:
#     """Standard scenario parameters and output data for the flanders pipeline.
#
#     We encourage developers to have a look at the standard_scenarios_flanders-module
#     for an explanation of the parameters.
#
#     Used for testing benchmarks for Flanders. The output numbers in this function are
#     hardcoded and checked/adjusted manually.
#
#     This scenario covers the output data for the standard use case for Flanders:
#
#     - indicator: C-factors defined in the indicator are used, see
#       :func:`pywatemsedem.flanders.standard_scenarios.apply_specific_landuse`.
#
#     - Following symptom-oriented measures are implemented:
#
#         - 'beheerovereenkomsten'
#         - 'erosiebestrijdingswerken'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Following source-oriented measures are implemented:
#
#         - 'beheerovereenkomsten'
#
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Buffers, grass strips and source-oriented measures are used.
#     """
#
#     # input choices
#     specific_landuse = True
#     c_factor_model = "indicator"
#     symptom_oriented_packages = ["beheerovereenkomsten", "erosiebestrijdingswerken"]
#     source_oriented_packages = ["beheerovereenkomsten"]
#     buffers = True
#     grass_strips = True
#     source_oriented = True
#
#     # output: ton
#     erosion = -16.69
#     deposition = 14.12
#     to_river = 0.90
#     outside_domain = 0.19
#     buffers = 0.10
#     to_ditches = 0.68
#     to_sewers = 0.41
#
#
# class specific_landuse_indicator_no_measures:
#     """Standard scenario parameters and output data for the flanders pipeline.
#
#     We encourage developers to have a look at the standard_scenarios_flanders-module
#     for an explanation of the parameters.
#
#     Used for testing benchmarks for Flanders. The output numbers in this function are
#     hardcoded and checked/adjusted manually.
#
#     This scenario covers the output data for the standard use case for Flanders:
#
#     - indicator: C-factors defined in the indicator are used, see
#       :func:`pywatemsedem.flanders.standard_scenarios.apply_specific_landuse`.
#
#     - No symptom-oriented measures.
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - No source-oriented measures are implemented:
#       See
#       :func:`pywatemsedem.flanders.standard_scenarios_flanders.apply_erosion_control_measures`
#
#     - Buffers, grass strips and source-oriented measures are not used.
#     """
#
#     # input choices
#     specific_landuse = True
#     c_factor_model = "indicator"
#     symptom_oriented_packages = None
#     source_oriented_packages = None
#     buffers = False
#     grass_strips = False
#     source_oriented = False
#
#     # output: ton
#     erosion = -19.85
#     deposition = 15.86
#     to_river = 1.41
#     outside_domain = 0.21
#     buffers = 0.00
#     to_ditches = 1.09
#     to_sewers = 0.73
