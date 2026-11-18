/* DATASTAT PIXEL LAB — statistics engine (window.Stats) */
window.Stats = (function () {
  "use strict";

  function mean(a) {
    var s = 0; for (var i = 0; i < a.length; i++) s += a[i];
    return a.length ? s / a.length : 0;
  }
  function variance(a) {
    if (a.length < 2) return 0;
    var m = mean(a), s = 0;
    for (var i = 0; i < a.length; i++) s += (a[i] - m) * (a[i] - m);
    return s / (a.length - 1);
  }
  function sd(a) { return Math.sqrt(variance(a)); }
  function quantile(sorted, q) {
    if (!sorted.length) return 0;
    var pos = (sorted.length - 1) * q, base = Math.floor(pos), rest = pos - base;
    if (base + 1 < sorted.length) return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
    return sorted[base];
  }
  function boxStats(a) {
    var s = a.slice().sort(function (x, y) { return x - y; });
    return {
      min: s[0], q1: quantile(s, 0.25), median: quantile(s, 0.5),
      q3: quantile(s, 0.75), max: s[s.length - 1], mean: mean(a), sd: sd(a), n: a.length
    };
  }

  function lnGamma(x) {
    var cof = [76.18009172947146, -86.50532032941677, 24.01409824083091,
      -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    var xx = x, y = x, tmp = xx + 5.5;
    tmp -= (xx + 0.5) * Math.log(tmp);
    var ser = 1.000000000190015;
    for (var j = 0; j < 6; j++) { y += 1; ser += cof[j] / y; }
    return -tmp + Math.log(2.5066282746310005 * ser / xx);
  }
  function betacf(a, b, x) {
    var MAXIT = 200, EPS = 3e-12, FPMIN = 1e-300;
    var qab = a + b, qap = a + 1, qam = a - 1;
    var c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    d = 1 / d;
    var h = d;
    for (var m = 1; m <= MAXIT; m++) {
      var m2 = 2 * m;
      var aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d;
      var del = d * c; h *= del;
      if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  }
  function betai(a, b, x) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    var bt = Math.exp(lnGamma(a + b) - lnGamma(a) - lnGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(a, b, x) / a;
    return 1 - bt * betacf(b, a, 1 - x) / b;
  }
  function tTwoTailP(t, df) { return betai(df / 2, 0.5, df / (df + t * t)); }
  function fUpperP(F, df1, df2) { return betai(df2 / 2, df1 / 2, df2 / (df2 + df1 * F)); }

  function pForAlt(t, p2, alt) {
    if (alt === "greater") return t > 0 ? p2 / 2 : 1 - p2 / 2;
    if (alt === "less") return t < 0 ? p2 / 2 : 1 - p2 / 2;
    return p2;
  }

  function tTest(a, b, alt) {
    var n1 = a.length, n2 = b.length;
    var m1 = mean(a), m2 = mean(b), v1 = variance(a), v2 = variance(b);
    var se = Math.sqrt(v1 / n1 + v2 / n2);
    var t = se === 0 ? 0 : (m1 - m2) / se;
    var df = Math.pow(v1 / n1 + v2 / n2, 2) /
      (Math.pow(v1 / n1, 2) / (n1 - 1) + Math.pow(v2 / n2, 2) / (n2 - 1));
    var p2 = tTwoTailP(t, df);
    var sp = Math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2));
    var d = sp === 0 ? 0 : (m1 - m2) / sp;
    return {
      test: "Welch two-sample t-test", t: t, df: df, p2: p2, p: pForAlt(t, p2, alt || "two"),
      mean1: m1, mean2: m2, sd1: Math.sqrt(v1), sd2: Math.sqrt(v2), n1: n1, n2: n2, d: d
    };
  }

  function anova(groups, alt) {
    var k = groups.length, N = 0, grandSum = 0;
    groups.forEach(function (g) { N += g.length; g.forEach(function (v) { grandSum += v; }); });
    var grand = grandSum / N;
    var ssB = 0, ssW = 0, means = [], sds = [];
    groups.forEach(function (g) {
      var m = mean(g), v = variance(g);
      means.push(m); sds.push(Math.sqrt(v));
      ssB += g.length * (m - grand) * (m - grand);
      ssW += (g.length - 1) * v;
    });
    var df1 = k - 1, df2 = N - k;
    var msB = ssB / df1, msW = ssW / df2;
    var F = msW === 0 ? 0 : msB / msW;
    var p = fUpperP(F, df1, df2);
    return {
      test: "One-way ANOVA", F: F, df1: df1, df2: df2, p: p, p2: p,
      eta2: (ssB + ssW) === 0 ? 0 : ssB / (ssB + ssW), means: means, sds: sds, grand: grand, N: N, k: k
    };
  }

  function pearson(x, y, alt) {
    var n = x.length, mx = mean(x), my = mean(y);
    var sxy = 0, sxx = 0, syy = 0;
    for (var i = 0; i < n; i++) {
      var dx = x[i] - mx, dy = y[i] - my;
      sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
    }
    var r = sxx && syy ? sxy / Math.sqrt(sxx * syy) : 0;
    if (r > 1) r = 1; if (r < -1) r = -1;
    var df = n - 2;
    var t = r * Math.sqrt(df / (1 - r * r));
    var p2 = tTwoTailP(t, df);
    return { test: "Pearson correlation", r: r, t: t, df: df, p2: p2, p: pForAlt(t, p2, alt || "two"), n: n };
  }

  function linreg(x, y, alt) {
    var n = x.length, mx = mean(x), my = mean(y);
    var sxy = 0, sxx = 0, syy = 0;
    for (var i = 0; i < n; i++) {
      var dx = x[i] - mx, dy = y[i] - my;
      sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
    }
    var slope = sxx ? sxy / sxx : 0;
    var intercept = my - slope * mx;
    var r2 = (sxx && syy) ? (sxy * sxy) / (sxx * syy) : 0;
    var df1 = 1, df2 = n - 2;
    var F = (r2 >= 1) ? Infinity : (r2 / df1) / ((1 - r2) / df2);
    var p = fUpperP(F, df1, df2);
    return {
      test: "Simple linear regression", slope: slope, intercept: intercept, r2: r2,
      F: F, df1: df1, df2: df2, p: p, n: n
    };
  }

  // RNG + samplers
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function makeSampler(seed) {
    var r = mulberry32(seed >>> 0);
    return {
      next: r,
      normal: function (m, s) {
        var u = 1 - r(), v = r();
        return m + s * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
      },
      uniform: function (m, s) { return m + (r() * 2 - 1) * s * 1.732; },
      exponential: function (m, s) { return m + (-Math.log(1 - r())) * s; },
      bimodal: function (m, s) { return r() < 0.5 ? m - 1.1 * s + 0.4 * s * (r() - 0.5) : m + 1.1 * s + 0.4 * s * (r() - 0.5); }
    };
  }

  return {
    mean: mean, variance: variance, sd: sd, quantile: quantile, boxStats: boxStats,
    betai: betai, tTwoTailP: tTwoTailP, fUpperP: fUpperP,
    tTest: tTest, anova: anova, pearson: pearson, linreg: linreg,
    mulberry32: mulberry32, makeSampler: makeSampler
  };
})();
