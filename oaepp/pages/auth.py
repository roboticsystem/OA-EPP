"""
F-D-005 仓库协作者权限管理
feat(F-D-005) 仓库协作者权限管理
路由: /auth
"""
import json
from datetime import datetime

try:
    import reflex as rx
except Exception:
    rx = None

from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


# ==================== 角色权限定义 ====================

ROLE_PERMISSIONS = {
    "Admin": ["push", "pull", "manage", "delete", "admin"],
    "Write": ["push", "pull", "manage"],
    "Triage": ["pull", "triage"],
    "Read": ["pull"]
}

VALID_ROLES = list(ROLE_PERMISSIONS.keys())


# ==================== 模拟数据存储 ====================

collaborators_db = {}
audit_logs_db = []


def _log_audit(action: str, target_type: str, target_id: str, detail: dict):
    """记录审计日志"""
    audit_logs_db.append({
        "id": len(audit_logs_db) + 1,
        "actor_user_id": "teacher",
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "detail_json": json.dumps(detail),
        "action_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# ==================== FastAPI 路由 ====================

router = APIRouter()


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "Read"


@router.post("/api/devops/collaborators")
def add_collaborator(
    req: AddMemberRequest,
    team_name: str = Query(...)
):
    """通过团队添加协作者"""
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"无效角色，必须是 {VALID_ROLES} 之一")

    key = f"{team_name}:{req.user_id}"
    collaborators_db[key] = {
        "user_id": req.user_id,
        "role": req.role,
        "team_name": team_name,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    _log_audit("collaborator_add", "collaborators", req.user_id, {
        "team_name": team_name,
        "user_id": req.user_id,
        "role": req.role
    })

    return {"ok": True, "message": f"已通过团队 {team_name} 添加协作者 {req.user_id}，角色：{req.role}"}


@router.get("/api/devops/collaborators/list")
def get_collaborators(team_name: str = Query(...)):
    """获取团队协作者列表"""
    result = []
    for key, data in collaborators_db.items():
        if data["team_name"] == team_name:
            result.append(data)
    result.sort(key=lambda x: x["added_at"], reverse=True)
    return result


@router.delete("/api/devops/collaborators/{user_id}")
def remove_collaborator(user_id: str, team_name: str = Query(...)):
    """从团队中移除协作者"""
    key = f"{team_name}:{user_id}"
    if key in collaborators_db:
        del collaborators_db[key]

        _log_audit("collaborator_remove", "collaborators", user_id, {
            "team_name": team_name,
            "user_id": user_id
        })

        return {"ok": True, "message": f"已从团队 {team_name} 移除协作者 {user_id}"}
    else:
        raise HTTPException(status_code=404, detail="协作者不存在")


@router.get("/api/devops/collaborators/audit")
def get_audit_logs(target_type: str = Query(None), target_id: str = Query(None)):
    """获取权限变更操作记录"""
    result = audit_logs_db.copy()
    if target_type:
        result = [r for r in result if r["target_type"] == target_type]
    if target_id:
        result = [r for r in result if r["target_id"] == target_id]
    result.sort(key=lambda x: x["action_at"], reverse=True)
    return result[:100]


@router.get("/api/devops/roles")
def get_valid_roles():
    """获取有效的角色权限列表"""
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


# ==================== 页面渲染 ====================

def auth_page():
    """仓库协作者权限管理页面（Reflex 组件）"""
    return rx.html(render())


@router.get("/auth")
def auth_page_html():
    """仓库协作者权限管理页面（直接返回 HTML）"""
    return HTMLResponse(content=render())


def render():
    """返回完整的仓库协作者权限管理页面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F-D-005 仓库协作者权限管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(180deg, #5b21b6 0%, #7c3aed 50%, #9333ea 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        
        /* 顶部用户信息 */
        .user-bar {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }
        .user-bar span {
            color: white;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .user-bar button {
            padding: 6px 16px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .user-bar button:hover {
            background: rgba(255,255,255,0.3);
        }
        
        /* 卡片样式 */
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            padding: 24px;
            margin-bottom: 20px;
        }
        
        /* 头部卡片 */
        .header-card {
            text-align: center;
        }
        .header-card h1 {
            font-size: 22px;
            color: #1f2937;
            margin-bottom: 8px;
            font-weight: 600;
        }
        .header-card p {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 16px;
        }
        .role-badges {
            display: flex;
            justify-content: center;
            gap: 10px;
        }
        .role-badge {
            padding: 6px 16px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 600;
            color: white;
        }
        .role-admin { background: #dc2626; }
        .role-write { background: #f59e0b; }
        .role-triage { background: #2563eb; }
        .role-read { background: #6b7280; }
        
        /* 统计卡片 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }
        .stat-card {
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #6366f1;
            margin-bottom: 4px;
        }
        .stat-label {
            font-size: 13px;
            color: #6b7280;
        }
        
        /* 功能特性 */
        .feature-list {
            list-style: none;
            padding: 0;
        }
        .feature-list li {
            padding: 10px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #f3f4f6;
        }
        .feature-list li:last-child {
            border-bottom: none;
        }
        .feature-list .check {
            width: 20px;
            height: 20px;
            background: #10b981;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 11px;
            flex-shrink: 0;
        }
        .feature-list span {
            font-size: 14px;
            color: #374151;
        }
        
        /* 标签页 */
        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab.active {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
        }
        .tab:not(.active) {
            background: white;
            color: #6b7280;
        }
        .tab:not(.active):hover {
            background: #f3f4f6;
        }
        
        /* 表单样式 */
        .form-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }
        .form-row-2 {
            grid-template-columns: repeat(2, 1fr);
        }
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: #374151;
            margin-bottom: 6px;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 13px;
            transition: border-color 0.2s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #6366f1;
        }
        
        /* 按钮 */
        .btn {
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-danger:hover {
            background: #dc2626;
        }
        
        /* 表格 */
        .table-container {
            margin-top: 16px;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        .table th {
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            color: #374151;
        }
        .table td {
            padding: 12px;
            font-size: 13px;
            color: #4b5563;
            border-bottom: 1px solid #f3f4f6;
        }
        .role-tag {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: white;
        }
        
        /* 空状态 */
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #9ca3af;
            font-size: 14px;
        }
        
        /* Toast 提示 */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 14px 24px;
            border-radius: 10px;
            color: white;
            font-size: 14px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .toast.success {
            background: linear-gradient(135deg, #10b981, #059669);
        }
        .toast.error {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        @keyframes slideIn {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* 卡片标题 */
        .card-title {
            font-size: 15px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 16px;
        }
        
        /* 查询区域 */
        .search-row {
            display: flex;
            gap: 12px;
            align-items: flex-end;
            margin-bottom: 16px;
        }
        .search-row input {
            flex: 1;
            max-width: 300px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 用户信息栏 -->
        <div class="user-bar">
            <span>👤 教师已登录</span>
            <button id="btn-logout">退出登录</button>
        </div>

        <!-- 头部卡片 -->
        <div class="card header-card">
            <h1>F-D-005 仓库协作者权限管理</h1>
            <p>通过 GitHub Team 统一管理课程组成员权限，禁止个人直接授权，确保权限管理规范化</p>
            <div class="role-badges">
                <span class="role-badge role-admin">Admin</span>
                <span class="role-badge role-write">Write</span>
                <span class="role-badge role-triage">Triage</span>
                <span class="role-badge role-read">Read</span>
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">4</div>
                <div class="stat-label">角色类型</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">Team</div>
                <div class="stat-label">管理方式</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">✓</div>
                <div class="stat-label">操作审计</div>
            </div>
        </div>

        <!-- 功能特性 -->
        <div class="card">
            <div class="card-title">功能特性</div>
            <ul class="feature-list">
                <li><span class="check">✓</span><span>通过 GitHub Team 而非个人直接授权管理权限</span></li>
                <li><span class="check">✓</span><span>通过 GitHub Team 而非个人直接授权管理权限</span></li>
                <li><span class="check">✓</span><span>角色分配符合 Admin/Write/Triage/Read 规范</span></li>
                <li><span class="check">✓</span><span>权限变更有操作记录（audit_logs）</span></li>
                <li><span class="check">✓</span><span>禁止个人直接授权，确保权限管理规范化</span></li>
            </ul>
        </div>

        <!-- 标签页切换 -->
        <div class="tabs">
            <button class="tab active" id="tab-manage">权限操作</button>
            <button class="tab" id="tab-audit">操作记录</button>
            <button class="tab" id="tab-roles">角色说明</button>
        </div>

        <!-- 权限操作标签页 -->
        <div id="manage-tab">
            <!-- 添加协作者 -->
            <div class="card">
                <div class="card-title">添加协作者</div>
                <div class="form-row">
                    <div class="form-group">
                        <label>团队名称 *</label>
                        <input type="text" id="team_name" placeholder="团队名称" value="robotics-course-2024">
                    </div>
                    <div class="form-group">
                        <label>用户 ID *</label>
                        <input type="text" id="user_id" placeholder="GitHub 用户名或学号">
                    </div>
                    <div class="form-group">
                        <label>角色权限</label>
                        <select id="role">
                            <option value="Admin">Admin - 管理员</option>
                            <option value="Write">Write - 写入</option>
                            <option value="Triage">Triage - 分类</option>
                            <option value="Read" selected>Read - 只读</option>
                        </select>
                    </div>
                </div>
                <button class="btn btn-primary" id="btn-add-collaborator">添加协作者</button>
            </div>

            <!-- 协作者列表 -->
            <div class="card">
                <div class="card-title">协作者列表</div>
                <div class="search-row">
                    <input type="text" id="list_team_name" placeholder="团队名称" value="robotics-course-2024">
                    <button class="btn btn-primary" id="btn-load-collaborators">查询</button>
                </div>
                <div id="collaborator-list">
                    <div class="empty-state">点击查询查看协作者列表</div>
                </div>
            </div>

            <!-- 移除协作者 -->
            <div class="card">
                <div class="card-title">移除协作者</div>
                <div class="form-row form-row-2">
                    <div class="form-group">
                        <label>团队名称 *</label>
                        <input type="text" id="remove_team_name" placeholder="团队名称" value="robotics-course-2024">
                    </div>
                    <div class="form-group">
                        <label>用户 ID *</label>
                        <input type="text" id="remove_user_id" placeholder="要移除的用户 ID">
                    </div>
                </div>
                <button class="btn btn-danger" id="btn-remove-collaborator">移除协作者</button>
            </div>
        </div>

        <!-- 操作记录标签页 -->
        <div id="audit-tab" style="display: none;">
            <div class="card">
                <div class="card-title">操作审计日志</div>
                <div id="audit-list">
                    <div class="empty-state">加载中...</div>
                </div>
            </div>
        </div>

        <!-- 角色说明标签页 -->
        <div id="roles-tab" style="display: none;">
            <div class="card">
                <div class="card-title">角色权限说明</div>
                <div style="margin-bottom: 24px;">
                    <p style="color: #6b7280; font-size: 14px; margin-bottom: 16px;">权限通过 GitHub Team 统一管理，禁止个人直接授权，确保权限管理规范化。</p>
                    
                    <!-- 角色卡片 -->
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px;">
                        <div style="background: #fef2f2; padding: 20px; border-radius: 12px; border-left: 4px solid #dc2626;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                <span style="font-size: 24px;">👑</span>
                                <h3 style="color: #dc2626; font-size: 16px; font-weight: 600;">Admin</h3>
                            </div>
                            <p style="color: #4b5563; font-size: 13px; margin-bottom: 12px;">完全仓库权限，包括删除仓库、管理团队、设置保护分支等</p>
                            <div style="background: rgba(220, 38, 38, 0.1); padding: 12px; border-radius: 8px;">
                                <div style="font-size: 12px; color: #dc2626; font-weight: 600; margin-bottom: 8px;">权限列表：</div>
                                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                                    <span style="background: rgba(220, 38, 38, 0.2); color: #dc2626; padding: 4px 8px; border-radius: 4px; font-size: 11px;">push</span>
                                    <span style="background: rgba(220, 38, 38, 0.2); color: #dc2626; padding: 4px 8px; border-radius: 4px; font-size: 11px;">pull</span>
                                    <span style="background: rgba(220, 38, 38, 0.2); color: #dc2626; padding: 4px 8px; border-radius: 4px; font-size: 11px;">manage</span>
                                    <span style="background: rgba(220, 38, 38, 0.2); color: #dc2626; padding: 4px 8px; border-radius: 4px; font-size: 11px;">delete</span>
                                    <span style="background: rgba(220, 38, 38, 0.2); color: #dc2626; padding: 4px 8px; border-radius: 4px; font-size: 11px;">admin</span>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background: #fffbeb; padding: 20px; border-radius: 12px; border-left: 4px solid #f59e0b;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                <span style="font-size: 24px;">✏️</span>
                                <h3 style="color: #f59e0b; font-size: 16px; font-weight: 600;">Write</h3>
                            </div>
                            <p style="color: #4b5563; font-size: 13px; margin-bottom: 12px;">推送代码、创建分支、发起 PR、管理 Issues</p>
                            <div style="background: rgba(245, 158, 11, 0.1); padding: 12px; border-radius: 8px;">
                                <div style="font-size: 12px; color: #f59e0b; font-weight: 600; margin-bottom: 8px;">权限列表：</div>
                                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                                    <span style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 4px 8px; border-radius: 4px; font-size: 11px;">push</span>
                                    <span style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 4px 8px; border-radius: 4px; font-size: 11px;">pull</span>
                                    <span style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 4px 8px; border-radius: 4px; font-size: 11px;">manage</span>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background: #eff6ff; padding: 20px; border-radius: 12px; border-left: 4px solid #2563eb;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                <span style="font-size: 24px;">🏷️</span>
                                <h3 style="color: #2563eb; font-size: 16px; font-weight: 600;">Triage</h3>
                            </div>
                            <p style="color: #4b5563; font-size: 13px; margin-bottom: 12px;">管理 Issues 和 PR，添加标签，无法推送代码</p>
                            <div style="background: rgba(37, 99, 235, 0.1); padding: 12px; border-radius: 8px;">
                                <div style="font-size: 12px; color: #2563eb; font-weight: 600; margin-bottom: 8px;">权限列表：</div>
                                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                                    <span style="background: rgba(37, 99, 235, 0.2); color: #2563eb; padding: 4px 8px; border-radius: 4px; font-size: 11px;">pull</span>
                                    <span style="background: rgba(37, 99, 235, 0.2); color: #2563eb; padding: 4px 8px; border-radius: 4px; font-size: 11px;">triage</span>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background: #f3f4f6; padding: 20px; border-radius: 12px; border-left: 4px solid #6b7280;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                <span style="font-size: 24px;">📖</span>
                                <h3 style="color: #6b7280; font-size: 16px; font-weight: 600;">Read</h3>
                            </div>
                            <p style="color: #4b5563; font-size: 13px; margin-bottom: 12px;">仅查看仓库内容，无法修改或提交</p>
                            <div style="background: rgba(107, 114, 128, 0.1); padding: 12px; border-radius: 8px;">
                                <div style="font-size: 12px; color: #6b7280; font-weight: 600; margin-bottom: 8px;">权限列表：</div>
                                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                                    <span style="background: rgba(107, 114, 128, 0.2); color: #6b7280; padding: 4px 8px; border-radius: 4px; font-size: 11px;">pull</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 权限对比表格 -->
                    <div style="background: #f9fafb; padding: 16px; border-radius: 12px;">
                        <h4 style="font-size: 14px; font-weight: 600; color: #1f2937; margin-bottom: 12px;">权限对比</h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                            <thead>
                                <tr style="background: #e5e7eb;">
                                    <th style="padding: 10px; text-align: left; font-weight: 600; color: #374151;">权限</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #374151;">Admin</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #374151;">Write</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #374151;">Triage</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #374151;">Read</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 10px; color: #4b5563;">查看仓库</td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 10px; color: #4b5563;">推送代码</td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 10px; color: #4b5563;">创建分支</td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 10px; color: #4b5563;">管理 Issues</td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 10px; color: #4b5563;">管理团队</td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; color: #4b5563;">删除仓库</td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #10b981; font-weight: 600;">✓</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                    <td style="padding: 10px; text-align: center;"><span style="color: #d1d5db;">-</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ── 虚拟前端数据存储 ──
        const collaboratorsData = {};  // { "team_name:user_id": { user_id, role, team_name, added_at } }
        const auditLogsData = [];      // 审计日志数组
        let auditIdCounter = 1;

        // 初始化一些示例数据
        const initTeamName = 'robotics-course-2024';
        collaboratorsData[`${initTeamName}:teacher-zhang`] = {
            user_id: 'teacher-zhang',
            role: 'Admin',
            team_name: initTeamName,
            added_at: new Date(Date.now() - 3600000).toISOString().slice(0, 19).replace('T', ' ')
        };
        collaboratorsData[`${initTeamName}:student-li`] = {
            user_id: 'student-li',
            role: 'Write',
            team_name: initTeamName,
            added_at: new Date(Date.now() - 1800000).toISOString().slice(0, 19).replace('T', ' ')
        };
        collaboratorsData[`${initTeamName}:student-wang`] = {
            user_id: 'student-wang',
            role: 'Read',
            team_name: initTeamName,
            added_at: new Date(Date.now() - 900000).toISOString().slice(0, 19).replace('T', ' ')
        };

        // 初始化审计日志
        auditLogsData.push(
            {
                id: auditIdCounter++,
                actor_user_id: 'teacher',
                action: 'collaborator_add',
                target_type: 'collaborators',
                target_id: 'teacher-zhang',
                detail_json: JSON.stringify({ team_name: initTeamName, user_id: 'teacher-zhang', role: 'Admin' }),
                action_at: new Date(Date.now() - 3600000).toISOString().slice(0, 19).replace('T', ' ')
            },
            {
                id: auditIdCounter++,
                actor_user_id: 'teacher',
                action: 'collaborator_add',
                target_type: 'collaborators',
                target_id: 'student-li',
                detail_json: JSON.stringify({ team_name: initTeamName, user_id: 'student-li', role: 'Write' }),
                action_at: new Date(Date.now() - 1800000).toISOString().slice(0, 19).replace('T', ' ')
            },
            {
                id: auditIdCounter++,
                actor_user_id: 'teacher',
                action: 'collaborator_add',
                target_type: 'collaborators',
                target_id: 'student-wang',
                detail_json: JSON.stringify({ team_name: initTeamName, user_id: 'student-wang', role: 'Read' }),
                action_at: new Date(Date.now() - 900000).toISOString().slice(0, 19).replace('T', ' ')
            }
        );

        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        function _logAudit(action, targetType, targetId, detail) {
            auditLogsData.push({
                id: auditIdCounter++,
                actor_user_id: 'teacher',
                action: action,
                target_type: targetType,
                target_id: targetId,
                detail_json: JSON.stringify(detail),
                action_at: new Date().toISOString().slice(0, 19).replace('T', ' ')
            });
        }

        function showTab(tabName, clickedTab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('[id$="-tab"]').forEach(c => c.style.display = 'none');
            clickedTab.classList.add('active');
            document.getElementById(tabName + '-tab').style.display = 'block';
            if (tabName === 'audit') renderAuditLogs(auditLogsData);
        }

        function addCollaborator() {
            const team_name = document.getElementById('team_name').value.trim();
            const user_id = document.getElementById('user_id').value.trim();
            const role = document.getElementById('role').value;

            if (!team_name || !user_id) {
                showToast('请填写团队名称和用户 ID', 'error');
                return;
            }

            const validRoles = ['Admin', 'Write', 'Triage', 'Read'];
            if (!validRoles.includes(role)) {
                showToast(`无效角色，必须是 ${validRoles.join('/')} 之一`, 'error');
                return;
            }

            const key = `${team_name}:${user_id}`;
            const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
            const isUpdate = key in collaboratorsData;

            collaboratorsData[key] = {
                user_id: user_id,
                role: role,
                team_name: team_name,
                added_at: now
            };

            _logAudit('collaborator_add', 'collaborators', user_id, {
                team_name: team_name,
                user_id: user_id,
                role: role
            });

            showToast(`✓ 已通过团队 ${team_name} ${isUpdate ? '更新' : '添加'}协作者 ${user_id}，角色：${role}`);
            document.getElementById('user_id').value = '';
            document.getElementById('list_team_name').value = team_name;
            renderAuditLogs(auditLogsData);
            loadCollaborators();
        }

        function loadCollaborators() {
            const team_name = document.getElementById('list_team_name').value.trim();
            if (!team_name) {
                showToast('请填写团队名称', 'error');
                return;
            }

            // 从虚拟数据存储中查询
            const result = [];
            for (const key in collaboratorsData) {
                const data = collaboratorsData[key];
                if (data.team_name === team_name) {
                    result.push(data);
                }
            }
            result.sort((a, b) => (b.added_at || '').localeCompare(a.added_at || ''));

            renderCollaborators(result);
            document.getElementById('team_name').value = team_name;
            document.getElementById('remove_team_name').value = team_name;
        }

        function renderCollaborators(data) {
            const list = document.getElementById('collaborator-list');
            if (!data || data.length === 0) {
                list.innerHTML = `
                    <div class="empty-state">
                        <div style="font-size: 48px; margin-bottom: 16px;">👥</div>
                        <div>暂无协作者</div>
                        <div style="font-size: 12px; color: #9ca3af; margin-top: 8px;">在上方添加协作者</div>
                    </div>
                `;
                return;
            }

            const getRoleColor = (role) => {
                const colors = { 'Admin': '#dc2626', 'Write': '#f59e0b', 'Triage': '#2563eb', 'Read': '#6b7280' };
                return colors[role] || '#6b7280';
            };

            list.innerHTML = `
                <div class="table-container">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>用户 ID</th>
                                <th>角色权限</th>
                                <th>团队名称</th>
                                <th>添加时间</th>
                                <th style="width: 120px;">操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(item => `
                                <tr>
                                    <td style="font-weight: 500; color: #374151;">${item.user_id}</td>
                                    <td>
                                        <span class="role-tag" style="background: ${getRoleColor(item.role)}">${item.role}</span>
                                    </td>
                                    <td>${item.team_name || ''}</td>
                                    <td style="color: #6b7280;">${item.added_at || '-'}</td>
                                    <td>
                                        <div style="display: flex; gap: 6px;">
                                            <button 
                                                onclick="editRole('${item.user_id}', '${item.team_name}', '${item.role}')"
                                                style="padding: 4px 10px; background: #f3f4f6; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; color: #374151;">
                                                编辑
                                            </button>
                                            <button 
                                                onclick="quickRemove('${item.user_id}', '${item.team_name}')"
                                                style="padding: 4px 10px; background: #fee2e2; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; color: #dc2626;">
                                                删除
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    <div style="margin-top: 12px; font-size: 13px; color: #6b7280;">
                        共 ${data.length} 位协作者
                    </div>
                </div>
            `;
        }

        function removeCollaborator() {
            const team_name = document.getElementById('remove_team_name').value.trim();
            const user_id = document.getElementById('remove_user_id').value.trim();

            if (!team_name || !user_id) {
                showToast('请填写团队名称和用户 ID', 'error');
                return;
            }

            if (!confirm(`确定要从团队 ${team_name} 中移除协作者 ${user_id} 吗？`)) {
                return;
            }

            const key = `${team_name}:${user_id}`;
            if (key in collaboratorsData) {
                delete collaboratorsData[key];

                _logAudit('collaborator_remove', 'collaborators', user_id, {
                    team_name: team_name,
                    user_id: user_id
                });

                showToast(`✓ 已从团队 ${team_name} 移除协作者 ${user_id}`);
                document.getElementById('remove_user_id').value = '';
                document.getElementById('list_team_name').value = team_name;
                renderAuditLogs(auditLogsData);
                loadCollaborators();
            } else {
                showToast('协作者不存在', 'error');
            }
        }

        // 编辑角色权限
        window.editRole = function(user_id, team_name, current_role) {
            const roles = ['Admin', 'Write', 'Triage', 'Read'];
            const roleOptions = roles.filter(r => r !== current_role).map(r => `<option value="${r}">${r}</option>`).join('');
            
            const newRole = prompt(`为 ${user_id} 选择新角色（当前：${current_role}）:\n\n${roles.join('\n')}`, current_role);
            
            if (!newRole || !roles.includes(newRole)) {
                if (newRole !== null) showToast('无效角色', 'error');
                return;
            }

            if (newRole === current_role) {
                showToast('角色未变化', 'error');
                return;
            }

            const key = `${team_name}:${user_id}`;
            if (key in collaboratorsData) {
                collaboratorsData[key].role = newRole;
                collaboratorsData[key].added_at = new Date().toISOString().slice(0, 19).replace('T', ' ');

                _logAudit('collaborator_role_update', 'collaborators', user_id, {
                    team_name: team_name,
                    user_id: user_id,
                    role: newRole,
                    previous_role: current_role
                });

                showToast(`✓ 已将 ${user_id} 的角色更新为 ${newRole}`);
                renderAuditLogs(auditLogsData);
                loadCollaborators();
            }
        }

        // 快速删除
        window.quickRemove = function(user_id, team_name) {
            if (!confirm(`确定要从团队 ${team_name} 中移除协作者 ${user_id} 吗？`)) {
                return;
            }

            const key = `${team_name}:${user_id}`;
            if (key in collaboratorsData) {
                delete collaboratorsData[key];

                _logAudit('collaborator_remove', 'collaborators', user_id, {
                    team_name: team_name,
                    user_id: user_id
                });

                showToast(`✓ 已从团队 ${team_name} 移除协作者 ${user_id}`);
                renderAuditLogs(auditLogsData);
                loadCollaborators();
            } else {
                showToast('协作者不存在', 'error');
            }
        }

        function loadAuditLogs() {
            renderAuditLogs(auditLogsData);
        }

        function renderAuditLogs(data) {
            const list = document.getElementById('audit-list');
            if (!data || data.length === 0) {
                list.innerHTML = `
                    <div class="empty-state">
                        <div style="font-size: 48px; margin-bottom: 16px;">📋</div>
                        <div>暂无操作记录</div>
                        <div style="font-size: 12px; color: #9ca3af; margin-top: 8px;">操作协作者后会在此记录</div>
                    </div>
                `;
                return;
            }

            const actionConfig = {
                'collaborator_add': { text: '添加协作者', icon: '➕', color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)' },
                'collaborator_remove': { text: '移除协作者', icon: '➖', color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.1)' },
                'collaborator_role_update': { text: '更新角色权限', icon: '🔄', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)' }
            };

            function formatTime(dateStr) {
                if (!dateStr) return '未知时间';
                const now = new Date();
                const actionTime = new Date(dateStr.replace(' ', 'T'));
                const diffMs = now - actionTime;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMins / 60);
                const diffDays = Math.floor(diffHours / 24);

                if (diffMins < 1) return '刚刚';
                if (diffMins < 60) return `${diffMins}分钟前`;
                if (diffHours < 24) return `${diffHours}小时前`;
                return dateStr;
            }

            // 统计信息
            const stats = {
                total: data.length,
                add: data.filter(item => item.action === 'collaborator_add').length,
                remove: data.filter(item => item.action === 'collaborator_remove').length,
                update: data.filter(item => item.action === 'collaborator_role_update').length
            };

            list.innerHTML = `
                <!-- 统计卡片 -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
                    <div style="background: #f9fafb; padding: 14px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 20px; font-weight: 700; color: #6366f1;">${stats.total}</div>
                        <div style="font-size: 12px; color: #6b7280;">总记录</div>
                    </div>
                    <div style="background: rgba(16, 185, 129, 0.1); padding: 14px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 20px; font-weight: 700; color: #10b981;">${stats.add}</div>
                        <div style="font-size: 12px; color: #059669;">添加</div>
                    </div>
                    <div style="background: rgba(239, 68, 68, 0.1); padding: 14px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 20px; font-weight: 700; color: #ef4444;">${stats.remove}</div>
                        <div style="font-size: 12px; color: #dc2626;">移除</div>
                    </div>
                    <div style="background: rgba(245, 158, 11, 0.1); padding: 14px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 20px; font-weight: 700; color: #f59e0b;">${stats.update}</div>
                        <div style="font-size: 12px; color: #d97706;">更新</div>
                    </div>
                </div>

                <!-- 日志列表 -->
                <div style="max-height: 500px; overflow-y: auto; padding-right: 8px;">
                    ${data.map(item => {
                        const config = actionConfig[item.action] || { text: item.action, icon: '📝', color: '#6b7280', bgColor: '#f3f4f6' };
                        const detail = typeof item.detail_json === 'string' ? JSON.parse(item.detail_json) : item.detail_json;
                        return `
                            <div style="background: white; border: 1px solid #e5e7eb; padding: 16px; border-radius: 10px; margin-bottom: 12px;">
                                <div style="display: flex; align-items: flex-start; gap: 14px;">
                                    <div style="width: 40px; height: 40px; border-radius: 10px; background: ${config.bgColor}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                        <span style="font-size: 18px;">${config.icon}</span>
                                    </div>
                                    <div style="flex: 1;">
                                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                                            <div style="display: flex; align-items: center; gap: 8px;">
                                                <span style="font-weight: 600; color: ${config.color};">${config.text}</span>
                                                <span style="background: #f3f4f6; color: #6b7280; padding: 2px 8px; border-radius: 4px; font-size: 11px;">#${item.id}</span>
                                            </div>
                                            <span style="font-size: 12px; color: #9ca3af;">${formatTime(item.action_at)}</span>
                                        </div>
                                        <div style="font-size: 13px; color: #6b7280; margin-bottom: 8px;">
                                            <div style="display: flex; align-items: center; gap: 4px;">
                                                <span>👤</span>
                                                <span><strong style="color: #374151;">操作人:</strong> ${item.actor_user_id || '未知'}</span>
                                            </div>
                                        </div>
                                        <div style="background: #f9fafb; padding: 10px; border-radius: 6px;">
                                            <div style="font-size: 12px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                                                <div><span style="color: #6b7280;">团队:</span> <span style="font-weight: 500; color: #374151;">${detail.team_name || '-'}</span></div>
                                                <div><span style="color: #6b7280;">用户:</span> <span style="font-weight: 500; color: #374151;">${detail.user_id || '-'}</span></div>
                                                <div><span style="color: #6b7280;">角色:</span> <span style="font-weight: 500; color: #374151;">${detail.role || '-'}</span></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        function logout() {
            showToast('已退出登录', 'success');
        }

        // ── 事件绑定 ──
        document.addEventListener('DOMContentLoaded', function() {
            // 标签页切换
            document.getElementById('tab-manage').addEventListener('click', function() {
                showTab('manage', this);
            });
            document.getElementById('tab-audit').addEventListener('click', function() {
                showTab('audit', this);
            });
            document.getElementById('tab-roles').addEventListener('click', function() {
                showTab('roles', this);
            });

            // 按钮事件
            document.getElementById('btn-add-collaborator').addEventListener('click', addCollaborator);
            document.getElementById('btn-load-collaborators').addEventListener('click', loadCollaborators);
            document.getElementById('btn-remove-collaborator').addEventListener('click', removeCollaborator);
            document.getElementById('btn-logout').addEventListener('click', logout);

            // 初始化：自动加载协作者列表和审计日志
            loadCollaborators();
            renderAuditLogs(auditLogsData);
        });
    </script>
</body>
</html>
"""
