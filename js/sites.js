(function () {
  var list = document.getElementById("qzSitesList");
  if (!list) return;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function hostname(url) {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch (e) {
      return "";
    }
  }

  function iconHtml(site, name) {
    var emoji = site.emoji || "🌐";
    var alt = site.image_alt || name;
    var src = site.image || site.favicon || "";
    if (src && src.indexOf("http") !== 0 && src.charAt(0) !== "/") src = "/" + src;
    var fallback = '<span class="site-fallback" aria-hidden="true">' + esc(emoji) + "</span>";
    if (!src) return fallback;
    return (
      '<span class="site-icon-wrap">' +
        '<img class="site-icon" src="' + esc(src) + '" alt="' + esc(alt) + '" width="56" height="56" loading="lazy" onerror="this.hidden=true;var f=this.nextElementSibling;if(f)f.hidden=false;">' +
        '<span class="site-fallback" hidden aria-hidden="true">' + esc(emoji) + "</span>" +
      "</span>"
    );
  }

  function badgeHtml(site) {
    if (!site.own) return "";
    var label = (window.KUANG_I18N && window.KUANG_I18N.t && window.KUANG_I18N.t("madeByMe")) || "Made by me";
    return '<span class="site-badge">' + esc(label) + "</span>";
  }

  function cardHtml(site) {
    var url = site.url || site.canonical || "";
    var name = site.name || site.title || url;
    var domain = site.domain || hostname(url) || hostname(site.canonical || "") || url;
    var desc = site.description || "";
    var ownClass = site.own ? " is-own" : "";
    return (
      '<a class="card site-card' + ownClass + '" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' +
        iconHtml(site, name) +
        '<span class="site-body">' +
          '<span class="site-head">' +
            '<strong class="site-name">' + esc(name) + "</strong>" +
            badgeHtml(site) +
          "</span>" +
          (domain ? '<span class="site-domain">' + esc(domain) + "</span>" : "") +
          (desc ? '<span class="site-desc">' + esc(desc) + "</span>" : "") +
        "</span>" +
      "</a>"
    );
  }

  function apply(data) {
    var sites = (data && (data.sites || data.friends)) || [];
    if (!sites.length) return;
    list.innerHTML = sites.map(cardHtml).join("");
    var loc = (window.KUANG_I18N && window.KUANG_I18N.locale) || "zh";
    var intro = document.getElementById("qzSitesIntro") || document.getElementById("qzSitesIntroZh");
    var key = loc === "zh" ? "intro_zh" : "intro_" + loc;
    if (intro && (data[key] || data.intro_en || data.intro_zh)) {
      intro.textContent = data[key] || data.intro_en || data.intro_zh;
    }
  }

  if (list.getAttribute("data-static") === "1") return;

  fetch("/data/sites.json", { cache: "no-store" })
    .then(function (res) {
      if (!res.ok) throw new Error("sites.json " + res.status);
      return res.json();
    })
    .then(apply)
    .catch(function () {
      /* keep the static fallback already in the HTML */
    });
})();
