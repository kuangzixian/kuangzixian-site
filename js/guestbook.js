(function () {
  var form = document.getElementById("gbForm");
  var listEl = document.getElementById("gbList");
  var statusEl = document.getElementById("gbStatus");
  var nickInput = document.getElementById("gbNickname");
  var contentInput = document.getElementById("gbContent");
  var nickCount = document.getElementById("gbNickCount");
  var contentCount = document.getElementById("gbContentCount");
  var submitBtn = document.getElementById("gbSubmit");
  if (!form || !listEl) return;

  var MESSAGES = {
    zh: {
      empty: "还没有留言，来写第一条吧。",
      unavailable: "留言板暂时连不上，过一会儿再试试。",
      invalid_nickname: "昵称需要 1 到 20 个字。",
      invalid_content: "留言需要 1 到 500 个字。",
      has_link: "为了减少广告，留言里先不要放链接。",
      spam: "这条看起来像广告，没有发出去。",
      too_fast: "写得有点勤，请过几分钟再留。",
      network: "网络不太稳，请稍后再试。",
      sent: "已记下。",
      sending: "正在发送…",
      justNow: "刚刚",
      minutes: function (n) { return n + " 分钟前"; },
      hours: function (n) { return n + " 小时前"; },
      days: function (n) { return n + " 天前"; },
    },
    en: {
      empty: "No notes yet — be the first to write one.",
      unavailable: "The guestbook is temporarily unavailable. Please try again later.",
      invalid_nickname: "Nickname must be 1 to 20 characters.",
      invalid_content: "The note must be 1 to 500 characters.",
      has_link: "Please leave the note without links, to keep spam down.",
      spam: "This looked like an ad, so it was not posted.",
      too_fast: "That is a bit quick. Please wait a few minutes.",
      network: "The network hiccuped. Please try again.",
      sent: "Saved.",
      sending: "Sending…",
      justNow: "just now",
      minutes: function (n) { return n + " min ago"; },
      hours: function (n) { return n + " hr ago"; },
      days: function (n) { return n + " days ago"; },
    },
  };

  function isEn() {
    return document.documentElement.getAttribute("lang") === "en";
  }

  function t() {
    return isEn() ? MESSAGES.en : MESSAGES.zh;
  }

  function charLen(s) {
    return Array.from(s || "").length;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function relTime(iso) {
    var dict = t();
    var ts = Date.parse(iso);
    if (!isFinite(ts)) return "";
    var sec = Math.round((Date.now() - ts) / 1000);
    if (sec < 45) return dict.justNow;
    if (sec < 3600) return dict.minutes(Math.max(1, Math.round(sec / 60)));
    if (sec < 86400) return dict.hours(Math.max(1, Math.round(sec / 3600)));
    return dict.days(Math.max(1, Math.round(sec / 86400)));
  }

  function setStatus(kind, code) {
    if (!statusEl) return;
    var dict = t();
    var text = "";
    if (kind === "ok") text = dict.sent;
    else if (kind === "pending") text = dict.sending;
    else if (kind === "clear") text = "";
    else text = dict[code] || dict.network;
    statusEl.textContent = text;
    statusEl.className = "gb-status" + (kind ? " is-" + kind : "");
  }

  function updateCounts() {
    if (nickCount) nickCount.textContent = charLen(nickInput && nickInput.value) + "/20";
    if (contentCount) contentCount.textContent = charLen(contentInput && contentInput.value) + "/500";
  }

  function itemHtml(msg, pending) {
    var name = escapeHtml(msg.nickname || "");
    var body = escapeHtml(msg.content || "").replace(/\n/g, "<br>");
    var time = escapeHtml(relTime(msg.created_at));
    var idAttr = msg.id != null ? ' data-id="' + escapeHtml(String(msg.id)) + '"' : "";
    var pendingClass = pending ? " is-pending" : "";
    var floor = '<span class="gb-floor"></span>';
    return (
      '<article class="card gb-item' + pendingClass + '"' + idAttr +
        ' data-created="' + escapeHtml(msg.created_at || "") + '">' +
        '<header class="gb-item-head">' +
          floor +
          '<strong class="gb-name">' + name + "</strong>" +
          '<time class="gb-time" datetime="' + escapeHtml(msg.created_at || "") + '">' + time + "</time>" +
        "</header>" +
        '<p class="gb-body">' + body + "</p>" +
      "</article>"
    );
  }

  function refreshTimes() {
    listEl.querySelectorAll(".gb-item[data-created]").forEach(function (el) {
      var time = el.querySelector(".gb-time");
      if (time) time.textContent = relTime(el.getAttribute("data-created"));
    });
    var empty = listEl.querySelector(".gb-empty, .gb-unavailable");
    if (empty) {
      if (empty.classList.contains("gb-unavailable")) {
        empty.textContent = t().unavailable;
      } else {
        empty.textContent = t().empty;
      }
    }
    if (statusEl && statusEl.classList.contains("is-error")) {
      var code = statusEl.getAttribute("data-code");
      if (code) statusEl.textContent = t()[code] || t().network;
    }
  }

  function showEmpty() {
    listEl.innerHTML = '<p class="gb-empty lede">' + escapeHtml(t().empty) + "</p>";
  }

  function showUnavailable() {
    listEl.innerHTML = '<p class="gb-unavailable lede">' + escapeHtml(t().unavailable) + "</p>";
  }

  function assignFloors() {
    var items = listEl.querySelectorAll(".gb-item");
    var n = items.length;
    // List is newest-first (Qzone style). Oldest at the bottom is 第1楼;
    // the newest at the top gets the highest floor number.
    items.forEach(function (el, i) {
      var floor = n - i;
      el.setAttribute("data-floor", String(floor));
      var span = el.querySelector(".gb-floor");
      if (!span) return;
      span.innerHTML = '<span class="zh">第' + floor + '楼</span><span class="en-only">Floor ' + floor + "</span>";
    });
  }

  function renderList(messages) {
    if (!messages || !messages.length) {
      showEmpty();
      return;
    }
    listEl.innerHTML = messages.map(function (m) { return itemHtml(m, false); }).join("");
    assignFloors();
  }

  function loadList() {
    return fetch("/api/messages", { headers: { accept: "application/json" } })
      .then(function (res) {
        if (!res.ok) throw new Error("bad status");
        return res.json();
      })
      .then(function (data) {
        if (!data || !data.ok) throw new Error("bad payload");
        renderList(data.messages || []);
      })
      .catch(function () {
        showUnavailable();
      });
  }

  function submit(ev) {
    ev.preventDefault();
    var nickname = (nickInput && nickInput.value) || "";
    var content = (contentInput && contentInput.value) || "";
    var hp = (form.querySelector('[name="website"]') || {}).value || "";
    var pending = {
      nickname: nickname.trim(),
      content: content.trim(),
      created_at: new Date().toISOString(),
    };
    var localCheck = charLen(pending.nickname.replace(/\s+/g, " ").trim());
    if (localCheck < 1 || localCheck > 20) {
      setStatus("error", "invalid_nickname");
      if (statusEl) statusEl.setAttribute("data-code", "invalid_nickname");
      return;
    }
    var contentLen = charLen(pending.content);
    if (contentLen < 1 || contentLen > 500) {
      setStatus("error", "invalid_content");
      if (statusEl) statusEl.setAttribute("data-code", "invalid_content");
      return;
    }

    var empty = listEl.querySelector(".gb-empty, .gb-unavailable");
    if (empty) empty.remove();
    var temp = document.createElement("div");
    temp.innerHTML = itemHtml(pending, true);
    var card = temp.firstElementChild;
    listEl.insertBefore(card, listEl.firstChild);
    assignFloors();
    setStatus("pending");
    if (statusEl) statusEl.removeAttribute("data-code");
    if (submitBtn) submitBtn.disabled = true;

    fetch("/api/messages", {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({
        nickname: pending.nickname,
        content: pending.content,
        website: hp,
      }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { res: res, data: data };
        }).catch(function () {
          return { res: res, data: null };
        });
      })
      .then(function (pack) {
        var data = pack.data || {};
        if (pack.res.status === 201 && data.ok && data.message) {
          var next = document.createElement("div");
          next.innerHTML = itemHtml(data.message, false);
          card.replaceWith(next.firstElementChild);
          assignFloors();
          form.reset();
          updateCounts();
          setStatus("ok");
          return;
        }
        if (pack.res.status === 201 && data.ok && data.ignored) {
          card.remove();
          assignFloors();
          form.reset();
          updateCounts();
          setStatus("ok");
          return;
        }
        card.remove();
        if (!listEl.querySelector(".gb-item")) showEmpty();
        else assignFloors();
        var code = data.error || (pack.res.status === 429 ? "too_fast" : "network");
        setStatus("error", code);
        if (statusEl) statusEl.setAttribute("data-code", code);
      })
      .catch(function () {
        card.remove();
        if (!listEl.querySelector(".gb-item")) showEmpty();
        else assignFloors();
        setStatus("error", "network");
        if (statusEl) statusEl.setAttribute("data-code", "network");
      })
      .then(function () {
        if (submitBtn) submitBtn.disabled = false;
      });
  }

  if (nickInput) nickInput.addEventListener("input", updateCounts);
  if (contentInput) contentInput.addEventListener("input", updateCounts);
  form.addEventListener("submit", submit);
  updateCounts();
  loadList();

  try {
    new MutationObserver(refreshTimes).observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang"],
    });
  } catch (e) {}
  window.setInterval(refreshTimes, 60000);
})();
