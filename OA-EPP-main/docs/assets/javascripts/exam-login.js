/**
 * exam-login.js
 * 考试身份认证 + 自动提交成绩模块
 *
 * 使用方式：在 Markdown 页面中添加：
 *   <div id="exam-meta" data-exam-id="chapter2" data-exam-title="第二章 CubeMX编程测验"></div>
 *
 * 该脚本会：
 * 1. 找到 .quiz-intro 区块，在其前面插入"登录后开始做题"按钮
 * 2. 用覆盖层遮住题目
 * 3. 弹出身份确认 Modal（支持姓名/拼音搜索）
 * 4. 核验身份（服务器端检查是否已提交）
 * 5. 已提交 → 展示成绩，题目保持隐藏
 * 6. 未提交 → 解除覆盖层，监听答题进度，全部答完后自动提交
 */
(function () {
  "use strict";

  // 后端 API 基础路径
  // 本地开发时（localhost/127.0.0.1）FastAPI 跑在 :8009，生产环境由 Nginx 同域转发
  const IS_LOCAL = location.hostname === "127.0.0.1" || location.hostname === "localhost";
  const API = IS_LOCAL ? "http://127.0.0.1:8009" : "";

  // ── 工具函数 ──────────────────────────────────────────
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function ce(tag, cls, html) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (html !== undefined) el.innerHTML = html;
    return el;
  }

  // ── 页面初始化 ────────────────────────────────────────
  function init() {
    const meta = document.getElementById("exam-meta");
    if (!meta) return; // 本页面没有考试模块，跳过

    const examId    = meta.dataset.examId;
    const examTitle = meta.dataset.examTitle || "章节测验";

    const quizIntro = qs(".quiz-intro");
    if (!quizIntro) return;

    // 找到所有 .quiz 元素和 #quiz-results
    const quizEls   = Array.from(document.querySelectorAll(".quiz"));
    const quizResults = document.getElementById("quiz-results");

    // 创建登录横幅（插入到 quiz-intro 前面）
    const banner = buildBanner(examTitle);
    quizIntro.parentNode.insertBefore(banner, quizIntro);

    // 创建覆盖层（覆盖整个题目区域）
    const overlay = buildOverlay(quizIntro, quizEls, quizResults);

    // 检查 sessionStorage 是否有已验证 token
    const storedToken = sessionStorage.getItem(`exam_token_${examId}`);
    if (storedToken) {
      // 静默校验：直接向服务器确认是否已提交
      const cachedStudentId = sessionStorage.getItem(`exam_student_id_${examId}`);
      if (cachedStudentId) {
        silentCheck(examId, cachedStudentId, overlay, banner, quizEls, quizResults, storedToken);
        return;
      }
    }

    // 绑定登录按钮
    qs(".exam-login-btn", banner).addEventListener("click", () => {
      openModal(examId, examTitle, overlay, banner, quizEls, quizResults);
    });
  }

  // ── 静默校验（刷新后恢复状态）─────────────────────────
  async function silentCheck(examId, studentId, overlay, banner, quizEls, quizResults, token) {
    try {
      const r = await fetch(`${API}/api/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, exam_id: examId }),
      });
      const d = await r.json();
      if (!r.ok) { return; } // token 失效，保持遮罩
      if (d.already_submitted) {
        showSubmitted(d, banner, overlay, quizEls, quizResults);
      } else {
        unlockQuiz(d.name, token, examId, overlay, banner, quizEls, quizResults);
      }
    } catch (e) { /* 网络错误，保持遮罩 */ }
  }

  // ── 构建登录横幅 ──────────────────────────────────────
  function buildBanner(title) {
    const div = ce("div", "exam-login-banner");
    div.innerHTML = `
      <h3>📝 ${title}</h3>
      <p>请先确认身份，才能开始答题。完成后成绩将自动提交到服务器。</p>
      <button class="exam-login-btn">🔒 登录后开始做题</button>
    `;
    return div;
  }

  // ── 构建题目覆盖层 ────────────────────────────────────
  function buildOverlay(quizIntro, quizEls, quizResults) {
    // 隐藏 quiz-intro 的重置按钮（防止学生自行重置）
    const resetBtn = quizIntro.querySelector(".quiz-intro-reset");
    if (resetBtn) resetBtn.style.display = "none";

    // 用 wrapper 包裹所有题目元素，加覆盖层
    const wrap = ce("div", "exam-quiz-overlay");
    wrap.style.minHeight = "80px";

    // 把 quizIntro 移入 wrap（插入顺序：quizIntro、quizEls、quizResults）
    quizIntro.parentNode.insertBefore(wrap, quizIntro);
    wrap.appendChild(quizIntro);
    quizEls.forEach(el => wrap.appendChild(el));
    if (quizResults) wrap.appendChild(quizResults);

    const mask = ce("div", "exam-quiz-mask");
    mask.innerHTML = `<span style="color:#888;font-size:.95rem">请先登录后查看题目</span>`;
    wrap.appendChild(mask);
    mask.style.pointerEvents = "all";

    return { wrap, mask };
  }

  // ── 打开身份确认 Modal ────────────────────────────────
  function openModal(examId, examTitle, overlay, banner, quizEls, quizResults) {
    const backdrop = ce("div", "exam-modal-backdrop");
    backdrop.innerHTML = `
      <div class="exam-modal">
        <div class="exam-modal-header">
          <h3>确认身份 — ${examTitle}</h3>
          <button class="exam-modal-close" title="关闭">✕</button>
        </div>
        <div class="exam-modal-body">
          <div id="exam-modal-msg" style="display:none"></div>
          <label>输入姓名（支持中文或拼音，如：张三 / zhangsan / zs）</label>
          <input type="text" id="exam-name-input" placeholder="请输入姓名…" autocomplete="off">
          <div id="exam-candidate-wrap" style="display:none">
            <div class="exam-candidate-list" id="exam-candidate-list"></div>
          </div>
          <button class="exam-confirm-btn" id="exam-confirm-btn" disabled>确认，开始做题</button>
          <p class="exam-modal-hint">找不到自己？请联系老师确认名单</p>
        </div>
      </div>
    `;
    document.body.appendChild(backdrop);

    let selectedStudentId = null;
    let selectedName = null;
    let searchTimer = null;

    // 关闭
    qs(".exam-modal-close", backdrop).addEventListener("click", () => backdrop.remove());
    backdrop.addEventListener("click", e => { if (e.target === backdrop) backdrop.remove(); });

    // 搜索
    const nameInput = backdrop.querySelector("#exam-name-input");
    nameInput.addEventListener("input", () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => searchStudents(nameInput.value.trim()), 300);
    });
    nameInput.focus();

    // 确认按钮
    backdrop.querySelector("#exam-confirm-btn").addEventListener("click", async () => {
      if (!selectedStudentId) return;
      await doVerify(selectedStudentId, selectedName, examId, backdrop, overlay, banner, quizEls, quizResults);
    });

    async function searchStudents(q) {
      if (!q) { qs("#exam-candidate-wrap", backdrop).style.display = "none"; return; }
      try {
        const r = await fetch(`${API}/api/students/search?q=${encodeURIComponent(q)}`);
        const list = await r.json();
        renderCandidates(list);
      } catch (e) { showModalMsg("网络错误，请检查连接", "error"); }
    }

    function renderCandidates(list) {
      const wrap = qs("#exam-candidate-wrap", backdrop);
      const container = qs("#exam-candidate-list", backdrop);
      selectedStudentId = null;
      selectedName = null;
      qs("#exam-confirm-btn", backdrop).disabled = true;

      if (!list.length) {
        wrap.style.display = "block";
        container.innerHTML = `<div style="padding:12px 14px;color:#bbb;font-size:.9rem">未找到匹配学生</div>`;
        return;
      }
      wrap.style.display = "block";
      container.innerHTML = list.map(s => `
        <div class="exam-candidate-item" data-id="${s.student_id}" data-name="${s.name}">
          <div>
            <div class="exam-cand-name">${s.name}</div>
            <div class="exam-cand-meta">${s.student_id}${s.class_name ? " · " + s.class_name : ""}</div>
          </div>
          <span style="color:#1565c0;font-size:.85rem">选择 ›</span>
        </div>
      `).join("");

      container.querySelectorAll(".exam-candidate-item").forEach(item => {
        item.addEventListener("click", () => {
          container.querySelectorAll(".exam-candidate-item").forEach(i => i.classList.remove("selected"));
          item.classList.add("selected");
          selectedStudentId = item.dataset.id;
          selectedName = item.dataset.name;
          qs("#exam-confirm-btn", backdrop).disabled = false;
        });
      });
    }

    function showModalMsg(msg, type) {
      const el = qs("#exam-modal-msg", backdrop);
      el.className = `exam-modal-msg ${type}`;
      el.textContent = msg;
      el.style.display = "block";
    }
  }

  // ── 核验身份（服务器端）──────────────────────────────
  async function doVerify(studentId, studentName, examId, backdrop, overlay, banner, quizEls, quizResults) {
    const btn = backdrop.querySelector("#exam-confirm-btn");
    btn.disabled = true;
    btn.textContent = "验证中…";

    try {
      const r = await fetch(`${API}/api/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, exam_id: examId }),
      });
      const d = await r.json();

      if (!r.ok) {
        const msgEl = backdrop.querySelector("#exam-modal-msg");
        msgEl.className = "exam-modal-msg error";
        msgEl.textContent = d.detail || "验证失败";
        msgEl.style.display = "block";
        btn.disabled = false;
        btn.textContent = "确认，开始做题";
        return;
      }

      backdrop.remove();

      if (d.already_submitted) {
        showSubmitted(d, banner, overlay, quizEls, quizResults);
      } else {
        // 保存 token 到 sessionStorage
        sessionStorage.setItem(`exam_token_${examId}`, d.token);
        sessionStorage.setItem(`exam_student_id_${examId}`, studentId);
        unlockQuiz(d.name, d.token, examId, overlay, banner, quizEls, quizResults);
      }
    } catch (e) {
      const msgEl = backdrop.querySelector("#exam-modal-msg");
      msgEl.className = "exam-modal-msg error";
      msgEl.textContent = "网络错误：" + e.message;
      msgEl.style.display = "block";
      btn.disabled = false;
      btn.textContent = "确认，开始做题";
    }
  }

  // ── 显示已提交成绩（题目保持隐藏）───────────────────
  function showSubmitted(data, banner, overlay, quizEls, quizResults) {
    // 替换横幅为成绩展示
    const pct = data.total > 0 ? Math.round(data.score / data.total * 100) : 0;
    const submitted = ce("div", "exam-submitted-banner");
    submitted.innerHTML = `
      <div style="font-size:1.6rem;margin-bottom:8px">🎉</div>
      <div class="score-big">${data.score}</div>
      <div class="score-label">满分 ${data.total} 分（${pct}%）</div>
      <div class="submitted-time">提交时间：${data.submitted_at}</div>
      <div style="margin-top:12px;font-size:.88rem;color:#888">您已完成本次测验，成绩已记录</div>
    `;
    banner.replaceWith(submitted);

    // 隐藏题目区域（保持覆盖）
    if (overlay && overlay.mask) {
      overlay.mask.innerHTML = `<span style="color:#888;font-size:.95rem">本次测验已完成</span>`;
    }
  }

  // ── 解锁题目 ─────────────────────────────────────────
  function unlockQuiz(name, token, examId, overlay, banner, quizEls, quizResults) {
    // 移除覆盖层
    if (overlay && overlay.mask) overlay.mask.remove();

    // 替换横幅为状态条
    const statusBar = ce("div", "exam-status-bar");
    statusBar.innerHTML = `✅ 已登录：<strong>${name}</strong>　|　全部作答完成后将自动提交成绩`;
    banner.replaceWith(statusBar);

    // 监听答题进度，全部答完自动提交
    watchProgress(token, examId, name, statusBar, quizEls, quizResults);
  }

  // ── 监听做题进度，自动提交 ───────────────────────────
  function watchProgress(token, examId, name, statusBar, quizEls, quizResults) {
    // 防止重复提交
    let submitted = false;

    function checkCompletion() {
      if (submitted) return;

      // 从 quiz-results 读取分数（mkdocs-quiz 在完成后填充该区域）
      const answeredEl = document.querySelector(".quiz-progress-answered");
      const totalEl    = document.querySelector(".quiz-progress-total");
      const scoreEl    = document.querySelector(".quiz-progress-score");
      const scoreTotalEl = document.querySelector(".quiz-progress-score-total");

      if (!answeredEl || !totalEl) return;

      const answered = parseInt(answeredEl.textContent) || 0;
      const total    = parseInt(totalEl.textContent) || 0;

      if (total === 0 || answered < total) return;

      // 全部答完
      submitted = true;

      const score     = parseInt(scoreEl?.textContent) || 0;
      const scoreTotal = parseInt(scoreTotalEl?.textContent) || total;

      // 延迟 800ms 再提交，给用户看到最后反馈
      setTimeout(() => doSubmit(token, examId, name, score, scoreTotal, statusBar, quizResults), 800);
    }

    // 监听 DOM 变化（mkdocs-quiz 修改进度条文本）
    const observer = new MutationObserver(checkCompletion);
    document.querySelectorAll(".quiz-progress-answered").forEach(el => {
      observer.observe(el, { childList: true, characterData: true, subtree: true });
    });

    // 也周期性检查一次（以防事件遗漏）
    const interval = setInterval(() => {
      checkCompletion();
      if (submitted) clearInterval(interval);
    }, 1000);
  }

  // ── 提交成绩到服务器 ─────────────────────────────────
  async function doSubmit(token, examId, name, score, total, statusBar, quizResults) {
    try {
      const r = await fetch(`${API}/api/exam/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ score, total }),
      });

      if (r.ok) {
        const now = new Date().toLocaleString("zh-CN");
        const pct = total > 0 ? Math.round(score / total * 100) : 0;
        statusBar.className = "";
        statusBar.innerHTML = `
          <div class="exam-submitted-banner">
            <div style="font-size:1.4rem;margin-bottom:6px">🎉 成绩已提交！</div>
            <div style="font-size:.95rem;color:#555;margin-bottom:8px">${name}，你本次测验的成绩：</div>
            <div class="score-big">${score}</div>
            <div class="score-label">满分 ${total} 分（${pct}%）</div>
            <div class="submitted-time">${now}</div>
          </div>
        `;
        // 清除 sessionStorage（已提交无需再保存 token）
        sessionStorage.removeItem(`exam_token_${examId}`);
      } else {
        const d = await r.json();
        if (r.status === 409) {
          // 已提交（并发情况）
          statusBar.innerHTML = `✅ ${d.detail}`;
        } else {
          statusBar.className = "exam-status-bar";
          statusBar.style.background = "#fff3e0";
          statusBar.style.borderColor = "#ffe082";
          statusBar.style.color = "#e65100";
          statusBar.textContent = "⚠️ 提交失败：" + (d.detail || "请刷新页面重试");
        }
      }
    } catch (e) {
      statusBar.style.background = "#ffebee";
      statusBar.textContent = "⚠️ 网络错误，成绩提交失败，请联系老师：" + e.message;
    }
  }

  // ── 入口：等待 DOM 就绪 ───────────────────────────────
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    // MkDocs Material 用 instant navigation，需要在每次导航后重新初始化
    init();
  }

  // 支持 MkDocs Material instant navigation（SPA 模式）
  document.addEventListener("DOMContentSwitch", init);

})();
