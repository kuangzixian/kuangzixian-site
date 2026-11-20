(function () {
  var root = document.documentElement;
  var I18N = window.KUANG_I18N || {};
  var themeToggle = document.getElementById("themeToggle");
  var header = document.querySelector(".site-header");
  var themeColorMeta = document.getElementById("themeColor");
  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {}

  function isEn() {
    return (I18N.locale || root.getAttribute("lang") || "zh") === "en" || root.getAttribute("lang") === "en";
  }

  if (I18N.initSwitcher) I18N.initSwitcher();

  window.addEventListener("scroll", function () {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 8);
  }, { passive: true });

  var more = document.getElementById("shelfMore");
  var grid = document.getElementById("shelfGrid");
  if (more && grid) {
    more.addEventListener("click", function () {
      grid.querySelectorAll(".shelf-card.is-hidden").forEach(function (el) {
        el.classList.remove("is-hidden");
      });
      more.parentElement.classList.add("hidden");
    });
  }
  document.querySelectorAll("[data-shelf-filter]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var cat = btn.getAttribute("data-shelf-filter");
      document.querySelectorAll("[data-shelf-filter]").forEach(function (b) { b.classList.remove("is-on"); });
      btn.classList.add("is-on");
      var cards = grid ? grid.querySelectorAll(".shelf-card") : [];
      cards.forEach(function (card) {
        var match = cat === "all" || card.getAttribute("data-cat") === cat;
        card.classList.toggle("is-filtered", !match);
        if (match) card.classList.remove("is-hidden");
      });
      if (more && more.parentElement) more.parentElement.classList.add("hidden");
    });
  });

  /* theme */
  function currentTheme() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function refreshThemeLabel() {
    if (!themeToggle) return;
    var dark = currentTheme() === "dark";
    var labels = {
      zh: dark ? "切换到浅色主题" : "切换到深色主题",
      en: dark ? "Switch to light theme" : "Switch to dark theme",
      es: dark ? "Cambiar a tema claro" : "Cambiar a tema oscuro",
      ko: dark ? "밝은 테마로 전환" : "어두운 테마로 전환",
      ja: dark ? "ライトテーマに切り替え" : "ダークテーマに切り替え"
    };
    var loc = (I18N.locale || "zh");
    themeToggle.setAttribute("aria-label", labels[loc] || labels.en);
  }

  function setTheme(theme, persist) {
    var next = theme === "dark" ? "dark" : "light";
    root.setAttribute("data-theme", next);
    if (themeColorMeta) themeColorMeta.setAttribute("content", next === "dark" ? "#161310" : "#f3eee4");
    if (persist) {
      try { localStorage.setItem("kuang-theme", next); } catch (err) {}
    }
    refreshThemeLabel();
  }

  if (!root.getAttribute("data-theme")) {
    var savedTheme = null;
    try { savedTheme = localStorage.getItem("kuang-theme"); } catch (e) {}
    if (savedTheme !== "light" && savedTheme !== "dark") {
      try {
        savedTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      } catch (e) {
        savedTheme = "light";
      }
    }
    setTheme(savedTheme, false);
  } else {
    refreshThemeLabel();
  }

  if (themeToggle && !document.querySelector("[data-skin-set]")) {
    themeToggle.addEventListener("click", function () {
      setTheme(currentTheme() === "dark" ? "light" : "dark", true);
    });
  }

  /* typewriter on the space signature */
  var mottoTarget = document.querySelector(".qz-sign .type-target")
    || document.querySelector(".motto .type-target");
  if (mottoTarget) {
    var mottoText = mottoTarget.textContent.trim();
    if (!reduceMotion && mottoText) {
      mottoTarget.textContent = "";
      mottoTarget.classList.add("is-typing");
      var mi = 0;
      var step = function () {
        mi += 1;
        mottoTarget.textContent = mottoText.slice(0, mi);
        if (mi < mottoText.length) {
          window.setTimeout(step, 42);
        } else {
          mottoTarget.classList.remove("is-typing");
        }
      };
      window.setTimeout(step, 280);
    }
  }

  /* scroll reveal + count up + bar fill */
  var revealEls = document.querySelectorAll(
    ".hero, .hero-stats, .year-progress, .stat-grid, .draw-panel, .now-grid, .fin-grid, .feat-grid, .quote-stage, .note-book, .shelf-filters, .shelf-grid, .article, .thought, .project, .social, .section-head"
  );
  revealEls.forEach(function (el) { el.classList.add("reveal"); });

  var countEls = document.querySelectorAll("[data-count]");
  function formatCount(n, format) {
    n = Math.round(n);
    if (format === "comma" && I18N.formatNumber) return I18N.formatNumber(n);
    var s = String(n);
    if (format === "comma") s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return s;
  }
  function runCount(el) {
    if (el.getAttribute("data-counted")) return;
    el.setAttribute("data-counted", "1");
    var target = Number(el.getAttribute("data-count"));
    var format = el.getAttribute("data-format") || "";
    if (!isFinite(target)) return;
    if (reduceMotion) {
      el.textContent = formatCount(target, format);
      return;
    }
    var start = performance.now();
    var duration = 1100;
    var tick = function (now) {
      var t = Math.min(1, (now - start) / duration);
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = formatCount(target * eased, format);
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = formatCount(target, format);
    };
    requestAnimationFrame(tick);
  }

  var bars = document.querySelectorAll(".progress, .bar");
  if (!reduceMotion) {
    bars.forEach(function (el) { el.classList.add("is-pending"); });
  }
  function fillBars(rootEl) {
    (rootEl.matches && (rootEl.matches(".progress, .bar")) ? [rootEl] : rootEl.querySelectorAll(".progress, .bar")).forEach(function (el) {
      el.classList.remove("is-pending");
    });
  }

  function revealNow(el) {
    if (!el || el.classList.contains("is-in")) {
      if (el && el.hasAttribute("data-count")) runCount(el);
      return;
    }
    el.classList.add("is-in");
    if (el.hasAttribute("data-count")) runCount(el);
    el.querySelectorAll("[data-count]").forEach(runCount);
    fillBars(el);
  }

  function revealVisible() {
    var vh = window.innerHeight || 0;
    revealEls.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < vh - 4 && r.bottom > 4) revealNow(el);
    });
    countEls.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < vh - 4 && r.bottom > 4) runCount(el);
    });
  }

  if (reduceMotion) {
    revealEls.forEach(function (el) { el.classList.add("is-in"); });
    countEls.forEach(runCount);
  } else if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        revealNow(entry.target);
        io.unobserve(entry.target);
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -32px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
    countEls.forEach(function (el) { io.observe(el); });
    revealVisible();
    window.addEventListener("resize", revealVisible, { passive: true });
    window.addEventListener("scroll", revealVisible, { passive: true });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-in"); });
    countEls.forEach(runCount);
    bars.forEach(function (el) { el.classList.remove("is-pending"); });
  }

  /* random book + quote rotator */
  var play = window.KUANG_PLAY || { books: [], quotes: [] };
  var lastBookId = "";
  var drawBtn = document.getElementById("drawBook");
  var drawResult = document.getElementById("drawResult");

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function pickOne(list, avoidKey, keyName) {
    if (!list || !list.length) return null;
    if (list.length === 1) return list[0];
    var choice = list[Math.floor(Math.random() * list.length)];
    var guard = 0;
    while (keyName && choice[keyName] === avoidKey && guard < 8) {
      choice = list[Math.floor(Math.random() * list.length)];
      guard += 1;
    }
    return choice;
  }

  function quoteHTML(q) {
    if (!q) {
      return '<p class="tiny">' + escapeHtml((I18N.t && I18N.t("noHighlight")) || "No curated highlight for this title.") + "</p>";
    }
    var kind = (I18N.t && I18N.t(q.type === "thought" ? "thought" : "highlight")) || (q.type === "thought" ? "Thought" : "Highlight");
    var body = "";
    if (q.type === "thought" && q.quote) {
      body += "<blockquote>" + escapeHtml(q.quote) + "</blockquote>";
      body += '<p class="thought-line">' + escapeHtml(q.text) + "</p>";
    } else {
      body += "<blockquote>" + escapeHtml(q.text) + "</blockquote>";
    }
    return '<span class="pill">' + escapeHtml(kind) + "</span>" + body;
  }

  function renderDraw(book) {
    if (!drawResult || !book) return;
    var q = book.quotes && book.quotes.length ? pickOne(book.quotes) : null;
    var alt = (I18N.t && I18N.t("coverOf", { title: book.title })) || ("Cover of " + book.title);
    var kind = book.kind === "album"
      ? escapeHtml((I18N.t && I18N.t("audiobook")) || "Audiobook")
      : escapeHtml(book.category || "");
    drawResult.innerHTML =
      '<a class="book-link" href="' + escapeHtml(book.link) + '" rel="noopener noreferrer">' +
        '<img class="cover" src="' + escapeHtml(book.cover) + '" alt="' + escapeHtml(alt) + '" width="88" height="118">' +
        "<div>" +
          "<h3>" + escapeHtml(book.title) + "</h3>" +
          '<p class="by">' + escapeHtml(book.author) + "</p>" +
          '<p class="meta">' + kind + "</p>" +
          quoteHTML(q) +
        "</div>" +
      "</a>";
    drawResult.hidden = false;
    lastBookId = book.id;
  }

  if (drawBtn && play.books.length) {
    drawBtn.addEventListener("click", function () {
      renderDraw(pickOne(play.books, lastBookId, "id"));
    });
  }

  var quoteCard = document.getElementById("quoteCard");
  var quoteNext = document.getElementById("quoteNext");
  var quoteIndex = -1;
  var quoteOrder = [];

  function shuffledOrder(n, startAvoid) {
    var arr = [];
    var i;
    for (i = 0; i < n; i += 1) arr.push(i);
    for (i = n - 1; i > 0; i -= 1) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }
    if (n > 1 && startAvoid >= 0 && arr[0] === startAvoid) {
      var sw = arr[1];
      arr[1] = arr[0];
      arr[0] = sw;
    }
    return arr;
  }

  function renderQuote(q) {
    if (!quoteCard || !q) return;
    var foot = (I18N.t && I18N.t("fromBook", { title: q.title, author: q.author }))
      || ("From " + q.title + " · " + q.author);
    quoteCard.innerHTML =
      quoteHTML(q) +
      "<footer><a href=\"" + escapeHtml(q.link) + "\" rel=\"noopener noreferrer\">" + escapeHtml(foot) + "</a></footer>";
  }

  function showNextQuote(animate) {
    if (!play.quotes.length || !quoteCard) return;
    if (!quoteOrder.length) quoteOrder = shuffledOrder(play.quotes.length, quoteIndex);
    quoteIndex = quoteOrder.shift();
    var q = play.quotes[quoteIndex];
    if (!animate || reduceMotion) {
      renderQuote(q);
      return;
    }
    quoteCard.classList.remove("is-in");
    quoteCard.classList.add("is-away");
    window.setTimeout(function () {
      renderQuote(q);
      quoteCard.classList.remove("is-away");
      quoteCard.classList.add("is-in");
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          quoteCard.classList.remove("is-in");
        });
      });
    }, 280);
  }

  if (quoteCard && play.quotes.length) {
    showNextQuote(false);
    if (quoteNext) quoteNext.addEventListener("click", function () { showNextQuote(true); });
  }

  function refreshDynamicLang() {
    if (drawResult && !drawResult.hidden && lastBookId) {
      var book = null;
      play.books.some(function (b) { if (b.id === lastBookId) { book = b; return true; } return false; });
      if (book) renderDraw(book);
    }
    if (quoteCard && quoteIndex >= 0 && play.quotes[quoteIndex]) {
      renderQuote(play.quotes[quoteIndex]);
    }
  }

  /* cursor glow + tilt */
  var glow = document.getElementById("cursorGlow");
  var finePointer = false;
  try { finePointer = window.matchMedia("(pointer: fine)").matches; } catch (e) {}
  if (glow && finePointer && !reduceMotion) {
    var glowOn = false;
    window.addEventListener("pointermove", function (e) {
      glow.style.left = e.clientX + "px";
      glow.style.top = e.clientY + "px";
      if (!glowOn) {
        glow.classList.add("is-on");
        glowOn = true;
      }
    }, { passive: true });
    window.addEventListener("pointerleave", function () {
      glow.classList.remove("is-on");
      glowOn = false;
    });
  }

  if (finePointer && !reduceMotion) {
    var tiltEl = null;
    document.addEventListener("pointermove", function (e) {
      var card = e.target.closest(".card, .rstat, .shelf-card");
      if (card && card.closest(".egg")) card = null;
      if (tiltEl && tiltEl !== card) {
        tiltEl.style.setProperty("--rx", "0deg");
        tiltEl.style.setProperty("--ry", "0deg");
      }
      tiltEl = card;
      if (!card) return;
      var r = card.getBoundingClientRect();
      if (!r.width || !r.height) return;
      var x = (e.clientX - r.left) / r.width;
      var y = (e.clientY - r.top) / r.height;
      card.style.setProperty("--rx", ((0.5 - y) * 7).toFixed(2) + "deg");
      card.style.setProperty("--ry", ((x - 0.5) * 8).toFixed(2) + "deg");
    }, { passive: true });
    document.addEventListener("pointerleave", function () {
      if (!tiltEl) return;
      tiltEl.style.setProperty("--rx", "0deg");
      tiltEl.style.setProperty("--ry", "0deg");
      tiltEl = null;
    });
  }

  /* easter egg: Konami or 5 avatar clicks */
  window.addEventListener("qzone:tabchange", function () {
    if (typeof revealVisible === "function") revealVisible();
  });

  var egg = document.getElementById("egg");
  var eggClose = document.getElementById("eggClose");
  var portrait = document.querySelector(".portrait");
  var eggOpen = false;
  var lastFocus = null;

  function openEgg() {
    if (!egg || eggOpen) return;
    eggOpen = true;
    lastFocus = document.activeElement;
    egg.hidden = false;
    if (eggClose) eggClose.focus();
  }

  function closeEgg() {
    if (!egg || !eggOpen) return;
    eggOpen = false;
    egg.hidden = true;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  if (eggClose) eggClose.addEventListener("click", closeEgg);
  if (egg) {
    egg.addEventListener("click", function (e) {
      if (e.target === egg) closeEgg();
    });
  }

  var konami = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65];
  var konamiPos = 0;
  document.addEventListener("keydown", function (e) {
    if (eggOpen && e.key === "Escape") {
      closeEgg();
      return;
    }
    var key = e.keyCode || e.which;
    if (key === konami[konamiPos]) {
      konamiPos += 1;
      if (konamiPos === konami.length) {
        konamiPos = 0;
        openEgg();
      }
    } else {
      konamiPos = key === konami[0] ? 1 : 0;
    }
  });

  if (portrait) {
    var clicks = 0;
    var clickTimer = 0;
    portrait.addEventListener("click", function () {
      clicks += 1;
      window.clearTimeout(clickTimer);
      if (clicks >= 5) {
        clicks = 0;
        openEgg();
        return;
      }
      clickTimer = window.setTimeout(function () { clicks = 0; }, 2200);
    });
  }
})();
