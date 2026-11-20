(function () {
  var listEl = document.getElementById("writingList");
  var postEl = document.getElementById("chatPost");

  function qs(name) {
    var m = /(?:^|[?&])id=([^&]*)/.exec(window.location.search);
    return m ? decodeURIComponent(m[1].replace(/\+/g, " ")) : "";
  }

  function pathChatId() {
    var m = window.location.pathname.match(/^(?:\/(?:en|es|ko|ja))?\/writing\/([^/]+?)\/?$/);
    if (!m) return "";
    var id = decodeURIComponent(m[1]);
    if (/\.(md|html)$/i.test(id)) return "";
    return id;
  }

  function currentChatId() {
    return pathChatId() || qs("id");
  }

  function maybeRedirectLegacyChat() {
    var path = window.location.pathname;
    var isLegacy = path === "/chat" || path === "/chat.html" || /\/chat\.html$/.test(path);
    if (!isLegacy) return false;
    var id = qs("id");
    if (id) {
      var loc = window.KUANG_I18N;
      var dest = "/writing/" + encodeURIComponent(id);
      if (loc && loc.localizePath) dest = loc.localizePath(dest, loc.locale || "zh");
      window.location.replace(dest);
    } else {
      var loc2 = window.KUANG_I18N;
      var home = "/#writing";
      if (loc2 && loc2.localizePath) home = loc2.localizePath("/", loc2.locale || "zh") + "#writing";
      window.location.replace(home);
    }
    return true;
  }

  function I() { return window.KUANG_I18N || {}; }
  function tr(key) { return (I().t && I().t(key)) || key; }
  function loc() { return I().locale || "zh"; }
  function pickField(obj, base) {
    var L = loc();
    if (L === "zh") return obj[base] || "";
    return obj[base + "_" + L] || obj[base + "_en"] || obj[base] || "";
  }
  function writingHref(id) {
    var path = "/writing/" + encodeURIComponent(id);
    if (I().localizePath) return I().localizePath(path, loc());
    return path;
  }
  function writingListHref() {
    if (I().localizePath) return I().localizePath("/", loc()) + "#writing";
    return "/#writing";
  }

  function tagsHtml(tags) {
    if (!tags || !tags.length) return "";
    return '<div class="article-tags">' + tags.map(function (t) {
      return '<span class="pill">' + window.escapeHtml(t) + "</span>";
    }).join("") + "</div>";
  }

  function renderList(chats) {
    if (!listEl) return;
    if (!chats.length) {
      listEl.innerHTML = '<p class="lede">' + window.escapeHtml(tr("noConversations")) + "</p>";
      return;
    }
    listEl.innerHTML = chats.map(function (c) {
      var href = writingHref(c.id);
      var title = window.escapeHtml(pickField(c, "title"));
      var sum = window.escapeHtml(pickField(c, "summary"));
      var date = c.date || "";
      var dateLabel = date;
      if (date && I().formatDate) dateLabel = I().formatDate(date);
      return (
        '<a class="card article" href="' + href + '">' +
          '<div class="meta">' +
            window.escapeHtml(tr("conversation")) +
            (date ? '<time datetime="' + window.escapeHtml(date) + '">' + window.escapeHtml(dateLabel) + "</time>" : "") +
          "</div>" +
          "<h3>" + title + "</h3>" +
          "<p>" + sum + "</p>" +
          tagsHtml(c.tags) +
        "</a>"
      );
    }).join("");
    listEl.querySelectorAll(".article").forEach(function (el) {
      el.classList.add("reveal", "is-in");
    });
  }

  function roleLabel(msg) {
    if (msg.role === "assistant") {
      return { zh: msg.name || "GPT", en: msg.name || "GPT", cls: "is-assistant" };
    }
    return { zh: msg.name || "匡子闲", en: msg.name || "匡子闲", cls: "is-user" };
  }

  function renderPost(chat) {
    if (!postEl) return;
    var date = chat.date || "";
    var title = pickField(chat, "title");
    var summary = pickField(chat, "summary") || title;
    document.title = title + " · 匡子闲";
    var desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute("content", summary);
    var ogt = document.querySelector('meta[property="og:title"]');
    if (ogt) ogt.setAttribute("content", title + " · 匡子闲");
    var ogd = document.querySelector('meta[property="og:description"]');
    if (ogd) ogd.setAttribute("content", summary);
    var twt = document.querySelector('meta[name="twitter:title"]');
    if (twt) twt.setAttribute("content", title + " · 匡子闲");
    var twd = document.querySelector('meta[name="twitter:description"]');
    if (twd) twd.setAttribute("content", summary);
    var pageUrl = "https://kuangzixian.pages.dev" + writingHref(chat.id);
    var ogu = document.querySelector('meta[property="og:url"]');
    if (ogu) ogu.setAttribute("content", pageUrl);
    var canon = document.querySelector('link[rel="canonical"]');
    if (canon) canon.setAttribute("href", pageUrl);
    var mdLink = document.getElementById("mdAlternate");
    if (mdLink) mdLink.setAttribute("href", "/writing/" + encodeURIComponent(chat.id) + ".md");

    var promptBlock = "";
    if (chat.prompt) {
      var kind = chat.prompt_kind || "prompt";
      var label = tr(kind === "question" ? "myQuestion" : "myPrompt");
      promptBlock =
        '<aside class="prompt-block">' +
          '<p class="prompt-kicker">' + window.escapeHtml(label) + "</p>" +
          '<div class="prompt-body">' + window.renderMarkdown(chat.prompt) + "</div>" +
        "</aside>";
    }

    var promptText = (chat.prompt || "").trim();
    var messages = (chat.messages || []).filter(function (m, idx) {
      if (idx === 0 && m.role === "user" && promptText && (m.content || "").trim() === promptText) {
        return false;
      }
      return true;
    });

    var thread = messages.map(function (m) {
      var lab = roleLabel(m);
      return (
        '<section class="turn ' + lab.cls + '">' +
          '<p class="turn-role">' + window.escapeHtml(lab.zh) + "</p>" +
          '<div class="turn-body md">' + window.renderMarkdown(m.content || "") + "</div>" +
        "</section>"
      );
    }).join("");

    var sources = [];
    if (chat.source_url) {
      sources.push(
        '<a href="' + window.escapeHtml(chat.source_url) + '" rel="noopener noreferrer">' +
        '<span class="zh">原始 ChatGPT 分享链接</span>' +
        '<span class="en-only">Original ChatGPT share link</span></a>'
      );
    }
    if (chat.prompt_url) {
      sources.push(
        '<a href="' + window.escapeHtml(chat.prompt_url) + '" rel="noopener noreferrer">' +
        '<span class="zh">原始 Prompt 分享链接</span>' +
        '<span class="en-only">Original prompt share link</span></a>'
      );
    }

    postEl.innerHTML =
      '<p class="post-back"><a href="' + writingListHref() + '">' + window.escapeHtml(tr("backWriting")) + "</a></p>" +
      '<header class="post-head">' +
        '<p class="kicker">Writing</p>' +
        "<h1>" + window.escapeHtml(title) + "</h1>" +
        '<div class="meta">' +
          (date ? '<time datetime="' + window.escapeHtml(date) + '">' + window.escapeHtml((I().formatDate && I().formatDate(date)) || date) + "</time>" : "") +
          "<span>" + window.escapeHtml(tr("withGpt")) + "</span>" +
        "</div>" +
        tagsHtml(chat.tags) +
      "</header>" +
      promptBlock +
      '<div class="thread">' + thread + "</div>" +
      (sources.length ? '<p class="post-source">' + sources.join(" · ") + "</p>" : "");
  }

  function renderMissing() {
    if (!postEl) return;
    document.title = "404 · 匡子闲";
    postEl.innerHTML =
      '<p class="post-back"><a href="' + writingListHref() + '">' + window.escapeHtml(tr("backWriting")) + "</a></p>" +
      '<p class="lede">' + window.escapeHtml(tr("notFound")) + "</p>";
  }

  function hasStaticPost() {
    return !!(postEl && postEl.getAttribute("data-rendered") === "static" && postEl.querySelector(".thread"));
  }

  function init(data) {
    var chats = (data && data.chats) || [];
    if (listEl && listEl.getAttribute("data-static") !== "1") renderList(chats);
    if (postEl && !hasStaticPost()) {
      var id = currentChatId();
      var found = null;
      chats.some(function (c) { if (c.id === id) { found = c; return true; } return false; });
      if (found) renderPost(found);
      else renderMissing();
    }
  }

  if (maybeRedirectLegacyChat()) return;

  fetch("/data/chats.json")
    .then(function (res) {
      if (!res.ok) throw new Error("chats.json " + res.status);
      return res.json();
    })
    .then(init)
    .catch(function () {
      if (listEl) {
        listEl.querySelectorAll(".article").forEach(function (el) {
          el.classList.add("reveal", "is-in");
        });
      }
      if (postEl && !hasStaticPost()) {
        postEl.innerHTML =
          '<p class="post-back"><a href="' + writingListHref() + '">' + window.escapeHtml(tr("backWriting")) + "</a></p>" +
          '<p class="lede">' + window.escapeHtml(tr("loadFailed")) + "</p>";
      }
    });
})();
