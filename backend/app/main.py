from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from app.database import init_db
from app.sync_exams import sync_exams
from app.routers import students, auth, exam, teacher, classroom_exam

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
app.include_router(classroom_exam.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

_CLASSROOM_EXAM_HTML = "classroom-exam.html"
_CLASSROOM_EXAM_ADMIN_HTML = "classroom-exam-admin.html"


def _static_file(name: str) -> FileResponse:
    path = os.path.join(STATIC_DIR, name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=500, detail=f"缺少静态文件: {name}")
    return FileResponse(path)


@app.get("/teacher")
def teacher_page():
    return FileResponse(os.path.join(STATIC_DIR, "teacher.html"))


@app.get("/score")
def score_page():
    return FileResponse(os.path.join(STATIC_DIR, "score.html"))


@app.get("/classroom-exam")
@app.get("/classroom-exam/")
def classroom_exam_page():
    return _static_file(_CLASSROOM_EXAM_HTML)


@app.get("/classroom-exam/admin")
@app.get("/classroom-exam/admin/")
def classroom_exam_admin_page():
    return _static_file(_CLASSROOM_EXAM_ADMIN_HTML)


# 浏览器常误开 /api/classroom-exam（API 前缀），返回页面而非 {"detail":"Not Found"}
@app.get("/api/classroom-exam")
@app.get("/api/classroom-exam/")
def classroom_exam_page_api_alias():
    return _static_file(_CLASSROOM_EXAM_HTML)


@app.get("/api/classroom-exam/admin")
@app.get("/api/classroom-exam/admin/")
def classroom_exam_admin_page_api_alias():
    return _static_file(_CLASSROOM_EXAM_ADMIN_HTML)


@app.on_event("startup")
def startup():
    init_db()
    sync_exams()