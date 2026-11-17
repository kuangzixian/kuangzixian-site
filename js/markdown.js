/* Tiny Markdown + code highlighter. No CDN. */
(function (root) {
  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  var KEYWORDS = (
    "break case catch class const continue debugger default delete do else export extends " +
    "finally for function if import in instanceof let new return static super switch this " +
    "throw try typeof var void while with yield async await of from as " +
    "func package import type struct interface map chan go defer select range " +
    "true false null nil undefined"
  ).split(/\s+/);
  var KW = new RegExp("\\b(" + KEYWORDS.join("|") + ")\\b", "g");

  function highlight(code) {
    var s = escapeHtml(code);
    var slots = [];
    function stash(html) {
      slots.push(html);
      return "\u0000" + (slots.length - 1) + "\u0000";
    }
    s = s.replace(/\/\*[\s\S]*?\*\//g, function (m) {
      return stash('<span class="tok-cmt">' + m + "</span>");
    });
    s = s.replace(/(^|[^:\\])\/\/[^\n]*/g, function (m) {
      return stash('<span class="tok-cmt">' + m + "</span>");
    });
    s = s.replace(/`(?:\\.|[^`\\])*`/g, function (m) {
      return stash('<span class="tok-str">' + m + "</span>");
    });
    s = s.replace(/&quot;(?:\\.|[^&])*?&quot;/g, function (m) {
      return stash('<span class="tok-str">' + m + "</span>");
    });
    s = s.replace(/'(?:\\.|[^'\\])*'/g, function (m) {
      return stash('<span class="tok-str">' + m + "</span>");
    });
    s = s.replace(/\b0x[0-9a-fA-F]+\b|\b\d+(?:\.\d+)?\b/g, function (m) {
      return stash('<span class="tok-num">' + m + "</span>");
    });
    s = s.replace(KW, '<span class="tok-kw">$1</span>');
    s = s.replace(/\u0000(\d+)\u0000/g, function (_, i) { return slots[Number(i)]; });
    return s;
  }

  function inlineMd(s) {
    s = escapeHtml(s).replace(/\\./g, function (m) {
      var ch = m.charAt(1);
      return ch === "<" ? "&lt;" : ch === ">" ? "&gt;" : ch === "&" ? "&amp;" : ch;
    });
    s = s.replace(/`([^`]+)`/g, function (_, c) {
      return "<code>" + c + "</code>";
    });
    s = s.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, function (_, text, url) {
      return '<a href="' + url + '" rel="noopener noreferrer">' + text + "</a>";
    });
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
    return s;
  }

  function renderList(items, ordered) {
    var tag = ordered ? "ol" : "ul";
    var html = "<" + tag + ">";
    items.forEach(function (item) {
      html += "<li>" + item.split(/\n/).map(function (line, i) {
        return (i ? "<br>" : "") + inlineMd(line);
      }).join("") + "</li>";
    });
    return html + "</" + tag + ">";
  }

  function lineHasTable(line) {
    if (!line || !line.trim()) return false;
    if (isTableSep(line)) return true;
    return line.indexOf("|") !== -1;
  }

  function isTableSep(line) {
    return /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(line);
  }

  function splitCells(line) {
    var t = line.trim();
    if (t.charAt(0) === "|") t = t.slice(1);
    if (t.charAt(t.length - 1) === "|") t = t.slice(0, -1);
    return t.split("|").map(function (c) { return c.trim(); });
  }

  function renderTable(rows) {
    if (!rows.length) return "";
    var head = rows[0];
    var body = rows.slice(1);
    var html = '<div class="md-table"><table><thead><tr>';
    head.forEach(function (c) { html += "<th>" + inlineMd(c) + "</th>"; });
    html += "</tr></thead><tbody>";
    body.forEach(function (row) {
      html += "<tr>";
      row.forEach(function (c) { html += "<td>" + inlineMd(c) + "</td>"; });
      html += "</tr>";
    });
    return html + "</tbody></table></div>";
  }

  function renderMarkdown(src) {
    var text = String(src || "").replace(/\r\n/g, "\n").replace(/\t/g, "    ");
    var lines = text.split("\n");
    var out = [];
    var i = 0;
    var para = [];
    var quote = [];
    var list = null;
    var listOrdered = false;

    function flushPara() {
      if (!para.length) return;
      var body = para.join("\n").trim();
      if (body) out.push("<p>" + body.split(/\n/).map(inlineMd).join("<br>") + "</p>");
      para = [];
    }
    function flushQuote() {
      if (!quote.length) return;
      out.push("<blockquote>" + renderMarkdown(quote.join("\n")) + "</blockquote>");
      quote = [];
    }
    function flushList() {
      if (!list) return;
      out.push(renderList(list, listOrdered));
      list = null;
    }
    function flushAll() {
      flushPara();
      flushQuote();
      flushList();
    }

    while (i < lines.length) {
      var line = lines[i];

      var fence = line.match(/^```([\w+-]*)\s*$/);
      if (fence) {
        flushAll();
        var lang = fence[1] || "";
        var code = [];
        i += 1;
        while (i < lines.length && !/^```\s*$/.test(lines[i])) {
          code.push(lines[i]);
          i += 1;
        }
        out.push(
          '<pre><code class="lang-' + escapeHtml(lang) + '">' +
          highlight(code.join("\n")) +
          "</code></pre>"
        );
        i += 1;
        continue;
      }

      if (line.indexOf("|") !== -1 && i + 1 < lines.length && isTableSep(lines[i + 1])) {
        flushAll();
        var rows = [splitCells(line)];
        i += 2;
        while (i < lines.length && lineHasTable(lines[i])) {
          if (!isTableSep(lines[i])) rows.push(splitCells(lines[i]));
          i += 1;
        }
        out.push(renderTable(rows));
        continue;
      }

      if (/^---+\s*$/.test(line) || /^\*\*\*+\s*$/.test(line)) {
        flushAll();
        out.push("<hr>");
        i += 1;
        continue;
      }

      var heading = line.match(/^(#{1,6})\s+(.+?)\s*$/);
      if (heading) {
        flushAll();
        var level = heading[1].length;
        out.push("<h" + level + ">" + inlineMd(heading[2]) + "</h" + level + ">");
        i += 1;
        continue;
      }

      var q = line.match(/^>\s?(.*)$/);
      if (q) {
        flushPara();
        flushList();
        quote.push(q[1]);
        i += 1;
        continue;
      }
      if (quote.length) flushQuote();

      var ul = line.match(/^[-*+]\s+(.+)$/);
      var ol = line.match(/^\d+\.\s+(.+)$/);
      if (ul || ol) {
        flushPara();
        var ordered = !!ol;
        if (!list || listOrdered !== ordered) {
          flushList();
          list = [];
          listOrdered = ordered;
        }
        list.push((ul || ol)[1]);
        i += 1;
        continue;
      }
      if (list && /^\s{2,}\S/.test(line)) {
        list[list.length - 1] += "\n" + line.replace(/^\s+/, "");
        i += 1;
        continue;
      }
      if (list) flushList();

      if (/^\s*$/.test(line)) {
        flushPara();
        i += 1;
        continue;
      }
      para.push(line);
      i += 1;
    }
    flushAll();
    return out.join("\n");
  }

  root.renderMarkdown = renderMarkdown;
  root.escapeHtml = escapeHtml;
})(window);
