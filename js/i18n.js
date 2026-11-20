(function (global) {
  var ORDER = ["zh", "en", "es", "ko", "ja"];
  var LOCALES = {
    zh: { htmlLang: "zh-CN", hreflang: "zh-CN", og: "zh_CN", prefix: "", name: "中文", intl: "zh-CN" },
    en: { htmlLang: "en", hreflang: "en", og: "en_US", prefix: "/en", name: "English", intl: "en" },
    es: { htmlLang: "es", hreflang: "es", og: "es_ES", prefix: "/es", name: "Español", intl: "es" },
    ko: { htmlLang: "ko", hreflang: "ko", og: "ko_KR", prefix: "/ko", name: "한국어", intl: "ko" },
    ja: { htmlLang: "ja", hreflang: "ja", og: "ja_JP", prefix: "/ja", name: "日本語", intl: "ja" }
  };

  var UI = {
    langLabel: {
      zh: "选择语言",
      en: "Choose language",
      es: "Elegir idioma",
      ko: "언어 선택",
      ja: "言語を選ぶ"
    },
    snowOn: { zh: "飘雪特效：开", en: "Snow: On", es: "Nieve: activada", ko: "눈 효과: 켜짐", ja: "雪の演出：オン" },
    snowOff: { zh: "飘雪特效：关", en: "Snow: Off", es: "Nieve: desactivada", ko: "눈 효과: 꺼짐", ja: "雪の演出：オフ" },
    snowTitleOn: {
      zh: "飘雪特效开启，点击可重播或关闭",
      en: "Snow is on. Click to replay or turn off.",
      es: "La nieve está activada. Clic para repetir o apagar.",
      ko: "눈 효과가 켜져 있습니다. 다시 재생하거나 끄려면 누르세요.",
      ja: "雪の演出はオンです。クリックで再生し直すかオフにできます。"
    },
    snowTitleOff: {
      zh: "开启飘雪特效",
      en: "Turn on snow",
      es: "Activar la nieve",
      ko: "눈 효과 켜기",
      ja: "雪の演出をオンにする"
    },
    snowReducedTitle: {
      zh: "已按系统设置关闭动态效果",
      en: "Motion is off, following your system setting.",
      es: "El movimiento está desactivado según la configuración del sistema.",
      ko: "시스템 설정에 따라 움직임 효과가 꺼져 있습니다.",
      ja: "システムの設定に合わせて動きをオフにしています。"
    },
    snowReducedLabel: {
      zh: "飘雪特效已关闭（减少动态效果）",
      en: "Snow is off (reduced motion)",
      es: "Nieve desactivada (menos movimiento)",
      ko: "눈 효과 꺼짐(움직임 줄이기)",
      ja: "雪の演出はオフです（動きを減らす設定）"
    },
    coverOf: {
      zh: "《{title}》封面",
      en: "Cover of {title}",
      es: "Portada de {title}",
      ko: "《{title}》 표지",
      ja: "『{title}』の表紙"
    },
    fromBook: {
      zh: "出自《{title}》· {author}",
      en: "From {title} · {author}",
      es: "De {title} · {author}",
      ko: "《{title}》· {author}",
      ja: "『{title}』· {author}"
    },
    thought: { zh: "想法", en: "Thought", es: "Idea", ko: "생각", ja: "感想" },
    highlight: { zh: "划线", en: "Highlight", es: "Subrayado", ko: "밑줄", ja: "ハイライト" },
    audiobook: { zh: "有声书", en: "Audiobook", es: "Audiolibro", ko: "오디오북", ja: "オーディオブック" },
    noHighlight: {
      zh: "这本书在精选笔记里还没有摘录。",
      en: "No curated highlight for this title.",
      es: "Este libro aún no tiene una cita seleccionada.",
      ko: "이 책에는 아직 골라 둔 발췌가 없습니다.",
      ja: "この本にはまだ選んだ抜粋がありません。"
    },
    gbEmpty: { zh: "还没有留言，来写第一条吧。", en: "No notes yet — be the first to write one.", es: "Aún no hay mensajes. Sé la primera persona en escribir uno.", ko: "아직 남긴 글이 없습니다. 첫 번째를 남겨 보세요.", ja: "まだ伝言がありません。最初の一言をどうぞ。" },
    gbUnavailable: { zh: "留言板暂时连不上，过一会儿再试试。", en: "The guestbook is temporarily unavailable. Please try again later.", es: "El libro de visitas no está disponible por ahora. Inténtalo más tarde.", ko: "방명록에 잠시 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.", ja: "伝言板に一時つながっていません。しばらくしてからもう一度どうぞ。" },
    gbInvalidNickname: { zh: "昵称需要 1 到 20 个字。", en: "Nickname must be 1 to 20 characters.", es: "El apodo debe tener entre 1 y 20 caracteres.", ko: "닉네임은 1~20자여야 합니다.", ja: "ニックネームは1〜20字にしてください。" },
    gbInvalidContent: { zh: "留言需要 1 到 500 个字。", en: "The note must be 1 to 500 characters.", es: "El mensaje debe tener entre 1 y 500 caracteres.", ko: "글은 1~500자여야 합니다.", ja: "伝言は1〜500字にしてください。" },
    gbHasLink: { zh: "为了减少广告，留言里先不要放链接。", en: "Please leave the note without links, to keep spam down.", es: "Por favor, no incluyas enlaces, para reducir el spam.", ko: "광고를 줄이려면 글에 링크를 넣지 마세요.", ja: "広告を減らすため、リンクは入れないでください。" },
    gbSpam: { zh: "这条看起来像广告，没有发出去。", en: "This looked like an ad, so it was not posted.", es: "Esto parecía un anuncio, así que no se publicó.", ko: "광고처럼 보여서 등록되지 않았습니다.", ja: "広告のように見えたため、投稿しませんでした。" },
    gbTooFast: { zh: "写得有点勤，请过几分钟再留。", en: "That is a bit quick. Please wait a few minutes.", es: "Vas un poco rápido. Espera unos minutos.", ko: "조금 빠르네요. 몇 분 뒤에 다시 남겨 주세요.", ja: "少し早いです。数分してからもう一度どうぞ。" },
    gbNetwork: { zh: "网络不太稳，请稍后再试。", en: "The network hiccuped. Please try again.", es: "Hubo un problema de red. Inténtalo de nuevo.", ko: "네트워크가 불안정합니다. 잠시 후 다시 시도해 주세요.", ja: "通信が不安定です。しばらくしてからもう一度どうぞ。" },
    gbSent: { zh: "已记下。", en: "Saved.", es: "Guardado.", ko: "남겼습니다.", ja: "残しました。" },
    gbSending: { zh: "正在发送…", en: "Sending…", es: "Enviando…", ko: "보내는 중…", ja: "送信中…" },
    justNow: { zh: "刚刚", en: "just now", es: "ahora mismo", ko: "방금", ja: "たった今" },
    minutesAgo: { zh: "{n} 分钟前", en: "{n} min ago", es: "hace {n} min", ko: "{n}분 전", ja: "{n}分前" },
    hoursAgo: { zh: "{n} 小时前", en: "{n} hr ago", es: "hace {n} h", ko: "{n}시간 전", ja: "{n}時間前" },
    daysAgo: { zh: "{n} 天前", en: "{n} days ago", es: "hace {n} días", ko: "{n}일 전", ja: "{n}日前" },
    conversation: { zh: "对话", en: "Conversation", es: "Conversación", ko: "대화", ja: "対話" },
    backWriting: { zh: "← 返回文章列表", en: "← Back to writing", es: "← Volver a los textos", ko: "← 글 목록으로", ja: "← 記事一覧に戻る" },
    withGpt: { zh: "匡子闲 与 GPT", en: "匡子闲 and GPT", es: "匡子闲 y GPT", ko: "匡子闲과 GPT", ja: "匡子闲とGPT" },
    myQuestion: { zh: "我的问题", en: "My question", es: "Mi pregunta", ko: "내 질문", ja: "わたしの質問" },
    myPrompt: { zh: "我的 Prompt", en: "My prompt", es: "Mi prompt", ko: "내 프롬프트", ja: "わたしのプロンプト" },
    sourceChat: { zh: "原始 ChatGPT 分享链接", en: "Original ChatGPT share link", es: "Enlace original de ChatGPT", ko: "원래 ChatGPT 공유 링크", ja: "元の ChatGPT 共有リンク" },
    sourcePrompt: { zh: "原始 Prompt 分享链接", en: "Original prompt share link", es: "Enlace original del prompt", ko: "원래 프롬프트 공유 링크", ja: "元のプロンプト共有リンク" },
    notFound: { zh: "没有找到这篇对话。", en: "This conversation could not be found.", es: "No se encontró esta conversación.", ko: "이 대화를 찾을 수 없습니다.", ja: "この対話は見つかりませんでした。" },
    loadFailed: { zh: "对话加载失败，请稍后再试。", en: "Failed to load the conversation. Please try again later.", es: "No se pudo cargar la conversación. Inténtalo más tarde.", ko: "대화를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.", ja: "対話を読み込めませんでした。しばらくしてからもう一度どうぞ。" },
    noConversations: { zh: "还没有对话。", en: "No conversations yet.", es: "Aún no hay conversaciones.", ko: "아직 대화가 없습니다.", ja: "まだ対話がありません。" },
    open: { zh: "打开", en: "Open", es: "Abrir", ko: "열기", ja: "開く" },
    close: { zh: "收起", en: "Close", es: "Cerrar", ko: "닫기", ja: "閉じる" },
    madeByMe: { zh: "自己做的", en: "Made by me", es: "Hecho por mí", ko: "직접 만든 것", ja: "自分で作った" },
    notFoundTitle: { zh: "空间里没有这个页面", en: "This page isn’t in the zone.", es: "Esta página no está en el espacio.", ko: "공간에 이 페이지가 없습니다.", ja: "このページは空間にありません。" },
    notFoundBody: { zh: "这个地址没有对应的内容。可能是链接写错了，或页面已经换了地方。", en: "Nothing lives at this address. The link may be mistyped, or the page has moved.", es: "No hay nada en esta dirección. Puede que el enlace esté mal escrito o que la página se haya mudado.", ko: "이 주소에는 해당하는 내용이 없습니다. 링크가 잘못되었거나 페이지가 옮겨졌을 수 있습니다.", ja: "このアドレスには内容がありません。リンクの誤りか、ページが移ったのかもしれません。" },
    backHome: { zh: "回到首页", en: "Back to home", es: "Volver al inicio", ko: "홈으로", ja: "ホームに戻る" },
    gbFloor: { zh: "第{n}楼", en: "Floor {n}", es: "Piso {n}", ko: "{n}층", ja: "{n}階" },
    goLogs: { zh: "去看日志", en: "Read the logs", es: "Ver los diarios", ko: "로그 보기", ja: "日誌を見る" },
    writingKicker: { zh: "日志", en: "Writing", es: "Diario", ko: "로그", ja: "日誌" },
    originalConversation: {
      zh: "这篇对话原文是中文。",
      en: "This conversation was originally in Chinese.",
      es: "Esta conversación se escribió originalmente en chino.",
      ko: "이 대화는 원래 중국어로 이루어졌습니다.",
      ja: "この対話はもともと中国語で行われました。"
    },
    originalLink: { zh: "查看原文", en: "Read the original", es: "Ver el original", ko: "원문 보기", ja: "原文を読む" }
  };

  function pathLocale(pathname) {
    var m = String(pathname || "").match(/^\/(en|es|ko|ja)(?=\/|$)/);
    return m ? m[1] : "zh";
  }

  function detectBrowserLocale() {
    var list = [];
    try {
      if (navigator.languages && navigator.languages.length) {
        list = Array.prototype.slice.call(navigator.languages);
      } else if (navigator.language) {
        list = [navigator.language];
      }
    } catch (e) {}
    var i, n;
    for (i = 0; i < list.length; i += 1) {
      n = String(list[i] || "").toLowerCase().replace("_", "-");
      if (n.indexOf("zh") === 0) return "zh";
      if (n.indexOf("en") === 0) return "en";
      if (n.indexOf("es") === 0) return "es";
      if (n.indexOf("ko") === 0) return "ko";
      if (n.indexOf("ja") === 0) return "ja";
    }
    return null;
  }

  function isBot() {
    try {
      return /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|linkedinbot|pinterest|googleother|wget|curl|python-requests|preview/i.test(navigator.userAgent || "");
    } catch (e) {
      return false;
    }
  }

  function stripLocale(pathname) {
    var p = String(pathname || "/");
    p = p.replace(/^\/(en|es|ko|ja)(?=\/|$)/, "") || "/";
    if (p.length > 1 && p.slice(-1) === "/") p = p.slice(0, -1);
    return p || "/";
  }

  function localizePath(pathname, loc, search, hash) {
    var info = LOCALES[loc] || LOCALES.zh;
    var p = stripLocale(pathname);
    if (p === "/index.html") p = "/";
    var dest;
    if (p === "/") dest = info.prefix ? info.prefix + "/" : "/";
    else dest = (info.prefix || "") + p;
    return dest + (search || "") + (hash || "");
  }

  var locale = pathLocale(global.location && global.location.pathname);

  function t(key, vars) {
    var pack = UI[key] || {};
    var text = pack[locale] || pack.en || pack.zh || key;
    if (vars) {
      Object.keys(vars).forEach(function (k) {
        text = text.replace(new RegExp("\\{" + k + "\\}", "g"), String(vars[k]));
      });
    }
    return text;
  }

  function formatNumber(n) {
    try {
      return new Intl.NumberFormat(LOCALES[locale].intl).format(n);
    } catch (e) {
      return String(n);
    }
  }

  function formatDate(iso, options) {
    var ts = typeof iso === "number" ? iso : Date.parse(iso);
    if (!isFinite(ts)) return iso || "";
    var opts = options || { year: "numeric", month: "short", day: "numeric", timeZone: "Asia/Shanghai" };
    try {
      return new Intl.DateTimeFormat(LOCALES[locale].intl, opts).format(new Date(ts));
    } catch (e) {
      return iso;
    }
  }

  function getSavedLang() {
    try { return localStorage.getItem("kuang-lang"); } catch (e) { return null; }
  }

  function setSavedLang(loc) {
    try { localStorage.setItem("kuang-lang", loc); } catch (e) {}
  }

  function maybeRedirect() {
    if (isBot()) return;
    var loc = global.location;
    if (!loc) return;
    var cur = pathLocale(loc.pathname);
    var saved = getSavedLang();
    if (saved && !LOCALES[saved]) saved = null;
    if (cur !== "zh") {
      if (saved !== cur) setSavedLang(cur);
      return;
    }
    var want = saved || detectBrowserLocale();
    if (!want || want === "zh" || !LOCALES[want]) return;
    if (!saved) setSavedLang(want);
    var dest = localizePath(loc.pathname, want, loc.search, loc.hash);
    if (dest !== loc.pathname + loc.search + loc.hash) {
      loc.replace(dest);
    }
  }

  function closeMenus(root) {
    (root || document).querySelectorAll("[data-lang-switcher]").forEach(function (box) {
      var btn = box.querySelector(".lang-switcher-btn");
      var menu = box.querySelector(".lang-switcher-menu");
      if (btn) btn.setAttribute("aria-expanded", "false");
      if (menu) menu.hidden = true;
    });
  }

  function menuItems(menu) {
    return Array.prototype.slice.call(menu.querySelectorAll("[data-lang]"));
  }

  function openMenu(box) {
    var btn = box.querySelector(".lang-switcher-btn");
    var menu = box.querySelector(".lang-switcher-menu");
    if (!btn || !menu) return;
    closeMenus();
    btn.setAttribute("aria-expanded", "true");
    menu.hidden = false;
    var current = menu.querySelector("[aria-current='true']") || menuItems(menu)[0];
    if (current) current.focus();
  }

  function moveFocus(menu, delta) {
    var items = menuItems(menu);
    if (!items.length) return;
    var i = items.indexOf(document.activeElement);
    if (i < 0) {
      i = items.findIndex(function (a) { return a.getAttribute("aria-current") === "true"; });
      if (i < 0) i = 0;
    } else {
      i = (i + delta + items.length) % items.length;
    }
    items[i].focus();
  }

  function bindLangLink(a, loc) {
    var code = a.getAttribute("data-lang");
    if (!LOCALES[code] || !loc) return;
    a.setAttribute("href", localizePath(loc.pathname, code, loc.search, loc.hash));
    if (code === locale) a.setAttribute("aria-current", "true");
    else a.removeAttribute("aria-current");
    a.addEventListener("click", function () { setSavedLang(code); });
  }

  function initSwitcher() {
    var loc = global.location;
    document.querySelectorAll("[data-lang-switcher]").forEach(function (box) {
      var btn = box.querySelector(".lang-switcher-btn");
      var menu = box.querySelector(".lang-switcher-menu");
      if (!btn || !menu) return;
      box.querySelectorAll("[data-lang]").forEach(function (a) { bindLangLink(a, loc); });
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var open = btn.getAttribute("aria-expanded") === "true";
        if (open) {
          closeMenus();
          btn.focus();
        } else {
          openMenu(box);
        }
      });
      btn.addEventListener("keydown", function (e) {
        if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
        e.preventDefault();
        openMenu(box);
        if (e.key === "ArrowUp") {
          var items = menuItems(menu);
          if (items.length) items[items.length - 1].focus();
        }
      });
      menu.addEventListener("click", function (e) { e.stopPropagation(); });
      menu.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown") { e.preventDefault(); moveFocus(menu, 1); }
        else if (e.key === "ArrowUp") { e.preventDefault(); moveFocus(menu, -1); }
        else if (e.key === "Home") { e.preventDefault(); var first = menuItems(menu)[0]; if (first) first.focus(); }
        else if (e.key === "End") {
          e.preventDefault();
          var items = menuItems(menu);
          if (items.length) items[items.length - 1].focus();
        } else if (e.key === "Escape") {
          e.preventDefault();
          closeMenus();
          btn.focus();
        } else if (e.key === "Tab") {
          closeMenus();
        }
      });
    });
    document.querySelectorAll("[data-lang-list] [data-lang]").forEach(function (a) {
      bindLangLink(a, loc);
    });
    document.addEventListener("click", function () { closeMenus(); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenus();
    });
  }

  global.KUANG_I18N = {
    locale: locale,
    locales: LOCALES,
    order: ORDER,
    t: t,
    formatNumber: formatNumber,
    formatDate: formatDate,
    pathLocale: pathLocale,
    localizePath: localizePath,
    detectBrowserLocale: detectBrowserLocale,
    maybeRedirect: maybeRedirect,
    setSavedLang: setSavedLang,
    initSwitcher: initSwitcher
  };
})(window);
