# implicit testing of the modelinput class
from pathlib import Path

from pywatemsedem.io.modelinput import Modelinput

# testing normal functioning


def test_modelinput_all():
    """tests for Modelinput class"""
    # Initialization
    file_path = Path("tests") / "io" / "data" / "modelinput"
    ini = file_path / "inifile.ini"
    example = Modelinput(ini, resolution=20, epsg=31370, nodata=-9999)

    # C-factor
    example.cfactor
    example.cfactor.plot()
    # example.cfactor.hv_plot()

    # Buffers: no data for langegracht
    example.buffers
    example.buffers.plot()
    # example.buffers.hv_plot()

    # DTM
    example.dtm
    example.dtm.plot()
    # example.dtm.hv_plot()

    # K-factor
    example.kfactor
    example.kfactor.plot()
    # example.kfactor.hv_plot()

    # kTC
    example.ktc
    example.ktc.plot()
    # example.ktc.hv_plot()

    # Outlet
    example.outlet
    example.outlet.plot()
    # example.outlet.hv_plot()

    # P-factor
    example.pfactor
    example.pfactor.plot()
    # example.pfactor.hv_plot()

    # landuseparcels
    example.compositelanduse
    # example.landuseparcels.plot()
    # example.landuseparcels.hv_plot()

    # PTEF
    example.ptef
    example.ptef.plot()
    # example.ptef.hv_plot()

    # riversegments
    example.riversegments
    example.riversegments.plot()
    # example.riversegments.hv_plot()

    # riverrouting
    example.riverrouting
    example.riverrouting.plot()
    # example.riverrouting.hv_plot()

    ## sewers
    # example.sewers
    # example.sewers.plot()
    ## example.sewers.hv_plot()

    # upstream segments
    example.upstream_segments

    # adjecant segments
    example.adjacent_segments
