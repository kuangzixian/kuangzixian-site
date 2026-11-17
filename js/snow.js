(function () {
  var STORAGE = "kuang-snow";
  var BURST_MS = 8000;
  var FADE_MS = 2000;
  var DESKTOP_COUNT = 52;
  var MOBILE_COUNT = 28;

  var canvas = null;
  var ctx = null;
  var particles = [];
  var raf = 0;
  var running = false;
  var paused = false;
  var startAt = 0;
  var lastTs = 0;
  var width = 0;
  var height = 0;

  function reducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function isMobile() {
    return window.innerWidth <= 800;
  }

  function prefOn() {
    try {
      return localStorage.getItem(STORAGE) !== "off";
    } catch (e) {
      return true;
    }
  }

  function setPref(on) {
    try {
      localStorage.setItem(STORAGE, on ? "on" : "off");
    } catch (e) {}
    syncButtons();
  }

  function palette() {
    var skin = document.documentElement.getAttribute("data-skin") || "blue";
    if (skin === "pink") {
      return ["#ffffff", "#ffe0ec", "#f5a8c4", "#ee7aa8", "#ffe56a", "#fff4a8", "#ffd24a"];
    }
    if (skin === "night") {
      return ["#ffffff", "#fff8d0", "#ffe56a", "#ffd24a", "#fff4a8", "#f5e6a0", "#fffdf0"];
    }
    return ["#ffffff", "#f0f7ff", "#e8f4ff", "#c9e9ff", "#7ec8f7", "#dbeeff", "#ffffff"];
  }

  function pickColor() {
    var list = palette();
    return list[(Math.random() * list.length) | 0];
  }

  function makeParticle(spread) {
    var typeRand = Math.random();
    var type = typeRand < 0.45 ? "flake" : typeRand < 0.8 ? "sparkle" : "glint";
    return {
      x: Math.random() * width,
      y: spread ? Math.random() * height * 0.7 - 20 : -10 - Math.random() * 80,
      size: type === "glint" ? 1.2 + Math.random() * 2.2 : 5 + Math.random() * 8,
      vy: 18 + Math.random() * 36,
      sway: 10 + Math.random() * 22,
      freq: 0.6 + Math.random() * 1.4,
      phase: Math.random() * Math.PI * 2,
      rot: Math.random() * Math.PI * 2,
      vr: (Math.random() - 0.5) * 1.4,
      type: type,
      color: pickColor(),
      alpha: 0.55 + Math.random() * 0.45,
      twinkleFreq: 1.5 + Math.random() * 3,
      twinklePhase: Math.random() * Math.PI * 2
    };
  }

  function seed() {
    var n = isMobile() ? MOBILE_COUNT : DESKTOP_COUNT;
    particles = [];
    for (var i = 0; i < n; i++) particles.push(makeParticle(true));
  }

  function ensureCanvas() {
    if (canvas) return;
    canvas = document.createElement("canvas");
    canvas.id = "qzSnow";
    canvas.setAttribute("aria-hidden", "true");
    document.body.appendChild(canvas);
    ctx = canvas.getContext("2d", { alpha: true });
    resize();
  }

  function resize() {
    if (!canvas || !ctx) return;
    width = window.innerWidth;
    height = window.innerHeight;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.floor(width * dpr));
    canvas.height = Math.max(1, Math.floor(height * dpr));
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function drawFlake(p, tw) {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.globalAlpha = p.alpha * tw;
    ctx.strokeStyle = p.color;
    ctx.lineWidth = Math.max(0.8, p.size / 8);
    ctx.lineCap = "round";
    var r = p.size;
    for (var i = 0; i < 6; i++) {
      ctx.rotate(Math.PI / 3);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(0, -r);
      ctx.moveTo(0, -r * 0.5);
      ctx.lineTo(-r * 0.22, -r * 0.7);
      ctx.moveTo(0, -r * 0.5);
      ctx.lineTo(r * 0.22, -r * 0.7);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawSparkle(p, tw) {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.globalAlpha = p.alpha * tw;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    var r = p.size;
    var r2 = p.size * 0.28;
    for (var i = 0; i < 8; i++) {
      var a = (i * Math.PI) / 4 - Math.PI / 2;
      var rad = i % 2 === 0 ? r : r2;
      if (i === 0) ctx.moveTo(Math.cos(a) * rad, Math.sin(a) * rad);
      else ctx.lineTo(Math.cos(a) * rad, Math.sin(a) * rad);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawGlint(p, tw) {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.globalAlpha = p.alpha * tw;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(0, 0, p.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function fadeFactor(now) {
    var elapsed = now - startAt;
    if (elapsed <= BURST_MS) return 1;
    var t = (elapsed - BURST_MS) / FADE_MS;
    if (t >= 1) return 0;
    return 1 - t;
  }

  function tick(ts) {
    if (!running || paused) return;
    if (!lastTs) lastTs = ts;
    var dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;
    var now = performance.now();
    var fade = fadeFactor(now);
    if (fade <= 0) {
      stop(false);
      return;
    }

    ctx.clearRect(0, 0, width, height);
    ctx.globalAlpha = 1;
    var recycle = fade >= 1;
    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      p.y += p.vy * dt;
      p.x += Math.sin((now / 1000) * p.freq + p.phase) * p.sway * dt;
      p.rot += p.vr * dt;
      if (recycle) {
        if (p.y - p.size > height + 8) {
          particles[i] = makeParticle(false);
          p = particles[i];
        } else if (p.x < -20) {
          p.x = width + 10;
        } else if (p.x > width + 20) {
          p.x = -10;
        }
      }
      var tw = 0.55 + 0.45 * Math.sin((now / 1000) * p.twinkleFreq + p.twinklePhase);
      var visible = p.alpha * tw * fade;
      if (visible <= 0.02) continue;
      if (p.type === "flake") drawFlake(p, tw * fade);
      else if (p.type === "sparkle") drawSparkle(p, tw * fade);
      else drawGlint(p, tw * fade);
    }

    raf = requestAnimationFrame(tick);
  }

  function stop(clearPref) {
    running = false;
    paused = false;
    lastTs = 0;
    if (raf) {
      cancelAnimationFrame(raf);
      raf = 0;
    }
    if (ctx && canvas) ctx.clearRect(0, 0, width, height);
    if (canvas) canvas.hidden = true;
    if (clearPref) setPref(false);
    else syncButtons();
  }

  function start() {
    if (reducedMotion()) {
      stop(false);
      syncButtons();
      return;
    }
    ensureCanvas();
    resize();
    seed();
    canvas.hidden = false;
    running = true;
    paused = false;
    startAt = performance.now();
    lastTs = 0;
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(tick);
    setPref(true);
  }

  function syncButtons() {
    var on = prefOn() && !reducedMotion();
    var playing = running && !paused;
    var btn = document.getElementById("qzSnowBtn");
    if (btn) {
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.classList.toggle("is-on", on);
      btn.classList.toggle("is-playing", playing);
      if (reducedMotion()) {
        btn.setAttribute("title", "已按系统设置关闭动态效果");
        btn.setAttribute("aria-label", "飘雪特效已关闭（减少动态效果）");
      } else {
        btn.setAttribute("title", on ? "飘雪特效开启，点击可重播或关闭" : "开启飘雪特效");
        btn.setAttribute("aria-label", on ? "飘雪特效：开" : "飘雪特效：关");
      }
    }
    var toggle = document.getElementById("qzSnowToggle");
    if (toggle) {
      var zh = toggle.querySelector(".zh");
      var en = toggle.querySelector(".en-only");
      if (zh) zh.textContent = on ? "飘雪特效：开" : "飘雪特效：关";
      if (en) en.textContent = on ? "Snow: On" : "Snow: Off";
      toggle.setAttribute("aria-pressed", on ? "true" : "false");
      toggle.classList.toggle("is-on", on);
    }
  }

  function onButtonClick() {
    if (reducedMotion()) return;
    if (running) {
      stop(true);
      return;
    }
    start();
  }

  window.addEventListener("resize", function () {
    if (!canvas) return;
    resize();
  });

  document.addEventListener("visibilitychange", function () {
    if (!running) return;
    if (document.hidden) {
      paused = true;
      lastTs = 0;
      if (raf) {
        cancelAnimationFrame(raf);
        raf = 0;
      }
    } else if (paused) {
      paused = false;
      lastTs = 0;
      raf = requestAnimationFrame(tick);
    }
  });

  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    var onMq = function () {
      if (reducedMotion()) stop(false);
      syncButtons();
    };
    if (mq.addEventListener) mq.addEventListener("change", onMq);
    else if (mq.addListener) mq.addListener(onMq);
  }

  function bind() {
    var btn = document.getElementById("qzSnowBtn");
    if (btn) btn.addEventListener("click", onButtonClick);
    var toggle = document.getElementById("qzSnowToggle");
    if (toggle) toggle.addEventListener("click", onButtonClick);
    syncButtons();
    if (prefOn() && !reducedMotion()) start();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
