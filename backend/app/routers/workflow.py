import os
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, List
from pydantic import BaseModel
from app.database import db
from app.auth_utils import verify_teacher_token
from app.services.github_service import github_service

router = APIRouter()

COURSE_ID = os.environ.get("COURSE_ID", "default")


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


class RuleConfig(BaseModel):
    """规则配置"""
    course_id: str = COURSE_ID
    require_pr_on_close: bool = True
    require_merged_pr: bool = False


class CloseIssueRequest(BaseModel):
    """关闭Issue请求"""
    issue_number: int
    pr_number: Optional[int] = None
    close_comment: Optional[str] = ""
    github_owner: str
    github_repo: str


class PRValidationResponse(BaseModel):
    """PR验证响应"""
    valid: bool
    exists: bool
    number: Optional[int] = None
    title: Optional[str] = None
    state: Optional[str] = None
    is_merged: Optional[bool] = None
    message: str


class IssueAssociationResponse(BaseModel):
    """Issue关联响应"""
    success: bool
    issue_number: int
    pr_number: int
    pr_title: str
    pr_state: str
    pr_merged: bool
    message: str


class WarningRecord(BaseModel):
    """警告记录"""
    id: int
    course_id: str
    issue_number: int
    issue_title: Optional[str]
    closed_by: Optional[str]
    closed_at: Optional[str]
    warning_type: str
    warning_message: str
    resolved: bool
    created_at: str


@router.get("/api/workflow/rule")
async def get_rule_config(
    course_id: str = Query(COURSE_ID),
    authorization: Optional[str] = Header(None)
):
    """获取课程的Issue-PR规则配置"""
    _require_teacher(authorization)
    
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT require_pr_on_close, require_merged_pr FROM issue_pr_rules WHERE course_id = %s",
            (course_id,)
        )
        rule = cur.fetchone()
        
        if rule:
            return {
                "course_id": course_id,
                "require_pr_on_close": bool(rule["require_pr_on_close"]),
                "require_merged_pr": bool(rule["require_merged_pr"])
            }
        else:
            # 默认规则：开启强制关联PR，不要求已合并
            return {
                "course_id": course_id,
                "require_pr_on_close": True,
                "require_merged_pr": False
            }


@router.post("/api/workflow/rule")
async def set_rule_config(
    config: RuleConfig,
    authorization: Optional[str] = Header(None)
):
    """设置课程的Issue-PR规则配置"""
    _require_teacher(authorization)
    
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO issue_pr_rules (course_id, require_pr_on_close, require_merged_pr)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                require_pr_on_close = VALUES(require_pr_on_close),
                require_merged_pr = VALUES(require_merged_pr),
                updated_at = CURRENT_TIMESTAMP
        """, (config.course_id, config.require_pr_on_close, config.require_merged_pr))
    
    return {
        "success": True,
        "message": "规则配置已更新",
        "config": {
            "course_id": config.course_id,
            "require_pr_on_close": config.require_pr_on_close,
            "require_merged_pr": config.require_merged_pr
        }
    }


@router.get("/api/workflow/validate-pr")
async def validate_pr(
    pr_number: int = Query(...),
    github_owner: str = Query(...),
    github_repo: str = Query(...),
    authorization: Optional[str] = Header(None)
):
    """验证PR编号是否存在（实时GitHub API校验）"""
    _require_teacher(authorization)
    
    try:
        result = await github_service.validate_pr_number(github_owner, github_repo, pr_number)
        return PRValidationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR验证失败: {str(e)}")


@router.post("/api/workflow/close-issue")
async def close_issue_with_pr(
    request: CloseIssueRequest,
    authorization: Optional[str] = Header(None)
):
    """关闭Issue并关联PR（平台内关闭流程）"""
    _require_teacher(authorization)
    
    # 获取当前课程规则配置
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT require_pr_on_close, require_merged_pr FROM issue_pr_rules WHERE course_id = %s",
            (COURSE_ID,)
        )
        rule = cur.fetchone()
        require_pr = rule["require_pr_on_close"] if rule else True
        require_merged = rule["require_merged_pr"] if rule else False
    
    # 检查是否需要关联PR
    if require_pr and not request.pr_number:
        raise HTTPException(status_code=400, detail="当前课程规则要求关闭Issue时必须关联PR编号")
    
    # 如果提供了PR编号，验证PR
    pr_info = None
    if request.pr_number:
        try:
            pr_info = await github_service.validate_pr_number(
                request.github_owner, request.github_repo, request.pr_number
            )
            
            if not pr_info["valid"]:
                raise HTTPException(status_code=400, detail=pr_info["message"])
            
            # 如果规则要求PR必须已合并
            if require_merged and not pr_info["is_merged"]:
                return {
                    "success": False,
                    "need_confirmation": True,
                    "message": f"PR #{request.pr_number} 尚未合并，确定要关闭Issue吗？",
                    "pr_info": pr_info
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PR验证失败: {str(e)}")
    
    # 获取Issue信息
    try:
        issue = await github_service.get_issue(
            request.github_owner, request.github_repo, request.issue_number
        )
        if not issue:
            raise HTTPException(status_code=404, detail=f"Issue #{request.issue_number} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Issue查询失败: {str(e)}")
    
    # 构建评论内容
    comment = request.close_comment or ""
    if request.pr_number and pr_info:
        pr_ref = f"关联PR: #{request.pr_number} ({pr_info['title']})"
        if comment:
            comment = f"{comment}\n\n{pr_ref}"
        else:
            comment = pr_ref
    
    # 关闭Issue
    try:
        success = await github_service.close_issue(
            request.github_owner, request.github_repo, request.issue_number, comment
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Issue关闭失败: {str(e)}")
    
    # 记录关联关系
    if success and request.pr_number and pr_info:
        with db() as conn:
            cur = conn.cursor()
            merged_at = pr_info.get("merged_at")
            cur.execute("""
                INSERT INTO issue_pr_associations (
                    course_id, issue_number, pr_number, pr_title, pr_state, pr_merged_at, closed_by, closed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                    pr_number = VALUES(pr_number),
                    pr_title = VALUES(pr_title),
                    pr_state = VALUES(pr_state),
                    pr_merged_at = VALUES(pr_merged_at),
                    closed_at = NOW()
            """, (
                COURSE_ID,
                request.issue_number,
                request.pr_number,
                pr_info.get("title", ""),
                pr_info.get("state", ""),
                merged_at,
                issue.get("closed_by", "")
            ))
    
    return {
        "success": True,
        "message": f"Issue #{request.issue_number} 已成功关闭",
        "issue_number": request.issue_number,
        "pr_number": request.pr_number,
        "pr_info": pr_info
    }


@router.get("/api/workflow/issue/{issue_number}")
async def get_issue_association(
    issue_number: int,
    authorization: Optional[str] = Header(None)
):
    """获取Issue的关联信息"""
    _require_teacher(authorization)
    
    # 从数据库获取关联记录
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM issue_pr_associations WHERE course_id = %s AND issue_number = %s",
            (COURSE_ID, issue_number)
        )
        association = cur.fetchone()
    
    if association:
        return {
            "issue_number": association["issue_number"],
            "pr_number": association["pr_number"],
            "pr_title": association["pr_title"],
            "pr_state": association["pr_state"],
            "pr_merged": association["pr_merged_at"] is not None,
            "pr_merged_at": association["pr_merged_at"],
            "closed_by": association["closed_by"],
            "closed_at": association["closed_at"]
        }
    else:
        return {
            "issue_number": issue_number,
            "pr_number": None,
            "message": "该Issue尚未关联PR"
        }


@router.post("/api/workflow/webhook/issue-close")
async def handle_github_webhook(
    payload: dict
):
    """处理GitHub Issue关闭事件的Webhook"""
    # 解析GitHub Webhook payload
    action = payload.get("action")
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})
    
    # 只处理Issue关闭事件
    if action != "closed":
        return {"success": True, "message": "非关闭事件，忽略"}
    
    issue_number = issue.get("number")
    issue_title = issue.get("title")
    closed_by = issue.get("closed_by", {}).get("login", "")
    closed_at = issue.get("closed_at")
    repo_full_name = repository.get("full_name", "")
    
    if not issue_number:
        return {"success": False, "message": "缺少Issue编号"}
    
    # 获取当前课程规则
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT require_pr_on_close FROM issue_pr_rules WHERE course_id = %s",
            (COURSE_ID,)
        )
        rule = cur.fetchone()
        require_pr = rule["require_pr_on_close"] if rule else True
    
    # 如果规则不要求PR，直接返回
    if not require_pr:
        return {"success": True, "message": "规则未启用，忽略"}
    
    # 检查是否已存在关联记录
    cur.execute(
        "SELECT pr_number FROM issue_pr_associations WHERE course_id = %s AND issue_number = %s",
        (COURSE_ID, issue_number)
    )
    existing_association = cur.fetchone()
    
    if existing_association:
        # 已有关联记录，更新PR状态（如果需要）
        return {"success": True, "message": "Issue已关联PR，无需处理"}
    
    # 检查Issue body中是否包含PR引用（如 "Fixes #123" 或关联的PR）
    issue_body = issue.get("body", "")
    has_pr_reference = any(keyword in issue_body.lower() for keyword in ["#", "pull request", "pr #"])
    
    if not has_pr_reference:
        # 生成警告记录
        cur.execute("""
            INSERT INTO issue_close_warnings (
                course_id, issue_number, issue_title, closed_by, closed_at, 
                warning_type, warning_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            COURSE_ID,
            issue_number,
            issue_title,
            closed_by,
            closed_at,
            "no_pr_associated",
            f"Issue #{issue_number} 被直接关闭，未关联PR。仓库: {repo_full_name}"
        ))
        
        return {
            "success": True,
            "warning_created": True,
            "message": f"Issue #{issue_number} 未关联PR被关闭，已生成警告记录"
        }
    
    return {"success": True, "message": "Issue body包含PR引用，无需处理"}


@router.get("/api/workflow/warnings")
async def get_warnings(
    resolved: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    """获取Issue关闭警告记录列表"""
    _require_teacher(authorization)
    
    offset = (page - 1) * page_size
    
    with db() as conn:
        cur = conn.cursor()
        
        if resolved is not None:
            cur.execute("""
                SELECT * FROM issue_close_warnings 
                WHERE course_id = %s AND resolved = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (COURSE_ID, resolved, page_size, offset))
        else:
            cur.execute("""
                SELECT * FROM issue_close_warnings 
                WHERE course_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (COURSE_ID, page_size, offset))
        
        warnings = cur.fetchall()
        
        # 获取总数
        if resolved is not None:
            cur.execute(
                "SELECT COUNT(*) as total FROM issue_close_warnings WHERE course_id = %s AND resolved = %s",
                (COURSE_ID, resolved)
            )
        else:
            cur.execute(
                "SELECT COUNT(*) as total FROM issue_close_warnings WHERE course_id = %s",
                (COURSE_ID,)
            )
        
        total = cur.fetchone()["total"]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "warnings": [
            WarningRecord(
                id=w["id"],
                course_id=w["course_id"],
                issue_number=w["issue_number"],
                issue_title=w["issue_title"],
                closed_by=w["closed_by"],
                closed_at=w["closed_at"],
                warning_type=w["warning_type"],
                warning_message=w["warning_message"],
                resolved=bool(w["resolved"]),
                created_at=str(w["created_at"])
            )
            for w in warnings
        ]
    }


@router.put("/api/workflow/warnings/{warning_id}/resolve")
async def resolve_warning(
    warning_id: int,
    authorization: Optional[str] = Header(None)
):
    """标记警告记录为已处理"""
    _require_teacher(authorization)
    
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE issue_close_warnings 
            SET resolved = 1, resolved_at = NOW() 
            WHERE id = %s AND course_id = %s
        """, (warning_id, COURSE_ID))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="警告记录不存在")
    
    return {"success": True, "message": "警告记录已标记为已处理"}


@router.delete("/api/workflow/warnings/{warning_id}")
async def delete_warning(
    warning_id: int,
    authorization: Optional[str] = Header(None)
):
    """删除警告记录"""
    _require_teacher(authorization)
    
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM issue_close_warnings WHERE id = %s AND course_id = %s",
            (warning_id, COURSE_ID)
        )
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="警告记录不存在")
    
    return {"success": True, "message": "警告记录已删除"}