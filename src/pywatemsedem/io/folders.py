from dataclasses import dataclass
from pathlib import Path


def ensure_folder(
    folder: Path,
    *,
    create: bool = False,
    error_if_empty: bool = False,
):
    """Validate that a folder exists and optionally create it.

    Parameters
    ----------
    folder : Path
        Directory to validate.
    create : bool, default=False
        If ``True``, create ``folder`` (including parents) when it does not
        exist.
    error_if_empty : bool, default=False
        If ``True``, raise an error when the directory exists but contains no
        files or subdirectories.

    Raises
    ------
    FileNotFoundError
        If ``folder`` does not exist and ``create`` is ``False``.
    IOError
        If ``error_if_empty`` is ``True`` and the directory is empty.
    """

    if not folder.exists():
        if create:
            folder.mkdir(parents=True, exist_ok=True)
        else:
            raise FileNotFoundError(folder)

    if error_if_empty and not any(folder.iterdir()):
        raise IOError(f"{folder} is empty")


@dataclass
class CatchmentFolder:
    """Path container for the catchment-level input structure.

    Parameters
    ----------
    home_folder : Path
        Root directory where catchment data is stored.
    resolution : int
        Raster resolution in meters used to build the raster folder name.
    """

    home_folder: Path
    resolution: int

    def __post_init__(self):
        """Normalize ``home_folder`` to a ``Path`` instance."""
        self.home_folder = Path(self.home_folder)

    @property
    def catchment_folder(self) -> Path:
        """Return the main catchment data folder."""
        return self.home_folder / "Data_Bekken"

    @property
    def vct_folder(self) -> Path:
        """Return the directory containing vector shapefiles."""
        return self.catchment_folder / "Shps"

    @property
    def rst_folder(self) -> Path:
        """Return the resolution-specific raster directory."""
        return self.catchment_folder / f"Rst_{self.resolution}m"

    def create_all(self):
        """Create all catchment-level directories if they do not exist."""
        for folder in (
            self.home_folder,
            self.catchment_folder,
            self.vct_folder,
            self.rst_folder,
        ):
            folder.mkdir(parents=True, exist_ok=True)

    def check_all(self, **options):
        """Validate all catchment-level directories.

        Parameters
        ----------
        **options
            Keyword arguments forwarded to :func:`ensure_folder`.
        """
        for folder in (
            self.home_folder,
            self.catchment_folder,
            self.vct_folder,
            self.rst_folder,
        ):
            ensure_folder(folder, **options)


@dataclass
class ScenarioFolders:
    """Path container for scenario-specific model input/output folders.

    Parameters
    ----------
    cfolder : CatchmentFolder
        Catchment-level folder definition.
    scenario_label : str
        Scenario identifier used in the scenario folder name.
    year : int
        Simulation year used for the year-specific subfolder.
    """

    cfolder: CatchmentFolder
    scenario_label: str
    year: int

    @property
    def scenario_folder(self) -> Path:
        """Return the root folder for the selected scenario."""
        return self.cfolder.home_folder / f"scenario_{self.scenario_label}"

    @property
    def wsinput_folder(self) -> Path:
        """Return the model input directory for this scenario."""
        return self.scenario_folder / "modelinput"

    @property
    def wsoutput_folder(self) -> Path:
        """Return the model output directory for this scenario."""
        return self.scenario_folder / "modeloutput"

    @property
    def postprocess_folder(self) -> Path:
        """Return the postprocessing output directory."""
        return self.scenario_folder / "postprocessing"

    @property
    def year_folder(self) -> Path:
        """Return the year-specific scenario directory."""
        return self.scenario_folder / str(self.year)

    def create_all(self):
        """Create catchment and scenario directories when missing."""
        self.cfolder.create_all()

        for folder in (
            self.scenario_folder,
            self.wsinput_folder,
            self.wsoutput_folder,
            self.postprocessing_folder,
            self.year_folder,
        ):
            folder.mkdir(parents=True, exist_ok=True)

    def check_all(self, **options):
        """Validate catchment and scenario directories.

        Parameters
        ----------
        **options
            Keyword arguments forwarded to :func:`ensure_folder`.
        """
        self.cfolder.check_all(**options)

        for folder in (
            self.scenario_folder,
            self.wsinput_folder,
            self.wsoutput_folder,
            self.postprocessing_folder,
            self.year_folder,
        ):
            ensure_folder(folder, **options)
