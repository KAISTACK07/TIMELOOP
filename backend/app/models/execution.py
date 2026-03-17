from pydantic import BaseModel
from typing import List, Dict, Any


class ExecutionRequest(BaseModel):
    code: str


class Snapshot(BaseModel):
    step: int
    event: str
    line_no: int
    function: str
    locals: Dict[str, Any]


from typing import List, Dict, Any

class ExecutionResponse(BaseModel):
    session_id: str
    snapshots: List[Snapshot]
    variable_history: Dict[str, Any] = {}
    truncated: bool