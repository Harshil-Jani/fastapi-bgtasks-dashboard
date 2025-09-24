from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("fastapi-bgtasks-dashboard")  # project name from pyproject.toml
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

from .route import mount_bg_tasks_dashboard

__all__ = ["mount_bg_tasks_dashboard"]
