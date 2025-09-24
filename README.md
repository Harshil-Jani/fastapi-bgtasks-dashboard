# FastAPI Background Tasks Dashboard

A simple and lightweight open-source dashboard to see what your FastAPI background tasks are doing in real time.

![Dashboard Preview](https://raw.githubusercontent.com/Harshil-Jani/fastapi-bgtasks-dashboard/refs/heads/main/image.png)

Just **one line** to get your dashboard running — mount that dashboard on your FastAPI app and you’re done:

```python
from fastapi import FastAPI
from fastapi_bgtasks_dashboard import mount_bg_tasks_dashboard

app = FastAPI()

# Add dashboard for background tasks
mount_bg_tasks_dashboard(app=app)
```

## Why this project?

FastAPI has a built-in `BackgroundTasks` feature that lets you run things after sending a response. But

- You don’t get a live view of what tasks are running.
- You don’t know when they start or finish.
- If something fails, there’s no quick way to check.
- If some tasks run without you noticing then your resources may exhaust.

This project was built to fill that gap.

Now you can have a clean, lightweight dashboard to watch your background jobs, with no external services or heavy dependencies.

# Installation

```
pip install fastapi-bgtasks-dashboard
```

# Quick Usage Example

Create a file `main.py` and install dependencies
```
pip install fastapi uvicorn
pip install fastapi-bgtasks-dashboard
```

Add the following code to `main.py`
```python
from fastapi import FastAPI, BackgroundTasks
from fastapi_bgtasks_dashboard import mount_bg_tasks_dashboard

app = FastAPI()

# Add dashboard for background tasks
mount_bg_tasks_dashboard(app=app)

def simple_task(name: str):
    import time
    print(f"Started task for {name}")
    time.sleep(20)
    print(f"Finished task for {name}")

@app.get("/hello/{name}")
async def say_hello(name: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(simple_task, name)
    return {"message": f"Hello {name}, task started in background!"}
```

Run the server with:

```
uvicorn main:app --reload
```

Now open your browser at:
👉 http://localhost:8000/dashboard

You’ll see a live dashboard of all background tasks.

# Features & Roadmap

- [ ] Persistent storage support (SQLite, Postgres, etc.)
- [ ] Export tasks to JSON/CSV
- [x] Real-time updates (via WebSocket)
- [x] Sortable columns (default: newest first)
- [x] Filter by function name or status
- [x] Paginate after 100 tasks for smooth performance
- [x] Display task duration in ms / s / m / h
- [x] Show task parameters
- [x] Run tasks again with one click
- [x] Clear all in-memory tasks instantly
- [x] Lightweight in-memory storage (no database required)

## Contributing

We welcome contributions! Whether it's fixing bugs, improving the dashboard, or adding new features, you can help make this project better.

### How to Contribute

1.  **Clone the repository**

    ```bash
    git clone git@github.com:Harshil-Jani/fastapi-bgtasks-dashboard.git
    cd fastapi-bgtasks-dashboard
    ```

2.  **Install the package locally**

    ```bash
    pip install -e .
    ```

    This command installs the package in editable mode, so any changes you make locally will be immediately reflected.

3.  **Run the example usage script**

    There is a `usage.py` file that demonstrates how to use the dashboard.
    Install fastapi and uvicorn to run this script.

    ```bash
    pip install fastapi uvicorn
    ```


    ```bash
    uvicorn usage:app --reload
    ```

    You can then test your changes by opening your browser to `http://localhost:8000/dashboard`.

4.  **Make your changes**
    * Fix bugs
    * Add new features
    * Improve documentation

5.  **Submit a Pull Request**

    Once you're happy with your changes, commit them with a clear message and open a pull request against the `main` branch. We'll review it and merge it if everything looks good.

> **Note:** This project is designed to be lightweight and easy to use, so please keep new features aligned with this philosophy whenever possible.

# License

MIT – Free to use and improve.
Made with ❤️ for the open-source community.