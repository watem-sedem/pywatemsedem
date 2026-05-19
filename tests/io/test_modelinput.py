# implicit testing of the modelinput class
from pathlib import Path

from pywatemsedem.io.modelinput import Modelinput

# testing normal functioning


def test_modelinput_all():
    """tests for Modelinput class"""
    # Initialization
    file_path = Path("tests") / "runs" / "langegracht" / "scenario_1" / "modelinput"
    ini = file_path / "inifile.ini"
    example = Modelinput(ini, resolution=20, epsg=31370, nodata=-9999)

    # C-factor
    example.cfactor = file_path / "cfactor.rst"
    example.cfactor.plot()
    # example.cfactor.hv_plot()

    # Buffers: no data for langegracht
    example.buffers = file_path / "buffers.rst"
    example.buffers.plot()
    # example.buffers.hv_plot()

    # DTM
    example.dtm = file_path / "dtm.rst"
    example.dtm.plot()
    # example.dtm.hv_plot()

    # K-factor
    example.kfactor = file_path / "kfactor.rst"
    example.kfactor.plot()
    # example.kfactor.hv_plot()

    # kTC
    example.ktc = file_path / "ktc_map.rst"
    example.ktc.plot()
    # example.ktc.hv_plot()

    # Outlet
    example.outlet = file_path / "Outlet.rst"
    example.outlet.plot()
    # example.outlet.hv_plot()

    # P-factor
    example.pfactor = file_path / "pfactor.rst"
    example.pfactor.plot()
    # example.pfactor.hv_plot()

    # landuseparcels
    example.compositelanduse = file_path / "parcels_landuse.rst"
    # example.landuseparcels.plot()
    # example.landuseparcels.hv_plot()

    # PTEF
    example.ptef = file_path / "PTEFmap.rst"
    example.ptef.plot()
    # example.ptef.hv_plot()

    # riversegments
    example.riversegments = file_path / "segments.rst"
    example.riversegments.plot()
    # example.riversegments.hv_plot()

    # riverrouting
    example.riverrouting = file_path / "routing.rst"
    example.riverrouting.plot()
    # example.riverrouting.hv_plot()

    ## sewers
    # example.sewers = file_path / "sewers.rst"
    # example.sewers.plot()
    ## example.sewers.hv_plot()

    # upstream segments
    example.upstreamsegments = file_path / "up_edges.txt"

    # adjecant segments
    example.adjacentsegments = file_path / "adjacentedges.txt"
