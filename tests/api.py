from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/run-test/{test_name}")
async def run_test(test_name: str):
    allowed_tests = {
        "stress": "tests/stress_tester.py",
        "metrics": "tests/metrics_analyzer.py"
    }

    if test_name not in allowed_tests:
        return {"error" : "Invalid test name"}

    script = allowed_tests[test_name]

    try:
        result = subprocess.run(
            ["python", script],
            capture_output = True,
            text = True,
            timeout = 45
        )

        return {
            "test" : test_name,
            "stdout" : result.stdout,
            "stderr" : result.stderr,
            "returncode" : result.returncode
        }
    
    except Exception as e:
        return {"error": str(e)}