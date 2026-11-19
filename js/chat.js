(function () {
  var listEl = document.getElementById("writingList");
  var postEl = document.getElementById("chatPost");

  function qs(name) {
    var m = /(?:^|[?&])id=([^&]*)/.exec(window.location.search);
    return m ? decodeURIComponent(m[1].replace(/\+/g, " ")) : "";
  }

  function pathChatId() {
    var m = window.location.pathname.match(/^\/writing\/([^/]+?)\/?$/);
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
      window.location.replace("/writing/" + encodeURIComponent(id));
    } else {
      window.location.replace("/#writing");
    }
    return true;
  }

  function isEn() {
    return document.documentElement.getAttribute("lang") === "en";
  }

  function setText(id, zh, en) {
    var el = document.getElementById(id);
    if (!el) return;
    el.innerHTML =
      '<span class="zh">' + window.escapeHtml(zh) + "</span>" +
      '<span class="en-only">' + window.escapeHtml(en || zh) + "</span>";
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
      listEl.innerHTML = '<p class="lede zh">还没有对话。</p><p class="lede en-only">No conversations yet.</p>';
      return;
    }
    listEl.innerHTML = chats.map(function (c) {
      var href = "/writing/" + encodeURIComponent(c.id);
      var title = window.escapeHtml(c.title || "");
      var titleEn = window.escapeHtml(c.title_en || c.title || "");
      var sum = window.escapeHtml(c.summary || "");
      var sumEn = window.escapeHtml(c.summary_en || c.summary || "");
      var date = window.escapeHtml(c.date || "");
      return (
        '<a class="card article" href="' + href + '">' +
          '<div class="meta">' +
            '<span class="zh">对话</span><span class="en-only">Conversation</span>' +
            (date ? '<time datetime="' + date + '">' + date + "</time>" : "") +
          "</div>" +
          "<h3><span class=\"zh\">" + title + "</span><span class=\"en-only\">" + titleEn + "</span></h3>" +
          '<p class="zh">' + sum + "</p>" +
          '<p class="en-only">' + sumEn + "</p>" +
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
    var title = chat.title || "";
    var titleEn = chat.title_en || title;
    document.title = title + " · 匡子闲";
    var desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute("content", chat.summary || title);
    var ogt = document.querySelector('meta[property="og:title"]');
    if (ogt) ogt.setAttribute("content", title + " · 匡子闲");
    var ogd = document.querySelector('meta[property="og:description"]');
    if (ogd) ogd.setAttribute("content", chat.summary || title);
    var twt = document.querySelector('meta[name="twitter:title"]');
    if (twt) twt.setAttribute("content", title + " · 匡子闲");
    var twd = document.querySelector('meta[name="twitter:description"]');
    if (twd) twd.setAttribute("content", chat.summary || title);
    var pageUrl = "https://kuangzixian.pages.dev/writing/" + encodeURIComponent(chat.id);
    var ogu = document.querySelector('meta[property="og:url"]');
    if (ogu) ogu.setAttribute("content", pageUrl);
    var canon = document.querySelector('link[rel="canonical"]');
    if (canon) canon.setAttribute("href", pageUrl);
    var mdLink = document.getElementById("mdAlternate");
    if (mdLink) mdLink.setAttribute("href", "/writing/" + encodeURIComponent(chat.id) + ".md");

    var promptBlock = "";
    if (chat.prompt) {
      var kind = chat.prompt_kind || "prompt";
      var labelZh = kind === "question" ? "我的问题" : "我的 Prompt";
      var labelEn = kind === "question" ? "My question" : "My prompt";
      promptBlock =
        '<aside class="prompt-block">' +
          '<p class="prompt-kicker"><span class="zh">' + labelZh + '</span><span class="en-only">' + labelEn + "</span></p>" +
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
          '<p class="turn-role"><span class="zh">' + window.escapeHtml(lab.zh) + "</span>" +
          '<span class="en-only">' + window.escapeHtml(lab.en) + "</span></p>" +
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
      '<p class="post-back"><a href="/#writing"><span class="zh">← 返回文章列表</span><span class="en-only">← Back to writing</span></a></p>' +
      '<header class="post-head">' +
        '<p class="kicker">Writing</p>' +
        "<h1><span class=\"zh\">" + window.escapeHtml(title) + "</span>" +
        "<span class=\"en-only\">" + window.escapeHtml(titleEn) + "</span></h1>" +
        '<div class="meta">' +
          (date ? '<time datetime="' + window.escapeHtml(date) + '">' + window.escapeHtml(date) + "</time>" : "") +
          '<span class="zh">匡子闲 与 GPT</span><span class="en-only">匡子闲 and GPT</span>' +
        "</div>" +
        tagsHtml(chat.tags) +
      "</header>" +
      promptBlock +
      '<div class="thread">' + thread + "</div>" +
      (sources.length ? '<p class="post-source">' + sources.join(" · ") + "</p>" : "");
  }

  function renderMissing() {
    if (!postEl) return;
    document.title = "未找到 · 匡子闲";
    postEl.innerHTML =
      '<p class="post-back"><a href="/#writing"><span class="zh">← 返回文章列表</span><span class="en-only">← Back to writing</span></a></p>' +
      '<p class="lede zh">没有找到这篇对话。</p>' +
      '<p class="lede en-only">This conversation could not be found.</p>';
  }

  function hasStaticPost() {
    return !!(postEl && postEl.getAttribute("data-rendered") === "static" && postEl.querySelector(".thread"));
  }

  function init(data) {
    var chats = (data && data.chats) || [];
    if (listEl) renderList(chats);
    if (postEl) {
      var id = currentChatId();
      var found = null;
      chats.some(function (c) { if (c.id === id) { found = c; return true; } return false; });
      if (found) renderPost(found);
      else if (!hasStaticPost()) renderMissing();
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
          '<p class="post-back"><a href="/#writing"><span class="zh">← 返回文章列表</span><span class="en-only">← Back to writing</span></a></p>' +
          '<p class="lede zh">对话数据加载失败，请稍后再试。</p>' +
          '<p class="lede en-only">Failed to load the conversation. Please try again later.</p>';
      }
    });
})();
