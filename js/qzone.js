(function () {
  var root = document.documentElement;
  var TAB_IDS = ["home", "writing", "reading", "music", "boardgames", "sites", "guestbook", "profile"];
  var HASH_MAP = {
    "": "home",
    top: "home",
    home: "home",
    writing: "writing",
    logs: "writing",
    log: "writing",
    reading: "reading",
    music: "music",
    boardgames: "boardgames",
    games: "boardgames",
    sites: "sites",
    links: "sites",
    friends: "sites",
    guestbook: "guestbook",
    profile: "profile",
    projects: "profile",
    social: "profile",
    ideas: "home"
  };
  var SKIN_COLORS = { blue: "#4a9de0", pink: "#ee7aa8", night: "#1b1530" };

  function hashName() {
    var raw = (location.hash || "#home").replace(/^#/, "").split("?")[0];
    return raw;
  }

  function tabFromHash() {
    var raw = hashName();
    return HASH_MAP[raw] || (TAB_IDS.indexOf(raw) >= 0 ? raw : "home");
  }

  function currentTab() {
    return root.getAttribute("data-tab") || "home";
  }

  function showTab(tab, opts) {
    opts = opts || {};
    if (TAB_IDS.indexOf(tab) < 0) tab = "home";
    root.setAttribute("data-tab", tab);
    document.querySelectorAll(".qz-tab").forEach(function (btn) {
      var on = btn.getAttribute("data-tab") === tab;
      btn.setAttribute("aria-selected", on ? "true" : "false");
      btn.classList.toggle("is-on", on);
    });
    document.querySelectorAll(".tab-panel").forEach(function (panel) {
      var on = panel.id === tab;
      panel.hidden = !on;
      panel.setAttribute("aria-hidden", on ? "false" : "true");
    });
    try {
      window.dispatchEvent(new CustomEvent("qzone:tabchange", { detail: { tab: tab } }));
    } catch (e) {}
    if (opts.scroll !== false) {
      var targetId = hashName();
      var el = (targetId && document.getElementById(targetId) && targetId !== tab)
        ? document.getElementById(targetId)
        : document.getElementById("qzTabs") || document.querySelector(".qz-content");
      if (el && opts.scroll !== "none") {
        if (opts.scroll !== "instant") el.scrollIntoView({ block: "start", behavior: "smooth" });
      }
    }
  }

  function canonicalizeAliasHash() {
    var raw = hashName();
    if (raw !== "links" && raw !== "friends") return;
    var next = "#sites";
    var q = (location.hash || "").indexOf("?");
    if (q >= 0) next += location.hash.slice(q);
    try {
      history.replaceState(null, "", location.pathname + location.search + next);
    } catch (e) {
      location.hash = next;
    }
  }

  function applyHash(opts) {
    canonicalizeAliasHash();
    showTab(tabFromHash(), opts);
  }

  applyHash({ scroll: "none" });
  window.addEventListener("hashchange", function () {
    applyHash({ scroll: true });
  });

  document.querySelectorAll(".qz-tab").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      var tab = btn.getAttribute("data-tab");
      if (!tab) return;
      if (btn.tagName === "A") {
        // let hash update; hashchange will run
        return;
      }
      e.preventDefault();
      if (location.hash !== "#" + tab) {
        location.hash = tab;
      } else {
        showTab(tab, { scroll: true });
      }
    });
  });

  /* skins */
  function setSkin(skin, persist) {
    if (skin !== "blue" && skin !== "pink" && skin !== "night") skin = "blue";
    root.setAttribute("data-skin", skin);
    root.setAttribute("data-theme", skin === "night" ? "dark" : "light");
    var meta = document.getElementById("themeColor");
    if (meta) meta.setAttribute("content", SKIN_COLORS[skin] || SKIN_COLORS.blue);
    document.querySelectorAll("[data-skin-set]").forEach(function (btn) {
      btn.classList.toggle("is-on", btn.getAttribute("data-skin-set") === skin);
    });
    if (persist) {
      try {
        localStorage.setItem("kuang-skin", skin);
        localStorage.setItem("kuang-theme", skin === "night" ? "dark" : "light");
      } catch (e) {}
    }
  }

  setSkin(root.getAttribute("data-skin") || "blue", false);
  document.querySelectorAll("[data-skin-set]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setSkin(btn.getAttribute("data-skin-set"), true);
    });
  });

  var themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var order = ["blue", "pink", "night"];
      var cur = root.getAttribute("data-skin") || "blue";
      var next = order[(order.indexOf(cur) + 1) % order.length];
      setSkin(next, true);
    });
  }

  /* compact settings menu (mobile) */
  var menuBtn = document.getElementById("qzMenuBtn");
  var menuPanel = document.getElementById("qzMenuPanel");
  function setMenuOpen(open) {
    if (!menuBtn || !menuPanel) return;
    menuPanel.hidden = !open;
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    menuBtn.classList.toggle("is-on", open);
  }
  if (menuBtn && menuPanel) {
    menuBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      setMenuOpen(menuPanel.hidden);
    });
    document.addEventListener("click", function (e) {
      if (!menuPanel.hidden && !menuPanel.contains(e.target) && e.target !== menuBtn) {
        setMenuOpen(false);
      }
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    setMenuOpen(false);
  });

  window.qzoneShowTab = showTab;
})();
