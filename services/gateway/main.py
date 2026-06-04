from fastapi import FastAPI

from routing.task import router as task_router
from routing.results import router as result_router
from shared.metrics import metrics

app = FastAPI()

app.include_router(task_router)
app.include_router(result_router)


@app.get("/")
async def root():
    return {"message": "Gateway Running"}

@app.get("/metrics")
def get_metrics():
    return metrics.get_metrics()