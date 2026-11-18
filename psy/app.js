/* DATASTAT PIXEL LAB â€” game logic + UI (window.DataStatGame) */
(function () {
  "use strict";
  var S = window.Stats;
  function $(id) { return document.getElementById(id); }

  var state = {
    step: "data",
    seed: 12345,
    design: "two",
    distribution: "normal",
    n: 30,
    groupsCount: 3,
    mean: 50,
    spread: 10,
    effect: 0.6,
    data: null,
    question: null,
    alpha: 0.05,
    alternative: "two",
    ran: false,
    results: null,
    narrative: "",
    published: false,
    reportScore: 0,
    objectives: { data: false, question: false, run: false, interpret: false, publish: false }
  };

  var QUESTIONS = [
    { id: "compare2", text: "Are these two groups different?", test: "t", need: "two", rec: "Welch two-sample t-test" },
    { id: "compare3", text: "Do three or more groups differ?", test: "anova", need: "three", rec: "One-way ANOVA" },
    { id: "relationship", text: "Are two variables related?", test: "correlation", need: "correlation", rec: "Pearson correlation" },
    { id: "predict", text: "Can one variable predict another?", test: "regression", need: "correlation", rec: "Simple linear regression" }
  ];
  function qById(id) { for (var i = 0; i < QUESTIONS.length; i++) if (QUESTIONS[i].id === id) return QUESTIONS[i]; return null; }

  function fmt(x, d) { return (typeof x === "number" && isFinite(x)) ? x.toFixed(d === undefined ? 3 : d) : "â€”"; }
  function pStr(p) { return p < 0.001 ? "< .001" : "= " + fmt(p, 3); }
  function r2(x) { return Math.round(x * 100) / 100; }

  /* ---------- data generation ---------- */
  function generateData() {
    var rng = S.makeSampler(state.seed);
    var dist = state.distribution;
    function sample(m) {
      if (dist === "uniform") return rng.uniform(m, state.spread);
      if (dist === "exponential") return rng.exponential(m, state.spread);
      if (dist === "bimodal") return rng.bimodal(m, state.spread);
      return rng.normal(m, state.spread);
    }
    if (state.design === "correlation") {
      var n = Math.max(5, state.n), x = [], y = [];
      var r = Math.max(-0.99, Math.min(0.99, state.effect));
      for (var i = 0; i < n; i++) {
        var xv = rng.normal(state.mean, state.spread);
        var noise = rng.normal(0, state.spread * Math.sqrt(Math.max(0.0001, 1 - r * r)));
        x.push(r2(xv));
        y.push(r2(state.mean + r * (xv - state.mean) + noise));
      }
      state.data = { design: "correlation", x: x, y: y };
    } else {
      var k = state.design === "three" ? Math.max(3, state.groupsCount) : 2;
      var groups = [];
      for (var g = 0; g < k; g++) {
        var m = state.mean + state.effect * 10 * (g - (k - 1) / 2);
        var arr = [];
        for (var j = 0; j < Math.max(5, state.n); j++) arr.push(r2(sample(m)));
        groups.push(arr);
      }
      state.data = { design: state.design === "three" ? "three" : "two", groups: groups };
    }
    state.ran = false; state.results = null; state.narrative = ""; state.published = false;
    state.reportScore = 0;
    state.objectives.data = true;
    state.objectives.run = false; state.objectives.interpret = false; state.objectives.publish = false;
    state.seed = (state.seed * 1103515245 + 12345) >>> 0;
    refreshAll();
    if (window.SandboxScene) window.SandboxScene.generate(state);
    if ($("sceneCaption")) $("sceneCaption").textContent = "Sandbox generated — click an NPC to chat.";
  }

  function loadSample() {
    var which = Math.floor(Math.random() * 3);
    if (which === 0) {
      state.design = "two"; state.distribution = "normal"; state.n = 24; state.mean = 72; state.spread = 9; state.effect = 0.8;
    } else if (which === 1) {
      state.design = "three"; state.distribution = "normal"; state.n = 20; state.groupsCount = 3; state.mean = 60; state.spread = 12; state.effect = 1.2;
    } else {
      state.design = "correlation"; state.distribution = "normal"; state.n = 40; state.mean = 50; state.spread = 12; state.effect = 0.72;
    }
    state.seed = (Date.now() ^ (Math.random() * 1e9)) >>> 0;
    syncControls();
    generateData();
  }

  /* ---------- recommendation / compatibility ---------- */
  function compatible(q) {
    var info = qById(q); var d = state.data;
    if (!info) return { ok: false, msg: "Choose a research question." };
    if (!d) return { ok: false, msg: "Generate a dataset first (step 1)." };
    if (info.need === "two") return (d.groups && d.groups.length >= 2) ? { ok: true, msg: "" } : { ok: false, msg: "This question needs a two-group dataset." };
    if (info.need === "three") return (d.groups && d.groups.length >= 3) ? { ok: true, msg: "" } : { ok: false, msg: "This question needs a 3+ group dataset." };
    if (info.need === "correlation") return (d.design === "correlation") ? { ok: true, msg: "" } : { ok: false, msg: "This question needs a two-variable (x, y) dataset." };
    return { ok: false, msg: "" };
  }

  function renderQuestions() {
    var box = $("questionList");
    box.innerHTML = "";
    QUESTIONS.forEach(function (q) {
      var b = document.createElement("button");
      b.className = "questionBtn" + (state.question === q.id ? " sel" : "");
      b.textContent = q.text;
      b.addEventListener("click", function () {
        state.question = q.id;
        state.objectives.question = true;
        renderQuestions();
        renderRecommendation();
        updateObjectives();
      });
      box.appendChild(b);
    });
  }

  function renderRecommendation() {
    var card = $("recommendation");
    var info = qById(state.question);
    if (!info) { card.classList.add("hidden"); $("analysisNote").textContent = ""; updateRunBtn(); return; }
    var comp = compatible(state.question);
    card.classList.remove("hidden");
    card.innerHTML =
      '<h3>Recommended test</h3>' +
      '<div class="kv"><div class="k">Question</div><div>' + info.text + '</div>' +
      '<div class="k">Recommended</div><div><b>' + info.rec + '</b></div>' +
      '<div class="k">Why</div><div>' + whyText(info) + '</div></div>';
    var note = $("analysisNote");
    if (!comp.ok) { note.textContent = "âš  " + comp.msg; }
    else { note.textContent = "Dataset is compatible. Set alpha and run the test."; }
    updateRunBtn();
  }
  function whyText(info) {
    if (info.test === "t") return "Comparing the means of two independent groups uses a t-test.";
    if (info.test === "anova") return "Comparing means across 3+ groups uses a one-way ANOVA.";
    if (info.test === "correlation") return "Testing whether two numeric variables move together uses Pearson correlation.";
    if (info.test === "regression") return "Predicting an outcome from a predictor uses simple linear regression.";
    return "";
  }

  /* ---------- run analysis ---------- */
  function runAnalysis() {
    var info = qById(state.question);
    var comp = compatible(state.question);
    if (!info || !comp.ok) { $("analysisNote").textContent = "âš  " + comp.msg; return; }
    var d = state.data, res;
    if (info.test === "t") {
      res = S.tTest(d.groups[0], d.groups[1], state.alternative); res.testId = "t";
    } else if (info.test === "anova") {
      res = S.anova(d.groups, state.alternative); res.testId = "anova";
    } else if (info.test === "correlation") {
      res = S.pearson(d.x, d.y, state.alternative); res.testId = "correlation";
    } else {
      res = S.linreg(d.x, d.y, state.alternative); res.testId = "regression";
    }
    res.alpha = state.alpha;
    res.significant = res.p < state.alpha;
    state.results = res;
    state.ran = true;
    state.objectives.run = true;
    state.objectives.interpret = true;
    state.narrative = buildNarrative(res);
    state.published = false;
    state.reportScore = 0;
    refreshAll();
    goStep("results");
  }

  function effectPhrase(res) {
    if (res.testId === "t") { var d = Math.abs(res.d); return d < 0.2 ? "very small" : d < 0.5 ? "small" : d < 0.8 ? "moderate" : "large"; }
    if (res.testId === "anova") { var e = res.eta2; return e < 0.01 ? "very small" : e < 0.06 ? "small" : e < 0.14 ? "moderate" : "large"; }
    if (res.testId === "correlation") { var r = Math.abs(res.r); return r < 0.1 ? "very weak" : r < 0.3 ? "weak" : r < 0.5 ? "moderate" : r < 0.7 ? "strong" : "very strong"; }
    if (res.testId === "regression") { var q = res.r2; return q < 0.04 ? "very weak" : q < 0.09 ? "weak" : q < 0.25 ? "moderate" : "strong"; }
    return "";
  }

  function buildNarrative(res) {
    var a = res.alpha, sig = res.significant;
    var lead = sig ? "A statistically significant result was found" : "No statistically significant result was found";
    var lines = [];
    if (res.testId === "t") {
      lines.push("Welch's two-sample t-test compared Group A (M = " + fmt(res.mean1, 2) + ", SD = " + fmt(res.sd1, 2) +
        ", n = " + res.n1 + ") with Group B (M = " + fmt(res.mean2, 2) + ", SD = " + fmt(res.sd2, 2) + ", n = " + res.n2 + ").");
      lines.push(lead + ": t(" + fmt(res.df, 1) + ") = " + fmt(res.t, 2) + ", p " + pStr(res.p) + ", alpha = " + a + ".");
      lines.push("The standardised difference (Cohen's d = " + fmt(res.d, 2) + ") is a " + effectPhrase(res) + " effect. " +
        (sig ? "In plain terms, the two groups differ more than we would expect by chance." : "In plain terms, the data do not provide strong evidence that the groups differ."));
    } else if (res.testId === "anova") {
      lines.push("A one-way ANOVA compared " + res.k + " groups (N = " + res.N + ").");
      lines.push(lead + ": F(" + res.df1 + ", " + res.df2 + ") = " + fmt(res.F, 2) + ", p " + pStr(res.p) + ", alpha = " + a + ".");
      lines.push("Eta-squared = " + fmt(res.eta2, 2) + " (" + effectPhrase(res) + " effect). " +
        (sig ? "At least one group mean differs from the others." : "The group means are consistent with chance variation."));
    } else if (res.testId === "correlation") {
      var dir = res.r >= 0 ? "positive" : "negative";
      lines.push("Pearson correlation examined the association between x and y (n = " + res.n + ").");
      lines.push(lead + ": r(" + res.df + ") = " + fmt(res.r, 2) + ", p " + pStr(res.p) + ", alpha = " + a + ".");
      lines.push("This is a " + effectPhrase(res) + ", " + dir + " relationship. " +
        (sig ? "As one variable rises, the other tends to " + (res.r >= 0 ? "rise" : "fall") + "." : "The variables do not appear to move together."));
    } else {
      lines.push("Simple linear regression predicted y from x (n = " + res.n + ").");
      lines.push("Model: y = " + fmt(res.slope, 3) + "Â·x + " + fmt(res.intercept, 3) + ". RÂ² = " + fmt(res.r2, 2) +
        ", F(" + res.df1 + ", " + res.df2 + ") = " + fmt(res.F, 2) + ", p " + pStr(res.p) + ".");
      lines.push(lead + ". The predictor explains " + fmt(res.r2 * 100, 1) + "% of the variance (" + effectPhrase(res) + " effect). " +
        (sig ? "The predictor is useful for prediction." : "The predictor adds little predictive value."));
    }
    lines.push("Remember to check assumptions (independence, normality, and variance) before generalising.");
    return lines.join("\n\n");
  }

  /* ---------- charts ---------- */
  function chartBase(canvas) {
    var ctx = canvas.getContext("2d");
    var W = canvas.width, H = canvas.height;
    ctx.fillStyle = "#0c0c16"; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "#24243a"; ctx.lineWidth = 1;
    for (var x = 0; x < W; x += 20) { ctx.beginPath(); ctx.moveTo(x + .5, 0); ctx.lineTo(x + .5, H); ctx.stroke(); }
    for (var y = 0; y < H; y += 20) { ctx.beginPath(); ctx.moveTo(0, y + .5); ctx.lineTo(W, y + .5); ctx.stroke(); }
    return { ctx: ctx, W: W, H: H };
  }
  function drawHistogram(canvas, values, color) {
    var b = chartBase(canvas), ctx = b.ctx, W = b.W, H = b.H;
    var pad = 24, bins = 10;
    var min = Math.min.apply(null, values), max = Math.max.apply(null, values);
    if (min === max) max = min + 1;
    var counts = new Array(bins).fill(0);
    values.forEach(function (v) { var i = Math.min(bins - 1, Math.floor((v - min) / (max - min) * bins)); counts[i]++; });
    var maxC = Math.max.apply(null, counts) || 1;
    var chartW = W - pad - 10, chartH = H - pad - 12;
    ctx.strokeStyle = "#5a5a7a"; ctx.beginPath(); ctx.moveTo(pad, 8); ctx.lineTo(pad, H - pad); ctx.lineTo(W - 10, H - pad); ctx.stroke();
    var bw = chartW / bins;
    for (var i = 0; i < bins; i++) {
      var h = counts[i] / maxC * chartH;
      ctx.fillStyle = color;
      ctx.fillRect(Math.round(pad + i * bw + 1), Math.round(H - pad - h), Math.ceil(bw - 2), Math.ceil(h));
    }
    ctx.fillStyle = "#8a8aa0"; ctx.font = "9px monospace";
    ctx.fillText(fmt(min, 1), pad, H - 8);
    ctx.fillText(fmt(max, 1), W - 40, H - 8);
  }
  function drawBox(canvas, groups, labels) {
    var b = chartBase(canvas), ctx = b.ctx, W = b.W, H = b.H;
    var all = [].concat.apply([], groups);
    var min = Math.min.apply(null, all), max = Math.max.apply(null, all);
    if (min === max) max = min + 1;
    var padT = 14, padB = 26, padL = 26, padR = 10;
    var top = 8, bottom = H - padB;
    function yy(v) { return bottom - (v - min) / (max - min) * (bottom - top); }
    ctx.strokeStyle = "#5a5a7a"; ctx.beginPath(); ctx.moveTo(padL, top); ctx.lineTo(padL, bottom); ctx.lineTo(W - padR, bottom); ctx.stroke();
    var n = groups.length, slot = (W - padL - padR) / n;
    for (var g = 0; g < n; g++) {
      var st = S.boxStats(groups[g]);
      var cx = padL + slot * (g + 0.5);
      var bw = Math.min(26, slot * 0.5);
      ctx.strokeStyle = "#8a8aa0";
      ctx.beginPath(); ctx.moveTo(cx, yy(st.min)); ctx.lineTo(cx, yy(st.max)); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx - bw / 2, yy(st.min)); ctx.lineTo(cx + bw / 2, yy(st.min)); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx - bw / 2, yy(st.max)); ctx.lineTo(cx + bw / 2, yy(st.max)); ctx.stroke();
      ctx.fillStyle = "#6aa6ff";
      ctx.fillRect(Math.round(cx - bw / 2), Math.round(yy(st.q3)), Math.round(bw), Math.max(1, Math.round(yy(st.q1) - yy(st.q3))));
      ctx.strokeStyle = "#0c0c16"; ctx.beginPath(); ctx.moveTo(cx - bw / 2, yy(st.q1)); ctx.lineTo(cx + bw / 2, yy(st.q1)); ctx.stroke();
      ctx.strokeStyle = "#ffd24a"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(cx - bw / 2, yy(st.median)); ctx.lineTo(cx + bw / 2, yy(st.median)); ctx.stroke(); ctx.lineWidth = 1;
      ctx.fillStyle = "#8a8aa0"; ctx.font = "9px monospace";
      ctx.fillText(labels[g], Math.round(cx - 6), H - 8);
    }
  }
  function drawScatter(canvas, x, y, slope, intercept) {
    var b = chartBase(canvas), ctx = b.ctx, W = b.W, H = b.H;
    var padL = 28, padB = 24, padT = 10, padR = 12;
    var minX = Math.min.apply(null, x), maxX = Math.max.apply(null, x);
    var minY = Math.min.apply(null, y), maxY = Math.max.apply(null, y);
    if (minX === maxX) maxX = minX + 1;
    if (minY === maxY) maxY = minY + 1;
    function px(v) { return padL + (v - minX) / (maxX - minX) * (W - padL - padR); }
    function py(v) { return H - padB - (v - minY) / (maxY - minY) * (H - padT - padB); }
    ctx.strokeStyle = "#5a5a7a"; ctx.beginPath(); ctx.moveTo(padL, padT); ctx.lineTo(padL, H - padB); ctx.lineTo(W - padR, H - padB); ctx.stroke();
    ctx.fillStyle = "#6fbf58";
    for (var i = 0; i < x.length; i++) ctx.fillRect(Math.round(px(x[i])) - 1, Math.round(py(y[i])) - 1, 3, 3);
    if (typeof slope === "number" && isFinite(slope)) {
      ctx.strokeStyle = "#ffd24a"; ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(px(minX), py(slope * minX + intercept));
      ctx.lineTo(px(maxX), py(slope * maxX + intercept));
      ctx.stroke(); ctx.lineWidth = 1;
    }
    ctx.fillStyle = "#8a8aa0"; ctx.font = "9px monospace";
    ctx.fillText("x", W - 16, H - 8);
    ctx.fillText("y", 8, 16);
  }

  function renderCharts(res) {
    var d = state.data;
    if (res.testId === "t" || res.testId === "anova") {
      var groups = res.testId === "t" ? [d.groups[0], d.groups[1]] : d.groups;
      var labels = groups.map(function (_, i) { return "G" + (i + 1); });
      drawHistogram($("chart1"), [].concat.apply([], groups), "#6aa6ff");
      $("cap1").textContent = "Histogram of all observations";
      drawBox($("chart2"), groups, labels);
      $("cap2").textContent = "Box plot by group";
    } else if (res.testId === "correlation") {
      drawScatter($("chart1"), d.x, d.y, null, null);
      $("cap1").textContent = "Scatter plot of x vs y";
      drawHistogram($("chart2"), d.y, "#6fbf58");
      $("cap2").textContent = "Distribution of y";
    } else {
      drawScatter($("chart1"), d.x, d.y, res.slope, res.intercept);
      $("cap1").textContent = "Scatter with regression line";
      drawHistogram($("chart2"), d.x, "#ff8a8a");
      $("cap2").textContent = "Distribution of x";
    }
  }

  /* ---------- results + report ---------- */
  function renderResults() {
    var res = state.results;
    if (!res) { $("resultsSummary").innerHTML = '<span class="note">Run an analysis first.</span>'; return; }
    var html = '<h3>' + res.test + '</h3><div class="kv">';
    if (res.testId === "t") {
      html += row("Statistic", "t = " + fmt(res.t, 3)) + row("df", fmt(res.df, 2)) +
        row("p-value", fmt(res.p, 4)) + row("Alpha", res.alpha) +
        row("Sig.", res.significant ? '<span class="sig">YES</span>' : '<span class="nosig">NO</span>') +
        row("Group A", "M = " + fmt(res.mean1, 2) + ", SD = " + fmt(res.sd1, 2) + ", n = " + res.n1) +
        row("Group B", "M = " + fmt(res.mean2, 2) + ", SD = " + fmt(res.sd2, 2) + ", n = " + res.n2) +
        row("Effect size", "Cohen's d = " + fmt(res.d, 2));
    } else if (res.testId === "anova") {
      html += row("Statistic", "F = " + fmt(res.F, 3)) + row("df", res.df1 + ", " + res.df2) +
        row("p-value", fmt(res.p, 4)) + row("Alpha", res.alpha) +
        row("Sig.", res.significant ? '<span class="sig">YES</span>' : '<span class="nosig">NO</span>') +
        row("Groups", res.k + " (N = " + res.N + ")") +
        row("Effect size", "Î·Â² = " + fmt(res.eta2, 3));
    } else if (res.testId === "correlation") {
      html += row("Statistic", "r = " + fmt(res.r, 3)) + row("df", res.df) +
        row("p-value", fmt(res.p, 4)) + row("Alpha", res.alpha) +
        row("Sig.", res.significant ? '<span class="sig">YES</span>' : '<span class="nosig">NO</span>') +
        row("n", res.n);
    } else {
      html += row("Equation", "y = " + fmt(res.slope, 3) + "Â·x + " + fmt(res.intercept, 3)) +
        row("RÂ²", fmt(res.r2, 3)) + row("F", fmt(res.F, 2)) + row("df", res.df1 + ", " + res.df2) +
        row("p-value", fmt(res.p, 4)) + row("Sig.", res.significant ? '<span class="sig">YES</span>' : '<span class="nosig">NO</span>');
    }
    html += "</div>";
    $("resultsSummary").innerHTML = html;
    $("narrative").textContent = state.narrative;
    renderCharts(res);
  }
  function row(k, v) { return '<div class="k">' + k + '</div><div>' + v + '</div>'; }

  function updateObjectives() {
    var defs = [
      ["data", "Generate / load a dataset"],
      ["question", "Choose a research question"],
      ["run", "Run a statistical test"],
      ["interpret", "Review the interpretation"],
      ["publish", "Publish a conclusion"]
    ];
    var box = $("objectives");
    box.innerHTML = "";
    var done = 0;
    defs.forEach(function (d) {
      var ok = !!state.objectives[d[0]];
      if (ok) done++;
      var el = document.createElement("div");
      el.className = "obj" + (ok ? " done" : "");
      el.innerHTML = '<span class="box">' + (ok ? "â– " : "â–¡") + '</span><span>' + d[1] + '</span>';
      box.appendChild(el);
    });
    $("scoreVal").textContent = (done * 20) + (state.reportScore || 0);
  }

  function publish() {
    if (!state.results) { return; }
    var title = $("titleInput").value.trim();
    var concl = $("conclusionInput").value.trim();
    if (!title || !concl) { alert("Please add a title and a conclusion."); return; }
    var res = state.results;
    var score = 10;
    var correctTest = res.testId === qById(state.question).test;
    if (correctTest) score += 20;
    var text = concl.toLowerCase();
    var saysNotSig = /not\s+significant|no\s+significant|did\s+not\s+find|no\s+evidence/.test(text);
    var saysSig = /\bsignificant\b/.test(text) && !saysNotSig;
    var consistent = res.significant ? saysSig : saysNotSig;
    if (consistent) score += 20;
    if (concl.length > 25) score += 10;
    state.reportScore = score;
    state.published = true;
    state.objectives.publish = true;

    var html = '<h3>PUBLISHED REPORT</h3>';
    html += '<div class="scoreline">Score: ' + score + ' / 60</div><div class="kv" style="margin-top:8px;">';
    html += row("Title", title);
    html += row("Test used", res.test);
    html += row("Correct test?", correctTest ? '<span class="sig">YES</span>' : '<span class="nosig">NO â€” expected ' + qById(state.question).rec + '</span>');
    html += row("Significant?", res.significant ? "Yes (p " + pStr(res.p) + ")" : "No (p " + pStr(res.p) + ")");
    html += row("Interpretation", consistent ? '<span class="sig">Consistent with data</span>' : '<span class="nosig">Inconsistent with the p-value</span>');
    html += "</div>";
    html += '<div class="narrative" style="margin-top:8px;">' + concl.replace(/</g, "&lt;") + "</div>";
    $("report").innerHTML = html;
    $("report").classList.remove("hidden");
    var badge = $("badge");
    badge.classList.remove("hidden");
    badge.textContent = score >= 55 ? "â˜… GOLD RESEARCHER â˜…" : score >= 40 ? "SILVER ANALYST" : score >= 25 ? "BRONZE APPRENTICE" : "KEEP PRACTICING";
    updateObjectives();
  }

  /* ---------- navigation / refresh ---------- */
  function goStep(step) {
    state.step = step;
    ["data", "analysis", "results", "publish"].forEach(function (s) {
      $("panel-" + s).classList.toggle("hidden", s !== step);
    });
    Array.prototype.forEach.call(document.querySelectorAll("#steps button"), function (b) {
      b.classList.toggle("active", b.dataset.step === step);
    });
    if (window.SandboxScene) window.SandboxScene.setStep(step);
  }
  function updateNav() {
    var canResults = !!state.ran;
    document.querySelector('#steps button[data-step="results"]').disabled = !canResults;
    document.querySelector('#steps button[data-step="publish"]').disabled = !canResults;
  }
  function updateRunBtn() {
    var comp = compatible(state.question);
    $("runBtn").disabled = !comp.ok;
  }

  function syncControls() {
    $("designSelect").value = state.design;
    $("distSelect").value = state.distribution;
    $("nInput").value = state.n;
    $("groupsInput").value = state.groupsCount;
    $("meanInput").value = state.mean;
    $("spreadInput").value = state.spread;
    $("effectInput").value = state.effect;
  }

  function renderDataTable() {
    var t = $("dataTable"), d = state.data;
    if (!d) { t.innerHTML = '<tbody><tr><td class="note">No dataset yet. Click â€œGenerate dataâ€.</td></tr></tbody>'; return; }
    var html;
    if (d.design === "correlation") {
      html = '<thead><tr><th>#</th><th>x</th><th>y</th></tr></thead><tbody>';
      for (var i = 0; i < Math.min(d.x.length, 80); i++) {
        html += '<tr><td>' + (i + 1) + '</td><td><input data-k="x" data-i="' + i + '" type="number" step="0.01" value="' + d.x[i] + '"></td>' +
          '<td><input data-k="y" data-i="' + i + '" type="number" step="0.01" value="' + d.y[i] + '"></td></tr>';
      }
      html += "</tbody>";
    } else {
      html = '<thead><tr><th>Group</th><th>Value</th></tr></thead><tbody>';
      d.groups.forEach(function (g, gi) {
        g.forEach(function (v, vi) {
          html += '<tr><td>G' + (gi + 1) + '</td><td><input data-k="g" data-g="' + gi + '" data-i="' + vi + '" type="number" step="0.01" value="' + v + '"></td></tr>';
        });
      });
      html += "</tbody>";
    }
    t.innerHTML = html;
    Array.prototype.forEach.call(t.querySelectorAll("input"), function (inp) {
      inp.addEventListener("change", function () {
        var v = parseFloat(inp.value); if (!isFinite(v)) v = 0;
        if (inp.dataset.k === "x") state.data.x[+inp.dataset.i] = v;
        else if (inp.dataset.k === "y") state.data.y[+inp.dataset.i] = v;
        else state.data.groups[+inp.dataset.g][+inp.dataset.i] = v;
        state.ran = false; state.results = null; state.objectives.run = false; state.objectives.interpret = false;
        updateNav(); updateObjectives();
      });
    });
    var count = d.design === "correlation" ? d.x.length : d.groups.reduce(function (a, g) { return a + g.length; }, 0);
    $("dataInfo").textContent = "Dataset: " + (d.design === "correlation" ? "x/y, n = " + count : d.groups.length + " groups, N = " + count);
  }

  function refreshAll() {
    syncControls();
    renderDataTable();
    renderQuestions();
    renderRecommendation();
    renderResults();
    updateNav();
    updateObjectives();
    updateRunBtn();
  }

  /* ---------- wiring ---------- */
  function init() {
    $("genBtn").addEventListener("click", function () {
      state.design = $("designSelect").value;
      state.distribution = $("distSelect").value;
      state.n = Math.max(5, parseInt($("nInput").value, 10) || 30);
      state.groupsCount = Math.max(3, parseInt($("groupsInput").value, 10) || 3);
      state.mean = parseFloat($("meanInput").value) || 50;
      state.spread = Math.max(1, parseFloat($("spreadInput").value) || 10);
      state.effect = parseFloat($("effectInput").value);
      if (!isFinite(state.effect)) state.effect = 0;
      generateData();
    });
    $("sampleBtn").addEventListener("click", loadSample);
    $("alphaSelect").addEventListener("change", function () { state.alpha = parseFloat(this.value); });
    $("altSelect").addEventListener("change", function () { state.alternative = this.value; });
    $("runBtn").addEventListener("click", runAnalysis);
    $("toPublishBtn").addEventListener("click", function () {
      if (!state.ran) return;
      $("conclusionInput").value = state.narrative.split("\n\n").slice(0, 2).join(" ");
      goStep("publish");
    });
    $("publishBtn").addEventListener("click", publish);
    Array.prototype.forEach.call(document.querySelectorAll("#steps button"), function (b) {
      b.addEventListener("click", function () { if (!b.disabled) goStep(b.dataset.step); });
    });

    if (window.SandboxScene) {
      window.SandboxScene.init($("scene"));
      window.SandboxScene.setTalkHandler(function (npc) {
        var line = npc.talk[Math.floor(Math.random() * npc.talk.length)];
        $("sceneCaption").textContent = npc.name + ": " + line;
      });
      window.SandboxScene.generate(state);
    }

    refreshAll();
    goStep("data");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

  window.DataStatGame = { state: state, generateData: generateData, runAnalysis: runAnalysis };
})();

