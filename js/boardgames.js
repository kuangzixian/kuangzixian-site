(function () {
  var list = document.getElementById("qzBoardgamesList");
  if (!list) return;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function pick(game, base) {
    var loc = (window.KUANG_I18N && window.KUANG_I18N.locale) || "zh";
    return game[base + "_" + loc] || game[base + "_en"] || game[base + "_zh"] || "";
  }

  function cardHtml(game) {
    var id = game.id || "";
    var emoji = game.emoji || "🎲";
    var loc = (window.KUANG_I18N && window.KUANG_I18N.locale) || "zh";
    var name = pick(game, "name") || "Game";
    var nameZh = game.name_zh || "";
    var nameEn = game.name_en || "";
    var blurb = pick(game, "blurb");
    var aka = "";
    if (loc === "zh" && nameEn && nameZh && nameEn !== nameZh) aka = '<p class="bgame-aka">' + esc(nameEn) + "</p>";
    else if (loc !== "zh" && nameZh && name && nameZh !== name) aka = '<p class="bgame-aka">' + esc(nameZh) + "</p>";
    return (
      '<article class="card bgame-card" data-game="' + esc(id) + '">' +
        '<span class="bgame-icon" data-game="' + esc(id) + '" aria-hidden="true">' + esc(emoji) + "</span>" +
        '<div class="bgame-body">' +
          '<h3 class="bgame-name">' + esc(name) + "</h3>" +
          aka +
          (blurb ? '<p class="bgame-desc">' + esc(blurb) + "</p>" : "") +
        "</div>" +
      "</article>"
    );
  }

  function apply(data) {
    var games = (data && data.games) || [];
    if (!games.length) return;
    list.innerHTML = games.map(cardHtml).join("");
    var loc = (window.KUANG_I18N && window.KUANG_I18N.locale) || "zh";
    var intro = document.getElementById("qzBoardgamesIntro") || document.getElementById("qzBoardgamesIntroZh");
    var key = loc === "zh" ? "intro_zh" : "intro_" + loc;
    if (intro && (data[key] || data.intro_en || data.intro_zh)) {
      intro.textContent = data[key] || data.intro_en || data.intro_zh;
    }
  }

  if (list.getAttribute("data-static") === "1") return;

  fetch("/data/boardgames.json", { cache: "no-store" })
    .then(function (res) {
      if (!res.ok) throw new Error("boardgames.json " + res.status);
      return res.json();
    })
    .then(apply)
    .catch(function () {
      /* keep the static fallback already in the HTML */
    });
})();
