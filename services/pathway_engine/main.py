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
    events = pw.io.http.read(
        host="0.0.0.0",
        port=8080,
        schema=AgenticEventSchema,
        json_utf8=True
    )
    
    # Example ETL: filter out tool calls for out-of-band watchdog processing
    tool_events = events.filter(events.event_type == 'tool_call')
    
    # Write full event log to CSV
    pw.io.csv.write(events, "data/agentic_events.csv")
    
    # Expose a derived stream for the BDH Watchdog to consume
    # In production, this might be pw.io.kafka.write or a distinct HTTP endpoint.
    # For now, we'll write to a distinct file or table that watchdog can tail.
    pw.io.csv.write(tool_events, "data/tool_events_watchdog.csv")
    
    # Execute the engine
    pw.run()

if __name__ == "__main__":
    run_stream()
