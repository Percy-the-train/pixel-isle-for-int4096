import os
import random
from PIL import Image, ImageDraw, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)
random.seed(4096)

GAME = r"C:\Users\Percy\Downloads\WhatsApp Image 2026-11-18 at 2.13.31 PM.jpeg"


def wood_background(path, w=1600, h=900):
    img = Image.new("RGB", (w, h), "#7c4d2a")
    d = ImageDraw.Draw(img)
    shades = ["#8a5931", "#81502c", "#946137", "#744627", "#8f5c33", "#7a4b29"]
    plank_h = 52
    y = -6
    row = 0
    while y < h:
        base = shades[row % len(shades)]
        d.rectangle([0, y, w, y + plank_h - 1], fill=base)
        # top highlight and bottom grout
        d.line([(0, y), (w, y)], fill="#a06a3c", width=2)
        d.line([(0, y + plank_h - 3), (w, y + plank_h - 3)], fill="#5c381e", width=2)
        d.line([(0, y + plank_h - 1), (w, y + plank_h - 1)], fill="#3f2412", width=1)
        # staggered vertical joints
        offset = (row * 173) % 320
        for x in range(offset, w, 320):
            d.line([(x, y + 2), (x, y + plank_h - 4)], fill="#4c2d19", width=2)
            d.line([(x + 1, y + 2), (x + 1, y + plank_h - 4)], fill="#9a6639", width=1)
        # grain
        for _ in range(9):
            gx = random.randrange(0, w)
            gy = random.randrange(y + 5, y + plank_h - 6)
            glen = random.randrange(18, 120)
            c = "#9b6738" if random.random() > 0.45 else "#6d4324"
            d.line([(gx, gy), (min(w, gx + glen), gy)], fill=c, width=1)
        y += plank_h
        row += 1
    # darken slightly for slide use
    img = ImageEnhance.Brightness(img).enhance(0.78)
    img = ImageEnhance.Color(img).enhance(0.92)
    img.save(path)


def carpet_background(path, w=1600, h=900):
    base = (110, 38, 39)
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    # subtle vertical plank-like carpet seams every 200px
    for x in range(0, w, 200):
        d.line([(x, 0), (x, h)], fill=(96, 32, 34), width=2)
    motif = [
        "..0..",
        ".010.",
        "01210",
        ".010.",
        "..0..",
    ]
    colmap = {"0": (94, 29, 31), "1": (143, 53, 52), "2": (168, 77, 69)}
    step = 64
    px = 8
    for gy in range(0, h, step):
        for gx in range(0, w, step):
            for ry, row in enumerate(motif):
                for rx, ch in enumerate(row):
                    if ch in colmap:
                        x0 = gx + rx * px + 12
                        y0 = gy + ry * px + 10
                        d.rectangle([x0, y0, x0 + px - 1, y0 + px - 1], fill=colmap[ch])
    # vignette
    vig = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vig)
    for i in range(70):
        v = int(105 * (i / 70.0))
        vd.rectangle([i, i, w - 1 - i, h - 1 - i], outline=v)
    dark = Image.new("RGB", (w, h), (38, 12, 14))
    img = Image.composite(img, dark, vig.point(lambda p: 255 - p))
    img.save(path)


def title_background(path, w=1920, h=1080):
    im = Image.open(GAME).convert("RGB")
    # crop to 16:9
    tw, th = im.size
    target = w / h
    if tw / th > target:
        nw = int(th * target)
        im = im.crop(((tw - nw) // 2, 0, (tw + nw) // 2, th))
    else:
        nh = int(tw / target)
        im = im.crop((0, (th - nh) // 2, tw, (th + nh) // 2))
    im = im.resize((w, h), Image.NEAREST)
    # warm dark overlay
    overlay = Image.new("RGB", (w, h), (32, 18, 12))
    im = Image.blend(im, overlay, 0.58)
    d = ImageDraw.Draw(im)
    # vignette
    for i in range(120):
        a = int(120 * (i / 120.0))
        d.rectangle([i, i, w - 1 - i, h - 1 - i], outline=(20 - a // 8, 12 - a // 12, 8))
    # scanlines
    scan = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for y in range(0, h, 4):
        sd.line([(0, y), (w, y)], fill=(0, 0, 0, 26))
    im = Image.alpha_composite(im.convert("RGBA"), scan).convert("RGB")
    im.save(path)


def paper_panel(path, w=1600, h=840):
    img = Image.new("RGB", (w, h), "#efe2c0")
    d = ImageDraw.Draw(img)
    for _ in range(9000):
        x = random.randrange(w)
        y = random.randrange(h)
        c = random.choice(["#e7d8b3", "#f6ebce", "#e2d1a9", "#f1e4c4"])
        d.point((x, y), fill=c)
    # faint grid
    for x in range(0, w, 12):
        d.line([(x, 0), (x, h)], fill="#e9dab6", width=1)
    for y in range(0, h, 12):
        d.line([(0, y), (w, y)], fill="#e9dab6", width=1)
    # edge wear
    for i in range(10):
        c = "#d9c69d" if i % 2 == 0 else "#e5d4ad"
        d.rectangle([i, i, w - 1 - i, h - 1 - i], outline=c)
    img.save(path)


ICON_PALETTE = {
    ".": None,
    "#": "#171319",
    "w": "#f1e4c4",
    "y": "#e3a83b",
    "r": "#9a3434",
    "g": "#7aa549",
    "b": "#26324f",
    "x": "#8d7a5a",
}

ICONS = {
    "news": [
        "................",
        ".##############.",
        ".#wwwwwwwwwwww#.",
        ".#w##########w#.",
        ".#w#yyyyyyyy#w#.",
        ".#w#y######y#w#.",
        ".#w#yyyyyyyy#w#.",
        ".#w##########w#.",
        ".#wwwwwwwwwwww#.",
        ".#w##ww##ww##w#.",
        ".#wwwwwwwwwwww#.",
        ".#w##ww##ww##w#.",
        ".#wwwwwwwwwwww#.",
        ".##############.",
        "................",
        "................",
    ],
    "game": [
        "................",
        "................",
        "....########....",
        "..##wwwwwwww##..",
        ".#wwwwwwwwwwww#.",
        ".#ww#wwwwww#ww#.",
        ".#wwwyyyyyywww#.",
        ".#ww#wwwwww#ww#.",
        "..##wwwwwwww##..",
        "....##w##w##....",
        ".....#....#.....",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "model": [
        "................",
        "....#.#..#.#....",
        "...##########...",
        "..#wwwwwwwwww#..",
        ".#w#wwwwwwww#w#.",
        ".#wwwwwwwwwwww#.",
        ".#w#wwwwwwww#w#.",
        ".#wwwwwwwwwwww#.",
        ".#w#wwwwwwww#w#.",
        "..#wwwwwwwwww#..",
        "...##########...",
        "....#.#..#.#....",
        "................",
        "................",
        "................",
        "................",
    ],
    "chart": [
        "................",
        "................",
        ".#..............",
        ".#..............",
        ".#....##........",
        ".#....##...##...",
        ".#.##.##...##...",
        ".#.##.##.#.##...",
        ".#.##.##.#.##.#.",
        ".#.##.##.#.##.#.",
        ".###############",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "alert": [
        "................",
        ".......##.......",
        "......####......",
        "......#ww#......",
        ".....#wwww#.....",
        ".....#wwww#.....",
        "....#ww##ww#....",
        "....#ww##ww#....",
        "...#wwwwwwww#...",
        "...#wwwwwwww#...",
        "..#wwww##wwww#..",
        "..#wwww##wwww#..",
        "..#wwwwwwwwww#..",
        "...##########...",
        "................",
        "................",
    ],
    "check": [
        "................",
        "............##..",
        "...........###..",
        "..........###...",
        ".........###....",
        ".##.....###.....",
        "###....###......",
        ".###..###.......",
        "..######........",
        "...####.........",
        "....##..........",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "clue": [
        "................",
        ".....######.....",
        "....##wwww##....",
        "...##wwwwww##...",
        "...##ww##ww##...",
        "...##wwwwww##...",
        "....##wwww##....",
        ".....######.....",
        ".......###......",
        "........###.....",
        ".........###....",
        "..........###...",
        "...........###..",
        "................",
        "................",
        "................",
    ],
    "book": [
        "................",
        "..###########...",
        "..#wwwwwwwww#...",
        "..#w#######w#...",
        "..#wwwwwwwww#...",
        "..#w#######w#...",
        "..#wwwwwwwww#...",
        "..#w#######w#...",
        "..#wwwwwwwww#...",
        "..#w#######w#...",
        "..#wwwwwwwww#...",
        "..###########...",
        "................",
        "................",
        "................",
        "................",
    ],
    "gear": [
        "................",
        "....#..#..#.....",
        "...#ww#ww#ww#...",
        "..#wwwwwwwwww#..",
        ".#wwww####wwww#.",
        ".#www##ww##www#.",
        ".#www#wwww#www#.",
        ".#www##ww##www#.",
        ".#wwww####wwww#.",
        "..#wwwwwwwwww#..",
        "...#ww#ww#ww#...",
        "....#..#..#.....",
        "................",
        "................",
        "................",
        "................",
    ],
    "target": [
        "................",
        "....########....",
        "..##wwwwwwww##..",
        ".#wwww####wwww#.",
        ".#www##ww##www#.",
        "#www##wwww##www#",
        "#www#wwwwww#www#",
        "#www##wwww##www#",
        ".#www##ww##www#.",
        ".#wwww####wwww#.",
        "..##wwwwwwww##..",
        "....########....",
        "................",
        "................",
        "................",
        "................",
    ],
}


def chart_background(path, kind="bar", w=1400, h=800):
    img = Image.new("RGB", (w, h), "#e9dbb8")
    d = ImageDraw.Draw(img)
    for x in range(0, w, 20):
        d.line([(x, 0), (x, h)], fill="#e2d2ab", width=1)
    for y in range(0, h, 20):
        d.line([(0, y), (w, y)], fill="#e2d2ab", width=1)
    ax_l, ax_r, ax_t, ax_b = 110, w - 60, 90, h - 100
    d.line([(ax_l, ax_t), (ax_l, ax_b)], fill="#a58f68", width=4)
    d.line([(ax_l, ax_b), (ax_r, ax_b)], fill="#a58f68", width=4)
    if kind == "bar":
        n = 5
        bw = (ax_r - ax_l) // (n + 3)
        heights = [0.32, 0.48, 0.62, 0.74, 0.9]
        for i, hh in enumerate(heights):
            x0 = ax_l + 40 + i * (bw + 26)
            y0 = ax_b - int((ax_b - ax_t - 30) * hh)
            d.rectangle([x0, y0, x0 + bw, ax_b], fill="#d6c294", outline="#b9a273", width=3)
            d.rectangle([x0, y0, x0 + bw, y0 + 10], fill="#c7b083")
            d.line([(x0 + 8, ax_b + 18), (x0 + bw - 8, ax_b + 18)], fill="#b9a273", width=4)
    elif kind == "line":
        pts = [(ax_l + 40, ax_b - 120), (ax_l + 230, ax_b - 260), (ax_l + 420, ax_b - 190),
               (ax_l + 610, ax_b - 340), (ax_l + 800, ax_b - 300), (ax_l + 990, ax_b - 470),
               (ax_l + 1130, ax_b - 520)]
        d.line(pts, fill="#b9a273", width=5, joint="curve")
        for px, py in pts:
            d.rectangle([px - 7, py - 7, px + 7, py + 7], fill="#e3a83b", outline="#8a5931", width=2)
            d.line([(px, ax_b), (px, py)], fill="#d6c294", width=2)
    elif kind == "matrix":
        x0, y0 = ax_l + 130, ax_t + 50
        cell = 150
        for r in range(3):
            for c in range(3):
                shade = "#d9c69d" if r == c else "#e4d5b1"
                d.rectangle([x0 + c * cell, y0 + r * cell, x0 + (c + 1) * cell - 4, y0 + (r + 1) * cell - 4],
                            fill=shade, outline="#b9a273", width=3)
                if r == c:
                    d.rectangle([x0 + c * cell + 12, y0 + r * cell + 12,
                                 x0 + (c + 1) * cell - 16, y0 + (r + 1) * cell - 16],
                                fill="#c7b083")
    img.save(path)


def make_icons(folder):
    os.makedirs(folder, exist_ok=True)
    for name, grid in ICONS.items():
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y, row in enumerate(grid):
            for x, ch in enumerate(row):
                col = ICON_PALETTE.get(ch)
                if col:
                    im.putpixel((x, y), tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
        im = im.resize((128, 128), Image.NEAREST)
        im.save(os.path.join(folder, f"{name}.png"))


if __name__ == "__main__":
    wood_background(os.path.join(ASSETS, "bg_wood.png"))
    carpet_background(os.path.join(ASSETS, "bg_carpet.png"))
    title_background(os.path.join(ASSETS, "bg_title.png"))
    paper_panel(os.path.join(ASSETS, "panel_paper.png"))
    chart_background(os.path.join(ASSETS, "ph_bar.png"), "bar")
    chart_background(os.path.join(ASSETS, "ph_line.png"), "line")
    chart_background(os.path.join(ASSETS, "ph_matrix.png"), "matrix")
    make_icons(os.path.join(ASSETS, "icons"))
    print("assets written")
