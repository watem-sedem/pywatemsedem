from importlib.metadata import PackageNotFoundError, version

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

# check if SAGA/WaTEM topology is installed properly
import os
import shutil
import subprocess
from pathlib import Path

# Check if saga_cmd executable can be found
if shutil.which("saga_cmd") is None:  # saga_cmd cannot be found in the PATH variable
    # Check if there is an environment variable "SAGA"
    if os.environ.get("SAGA") is not None and Path(os.environ.get("SAGA")).exists():
        os.environ["SAGA_TLB"] = os.environ.get("SAGA")
        os.environ["PATH"] = (
            os.environ.get("SAGA") + os.pathsep + os.environ["PATH"]
        )  # Add saga location to PATH
        if shutil.which("saga_cmd") is None:
            msg = (
                "SAGA is not properly installed, pywatemsedem cannot"
                " access saga_cmd via PATH or SAGA"
            )
            raise OSError(msg)
    else:
        msg = (
            "SAGA is not available in the environment variable PATH "
            "and there is no environment variable SAGA"
        )
        raise OSError(msg)

# Check if the topology module is installed
try:
    subprocess.check_output(["saga_cmd", "topology"], stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
    if "Error: select a library" in e.output.decode():
        msg = (
            "SAGA/WaTEM is not properly installed, check the installation instruction "
            "in the documentation."
        )
        raise OSError(msg)
