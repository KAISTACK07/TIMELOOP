from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ExecutionRequest(BaseModel):
    code: str
    mode: Optional[str] = "smart"


class Snapshot(BaseModel):
    step: int
    event: str
    line_no: int
    call_site_line: Optional[int] = None
    function: str
    stack: List[str]

    locals: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None
    value: Optional[Any] = None
    branch: Optional[str] = None
    iteration: Optional[int] = None
    loop_var: Optional[Dict[str, Any]] = None
    is_full: bool


class ExecutionResponse(BaseModel):
    session_id: str
    snapshots: List[Snapshot]
    variable_history: Dict[str, Any] = {}
    line_index: Dict[int, List[int]] = {}
    function_calls: Optional[List[Dict[str, Any]]] = []
    truncated: bool
    error: Optional[str] = None