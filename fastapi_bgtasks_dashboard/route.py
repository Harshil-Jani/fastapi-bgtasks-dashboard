from fastapi import APIRouter, FastAPI, BackgroundTasks
from .core import _wrap_task
from .dashboard import router


# Mount background tasks dashboard.
def mount_bg_tasks_dashboard(app: FastAPI = None, mount_dashboard: bool = True):
    if getattr(BackgroundTasks, "_patched_by_bgtasks_dashboard", False):
        if app and mount_dashboard:
            app.include_router(router)
        return

    orig_add_task = BackgroundTasks.add_task

    def patched_add_task(self, func, *args, **kwargs):
        wrapped = _wrap_task(func, *args, **kwargs)
        return orig_add_task(self, wrapped)

    BackgroundTasks.add_task = patched_add_task
    BackgroundTasks._patched_by_bgtasks_dashboard = True

    if app and mount_dashboard:
        app.include_router(router)
