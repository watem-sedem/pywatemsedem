def valid_routing_vector(self):
    """Check whether a routing vector has been created."""
    if self.vct_routing is None:
        msg = "No routing vector created, please first run 'make_routing_vct'."
        raise IOError(msg)


def valid_routing_sedi_out_vector(self):
    """Check whether a routing vector with sedi_out has been created."""
    if self.vct_routing is None:
        msg = (
            "No routing vector (with sedi_out) created, please first run "
            "'couple_sediout_routing.'"
        )
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
