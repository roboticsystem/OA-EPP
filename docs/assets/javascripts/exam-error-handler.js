/**
 * exam-error-handler.js
 * 统一错误处理模块 — 错误分类、友好提示、重试机制
 *
 * 暴露 window.ExamErrorHandler，供 exam-login.js 和 teacher.html 使用。
 * 在所有 MkDocs 页面和教师后台页面中加载。
 */
(function () {
  "use strict";

  // ── 错误类型枚举 ──────────────────────────────────────
  var TYPES = {
    NETWORK: "NETWORK",
    TIMEOUT: "TIMEOUT",
    AUTH: "AUTH",
    PERMISSION: "PERMISSION",
    NOT_FOUND: "NOT_FOUND",
    CONFLICT: "CONFLICT",
    VALIDATION: "VALIDATION",
    UPLOAD: "UPLOAD",
    SERVER: "SERVER",
    UNKNOWN: "UNKNOWN",
  };

  // ── 上下文 → 错误消息映射 ─────────────────────────────
  var MSG = {};

  // 网络错误
  MSG["NETWORK"] = {
    login: { message: "无法连接服务器，请检查网络后重试", suggestion: "请确认网络连接正常后点击重试" },
    upload: { message: "上传失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
    verify: { message: "身份验证失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
    submit: { message: "成绩提交失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
    search: { message: "搜索失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
    load: { message: "数据加载失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
    delete: { message: "删除失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
    export: { message: "导出失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
    add: { message: "添加失败：网络连接中断", suggestion: "请检查网络连接后点击重试" },
  };

  MSG["TIMEOUT"] = {
    default: { message: "请求超时，请稍后重试", suggestion: "服务器响应较慢，请稍后重试" },
  };

  MSG["AUTH"] = {
    login: { message: "密码错误，请重新输入", suggestion: "请确认密码后重新尝试" },
    verify: { message: "验证失败，请重新选择身份", suggestion: "请重新选择学生后确认" },
    load: { message: "登录已过期，请重新登录", suggestion: "请退出后重新登录" },
  };

  MSG["PERMISSION"] = {
    verify: { message: "学号不在名单中，请联系老师确认", suggestion: "如确认已在名单中，请联系老师" },
  };

  MSG["CONFLICT"] = {
    submit: { message: "您已经提交过本次考试的成绩", suggestion: "每人每考试只能提交一次" },
    add: { message: "", suggestion: "" }, // 使用服务器返回的 detail
  };

  MSG["UPLOAD"] = {
    upload: { message: "上传失败", suggestion: "请检查文件格式和大小后重试" },
  };

  MSG["SERVER"] = {
    default: { message: "服务器繁忙，请稍后重试", suggestion: "如持续出现此问题，请联系老师" },
  };

  MSG["VALIDATION"] = {
    upload: { message: "", suggestion: "请检查文件格式和大小后重新选择" },
  };

  MSG["UNKNOWN"] = {
    default: { message: "操作失败，请稍后重试", suggestion: "如持续出现此问题，请刷新页面后重试" },
  };

  // ── 可重试的错误类型 ──────────────────────────────────
  var RETRYABLE = {};
  RETRYABLE[TYPES.NETWORK] = true;
  RETRYABLE[TYPES.TIMEOUT] = true;
  RETRYABLE[TYPES.SERVER] = true;
  RETRYABLE[TYPES.UPLOAD] = true;
  RETRYABLE[TYPES.VALIDATION] = true;
  RETRYABLE[TYPES.UNKNOWN] = true;

  // ── 图标 ──────────────────────────────────────────────
  var ICONS = {};
  ICONS[TYPES.NETWORK] = "🔌";
  ICONS[TYPES.TIMEOUT] = "⏱️";
  ICONS[TYPES.AUTH] = "🔒";
  ICONS[TYPES.PERMISSION] = "🚫";
  ICONS[TYPES.NOT_FOUND] = "🔍";
  ICONS[TYPES.CONFLICT] = "⚠️";
  ICONS[TYPES.VALIDATION] = "📋";
  ICONS[TYPES.UPLOAD] = "📂";
  ICONS[TYPES.SERVER] = "💥";
  ICONS[TYPES.UNKNOWN] = "❓";

  // ── 核心函数：错误分类 ────────────────────────────────
  /**
   * 将 fetch 错误或 Response 分类为具体错误类型
   * @param {Error|Object} error - fetch 抛出的 Error 或 {status, responseJSON, message}
   * @param {string} context - 操作上下文
   * @returns {{type, message, suggestion, canRetry, detail}}
   */
  function categorizeError(error, context) {
    var type = TYPES.UNKNOWN;
    var detail = "";

    // 1. 检测是否为 HTTP Response（有 statusCode）
    if (error && typeof error.status === "number") {
      detail = (error.responseJSON && error.responseJSON.detail) || error.message || "";
      if (error.status === 401) type = TYPES.AUTH;
      else if (error.status === 403) type = TYPES.PERMISSION;
      else if (error.status === 404) type = TYPES.NOT_FOUND;
      else if (error.status === 409) type = TYPES.CONFLICT;
      else if (error.status === 413) type = TYPES.UPLOAD;
      else if (error.status === 422) type = TYPES.VALIDATION;
      else if (error.status >= 500) type = TYPES.SERVER;
      else type = TYPES.UNKNOWN;
    }
    // 2. 检测是否为原生 Error（网络/超时）
    else if (error instanceof Error) {
      detail = error.message || "";
      if (error.name === "AbortError" || /timeout|超时/i.test(detail)) {
        type = TYPES.TIMEOUT;
      } else if (/network|fetch|failed|网络|中断|拒绝连接|ECONNREFUSED/i.test(detail)) {
        type = TYPES.NETWORK;
      } else {
        type = TYPES.NETWORK; // 默认网络错误
      }
    }
    // 2.5 检测普通对象（如 { message: "文件过大..." } 客户端校验错误）
    else if (error && typeof error === "object" && error.message) {
      detail = error.message;
      type = TYPES.VALIDATION;
    }
    // 3. 字符串消息
    else if (typeof error === "string") {
      detail = error;
      type = TYPES.UNKNOWN;
    }

    // 获取对应上下文的消息
    var msgEntry = null;
    if (MSG[type]) {
      msgEntry = MSG[type][context] || MSG[type]["default"];
    }
    if (!msgEntry) {
      msgEntry = MSG[TYPES.UNKNOWN]["default"];
    }

    var message = msgEntry.message;
    var suggestion = msgEntry.suggestion;

    // 客户端校验/UPLOAD/UNKNOWN 类型：优先使用具体 detail 作为消息
    if (detail && (type === TYPES.VALIDATION || type === TYPES.UPLOAD || type === TYPES.UNKNOWN)) {
      message = detail;
      suggestion = msgEntry.suggestion;
    }
    // CONFLICT 特殊处理：使用服务器返回的 detail
    else if (type === TYPES.CONFLICT && detail) {
      message = detail;
    }

    return {
      type: type,
      message: message,
      suggestion: suggestion,
      canRetry: !!RETRYABLE[type],
      detail: detail,
    };
  }

  // ── 原地展示错误（含重试按钮）────────────────────────
  /**
   * 在指定容器中渲染错误卡片，可选重试按钮
   * @param {HTMLElement} container - 错误展示容器
   * @param {*} error - 原始错误对象
   * @param {string} context - 操作上下文
   * @param {{onRetry: Function}} opts
   */
  function showInPlace(container, error, context, opts) {
    if (!container) return;
    opts = opts || {};
    var info = categorizeError(error, context);

    var html = '<div class="exam-error-inline">';
    html += '<div class="exam-error-icon">' + (ICONS[info.type] || "❓") + "</div>";
    html += '<div class="exam-error-content">';
    html += '<div class="exam-error-msg">' + escapeHtml(info.message) + "</div>";
    if (info.suggestion) {
      html += '<div class="exam-error-suggestion">' + escapeHtml(info.suggestion) + "</div>";
    }
    if (info.canRetry && opts.onRetry) {
      html +=
        '<button class="exam-retry-btn" onclick="this.disabled=true;this.textContent=\'重试中…\';(' +
        opts.onRetry.toString() +
        ")()\">重试</button>";
    }
    html += "</div></div>";

    container.innerHTML = html;
  }

  // ── Toast 通知 ────────────────────────────────────────
  var toastIdCounter = 0;

  /**
   * 在页面右上角显示浮动错误提示
   * @param {*} error
   * @param {string} context
   * @param {{onRetry: Function, duration: number}} opts
   */
  function showToast(error, context, opts) {
    opts = opts || {};
    var info = categorizeError(error, context);
    var duration = opts.duration || 6000;
    var id = "exam-toast-" + ++toastIdCounter;

    var toast = document.createElement("div");
    toast.className = "exam-error-toast exam-toast-error";
    toast.id = id;

    var icon = ICONS[info.type] || "❓";
    var retryHtml = "";
    if (info.canRetry && opts.onRetry) {
      retryHtml =
        '<span class="exam-retry-link" id="' +
        id +
        '-retry">重试</span>';
    }

    toast.innerHTML =
      '<span style="font-size:1.1rem;flex-shrink:0">' +
      icon +
      "</span>" +
      '<div style="flex:1;min-width:0">' +
      '<div style="font-size:.9rem;color:#333;margin-bottom:2px">' +
      escapeHtml(info.message) +
      "</div>" +
      (info.suggestion
        ? '<div style="font-size:.8rem;color:#888">' +
          escapeHtml(info.suggestion) +
          retryHtml +
          "</div>"
        : retryHtml
          ? '<div style="font-size:.8rem">' + retryHtml + "</div>"
          : "") +
      "</div>";

    document.body.appendChild(toast);

    // 绑定重试
    if (info.canRetry && opts.onRetry) {
      var retryEl = document.getElementById(id + "-retry");
      if (retryEl) {
        retryEl.addEventListener("click", function () {
          removeToast(id);
          opts.onRetry();
        });
      }
    }

    // 自动消失
    setTimeout(function () {
      removeToast(id);
    }, duration);
  }

  function removeToast(id) {
    var el = document.getElementById(id);
    if (el) {
      el.style.opacity = "0";
      el.style.transition = "opacity .3s";
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 300);
    }
  }

  // ── Fetch 自动重试 ────────────────────────────────────
  /**
   * 带自动重试的 fetch 封装
   * @param {string} url
   * @param {RequestInit} options
   * @param {string} context
   * @param {{maxRetries: number, retryDelay: number}} opts
   * @returns {Promise<Response>}
   */
  function retryingFetch(url, options, context, opts) {
    opts = opts || {};
    var maxRetries = opts.maxRetries || 2;
    var retryDelay = opts.retryDelay || 1000;
    var attempt = 0;

    function tryFetch() {
      return fetch(url, options).then(function (response) {
        // HTTP 错误且不可重试 → 包装为类 Error 对象抛出
        if (!response.ok && !RETRYABLE[_httpStatusToType(response.status)]) {
          return response.json()
            .then(function (body) {
              var err = new Error(body.detail || "请求失败");
              err.status = response.status;
              err.responseJSON = body;
              throw err;
            })
            .catch(function (jsonErr) {
              // 无法解析 JSON（如 401 无 body）
              if (jsonErr.status) throw jsonErr;
              var err = new Error("请求失败");
              err.status = response.status;
              throw err;
            });
        }
        // HTTP 错误但可重试 → 继续抛出让外层 catch 处理重试
        if (!response.ok) {
          return response.json()
            .then(function (body) {
              var err = new Error(body.detail || "请求失败");
              err.status = response.status;
              err.responseJSON = body;
              throw err;
            })
            .catch(function (jsonErr) {
              if (jsonErr.status) throw jsonErr;
              var err = new Error("请求失败");
              err.status = response.status;
              throw err;
            });
        }
        return response;
      }).catch(function (err) {
        // 已经是结构化错误（有 status），检查是否可重试
        if (err.status && !RETRYABLE[_httpStatusToType(err.status)]) {
          throw err;
        }
        // 网络错误或可重试的 HTTP 错误
        attempt++;
        if (attempt <= maxRetries) {
          var delay = retryDelay * Math.pow(2, attempt - 1);
          return new Promise(function (resolve) {
            setTimeout(function () {
              resolve(tryFetch());
            }, delay);
          });
        }
        // 重试耗尽 → 增加上下文信息后抛出
        if (!err.context) {
          err.context = context;
        }
        throw err;
      });
    }

    return tryFetch();
  }

  function _httpStatusToType(status) {
    if (status === 401) return TYPES.AUTH;
    if (status === 403) return TYPES.PERMISSION;
    if (status === 404) return TYPES.NOT_FOUND;
    if (status === 409) return TYPES.CONFLICT;
    if (status === 413) return TYPES.UPLOAD;
    if (status === 422) return TYPES.VALIDATION;
    if (status >= 500) return TYPES.SERVER;
    return TYPES.UNKNOWN;
  }

  // ── 文件校验 ──────────────────────────────────────────
  /**
   * 在上传前校验文件
   * @param {File} file
   * @param {{maxSize: number, allowedTypes: string[], allowedExtensions: string[]}} rules
   * @returns {{valid: boolean, error: string|null}}
   */
  function validateFile(file, rules) {
    rules = rules || {};
    if (!file) {
      return { valid: false, error: "文件为空，请重新选择" };
    }

    // 大小校验
    if (rules.maxSize && file.size > rules.maxSize) {
      var maxMB = (rules.maxSize / 1024 / 1024).toFixed(0);
      var actualMB = (file.size / 1024 / 1024).toFixed(1);
      return {
        valid: false,
        error: "文件过大（最大 " + maxMB + "MB），当前文件 " + actualMB + "MB，请压缩或拆分后重试",
      };
    }

    // 空文件
    if (file.size === 0) {
      return { valid: false, error: "文件为空，请重新选择" };
    }

    // 扩展名校验
    if (rules.allowedExtensions && rules.allowedExtensions.length) {
      var ext = "." + file.name.split(".").pop().toLowerCase();
      if (rules.allowedExtensions.indexOf(ext) === -1) {
        var extList = rules.allowedExtensions.join("、");
        return {
          valid: false,
          error: "不支持的文件类型，请上传 " + extList + " 格式的文件",
        };
      }
    }

    // MIME 类型校验（宽松校验，因为 CSV 的 MIME 可能不标准）
    if (rules.allowedTypes && rules.allowedTypes.length) {
      if (rules.allowedTypes.indexOf(file.type) === -1 && file.type !== "") {
        // 仅当 MIME 不为空且不匹配时才报错
        return {
          valid: false,
          error: "不支持的文件类型，请上传 CSV 格式的文件",
        };
      }
    }

    return { valid: true, error: null };
  }

  // ── 工具函数 ──────────────────────────────────────────
  function escapeHtml(str) {
    if (!str) return "";
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ── 暴露 API ──────────────────────────────────────────
  window.ExamErrorHandler = {
    TYPES: TYPES,
    categorizeError: categorizeError,
    showInPlace: showInPlace,
    showToast: showToast,
    retryingFetch: retryingFetch,
    validateFile: validateFile,
  };
})();
