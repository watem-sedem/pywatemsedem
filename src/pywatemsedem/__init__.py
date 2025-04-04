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
import subprocess

try:
    subprocess.check_output(["saga_cmd", "topology"], stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
    if "Error: select a library" in e.output.decode():
        msg = (
            "SAGA/WaTEM is not properly installed, check the installation instruction "
            "in the documentation."
        )
        raise OSError(msg)
