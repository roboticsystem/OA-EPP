from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import init_db
from app.database_mysql import check_mysql_connection
from app.sync_exams import sync_exams
from app.routers import students, auth, exam, teacher, editor

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
app.include_router(editor.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/teacher")
def teacher_page():
    return FileResponse(os.path.join(STATIC_DIR, "teacher.html"))


@app.get("/score")
def score_page():
    return FileResponse(os.path.join(STATIC_DIR, "score.html"))


@app.get("/editor")
def editor_page():
    return FileResponse(os.path.join(STATIC_DIR, "editor.html"))


@app.get("/review")
def review_page():
    return FileResponse(os.path.join(STATIC_DIR, "review.html"))


@app.on_event("startup")
def startup():
    init_db()
    sync_exams()
    if check_mysql_connection():
        print("[startup] MySQL 连接成功 — 需求文档编辑器可用")
    else:
        print("[startup] WARNING: MySQL 不可达 — 需求文档编辑器将无法使用")