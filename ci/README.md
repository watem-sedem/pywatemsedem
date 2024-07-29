# Drone CI Initial setup

## Activate your repository in drone

Go to [drone.fluves.net](https://drone.fluves.net), search for your repository and click on `activate`.

## Setup credentials in drone

Secrets are defined at organization level with following credentials already predefined, so no specific actions are required.

- To publish package releases to gitea, the `release_token` (see vault > `droneci - gitea release token`) is used.
- To publish your documentation as a website on [docs.fluves.net/](https://docs.fluves.net/), the `rsync_key` is used, see `vault > droneci - docs-rsync-key`.
- To publish the code coverage as a website on [coverage.fluves.net](https://coverage.fluves.net/), the `rsync_key` is used.

## Prepare Docker containers for drone CI runs

In order to run the `.drone.yml` CI runs, the required Docker containers need to exist in the
Fluves Docker registry [`registry.fluves.net`](https://registry.fluves.net/v2/_catalog).

The Docker specification is depending on the environment setup and the base template for `venv` and `conda`
are provided. Make sure to follow the Fluves docker name convention for tagging the
images: `registry.fluves.net/drone/PACKAGENAME/ENVIRONMENT-VERSION`, e.g. `registry.fluves.net/drone/pyws/venv-3.11`.

### Virtualenv

Do build a Docker image for virtualenv, choose a specific Python version. For example, prepare an image for Python 3.11:

```bash
docker build -f Dockerfile.venv -t registry.fluves.net/drone/pyws/venv-3.11 --build-arg "PYTHON_VERSION=3.11" .
docker push registry.fluves.net/drone/pyws/venv-3.11
```

**NOTE:** If you will use packages from the internal network, and you are using systemd-resolved or are not using the Fluves DNS, you must set the DNS for the Docker Daemon to the Fluves DNS: 10.28.0.1. To that end, create or edit **/etc/docker/daemon.json** and put:

```json
{
    "dns": ["10.28.0.1"]
}
```
w
If you need to test multiple Python versions, create an image for each Docker container and add a separate pipeline in
the `.drone.yml` file for each version.

### Conda

Using conda, the Python environment is part of the `environment.yml` file:

```bash
docker build -f Dockerfile.conda -t registry.fluves.net/drone/pyws/conda .
docker push registry.fluves.net/drone/pyws/conda
```

### Windows

The Windows Docker image is a generic image that is available on the Fluves Docker registry, see for [win-venv-3.11 image](example https://registry.fluves.net/#!/taglist/drone/win-venv-3.11).

To prepare a ew windows Docker built (e.g. with an updated python version), you need to build the Docker inside the Styx Windows VM:

- Log in with remote desktop
- Open Powershell as administrator
- Clone the repo (with the Docker file)
- Run the build command, e.g. for a Python version 3.11

  ```bash
  docker build -f Dockerfile.conda -t registry.fluves.net/drone/win-venv-3.11 .
  docker push registry.fluves.net/drone/win-venv-3.11 .
  ```
