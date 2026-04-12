from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ExecutionRequest(BaseModel):
    code: str
    mode: Optional[str] = "fast"


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
    line_index: Dict[int, List[int]] = {}
    truncated: bool
    error: Optional[str] = None