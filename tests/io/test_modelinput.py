# implicit testing of the modelinput class

from pathlib import Path

import pytest

from pywatemsedem.io.modelinput import Modelinput

# testing normal functioning


@pytest.mark.skip(
    reason="test gives saga-issues in conda pipeline, ommited, raised as"
    " issue in saga"
)
def test_modelinput_all():
    """tests for Modelinput class"""
    # folder = Path(r"pywatemsedem/tests/io/data")
    folder = Path("tests") / "io" / "data"
    filepath = folder / "model_in"
    P_ex = filepath / "pfactor.rst"
    example = Modelinput(P_ex, resolution=20, epsg=31370, nodata=-9999)
    # C-factor
    example.cfactor = filepath / "cfactor.rst"
    example.cfactor.plot()
    # example.cfactor.hv_plot()
    # Buffers: no data for langegracht
    example.buffers = filepath / "buffers.rst"
    example.buffers.plot()
    # example.buffers.hv_plot()
    # DTM
    example.dtm = filepath / "dtm.rst"
    example.dtm.plot()
    # example.dtm.hv_plot()
    # K-factor
    example.kfactor = filepath / "Kfactor.rst"
    example.kfactor.plot()
    # example.kfactor.hv_plot()
    # kTC
    example.ktc = filepath / "ktc.rst"
    example.ktc.plot()
    # example.ktc.hv_plot()
    # Outlet
    example.outlet = filepath / "Outlet.rst"
    example.outlet.plot()
    # example.outlet.hv_plot()
    # P-factor
    example.pfactor = P_ex
    example.pfactor.plot()
    # example.pfactor.hv_plot()
    # landuseparcels
    example.compositelanduse = filepath / "perceelskaart.rst"
    # example.landuseparcels.plot()
    # example.landuseparcels.hv_plot()
    # PTEF
    example.ptef = filepath / "PTEFmap.rst"
    example.ptef.plot()
    # example.ptef.hv_plot()
    # riversegments
    example.riversegments = filepath / "segments.rst"
    example.riversegments.plot()
    # example.riversegments.hv_plot()
    # riverrouting
    example.riverrouting = filepath / "routing.rst"
    example.riverrouting.plot()
    # example.riverrouting.hv_plot()
    # sewers
    example.sewers = filepath / "sewers.rst"
    example.sewers.plot()
    # example.sewers.hv_plot()
    # upstream segments
    example.upstreamsegments = filepath / "upedges.txt"
    # adjecant segments
    example.adjacentsegments = filepath / "adjedges.txt"
