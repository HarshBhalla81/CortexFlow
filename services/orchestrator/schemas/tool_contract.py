import json
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any

class ToolDispatchSchema(BaseModel):
    """
    Strict JSON schema specification for agent tool-dispatches.
    Ensures variations in provider function-calling syntax are normalized
    before hitting the Pathway stream.
    """
    tool_name: str = Field(..., description="The exact name of the tool to be invoked.")
    tool_arguments: Dict[str, Any] = Field(default_factory=dict, description="Parsed JSON arguments for the tool.")
    agent_id: str = Field(..., description="Identifier of the agent making the call.")
    session_id: str = Field(..., description="Session identifier for tracking.")

def validate_tool_dispatch(raw_dispatch: dict) -> ToolDispatchSchema:
    try:
        # If arguments come in as a string (common with LLMs), parse it
        if isinstance(raw_dispatch.get("tool_arguments"), str):
            raw_dispatch["tool_arguments"] = json.loads(raw_dispatch["tool_arguments"])
        return ToolDispatchSchema(**raw_dispatch)
    except ValidationError as e:
        raise ValueError(f"Invalid tool dispatch format: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Tool arguments are not valid JSON: {e}")
