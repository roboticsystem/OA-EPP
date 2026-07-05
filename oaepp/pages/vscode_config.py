"""F-T-002 VS Code 扩展与 Copilot 提示词配置 — Reflex 页面

需求编号：F-T-002
模块定位：教师端管理页面，提供 VS Code 扩展配置与 Copilot 指令编辑功能

规则遵循（PR_Review提示词.md）：
- ✅ 仅修改 pages/ 目录
- ✅ 不使用 print 调试，不使用全局变量赋值
- ✅ 通过 GlobalState.show_toast 进行状态反馈
"""

try:
    import reflex as rx
except Exception:
    rx = None

vscode_config_page = None

if rx is not None:
    try:
        from states.vscode_config import VSCodeConfigState
    except Exception:
        try:
            from oaepp.states.vscode_config import VSCodeConfigState
        except Exception:
            VSCodeConfigState = None

    def _rec_item(item: dict):
        return rx.hstack(
            rx.code(item["id"], size="1"),
            rx.text(item.get("name", ""), size="1", color_scheme="gray"),
            rx.icon_button(
                "x",
                on_click=lambda eid=item["id"]: VSCodeConfigState.remove_recommendation(eid),
                variant="ghost",
                color_scheme="red",
                size="1",
            ),
            justify="between",
            width="100%",
            padding="4px",
        )

    def _ban_item(item: dict):
        return rx.hstack(
            rx.code(item["id"], size="1"),
            rx.text(item.get("name", ""), size="1", color_scheme="gray"),
            rx.icon_button(
                "x",
                on_click=lambda eid=item["id"]: VSCodeConfigState.remove_banned(eid),
                variant="ghost",
                color_scheme="red",
                size="1",
            ),
            justify="between",
            width="100%",
            padding="4px",
        )

    def _file_tab(f: dict):
        return rx.button(
            f["name"],
            on_click=lambda p=f["path"]: VSCodeConfigState.set_current_file(p),
            variant="ghost",
            size="1",
        )

    def vscode_config_page():
        return rx.container(
            rx.vstack(
                rx.heading("VS Code & Copilot 配置管理", size="6"),
                rx.text(
                    "F-T-002 · 教师端 · 开发运维",
                    color_scheme="gray",
                    size="1",
                ),

                rx.cond(
                    VSCodeConfigState.toast_message != "",
                    rx.callout(
                        VSCodeConfigState.toast_message,
                        icon=rx.cond(
                            VSCodeConfigState.toast_type == "error",
                            "triangle_alert",
                            rx.cond(
                                VSCodeConfigState.toast_type == "success",
                                "circle_check",
                                "info",
                            ),
                        ),
                        color_scheme=rx.cond(
                            VSCodeConfigState.toast_type == "error",
                            "red",
                            rx.cond(
                                VSCodeConfigState.toast_type == "success",
                                "green",
                                "blue",
                            ),
                        ),
                        width="100%",
                    ),
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("VS Code 扩展管理", size="3"),
                        rx.hstack(
                            rx.vstack(
                                rx.heading("推荐安装", size="2", color_scheme="blue"),
                                rx.foreach(
                                    VSCodeConfigState.recommendations,
                                    _rec_item,
                                ),
                                rx.hstack(
                                    rx.input(
                                        placeholder="扩展 ID",
                                        value=VSCodeConfigState.rec_id,
                                        on_change=VSCodeConfigState.set_rec_id,
                                        size="1",
                                    ),
                                    rx.input(
                                        placeholder="名称",
                                        value=VSCodeConfigState.rec_name,
                                        on_change=VSCodeConfigState.set_rec_name,
                                        size="1",
                                    ),
                                    rx.button(
                                        "+ 添加",
                                        on_click=VSCodeConfigState.add_recommendation,
                                        color_scheme="blue",
                                        size="1",
                                    ),
                                    width="100%",
                                ),
                                width="50%",
                            ),
                            rx.vstack(
                                rx.heading("禁止安装", size="2", color_scheme="red"),
                                rx.foreach(
                                    VSCodeConfigState.banned,
                                    _ban_item,
                                ),
                                rx.hstack(
                                    rx.input(
                                        placeholder="扩展 ID",
                                        value=VSCodeConfigState.ban_id,
                                        on_change=VSCodeConfigState.set_ban_id,
                                        size="1",
                                    ),
                                    rx.input(
                                        placeholder="名称",
                                        value=VSCodeConfigState.ban_name,
                                        on_change=VSCodeConfigState.set_ban_name,
                                        size="1",
                                    ),
                                    rx.button(
                                        "+ 添加",
                                        on_click=VSCodeConfigState.add_banned,
                                        color_scheme="red",
                                        variant="outline",
                                        size="1",
                                    ),
                                    width="100%",
                                ),
                                width="50%",
                            ),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("预设模板:", size="1", color_scheme="gray"),
                            rx.button(
                                "Python标准",
                                on_click=lambda: VSCodeConfigState.apply_preset(
                                    "python-dev"
                                ),
                                size="1",
                            ),
                            rx.button(
                                "Copilot全家桶",
                                on_click=lambda: VSCodeConfigState.apply_preset(
                                    "copilot-suite"
                                ),
                                size="1",
                            ),
                            rx.button(
                                "Reflex开发",
                                on_click=lambda: VSCodeConfigState.apply_preset(
                                    "reflex-dev"
                                ),
                                size="1",
                            ),
                            padding_top="8px",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("JSON 预览", size="3"),
                        rx.text(
                            ".vscode/extensions.json",
                            size="1",
                            color_scheme="gray",
                        ),
                        rx.code_block(
                            VSCodeConfigState.json_preview,
                            language="json",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.button(
                                "生成文件",
                                on_click=VSCodeConfigState.generate_extensions_json,
                                color_scheme="blue",
                                size="1",
                            ),
                            width="100%",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("Copilot 指令文件编辑", size="3"),
                        rx.hstack(
                            rx.foreach(
                                VSCodeConfigState.instruction_files,
                                _file_tab,
                            ),
                            width="100%",
                        ),
                        rx.text_area(
                            value=VSCodeConfigState.editor_content,
                            on_change=VSCodeConfigState.set_editor_content,
                            placeholder="选择文件后在此编辑...",
                            width="100%",
                            min_height="260px",
                        ),
                        rx.hstack(
                            rx.button(
                                "重新加载",
                                on_click=VSCodeConfigState.load_file_content,
                                size="1",
                            ),
                            rx.button(
                                "保存文件",
                                on_click=VSCodeConfigState.save_file_content,
                                color_scheme="green",
                                size="1",
                            ),
                            width="100%",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.hstack(
                        rx.cond(
                            VSCodeConfigState.git_dirty,
                            rx.badge("有变更", color_scheme="orange"),
                            rx.badge("干净", color_scheme="green"),
                        ),
                        rx.text(
                            "分支: " + VSCodeConfigState.git_branch,
                            size="1",
                            color_scheme="gray",
                        ),
                        rx.spacer(),
                        rx.button(
                            "刷新状态",
                            on_click=VSCodeConfigState.check_git_status,
                            size="1",
                        ),
                        rx.button(
                            "提交到仓库",
                            on_click=VSCodeConfigState.commit_and_push,
                            color_scheme="blue",
                            size="1",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                on_mount=VSCodeConfigState.on_mount,
                spacing="4",
                width="100%",
            ),
            width="100%",
            min_height="100vh",
            max_width="900px",
            margin="0 auto",
            padding="20px",
        )
