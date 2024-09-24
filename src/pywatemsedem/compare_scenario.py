from pathlib import Path

import pandas as pd

from pywatemsedem.geo.utils import grid_difference
from pywatemsedem.io.modeloutput import load_total_sediment_file
from pywatemsedem.tools import zip_folder

from .postprocess import PostProcess


class DeltaScenario:
    """Construct a DeltaScenario instance with two instances of PostProcess

    Parameters
    ----------
    pp1: pywatemsedem.postproces.PostProcess
        First PostProcess instance of scenario used for the comparison.
    pp2: pywatemsedem.postproces.PostProcess
        Second PostProcess instance of scenario used for the comparison.
    resmap:
        Folder path used to write results to

    Examples
    --------
    Define inputs
        >>> pp1 = PostProcess(molenbeek, 1, 2019, 20, 31370)
        >>> pp2 = PostProcess(molenbeek, 2, 2019, 20, 31370)

    Run
        >>> delta_scenario = DeltaScenario(pp1,pp2)
        >>> delta_scenario.comparison_total_sediment_file()
        >>> ...
    """

    def __init__(self, pp1, pp2, resmap=None):
        """

        Parameters
        ----------
        pp1: pywatemsedem.core.postprocess.PostProcess
            See class:`pywatemsedem.postprocess.PostProcess`
        pp2: pywatemsedem.core.postprocess.PostProcess
            See class:`pywatemsedem.postprocess.PostProcess`
        resmap: str or pathlib.Path, default None
            Folder path of results map
        """
        if self.check_input(pp1):
            self.pp1 = pp1
        if self.check_input(pp2):
            self.pp2 = pp2
        if resmap is None:
            self.resmap = (
                Path.cwd()
                / pp1.catchment_name
                / f"compare_scenario{pp1.scenario}_{pp2.scenario}"
            )
        else:
            self.resmap = Path(resmap)
        if not self.resmap.exists():
            self.resmap.mkdir(parents=True, exist_ok=True)

        self.check_rasterprop()

    def check_input(self, pp):
        """Check the type of input given to DeltaScenario class

        Parameters
        ----------
        pp : pywatemsedem.postproces.PostProcess
            A PostProcess instance of scenario used for the comparison.
        """
        if not isinstance(pp, PostProcess):
            msg = (
                f"{pp} is not an instance of the class PostProcess, "
                f"see ~:class:pywatemsedem.postprocess.PostProcess"
            )
            raise IOError(msg)
        else:
            return True

    def check_rasterprop(self):
        """Check if the raster properties are equal for both scenario's"""
        rstparams1 = self.pp1.rstparams
        rstparams2 = self.pp2.rstparams
        if rstparams1 == rstparams2:
            return True
        else:
            return False

    def zip_files(self):
        """Zip output folder of deltascenario"""

        zip_folder(self.resmap)

    def comparison_total_sediment_file(self):
        """Compare the values in the total sediments file

        Returns
        -------
        df: pandas.DataFrame
            Holding results of summary values for run for scenario 1 and 2,
            and the difference between those values.

            - *sc1*: values for general statistics scenario 1
            - *sc2*: values for general statistics scenario 2
            - *difference*: difference between statistics scenario 1 and 2

        """
        df_1 = load_total_sediment_file(self.pp1.files["txt_total_sediment"])
        df_2 = load_total_sediment_file(self.pp2.files["txt_total_sediment"])

        df = pd.DataFrame(index=df_1.keys(), columns=["sc1", "sc2", "difference"])
        df["sc1"] = df_1.values()
        df["sc2"] = df_2.values()
        df["difference"] = df["sc1"] - df["sc2"]

        return df

    def difference_grids(self):
        """Make difference grids for a number of files"""
        difference_grids = [
            "rst_sediout",
            "rst_sediin",
            "rst_sediexport",
            "rst_watereros",
        ]

        for grid in difference_grids:
            rst_1 = self.pp1.files[grid]
            rst_2 = self.pp2.files[grid]
            rst_out = self.resmap / (grid + "_difference.rst")
            grid_difference(rst_1, rst_2, rst_out)
