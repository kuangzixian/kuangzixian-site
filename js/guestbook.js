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

  function I() { return window.KUANG_I18N || {}; }

  function t() {
    var tr = I().t || function (k) { return k; };
    return {
      empty: tr("gbEmpty"),
      unavailable: tr("gbUnavailable"),
      invalid_nickname: tr("gbInvalidNickname"),
      invalid_content: tr("gbInvalidContent"),
      has_link: tr("gbHasLink"),
      spam: tr("gbSpam"),
      too_fast: tr("gbTooFast"),
      network: tr("gbNetwork"),
      sent: tr("gbSent"),
      sending: tr("gbSending"),
      justNow: tr("justNow"),
      minutes: function (n) { return tr("minutesAgo", { n: n }); },
      hours: function (n) { return tr("hoursAgo", { n: n }); },
      days: function (n) { return tr("daysAgo", { n: n }); },
    };
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
      span.textContent = (I().t && I().t("gbFloor", { n: floor })) || ("Floor " + floor);
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
