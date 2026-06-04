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
    """仓库协作者权限管理页面"""
    return rx.html(render())


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
            <button onclick="logout()">退出登录</button>
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
            <button class="tab active" onclick="showTab('manage')">权限操作</button>
            <button class="tab" onclick="showTab('audit')">操作记录</button>
            <button class="tab" onclick="showTab('roles')">角色说明</button>
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
                <button class="btn btn-primary" onclick="addCollaborator()">添加协作者</button>
            </div>

            <!-- 协作者列表 -->
            <div class="card">
                <div class="card-title">协作者列表</div>
                <div class="search-row">
                    <input type="text" id="list_team_name" placeholder="团队名称" value="robotics-course-2024">
                    <button class="btn btn-primary" onclick="loadCollaborators()">查询</button>
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
                <button class="btn btn-danger" onclick="removeCollaborator()">移除协作者</button>
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
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
                    <div style="background: #fef2f2; padding: 16px; border-radius: 10px; border-left: 4px solid #dc2626;">
                        <h3 style="color: #dc2626; margin-bottom: 8px; font-size: 15px;">👑 Admin</h3>
                        <p style="color: #4b5563; font-size: 13px;">完全仓库权限，包括删除仓库、管理团队、设置保护分支等</p>
                    </div>
                    <div style="background: #fffbeb; padding: 16px; border-radius: 10px; border-left: 4px solid #f59e0b;">
                        <h3 style="color: #f59e0b; margin-bottom: 8px; font-size: 15px;">✏️ Write</h3>
                        <p style="color: #4b5563; font-size: 13px;">推送代码、创建分支、发起 PR、管理 Issues</p>
                    </div>
                    <div style="background: #eff6ff; padding: 16px; border-radius: 10px; border-left: 4px solid #2563eb;">
                        <h3 style="color: #2563eb; margin-bottom: 8px; font-size: 15px;">🏷️ Triage</h3>
                        <p style="color: #4b5563; font-size: 13px;">管理 Issues 和 PR，添加标签，无法推送代码</p>
                    </div>
                    <div style="background: #f3f4f6; padding: 16px; border-radius: 10px; border-left: 4px solid #6b7280;">
                        <h3 style="color: #6b7280; margin-bottom: 8px; font-size: 15px;">📖 Read</h3>
                        <p style="color: #4b5563; font-size: 13px;">仅查看仓库内容，无法修改或提交</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '/api';

        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('[id$="-tab"]').forEach(c => c.style.display = 'none');
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').style.display = 'block';
            if (tabName === 'audit') loadAuditLogs();
        }

        async function addCollaborator() {
            const team_name = document.getElementById('team_name').value.trim();
            const user_id = document.getElementById('user_id').value.trim();
            const role = document.getElementById('role').value;

            if (!team_name || !user_id) {
                showToast('请填写团队名称和用户 ID', 'error');
                return;
            }

            const button = event.target;
            button.disabled = true;
            button.innerHTML = '添加中...';

            try {
                const res = await fetch(`${API_BASE}/devops/collaborators?team_name=${encodeURIComponent(team_name)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_id, role })
                });

                if (res.ok) {
                    showToast(`✓ 已通过团队 ${team_name} 添加协作者 ${user_id}，角色：${role}`);
                    document.getElementById('user_id').value = '';
                    document.getElementById('list_team_name').value = team_name;
                    loadAuditLogs();
                    loadCollaborators();
                } else {
                    const errData = await res.json();
                    showToast(errData.detail || '添加失败', 'error');
                }
            } catch (err) {
                console.error('API call error:', err);
                showToast('网络请求失败', 'error');
            } finally {
                button.disabled = false;
                button.innerHTML = '添加协作者';
            }
        }

        async function loadCollaborators() {
            const team_name = document.getElementById('list_team_name').value.trim();
            if (!team_name) {
                showToast('请填写团队名称', 'error');
                return;
            }

            const list = document.getElementById('collaborator-list');
            list.innerHTML = '<div class="empty-state">查询中...</div>';

            const button = document.querySelector('.search-row .btn-primary');
            if (button) {
                button.disabled = true;
                button.innerHTML = '查询中...';
            }

            try {
                const res = await fetch(`${API_BASE}/devops/collaborators/list?team_name=${encodeURIComponent(team_name)}`);
                if (res.ok) {
                    const data = await res.json();
                    renderCollaborators(data);
                    document.getElementById('team_name').value = team_name;
                    document.getElementById('remove_team_name').value = team_name;
                } else {
                    renderCollaborators([]);
                }
            } catch (err) {
                console.error('API call error:', err);
                renderCollaborators([]);
            } finally {
                if (button) {
                    button.disabled = false;
                    button.innerHTML = '查询';
                }
            }
        }

        function renderCollaborators(data) {
            const list = document.getElementById('collaborator-list');
            if (!data || data.length === 0) {
                list.innerHTML = '<div class="empty-state">暂无协作者</div>';
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
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(item => `
                                <tr>
                                    <td>${item.user_id}</td>
                                    <td><span class="role-tag" style="background: ${getRoleColor(item.role)}">${item.role}</span></td>
                                    <td>${item.team_name || ''}</td>
                                    <td>${item.added_at || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        async function removeCollaborator() {
            const team_name = document.getElementById('remove_team_name').value.trim();
            const user_id = document.getElementById('remove_user_id').value.trim();

            if (!team_name || !user_id) {
                showToast('请填写团队名称和用户 ID', 'error');
                return;
            }

            if (!confirm(`确定要从团队 ${team_name} 中移除协作者 ${user_id} 吗？`)) {
                return;
            }

            const button = event.target;
            button.disabled = true;
            button.innerHTML = '移除中...';

            try {
                const res = await fetch(`${API_BASE}/devops/collaborators/${user_id}?team_name=${encodeURIComponent(team_name)}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast(`✓ 已从团队 ${team_name} 移除协作者 ${user_id}`);
                    document.getElementById('remove_user_id').value = '';
                    document.getElementById('list_team_name').value = team_name;
                    loadAuditLogs();
                    loadCollaborators();
                } else {
                    const errData = await res.json();
                    showToast(errData.detail || '移除失败', 'error');
                }
            } catch (err) {
                console.error('API call error:', err);
                showToast('网络请求失败', 'error');
            } finally {
                button.disabled = false;
                button.innerHTML = '移除协作者';
            }
        }

        async function loadAuditLogs() {
            const list = document.getElementById('audit-list');
            list.innerHTML = '<div class="empty-state">加载中...</div>';

            try {
                const res = await fetch(`${API_BASE}/devops/collaborators/audit`);
                if (res.ok) {
                    const data = await res.json();
                    renderAuditLogs(data);
                } else {
                    renderAuditLogs([]);
                }
            } catch (err) {
                console.error('API call error:', err);
                renderAuditLogs([]);
            }
        }

        function renderAuditLogs(data) {
            const list = document.getElementById('audit-list');
            if (!data || data.length === 0) {
                list.innerHTML = '<div class="empty-state">暂无操作记录</div>';
                return;
            }

            const actionText = {
                'collaborator_add': '添加协作者',
                'collaborator_remove': '移除协作者',
                'collaborator_role_update': '更新角色权限'
            };

            list.innerHTML = data.map(item => {
                const detail = typeof item.detail_json === 'string' ? JSON.parse(item.detail_json) : item.detail_json;
                return `
                    <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #6366f1;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: 600; color: #1f2937;">${actionText[item.action] || item.action}</span>
                            <span style="font-size: 12px; color: #6b7280;">${item.action_at || '未知时间'}</span>
                        </div>
                        <div style="font-size: 13px; color: #6b7280;">
                            <strong>目标:</strong> ${item.target_type || ''} #${item.target_id || ''}<br>
                            <strong>详情:</strong> 团队=${detail.team_name || ''}, 用户=${detail.user_id || ''}, 角色=${detail.role || ''}
                        </div>
                    </div>
                `;
            }).join('');
        }

        function logout() {
            showToast('已退出登录', 'success');
        }

        loadAuditLogs();
    </script>
</body>
</html>
"""
