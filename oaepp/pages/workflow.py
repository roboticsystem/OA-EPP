"""
F-T-007 Issue-PR 关联规则管理页面

提供教师端工作流管理功能：
- Issue-PR 规则配置
- Issue 关闭时 PR 关联验证
- 警告记录管理
"""
try:
    import reflex as rx
except Exception:
    rx = None


def _html_fallback():
    return """
<div class="oaepp-workflow-page">
  <h1>工作流管理</h1>
  <div class="section">
    <h2>规则配置</h2>
    <div class="rule-item">
      <label><input type="checkbox" checked> 关闭 Issue 时必须关联 PR</label>
    </div>
    <div class="rule-item">
      <label><input type="checkbox"> 要求 PR 已合并才能关闭 Issue</label>
    </div>
  </div>
  <div class="section">
    <h2>警告记录</h2>
    <table>
      <tr><th>Issue</th><th>标题</th><th>关闭者</th><th>状态</th></tr>
      <tr><td>#123</td><td>修复登录问题</td><td>user1</td><td>待处理</td></tr>
    </table>
  </div>
</div>
"""


workflow_page = None
if rx is not None:
    from ..states.issue_pr import IssuePRState

    def workflow_page():
        """Issue-PR 关联规则管理页面（教师端）"""
        return rx.container(
            rx.vstack(
                # 页面标题
                rx.heading("工作流管理", size="5"),
                rx.text("Issue-PR 关联规则配置", color="gray"),
                
                # 规则配置卡片
                rx.box(
                    rx.vstack(
                        rx.heading("规则配置", size="4"),
                        
                        # 全局规则开关
                        rx.vstack(
                            rx.hstack(
                                rx.checkbox(
                                    default_checked=True,
                                    on_change=IssuePRState.set_global_rule(
                                        require_pr_on_close=True,
                                        require_merged_pr=False
                                    ),
                                ),
                                rx.text("关闭 Issue 时必须关联 PR", weight="medium"),
                                spacing="3",
                                align="center",
                            ),
                            rx.hstack(
                                rx.checkbox(
                                    default_checked=False,
                                    on_change=IssuePRState.set_global_rule(
                                        require_pr_on_close=True,
                                        require_merged_pr=True
                                    ),
                                ),
                                rx.text("要求 PR 已合并才能关闭 Issue", weight="medium"),
                                spacing="3",
                                align="center",
                            ),
                            spacing="4",
                            width="100%",
                        ),

                        # 课程规则配置（示例）
                        rx.divider(),
                        rx.heading("课程独立规则", size="4"),
                        rx.text("各课程可独立配置规则", color="gray"),
                        
                        # 规则状态提示
                        rx.box(
                            rx.text("当前全局规则状态："),
                            rx.text(f"  - 强制关联 PR: {'开启' if IssuePRState.require_pr_on_close else '关闭'}"),
                            rx.text(f"  - 要求合并: {'开启' if IssuePRState.require_merged_pr else '关闭'}"),
                            background="#f8fafc",
                            padding="12px",
                            border_radius="8px",
                            width="100%",
                        ),
                        
                        spacing="4",
                        width="100%",
                    ),
                    max_width="600px",
                    width="100%",
                    padding="24px",
                    border_radius="12px",
                    box_shadow="0 4px 12px rgba(0,0,0,0.05)",
                    background="white",
                ),

                # 警告记录卡片
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.heading("警告记录", size="4"),
                            rx.button(
                                "刷新",
                                on_click=IssuePRState.load_warnings(),
                                size="sm",
                            ),
                            justify="space-between",
                            align="center",
                            width="100%",
                        ),
                        
                        # 警告列表
                        rx.cond(
                            rx.len(IssuePRState.warnings) > 0,
                            rx.vstack(
                                rx.foreach(
                                    IssuePRState.warnings,
                                    lambda warning: rx.box(
                                        rx.hstack(
                                            rx.box(
                                                rx.text(f"Issue #{warning.issue_number}", weight="bold"),
                                                rx.text(warning.issue_title, color="gray"),
                                                spacing="1",
                                            ),
                                            rx.box(
                                                rx.text(f"关闭者: {warning.closed_by}"),
                                                rx.text(warning.warning_message, color="orange"),
                                                spacing="1",
                                            ),
                                            rx.button(
                                                "处理",
                                                on_click=IssuePRState.resolve_warning(warning.id),
                                                size="sm",
                                                variant="outline",
                                            ),
                                            justify="space-between",
                                            align="start",
                                            width="100%",
                                        ),
                                        padding="12px",
                                        border_radius="8px",
                                        background="#fffbeb" if not warning.resolved else "#ecfdf5",
                                        border="1px solid #fef3c7" if not warning.resolved else "1px solid #d1fae5",
                                        width="100%",
                                    ),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            rx.text("暂无警告记录", color="gray"),
                        ),
                        
                        spacing="4",
                        width="100%",
                    ),
                    max_width="800px",
                    width="100%",
                    padding="24px",
                    border_radius="12px",
                    box_shadow="0 4px 12px rgba(0,0,0,0.05)",
                    background="white",
                ),

                spacing="6",
                width="100%",
                padding="24px",
                max_width="900px",
                margin="0 auto",
            ),
            min_height="100vh",
            background="#f8fafc",
        )


def render():
    """Return HTML fallback string (used when Reflex not installed)."""
    return _html_fallback()