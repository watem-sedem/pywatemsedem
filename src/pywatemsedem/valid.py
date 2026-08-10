from pywatemsedem.io.modeloutput import (
    create_deposition_raster,
    create_erosion_raster,
)


def valid_ditches_sewers(
    func,
):
    """Decorator to check if DTM raster is defined."""

    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.files["rst_ditches_in"] is None:
            self.write_sedimentload_sewers_and_ditches()
        return func(self, *args, **kwargs)

    return wrapper


def valid_erosion_deposition(func):
    """Decorator to check if DTM raster is defined."""

    def wrapper(self, *args, **kwargs):
        """wrapper"""
        if self.files["rst_erosion"] is None:
            self.files["rst_erosion"] = create_erosion_raster(
                self.files["rst_watereros"]
            )
            self.files["rst_deposition"] = create_deposition_raster(
                self.files["rst_watereros"]
            )
        func(self, *args, **kwargs)

    return wrapper


def valid_routing_vector(self):
    """Check if routing vector is defined"""
    if self.vct_routing is None:
        msg = "No routing vector created, please first run 'make_routing_vct'."
        raise IOError(msg)


def valid_routing_sedi_out_vector(self):
    """Check if routing vector is defined"""
    if self.vct_routing is None:
        msg = (
            "No routing vector (with sedi_out) created, please first run "
            "'couple_sediout_routing."
        )
        raise IOError(msg)


def valid_endpoints(self):
    """Check if endpoints are in available"""
    if self.files["rst_endpoints"] is None:
        msg = "No endpoints in subcatchments."
        raise IOError(msg)


def valid_rivers(self):
    """Check if rivers are available"""
    if self.files["rst_riverrouting"] is None:
        msg = "No rivers in subcatchments."
        raise IOError(msg)


def valid_req_property(
    self, current_property=None, req_property_name=None, mandatory=False
):
    """Check for required property

    Parameters
    ----------
    self: Class.instance
    current_property: string
        Name of current property
    req_property_name: string
        Required set property, should be initialised to self
    mandatory: bool, default False
        Indicate whether property is mandatory
    """
    valid = getattr(self, req_property_name)
    if valid is None:
        if mandatory:
            msg = (
                f"Please first set mandatory property '{req_property_name}' before "
                f"setting '{current_property}'."
            )
            raise IOError(msg)
