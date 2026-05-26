from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

from app.database import init_db
from app.sync_exams import sync_exams
from app.routers import students, auth, exam, teacher


def _get_suggestion(status_code: int) -> str:
    """根据 HTTP 状态码返回用户友好的操作建议"""
    suggestions = {
        400: "请检查输入信息是否正确",
        401: "请重新登录后再试",
        403: "您没有权限执行此操作，请联系老师",
        404: "请求的资源不存在",
        409: "数据已存在，请勿重复操作",
        413: "文件太大，请压缩或拆分后重试",
        422: "输入数据格式不正确，请检查后重试",
        500: "服务器内部错误，请稍后重试",
    }
    return suggestions.get(status_code, "操作失败，请稍后重试")

app = FastAPI(title="研究生课程《机器人系统》考试系统", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一格式化 HTTPException 响应，附加操作建议"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"ERR_{exc.status_code}",
            "detail": exc.detail,
            "suggestion": _get_suggestion(exc.status_code),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将 Pydantic 校验错误转为用户友好的提示"""
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "ERR_422",
            "detail": "输入数据格式不正确，请检查后重试",
            "suggestion": _get_suggestion(422),
        },
    )

app.include_router(students.router)
app.include_router(auth.router)
app.include_router(exam.router)
app.include_router(teacher.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
DOCS_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "assets")

# 挂载 docs/assets/ 目录，使 FastAPI 也能提供 MkDocs 的静态资源（错误处理模块等）
if os.path.isdir(DOCS_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=DOCS_ASSETS_DIR), name="docs_assets")


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