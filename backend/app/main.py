from dotenv import load_dotenv
from pathlib import Path

# 从项目根目录加载 .env 文件（存在时）
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_file) if _env_file.exists() else None

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from app.database import init_db, seed_timeline_events
from app.sync_exams import sync_exams
from app.sync_chapters import sync_chapters
from app.routers import (
    students,
    auth,
    exam,
    teacher,
    report,
    notifications,
    chapters,
    timeline,
)
# classroom_exam 是 feature 分支新增的路由，若存在则包含
try:
    from app.routers import classroom_exam
    _HAS_CLASSROOM_EXAM = True
except Exception:
    _HAS_CLASSROOM_EXAM = False

app = FastAPI(title="嵌入式系统综合实践 - OA-EPP", docs_url="/api/docs")

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
app.include_router(report.router)
if _HAS_CLASSROOM_EXAM:
    app.include_router(classroom_exam.router)
app.include_router(notifications.router)
app.include_router(chapters.router)
app.include_router(timeline.router)

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


# classroom-exam 页面（feature 分支提供）
if _HAS_CLASSROOM_EXAM:
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


@app.get("/profile")
def profile_page():
    return FileResponse(os.path.join(STATIC_DIR, "profile.html"))


@app.get("/courses")
def courses_page():
    return FileResponse(os.path.join(STATIC_DIR, "courses.html"))


@app.get("/course")
def course_detail_page():
    return FileResponse(os.path.join(STATIC_DIR, "course.html"))


@app.get("/chapter")
def chapter_page():
    return FileResponse(os.path.join(STATIC_DIR, "chapter.html"))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup():
    init_db()
    sync_chapters()
    sync_exams()
    seed_timeline_events()
