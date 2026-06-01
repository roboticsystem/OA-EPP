from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
from pathlib import Path

# 将项目根目录加入 Python 路径，使 oaepp 包可被导入
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# 自动加载项目根目录的 .env 文件（如果存在）
_env_file = _root / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from app.database import init_db
from app.sync_exams import sync_exams
from app.routers import students, auth, exam, teacher, commitlint

app = FastAPI(title="研究生课程《机器人系统》考试系统", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students.router)
app.include_router(auth.router)
app.include_router(exam.router)
app.include_router(teacher.router)
app.include_router(commitlint.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/teacher")
def teacher_page():
    return FileResponse(os.path.join(STATIC_DIR, "teacher.html"))


@app.get("/score")
def score_page():
    return FileResponse(os.path.join(STATIC_DIR, "score.html"))


@app.on_event("startup")
def startup():
    init_db()
    sync_exams()