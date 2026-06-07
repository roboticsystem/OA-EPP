"""
F-T-002 VS Code扩展与Copilot提示词管理 — Reflex 页面
"""
try:
    import reflex as rx
except Exception:
    rx = None

vscode_config_page = None

if rx is not None:
    try:
        from states.teacher_vscode import VSCodeConfigState
    except Exception:
        try:
            from oaepp.states.teacher_vscode import VSCodeConfigState
        except Exception:
            VSCodeConfigState = None

    def _rec_item(item):
        return rx.hstack(
            rx.code(item["id"], size="1"),
            rx.text(item.get("name", ""), size="1", color="gray"),
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

    def _ban_item(item):
        return rx.hstack(
            rx.code(item["id"], size="1"),
            rx.text(item.get("name", ""), size="1", color="gray"),
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

    def _file_tab(f):
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
                rx.text("F-T-002 \u00b7 \u6559\u5e08\u7aef \u00b7 \u5f00\u53d1\u8fd0\u7ef4", color="gray", size="1"),

                rx.cond(
                    VSCodeConfigState.status_message != "",
                    rx.callout(
                        VSCodeConfigState.status_message,
                        icon=rx.cond(
                            VSCodeConfigState.status_type == "error", "triangle_alert",
                            rx.cond(VSCodeConfigState.status_type == "success", "circle_check", "info"),
                        ),
                        color_scheme=rx.cond(
                            VSCodeConfigState.status_type == "error", "red",
                            rx.cond(VSCodeConfigState.status_type == "success", "green", "blue"),
                        ),
                        width="100%",
                    ),
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("VS Code \u6269\u5c55\u7ba1\u7406", size="3"),
                        rx.hstack(
                            rx.vstack(
                                rx.heading("\u63a8\u8350\u5b89\u88c5", size="2", color="blue"),
                                rx.foreach(VSCodeConfigState.recommendations, _rec_item),
                                rx.hstack(
                                    rx.input(
                                        placeholder="\u6269\u5c55 ID",
                                        value=VSCodeConfigState.rec_id,
                                        on_change=VSCodeConfigState.set_rec_id,
                                        size="1",
                                    ),
                                    rx.input(
                                        placeholder="\u540d\u79f0",
                                        value=VSCodeConfigState.rec_name,
                                        on_change=VSCodeConfigState.set_rec_name,
                                        size="1",
                                    ),
                                    rx.button(
                                        "+ \u6dfb\u52a0",
                                        on_click=VSCodeConfigState.add_recommendation,
                                        color_scheme="blue",
                                        size="1",
                                    ),
                                    width="100%",
                                ),
                                width="50%",
                            ),
                            rx.vstack(
                                rx.heading("\u7981\u6b62\u5b89\u88c5", size="2", color="red"),
                                rx.foreach(VSCodeConfigState.banned, _ban_item),
                                rx.hstack(
                                    rx.input(
                                        placeholder="\u6269\u5c55 ID",
                                        value=VSCodeConfigState.ban_id,
                                        on_change=VSCodeConfigState.set_ban_id,
                                        size="1",
                                    ),
                                    rx.input(
                                        placeholder="\u540d\u79f0",
                                        value=VSCodeConfigState.ban_name,
                                        on_change=VSCodeConfigState.set_ban_name,
                                        size="1",
                                    ),
                                    rx.button(
                                        "+ \u6dfb\u52a0",
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
                            rx.text("\u9884\u8bbe\u6a21\u677f:", size="1", color="gray"),
                            rx.button(
                                "Python\u6807\u51c6",
                                on_click=lambda: VSCodeConfigState.apply_preset("python-dev"),
                                size="1",
                            ),
                            rx.button(
                                "Copilot\u5168\u5bb6\u6876",
                                on_click=lambda: VSCodeConfigState.apply_preset("copilot-suite"),
                                size="1",
                            ),
                            rx.button(
                                "Reflex\u5f00\u53d1",
                                on_click=lambda: VSCodeConfigState.apply_preset("reflex-dev"),
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
                        rx.heading("JSON \u9884\u89c8", size="3"),
                        rx.text(".vscode/extensions.json", size="1", color="gray"),
                        rx.code_block(
                            VSCodeConfigState.json_preview,
                            language="json",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.button(
                                "\u751f\u6210\u6587\u4ef6",
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
                        rx.heading("Copilot \u6307\u4ee4\u6587\u4ef6\u7f16\u8f91", size="3"),
                        rx.hstack(
                            rx.foreach(VSCodeConfigState.instruction_files, _file_tab),
                            width="100%",
                        ),
                        rx.text_area(
                            value=VSCodeConfigState.editor_content,
                            on_change=VSCodeConfigState.set_editor_content,
                            placeholder="\u9009\u62e9\u6587\u4ef6\u540e\u5728\u6b64\u7f16\u8f91...",
                            width="100%",
                            min_height="260px",
                        ),
                        rx.hstack(
                            rx.button(
                                "\u91cd\u65b0\u52a0\u8f7d",
                                on_click=VSCodeConfigState.load_file_content,
                                size="1",
                            ),
                            rx.button(
                                "\u4fdd\u5b58\u6587\u4ef6",
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
                            rx.badge("\u6709\u53d8\u66f4", color_scheme="orange"),
                            rx.badge("\u5e72\u51c0", color_scheme="green"),
                        ),
                        rx.text("\u5206\u652f: " + VSCodeConfigState.git_branch, size="1", color="gray"),
                        rx.spacer(),
                        rx.button(
                            "\u5237\u65b0\u72b6\u6001",
                            on_click=VSCodeConfigState.check_git_status,
                            size="1",
                        ),
                        rx.button(
                            "\u63d0\u4ea4\u5230\u4ed3\u5e93",
                            on_click=VSCodeConfigState.commit_and_push,
                            color_scheme="blue",
                            size="1",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                on_mount=[
                    VSCodeConfigState.load_extensions(),
                    VSCodeConfigState.load_instruction_files(),
                    VSCodeConfigState.check_git_status(),
                ],
                spacing="4",
                width="100%",
            ),
            width="100%",
            min_height="100vh",
            max_width="900px",
            margin="0 auto",
            padding="20px",
        )

else:
    def vscode_config_page():
        return """<div style="padding:40px;text-align:center;">
            <h2>Reflex not installed</h2>
            <p>Please install Reflex to use this feature.</p>
        </div>"""
