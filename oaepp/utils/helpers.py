"""
OA-EPP 通用工具函数

所有工具函数由负责人统一维护，学生只能调用，禁止修改或重写。

需求编号：F-S-001 ~ F-S-053（全局共享）
"""

import re
from typing import Optional


def validate_student_no(student_no: str) -> bool:
    """验证学号格式：10位数字"""
    return bool(re.match(r"^\d{10}$", student_no))


def validate_github_username(username: str) -> bool:
    """验证 GitHub 用户名格式：字母、数字、连字符、下划线，2-39 字符"""
    return bool(re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9_-]{0,37}[a-zA-Z0-9])?$", username))


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def format_score(score: float, total: float = 100.0) -> str:
    """格式化得分显示"""
    percentage = (score / total) * 100 if total > 0 else 0
    return f"{score:.1f}/{total:.0f} ({percentage:.1f}%)"


def generate_preview_url(pr_number: int, route: str) -> str:
    """
    生成 PR Preview 功能的 URL。

    根据 PR 编号和功能路由，生成可访问的预览 URL。

    Args:
        pr_number: PR 编号（整数）
        route: 功能路由路径（如 "/grades"、"/assignments"）

    Returns:
        完整的预览 URL 字符串

    Examples:
        >>> generate_preview_url(118, "/grades")
        'https://118.oaepp-reflex.uwis.cn/grades'
        >>> generate_preview_url(119, "/assignments")
        'https://119.oaepp-reflex.uwis.cn/assignments'
    """
    route_path = route.lstrip("/") if route else ""
    return f"https://{pr_number}.oaepp-reflex.uwis.cn/{route_path}"


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    # 移除路径分隔符和特殊字符
    sanitized = re.sub(r"[^\w\-.]", "_", filename)
    # 限制长度
    return sanitized[:255] if len(sanitized) > 255 else sanitized


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本，超出部分添加省略号"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
