from pydantic import BaseModel
from typing import List, Dict, Any , List, Optional


class ExecutionRequest(BaseModel):
    code: str

class Snapshot(BaseModel):
    step: int
    event: str
    line_no: int
    function: str
    stack: List[str]

    locals: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None
    is_full: bool


class ExecutionResponse(BaseModel):
    session_id: str
    snapshots: List[Snapshot]
    variable_history: Dict[str, Any] = {}
    truncated: bool