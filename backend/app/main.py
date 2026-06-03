from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import init_db, seed_timeline_events
from app.sync_exams import sync_exams
from app.routers import students, auth, exam, teacher, timeline

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
app.include_router(timeline.router)

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
    seed_timeline_events()