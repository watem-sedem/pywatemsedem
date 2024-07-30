class InputFileName:
    """Holds template inputfile names for WaTEM/SEDEM input

    Parameters
    ----------
    format: str | pathlib.Path
        Database format.
    """

    def __init__(self, format="filebased"):

        if format == "filebased":
            self.kfactor_file = "kfactor.rst"
            self.dtm_file = "dtm.rst"
            self.pfactor_file = "pfactor.rst"
            self.segments_file = "segments.rst"
            self.routing_file = "routing.rst"
            self.parcelmosaic_file = "parcels_landuse.rst"
            self.cfactor_file = "cfactor.rst"
            self.outlet_file = "outlet.rst"
            self.ktc_file = "ktc_map.rst"
            self.mask_file = "mask.rst"
            self.ditches_file = "ditches.rst"
            self.conductivedams_file = "conductivedams.rst"
            self.endpoints_file = "sewers.rst"
            self.endpoints_id_file = "sewers_id.rst"
            self.buffers_file = "buffers.rst"
            self.cn_file = "cn.rst"
            self.adjacentedges_file = "adjacent_edges.txt"
            self.upedges_file = "up_edges.txt"

        else:
            msg = f"Database format '{format} not implemented."
            raise NotImplementedError(msg)
