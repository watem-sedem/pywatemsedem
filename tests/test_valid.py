import pytest

from pywatemsedem.valid import valid_req_property


class ExampleClass:
    """Example class for testing decorator pywatemsedem.valid.valid_req_property"""

    _req_property = None

    @property
    def non_mandatory(self):
        """Define a property based on a non-mandatory required property"""
        valid_req_property(
            self,
            current_property="Non mandatory property",
            req_property_name="req_property",
            mandatory=False,
        )
        return self._req_property + 5

    @property
    def mandatory(self):
        """Define a property based on a mandatory required property"""
        valid_req_property(
            self,
            current_property="mandatory property",
            req_property_name="req_property",
            mandatory=True,
        )
        return self._req_property + 5

    @property
    def req_property(self):
        """Getter req propery"""
        return self._req_property

    @req_property.setter
    def req_property(self, value):
        """Setter req propery with float value"""
        self._req_property = value


class TestValidSourceProperty:
    """This test class is used to check functioning of the required property decorator
    pywatemsedem.valid.valid_req_property

    The required property decorator checks whether a required property is properly
    defined. A distinction is made between mandatory or non-mandatory properties:

    - *mandatory*: The class needs the required property X to be defined (not equal to
      None) when calling property Y, otherwise it raises an Error.
    - *non_mandatory*: The class needs the required property X to be defined (not equal
      to None) when calling property Y, otherwise it returns a None.
    """

    def test_non_mandatory(self):
        """Test for non mandatory required property"""
        source = ExampleClass()
        source.req_property = 8

        assert source.non_mandatory == 13

    def test_mandatory(self):
        """Test for mandatory required property"""
        source = ExampleClass()
        err_msg = "Please first set mandatory property"
        with pytest.raises(IOError, match=err_msg):
            print(source.mandatory)

        source.req_property = 3
        assert source.non_mandatory == 8
