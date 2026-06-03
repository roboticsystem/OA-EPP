from dotenv import load_dotenv
from pathlib import Path

# 从项目根目录加载 .env 文件
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_file)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import init_db, seed_timeline_events
from app.sync_exams import sync_exams
from app.sync_chapters import sync_chapters
from app.routers import students, auth, exam, teacher, chapters, timeline

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
app.include_router(chapters.router)
app.include_router(timeline.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/teacher")
def teacher_page():
    return FileResponse(os.path.join(STATIC_DIR, "teacher.html"))


@app.get("/score")
def score_page():
    return FileResponse(os.path.join(STATIC_DIR, "score.html"))


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


@app.on_event("startup")
def startup():
    init_db()
    sync_chapters()
    sync_exams()
    seed_timeline_events()
