"""oaepp.utils.error_handler — 异常类型到错误码/文案的映射。

提供 handle_error() 统一异常处理入口，
以及 ERROR_MESSAGES / ERROR_POLICY 等配置常量。
"""

from typing import Any

from oaepp.constants import ErrorCode, ErrorSeverity


# ── 错误码 → 用户可见文案 ──
ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.FILE_TOO_LARGE: "文件大小超出限制",
    ErrorCode.UNSUPPORTED_FORMAT: "不支持的文件格式",
    ErrorCode.NETWORK_TIMEOUT: "网络请求超时，请检查网络连接",
    ErrorCode.NETWORK_ERROR: "网络连接异常，请稍后重试",
    ErrorCode.PERMISSION_DENIED: "权限不足，无法执行此操作",
    ErrorCode.EXAM_ALREADY_SUBMITTED: "该考试已提交，不可重复提交",
    ErrorCode.DEADLINE_PASSED: "提交截止时间已过",
    ErrorCode.AUTH_FAILED: "身份验证失败，请重新登录",
    ErrorCode.ACCOUNT_LOCKED: "账户已被锁定",
    ErrorCode.UNKNOWN: "未知错误，请稍后重试",
}

# ── 错误码 → 处理策略 ──
ERROR_POLICY: dict[ErrorCode, dict[str, Any]] = {
    ErrorCode.FILE_TOO_LARGE: {"retryable": False, "severity": ErrorSeverity.WARNING},
    ErrorCode.UNSUPPORTED_FORMAT: {"retryable": False, "severity": ErrorSeverity.WARNING},
    ErrorCode.NETWORK_TIMEOUT: {"retryable": True, "severity": ErrorSeverity.ERROR},
    ErrorCode.NETWORK_ERROR: {"retryable": True, "severity": ErrorSeverity.ERROR},
    ErrorCode.PERMISSION_DENIED: {"retryable": False, "severity": ErrorSeverity.ERROR},
    ErrorCode.EXAM_ALREADY_SUBMITTED: {"retryable": False, "severity": ErrorSeverity.WARNING},
    ErrorCode.DEADLINE_PASSED: {"retryable": False, "severity": ErrorSeverity.WARNING},
    ErrorCode.AUTH_FAILED: {"retryable": False, "severity": ErrorSeverity.ERROR},
    ErrorCode.ACCOUNT_LOCKED: {"retryable": False, "severity": ErrorSeverity.ERROR},
    ErrorCode.UNKNOWN: {"retryable": False, "severity": ErrorSeverity.ERROR},
}

# ── 异常类型 → ErrorCode 映射 ──
_EXCEPTION_MAP: dict[type, ErrorCode] = {
    TimeoutError: ErrorCode.NETWORK_TIMEOUT,
    ConnectionError: ErrorCode.NETWORK_ERROR,
    PermissionError: ErrorCode.PERMISSION_DENIED,
}


def handle_error(exc: Exception) -> tuple[ErrorCode, str, str, str]:
    """将异常映射为 (ErrorCode, 用户文案, 严重程度, 重试标签)。"""
    for exc_type, code in _EXCEPTION_MAP.items():
        if isinstance(exc, exc_type):
            policy = ERROR_POLICY.get(code, {})
            return (
                code,
                ERROR_MESSAGES.get(code, "未知错误"),
                policy.get("severity", ErrorSeverity.ERROR),
                "重试" if policy.get("retryable") else "",
            )
    return (
        ErrorCode.UNKNOWN,
        ERROR_MESSAGES[ErrorCode.UNKNOWN],
        ErrorSeverity.ERROR,
        "",
    )
