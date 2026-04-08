from fastapi import APIRouter
from app.models.execution import ExecutionRequest, ExecutionResponse
from app.engine.executor import ExecutionEngine

router = APIRouter()
SESSION_STORE = {}


@router.post("/execute", response_model=ExecutionResponse)
def execute(payload: ExecutionRequest):
    engine = ExecutionEngine()
    result = engine.run(payload.code)

    #  store snapshots using session_id
    SESSION_STORE[result["session_id"]] = {
    "snapshots": result["snapshots"],
    "variable_history": result["variable_history"],
    "line_index": result["line_index"]
    }
    return result

from fastapi import Query
from app.engine.reconstruction import reconstruct_state



@router.get("/state")
def get_state(session_id: str = Query(...), step: int = Query(...)):
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    snapshots = SESSION_STORE[session_id]

    if step < 0 or step >= len(snapshots):
        return {"error": "Invalid step"}

    state = reconstruct_state(snapshots, step)

    return {
        "step": step,
        "state": state
    }
@router.get("/variable-history")
def get_variable_history(session_id: str, name: str):
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    session = SESSION_STORE[session_id]
    variable_history = session.get("variable_history", {})
    history = variable_history.get(name, [])

    formatted_history = [
        {"step": step, "value": value}
        for step, value in history
    ]

    return {
        "variable": name,
        "history": formatted_history
    }
@router.get("/function-calls")
def get_function_calls(session_id: str, name: str):
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    session = SESSION_STORE[session_id]
    snapshots = session["snapshots"]

    calls = []

    for snap in snapshots:
        if snap["event"] == "call" and snap["function"] == name:
            calls.append(snap["step"])

    return {
        "function": name,
        "calls": calls
    } 
@router.get("/jump-to-line")
def jump_to_line(session_id: str, line: int):
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    session = SESSION_STORE[session_id]

    line_index = session.get("line_index", {})

    steps = line_index.get(line, [])

    return {
        "line": line,
        "steps": steps
    }        
@router.get("/exceptions")
def get_exceptions(session_id: str):
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    session = SESSION_STORE[session_id]
    snapshots = session["snapshots"]

    exceptions = []

    # for snap in snapshots:
    #     if snap["event"] == "exception":
    #         exceptions.append({
    #             "step": snap["step"],
    #             "line": snap["line_no"],
    #             "function": snap["function"]
    #         })
    for snap in snapshots:
        if snap["event"] == "exception":
            print("FOUND EXCEPTION:", snap)        

    return {
        "exceptions": exceptions
    }    