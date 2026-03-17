from fastapi import APIRouter
from app.models.execution import ExecutionRequest, ExecutionResponse
from app.engine.executor import ExecutionEngine

router = APIRouter()


@router.post("/execute", response_model=ExecutionResponse)
def execute(payload: ExecutionRequest):
    engine = ExecutionEngine()
    result = engine.run(payload.code)
    return result