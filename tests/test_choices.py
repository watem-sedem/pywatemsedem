"""Test functions for utils scripts"""
import pytest

from pywatemsedem.choices import (
    UserChoice,
    WSExtensions,
    WSExtensionsParameters,
    WSOptions,
    WSOutput,
    WSParameters,
)


def test_userchoice_not_allowed_value():
    """Test if a ValueError is raised when a not allowed value is entered"""
    user_choice = UserChoice(
        "Test1",
        "Tests",
        str,
        True,
        None,
        ["This string is allowed", "A second allowed string"],
    )
    with pytest.raises(ValueError) as excinfo:
        user_choice.value = "Not allowed string"
    assert (
        "Value should be one of: ['This string is allowed', 'A second allowed string']."
    ) in str(excinfo.value)


def test_userchoice_wrong_dtype():
    """Test if a ValueError is raised when a value with a wrong dtype is entered"""
    user_choice = UserChoice(
        "Test2",
        "Tests",
        float,
        True,
    )
    with pytest.raises(TypeError) as excinfo:
        user_choice.value = "This value should be a float"
    assert ("Value assigned to key 'Test2' should be dtype '<class 'float'>'.") in str(
        excinfo.value
    )


def test_initiation_ws_options():
    """Test if the WSOptions model is initialised ok"""
    ws_opt = WSOptions()

    assert ws_opt.l_model.default_value == "Desmet1996_Vanoost2003"
    assert ws_opt.l_model.key == "L model"
    assert ws_opt.l_model.dtype == str
    assert ws_opt.l_model.allowed_values == [
        "Desmet1996_Vanoost2003",
        "Desmet1996_McCool",
    ]

    assert ws_opt.s_model.default_value == "Nearing1997"
    assert ws_opt.s_model.key == "S model"
    assert ws_opt.s_model.dtype == str
    assert ws_opt.s_model.allowed_values == ["Nearing1997", "McCool1987"]

    assert not ws_opt.only_routing.default_value
    assert ws_opt.only_routing.dtype == bool
    assert ws_opt.only_routing.key == "only routing"

    assert ws_opt.tc_model.default_value == "VanOost2000"
    assert ws_opt.tc_model.key == "TC model"
    assert ws_opt.tc_model.dtype == str
    assert ws_opt.tc_model.allowed_values == ["VanOost2000", "Verstraeten2007"]

    assert not ws_opt.calculate_tillage_erosion.default_value
    assert ws_opt.calculate_tillage_erosion.key == "calculate tillage erosion"
    assert ws_opt.calculate_tillage_erosion.dtype == bool


@pytest.mark.skip(reason="not yet implemented")
def test_initialisation_ws_parameters():
    """Test if the WSParamaeters object is initialised ok"""
    WSParameters()


@pytest.mark.skip(reason="not yet implemented")
def test_initialisation_ws_extensions():
    """Test if the WSExtensions object is initialised ok"""
    WSExtensions()


def test_initialisation_ws_extension_parameters_cn():
    """Test if the cn parameters are set to mandatory when cn is enabled as an extension"""
    ws_ext = WSExtensions()
    ws_ext.curve_number = True
    ws_ext_param = WSExtensionsParameters(ws_ext)

    assert ws_ext_param.alpha.mandatory
    assert ws_ext_param.beta.mandatory
    assert ws_ext_param.stream_velocity.mandatory
    assert ws_ext_param.antecedent_rainfall.mandatory
    assert ws_ext_param.desired_timestep.mandatory
    assert ws_ext_param.endtime_model.mandatory


def test_initialisation_ws_extension_parameters_create_ktc_map():
    """Test if the ktc parameters are set to mandatory when create_ktc_map is enabled as an extension"""
    ws_ext = WSExtensions()
    ws_ext.create_ktc_map = True
    ws_ext_param = WSExtensionsParameters(ws_ext)
    assert ws_ext_param.ktc_low.mandatory
    assert ws_ext_param.ktc_high.mandatory
    assert ws_ext_param.ktc_limit.mandatory


def test_initialisation_ws_extension_parameters_create_ktil_map():
    """Test if the ktil parameters are set to mandatory when create_ktil_map is enabled as an extension"""
    ws_ext = WSExtensions()
    ws_ext.create_ktil_map = True
    ws_ext_param = WSExtensionsParameters(ws_ext)
    assert ws_ext_param.ktil_default.mandatory
    assert ws_ext_param.ktil_threshold.mandatory


def test_initialisation_ws_extension_parameters_include_sewers():
    """Test if the sewer_exit parameters is set to mandatory when iclude_sewer is enabled as an extension"""
    ws_ext = WSExtensions()
    ws_ext.include_sewers = True
    ws_ext_param = WSExtensionsParameters(ws_ext)
    assert ws_ext_param.sewer_exit.mandatory


def test_initialisation_ws_extension_parameters_estimate_clay_content():
    """Test if the clay_content_parent_material parameter is set to mandatory
    when estimate_clay_content is enabled as an extension"""
    ws_ext = WSExtensions()
    ws_ext.estimate_clay_content = True
    ws_ext_param = WSExtensionsParameters(ws_ext)
    assert ws_ext_param.clay_content_parent_material.mandatory


@pytest.mark.skip(reason="not yet implemented")
def test_initialisation_ws_output():
    """Test if the WSOutput object is initialised ok"""
    ws_out = WSOutput()

    assert ws_out.write_aspect.key == "write aspect"
    assert ws_out.write_aspect.dtype == bool
    assert not ws_out.write_aspect.mandatory

    assert ws_out.write_rusle.key == "write rusle"
    assert ws_out.write_rusle.dtype == bool
    assert not ws_out.write_rusle.mandatory

    assert ws_out.write_rusle.key == "write rusle"
    assert ws_out.write_rusle.dtype == bool
    assert not ws_out.write_rusle.mandatory

    assert ws_out.write_ls_factor.key == "write ls factor"
    assert ws_out.write_ls_factor.dtype == bool
    assert not ws_out.write_ls_factor.mandatory

    assert ws_out.write_upstream_area.key == "write upstream area"
    assert ws_out.write_upstream_area.dtype == bool
    assert not ws_out.write_upstream_area.mandatory

    assert ws_out.write_slope.key == "write slope"
    assert ws_out.write_slope.dtype == bool
    assert not ws_out.write_slope.mandatory

    assert ws_out.write_routing_table.key == "write routing table"
    assert ws_out.write_routing_table.dtype == bool
    assert not ws_out.write_routing_table.mandatory

    assert ws_out.write_routing_column_row.key == "write routing column/row"
    assert ws_out.write_routing_column_row.dtype == bool
    assert not ws_out.write_routing_column_row.mandatory

    assert ws_out.write_sediment_export.key == "write sediment export"
    assert ws_out.write_sediment_export.dtype == bool
    assert not ws_out.write_sediment_export.mandatory

    assert ws_out.write_water_erosion.key == "write water erosion"
    assert ws_out.write_water_erosion.dtype == bool
    assert not ws_out.write_water_erosion.mandatory

    assert ws_out.write_rainfall_excess.key == "write rainfall excess"
    assert ws_out.write_rainfall_excess.dtype == bool
    assert not ws_out.write_rainfall_excess.mandatory

    assert ws_out.write_total_runoff.key == "write total runoff"
    assert ws_out.write_total_runoff.dtype == bool
    assert not ws_out.write_total_runoff.mandatory

    assert ws_out.export_saga.key == "Export .sgrd grids"
    assert ws_out.export_saga.dtype == bool
    assert not ws_out.export_saga.mandatory


def test_mandatory_value_not_given():
    """Test when no mandatory value is given, a ValueError is raised"""
    ws_params = WSParameters()

    with pytest.raises(ValueError) as excinfo:
        ws_params.check_mandatory_values()
    assert ("R factor is mandatory and cannot be None") in str(excinfo.value)


def test_apply_defaults():
    """Test if the mixin function apply defaults works as assumed"""
    ws_opt = WSOptions()
    ws_opt.apply_defaults()

    assert ws_opt.l_model.value == ws_opt.l_model.default_value
    assert ws_opt.s_model.value == ws_opt.s_model.default_value
    assert ws_opt.tc_model.value == ws_opt.tc_model.default_value
    assert ws_opt.only_routing.value == ws_opt.only_routing.default_value
    assert (
        ws_opt.calculate_tillage_erosion.value
        == ws_opt.calculate_tillage_erosion.default_value
    )
