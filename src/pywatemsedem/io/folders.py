from dataclasses import dataclass
from pathlib import Path


@dataclass
class CatchmentFolder:
    home_folder: Path
    resolution: int

    def __post_init__(self):
        self.home_folder = Path(self.home_folder)
        self.catchment_folder = self.home_folder / "Data_Bekken"
        self.vct_folder = self.catchment_folder / "Shps"
        self.rst_folder = self.catchment_folder / f"Rst_{self.resolution}m"

    def create_all(self):
        self.check_home_folder(create=True)
        self.check_catchment_folder(create=True)
        self.check_vct_folder(create=True)
        self.check_rst_folder(create=True)

    def check_home_folder(self, **options):
        """Create home folder"""
        check_and_create_home_folder(self.home_folder, **options)

    def check_catchment_folder(self, **options):
        """Create 'Data_bekken' folder"""
        check_and_create_catchment_folder(self.home_folder, **options)

    def check_vct_folder(self, **options):
        """Create home folder"""
        check_and_create_vct_folder(self.catchment_folder, **options)

    def check_rst_folder(self, **options):
        """Create 'Data_bekken' folder"""
        check_and_create_rst_folder(self.catchment_folder, self.resolution, **options)


@dataclass
class ScenarioFolders:
    """Class for keeping track of Scenario folder names

    Parameters
    ----------
    cfolder: CatchmentFolder
        See :class:`pywatemsedem.io.folders.CatchmentFolder`
    scenario_label: str
        Specific label for scenario.
    """

    cfolder: CatchmentFolder
    scenario_label: str
    year: int

    def __post_init__(self):
        """Assign folder names to self"""
        self.scenario_folder = (
            self.cfolder.home_folder / f"scenario_{self.scenario_label}"
        )
        self.cnwsinput_folder = self.scenario_folder / "modelinput"
        self.cnwsoutput_folder = self.scenario_folder / "modeloutput"
        self.postprocess_folder = self.scenario_folder / "postprocessing"
        self.scenarioyear_folder = self.scenario_folder / f"{self.year}"

    def create_all(self):
        self.cfolder.create_all()
        self.check_scenario(create=True)
        self.check_cnwsinput(create=True)
        self.check_cnwsoutput(create=True)
        self.check_postprocessing(create=True)
        self.check_years(create=True)

    def check_scenario(self, **options):
        """Create 'scenario_x' folder"""
        check_and_create_scenario_folder(
            self.cfolder.home_folder, self.scenario_label, **options
        )

    def check_cnwsinput(self, **options):
        """Create 'scenario_x/modelinput' folder"""
        check_and_create_cnwsinput_folder(self.scenario_folder, **options)

    def check_cnwsoutput(self, **options):
        """Create 'scenario_x/modeloutput' folder"""
        check_and_create_cnwsoutput_folder(self.scenario_folder, **options)

    def check_postprocessing(self, **options):
        """Create 'scenario_x/postprocess' folder"""
        check_and_create_postprocessing_folder(self.scenario_folder, **options)

    def check_years(self, **options):
        """Create 'scenario_x/year' folder"""
        check_and_create_years_folder(self.scenario_folder, self.year, **options)


def check_and_create_home_folder(home_folder, **options):
    """Check and create home folder

    Parameters
    ----------
    home_folder: pathlib.Path
        Folder path of home.
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    check_and_create_folder(
        home_folder, msg_subject=f"Home folder '{home_folder}'", **options
    )


def check_and_create_catchment_folder(home_folder, **options):
    """Check and create home/catchment folder

    Parameters
    ----------
    home_folder: pathlib.Path
        Folder path of home.
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    check_and_create_folder(
        home_folder / "Data_Bekken",
        msg_subject=f"Catchment folder 'Data_bekken' in '{home_folder}'",
        **options,
    )


def check_and_create_rst_folder(catchment_folder, resolution, **options):
    """Check and create home/catchment/vct folder

    Parameters
    ----------
    catchment_folder: pathlib.Path
        See :func:`pywatemsedem.pywatemsedem.folders.check_and_create_catchment_folder`
    resolution: int
        Spatial resolution
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    check_and_create_folder(
        catchment_folder / f"Rst_{resolution}m",
        msg_subject=f"Vector folder 'Rst_{resolution}m' in '{catchment_folder}'",
        **options,
    )


def check_and_create_vct_folder(catchment_folder, **options):
    """Check and create home/catchment/vct folder

    Parameters
    ----------
    catchment_folder: pathlib.Path
        See :func:`pywatemsedem.pywatemsedem.folders.check_and_create_catchment_folder`
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    check_and_create_folder(
        catchment_folder / "Shps",
        msg_subject=f"Vector folder 'Shps' in '{catchment_folder}'",
        **options,
    )


def check_and_create_vctyears_folder(vct_folder, year, **options):
    """Check and create home/catchment/shps/year folder

    Parameters
    ----------
    vct_folder: pathlib.Path
        See :func:`pywatemsedem.pywatemsedem.folders.check_and_create_vct_folder`
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    check_and_create_folder(
        vct_folder / f"{year}",
        msg_subject=f"Year-folder '{year}' in '{vct_folder}'",
        **options,
    )


def check_and_create_scenario_folder(home_folder, scenario_label, **options):
    """Check and create home/scenario_x folder

    Parameters
    ----------
    home_folder: pathlib.Path
        Folder path of home.
    scenario_label: str
        Scenario label, can be string format of a numeric (e.g. 1, 2, ...) or
        string (e.g. A, B, ...)
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    check_and_create_folder(
        home_folder / f"scenario_{scenario_label}",
        msg_subject=f"Scenario folder with label "
        f"'{scenario_label}' in '{home_folder}'",
        **options,
    )


def check_and_create_cnwsinput_folder(scenario_folder, **options):
    """Check and create home/scenario_x/modelinput folder

    Parameters
    ----------
    scenario_folder: pathlib.Path
        Folder path subfolder *scenario_x* in home folder.
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    check_and_create_folder(
        scenario_folder / "modelinput",
        msg_subject=f"Subfolder 'modelinput' in '{scenario_folder}'",
        **options,
    )


def check_and_create_cnwsoutput_folder(scenario_folder, **options):
    """Check and create home/scenario_x/modeloutput folder

    Parameters
    ----------
    scenario_folder: pathlib.Path
        Folder path subfolder *scenario_x* in home folder.
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    folder = scenario_folder / "modeloutput"
    check_and_create_folder(
        folder, msg_subject=f"Subfolder 'modeloutput' in '{scenario_folder}'", **options
    )


def check_and_create_postprocessing_folder(scenario_folder, **options):
    """Check and create home/scenario_x/postprocessing folder

    Parameters
    ----------
    scenario_folder: pathlib.Path
        Folder path subfolder *scenario_x* in home folder.
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    folder = scenario_folder / "postprocessing"
    check_and_create_folder(
        folder, msg_subject=f"Subfolder 'postprocess' in '{scenario_folder}'", **options
    )


def check_and_create_years_folder(scenario_folder, year, **options):
    """Check and create home/scenario_x/year folder

    Parameters
    ----------
    scenario_folder: pathlib.Path
        Folder path subfolder *scenario_x* in home folder.
    year: list
        Years of simulation
    options:
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    """
    folder = scenario_folder / f"{year}"
    check_and_create_folder(
        folder,
        msg_subject=f"Subfolder '{year}' in " f"'{scenario_folder}'",
        **options,
    )


def check_and_create_folder(
    folder, msg_subject="Folder", create=False, error_if_empty=False
):
    """Check and create pywatemsedem folder

    Parameters
    ----------
    folder: pathlib.Path
        Folder path of pywatemsedem folder
    msg_subject: str
        Custom message used be to complete message
    create: bool
        Indicate whether you want to create the folder
    error_if_empty: bool
        See :func:`pywatemsedem.pywatemsedem.folders.error_if_folder_empty`
    """
    if not folder.exists():
        if create:
            folder.mkdir(exist_ok=True, parents=False)
        else:
            raise IOError(msg_subject + " does not exist.")
    else:
        throw_error_if_folder_empty(folder, msg_subject, error_if_empty)


def throw_error_if_folder_empty(folder, msg, error_if_empty):
    """Check if pywatemsedem folder is empty

    Parameters
    ----------
    folder: pathlib.Path
        See :func:`pywatemsedem.io.folders.check_and_create_folder`
    error_if_empty: bool
        Check if folder is empty
    """
    if error_if_empty:

        if not any(folder.iterdir()):
            raise IOError(msg + " is empty.")
