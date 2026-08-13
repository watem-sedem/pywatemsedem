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
