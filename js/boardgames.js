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

  function cardHtml(game) {
    var id = game.id || "";
    var emoji = game.emoji || "🎲";
    var nameZh = game.name_zh || "";
    var nameEn = game.name_en || "";
    var title = nameZh || nameEn || "Game";
    var blurbZh = game.blurb_zh || "";
    var blurbEn = game.blurb_en || "";
    return (
      '<article class="card bgame-card" data-game="' + esc(id) + '">' +
        '<span class="bgame-icon" data-game="' + esc(id) + '" aria-hidden="true">' + esc(emoji) + "</span>" +
        '<div class="bgame-body">' +
          '<h3 class="bgame-name">' +
            '<span class="zh">' + esc(nameZh || nameEn) + "</span>" +
            '<span class="en-only">' + esc(nameEn || nameZh) + "</span>" +
          "</h3>" +
          (nameEn && nameZh && nameEn !== nameZh
            ? '<p class="bgame-aka zh">' + esc(nameEn) + "</p>" +
              '<p class="bgame-aka en-only">' + esc(nameZh) + "</p>"
            : "") +
          (blurbZh ? '<p class="bgame-desc zh">' + esc(blurbZh) + "</p>" : "") +
          (blurbEn ? '<p class="bgame-desc en-only">' + esc(blurbEn) + "</p>" : "") +
        "</div>" +
      "</article>"
    );
  }

  function apply(data) {
    var games = (data && data.games) || [];
    if (!games.length) return;
    list.innerHTML = games.map(cardHtml).join("");
    var introZh = document.getElementById("qzBoardgamesIntroZh");
    var introEn = document.getElementById("qzBoardgamesIntroEn");
    if (introZh && data.intro_zh) introZh.textContent = data.intro_zh;
    if (introEn && data.intro_en) introEn.textContent = data.intro_en;
  }

  fetch("data/boardgames.json", { cache: "no-store" })
    .then(function (res) {
      if (!res.ok) throw new Error("boardgames.json " + res.status);
      return res.json();
    })
    .then(apply)
    .catch(function () {
      /* keep the static fallback already in the HTML */
    });
})();
