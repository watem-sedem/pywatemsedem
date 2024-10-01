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
        None,
        str,
        False,
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
        None,
        float,
        False,
    )
    with pytest.raises(TypeError) as excinfo:
        user_choice.value = "This value should be a float"
    assert ("Value assigned to key 'Test2' should be dtype '<class 'float'>'.") in str(
        excinfo.value
    )


def test_initiation_ws_options():
    """Test if the WSOptions model is initialised ok"""
    ws_opt = WSOptions()

    assert ws_opt.l_model.value == "Desmet1996_Vanoost2003"
    assert ws_opt.l_model.key == "L model"
    assert (
        ws_opt.l_model.allowed_values
        == "['Desmet1996_Vanoost2003', 'Desmet1996_McCool']"
    )

    assert ws_opt.s_model.value == "Nearing1997"
    assert ws_opt.s_model.key == "S model"
    assert ws_opt.s_model.allowed_values == "['Nearing1997', 'McCool1987']"

    assert not ws_opt.only_routing.value
    assert ws_opt.only_routing.key == "only routing"

    assert ws_opt.tc_model.value == "VanOost2000"
    assert ws_opt.tc_model.key == "TC model"
    assert ws_opt.tc_model.allowed_values == "['VanOost2000', 'Verstraeten2007']"

    assert not ws_opt.calculate_tillage_erosion
    assert ws_opt.calculate_tillage_erosion.key == "calculate tillage erosion"


@pytest.skip
def test_initialisation_ws_parameters():
    """Test if the WSParamaeters object is initialised ok"""
    WSParameters()


@pytest.skip
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


@pytest.skip
def test_initialisation_ws_output():
    """Test if the WSOutput object is initialised ok"""
    WSOutput()


def test_mandatory_value_not_given():
    """Test when no mandatory value is given, a ValueError is raised"""
    ws_params = WSParameters()

    with pytest.raises(ValueError) as excinfo:
        ws_params.check_mandatory_values()
    assert ("R factor is mandatory and cannot be None") in str(excinfo.value)
