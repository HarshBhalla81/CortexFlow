from fastapi import FastAPI
import redis    

app = FastAPI()

r = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.get("/")
async def root():
    return {"message": "Gateway Running"}

@app.post("/request")
async def process_request(data: dict):

    r.xadd(
        "agent_stream",
        {"request": str(data)}
    )

    return {
        "status": "queued",
        "data": data
    }