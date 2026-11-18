/* Pixel Isle shared engine. Exposes window.PI */
window.PI = (function () {
  "use strict";

  var VIEW_W = 320;
  var VIEW_H = 180;
  var TILE = 16;
  var INTERNAL_W = 38;
  var INTERNAL_H = 21;

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  var rnd = mulberry32(20261029);

  function grid(w, h, c) {
    var m = [];
    for (var y = 0; y < h; y++) m.push(new Array(w).fill(c));
    return m;
  }
  function rect(m, x0, y0, w, h, c) {
    for (var y = y0; y < y0 + h; y++)
      for (var x = x0; x < x0 + w; x++)
        if (y >= 0 && y < m.length && x >= 0 && x < m[0].length) m[y][x] = c;
  }
  function ellipse(m, cx, cy, rx, ry, c) {
    for (var dy = -ry; dy <= ry; dy++)
      for (var dx = -rx; dx <= rx; dx++)
        if ((dx * dx) / (rx * rx || 1) + (dy * dy) / (ry * ry || 1) <= 1) {
          var x = cx + dx, y = cy + dy;
          if (y >= 0 && y < m.length && x >= 0 && x < m[0].length) m[y][x] = c;
        }
  }

  function sprite(rows, colors) {
    var h = rows.length, w = rows[0].length;
    var c = document.createElement("canvas");
    c.width = w; c.height = h;
    var g = c.getContext("2d");
    for (var y = 0; y < h; y++) {
      var row = rows[y];
      for (var x = 0; x < row.length; x++) {
        var col = colors[row[x]];
        if (!col) continue;
        g.fillStyle = col;
        g.fillRect(x, y, 1, 1);
      }
    }
    return c;
  }

  /* ---------- outdoor ground tiles ---------- */
  var GRASS_COLORS = { G: "#6fbf58", g: "#86d06d", d: "#5c9f46" };
  var PATH_COLORS = { P: "#d9b26a", p: "#e0bd79", q: "#c9a25c" };
  var WATER_COLORS = { W: "#3f8fcf", w: "#59a7dd", b: "#2f74b0" };

  function makeGrass() {
    var rows = [];
    for (var y = 0; y < 16; y++) rows.push(new Array(16).fill("G"));
    for (var i = 0; i < 14; i++) {
      var x = Math.floor(rnd() * 16), yy = Math.floor(rnd() * 16);
      rows[yy][x] = rnd() < 0.5 ? "g" : "d";
    }
    return sprite(rows, GRASS_COLORS);
  }
  function makePath() {
    var rows = [];
    for (var y = 0; y < 16; y++) rows.push(new Array(16).fill("P"));
    for (var i = 0; i < 12; i++) {
      var x = Math.floor(rnd() * 16), yy = Math.floor(rnd() * 16);
      rows[yy][x] = rnd() < 0.5 ? "p" : "q";
    }
    return sprite(rows, PATH_COLORS);
  }
  function makeWater(frame) {
    var rows = [];
    for (var y = 0; y < 16; y++) rows.push(new Array(16).fill("W"));
    for (var x = 0; x < 16; x++)
      for (var y = 0; y < 16; y++)
        if ((x + y + frame) % 6 === 0) rows[y][x] = "w";
        else if ((x + y + frame) % 11 === 0) rows[y][x] = "b";
    return sprite(rows, WATER_COLORS);
  }
  function makeBrick() {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) {
        var c = "B";
        if (y % 4 === 0) c = "M";
        else {
          var off = Math.floor(y / 4) % 2 === 0 ? 0 : 4;
          if ((x - off) % 8 === 0) c = "M";
        }
        r.push(c);
      }
      rows.push(r);
    }
    return sprite(rows, { B: "#a34a3a", M: "#6b3127" });
  }
  function makeRoof() {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) {
        var c = "R";
        if (y % 3 === 0) c = "r";
        else if ((x + y) % 7 === 0) c = "D";
        r.push(c);
      }
      rows.push(r);
    }
    return sprite(rows, { R: "#c9503a", r: "#a83a2a", D: "#7c2a1e" });
  }

  /* ---------- outdoor objects ---------- */
  var TREE = sprite([
    "................", ".....KKKKK......", "....KGGGGGGK....", "...KGGgGGGGGK...",
    "...KGgGGGGGGK...", "..KGGGGGGGGGK...", "..KGGGGGGGGGGK..", "..KGGGGGGGdGGK..",
    "..KGGGGGGGddGK..", "..KGGGGGGGdddK..", "...KGGGGGGddGK..", "...KGGGGGGGGGK..",
    "....KGGGGGGGK...", ".....KGGGGGK....", "......KTTTK.....", ".......KKK......"
  ], { K: "#2c4a1f", G: "#4f9a3a", g: "#6cbf4f", d: "#3a7a2a", T: "#7a5230" });

  var ROCK = sprite([
    "................", "................", "................", ".......KKK......",
    "......KGGGK.....", ".....KGgGGK.....", "....KGGGGGK.....", "...KGGgGGGGK....",
    "...KGGGGGGdK....", "..KGGGGGGdK.....", "..KGGGGGGdK.....", "..KGGGGGGddK....",
    "..KKKKKKKKK.....", "................", "................", "................"
  ], { K: "#2a2a30", G: "#8a8a94", g: "#a5a5b0", d: "#6a6a74" });

  var FLOWER = sprite([
    "................", "................", "................", "................",
    "................", ".......R........", "......RYR.......", ".......R........",
    "................", "................", "................", "......GG........",
    "......GG........", "......GG........", "................", "................"
  ], { R: "#e05050", Y: "#ffd24a", G: "#4f9a3a" });

  var FENCE = sprite([
    "................", "................", "................", "................",
    "................", "....WWWWWWWW....", "....W..W..W.....", "................",
    "................", "................", "....WWWWWWWW....", "....W..W..W.....",
    "................", "................", "................", "................"
  ], { W: "#9a6a3a" });

  var SIGN = sprite([
    "................", "................", "....KKKKKKKK....", "...KWWWWWWWWK...",
    "...KWWWWWWWWK...", "...KWWWWWWWWK...", "...KKKKKKKKKK...", ".......TT.......",
    ".......TT.......", ".......TT.......", ".......TT.......", ".......TT.......",
    "................", "................", "................", "................"
  ], { K: "#2a2018", W: "#c9a25c", T: "#7a5230" });

  var COIN = sprite([
    "................", "................", "................", "......KKKK......",
    ".....KYYYYK.....", ".....KYwwYK.....", ".....KYwWYK.....", ".....KYWWYK.....",
    ".....KYWKYK.....", ".....KYKKYK.....", ".....KYYYYK.....", "......KKKK......",
    "................", "................", "................", "................"
  ], { K: "#8a5a1f", Y: "#ffd24a", w: "#f0a830", W: "#d98a1f" });

  var DOOR_CLOSED = sprite([
    "KKKKKKKKKKKKKKKK", "KDDDDDDDDDDDDDDK", "KDDDDDDDDDDDDDDK", "KDDKDDKDDKDDKDDK",
    "KDDKDDKDDKDDKDDK", "KDDKDDKDDKDDKDDK", "KDDKDDKDDKDDKDDK", "KDDKDDKDDKDDKDDK",
    "KDDKDDKDDKDDKDDK", "KDDKDDKDDKDDKDDK", "KDDKDDKDDKDDKDDK", "KDDKDDKDDKDDKDDK",
    "KDDKDDKDDKDDKDDK", "KDDDDDDDDDDDDDDK", "KDDDDDDDDDDKGGDK", "KKKKKKKKKKKKKKKK"
  ], { K: "#2a2018", D: "#9a6a3a", G: "#ffd24a" });

  var DOOR_OPEN = sprite([
    "KKKKKKKKKKKKKKKK", "KooooooooooooooK", "KooooooooooooooK", "KooooooooooooooK",
    "KooooooooooooooK", "KooooooooooooooK", "KooooooooooooooK", "KooooooooooooooK",
    "KooooooooooooooK", "KooooooooooooooK", "KooooooooooooooK", "KooooooooooooooK",
    "KooooooooooooooK", "KooooooooooooooK", "KooooooooooooooK", "KKKKKKKKKKKKKKKK"
  ], { K: "#2a2018", o: "#15120c" });

  var STRAWBERRY = sprite([
    "...0000.0.0.....", "..0433303030....", "..043333303000..", "...044433333330.",
    "..0500044330440.", ".0504333043400..", ".05044440434020.", "055500002044020.",
    "051155566500520.", "061155155552570.", "055555555621770.", ".0251555551270..",
    ".0255555166770..", ".015551667770...", "..0226677700....", "..02227700......"
  ], { "0": "#1c1c1c", "1": "#ffffff", "2": "#9f5656", "3": "#77e26f", "4": "#56ae5c", "5": "#e38282", "6": "#e36363", "7": "#833f3f" });

  

  /* ---------- interior tiles ---------- */
  var FLOOR = (function () {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) {
        var c = "b";
        if (y % 4 === 0) c = "d";
        else if (y % 4 === 1) c = "h";
        r.push(c);
      }
      rows.push(r);
    }
    for (var gy = 0; gy < 16; gy += 4) {
      var off = (Math.floor(gy / 4) % 2 === 0) ? 4 : 12;
      for (var y2 = gy; y2 < Math.min(gy + 4, 16); y2++) rows[y2][off] = "d";
    }
    for (var i = 0; i < 6; i++) rows[Math.floor(rnd() * 16)][Math.floor(rnd() * 16)] = "h";
    return sprite(rows, { b: "#b07a45", d: "#8a5a30", h: "#c08a52" });
  })();

  var WALL = (function () {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) {
        var c = "w";
        if (x % 4 === 0) c = "d";
        else if (x % 4 === 1) c = "l";
        if (y === 0 || y === 15) c = "d";
        r.push(c);
      }
      rows.push(r);
    }
    return sprite(rows, { w: "#8a6a48", d: "#6f5236", l: "#9c7a56" });
  })();

  var RUG = (function () {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) {
        var c = "r";
        var dx = x % 8, dy = y % 8;
        var d = Math.abs(dx - 4) + Math.abs(dy - 4);
        if (d === 0 || d === 3) c = "y";
        else if (d === 1) c = "o";
        else if (d === 2) c = "b";
        r.push(c);
      }
      rows.push(r);
    }
    return sprite(rows, { r: "#7f2b2b", y: "#d8c090", o: "#b06a3a", b: "#2f3f5a" });
  })();

  var WINDOW = sprite([
    "ffffffffffffffff", "fnnnnnnnnnnnnnnf", "fnnnnsnnnnnnsnnf", "fnnnnnnnnnnnnnnf",
    "fnnnnnnnnnnnnnnf", "fnnnnnnnnnnnnnnf", "fnnnnnnnnnnnnnnf", "fnbbnnnnnnnnbbnf",
    "fnbbnnnnnnnnbbnf", "fnbybnnnnnnbybnf", "fnbybnnnnnnbybnf", "fbbbbbnnbbbbbbnf",
    "fbybbbnbybbbbbnf", "fbybbbnbybbbbbnf", "fbbbbbbbbbbbbbbf", "ffffffffffffffff"
  ], { f: "#3a1f14", n: "#1b2340", s: "#c8d0e0", b: "#10162a", y: "#ffd24a" });

  var CURTAIN = (function () {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) r.push(y === 0 ? "r" : (x % 2 === 0 ? "c" : "C"));
      rows.push(r);
    }
    return sprite(rows, { r: "#3a3226", c: "#6a7a68", C: "#879584" });
  })();

  var BOOKSHELF = sprite([
    "ffffffffffffffff", "fkkkkkkkkkkkkkkf", "fk1122334455kkkf", "fk1122334455kkkf",
    "fk1122334455kkkf", "fkkkkkkkkkkkkkkf", "fk5544332211kkkf", "fk5544332211kkkf",
    "fk5544332211kkkf", "fkkkkkkkkkkkkkkf", "fk1234512345kkkf", "fk1234512345kkkf",
    "fk1234512345kkkf", "fkkkkkkkkkkkkkkf", "ffffffffffffffff", "ffffffffffffffff"
  ], { f: "#5a3a1e", k: "#2a1c10", 1: "#c04a4a", 2: "#4a7ac0", 3: "#4aa05a", 4: "#c9a24a", 5: "#8a5ac0" });

  var FIREPLACE = sprite([
    "kkkkkkkkkkkkkkkk", "kmmmmmmmmmmmmmmk", "kmbbbbbbbbbbbbmk", "kmbkkkkkkkkkkbmk",
    "kmbkddddddddkbmk", "kmbkddddddddkbmk", "kmbkddddddddkbmk", "kmbkddddddddkbmk",
    "kmbkddddddddkbmk", "kmbkkkkkkkkkkbmk", "kmbbbbbbbbbbbbmk", "kmmmmmmmmmmmmmmk",
    "kkkkkkkkkkkkkkkk", "kkkkkkkkkkkkkkkk", "kkkkkkkkkkkkkkkk", "kkkkkkkkkkkkkkkk"
  ], { k: "#3a2a20", m: "#8a6a4a", b: "#a8a09a", d: "#1a1410" });

  var CHAIR = [
    "....................", "..........333333....", ".........313111133..", "........31231111313.",
    ".......3123111113123", ".......3123111113123", ".......3123211131223", ".......3123211131223",
    ".......3123211131223", "..33333331322131123.", ".331112223222221223.", ".31122333112333333..",
    ".33223111113111123..", "..331111113122333...", "..323331113233223...", "..322223333222223...",
    "..3432222222223343..", "..343332222233.343..", "...3...33343....3...", ".........343........"
  ];
  var CHAIR_RED = sprite(CHAIR, { "0": "#3a1c1c", "1": "#a83a3a", "2": "#602929", "3": "#2c0202", "4": "#4f4f4f" });
  var CHAIR_OLIVE = sprite(mirror(CHAIR), { "0": "#2f3a1c", "1": "#7aa64a", "2": "#4a6a2a", "3": "#223312", "4": "#4f4f4f" });

  var TABLE = sprite([
    "................", "................", "....kkkkkkkk....", "..kkQQQQQQQQkk..",
    ".kQQQWWQQWWQQQk.", ".kQQQWWQQWWQQQk.", ".kQQQQQQQQQQQQk.", "..kkQQQQQQQQkk..",
    "....kkkkkkkk....", "......kQQk......", "......kQQk......", "......kQQk......",
    "......kkkk......", "................", "................", "................"
  ], { k: "#4a3418", Q: "#a9743e", W: "#f2efe0" });

  var LAB_FLOOR = sprite([
    "0000000000000000", "0111111111111112", "0111111111111112", "0111111111111112",
    "0111111111111112", "0111111111111112", "0111111111111112", "0111111111111112",
    "0111111111111112", "0111111111111112", "0111111111111112", "0111111111111112",
    "0111111111111112", "0111111111111112", "0111111111111112", "2222222222222222"
  ], {"0":"#c7c7c7","1":"#737373","2":"#3b3b3b"});

  var LAB_WALLS = sprite([
    "1100000000000011", "1000000000000001", "0000000000000000", "0000000000000000",
    "0000000000000000", "0000000000000000", "0000000000000000", "0000000000000000",
    "0000000000000000", "0000000000000000", "0000000000000000", "0000000000000000",
    "0000000000000000", "0000000000000000", "1000000000000001", "1100000000000011"
  ], {"0":"#f2f2f2","1":"#4f4f4f","2":"#b07a45"});

  var WORKBENCH = sprite([
    ".DDDDDDDDDDDDDD.", "DLLLLLLLLLLLLLLD", "DLWMMWMMWMMWGGLD", "DLW11W22W33WGGLD",
    "DLWMMWMMWMMWGGLD", "DLWWWWWWWWWWWWLD", "DLWWWWGGGGWWWWLD", "DLLLLLLLLLLLLLLD",
    "DDDDDDDDDDDDDDDD", "DWWDWWWWWWWWDWWD", "DWWDWLLLLLLWDWWD", "DWWDWLGGGGLWDWWD",
    "DWWDWWWWWWWWDWWD", "DWWDDDDDDDDDDWWD", "DDDKKKKKKKKKDDDD", ".DDDDDDDDDDDDDD."
  ], {"1":"#00E5FF","2":"#FFEA00","3":"#D500F9","D":"#3B2219","W":"#795548","L":"#A1887F","M":"#546E7A","G":"#FFD700","K":"#1A0C06"});
  
  var CABINET = sprite([
    "kkkkkkkkkkkkkkkk", "kBBBBBBBBBBBBBBk", "kBbbbbbbbbbbbbBk", "kBbwwwwwwwwwwbBk",
    "kBbwwwwwwwwwwbBk", "kBbbbbbbbbbbbbBk", "kBbbbbhhbbbbbbBk", "kBbbbbbbbbbbbbBk",
    "kBbbbbbbbbbbbbBk", "kBBBBBBBBBBBBBBk", "kBbbbbbbbbbbbbBk", "kBbbbbbbbbbbbbBk",
    "kBbbbbbbbbbbbbBk", "kBbbbbbbbbbbbbBk", "kBBBBBBBBBBBBBBk", "kkkkkkkkkkkkkkkk"
  ], { k: "#2a1c10", B: "#6b4a2a", b: "#8a6338", w: "#e8dcc0", h: "#c9a24a" });

  var STAIRS = (function () {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) {
        var c;
        if (y % 4 === 0 || y % 4 === 1) c = "l";
        else if (y % 4 === 2) c = "m";
        else c = "d";
        r.push(c);
      }
      rows.push(r);
    }
    return sprite(rows, { l: "#b08a5a", m: "#9a7448", d: "#5a3f22" });
  })();

  var PICTURE = sprite([
    "aaaaaaaaaaaaaaaa", "aaaaaaaaaaaaaaaa", "aakkkkkkkkkkkkaa", "aakffffffffffkaa",
    "aakfppppppppfkaa", "aakfppppppppfkaa", "aakfppppppppfkaa", "aakfppppppppfkaa",
    "aakfppppppppfkaa", "aakfppppppppfkaa", "aakffffffffffkaa", "aakkkkkkkkkkkkaa",
    "aaaaaaaaaaaaaaaa", "aaaaaaaaaaaaaaaa", "aaaaaaaaaaaaaaaa", "aaaaaaaaaaaaaaaa"
  ], { a: "#7c3a2e", k: "#3a2a18", f: "#c9a24a", p: "#8a9aa0" });

  function combine(a, b) {
    var c = document.createElement("canvas");
    c.width = 16; c.height = 16;
    var g = c.getContext("2d");
    g.drawImage(a, 0, 0);
    g.drawImage(b, 0, 0);
    return c;
  }

  var DESK_BASE = (function () {
    var rows = [];
    for (var y = 0; y < 16; y++) {
      var r = [];
      for (var x = 0; x < 16; x++) {
        var c = "b";
        if (y % 5 === 0) c = "d";
        else if ((x * 7 + y * 3) % 13 === 0) c = "h";
        r.push(c);
      }
      rows.push(r);
    }
    return sprite(rows, { b: "#8a5a34", d: "#6b3f22", h: "#a56b3e" });
  })();

  var DESK_PHONE = combine(DESK_BASE, sprite([
    "................", "................", "................", "................",
    ".....kkkkkk.....", "....kKKKKKKk....", "...kKddddddKk...", "...kKdKKKKdKk...",
    "...kKddddddKk...", "....kKKKKKKk....", ".....kkkkkk.....", "................",
    "................", "................", "................", "................"
  ], { k: "#0c0c0c", K: "#1c1c1c", d: "#3a3a3a" }));

  var DESK_LAMP = combine(DESK_BASE, sprite([
    "....000.........",    "...04450........",    "..04445500......",    ".04444455500....",
    ".044444455550...",    "..049444555550..",    "...009944444550.",    ".....0094445550.",
    ".......0045550..",    ".......070000...",    ".......070......",    ".......070......",
    "......03780.....",    ".....0337880....",    "......07880.....",    ".......000......"
  ], {"0":"#000000","1":"#8a5a34","2":"#a56b3e","3":"#ffd24a","4":"#5fbf6f","5":"#3f9b4f","6":"#82734f","7":"#f7cb64","8":"#937d48","9":"#ceea99"}));

  var DESK_PAPERS = combine(DESK_BASE, sprite([
    "................", "................", "................", "....wwwwww......",
    "....wWWWWw......", "....wwwwww......", "....wWWWWw......", "....wwwwww......",
    "....wWWWWw......", "....wwwwww......", "................", "................",
    "................", "................", "................", "................"
  ], { w: "#e8dcc0", W: "#c9b98a" }));

  var DESK_MUG = combine(DESK_BASE, sprite([
    "................", "................", "......333.......", "....3311133.....",
    "...311110003....", "...33300033333..", "...333333332..3.", "...333333332..3.",
    "...333333322.3..", "...2333332223...", "...223322222....", "...222222222....",
    "....2222222.....", "......222.......", "................", "................"
  ], { "0": "#6b3f22", "1": "#8a5a34", "2": "#a1a1a1", "3": "#f0ece0" }));

  var CORK = sprite([
    "cccccccccccccccc", "cdcccccccdcccccc", "ccwwwcccwwwccccc", "ccwwwcccwwwccccc",
    "ccwrwcccwbwccccc", "cccccccccccccccc", "cccwwwccccwwcccc", "cccwwwccccwwcccc",
    "cccwbwccccwrcccc", "cccccccccccccccc", "cdcccccccdcccccc", "cccccccccccccccc",
    "ccwwwcccwwwccccc", "ccwwwcccwwwccccc", "ccwrwcccwbwccccc", "cccccccccccccccc"
  ], { c: "#b98a52", d: "#a47844", w: "#f0ece0", r: "#c04a4a", b: "#4a7ac0" });

  var MAP = sprite([
    "ffffffffffffffff", "fnnnnnnnnnnnnnnf", "fnnlllnnnnnnnnnf", "fnllllnnnnnllnnf",
    "fnlllnnnnnllllnf", "fnnnnnnnnnlllnnf", "fnnnnnllnnnnnnnf", "fnnnnllllnnnnnnf",
    "fnnnnnllnnnnllnf", "fnnnnnnnnnnllllf", "fnnnnnnnnnnllnnf", "fnllnnnnnnnnnnnf",
    "fllllnnnnnnnnnnf", "fnnnnnnnnnnnnnnf", "fnnnnnnnnnnnnnnf", "ffffffffffffffff"
  ], { f: "#3a2a1a", n: "#2f5a7a", l: "#7a9a5a" });

  var CLOCK_TOP = sprite([
    "................", "....kkkkkkkk....", "...kbbbbbbbbk...", "...kbwwwwwwbk...",
    "...kbwkkkkwbk...", "...kbwkwwkwbk...", "...kbwkkkkwbk...", "...kbwwwwwwbk...",
    "...kbbbbbbbbk...", "...kbbbbbbbbk...", "....kkkkkkkk....", "................",
    "................", "................", "................", "................"
  ], { k: "#2a1a0e", b: "#6b4a2a", w: "#d8c090" });

  var CLOCK_MID = sprite([
    "....kkkkkkkk....", "...kbbbbbbbbk...", "...kbddddddbk...", "...kbdggggdbk...",
    "...kbdggggdbk...", "...kbddddddbk...", "...kbddddddbk...", "...kbdggggdbk...",
    "...kbdggggdbk...", "...kbddddddbk...", "...kbbbbbbbbk...", "....kkkkkkkk....",
    "................", "................", "................", "................"
  ], { k: "#2a1a0e", b: "#6b4a2a", d: "#1a120a", g: "#c9a24a" });

  var CLOCK_BASE = sprite([
    "....kkkkkkkk....", "...kbbbbbbbbk...", "...kbbbbbbbbk...", "...kbbbbbbbbk...",
    "...kbbbbbbbbk...", "...kbbbbbbbbk...", "..kkbbbbbbbbkk..", "..kbbbbbbbbbbk..",
    "..kbbbbbbbbbbk..", "..kkkkkkkkkkkk..", "................", "................",
    "................", "................", "................", "................"
  ], { k: "#2a1a0e", b: "#6b4a2a" });

  var BOX = sprite([
    "kkkkkkkkkkkkkkkk", "kbbbbbbbbbbbbbbk", "kbBbbbbbbbbbbBbk", "kbBbbbbbbbbbbBbk",
    "kbBbbbbbbbbbbBbk", "kbBbbbbbbbbbbBbk", "kbBbbbbbbbbbbBbk", "kbBbbbbbbbbbbBbk",
    "kbBbbbbbbbbbbBbk", "kbBbbbbbbbbbbBbk", "kbBbbbbbbbbbbBbk", "kbBbbbbbbbbbbBbk",
    "kbBBBBBBBBBBBBbk", "kbbbbbbbbbbbbbbk", "kkkkkkkkkkkkkkkk", "................"
  ], { k: "#4a3a24", b: "#c8a06a", B: "#a87f4a" });

  var TRASH = combine(FLOOR, sprite([
    "....22..........",    "..2200333.......",    ".2000000333.....",    "20005400003331..",
    ".3355540000021..",    ".2333554450221..",".2333335522221..",    ".2333333222221..",
    "..233333222221..",    "..233333222211..",    "..23333322221...",    "...2233322221...",
    "...1122322221...",    ".....11222211...",    ".......11111....",    "................"
  ], {"0":"#000000","1":"#1d1d20","2":"#4f4040","3":"#7a6666","4":"#9e9e9e","5":"#636363"}));

  var KETTLE = sprite([
    "................", "................", "................", "......gg........",
    ".....gGGg.......", "....gGGGGg......", "....gGGGGg......", ".....gGGg.......",
    "....kkkkkk......", "....kbbbbk......", "....kbbbbk......", "....kbbbbk......",
    "....kkkkkk......", "................", "................", "................"
  ], { g: "#8a9aa4", G: "#c8d0d8", k: "#4a3418", b: "#a9743e" });

  var COAT = sprite([
    "................", ".......kk.......", ".......kk.......", "......kkkk......",
    ".....kGGGGk.....", "....kGGGGGGk....", "....kGGGGGGk....", "....kGGGGGGk....",
    "....kGGGGGGk....", "....kGGGGGGk....", ".....kGGGGk.....", "......kkkk......",
    "................", "................", "................", "................"
  ], { k: "#2a1a0e", G: "#6a6a5a" });

  var CAT = sprite([
    "rrrrrrrrrrrrrrrr", "rrrrrrrrrrrrrrrr", "rrrrrrrrrrrrrrrr", "rrrrrrrrrrrrrrrr",
    "rrrrrrrrrrrrrrrr", "rrrrrrrrrrrrrrrr", "rrrrrrrrrkkkrrrr", "rrrrrrrrkccckrrr",
    "rrrrrrrkccccckrr", "rrrrrrkccccccckr", "rrrrrrkccccccckr", "rrrrrrkccccccckr",
    "rrrrrrrkccccckrr", "rrrrrrrrkkkkkrrr", "rrrrrrrrrrrrrrrr", "rrrrrrrrrrrrrrrr"
  ], { r: "#7f2b2b", k: "#3a2a1e", c: "#b08a5a" });

  var PAPERS = combine(RUG, sprite([
    "................", "................", "...22.....22555.", "...202222200005.",
    "...200111041405.", "...203133411005.", "..2001111111305.", "..2044111333005.",
    "..2011331110005.", "..201111110405..", ".2041141334005..", ".2114311110005..",
    ".201110000005...", ".200000255005...", ".222222...555...", "................"
  ], { "0": "#d0c19f", "1": "#e8dcc0", "2": "#a4a289", "3": "#494337", "4": "#645e4f", "5": "#898270" }));

  var VOID = sprite([
    "0000000000000000", "0000000000000000", "0000000000000000", "0000000000000000",
    "0000000000000000", "0000000000000000", "0000000000000000", "0000000000000000",
    "0000000000000000", "0000000000000000", "0000000000000000", "0000000000000000",
    "0000000000000000", "0000000000000000", "0000000000000000", "0000000000000000"
  ], { "0": "#000000" });

  var DEAD_BODY = sprite([
    "................................", "................................",
    "....bbb..bbbb...................", "..bb000bbtttTb..................",
    ".b0000000bbttTbbb........bbbbb..", "b0222000000bttTTTbbbbb.bbHHHHHbb",
    "b0000222220bbtTTTTTTTbbHHHHEEEH0", "b62700000020ttTTTTTTTTHHEEEEbE00",
    "b66677702266TTTTTTTTTtHHbbbbbbbb", "b67666670666TTTTTTTtttHHHHHHb...",
    "b66766666666bTTtttttbbEEEEHHEb..", ".b667777666bbtTbbbb3333bbEEEEEb.",
    "..bb6666bbb3bttTTTTTTSb3bbbbEE0b", "....bbbb...33bbtttttSSb3....b00b",
    "............333bbbbbbb3......bb.", "............3333333333.........."
  ], { "0": "#2e2e2e", "1": "#c2c2c2", "2": "#595959", "3": "#a80b0b", "4": "#ddb788", "5": "#c8a06f", "6": "#242424", "7": "#4f4f4f", "K": "#b8b8b8", "H": "#6b4a2a", "h": "#7c552d", "S": "#f2c48d", "E": "#412c1f", "T": "#3f6fb0", "t": "#254574", "P": "#501902", "p": "#734a12", "B": "#694730", "b": "#000000" });

  /* ---------- characters (16x32, Stardew-style) ---------- */
  var CH_DOWN = [
    "................", "................", "................", "................",
    "................", "................", "....KKKKKKKK....", "...KhhhhhHHbK...",
    "...KhhHHHbbbK...", "...KHHHHHbbbK...", ".KKKKKKKKKKKKKK.", "KhhhhhhhHhHHbbbK",
    ".KKKKKKKKKKKKKK.", "...KS0TSST0SK...", "...KS0tSSt0SK...", "....KSSSSSSK....",
    ".....KSSSSK.....", "....KHKKKKBK....", "...KBB001EHBK...", "...KpBp1EBbHK...",
    "...KhKh1BBKEK...", "...KpKp1EBKBK...", "...KpKhBEHKEK...", "...KSSKEbKSSK...",
    "...KSSKEbKSSK...", "....KHbEbbEK....", "....KpHEBbEK....", "...KHpbEEBbEK...",
    "..KhpbEKEEEEK...", "..KhEE2K2PEKK...", "..KKK202K2K.....", "....KKKKKKK....."
  ];
  var CH_UP = [
    "................", "................", "................", "................",
    "................", "................", "....KKKKKKKK....", "...KhhhhhHHbK...",
    "...KhhHHHbbbK...", "...KHHHHHbbbK...", ".KKKKKKKKKKKKKK.", "KhhhhhhhHhHHbbbK",
    ".KKKKKKKKKKKKKK.", "...KHBbbEEEEK...", "...KSHHbbbESK...", "....KSBBBbSK....",
    ".....KSSSSK.....", "....KHKKKKBK....", "...KBBhhhhHBK...", "...KpBhhhhbHK...",
    "...KhKhhhBKEK...", "...KpKphhBKBK...", "...KpKhhhHKEK...", "...KSSKhhhKSK...",
    "...KSSKhbhKSK...", "....KHhhbhEK....", "....KphbbbEK....", "...KHpbbEBbEK...",
    "..KhpbbbbbbEEK..", "..KhbbbbbbbEEK..", "..KKKKKKKKKKK...", "....K222K22K...."
  ];
  var CH_LEFT = [
    "................", "................", "................", "................",
    "................", "................", "....KKKKKKKK....", "...KhhhhhHHbK...",
    "...KhhHHHbbbK...", "...KHHHHHbbbK...", ".KKKKKKKKKKKKKK.", "KhhhhhhhHhHHbbbK",
    ".KKKKKKKKKKKKKK.", "...KST0SbbbbK...", "...KSt0SSSbbK...", "..KSSSSSSSbK....",
    "...KSSSSSKK.....", "..KhKKKKKHBK....", "..KH001hpHHBK...", "..Khp0pphKbHK...",
    "..Khh1hpHKBEK...", "..KKp1phBKHEK...", ".KSKphhBKSEEK...", ".KSKBphBKSSSK...",
    ".KSKEEppKSSSK...", "..KKPPEpBBKK....", "...K3KPEpBK.....", "...K3K3bpBBK....",
    "...KPKPPbbEK....", "...K2K2PPPK.....", "..K0K022PPK.....", "..KKKKKKKKK....."
  ];

  function mirror(rows) { return rows.map(function (r) { return r.split("").reverse().join(""); }); }

  var PLAYER_COLORS = { K: "#201813", H: "#6b4a2a", h: "#7c552d", S: "#f2c48d", E: "#412c1f", T: "#3f6fb0", t: "#2f5590", P: "#501902", p: "#734a12", B: "#694730", b: "#50301b", "0": "#e8e8e8", "1": "#c2c2c2", "2": "#322f2f", "3": "#712504", "4": "#ddb788", "5": "#c8a06f" };
  var VILLAGER1_COLORS = { K: "#241a14", H: "#3a2a1e", h: "#54402c", S: "#f2c48d", E: "#241a14", T: "#4a8a4a", t: "#356a35", P: "#4a3b2a", p: "#33281c", B: "#5a3a1e", b: "#3a2410" };
  var VILLAGER2_COLORS = { K: "#241a14", H: "#c9a24a", h: "#e0c06a", S: "#f2c48d", E: "#241a14", T: "#b0503a", t: "#8a3a2a", P: "#3a4a6a", p: "#2a3650", B: "#5a3a1e", b: "#3a2410" };
  var HOLMES_COLORS = { K: "#1a1a1a", H: "#2a2a2a", h: "#3a3a3a", S: "#e6be93", E: "#1a1a1a", T: "#6b5a3a", t: "#4f4228", P: "#3a3a3a", p: "#2a2a2a", B: "#1a1a1a", b: "#0d0d0d" };

  function strideDown(rows) {
    return rows.slice(0, 26).concat([
      "...KPPKKKKPPK...",
      "..KPPK....KPPK..",
      "..KPPK....KPPK..",
      "..KPPK....KPPK..",
      ".KBBBK....KBBBK.",
      ".KbBBK....KbBBK."
    ]);
  }
  function strideSide(rows) {
    return rows.slice(0, 26).concat([
      "...KPPKKPPK.....",
      "..KPPK..KPPK....",
      "..KPPK..KPPK....",
      "..KPPK..KPPK....",
      ".KBBBK..KBBBK...",
      ".KbBBK..KbBBK..."
    ]);
  }

  function bob(rows, colors) {
    var base = sprite(rows, colors);
    var c = document.createElement("canvas");
    c.width = base.width; c.height = base.height;
    var g = c.getContext("2d");
    g.drawImage(base, 0, 1);
    return c;
  }

  var P_RIGHT = mirror(CH_LEFT);
  var playerFrames = {
    down: [sprite(CH_DOWN, PLAYER_COLORS), bob(CH_DOWN, PLAYER_COLORS)],
    up: [sprite(CH_UP, PLAYER_COLORS), bob(CH_UP, PLAYER_COLORS)],
    left: [sprite(CH_LEFT, PLAYER_COLORS), bob(CH_LEFT, PLAYER_COLORS)],
    right: [sprite(P_RIGHT, PLAYER_COLORS), bob(P_RIGHT, PLAYER_COLORS)]
  };
  var playerSpriteDown = sprite(CH_DOWN, PLAYER_COLORS);
  var npcSprites = [sprite(CH_DOWN, VILLAGER1_COLORS), sprite(CH_DOWN, VILLAGER2_COLORS)];
  var holmesNpc = sprite([
    "................", "................", "................", "................",
    "................", "................", "....00000000....", "...0111112230...",
    "...0112223330...", "...0222223330...", ".00000000000000.", "0111111121223330",
    ".00000000000000.", "...0475445740...", "...0476446740...", "....04444440....",
    ".....044440.....", "....02000000....", "...0008980200...", "...0202800320...",
    "...0101900000...", "...0202800000...", "...0201002000...", "...0440030440...",
    "...0440030440...", "....02303300....", "....02200300....", "...0223000300...",
    "..01230000000...", "..0100A0A1000...", "..000AAA0A0.....", "....0000000....."
  ], { "0": "#1a1a1a", "1": "#3a3a3a", "2": "#2a2a2a", "3": "#0d0d0d", "4": "#e6be93", "5": "#6b5a3a", "6": "#4f4228", "7": "#ffffff", "8": "#7d3636", "9": "#a44646", "A": "#483d3d" });

  var PSY_PLAYER_MALE = sprite([
    "..........0000000000............", ".........0EEEEEEEEEE0000........",
    ".......00EEEEEEEEEEEEEEE0.......", "......0EEEEEEEEE0EEEEEEEE0......",
    "......0EEEEEEE0040EEEEEEE0......", "......0EEEEEE004440EEEEEEE0.....",
    "......0EEEEEE044440EEE0EEEE0....", "......0EEEEE0044440EEE00EEE0....",
    ".....0EEEEEE04444440EE00EEE0....", ".....0EEEEEE04444440E040EE0.....",
    ".....0EEE0EE04444440E040EE0.....", ".....0EEE0EE04444440E04000......",
    ".....0EEE0EE00444440E04440......", "......0E0K0000KKKKK00KKKK0......",
    ".......04K41t34KKK4t314K40......", ".......04K41tt4K4K4tt14K40......",
    "........0K4444K444K4444K0.......", "........04KKKK44444KKKK40.......",
    ".........044444444444440........", "..........0044444444400.........",
    "............000000000...........", ".......000000TTppETT00000.......",
    "......0111110TppppET011110......", "......0111110TpppEET011110......",
    "......01111100TEEET0011110......", ".....0111111020TET020111110.....",
    ".....0111011022000220110110.....", ".....0111011022202220110110.....",
    ".....0111011022202220110110.....", "....011110110222202201101110....",
    "....01111011022K202201101110....", "....011101110222202201110110....",
    "....011101110222202201110110....", "....01110111022K202201110110....",
    "...01111011102222022011101110...", "...01111011102222022011101110...",
    "...011110111022K2022011101110...", "...01111011102222022011101110...",
    "...01111011102222022011101110...", "...01111011102220222011101110...",
    "...01111011102220222011101110...", "...01111011102220222011101110...",
    "..0111110111022202220111011110..", "..0111110111002060200111011110..",
    "..01111101110P0P6P0P0111011110..", "...0000001110PPP6PPP011100000...",
    "..04444401110PPP6PPP0111044440..", "..04444401110PPP6PPP0111044440..",
    "...0444401110PPP6PPP011104440...", "....000001110PPP6PPP01110000....",
    "........01110PPP6PPP01110.......", "........01110PPP6PPP01110.......",
    "........00000PPP6PPP00000.......", "..........0PPPPP6PPPPP0.........",
    "..........0PPPPP6PPPPP0.........", "..........0PPPPP6PPPPP0.........",
    "..........0PPPPP6PPPPP0.........", "..........0PPPPP6PPPPP0.........",
    "..........0PPPPP6PPPPP0.........", "..........0PPPPP6PPPPP0.........",
    "..........0000006000000.........", "..........0772220772220.........",
    "..........0222220222220.........", "..........0000000000000........."
  ], {"0":"#141414","1":"#ffffff","2":"#322f2f","3":"#196bd7","4":"#ddb788","5":"#c8a06f","6":"#2c1d11","7":"#949494","K":"#595454","H":"#242424","h":"#7c552d","S":"#f2c48d","E":"#332319","T":"#3f6fb0","t":"#2f5590","P":"#382414","p":"#4b3030","B":"#694730","b":"#50301b"});

  var PSY_PLAYER_FEMALE = sprite([
    "..........0000000000............", ".........0EEEEEEEEEE0000........",
    ".......00EEEEEEEEEEEEEEE0.......", "......0EEEEEEEEE0EEEEEEEE0......",
    "......0EEEEEEE0040EEEEEEE0......", "......0EEEEEE004440EEEEEEE0.....",
    "......0EEEEEE044440EEE0EEEE0....", "......0EEEEE0044440EEE00EEE0....",
    ".....0EEEEEE04444440EE00E0E0....", ".....0EEEEEE04444440E040E0E0....",
    ".....0EEE0EE04444440E040E0E0....", ".....0EEE0EE0K444440E0400EE0....",
    ".....0EEE0EE00K444K0E0K440E0....", ".....0EE0K00004KKK40044KK0E0....",
    ".....0E04K41t34K4K4t314K40E0....", ".....0E04K41tt4K4K4tt14K40E0....",
    ".....0EE04K444K444K444K40EE0....", ".....0EE044KKK44444KKK440EE0....",
    ".....0EEE044444444444440EEE0....", ".....0EEEE0044444444400EEEE0....",
    ".....0EEEEEE000000000EEEEEE0....", ".....0E000000TTppETT00000EE0....",
    ".....00111110TppppET011110E0....", "......0111110TpppEET011110E0....",
    "......01111100TEEET0011110E0....", ".....0111111020TET020111110.....",
    ".....0111011022000220110110.....", ".....0111011022202220110110.....",
    ".....0111011022202220110110.....", "....011110110222202201101110....",
    "....01111011022K202201101110....", "....011101110222202201110110....",
    "....011101110222202201110110....", "....01110111022K202201110110....",
    "...01111011102222022011101110...", "...01111011102222022011101110...",
    "...011110111022K2022011101110...", "...01111011102222022011101110...",
    "...01111011102222022011101110...", "...01111011102220222011101110...",
    "...01111011102220222011101110...", "...01111011102220222011101110...",
    "..0111110111022202220111011110..", "..0111110111002060200111011110..",
    "..01111101110P0P6P0P0111011110..", "...0000001110PPP6PPP011100000...",
    "..04444401110PPP6PPP0111044440..", "..04444401110PPP6PPP0111044440..",
    "...0444401110PPP6PPP011104440...", "....000001110PPP6PPP01110000....",
    "........01110PPP6PPP01110.......", "........01110PPP6PPP01110.......",
    "........00000PPP6PPP00000.......", "..........0PPPPP6PPPPP0.........",
    "..........0PPPPP6PPPPP0.........", "..........0PPPPP6PPPPP0.........",
    "..........0PPPPP6PPPPP0.........", "..........0PPPPP6PPPPP0.........",
    "..........0PPPPP6PPPPP0.........", "..........0PPPPP6PPPPP0.........",
    "..........0000006000000.........", "..........077HHH0772220.........",
    "..........0HHHHH0222220.........", "..........0000000000000........."
  ], {"0":"#141414","1":"#ffffff","2":"#322f2f","3":"#196bd7","4":"#ddb788","5":"#c8a06f","6":"#2c1d11","7":"#949494","K":"#595454","H":"#242424","h":"#7c552d","S":"#f2c48d","E":"#332319","T":"#3f6fb0","t":"#2f5590","P":"#382414","p":"#4b3030","B":"#694730","b":"#50301b"});

  var PLAYER_LOOKS = { "Percy": null, "Male": PSY_PLAYER_MALE, "Female": PSY_PLAYER_FEMALE };

  function drawPlayerLook(ctx, look, dir, frame, x, y) {
    if (look === "Male") { drawChar(ctx, PSY_PLAYER_MALE, x, y); return; }
    if (look === "Female") { drawChar(ctx, PSY_PLAYER_FEMALE, x, y); return; }
    drawChar(ctx, playerFrames[dir][frame], x, y);
  }

  var grassTiles = [makeGrass(), makeGrass(), makeGrass()];
  var pathTiles = [makePath(), makePath()];
  var waterTiles = [makeWater(0), makeWater(1)];
  var brickTile = makeBrick();
  var roofTile = makeRoof();

  /* ---------- scene builders ---------- */
  function buildIslandWorld() {
    var interior = grid(INTERNAL_W, INTERNAL_H, ".");
    for (var y = 0; y < INTERNAL_H; y++)
      for (var x = 0; x < INTERNAL_W; x++)
        if (rnd() < 0.045) interior[y][x] = "T";
        else if (rnd() < 0.02) interior[y][x] = "R";
        else if (rnd() < 0.035) interior[y][x] = "f";

    ellipse(interior, 9, 6, 4, 3, "~");
    ellipse(interior, 21, 3, 3, 2, "~");
    ellipse(interior, 8, 5, 2, 2, "~");

    rect(interior, 30, 13, 8, 2, "r");
    rect(interior, 30, 15, 8, 1, "W");
    rect(interior, 30, 16, 1, 3, "W");
    rect(interior, 37, 16, 1, 3, "W");
    rect(interior, 30, 19, 8, 1, "W");
    rect(interior, 31, 16, 6, 3, "P");
    interior[19][34] = "D";

    rect(interior, 2, 20, 33, 1, "P");

    rect(interior, 15, 13, 3, 1, "=");
    rect(interior, 15, 16, 3, 1, "=");
    interior[15][14] = "f"; interior[16][14] = "f"; interior[17][14] = "f"; interior[16][15] = "f";

    interior[4][19] = "S";

    [[10, 20], [15, 20], [22, 20], [28, 20], [6, 10], [14, 12], [24, 8], [18, 15],
     [26, 15], [12, 4], [30, 4], [32, 17], [5, 3], [3, 11]].forEach(function (c) {
      interior[c[1]][c[0]] = "C";
    });

    interior[15][8] = "N";
    interior[18][28] = "N";
    interior[17][3] = "X";

    var world = grid(INTERNAL_W + 4, INTERNAL_H + 4, "~");
    for (var yy = 0; yy < INTERNAL_H; yy++)
      for (var xx = 0; xx < INTERNAL_W; xx++)
        world[yy + 2][xx + 2] = interior[yy][xx];
    return world;
  }

  function buildHolmesWorld() {
    var W = INTERNAL_W + 4, H = INTERNAL_H + 4;
    var w = grid(W, H, "#");
    rect(w, 3, 3, 36, 19, "F");

    w[2][4] = "G"; w[3][4] = "H"; w[4][4] = "J";
    for (var cy = 2; cy <= 4; cy++) { w[cy][6] = "K"; w[cy][7] = "K"; w[cy][8] = "K"; }
    for (var cx = 14; cx <= 20; cx++) w[2][cx] = "c";
    for (var wx = 25; wx <= 27; wx++) w[2][wx] = "O";
    w[2][32] = "M";
    w[2][36] = "I";

    for (var yl = 8; yl <= 12; yl++) w[yl][3] = "L";
    w[6][3] = "V"; w[7][3] = "V";
    w[15][3] = "y";
    w[19][4] = "t";

    for (var yr = 7; yr <= 13; yr++) w[yr][38] = "L";
    w[18][36] = "x"; w[18][37] = "x"; w[20][36] = "x"; w[20][37] = "x";

    rect(w, 8, 9, 22, 9, "u");

    rect(w, 14, 6, 8, 3, "j");
    w[6][16] = "k"; w[6][20] = "l"; w[7][14] = "m"; w[7][17] = "n";
    w[10][17] = "A"; w[10][20] = "B";

    w[13][12] = "p"; w[15][22] = "p"; w[16][10] = "p";
    w[14][19] = "e";

    w[22][20] = "D";

    w[16][30] = "N";
    w[18][17] = "X";

    w[19][10] = "C"; w[19][25] = "C"; w[5][10] = "C";
    w[19][13] = "d";
    return w;
  }

  function buildBlankRows() {
    var W = INTERNAL_W + 4, H = INTERNAL_H + 4, rows = [];
    for (var y = 0; y < H; y++) {
      var s = "";
      for (var x = 0; x < W; x++) s += (x < 2 || x >= W - 2 || y < 2 || y >= H - 2) ? "~" : ".";
      rows.push(s);
    }
    return rows;
  }

  function worldToRows(w) { return w.map(function (r) { return r.join(""); }); }
  function rowsToWorld(rows) { return rows.map(function (r) { return r.split(""); }); }

  function defaultNpcData() {
    var d = {};
    d["10,17"] = ["Oh, hello traveller!", "The old door to the north-east is locked.", "Gather every coin on the island and it will open."];
    d["30,20"] = ["Lovely weather for a stroll!", "Find all the coins to unlock the door."];
    d["30,16"] = ["Good evening. I am Mr. Holmes.", "Welcome to my study.", "Find the clues (coins) and the south door will open."];
    return d;
  }
  function defaultSignData() {
    return { "6,21": "Welcome to Pixel Isle! Collect every coin and the door to the north-east will unlock." };
  }

  var DEFAULT_SCENES = {
    current: "Home Room",
    scenes: {
      "Home Room": [
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvv#KKccccc####OOOOOO##vvvvvvvvvvv",
        "vvvvvvvvvvv#FFFFFFFFFFFFFFFFFF#vvvvvvvvvvv",
        "vvvvvvvvvvv#FFFFFFFFFFFFFFFFFF#vvvvvvvvvvv",
        "vvvvvvvvvvv#FFFFFFFBFFFAFFFFFF#vvvvvvvvvvv",
        "vvvvvvvvvvv#FjjFuuuuuuuuuuFFFFLvvvvvvvvvvv",
        "vvvvvvvvvvv#FnjFuuuuuuuuupFFFFLvvvvvvvvvvv",
        "vvvvvvvvvvv#FjjFuuuuuuuuuuFFFFLvvvvvvvvvvv",
        "vvvvvvvvvvv#FjlFupuuuuuuuuFFFFLvvvvvvvvvvv",
        "vvvvvvvvvvv#FjjFuuuuuuuuuuFFFFLvvvvvvvvvvv",
        "vvvvvvvvvvv#FFtFFFFFFFFFFNFFFF#vvvvvvvvvvv",
        "vvvvvvvvvvv#FFFFFFFFFXFFFFFFFF#vvvvvvvvvvv",
        "vvvvvvvvvvv#FFFFFFFFFFFFFFFFFF#vvvvvvvvvvv",
        "vvvvvvvvvvv##########D#########vvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
      ],
      "muder sence": [
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "v#####I###OOO######vvvvvvvvvvvvvvvvvvvvvvv",
        "v#FFFFFFFFFFFAFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "vLFFFFFFFFFFFFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "vLFFFFFFFuuuuFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "vLFFFFFdFpuuuFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "vLFFFFFFFuuuuFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "vLFFFFFFFuuupFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "v#FFFFFFFuuuuFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "v#FFFFFFFFFFFFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "v#FFFFFXFFFFFFFFFF#vvvvvvvvvvvvvvvvvvvvvvv",
        "v######D###########vvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
      ]
    },
    npcData: {
      "10,17": ["Oh, hello traveller!", "The old door to the north-east is locked.", "Gather every coin on the island and it will open."],
      "30,20": ["Lovely weather for a stroll!", "Find all the coins to unlock the door."],
      "30,16": ["Good evening. I am Mr. Holmes.", "Welcome to my study.", "Find the clues (coins) and the south door will open."],
      "25,14": ["Hello there!"],
      "25,15": ["Hello there!"],
      "13,6": ["Hello there!"]
    },
    signData: { "6,21": "Welcome to Pixel Isle! Collect every coin and the door to the north-east will unlock." }
  };

  /* ---------- storage ---------- */
  var STORE_KEY = "pixelisle.v4";

  function loadStore() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)); } catch (e) { return null; }
  }
  function persist(state) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({
        scenes: state.scenes, current: state.currentScene,
        npcData: state.npcData, signData: state.signData
      }));
    } catch (e) {}
  }

  function initStore() {
    var store = loadStore();
    var scenes, current, npcData, signData;
    if (store && store.scenes && Object.keys(store.scenes).length) {
      scenes = store.scenes;
      current = (store.current && scenes[store.current]) ? store.current : Object.keys(scenes)[0];
      npcData = store.npcData || {};
      signData = store.signData || {};
    } else {
      scenes = JSON.parse(JSON.stringify(DEFAULT_SCENES.scenes));
      current = DEFAULT_SCENES.current;
      npcData = JSON.parse(JSON.stringify(DEFAULT_SCENES.npcData));
      signData = JSON.parse(JSON.stringify(DEFAULT_SCENES.signData));
    }
    return { scenes: scenes, currentScene: current, npcData: npcData, signData: signData };
  }

  /* ---------- world metadata ---------- */
  var SOLID_BASE = {
    "~": 1, "T": 1, "R": 1, "W": 1, "r": 1, "=": 1,
    "#": 1, "O": 1, "Y": 1, "L": 1, "E": 1, "A": 1, "B": 1, "Q": 1, "V": 1, "I": 1,
    "G": 1, "H": 1, "J": 1, "K": 1, "M": 1, "c": 1, "j": 1, "k": 1, "l": 1, "m": 1,
    "n": 1, "x": 1, "t": 1, "y": 1, "v": 1, "U": 1, "a": 1
  };
  var OVERLAY = { "T": 1, "R": 1, "f": 1, "=": 1, "S": 1, "C": 1, "b": 1 };

  function rebuild(world, npcData) {
    var W = world[0].length, H = world.length;
    var npcs = [], spawn = null, coins = 0, fCount = 0, dotCount = 0;
    for (var y = 0; y < H; y++) {
      for (var x = 0; x < W; x++) {
        var c = world[y][x];
        if (c === "C") coins++;
        else if (c === "N") npcs.push({ x: x * TILE, y: y * TILE, w: TILE, h: TILE, lines: (npcData && npcData[x + "," + y]) || ["Hello!"] });
        else if (c === "X") spawn = { x: x * TILE, y: y * TILE };
        if (c === "F") fCount++;
        else if (c === ".") dotCount++;
      }
    }
    if (!spawn) spawn = { x: 5 * TILE, y: 19 * TILE };
    var ground = fCount > dotCount ? "F" : ".";
    var indoor = ground === "F";
    for (var i = 0; i < npcs.length; i++) npcs[i].frames = [indoor ? holmesNpc : npcSprites[i % 2]];
    return {
      W: W, H: H, PXW: W * TILE, PXH: H * TILE,
      npcs: npcs, spawn: spawn, coinsLeft: coins, doorLocked: coins > 0,
      ground: ground, indoor: indoor
    };
  }

  /* ---------- drawing ---------- */
  function drawSprite(ctx, img, x, y) {
    ctx.drawImage(img, Math.round(x), Math.round(y), TILE, TILE);
  }

  function drawChar(ctx, img, x, y) {
    ctx.drawImage(img, Math.round(x), Math.round(y) - TILE, TILE, TILE * 2);
  }

  function drawBigChairs(ctx, world, tx0, ty0, tx1, ty1, camX, camY) {
    for (var ty = ty0; ty <= ty1; ty++) {
      for (var tx = tx0; tx <= tx1; tx++) {
        if (tx < 0 || ty < 0 || ty >= world.length || tx >= world[0].length) continue;
        var c = world[ty][tx];
        var img = c === "A" ? CHAIR_RED : c === "B" ? CHAIR_OLIVE : c === "d" ? DEAD_BODY : null;
        if (!img) continue;
        var sx = tx * TILE - camX, sy = ty * TILE - camY;
        var ox = Math.round(sx + (TILE - img.width) / 2);
        var oy = Math.round(sy + TILE - img.height);
        ctx.drawImage(img, ox, oy, img.width, img.height);
      }
    }
  }

  function drawTile(ctx, c, tx, ty, sx, sy, doorLocked, ground) {
    var gi = (tx * 13 + ty * 7) % grassTiles.length;
    var wf = (Math.floor(performance.now() / 400)) % 2;
    function groundTile() {
      if (ground === "F") drawSprite(ctx, FLOOR, sx, sy);
      else drawSprite(ctx, grassTiles[gi], sx, sy);
    }
    if (c === ".") drawSprite(ctx, grassTiles[gi], sx, sy);
    else if (c === "N" || c === "X") groundTile();
    else if (c === "~") drawSprite(ctx, waterTiles[wf], sx, sy);
    else if (c === "P") drawSprite(ctx, pathTiles[(tx + ty) % pathTiles.length], sx, sy);
    else if (c === "W") drawSprite(ctx, brickTile, sx, sy);
    else if (c === "r") drawSprite(ctx, roofTile, sx, sy);
    else if (c === "D") drawSprite(ctx, doorLocked ? DOOR_CLOSED : DOOR_OPEN, sx, sy);
    else if (c === "F") drawSprite(ctx, FLOOR, sx, sy);
    else if (c === "w") drawSprite(ctx, LAB_FLOOR, sx, sy);
    else if (c === "U") drawSprite(ctx, LAB_WALLS, sx, sy);
    else if (c === "a") drawSprite(ctx, WORKBENCH, sx, sy);
    else if (c === "#") drawSprite(ctx, WALL, sx, sy);
    else if (c === "u") drawSprite(ctx, RUG, sx, sy);
    else if (c === "O") drawSprite(ctx, WINDOW, sx, sy);
    else if (c === "Y") drawSprite(ctx, CURTAIN, sx, sy);
    else if (c === "L") drawSprite(ctx, BOOKSHELF, sx, sy);
    else if (c === "E") drawSprite(ctx, FIREPLACE, sx, sy);
    else if (c === "A" || c === "B" || c === "d") groundTile();
    else if (c === "Q") drawSprite(ctx, TABLE, sx, sy);
    else if (c === "V") drawSprite(ctx, COAT, sx, sy);
    else if (c === "Z") drawSprite(ctx, STAIRS, sx, sy);
    else if (c === "I") drawSprite(ctx, PICTURE, sx, sy);
    else if (c === "G") drawSprite(ctx, CLOCK_TOP, sx, sy);
    else if (c === "H") drawSprite(ctx, CLOCK_MID, sx, sy);
    else if (c === "J") drawSprite(ctx, CLOCK_BASE, sx, sy);
    else if (c === "K") drawSprite(ctx, CABINET, sx, sy);
    else if (c === "M") drawSprite(ctx, MAP, sx, sy);
    else if (c === "c") drawSprite(ctx, CORK, sx, sy);
    else if (c === "j") drawSprite(ctx, DESK_BASE, sx, sy);
    else if (c === "k") drawSprite(ctx, DESK_PHONE, sx, sy);
    else if (c === "l") drawSprite(ctx, DESK_LAMP, sx, sy);
    else if (c === "m") drawSprite(ctx, DESK_PAPERS, sx, sy);
    else if (c === "n") drawSprite(ctx, DESK_MUG, sx, sy);
    else if (c === "x") drawSprite(ctx, BOX, sx, sy);
    else if (c === "t") drawSprite(ctx, TRASH, sx, sy);
    else if (c === "y") drawSprite(ctx, KETTLE, sx, sy);
    else if (c === "e") drawSprite(ctx, CAT, sx, sy);
    else if (c === "p") drawSprite(ctx, PAPERS, sx, sy);
    else if (c === "v") drawSprite(ctx, VOID, sx, sy);
    else if (OVERLAY[c]) {
      groundTile();
      if (c === "T") drawSprite(ctx, TREE, sx, sy);
      else if (c === "R") drawSprite(ctx, ROCK, sx, sy);
      else if (c === "f") drawSprite(ctx, FLOWER, sx, sy);
      else if (c === "=") drawSprite(ctx, FENCE, sx, sy);
      else if (c === "S") drawSprite(ctx, SIGN, sx, sy);
      else if (c === "C") drawSprite(ctx, COIN, sx, sy);
      else if (c === "b") drawSprite(ctx, STRAWBERRY, sx, sy);
    }
  }

  function makeThumb(c) {
    var cv = document.createElement("canvas");
    cv.width = 16; cv.height = 16;
    var g = cv.getContext("2d");
    var gr = grassTiles[0];
    function gr2() { g.drawImage(gr, 0, 0, 16, 16); }
    if (c === ".") g.drawImage(gr, 0, 0, 16, 16);
    else if (c === "~") g.drawImage(waterTiles[0], 0, 0, 16, 16);
    else if (c === "P") g.drawImage(pathTiles[0], 0, 0, 16, 16);
    else if (c === "W") g.drawImage(brickTile, 0, 0, 16, 16);
    else if (c === "r") g.drawImage(roofTile, 0, 0, 16, 16);
    else if (c === "D") g.drawImage(DOOR_CLOSED, 0, 0, 16, 16);
    else if (c === "F") g.drawImage(FLOOR, 0, 0, 16, 16);
    else if (c === "w") g.drawImage(LAB_FLOOR, 0, 0, 16, 16);
    else if (c === "U") g.drawImage(LAB_WALLS, 0, 0, 16, 16);
    else if (c === "a") g.drawImage(WORKBENCH, 0, 0, 16, 16);
    else if (c === "#") g.drawImage(WALL, 0, 0, 16, 16);
    else if (c === "u") g.drawImage(RUG, 0, 0, 16, 16);
    else if (c === "O") g.drawImage(WINDOW, 0, 0, 16, 16);
    else if (c === "Y") g.drawImage(CURTAIN, 0, 0, 16, 16);
    else if (c === "L") g.drawImage(BOOKSHELF, 0, 0, 16, 16);
    else if (c === "E") g.drawImage(FIREPLACE, 0, 0, 16, 16);
    else if (c === "A") g.drawImage(CHAIR_RED, 0, 0, 16, 16);
    else if (c === "B") g.drawImage(CHAIR_OLIVE, 0, 0, 16, 16);
    else if (c === "Q") g.drawImage(TABLE, 0, 0, 16, 16);
    else if (c === "V") g.drawImage(COAT, 0, 0, 16, 16);
    else if (c === "Z") g.drawImage(STAIRS, 0, 0, 16, 16);
    else if (c === "I") g.drawImage(PICTURE, 0, 0, 16, 16);
    else if (c === "G") g.drawImage(CLOCK_TOP, 0, 0, 16, 16);
    else if (c === "H") g.drawImage(CLOCK_MID, 0, 0, 16, 16);
    else if (c === "J") g.drawImage(CLOCK_BASE, 0, 0, 16, 16);
    else if (c === "K") g.drawImage(CABINET, 0, 0, 16, 16);
    else if (c === "M") g.drawImage(MAP, 0, 0, 16, 16);
    else if (c === "c") g.drawImage(CORK, 0, 0, 16, 16);
    else if (c === "j") g.drawImage(DESK_BASE, 0, 0, 16, 16);
    else if (c === "k") g.drawImage(DESK_PHONE, 0, 0, 16, 16);
    else if (c === "l") g.drawImage(DESK_LAMP, 0, 0, 16, 16);
    else if (c === "m") g.drawImage(DESK_PAPERS, 0, 0, 16, 16);
    else if (c === "n") g.drawImage(DESK_MUG, 0, 0, 16, 16);
    else if (c === "x") g.drawImage(BOX, 0, 0, 16, 16);
    else if (c === "t") g.drawImage(TRASH, 0, 0, 16, 16);
    else if (c === "y") g.drawImage(KETTLE, 0, 0, 16, 16);
    else if (c === "e") g.drawImage(CAT, 0, 0, 16, 16);
    else if (c === "p") g.drawImage(PAPERS, 0, 0, 16, 16);
    else if (c === "v") g.drawImage(VOID, 0, 0, 16, 16);
    else if (c === "N") { gr2(); g.drawImage(npcSprites[0], 0, 0, 16, 16); }
    else if (c === "X") { gr2(); g.drawImage(playerSpriteDown, 0, 0, 16, 16); }
    else if (OVERLAY[c]) {
      gr2();
      var im = c === "T" ? TREE : c === "R" ? ROCK : c === "f" ? FLOWER : c === "=" ? FENCE : c === "S" ? SIGN : c === "b" ? STRAWBERRY : COIN;
      g.drawImage(im, 0, 0, 16, 16);
    }
    return cv;
  }

  var PALETTE = [
    { c: ".", label: "Grass" }, { c: "~", label: "Water" }, { c: "P", label: "Path" },
    { c: "T", label: "Tree" }, { c: "R", label: "Rock" }, { c: "f", label: "Flower" },
    { c: "=", label: "Fence" }, { c: "W", label: "Brick" }, { c: "r", label: "Roof" },
    { c: "D", label: "Door" }, { c: "C", label: "Coin" }, { c: "S", label: "Sign" },
    { c: "b", label: "Berry" }, { c: "N", label: "NPC" }, { c: "X", label: "Spawn" },
    { c: "F", label: "Floor" }, { c: "w", label: "Lab floor" }, { c: "U", label: "Lab wall" }, { c: "a", label: "Workbench" }, { c: "#", label: "Paneled wall" }, { c: "u", label: "Rug" },
    { c: "O", label: "Night window" }, { c: "L", label: "Bookshelf" }, { c: "I", label: "Picture" },
    { c: "c", label: "Corkboard" }, { c: "M", label: "World map" }, { c: "j", label: "Desk" },
    { c: "k", label: "Desk + phone" }, { c: "l", label: "Desk + lamp" }, { c: "m", label: "Desk + files" },
    { c: "n", label: "Desk + mug" }, { c: "A", label: "Chair" }, { c: "B", label: "Chair 2" },
    { c: "G", label: "Clock top" }, { c: "H", label: "Clock body" }, { c: "J", label: "Clock base" },
    { c: "K", label: "Filing cabinet" }, { c: "V", label: "Coat rack" }, { c: "x", label: "Box" },
    { c: "t", label: "Trash can" }, { c: "y", label: "Kettle table" }, { c: "e", label: "Cat (rug)" },
    { c: "p", label: "Papers (rug)" }, { c: "v", label: "Void" }, { c: "d", label: "Dead body" }
  ];

  var CATALOG = {
    "Grass": grassTiles[0], "Grass 2": grassTiles[1], "Grass 3": grassTiles[2],
    "Path": pathTiles[0], "Path 2": pathTiles[1],
    "Water": waterTiles[0], "Water 2": waterTiles[1],
    "Brick": brickTile, "Roof": roofTile,
    "Tree": TREE, "Rock": ROCK, "Flower": FLOWER, "Fence": FENCE, "Sign": SIGN,
    "Coin": COIN, "Door closed": DOOR_CLOSED, "Door open": DOOR_OPEN, "Berry": STRAWBERRY,
    "Floor": FLOOR, "Lab floor": LAB_FLOOR, "Lab wall": LAB_WALLS, "Workbench": WORKBENCH, "Wall": WALL, "Rug": RUG, "Night window": WINDOW, "Curtain": CURTAIN,
    "Bookshelf": BOOKSHELF, "Fireplace": FIREPLACE, "Chair red": CHAIR_RED, "Chair olive": CHAIR_OLIVE,
    "Table": TABLE, "Cabinet": CABINET, "Stairs": STAIRS, "Picture": PICTURE,
    "Desk": DESK_BASE, "Desk phone": DESK_PHONE, "Desk lamp": DESK_LAMP,
    "Desk papers": DESK_PAPERS, "Desk mug": DESK_MUG,
    "Corkboard": CORK, "World map": MAP, "Clock top": CLOCK_TOP, "Clock body": CLOCK_MID,
    "Clock base": CLOCK_BASE, "Box": BOX, "Trash can": TRASH, "Kettle table": KETTLE,
    "Coat rack": COAT, "Cat": CAT, "Papers": PAPERS, "Void": VOID, "Dead body": DEAD_BODY,
    "Player down 1": playerFrames.down[0], "Player down 2": playerFrames.down[1],
    "Player up 1": playerFrames.up[0], "Player up 2": playerFrames.up[1],
    "Player left 1": playerFrames.left[0], "Player left 2": playerFrames.left[1],
    "Player right 1": playerFrames.right[0], "Player right 2": playerFrames.right[1],
    "NPC villager 1": npcSprites[0], "NPC villager 2": npcSprites[1], "NPC Holmes": holmesNpc,
    "Player male": PSY_PLAYER_MALE, "Player female": PSY_PLAYER_FEMALE
  };

  var RAW = {
    "Player shape DOWN": { rows: CH_DOWN, pal: PLAYER_COLORS },
    "Player shape UP": { rows: CH_UP, pal: PLAYER_COLORS },
    "Player shape LEFT": { rows: CH_LEFT, pal: PLAYER_COLORS }
  };

  return {
    VIEW_W: VIEW_W,
    VIEW_H: VIEW_H,
    TILE: TILE,
    INTERNAL_W: INTERNAL_W,
    INTERNAL_H: INTERNAL_H,
    playerFrames: playerFrames,
    playerSpriteDown: playerSpriteDown,
    npcSprites: npcSprites,
    holmesNpc: holmesNpc,
    grassTiles: grassTiles,
    CATALOG: CATALOG,
    DEFAULT_SCENES: DEFAULT_SCENES,
    RAW: RAW,
    SOLID_BASE: SOLID_BASE,
    OVERLAY: OVERLAY,
    PANEL_PALETTE: PALETTE,
    PALETTE: PALETTE,
    sprite: sprite,
    buildIslandWorld: buildIslandWorld,
    buildHolmesWorld: buildHolmesWorld,
    buildBlankRows: buildBlankRows,
    worldToRows: worldToRows,
    rowsToWorld: rowsToWorld,
    defaultNpcData: defaultNpcData,
    defaultSignData: defaultSignData,
    initStore: initStore,
    persist: persist,
    rebuild: rebuild,
    drawSprite: drawSprite,
    drawChar: drawChar,
    drawPlayerLook: drawPlayerLook,
    PLAYER_LOOKS: PLAYER_LOOKS,
    PSY_PLAYER_MALE: PSY_PLAYER_MALE,
    PSY_PLAYER_FEMALE: PSY_PLAYER_FEMALE,
    drawBigChairs: drawBigChairs,
    drawTile: drawTile,
    makeThumb: makeThumb
  };
})();
