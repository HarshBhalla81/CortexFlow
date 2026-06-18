import pathway as pw
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define expanded schema for the World State
class AgenticEventSchema(pw.Schema):
    session_id: str
    task_id: str
    event_type: str  # e.g., 'user_prompt', 'model_thought', 'tool_call', 'tool_result'
    payload: str
    timestamp: float

def run_stream():
    logger.info("Starting Pathway Agentic Gateway Engine on 0.0.0.0:8080")
    
    # Ingest data using HTTP REST connector
    events, response_writer = pw.io.http.rest_connector(
        host="0.0.0.0",
        port=8080,
        schema=AgenticEventSchema
    )
    
    # Pathway rest_connector MUST have a response written back to the client
    # otherwise the HTTP request hangs forever, causing Gateway ReadTimeouts
    response_table = events.select(
        query_id=events.id,
        result=pw.apply(lambda x: {"status": "ok"}, events.id)
    )
    response_writer(response_table)
    
    
    
    # Write full event log to CSV
    pw.io.csv.write(events, "data/agentic_events.csv")
    
    # Write ALL events to the watchdog CSV so the Neural Watchdog can
    # perform anomaly detection and cycle detection on the full event stream
    pw.io.csv.write(events, "data/tool_events_watchdog.csv")
    
    # Execute the engine
    pw.run()

if __name__ == "__main__":
    run_stream()
