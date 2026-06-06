"""Reflex 项目配置 — OA-EPP 考试系统"""
import reflex as rx

config = rx.Config(
    app_name="oaepp",
    db_url="sqlite:///oaepp.db",
)
