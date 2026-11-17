(function () {
  var totalEl = document.getElementById("qzVisitTotal");
  var todayEl = document.getElementById("qzVisitToday");
  var boardEl = document.getElementById("qzVisitBoard");
  function pad(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function paint(data) {
    if (!data || !data.ok) return;
    if (totalEl) totalEl.textContent = pad(data.total);
    if (todayEl) todayEl.textContent = pad(data.today);
  }

  var dayKey;
  try {
    dayKey = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Shanghai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date());
  } catch (e) {
    dayKey = new Date().toISOString().slice(0, 10);
  }

  var flagged = false;
  try {
    flagged = localStorage.getItem("qz-visit-day") === dayKey;
  } catch (e) {}

  var url = flagged ? "/api/visits" : "/api/visits?increment=1";
  fetch(url, { credentials: "same-origin", headers: { accept: "application/json" } })
    .then(function (res) {
      if (!res.ok) throw new Error("bad status");
      return res.json();
    })
    .then(function (data) {
      paint(data);
      if (data && data.ok) {
        try {
          localStorage.setItem("qz-visit-day", dayKey);
        } catch (e) {}
      }
    })
    .catch(function () {});
})();
