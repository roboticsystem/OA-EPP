/**
 * footer-links.js
 * 在页面底部注入工具链接栏
 * - 本地开发（localhost）：显示完整 localhost 地址（含端口）
 * - 生产环境：显示相对路径（/teacher、/score）
 */
(function () {
  const IS_LOCAL = location.hostname === "127.0.0.1" || location.hostname === "localhost";

  const links = IS_LOCAL
    ? [
        { icon: "📖", label: "文档地址",   href: "http://127.0.0.1:8008",          note: "MkDocs 热重载" },
        { icon: "🎓", label: "教师后台",   href: "http://127.0.0.1:8009/teacher",  note: "密码：admin123" },
        { icon: "📊", label: "学生查分",   href: "http://127.0.0.1:8009/score",    note: "" },
        { icon: "📡", label: "API 文档",   href: "http://127.0.0.1:8009/api/docs", note: "FastAPI Swagger" },
      ]
    : [
        { icon: "🎓", label: "教师后台",   href: "/teacher", note: "" },
        { icon: "📊", label: "学生查分",   href: "/score",   note: "" },
      ];

  function inject() {
    // 避免重复注入
    if (document.getElementById("exam-footer-links")) return;

    const footerEl = document.querySelector(".md-footer");
    if (!footerEl) return;

    const bar = document.createElement("div");
    bar.id = "exam-footer-links";
    bar.style.cssText = [
      "background: var(--md-footer-bg-color, #1565c0)",
      "border-top: 1px solid rgba(255,255,255,.12)",
      "padding: 10px 16px",
      "display: flex",
      "align-items: center",
      "justify-content: center",
      "flex-wrap: wrap",
      "gap: 6px 20px",
      "font-size: .78rem",
    ].join(";");

    const labelEl = document.createElement("span");
    labelEl.textContent = IS_LOCAL ? "🛠 本地开发工具：" : "🔗 课程工具：";
    labelEl.style.cssText = "color:rgba(255,255,255,.6); white-space:nowrap;";
    bar.appendChild(labelEl);

    links.forEach(({ icon, label, href, note }) => {
      const a = document.createElement("a");
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener";
      a.style.cssText = [
        "color: rgba(255,255,255,.85)",
        "text-decoration: none",
        "white-space: nowrap",
        "padding: 3px 8px",
        "border-radius: 4px",
        "border: 1px solid rgba(255,255,255,.25)",
        "transition: background .15s",
      ].join(";");
      a.onmouseenter = () => a.style.background = "rgba(255,255,255,.15)";
      a.onmouseleave = () => a.style.background = "";
      a.innerHTML = `${icon} ${label}${note ? `<span style="opacity:.55;font-size:.9em"> · ${note}</span>` : ""}`;
      bar.appendChild(a);
    });

    footerEl.insertAdjacentElement("beforebegin", bar);
  }

  // 初始注入
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inject);
  } else {
    inject();
  }

  // MkDocs Material instant navigation（SPA 模式）支持
  document.addEventListener("DOMContentSwitch", () => {
    const old = document.getElementById("exam-footer-links");
    if (old) old.remove();
    inject();
  });
})();
