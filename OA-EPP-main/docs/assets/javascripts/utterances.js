// Utterances 评论系统注入
// 在页面内容区底部动态插入 Utterances widget
(function () {
  function insertUtterances() {
    // 找到内容容器
    var article = document.querySelector("article.md-content__inner");
    if (!article) return;

    // 避免重复注入
    if (article.querySelector(".utterances-container")) return;

    // 创建容器
    var container = document.createElement("div");
    container.className = "utterances-container";
    container.style.marginTop = "2rem";

    // 添加标题
    var heading = document.createElement("h2");
    heading.id = "__comments";
    heading.textContent = "\uD83D\uDCAC 评论";
    container.appendChild(heading);

    // 插入 Utterances script
    var script = document.createElement("script");
    script.src = "https://utteranc.es/client.js";
    script.setAttribute("repo", "uwislab/robotics-systems-course");
    script.setAttribute("issue-term", "pathname");
    script.setAttribute("theme", "github-light");
    script.setAttribute("crossorigin", "anonymous");
    script.async = true;
    container.appendChild(script);

    article.appendChild(container);
  }

  // 初始加载
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", insertUtterances);
  } else {
    insertUtterances();
  }

  // Material 即时导航支持（SPA 模式）
  if (typeof document$ !== "undefined") {
    document$.subscribe(function () {
      // 延迟执行确保 DOM 已更新
      setTimeout(insertUtterances, 100);
    });
  }
})();
