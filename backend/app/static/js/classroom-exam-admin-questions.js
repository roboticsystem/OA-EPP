/**
 * 课堂考试题目编辑器（教师发布页）
 */
try {
  console.log("classroom-exam-admin-questions.js: init");
  window.ClassroomQuestionEditor = (function () {
    "use strict";

  const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function nextLetter(n) {
    return LETTERS[n] || "?";
  }

  function renumberBlocks(container) {
    container.querySelectorAll(".q-block").forEach(function (block, idx) {
      block.querySelector(".q-num").textContent = "题目 " + (idx + 1);
    });
  }

  function bindTypeSwitch(block) {
    var sel = block.querySelector(".q-type");
    sel.addEventListener("change", function () {
      renderBody(block);
    });
  }

  function renderBody(block) {
    var body = block.querySelector(".q-body");
    var t = block.querySelector(".q-type").value;
    if (t === "single" || t === "multi") {
      body.innerHTML =
        '<div class="opt-list"></div>' +
        '<button type="button" class="btn btn-o btn-sm btn-add-opt">+ 新建选项</button>' +
        '<p class="hint">' +
        (t === "single" ? "点击选项左侧按钮标记唯一正确答案" : "勾选多个正确答案") +
        "</p>" +
        '<label class="lbl">本题分值</label><input type="number" class="q-score" value="2" min="0.5" step="0.5">';
      bindOptionList(block, t);
    } else if (t === "blank") {
      body.innerHTML =
        '<div class="blank-list"></div>' +
        '<button type="button" class="btn btn-o btn-sm btn-add-blank">+ 新建填空</button>' +
        '<p class="hint">每空单独设置参考答案与分值，本题总分为各空之和</p>' +
        '<div class="blank-total">本题总分：<strong class="blank-sum">0</strong> 分</div>';
      addBlankRow(block);
      block.querySelector(".btn-add-blank").addEventListener("click", function () {
        addBlankRow(block);
      });
    } else {
      body.innerHTML =
        '<label class="lbl">本题分值</label><input type="number" class="q-score" value="5" min="0.5" step="0.5">' +
        '<p class="hint">简答题需教师人工批改，学生提交后不会即时显示该题分数</p>';
    }
  }

  function bindOptionList(block, qtype) {
    var list = block.querySelector(".opt-list");
    var btn = block.querySelector(".btn-add-opt");
    btn.addEventListener("click", function () {
      var rows = list.querySelectorAll(".opt-row");
      if (rows.length >= 26) {
        alert("最多 26 个选项");
        return;
      }
      addOptionRow(block, qtype, "", false);
    });
    if (!list.children.length) {
      addOptionRow(block, qtype, "", false);
      addOptionRow(block, qtype, "", false);
    }
  }

  function addOptionRow(block, qtype, text, isAnswer) {
    var list = block.querySelector(".opt-list");
    var idx = list.querySelectorAll(".opt-row").length;
    if (idx >= 26) return;
    var letter = nextLetter(idx);
    var row = document.createElement("div");
    row.className = "opt-row";
    var inputType = qtype === "single" ? "radio" : "checkbox";
    var name = "correct-" + block.dataset.qid;
    row.innerHTML =
      '<label class="opt-ans">' +
      '<input type="' + inputType + '" name="' + name + '" value="' + letter + '"' +
      (isAnswer ? " checked" : "") + "> " + letter +
      "</label>" +
      '<input type="text" class="opt-text" placeholder="选项 ' + letter + ' 内容" value="' + esc(text) + '">' +
      '<button type="button" class="btn-del-opt" title="删除选项">×</button>';
    list.appendChild(row);
    row.querySelector(".btn-del-opt").addEventListener("click", function () {
      if (list.querySelectorAll(".opt-row").length <= 1) {
        alert("至少保留一个选项");
        return;
      }
      row.remove();
      relabelOptions(list);
    });
  }

  function relabelOptions(list) {
    list.querySelectorAll(".opt-row").forEach(function (row, i) {
      var letter = nextLetter(i);
      row.querySelector(".opt-ans").childNodes[1].textContent = " " + letter;
      row.querySelector(".opt-ans input").value = letter;
      row.querySelector(".opt-text").placeholder = "选项 " + letter + " 内容";
    });
  }

  function addBlankRow(block) {
    var list = block.querySelector(".blank-list");
    var n = list.querySelectorAll(".blank-row").length + 1;
    var row = document.createElement("div");
    row.className = "blank-row";
    row.innerHTML =
      '<span class="blank-label">空 ' + n + '</span>' +
      '<input type="text" class="blank-ans" placeholder="参考答案（多个用 | 分隔）">' +
      '<input type="number" class="blank-score" value="1" min="0.5" step="0.5" title="分值">' +
      '<span class="unit">分</span>' +
      '<button type="button" class="btn-del-blank">×</button>';
    list.appendChild(row);
    row.querySelector(".btn-del-blank").addEventListener("click", function () {
      if (list.querySelectorAll(".blank-row").length <= 1) {
        alert("至少保留一个填空");
        return;
      }
      row.remove();
      relabelBlanks(list);
      updateBlankSum(block);
    });
    row.querySelector(".blank-score").addEventListener("input", function () {
      updateBlankSum(block);
    });
    updateBlankSum(block);
  }

  function relabelBlanks(list) {
    list.querySelectorAll(".blank-row").forEach(function (row, i) {
      row.querySelector(".blank-label").textContent = "空 " + (i + 1);
    });
  }

  function updateBlankSum(block) {
    var sum = 0;
    block.querySelectorAll(".blank-score").forEach(function (inp) {
      sum += parseFloat(inp.value) || 0;
    });
    var el = block.querySelector(".blank-sum");
    if (el) el.textContent = sum.toFixed(1).replace(/\.0$/, "");
  }

  function createBlock(container) {
    var qid = "q" + Date.now() + Math.random().toString(36).slice(2, 6);
    var div = document.createElement("div");
    div.className = "q-block";
    div.dataset.qid = qid;
    div.innerHTML =
      '<div class="q-head">' +
      '<strong class="q-num">题目</strong>' +
      '<select class="q-type">' +
      '<option value="single">单选题</option>' +
      '<option value="multi">多选题</option>' +
      '<option value="blank">填空题</option>' +
      '<option value="short">简答题</option>' +
      "</select>" +
      '<button type="button" class="btn btn-d btn-sm btn-del-q">删除题目</button>' +
      "</div>" +
      '<textarea class="q-content" rows="2" placeholder="题干"></textarea>' +
      '<div class="q-body"></div>';
    container.appendChild(div);
    div.querySelector(".btn-del-q").addEventListener("click", function () {
      if (!confirm("确定删除本题？")) return;
      div.remove();
      renumberBlocks(container);
    });
    bindTypeSwitch(div);
    renderBody(div);
    renumberBlocks(container);
    return div;
  }

  function collectFromBlock(block) {
    var qtype = block.querySelector(".q-type").value;
    var content = block.querySelector(".q-content").value.trim();
    if (!content) throw new Error("请填写题干");

    if (qtype === "single" || qtype === "multi") {
      var rows = block.querySelectorAll(".opt-row");
      var options = [];
      var correct = [];
      rows.forEach(function (row, i) {
        var letter = nextLetter(i);
        var text = row.querySelector(".opt-text").value.trim();
        if (!text) throw new Error("请填写选项 " + letter + " 的内容");
        options.push(text);
        if (row.querySelector(".opt-ans input").checked) correct.push(letter);
      });
      if (!correct.length) throw new Error("请设置正确答案");
      if (qtype === "single" && correct.length > 1) throw new Error("单选题只能有一个正确答案");
      var score = parseFloat(block.querySelector(".q-score").value) || 0;
      if (score <= 0) throw new Error("请设置本题分值");
      return {
        qtype: qtype,
        content: content,
        options: options,
        answer_key: { correct: qtype === "single" ? correct[0] : correct },
        score: score,
      };
    }

    if (qtype === "blank") {
      var blanks = [];
      block.querySelectorAll(".blank-row").forEach(function (row, i) {
        var raw = row.querySelector(".blank-ans").value.trim();
        if (!raw) throw new Error("请填写第 " + (i + 1) + " 空的参考答案");
        var acceptable = raw.split("|").map(function (s) { return s.trim(); }).filter(Boolean);
        var bscore = parseFloat(row.querySelector(".blank-score").value) || 0;
        if (bscore <= 0) throw new Error("请设置第 " + (i + 1) + " 空的分值");
        blanks.push({ acceptable: acceptable, score: bscore });
      });
      var total = blanks.reduce(function (s, b) { return s + b.score; }, 0);
      return {
        qtype: "blank",
        content: content,
        options: null,
        answer_key: { blanks: blanks },
        score: total,
      };
    }

    var shortScore = parseFloat(block.querySelector(".q-score").value) || 0;
    if (shortScore <= 0) throw new Error("请设置简答题分值");
    return {
      qtype: "short",
      content: content,
      options: null,
      answer_key: {},
      score: shortScore,
    };
  }

  function collectAll(container) {
    var blocks = container.querySelectorAll(".q-block");
    if (!blocks.length) throw new Error("请至少添加一道题目");
    var out = [];
    blocks.forEach(function (b) {
      out.push(collectFromBlock(b));
    });
    return out;
  }

  function initDatetimeDefaults() {
    var start = document.getElementById("exam-start");
    var end = document.getElementById("exam-end");
    if (!start || !end) return;
    var now = new Date();
    now.setMinutes(now.getMinutes() - now.getMinutes() % 5);
    var pad = function (n) { return String(n).padStart(2, "0"); };
    var toLocal = function (d) {
      return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) +
        "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
    };
    if (!start.value) start.value = toLocal(now);
    if (!end.value) {
      var later = new Date(now.getTime() + 30 * 60000);
      end.value = toLocal(later);
    }
  }

  function bindDurationShortcuts() {
    document.querySelectorAll("[data-duration]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var start = document.getElementById("exam-start");
        var end = document.getElementById("exam-end");
        if (!start.value) initDatetimeDefaults();
        var base = new Date(start.value);
        if (isNaN(base)) base = new Date();
        var mins = parseInt(btn.dataset.duration, 10);
        var later = new Date(base.getTime() + mins * 60000);
        var pad = function (n) { return String(n).padStart(2, "0"); };
        end.value = later.getFullYear() + "-" + pad(later.getMonth() + 1) + "-" + pad(later.getDate()) +
          "T" + pad(later.getHours()) + ":" + pad(later.getMinutes());
      });
    });
  }

  function formatDatetimeForApi(localVal) {
    if (!localVal) return "";
    return localVal.replace("T", " ") + ":00";
  }

  return {
    createBlock: createBlock,
    collectAll: collectAll,
    initDatetimeDefaults: initDatetimeDefaults,
    bindDurationShortcuts: bindDurationShortcuts,
    formatDatetimeForApi: formatDatetimeForApi,
  };
  })();
} catch (err) {
  console.error("classroom-exam-admin-questions.js: load failed", err);
  window.ClassroomQuestionEditor = null;
}
