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
