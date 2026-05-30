from fastapi import FastAPI

from routing.task import router as task_router
from routing.results import router as result_router

app = FastAPI()

app.include_router(task_router)
app.include_router(result_router)


@app.get("/")
async def root():
    return {"message": "Gateway Running"}