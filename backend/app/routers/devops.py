"""F-D-005 仓库协作者权限管理 API"""
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_connection
from app.auth_utils import verify_teacher_token

router = APIRouter()


def _require_admin(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "Read"


@router.post("/api/devops/collaborators")
def add_collaborator(
    req: AddMemberRequest,
    team_name: str = Query(...),
    authorization: Optional[str] = Header(None)
):
    """通过团队添加协作者（禁止个人直接授权）"""
    _require_admin(authorization)
    valid_roles = ["Admin", "Write", "Triage", "Read"]
    if req.role not in valid_roles:
        raise HTTPException(status_code=422, detail=f"无效角色，必须是 {valid_roles} 之一")
    
    _log_audit("collaborator_add", "collaborators", req.user_id, {
        "team_name": team_name,
        "user_id": req.user_id,
        "role": req.role
    })
    
    return {"ok": True, "message": f"已通过团队 {team_name} 添加协作者 {req.user_id}，角色：{req.role}"}


@router.get("/api/devops/collaborators/list")
def get_collaborators(
    team_name: str = Query(...),
    authorization: Optional[str] = Header(None)
):
    """获取团队协作者列表（从审计日志重建，排除已移除的用户）"""
    try:
        _require_admin(authorization)
        
        query = """
            SELECT 
                a.target_id as user_id, 
                MAX(a.action_at) as last_action_at,
                (SELECT detail_json FROM audit_logs 
                 WHERE target_id = a.target_id AND action = 'collaborator_add'
                   AND detail_json LIKE ?
                 ORDER BY action_at DESC LIMIT 1) as detail_json,
                (SELECT MAX(action_at) FROM audit_logs 
                 WHERE target_id = a.target_id AND action = 'collaborator_remove'
                   AND detail_json LIKE ?) as remove_time
            FROM audit_logs a
            WHERE target_type = 'collaborators' 
              AND action = 'collaborator_add'
              AND detail_json LIKE ?
            GROUP BY target_id
            ORDER BY last_action_at DESC
        """
        
        conn = get_connection()
        try:
            rows = conn.execute(query, (f'%{team_name}%', f'%{team_name}%', f'%{team_name}%')).fetchall()
        finally:
            conn.close()
        
        result = []
        for r in rows:
            row_dict = dict(r) if isinstance(r, dict) else {k: r[k] for k in r.keys()}
            
            remove_time = row_dict.pop("remove_time", None)
            if remove_time:
                add_time = row_dict.get("last_action_at", "")
                if add_time and remove_time > add_time:
                    continue
            
            try:
                detail = json.loads(row_dict["detail_json"]) if row_dict["detail_json"] else {}
                row_dict["role"] = detail.get("role", "Read")
                row_dict["team_name"] = detail.get("team_name", "")
            except:
                row_dict["role"] = "Read"
                row_dict["team_name"] = ""
            row_dict.pop("detail_json", None)
            result.append(row_dict)
        
        return result
    except Exception as e:
        import traceback
        print(f"[LIST ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.delete("/api/devops/collaborators/{user_id}")
def remove_collaborator(
    user_id: str,
    team_name: str = Query(...),
    authorization: Optional[str] = Header(None)
):
    """从团队中移除协作者"""
    _require_admin(authorization)
    
    _log_audit("collaborator_remove", "collaborators", user_id, {
        "team_name": team_name,
        "user_id": user_id
    })
    
    return {"ok": True, "message": f"已从团队 {team_name} 移除协作者 {user_id}"}


@router.get("/api/devops/collaborators/audit")
def get_audit_logs(
    target_type: str = Query(None),
    target_id: str = Query(None),
    authorization: Optional[str] = Header(None)
):
    """获取权限变更操作记录"""
    try:
        _require_admin(authorization)
        
        query = "SELECT id, actor_user_id, action, target_type, target_id, detail_json, action_at FROM audit_logs WHERE 1=1"
        params = []
        
        if target_type:
            query += " AND target_type=?"
            params.append(target_type)
        if target_id:
            query += " AND target_id=?"
            params.append(target_id)
        
        query += " ORDER BY action_at DESC LIMIT 100"
        
        conn = get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()
        
        result = []
        for r in rows:
            row_dict = dict(r) if isinstance(r, dict) else {k: r[k] for k in r.keys()}
            try:
                row_dict["detail_json"] = json.loads(row_dict["detail_json"]) if row_dict["detail_json"] else None
            except:
                row_dict["detail_json"] = row_dict["detail_json"]
            result.append(row_dict)
        
        return result
    except Exception as e:
        import traceback
        print(f"[AUDIT ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.get("/api/devops/roles")
def get_valid_roles(authorization: Optional[str] = Header(None)):
    """获取有效的角色权限列表"""
    _require_admin(authorization)
    
    return {
        "roles": [
            {"value": "Admin", "label": "管理员", "description": "完全仓库权限，包括删除仓库"},
            {"value": "Write", "label": "写入", "description": "推送代码、创建分支、发起PR"},
            {"value": "Triage", "label": "分类", "description": "管理Issues和PR，无法推送代码"},
            {"value": "Read", "label": "只读", "description": "仅查看仓库内容"}
        ],
        "team_based": True,
        "description": "权限通过 GitHub Team 统一管理，禁止个人直接授权"
    }


def _log_audit(action: str, target_type: str, target_id: str, detail: dict):
    """记录审计日志到 audit_logs 表"""
    try:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, detail_json, action_at) VALUES (?, ?, ?, ?, ?, ?)",
                (1, action, target_type, target_id, json.dumps(detail), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print(f"[WARNING] 审计日志记录失败: {e}")
