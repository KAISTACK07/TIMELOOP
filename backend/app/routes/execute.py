from fastapi import APIRouter
from app.models.execution import ExecutionRequest, ExecutionResponse
from app.engine.executor import ExecutionEngine

router = APIRouter()
SESSION_STORE = {}


@router.post("/execute", response_model=ExecutionResponse)
def execute(payload: ExecutionRequest):
    engine = ExecutionEngine()
    result = engine.run(payload.code, payload.mode)
    SESSION_STORE[result["session_id"]] = {
    **result,
    "mode": payload.mode
}
    from app.utils.storage import save_session

    save_session(result["session_id"], {
        "snapshots": result["snapshots"],
        "variable_history": result["variable_history"],
        "line_index": result["line_index"]
    })
    return result

from fastapi import Query
from app.engine.reconstruction import reconstruct_state



@router.get("/state")
def get_state(session_id: str = Query(...), step: int = Query(...)):
    from app.utils.storage import load_session

    session = load_session(session_id)
    if not session:
        return {"error": "Invalid session_id"}

    snapshots = session["snapshots"]

    # validate step using set (fast + correct)
    steps = {snap["step"] for snap in snapshots}
    available_steps = sorted(snap["step"] for snap in snapshots)

    # find closest step <= requested step
    valid_step = None
    for s in available_steps:
        if s <= step:
            valid_step = s
        else:
            break

    if valid_step is None:
        return {"error": "Invalid step"}

    state = reconstruct_state(snapshots, valid_step)

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
def get_function_calls(session_id: str = Query(...), name: str = Query(...)):
    # 1. Validate session
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    session = SESSION_STORE[session_id]
    snapshots = session.get("snapshots", [])

    # 2. FAST mode guard
    if not snapshots or len(snapshots) <= 1:
        return {
            "error": "Detailed tracing required for function analysis"
        }

    # 3. Extract function calls
    calls = []

    for snap in snapshots:
        if snap.get("event") == "call" and snap.get("function") == name:
            calls.append(snap.get("step"))

    # 4. Handle no calls found
    if not calls:
        return {
            "function": name,
            "calls": [],
            "message": "No calls found for this function"
        }

    # 5. Return result
    return {
        "function": name,
        "calls": calls
    }


@router.get("/line")
def get_line_steps(
    session_id: str = Query(...),
    line_no: int = Query(...)
):
    # 1. Validate session
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    session = SESSION_STORE[session_id]
    snapshots = session.get("snapshots", [])

    # 2. FAST mode guard (important)
    if session.get("mode") == "fast":
        return {
            "line": line_no,
            "steps": [],
            "message": "Line tracking not available in fast mode"
        }
    # 3. Get line index
    line_index = session.get("line_index", {})

    steps = line_index.get(str(line_no)) or line_index.get(line_no)

    # 4. Line not executed
    if not steps:
        return {
            "line": line_no,
            "steps": [],
            "message": "Line not executed"
        }

    # 5. Success
    return {
        "line": line_no,
        "steps": steps
    }     
@router.get("/exceptions")
def get_exceptions(session_id: str):
    if session_id not in SESSION_STORE:
        return {"error": "Invalid session_id"}

    session = SESSION_STORE[session_id]
    snapshots = session.get("snapshots", [])

    errors = []

    for snap in snapshots:
        if snap.get("event") == "exception":
            errors.append({
                "step": snap.get("step"),
                "line_no": snap.get("line_no"),
                "error": snap.get("delta", {}).get("error")
            })

    if not errors:
        return {
            "exceptions": [],
            "message": "No exceptions occurred"
        }

    return {
        "exceptions": errors
    }   