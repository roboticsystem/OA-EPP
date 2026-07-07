"""
作业提交子系统 - 独立启动入口
不与 backend/ 目录耦合，可独立运行或由平台负责人后续集成。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .router import router

app = FastAPI(
    title="作业提交子系统 (F-S-020)",
    docs_url="/api/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()
    print("[assignments_app] 数据库初始化完成")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("assignments_app.main:app", host="0.0.0.0", port=8010,
                reload=True)
