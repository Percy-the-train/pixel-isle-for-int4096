/* DATASTAT PIXEL LAB — sandbox scene with background + NPCs (window.SandboxScene) */
window.SandboxScene = (function () {
  "use strict";

  var canvas, ctx, bg, bgc, W = 720, H = 220;
  var npcs = [];
  var active = "data";
  var hover = -1;
  var start = 0;
  var onTalk = null;
  var SCALE = 2;

  var STATIONS = [
    { x: 90, k: "data" },
    { x: 270, k: "analysis" },
    { x: 460, k: "results" },
    { x: 640, k: "publish" }
  ];

  function init(cv) {
    canvas = cv;
    ctx = canvas.getContext("2d");
    W = canvas.width; H = canvas.height;
    bg = document.createElement("canvas");
    bg.width = W; bg.height = H;
    bgc = bg.getContext("2d");
    start = performance.now();
    canvas.addEventListener("mousemove", onMove);
    canvas.addEventListener("click", onClick);
    canvas.addEventListener("mouseleave", function () { hover = -1; canvas.style.cursor = "default"; });
    buildBackground();
    requestAnimationFrame(loop);
  }

  function setStep(step) { active = step; }
  function setTalkHandler(fn) { onTalk = fn; }

  /* ---------- background ---------- */
  function R(c, x, y, w, h) { bgc.fillStyle = c; bgc.fillRect(x, y, w, h); }
  function buildBackground() {
    if (!bgc) return;
    R("#242436", 0, 0, W, 120);
    for (var x = 0; x < W; x += 32) R("#1e1e2e", x, 0, 2, 120);
    R("#2c2c44", 0, 0, W, 6);

    // floor
    R("#6b4a2a", 0, 120, W, H - 120);
    for (var y = 120; y < H; y += 16) R("#7a5530", 0, y, W, 1);
    for (var lx = 0; lx < W; lx += 48) R("#5f4226", lx, 120, 1, H - 120);

    // rug
    R("#7f2b2b", 180, 142, 360, 66);
    R("#2f3f5a", 186, 148, 348, 54);
    R("#8a3a3a", 192, 154, 336, 42);
    R("#6a2424", 198, 160, 324, 30);

    // window (night)
    R("#3a2a20", 34, 16, 108, 70);
    R("#141a2a", 38, 20, 100, 62);
    R("#1b2340", 42, 24, 92, 54);
    R("#c8d0e0", 56, 32, 2, 2); R("#c8d0e0", 84, 28, 2, 2); R("#c8d0e0", 110, 38, 2, 2);
    R("#10162a", 60, 52, 22, 26); R("#10162a", 92, 46, 26, 32);
    R("#ffd24a", 64, 58, 3, 3); R("#ffd24a", 98, 52, 3, 3); R("#ffd24a", 104, 60, 3, 3);
    R("#3a2a20", 66, 24, 2, 54); R("#3a2a20", 38, 50, 100, 2);

    // bookshelf
    R("#5a3a1e", 470, 16, 92, 84);
    R("#3a2410", 474, 20, 84, 76);
    var bookCols = ["#c04a4a", "#4a7ac0", "#4aa05a", "#c9a24a", "#8a5ac0", "#e86969"];
    for (var row = 0; row < 3; row++) {
      for (var b = 0; b < 6; b++) R(bookCols[(row + b) % bookCols.length], 478 + b * 13, 26 + row * 24, 10, 18);
      R("#2a1c10", 474, 44 + row * 24, 84, 3);
    }

    // wall poster with bar chart
    R("#14141d", 588, 16, 114, 84);
    R("#2a2a3a", 592, 20, 106, 76);
    R("#3a3a5a", 600, 82, 90, 2);
    var bars = [22, 40, 30, 52, 36];
    for (var i = 0; i < bars.length; i++) {
      R(i % 2 ? "#6aa6ff" : "#ffd24a", 602 + i * 17, 82 - bars[i], 12, bars[i]);
    }
    R("#ffd24a", 596, 24, 60, 2);

    // plant
    R("#4a3418", 12, 150, 22, 18);
    R("#3a2410", 10, 168, 26, 10);
    R("#4f9a3a", 14, 134, 18, 18);
    R("#6cbf4f", 10, 140, 10, 12);
    R("#3a7a2a", 26, 138, 10, 14);
  }

  /* ---------- NPCs ---------- */
  function mkNpc(x, y, shirt, hair, skin, name, talk) {
    return { x: x, y: y, shirt: shirt, hair: hair, skin: skin, name: name, talk: talk, phase: Math.random() * 6.28 };
  }

  function generate(state) {
    npcs = [];
    if (state && state.data) {
      var d = state.data;
      if (d.design === "correlation") {
        npcs.push(mkNpc(210, 148, "#6aa6ff", "#3a2a1e", "#f2c48d", "Variable X",
          ["I represent the predictor (x).", "Do I move together with Y?"]));
        npcs.push(mkNpc(360, 156, "#6fbf58", "#201813", "#f2c48d", "Variable Y",
          ["I'm the outcome (y).", "The regression line predicts me from x."]));
      } else {
        var colors = ["#6aa6ff", "#6fbf58", "#ff8a8a", "#ffd24a", "#c08aff", "#5fd0c0"];
        var names = "ABCDEF";
        d.groups.forEach(function (g, i) {
          npcs.push(mkNpc(180 + i * 82, 146 + (i % 2) * 12, colors[i % colors.length], "#3a2a1e", "#f2c48d",
            "Group " + names[i],
            ["I'm an observation in Group " + names[i] + ".", "There are " + g.length + " of us in this group."]));
        });
      }
    }
    npcs.push(mkNpc(66, 150, "#e8e8f0", "#201813", "#f2c48d", "Dr. Pixel",
      ["Welcome to the lab!", "Generate data, then choose an analysis.", "Click a station above to switch modules."]));
  }

  /* ---------- drawing ---------- */
  function P(ox, oy, ux, uy, uw, uh, color) {
    ctx.fillStyle = color;
    ctx.fillRect(ox + ux * SCALE, oy + uy * SCALE, uw * SCALE, uh * SCALE);
  }
  function shadow(ox, oy) {
    ctx.fillStyle = "rgba(0,0,0,0.35)";
    ctx.fillRect(ox + 3 * SCALE, oy + 23 * SCALE, 10 * SCALE, 2 * SCALE);
  }
  function drawPerson(n, t) {
    var bob = Math.round(Math.sin(t / 380 + n.phase));
    var x = n.x, y = n.y + bob;
    shadow(x, n.y);
    P(x, y, 5, 17, 3, 5, "#3a4a6a");
    P(x, y, 9, 17, 3, 5, "#3a4a6a");
    P(x, y, 4, 22, 4, 2, "#241a14");
    P(x, y, 9, 22, 4, 2, "#241a14");
    P(x, y, 4, 10, 8, 8, n.shirt);
    P(x, y, 2, 11, 2, 6, n.shirt);
    P(x, y, 12, 11, 2, 6, n.shirt);
    P(x, y, 2, 17, 2, 1, n.skin);
    P(x, y, 12, 17, 2, 1, n.skin);
    P(x, y, 7, 9, 2, 1, n.skin);
    P(x, y, 4, 2, 8, 7, n.skin);
    P(x, y, 3, 1, 10, 2, n.hair);
    P(x, y, 3, 3, 1, 4, n.hair);
    P(x, y, 12, 3, 1, 4, n.hair);
    P(x, y, 5, 5, 1, 1, "#1a1a1a");
    P(x, y, 10, 5, 1, 1, "#1a1a1a");
    if (hover === npcs.indexOf(n)) {
      ctx.strokeStyle = "#ffd24a";
      ctx.lineWidth = 2;
      ctx.strokeRect(x - 2, y - 2, 16 * SCALE + 4, 24 * SCALE + 4);
      ctx.lineWidth = 1;
    }
  }

  function drawStations(t) {
    STATIONS.forEach(function (s) {
      ctx.fillStyle = "#5a3a1e"; ctx.fillRect(s.x - 42, 112, 84, 16);
      ctx.fillStyle = "#3a2410"; ctx.fillRect(s.x - 42, 128, 84, 14);
      ctx.fillStyle = "#1c1c2a"; ctx.fillRect(s.x - 26, 84, 52, 28);
      ctx.fillStyle = "#0c0c16"; ctx.fillRect(s.x - 23, 87, 46, 22);
      if (s.k === "data") {
        ctx.fillStyle = "#6aa6ff";
        for (var i = 0; i < 4; i++) ctx.fillRect(s.x - 18 + i * 9, 104 - (i + 1) * 4, 6, (i + 1) * 4);
      } else if (s.k === "analysis") {
        ctx.strokeStyle = "#6fbf58"; ctx.beginPath();
        ctx.moveTo(s.x - 18, 104); ctx.lineTo(s.x - 8, 96); ctx.lineTo(s.x + 2, 100); ctx.lineTo(s.x + 12, 90); ctx.lineTo(s.x + 18, 94);
        ctx.stroke();
      } else if (s.k === "results") {
        ctx.fillStyle = "#ffd24a";
        for (var b = 0; b < 3; b++) ctx.fillRect(s.x - 16 + b * 12, 104 - (b + 2) * 5, 8, (b + 2) * 5);
      } else {
        ctx.fillStyle = "#c8d0e0";
        ctx.fillRect(s.x - 16, 92, 32, 3); ctx.fillRect(s.x - 16, 98, 26, 3); ctx.fillRect(s.x - 16, 104, 30, 3);
      }
      if (active === s.k && Math.floor(t / 400) % 2 === 0) {
        ctx.strokeStyle = "#ffd24a"; ctx.lineWidth = 2;
        ctx.strokeRect(s.x - 30, 82, 60, 62);
        ctx.lineWidth = 1;
      }
    });
  }

  function loop(t) {
    ctx.drawImage(bg, 0, 0);
    drawStations(t);
    var order = npcs.slice().sort(function (a, b) { return a.y - b.y; });
    order.forEach(function (n) { drawPerson(n, t); });
    requestAnimationFrame(loop);
  }

  /* ---------- input ---------- */
  function toLocal(e) {
    var r = canvas.getBoundingClientRect();
    return { x: (e.clientX - r.left) * (W / r.width), y: (e.clientY - r.top) * (H / r.height) };
  }
  function hit(p) {
    for (var i = 0; i < npcs.length; i++) {
      var n = npcs[i];
      if (p.x >= n.x && p.x <= n.x + 16 * SCALE && p.y >= n.y && p.y <= n.y + 24 * SCALE) return i;
    }
    return -1;
  }
  function onMove(e) {
    hover = hit(toLocal(e));
    canvas.style.cursor = hover >= 0 ? "pointer" : "default";
  }
  function onClick(e) {
    var i = hit(toLocal(e));
    if (i >= 0 && onTalk) onTalk(npcs[i]);
  }

  return { init: init, generate: generate, setStep: setStep, setTalkHandler: setTalkHandler };
})();
