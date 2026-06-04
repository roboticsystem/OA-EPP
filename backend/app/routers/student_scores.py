from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.auth_utils import verify_token
import sys, os

_backend_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from oaepp.states.score import ScoreState

router = APIRouter()


def _require_student(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    if payload.get("role") != "student":
        raise HTTPException(status_code=403, detail="仅限学生操作")
    return payload


@router.get("/api/student/dashboard")
def student_dashboard(authorization: Optional[str] = Header(None)):
    payload = _require_student(authorization)
    user_id = payload["user_id"]

    state = ScoreState()
    state.current_user_id = user_id
    import asyncio
    result = asyncio.run(state.load_scores())

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
