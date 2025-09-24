from fastapi import FastAPI, APIRouter, BackgroundTasks, WebSocket
from datetime import datetime
import inspect, uuid, threading, json, traceback, asyncio, typing
from .utils import _dt

# In-memory store for tasks
_tasks: dict = {}
_tasks_lock = threading.Lock()

# Connected websocket clients
_ws_connections: typing.Set[WebSocket] = set()
_ws_lock = threading.Lock()

# Store actual function objects for rerun
_registered_funcs: dict = {}

router = APIRouter()


# Broadcast current tasks snapshot
def _broadcast_update():
    with _tasks_lock:
        payload = {
            "tasks": [
                {
                    "id": tid,
                    "func": data["func_name"],
                    "status": data["status"],
                    "started_at": _dt(data.get("started_at")),
                    "ended_at": _dt(data.get("ended_at")),
                    "params": data.get("params", {}),
                }
                for tid, data in _tasks.items()
            ]
        }
    text = json.dumps(payload)

    async def _send_all():
        to_remove = []
        with _ws_lock:
            conns = list(_ws_connections)
        for ws in conns:
            try:
                await ws.send_text(text)
            except Exception:
                to_remove.append(ws)
        if to_remove:
            with _ws_lock:
                for ws in to_remove:
                    if ws in _ws_connections:
                        _ws_connections.remove(ws)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_send_all())
        else:
            asyncio.new_event_loop().run_until_complete(_send_all())
    except RuntimeError:
        asyncio.new_event_loop().run_until_complete(_send_all())


# Wrap task to track lifecycle + params
def _wrap_task(func, *args, **kwargs):
    task_id = str(uuid.uuid4())
    started_at = None
    ended_at = None

    # bind parameters
    bound_params = {}
    try:
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        for k, v in bound.arguments.items():
            try:
                json.dumps(v)
                bound_params[k] = v
            except Exception:
                bound_params[k] = repr(v)
    except Exception:
        bound_params = {"args": args, "kwargs": kwargs}

    # register function for rerun
    _registered_funcs[func.__name__] = func

    # register task as queued
    with _tasks_lock:
        _tasks[task_id] = {
            "func_name": getattr(func, "__name__", str(func)),
            "status": "queued",
            "started_at": None,
            "ended_at": None,
            "params": bound_params,
        }
    _broadcast_update()

    def _runner():
        nonlocal started_at, ended_at
        with _tasks_lock:
            _tasks[task_id]["status"] = "running"
            _tasks[task_id]["started_at"] = datetime.utcnow()
        _broadcast_update()

        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    fut = asyncio.run_coroutine_threadsafe(result, loop)
                    fut.result()
                else:
                    asyncio.get_event_loop().run_until_complete(result)
            with _tasks_lock:
                _tasks[task_id]["status"] = "finished"
        except Exception as e:
            tb = traceback.format_exc()
            with _tasks_lock:
                _tasks[task_id]["status"] = f"failed: {str(e)}"
                _tasks[task_id]["error_trace"] = tb
        finally:
            ended_at = datetime.utcnow()
            with _tasks_lock:
                _tasks[task_id]["ended_at"] = ended_at
            _broadcast_update()

    return _runner
