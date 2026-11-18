import os
from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_LINE_DASH_STYLE as MSO_LINE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
CHARTS = os.path.join(ASSETS, "charts")
OUT = os.environ.get("DECK_OUT") or os.path.join(HERE, "Pixel_Isle_INT4096.pptx")

PRESS_PATH = os.path.join(ASSETS, "fonts", "PressStart2P-Regular.ttf")
VT_PATH = os.path.join(ASSETS, "fonts", "VT323-Regular.ttf")
PRESS = "Press Start 2P"
BODY = "VT323"

SW, SH = 13.333, 7.5
PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 0.42, 0.34, 12.49, 6.52
CX, CW = 0.78, 11.76

INK = RGBColor(0x17, 0x13, 0x19)
INK_SOFT = RGBColor(0x3A, 0x2A, 0x1E)
CREAM = RGBColor(0xF1, 0xE4, 0xC4)
CREAM_LIGHT = RGBColor(0xF8, 0xEE, 0xD4)
CREAM_DARK = RGBColor(0xE3, 0xD2, 0xAB)
GOLD = RGBColor(0xE3, 0xA8, 0x3B)
GOLD_DARK = RGBColor(0xB9, 0x7A, 0x1E)
RED = RGBColor(0x9A, 0x34, 0x34)
RED_DARK = RGBColor(0x6E, 0x22, 0x24)
GREEN = RGBColor(0x7A, 0xA5, 0x49)
GREEN_DARK = RGBColor(0x3F, 0x5E, 0x2A)
NAVY = RGBColor(0x26, 0x32, 0x4F)
MUTED = RGBColor(0x6B, 0x5A, 0x44)
WHITE = RGBColor(0xFF, 0xF8, 0xE7)

_font_cache = {}


def hexrgb(c):
    return RGBColor.from_string(c)


def px_font(path):
    if path not in _font_cache:
        _font_cache[path] = ImageFont.truetype(path, 100)
    return _font_cache[path]


def text_width_in(text, size, path):
    return px_font(path).getlength(text) / 100.0 * size / 72.0


def fit_pixel(text, max_w, sizes=(54, 48, 44, 40, 36, 32, 28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 9, 8)):
    for s in sizes:
        if text_width_in(text, s, PRESS_PATH) <= max_w:
            return s
    return sizes[-1]


def add_bg(slide, name):
    slide.shapes.add_picture(os.path.join(ASSETS, name), 0, 0, width=Inches(SW), height=Inches(SH))


def rect(slide, x, y, w, h, fill=None, line=None, line_w=2.5, shadow=False,
         dash=None, shape=MSO_SHAPE.RECTANGLE):
    if shadow:
        s = slide.shapes.add_shape(shape, Inches(x + 0.07), Inches(y + 0.07), Inches(w), Inches(h))
        s.fill.solid()
        s.fill.fore_color.rgb = INK
        s.line.fill.background()
        s.shadow.inherit = False
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
        if dash:
            shp.line.dash_style = dash
    shp.shadow.inherit = False
    return shp


def line_h(slide, x, y, w, color=INK, weight=2.0):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Pt(weight))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def line_v(slide, x, y, h, color=INK, weight=2.0):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Pt(weight), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def set_text_shadow(run, color="171319", dist=2, blur=0, direction=2700000):
    rPr = run._r.get_or_add_rPr()
    effect = etree.SubElement(rPr, qn("a:effectLst"))
    shdw = etree.SubElement(effect, qn("a:outerShdw"))
    shdw.set("blurRad", str(int(blur * 12700)))
    shdw.set("dist", str(int(dist * 12700)))
    shdw.set("dir", str(direction))
    shdw.set("algn", "tl")
    shdw.set("rotWithShape", "0")
    clr = etree.SubElement(shdw, qn("a:srgbClr"))
    clr.set("val", color)


def text_box(slide, txt, x, y, w, h, font=BODY, size=20, color=INK, bold=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=0.92,
             shadow=None, margins=(0, 0, 0, 0), italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(margins[0])
    tf.margin_right = Inches(margins[1])
    tf.margin_top = Inches(margins[2])
    tf.margin_bottom = Inches(margins[3])
    try:
        tf.auto_size = None
    except Exception:
        pass
    lines = txt.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        r = p.add_run()
        r.text = ln
        r.font.name = font
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        if shadow:
            set_text_shadow(r, shadow[1], shadow[0], 0)
    return tb


def bullets(slide, x, y, w, h, items, size=19, color=INK, bullet_color=RED,
            gap=6, spacing=0.88):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    try:
        tf.auto_size = None
    except Exception:
        pass
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = spacing
        p.space_before = Pt(0)
        p.space_after = Pt(gap)
        r1 = p.add_run()
        r1.text = "> "
        r1.font.name = BODY
        r1.font.size = Pt(size)
        r1.font.bold = True
        r1.font.color.rgb = bullet_color
        if isinstance(item, tuple):
            lead, rest = item
            r2 = p.add_run()
            r2.text = lead
            r2.font.name = BODY
            r2.font.size = Pt(size)
            r2.font.bold = True
            r2.font.color.rgb = INK_SOFT
            r3 = p.add_run()
            r3.text = rest
            r3.font.name = BODY
            r3.font.size = Pt(size)
            r3.font.color.rgb = color
        else:
            r2 = p.add_run()
            r2.text = item
            r2.font.name = BODY
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
    return tb


def content_slide(prs, chapter, title, icon=None, page=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, "bg_wood.png")
    rect(slide, PANEL_X + 0.08, PANEL_Y + 0.08, PANEL_W, PANEL_H, fill=INK, line=None)
    slide.shapes.add_picture(os.path.join(ASSETS, "panel_paper.png"), Inches(PANEL_X), Inches(PANEL_Y),
                             width=Inches(PANEL_W), height=Inches(PANEL_H))
    rect(slide, PANEL_X, PANEL_Y, PANEL_W, PANEL_H, fill=None, line=INK, line_w=4)
    for px, py in [(PANEL_X, PANEL_Y), (PANEL_X + PANEL_W - 0.11, PANEL_Y),
                   (PANEL_X, PANEL_Y + PANEL_H - 0.11), (PANEL_X + PANEL_W - 0.11, PANEL_Y + PANEL_H - 0.11)]:
        rect(slide, px + 0.02, py + 0.02, 0.11, 0.11, fill=GOLD, line=INK, line_w=1.2)

    text_box(slide, chapter, CX, 0.47, 9.8, 0.24, font=BODY, size=12, color=MUTED)
    tsize = fit_pixel(title, 10.65, sizes=(34, 32, 30, 28, 26, 24, 22, 20, 18, 16))
    text_box(slide, title, CX, 0.78, 10.9, 0.62, font=PRESS, size=tsize, color=INK, spacing=0.95)
    if icon:
        slide.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"),
                                 Inches(11.86), Inches(0.62), width=Inches(0.52), height=Inches(0.52))
    line_h(slide, CX, 1.52, 11.72, color=INK, weight=2.4)
    line_h(slide, CX, 1.52, 1.35, color=RED, weight=2.4)
    if page is not None:
        footer(slide, len(prs.slides._sldIdLst))
    return slide


def footer(slide, page):
    text_box(slide, "PIXEL ISLE  //  INT4096  //  GROUP 2", CX, 7.03, 6.6, 0.25,
             font=BODY, size=11, color=GOLD)
    text_box(slide, "2026-27 SEM 1", 9.9, 7.03, 2.4, 0.25, font=BODY, size=11, color=GOLD,
             align=PP_ALIGN.RIGHT)
    rect(slide, 12.48, 6.99, 0.4, 0.3, fill=INK, line=None)
    text_box(slide, f"{page:02d}", 12.48, 7.02, 0.4, 0.24, font=PRESS, size=9, color=GOLD,
             align=PP_ALIGN.CENTER)


def section_slide(prs, num, title, subtitle, page):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, "bg_carpet.png")
    rect(slide, 0.6, 0.55, 2.65, 0.36, fill=INK, line=None)
    text_box(slide, "PIXEL ISLE // 001", 0.7, 0.63, 2.5, 0.24, font=PRESS, size=8, color=GOLD)
    text_box(slide, f"CHAPTER {num} // 04", 0.62, 1.35, 4.0, 0.3, font=BODY, size=16, color=GOLD)
    text_box(slide, num, 0.42, 1.55, 4.4, 2.4, font=PRESS, size=120, color=GOLD,
             shadow=(4, "171319"))
    text_box(slide, title, 4.45, 2.02, 8.2, 1.15, font=PRESS, size=fit_pixel(title, 8.0, (46, 42, 38, 34, 30, 26)),
             color=CREAM, shadow=(4, "171319"))
    line_h(slide, 4.5, 3.12, 2.2, color=GOLD, weight=3)
    text_box(slide, subtitle, 4.48, 3.42, 8.1, 0.8, font=BODY, size=26, color=CREAM, spacing=0.9)
    text_box(slide, "WASD TO ADVANCE", 9.8, 5.62, 3.0, 0.3, font=BODY, size=14, color=GOLD,
             align=PP_ALIGN.RIGHT)
    for i in range(4):
        on = (i + 1 == int(num))
        rect(slide, 0.62 + i * 0.62, 6.25, 0.48, 0.3, fill=GOLD if on else RED_DARK,
             line=INK, line_w=2)
        text_box(slide, f"{i+1:02d}", 0.62 + i * 0.62, 6.28, 0.48, 0.22, font=PRESS, size=7.5,
                 color=INK if on else CREAM, align=PP_ALIGN.CENTER)
    text_box(slide, "PIXEL ISLE  //  INT4096  //  GROUP 2", 0.62, 7.02, 6.6, 0.25,
             font=BODY, size=11, color=CREAM)
    text_box(slide, f"{len(prs.slides._sldIdLst):02d}", 12.45, 7.02, 0.45, 0.25, font=PRESS, size=9, color=GOLD,
             align=PP_ALIGN.RIGHT)
    return slide


def note_card(slide, x, y, w, h, title, body, accent=RED, icon=None,
              title_size=10, body_size=17, body_color=INK_SOFT):
    rect(slide, x, y, w, h, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    rect(slide, x, y, w, 0.36, fill=accent, line=INK, line_w=1.6)
    text_box(slide, title, x + 0.12, y + 0.09, w - (0.75 if icon else 0.2), 0.24,
             font=PRESS, size=title_size, color=CREAM)
    if icon:
        slide.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"),
                                 Inches(x + w - 0.45), Inches(y + 0.01), width=Inches(0.3), height=Inches(0.3))
    text_box(slide, body, x + 0.15, y + 0.47, w - 0.3, h - 0.55, font=BODY, size=body_size,
             color=body_color, spacing=0.86, anchor=MSO_ANCHOR.MIDDLE)


def stat_card(slide, x, y, w, h, big, label, sub=None, fill=INK, big_color=GOLD,
              label_color=CREAM, sub_color=CREAM_DARK):
    rect(slide, x, y, w, h, fill=fill, line=INK, line_w=3, shadow=True)
    bs = fit_pixel(big, w - 0.35, sizes=(56, 50, 46, 42, 38, 34, 30, 26, 22, 18))
    text_box(slide, big, x + 0.16, y + 0.14, w - 0.3, 0.85, font=PRESS, size=bs, color=big_color,
             spacing=0.95, shadow=(2, "000000"))
    text_box(slide, label, x + 0.18, y + 0.98, w - 0.34, 0.66, font=BODY, size=19, color=label_color,
             spacing=0.85)
    if sub:
        text_box(slide, sub, x + 0.18, y + h - 0.34, w - 0.34, 0.26, font=BODY, size=10,
                 color=sub_color)


def chart_placeholder(slide, x, y, w, h, fig, title, note, kind="bar", caption=None):
    rect(slide, x, y, w, h, fill=CREAM_DARK, line=INK, line_w=2.4, shadow=True)
    slide.shapes.add_picture(os.path.join(ASSETS, f"ph_{kind}.png"), Inches(x + 0.04), Inches(y + 0.04),
                             width=Inches(w - 0.08), height=Inches(h - 0.08))
    rect(slide, x, y, w, h, fill=None, line=RED, line_w=2.6, dash=MSO_LINE.DASH)
    for px, py in [(x, y), (x + w - 0.22, y), (x, y + h - 0.22), (x + w - 0.22, y + h - 0.22)]:
        rect(slide, px, py, 0.22, 0.22, fill=INK, line=None)
        rect(slide, px + 0.05, py + 0.05, 0.12, 0.12, fill=GOLD, line=None)
    tag_w = 1.15
    rect(slide, x + 0.22, y + 0.2, tag_w, 0.3, fill=INK, line=None)
    text_box(slide, fig, x + 0.22, y + 0.26, tag_w, 0.2, font=PRESS, size=8, color=GOLD,
             align=PP_ALIGN.CENTER)
    plate_w = min(w - 0.5, 6.2)
    rect(slide, x + 0.22, y + 0.62, plate_w, 1.18, fill=CREAM_LIGHT, line=INK, line_w=2)
    text_box(slide, title, x + 0.38, y + 0.76, plate_w - 0.32, 0.32, font=PRESS, size=12, color=RED,
             align=PP_ALIGN.CENTER)
    text_box(slide, note, x + 0.4, y + 1.12, plate_w - 0.36, 0.56, font=BODY, size=16, color=INK_SOFT,
             align=PP_ALIGN.CENTER, spacing=0.85)
    text_box(slide, "DROP CHART HERE", x + w - 2.0, y + h - 0.38, 1.75, 0.24, font=BODY, size=11,
             color=MUTED, align=PP_ALIGN.RIGHT)
    if caption:
        text_box(slide, caption, x, y + h + 0.08, w, 0.3, font=BODY, size=13, color=MUTED)


def chart_image(slide, x, y, w, h, fname, caption=None):
    path = os.path.join(CHARTS, fname)
    rect(slide, x, y, w, h, fill=CREAM_LIGHT, line=INK, line_w=2.6, shadow=True)
    with Image.open(path) as im:
        iw, ih = im.size
    ar = iw / ih
    inner_w, inner_h = w - 0.26, h - 0.26
    if (inner_w / inner_h) > ar:
        ph = inner_h
        pw = inner_h * ar
    else:
        pw = inner_w
        ph = inner_w / ar
    ix = x + (w - pw) / 2.0
    iy = y + (h - ph) / 2.0
    slide.shapes.add_picture(path, Inches(ix), Inches(iy), width=Inches(pw), height=Inches(ph))
    for px, py in [(x, y), (x + w - 0.18, y), (x, y + h - 0.18), (x + w - 0.18, y + h - 0.18)]:
        rect(slide, px, py, 0.18, 0.18, fill=GOLD, line=INK, line_w=1.2)
    if caption:
        text_box(slide, caption, x, y + h + 0.06, w, 0.26, font=BODY, size=12, color=MUTED)


def set_cell_borders(cell, color="171319", width=1.4):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for i, tag in enumerate(["a:lnL", "a:lnR", "a:lnT", "a:lnB"]):
        ln = etree.Element(qn(tag))
        ln.set("w", str(int(width * 12700)))
        ln.set("cap", "flat")
        ln.set("cmpd", "sng")
        ln.set("algn", "ctr")
        fill = etree.SubElement(ln, qn("a:solidFill"))
        clr = etree.SubElement(fill, qn("a:srgbClr"))
        clr.set("val", color)
        dash = etree.SubElement(ln, qn("a:prstDash"))
        dash.set("val", "solid")
        tcPr.insert(i, ln)


def cell_style(cell, txt, font=BODY, size=17, color=INK, fill=CREAM_LIGHT, bold=False,
               align=PP_ALIGN.LEFT):
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    cell.margin_left = Inches(0.09)
    cell.margin_right = Inches(0.06)
    cell.margin_top = Inches(0.02)
    cell.margin_bottom = Inches(0.02)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    set_cell_borders(cell)
    tf = cell.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.09)
    tf.margin_right = Inches(0.06)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = 0.9
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    r = p.add_run()
    r.text = txt
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color


def clickable_label(slide, x, y, w, h, txt, fill=INK, color=GOLD, size=9):
    rect(slide, x, y, w, h, fill=fill, line=None)
    text_box(slide, txt, x, y + (h - 0.2) / 2, w, 0.22, font=PRESS, size=size, color=color,
             align=PP_ALIGN.CENTER)


def notes(slide, txt):
    slide.notes_slide.notes_text_frame.text = txt


prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)

# ---------------------------------------------------------------- 1 TITLE
s = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(s, "bg_title.png")
rect(s, 0.55, 0.55, 7.55, 6.32, fill=INK, line=None)
s.shapes.add_picture(os.path.join(ASSETS, "panel_paper.png"), Inches(0.48), Inches(0.48),
                     width=Inches(7.55), height=Inches(6.32))
rect(s, 0.48, 0.48, 7.55, 6.32, fill=None, line=INK, line_w=4)
for px, py in [(0.48, 0.48), (7.92, 0.48), (0.48, 6.69), (7.92, 6.69)]:
    rect(s, px + 0.04, py + 0.04, 0.14, 0.14, fill=GOLD, line=INK, line_w=1.2)
clickable_label(s, 0.84, 0.82, 2.5, 0.34, "CASE FILE // 001", fill=RED, size=9)
text_box(s, "PIXEL ISLE", 0.8, 1.38, 6.95, 1.15, font=PRESS, size=44, color=GOLD,
         shadow=(4, "171319"))
text_box(s, "TURNING TODAY'S NEWS INTO A\nPLAYABLE DETECTIVE MYSTERY", 0.84, 2.62, 6.7, 0.95,
         font=PRESS, size=13, color=INK, spacing=1.45)
line_h(s, 0.84, 3.72, 6.6, color=INK, weight=2)
text_box(s, "A classical NLP pipeline that ranks the sentences that matter,\nthen rewrites them as clues in a daily murder mystery.",
         0.84, 3.9, 6.78, 0.9, font=BODY, size=19, color=INK_SOFT, spacing=0.9)
for i, lab in enumerate(["NLP", "CLASSICAL ML", "PIXEL GAME"]):
    rect(s, 0.84 + i * 1.55, 5.02, 1.4, 0.36, fill=CREAM_LIGHT, line=INK, line_w=2)
    text_box(s, lab, 0.84 + i * 1.55, 5.09, 1.4, 0.22, font=PRESS, size=7, color=INK,
             align=PP_ALIGN.CENTER)
rect(s, 0.84, 5.75, 2.95, 0.58, fill=RED, line=INK, line_w=3, shadow=True)
text_box(s, "PRESS START >>", 0.84, 5.91, 2.95, 0.28, font=PRESS, size=10, color=CREAM,
         align=PP_ALIGN.CENTER)
text_box(s, "INT4096  ARTIFICIAL INTELLIGENCE &\nMACHINE LEARNING IN EDUCATION", 4.15, 5.76, 3.55, 0.62,
         font=BODY, size=14, color=MUTED, spacing=0.88, align=PP_ALIGN.RIGHT)
text_box(s, "THE EDUCATION UNIVERSITY OF HONG KONG  //  2026-27 SEM 1", 0.84, 6.3, 6.95, 0.22,
         font=BODY, size=11, color=MUTED)
text_box(s, "GROUP 2  //  CHIU WAI YIU · LAI CHUN KUI · LAI WAN YAU SONYA · MAK TSUN WAI MARSIO ·\nWONG CHING WAI · WONG SUI KI · WONG TSZ CHING  //  18 NOV 2026",
         0.84, 6.52, 6.95, 0.52, font=BODY, size=10, color=MUTED)
clickable_label(s, 10.95, 6.75, 1.95, 0.32, "HOME ROOM // 22:40", fill=INK, size=7)
notes(s, "Timing 0:00-1:00. Open with the hook: today's news is usually a wall of text. Pixel Isle turns one real news story into a playable murder mystery. Say the group number and that this is an end-to-end NLP + game project. Keep this slide on screen while people settle.")

# ---------------------------------------------------------------- 2 AGENDA
s = content_slide(prs, "MISSION SELECT  //  20 MINUTES", "CHOOSE A CHAPTER", icon="game", page=2)
agenda = [
    ("01", "THE PROBLEM", "News is competing with games. Right now, games are winning.", RED, "alert"),
    ("02", "THE GAME", "A browser detective mystery built from today's news.", GOLD_DARK, "game"),
    ("03", "THE PIPELINE", "Crawl, clean, label, train, rank, rewrite, inject.", NAVY, "model"),
    ("04", "THE RESULTS", "Model comparison, limits, and what we learned.", GREEN_DARK, "chart"),
]
y = 1.82
for num, title, desc, accent, icon in agenda:
    rect(s, 0.78, y, 11.78, 1.08, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    rect(s, 0.78, y, 1.0, 1.08, fill=accent, line=INK, line_w=2)
    text_box(s, num, 0.78, y + 0.28, 1.0, 0.45, font=PRESS, size=22, color=CREAM, align=PP_ALIGN.CENTER)
    text_box(s, title, 1.95, y + 0.14, 5.0, 0.3, font=PRESS, size=14, color=INK)
    text_box(s, desc, 1.95, y + 0.53, 7.7, 0.4, font=BODY, size=19, color=INK_SOFT)
    s.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"), Inches(11.85), Inches(y + 0.28),
                         width=Inches(0.5), height=Inches(0.5))
    y += 1.22
text_box(s, "4 CHAPTERS  //  1 PLAYABLE CASE  //  ZERO WORKSHEETS", 0.8, 6.64, 11.7, 0.22,
         font=BODY, size=12, color=MUTED, align=PP_ALIGN.CENTER)
notes(s, "Timing 1:00-1:30. Four chapters. Problem, game, pipeline, results. The presentation is 20 minutes, so point at the chapter list rather than reading it. Mention that all group members will speak.")

# ---------------------------------------------------------------- 3 SECTION 01
s = section_slide(prs, "01", "THE PROBLEM", "News is competing with games.\nRight now, games are winning.", 3)
notes(s, "Timing 1:30-2:00. Chapter break. Move from the product idea to the education problem. The next two slides give the motivation and the design response.")

# ---------------------------------------------------------------- 4 PROBLEM
s = content_slide(prs, "CHAPTER 01 // THE PROBLEM", "NEWS FEELS LIKE HOMEWORK", icon="alert", page=4)
stat_card(s, 0.78, 1.8, 5.72, 2.15, "78%", "of kids find traditional news boring", fill=INK,
          big_color=GOLD, sub="(MEDIA TECHNOLOGY MONITOR, 2024)")
stat_card(s, 6.82, 1.8, 5.72, 2.15, "27%", "of kids read news during a month in Canada", fill=RED,
          big_color=CREAM, sub="(MEDIA TECHNOLOGY MONITOR, 2024)")
issues = [
    ("COMPLEX VOCABULARY", "Long sentences and unfamiliar words block the story.", "book"),
    ("LOW MOTIVATION", "Reading feels like a task, not something you choose.", "alert"),
    ("INFORMATION OVERLOAD", "Too many stories, too little signal about what matters.", "chart"),
]
x = 0.78
for title, body, icon in issues:
    note_card(s, x, 4.25, 3.79, 1.95, title, body, accent=NAVY, icon=icon, title_size=8.5, body_size=17)
    x += 3.99
text_box(s, "Source: MtM News Alert 09-05-2024 — https://mtm-otm.ca/_files/NewsAlert/09-05-2024.pdf",
         0.8, 6.45, 11.7, 0.24, font=BODY, size=12, color=MUTED)
notes(s, "Timing 2:00-4:00. Two numbers set up the problem: 78% find news boring; only 27% read news in a month in Canada. Then name the three barriers: vocabulary, motivation, overload. Emphasise that the issue is not a lack of news, but a lack of an engaging entry point.")

# ---------------------------------------------------------------- 5 ANSWER
s = content_slide(prs, "CHAPTER 01 // OUR ANSWER", "WHAT IF THE NEWS WAS THE GAME?", icon="game", page=5)
goals = [
    ("READ MORE NEWS", "A daily reason to open a real story.", "news", RED),
    ("BUILD INTEREST", "Curiosity first; comprehension follows.", "target", GOLD_DARK),
    ("TRAIN CRITICAL THINKING", "Weigh evidence, then explain the death.", "clue", GREEN_DARK),
]
y = 1.85
for title, body, icon, accent in goals:
    rect(s, 0.78, y, 5.95, 1.28, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    rect(s, 0.78, y, 1.05, 1.28, fill=accent, line=INK, line_w=2)
    s.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"), Inches(1.0), Inches(y + 0.31),
                         width=Inches(0.6), height=Inches(0.6))
    text_box(s, title, 2.02, y + 0.19, 4.5, 0.28, font=PRESS, size=11, color=INK)
    text_box(s, body, 2.02, y + 0.6, 4.5, 0.4, font=BODY, size=19, color=INK_SOFT)
    y += 1.45
text_box(s, "THE TRANSFORMATION", 7.3, 1.84, 5.2, 0.25, font=PRESS, size=9, color=MUTED)
flow = [
    ("TODAY'S NEWS", "A real BBC story", "news", NAVY),
    ("MODEL RANKS", "Key sentences survive", "model", GOLD_DARK),
    ("5 CLUES", "Rewritten for the case", "clue", RED),
    ("PIXEL ISLE", "A mystery to solve", "game", GREEN_DARK),
]
y = 2.22
for i, (title, sub, icon, accent) in enumerate(flow):
    rect(s, 7.35, y, 5.15, 0.78, fill=CREAM_LIGHT, line=INK, line_w=2.2, shadow=True)
    rect(s, 7.35, y, 0.72, 0.78, fill=accent, line=INK, line_w=1.8)
    s.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"), Inches(7.47), Inches(y + 0.13),
                         width=Inches(0.48), height=Inches(0.48))
    text_box(s, title, 8.2, y + 0.09, 4.1, 0.24, font=PRESS, size=9, color=INK)
    text_box(s, sub, 8.2, y + 0.37, 4.1, 0.3, font=BODY, size=16, color=INK_SOFT)
    if i < 3:
        rect(s, 9.82, y + 0.81, 0.22, 0.17, fill=RED, line=None, shape=MSO_SHAPE.DOWN_ARROW)
    y += 1.06
notes(s, "Timing 4:00-5:00. The design response is not a news app with a quiz. It is a detective game where the news supplies the clues. Point to the four-step transformation on the right. The goals on the left map directly to the problem slide.")

# ---------------------------------------------------------------- 6 SECTION 02
s = section_slide(prs, "02", "THE GAME", "A murder mystery you can play\nin a browser.", 6)
notes(s, "Timing 5:00-5:20. Chapter break. This is the product demo section: what the player actually sees and does.")

# ---------------------------------------------------------------- 7 GAME DEMO
s = content_slide(prs, "CHAPTER 02 // THE GAME", "INSPECT. COLLECT. ACCUSE.", icon="game", page=7)
img_w, img_h = 8.6, 8.6 / 1.754
img_x, img_y = 0.78, 1.64
rect(s, img_x + 0.08, img_y + 0.08, img_w, img_h, fill=INK, line=None)
s.shapes.add_picture(os.path.join(ASSETS, "game.png"), Inches(img_x), Inches(img_y),
                     width=Inches(img_w), height=Inches(img_h))
rect(s, img_x, img_y, img_w, img_h, fill=None, line=INK, line_w=4)
for px, py in [(img_x, img_y), (img_x + img_w - 0.12, img_y), (img_x, img_y + img_h - 0.12),
               (img_x + img_w - 0.12, img_y + img_h - 0.12)]:
    rect(s, px + 0.03, py + 0.03, 0.12, 0.12, fill=GOLD, line=INK, line_w=1)
text_box(s, "HOME ROOM — the scene where the case begins.", img_x, img_y + img_h + 0.06, img_w, 0.24,
         font=BODY, size=14, color=MUTED)
controls = [("WASD", "MOVE"), ("E", "INSPECT"), ("1-4", "ANSWER")]
y = 1.84
for key, lab in controls:
    rect(s, 9.62, y, 2.9, 0.62, fill=CREAM_LIGHT, line=INK, line_w=2.2, shadow=True)
    rect(s, 9.62, y, 0.95, 0.62, fill=INK, line=INK, line_w=2)
    text_box(s, key, 9.62, y + 0.18, 0.95, 0.26, font=PRESS, size=10, color=GOLD, align=PP_ALIGN.CENTER)
    text_box(s, lab, 10.72, y + 0.17, 1.65, 0.28, font=PRESS, size=10, color=INK)
    y += 0.76
note_card(s, 9.62, 4.18, 2.9, 2.3, "THE CASE", "Papers = the day's article.\n5 objects = 5 MCQs.\nFinale = explain the death.\nScore = answers + keywords.", accent=RED,
          title_size=9, body_size=17)
text_box(s, "LIVE DEMO  >>", 9.62, 6.52, 2.9, 0.24, font=PRESS, size=8, color=RED, align=PP_ALIGN.RIGHT)
notes(s, "Timing 5:20-8:00. This is the live demo slide. If the browser is available, switch to index.html -> Play for 60-90 seconds: walk to an object, press E, show a clue, press 1-4. If not, narrate the screenshot. Emphasise that the content is generated from a real news story, not hand-written fiction.")

# ---------------------------------------------------------------- 8 SECTION 03
s = section_slide(prs, "03", "THE PIPELINE", "Real news in.\nPlayable clues out.", 8)
notes(s, "Timing 8:00-8:20. Chapter break. The next four slides are the technical core: pipeline, dataset, preprocessing, model, and evaluation.")

# ---------------------------------------------------------------- 9 PIPELINE
s = content_slide(prs, "CHAPTER 03 // SYSTEM", "FROM RSS TO MURDER SCENE", icon="gear", page=9)
steps = [
    ("01", "COLLECT", "30+ RSS feeds", "news", RED),
    ("02", "CLEAN + SPLIT", "articles -> sentences", "gear", GOLD_DARK),
    ("03", "LABEL", "0 filler / 1 key / 2 evidence", "target", NAVY),
    ("04", "TRAIN", "TF-IDF + Logistic Regression", "model", GREEN_DARK),
    ("05", "RANK", "P(key) for every sentence", "chart", RED),
    ("06", "REWRITE", "top sentences -> clues", "book", GOLD_DARK),
    ("07", "INJECT", "clues -> case_data.js", "gear", NAVY),
    ("08", "PLAY", "inspect, answer, score", "game", GREEN_DARK),
]
bw, bh = 2.68, 1.62
x0, y0 = 0.88, 1.8
for i, (num, title, sub, icon, accent) in enumerate(steps):
    col = i % 4
    row = i // 4
    x = x0 + col * (bw + 0.33)
    y = y0 + row * 2.05
    rect(s, x, y, bw, bh, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    rect(s, x, y, 0.46, 0.34, fill=accent, line=INK, line_w=1.5)
    text_box(s, num, x, y + 0.08, 0.46, 0.2, font=PRESS, size=8, color=CREAM, align=PP_ALIGN.CENTER)
    s.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"), Inches(x + bw - 0.58), Inches(y + 0.14),
                         width=Inches(0.4), height=Inches(0.4))
    text_box(s, title, x + 0.14, y + 0.56, bw - 0.28, 0.3, font=PRESS, size=9, color=INK)
    text_box(s, sub, x + 0.14, y + 0.92, bw - 0.28, 0.6, font=BODY, size=16, color=INK_SOFT, spacing=0.82)
    if col < 3:
        rect(s, x + bw + 0.055, y + 0.7, 0.22, 0.2, fill=RED, line=None, shape=MSO_SHAPE.RIGHT_ARROW)
rect(s, 0.88, 5.82, 11.62, 0.7, fill=INK, line=None, shadow=True)
text_box(s, "THE MODEL DECIDES WHAT MATTERS. THE GAME MAKES IT MATTER TO THE PLAYER.",
         0.88, 6.03, 11.62, 0.3, font=PRESS, size=10, color=GOLD, align=PP_ALIGN.CENTER)
notes(s, "Timing 8:20-10:00. Walk the pipeline left to right, then top to bottom. The key split is step 4: the model ranks sentences. Step 6 is the last mile: raw news sentences are rewritten into clues that fit the murder-mystery fiction. This is the part most ML projects stop before.")

# ---------------------------------------------------------------- 10 DATASET
s = content_slide(prs, "CHAPTER 03 // DATA", "THE CASE FILE: 67,647 SENTENCES", icon="news", page=10)
stats = [
    ("67,647", "labelled sentences"),
    ("1,322", "news articles"),
    ("9", "news categories"),
    ("30+", "RSS feeds"),
]
pos = [(0.78, 1.82), (3.54, 1.82), (0.78, 3.5), (3.54, 3.5)]
for (big, lab), (x, y) in zip(stats, pos):
    rect(s, x, y, 2.55, 1.48, fill=CREAM_LIGHT, line=INK, line_w=2.2, shadow=True)
    bs = fit_pixel(big, 2.1, sizes=(32, 28, 24, 20, 18))
    text_box(s, big, x + 0.15, y + 0.19, 2.25, 0.55, font=PRESS, size=bs, color=RED)
    text_box(s, lab, x + 0.15, y + 0.88, 2.25, 0.4, font=BODY, size=17, color=INK_SOFT)
chart_image(s, 6.55, 1.82, 6.02, 4.25, "label_distribution.png",
            caption="Source: data_full.csv -> sentence_label value_counts()")
text_box(s, "Dataset: today's news from BBC, CNN, The Guardian and 30+ public RSS feeds.",
         0.8, 5.88, 5.55, 0.55, font=BODY, size=15, color=INK_SOFT)
text_box(s, "Article-level split: 80% train / 10% validation / 10% test.",
         0.8, 6.47, 5.55, 0.3, font=BODY, size=13, color=MUTED)
notes(s, "Timing 10:00-11:30. Size matters here: 67,647 sentences from 1,322 articles across 9 categories. The right side is intentionally a chart placeholder: insert the class distribution before the final presentation, because imbalance is a key discussion point. Mention that the split is article-level, so the same article never appears in train and test.")

# ---------------------------------------------------------------- 11 PREPROCESSING
s = content_slide(prs, "CHAPTER 03 // DATA", "CLEAN TEXT IN, USEFUL SIGNALS OUT", icon="gear", page=11)
rect(s, 0.78, 1.8, 5.68, 0.46, fill=RED, line=INK, line_w=1.8)
text_box(s, "CLEANING", 0.92, 1.9, 5.3, 0.24, font=PRESS, size=10, color=CREAM)
bullets(s, 0.9, 2.46, 5.4, 3.2, [
    "Strip HTML tags and unescape entities",
    "Normalize whitespace; trim excessive ellipses",
    "Drop articles <50 chars, sentences <15",
    "Split sentences with abbreviation awareness",
    "Deduplicate articles by content hash",
], size=20, gap=8)
rect(s, 6.82, 1.8, 5.68, 0.46, fill=GREEN_DARK, line=INK, line_w=1.8)
text_box(s, "FEATURES + SPLIT", 6.96, 1.9, 5.3, 0.24, font=PRESS, size=10, color=CREAM)
bullets(s, 6.94, 2.46, 5.4, 3.2, [
    "TF-IDF unigrams + bigrams",
    "min_df=2, sublinear_tf=True",
    "Sentence position + neighbouring sentences",
    "Article-level 80 / 10 / 10 split",
    "class_weight='balanced' for imbalance",
], size=20, gap=8, bullet_color=GREEN_DARK)
rect(s, 0.78, 4.98, 11.72, 0.6, fill=CREAM_LIGHT, line=RED, line_w=2, dash=MSO_LINE.DASH)
text_box(s, "WHY IT MATTERS: cleaner sentences mean less TF-IDF noise and a clearer key-sentence signal.",
         0.98, 5.12, 11.3, 0.3, font=BODY, size=18, color=RED)
rect(s, 0.78, 5.72, 11.72, 0.78, fill=INK, line=None, shadow=True)
text_box(s, "> raw HTML  ->  clean sentence  ->  TF-IDF vector  ->  label 0 / 1 / 2",
         0.98, 5.95, 11.3, 0.3, font=BODY, size=20, color=GREEN)
text_box(s, "[OK] 1,322 articles became 67,647 labelled sentences.", 0.98, 6.18, 11.3, 0.22,
         font=BODY, size=14, color=CREAM_DARK)
notes(s, "Timing 11:30-12:30. Two columns: cleaning on the left, representation and split on the right. Do not read every bullet. Highlight three: abbreviation-aware splitting, neighbour context, article-level split. The terminal strip summarises the transformation.")

# ---------------------------------------------------------------- 12 METHOD
s = content_slide(prs, "CHAPTER 03 // MODEL", "THREE LABELS, ONE QUESTION", icon="target", page=12)
text_box(s, "WHICH SENTENCE CARRIES THE STORY?", 0.8, 1.72, 11.2, 0.3, font=PRESS, size=12, color=RED)
classes = [
    ("0", "FILLER", "Stylistic, transitional, optional. Cut it and the story still stands.", MUTED),
    ("1", "KEY", "Main topic, central events, core facts. This is the story.", GOLD_DARK),
    ("2", "EVIDENCE", "Secondary but useful context: quotes, numbers, background.", RED),
]
x = 0.78
for num, name, desc, accent in classes:
    rect(s, x, 2.2, 3.78, 2.08, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    rect(s, x, 2.2, 0.95, 2.08, fill=accent, line=INK, line_w=2)
    text_box(s, num, x, 2.68, 0.95, 0.7, font=PRESS, size=36, color=CREAM, align=PP_ALIGN.CENTER)
    text_box(s, name, x + 1.12, 2.38, 2.5, 0.28, font=PRESS, size=11, color=INK)
    text_box(s, desc, x + 1.12, 2.78, 2.48, 1.2, font=BODY, size=17, color=INK_SOFT, spacing=0.86)
    x += 3.97
rect(s, 0.78, 4.52, 11.72, 2.0, fill=INK, line=GOLD, line_w=2.4, shadow=True)
text_box(s, "PRIMARY MODEL: TF-IDF + LOGISTIC REGRESSION", 1.0, 4.7, 11.2, 0.3, font=PRESS, size=12, color=GOLD)
specs = [
    ("VECTORIZER", "unigrams + bigrams\nmin_df=2, sublinear_tf"),
    ("CLASSIFIER", "LogisticRegression\nbalanced, max_iter=2000"),
    ("TARGET", "rank sentences by P(key)\nfor clue selection"),
]
for i, (k, v) in enumerate(specs):
    bx = 1.0 + i * 3.82
    text_box(s, k, bx, 5.15, 3.3, 0.22, font=PRESS, size=8, color=GREEN)
    text_box(s, v, bx, 5.47, 3.4, 0.72, font=BODY, size=17, color=CREAM, spacing=0.84)
notes(s, "Timing 12:30-13:30. The task is a three-class sentence classification problem. Label 1 is the one that matters most for clue selection. The primary model is deliberately classical: TF-IDF with unigrams and bigrams plus class-weighted logistic regression. It is fast, interpretable, and a strong baseline for sparse text.")

# ---------------------------------------------------------------- 13 WHY
s = content_slide(prs, "CHAPTER 03 // MODEL", "WHY TF-IDF + LOGISTIC REGRESSION", icon="check", page=13)
reasons = [
    "Strong, well-established baseline for text classification",
    "Handles high-dimensional sparse data efficiently",
    "Class weights address filler / key / evidence imbalance",
    "Coefficients show which words drive each class",
    "Fast to train, easy to reproduce on CPU",
]
y = 1.84
for r in reasons:
    rect(s, 0.78, y, 6.75, 0.74, fill=CREAM_LIGHT, line=INK, line_w=2, shadow=True)
    s.shapes.add_picture(os.path.join(ASSETS, "icons", "check.png"), Inches(0.94), Inches(y + 0.19),
                         width=Inches(0.36), height=Inches(0.36))
    text_box(s, r, 1.45, y + 0.16, 5.9, 0.42, font=BODY, size=19, color=INK_SOFT)
    y += 0.85
rect(s, 7.82, 1.84, 4.68, 4.36, fill=INK, line=INK, line_w=3, shadow=True)
text_box(s, "MODEL CARD", 8.02, 2.02, 4.2, 0.28, font=PRESS, size=11, color=GOLD)
line_h(s, 8.02, 2.4, 4.25, color=GOLD, weight=2)
card_lines = [
    ("FEATURES", "TF-IDF, 1-2 grams"),
    ("MIN_DF", "2"),
    ("SUBLINEAR_TF", "True"),
    ("CLASS_WEIGHT", "balanced"),
    ("MAX_ITER", "2000"),
    ("BASELINE", "classical, no deep learning"),
]
y = 2.55
for k, v in card_lines:
    text_box(s, k, 8.02, y, 1.85, 0.24, font=PRESS, size=7, color=GREEN)
    text_box(s, v, 9.82, y - 0.02, 2.45, 0.26, font=BODY, size=16, color=CREAM)
    y += 0.52
text_box(s, "ALSO COMPARED", 0.8, 6.2, 2.5, 0.22, font=PRESS, size=8, color=MUTED)
for i, lab in enumerate(["LINEAR SVM", "MULTINOMIAL NB", "RANDOM FOREST"]):
    rect(s, 2.65 + i * 1.7, 6.14, 1.55, 0.32, fill=CREAM_LIGHT, line=INK, line_w=1.8)
    text_box(s, lab, 2.65 + i * 1.7, 6.2, 1.55, 0.2, font=PRESS, size=7, color=INK, align=PP_ALIGN.CENTER)
notes(s, "Timing 13:30-14:30. Justify the model in five points. The two strongest for this project are class weighting and interpretability. The model card lists the exact settings so the audience can trust the reproducibility. Mention that Linear SVM, Multinomial NB, and Random Forest were considered as classical comparisons.")

# ---------------------------------------------------------------- 14 SPLIT
s = content_slide(prs, "CHAPTER 03 // EVALUATION", "A FAIR FIGHT: SAME SPLIT, SAME METRICS", icon="target", page=14)
segs = [("TRAIN", "80%", 0.78, 9.38, GOLD), ("VAL", "10%", 10.16, 1.17, GREEN), ("TEST", "10%", 11.33, 1.17, RED)]
for name, pct, x, w, col in segs:
    rect(s, x, 1.82, w, 0.7, fill=col, line=INK, line_w=2.4)
    text_box(s, f"{name}  {pct}", x, 2.02, w, 0.26, font=PRESS, size=9, color=CREAM if col != GOLD else INK,
             align=PP_ALIGN.CENTER)
text_box(s, "ARTICLE-LEVEL SPLIT — no sentence from one article appears in two sets.", 0.78, 2.62, 11.7, 0.26,
         font=BODY, size=16, color=MUTED, align=PP_ALIGN.CENTER)
roles = [
    ("TRAIN", "Learn model parameters.", GOLD_DARK, "book"),
    ("VALIDATION", "Check performance during development.", GREEN_DARK, "target"),
    ("TEST", "Report final performance once.", RED, "chart"),
]
x = 0.78
for name, desc, accent, icon in roles:
    rect(s, x, 3.02, 3.79, 1.5, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    rect(s, x, 3.02, 3.79, 0.36, fill=accent, line=INK, line_w=1.6)
    text_box(s, name, x + 0.14, 3.11, 3.2, 0.24, font=PRESS, size=9, color=CREAM)
    s.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"), Inches(x + 3.28), Inches(3.03),
                         width=Inches(0.32), height=Inches(0.32))
    text_box(s, desc, x + 0.16, 3.55, 3.45, 0.7, font=BODY, size=18, color=INK_SOFT)
    x += 3.97
text_box(s, "SAME METRICS FOR EVERY MODEL", 0.8, 4.78, 5.0, 0.24, font=PRESS, size=8, color=MUTED)
for i, lab in enumerate(["MACRO-F1", "KEY-F1", "TOP-3", "TRAIN TIME"]):
    rect(s, 0.78 + i * 2.2, 5.12, 2.0, 0.55, fill=INK, line=None, shadow=True)
    text_box(s, lab, 0.78 + i * 2.2, 5.26, 2.0, 0.24, font=PRESS, size=8, color=GOLD, align=PP_ALIGN.CENTER)
rect(s, 9.55, 4.95, 2.95, 1.0, fill=CREAM_LIGHT, line=RED, line_w=2, dash=MSO_LINE.DASH)
text_box(s, "ONE SEED\nSEED = 42", 9.7, 5.16, 2.65, 0.62, font=BODY, size=18, color=RED, align=PP_ALIGN.CENTER, spacing=0.85)
text_box(s, "Hold the split fixed. Report the same metric definitions. Then compare models.",
         0.8, 6.12, 11.7, 0.3, font=BODY, size=16, color=INK_SOFT)
notes(s, "Timing 14:30-15:15. Fair comparison is the message. Every model uses the same article-level split and the same metric definitions. Train learns parameters, validation checks during development, test is reported once. The single seed is a limitation to flag honestly.")

# ---------------------------------------------------------------- 14b ETHICS & DATA
s = content_slide(prs, "CHAPTER 03 // ETHICS & DATA", "REAL NEWS, USED RESPONSIBLY", icon="alert")
bullets(s, 0.9, 1.95, 5.6, 3.9, [
    "One real story per day from public RSS feeds (BBC, CNN, The Guardian).",
    "Content is current, real-world news — not fabricated or fictionalised.",
    "We keep short sentence excerpts, not republished full articles.",
    "Non-commercial, classroom prototype within a university course.",
], size=19, gap=10)
note_card(s, 6.85, 1.95, 5.65, 3.9, "COPYRIGHT & LICENSE",
          "BBC and other outlets are copyrighted, not open-source: RSS is for personal reading. "
          "Using brief excerpts in a non-commercial student prototype is low-risk, but we do not "
          "redistribute full articles or claim ownership. Any public demo uses the shortest necessary "
          "excerpts and credits the source.",
          accent=RED, title_size=9, body_size=16)
rect(s, 0.78, 5.75, 11.72, 0.7, fill=INK, line=None, shadow=True)
text_box(s, "REAL NEWS IS THE INPUT — USED IN GOOD FAITH FOR EDUCATION.", 0.98, 5.95, 11.3, 0.3,
         font=PRESS, size=9, color=GOLD, align=PP_ALIGN.CENTER)
notes(s, "Ethics and data use. The input is real, current news. We keep only short excerpts for a non-commercial educational prototype. Clarify that BBC content is copyrighted, not open-source, so the demo stays non-commercial and credits the source.")

# ---------------------------------------------------------------- 15 SECTION 04
s = section_slide(prs, "04", "THE RESULTS", "The model ranks.\nThe numbers decide.", 15)
notes(s, "Timing 15:15-15:30. Chapter break. Now the evidence. Start with the comparison table, then the training curve and confusion matrix placeholders.")

# ---------------------------------------------------------------- 16 RESULTS TABLE
s = content_slide(prs, "CHAPTER 04 // RESULTS", "MODEL COMPARISON: THE NUMBERS", icon="chart", page=16)
rows, cols = 5, 6
tbl_x, tbl_y, tbl_w = 0.78, 1.76, 11.72
tbl_h = 2.08
gt = s.shapes.add_table(rows, cols, Inches(tbl_x), Inches(tbl_y), Inches(tbl_w), Inches(tbl_h))
table = gt.table
table.first_row = True
table.horz_banding = False
table.columns[0].width = Inches(4.22)
for i in range(1, 6):
    table.columns[i].width = Inches(1.5)
table.rows[0].height = Inches(0.42)
for i in range(1, 5):
    table.rows[i].height = Inches(0.41)
headers = ["METHOD", "MACRO-F1", "KEY-F1", "TOP-3", "TIME", "PARAMS"]
for c, h in enumerate(headers):
    cell_style(table.cell(0, c), h, font=PRESS, size=9, color=GOLD, fill=INK,
               align=PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER)
rows_data = [
    ("TF-IDF + Logistic Regression (baseline)", "0.654", "0.424", "0.457", "<1 min", "0.39M", CREAM_LIGHT, False),
    ("LSTM + self-built vocab", "0.709", "0.543", "0.618", "10 min", "5.2M", CREAM_LIGHT, False),
    ("LSTM + RoBERTa tokenizer", "0.736", "0.552", "0.638", "9 min", "6.7M", CREAM_LIGHT, False),
    (">> DistilRoBERTa (reference)", "0.798", "0.660", "0.706", "26 min", "82.1M", CREAM_DARK, True),
]
for r, (name, a, b, c, d, e, fill, best) in enumerate(rows_data, start=1):
    cell_style(table.cell(r, 0), name, font=BODY, size=17 if r > 1 else 15,
               color=INK if r < 4 else INK, fill=fill, bold=best)
    for j, val in enumerate([a, b, c, d, e], start=1):
        cell_style(table.cell(r, j), val, font=BODY, size=17 if r > 1 else 13,
                   color=RED if val == "TBD" else (GREEN_DARK if best else INK), fill=fill,
                   bold=best, align=PP_ALIGN.CENTER)
chart_image(s, 0.78, 3.98, 11.72, 2.2, "compare_wide.png")
text_box(s, "Primary course model: TF-IDF + LogReg (baseline). Neural rows are reference comparisons (seed 42).",
         0.8, 6.3, 11.7, 0.42, font=BODY, size=12, color=MUTED, spacing=0.85)
notes(s, "Timing 15:30-17:00. The table is the evidence. DistilRoBERTa leads on every reported metric, but at 82.1M parameters and 26 minutes. The two LSTM variants are lighter and faster. The TF-IDF row is intentionally marked ADD: fill it from the final baseline run so the classical model has a fair place in the comparison. The chart placeholder below is for the grouped bar visual.")

# ---------------------------------------------------------------- 17 TRAINING CURVE
s = content_slide(prs, "CHAPTER 04 // RESULTS", "TRAINING CURVE: WHAT TO WATCH", icon="chart", page=17)
chart_placeholder(s, 0.78, 1.8, 7.55, 4.48, "FIG. 03", "LOSS + F1 VS EPOCH",
                  "Insert training / validation loss and validation macro-F1 by epoch.",
                  kind="line")
note_card(s, 8.58, 1.8, 3.92, 4.48, "READ THE CURVE", "", accent=NAVY, title_size=9)
bullets(s, 8.78, 2.42, 3.55, 3.2, [
    "Training loss decreased during the run.",
    "Validation loss fluctuated, especially at epoch 7.",
    "Validation F1 rose overall, but not every epoch.",
    "Lower training loss did not always mean better validation.",
], size=17, gap=7, bullet_color=GOLD_DARK)
rect(s, 8.78, 5.3, 3.52, 0.7, fill=INK, line=None)
text_box(s, "VALIDATION >\nTRAINING LOSS", 8.78, 5.43, 3.52, 0.46, font=PRESS, size=8, color=GOLD,
         align=PP_ALIGN.CENTER, spacing=1.15)
text_box(s, "Insert the exported training log or notebook chart.", 0.8, 6.4, 7.5, 0.26, font=BODY, size=13, color=MUTED)
notes(s, "Timing 17:00-17:45. The training curve is a placeholder: insert the real loss and macro-F1 curves. The talking point is already on the right: validation fluctuated, especially around epoch 7, and lower training loss is not automatically better. This is a good place to mention early stopping / best-checkpoint selection.")

# ---------------------------------------------------------------- 18 ERROR ANALYSIS
s = content_slide(prs, "CHAPTER 04 // RESULTS", "WHERE THE MODEL STILL STRUGGLES", icon="alert", page=18)
chart_image(s, 0.78, 1.8, 5.85, 4.48, "confusion_matrix.png",
            caption="Test-set matrix — TF-IDF + Logistic Regression")
note_card(s, 6.95, 1.8, 5.55, 4.48, "ERROR ANALYSIS", "", accent=RED, title_size=9)
bullets(s, 7.15, 2.42, 5.15, 3.0, [
    ("Evidence is hardest. ", "It overlaps with key sentences and has fewer clear cues."),
    ("Labels are noisy. ", "DeepSeek-assisted labels can be wrong, so scores absorb label error."),
    ("Class imbalance. ", "Filler dominates; balanced weights help, but do not erase the problem."),
    ("Next step. ", "Inspect top false positives and false negatives, then refine the label guide."),
], size=17, gap=7)
rect(s, 7.15, 5.36, 5.15, 0.66, fill=INK, line=None)
text_box(s, "LABEL NOISE = SCORE NOISE", 7.15, 5.55, 5.15, 0.26, font=PRESS, size=9, color=GOLD,
         align=PP_ALIGN.CENTER)
notes(s, "Timing 17:45-18:30. The matrix is a placeholder, but the failure modes are known. Evidence is the hardest class because it overlaps with key. Labels were LLM-assisted, so label noise is a real limitation. Class imbalance is handled with weights, not solved. End with the next step: inspect concrete errors.")

# ---------------------------------------------------------------- 19 WHAT RESULTS SHOW
s = content_slide(prs, "CHAPTER 04 // RESULTS", "WHAT THE RESULTS SHOW", icon="target", page=19)
cards = [
    ("BEST REPORTED", "DistilRoBERTa: 0.798 macro-F1 and 0.660 key-F1.", GREEN_DARK, "check"),
    ("BIGGER MODEL", "82.1M parameters vs 5.2M / 6.7M for the LSTM runs.", GOLD_DARK, "model"),
    ("NOISY LABELS", "DeepSeek-assisted labels may contain errors that move scores.", RED, "alert"),
    ("ONE SEED", "Single seed; measures sentence classification, not learning gains.", NAVY, "target"),
]
pos = [(0.78, 1.82), (6.82, 1.82), (0.78, 3.62), (6.82, 3.62)]
for (title, body, accent, icon), (x, y) in zip(cards, pos):
    note_card(s, x, y, 5.72, 1.7, title, body, accent=accent, icon=icon, title_size=9, body_size=20)
rect(s, 0.78, 5.55, 11.72, 0.62, fill=INK, line=GOLD, line_w=2, shadow=True)
text_box(s, "USEFUL FOR RANKING KEY SENTENCES. NOT A SUBSTITUTE FOR TEACHER JUDGEMENT.",
         0.98, 5.73, 11.3, 0.28, font=PRESS, size=9, color=GOLD, align=PP_ALIGN.CENTER)
notes(s, "Timing 18:30-19:00. Four honest takeaways. The best number belongs to a larger reference model. Labels are noisy. One seed is not a stability study. And most importantly: this measures sentence classification, not whether students learn better. That caveat protects the conclusion.")

# ---------------------------------------------------------------- 20 IMPLICATIONS
s = content_slide(prs, "CHAPTER 04 // IMPLICATIONS", "SO WHAT? PROBLEM -> RESULT", icon="game", page=20)
steps = [
    ("01", "EXTRACT", "The game pulls key sentences from a real BBC story.", "news"),
    ("02", "CLASSIFY", "The model ranks importance: filler, key, evidence.", "model"),
    ("03", "UNDERSTAND", "Kids meet the story one clue at a time.", "book"),
    ("04", "WANT MORE", "Current affairs becomes something to play.", "game"),
]
x = 0.78
for num, title, body, icon in steps:
    rect(s, x, 1.95, 2.76, 2.55, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    text_box(s, num, x + 0.16, 2.08, 0.6, 0.32, font=PRESS, size=16, color=RED)
    s.shapes.add_picture(os.path.join(ASSETS, "icons", icon + ".png"), Inches(x + 2.18), Inches(2.02),
                         width=Inches(0.42), height=Inches(0.42))
    text_box(s, title, x + 0.16, 2.58, 2.45, 0.3, font=PRESS, size=10, color=INK)
    text_box(s, body, x + 0.16, 3.0, 2.42, 1.3, font=BODY, size=17, color=INK_SOFT, spacing=0.86)
    if num != "04":
        rect(s, x + 2.8, 3.15, 0.2, 0.2, fill=RED, line=None, shape=MSO_SHAPE.RIGHT_ARROW)
    x += 3.02
rect(s, 0.78, 4.82, 5.72, 1.55, fill=RED, line=INK, line_w=2.4, shadow=True)
text_box(s, "THE PROBLEM", 0.98, 4.98, 5.2, 0.24, font=PRESS, size=8, color=CREAM)
text_box(s, "Bored by news.  Rarely reads it.", 0.98, 5.36, 5.2, 0.7, font=BODY, size=24, color=CREAM, spacing=0.86)
rect(s, 6.82, 4.82, 5.68, 1.55, fill=GREEN_DARK, line=INK, line_w=2.4, shadow=True)
text_box(s, "THE SHIFT", 7.02, 4.98, 5.2, 0.24, font=PRESS, size=8, color=CREAM)
text_box(s, "Curious.  Plays the story daily.", 7.02, 5.36, 5.2, 0.7, font=BODY, size=24, color=CREAM, spacing=0.86)
text_box(s, "FROM 'I DON'T READ THE NEWS' TO 'I SOLVED TODAY'S CASE.'", 0.8, 6.47, 11.7, 0.28,
         font=PRESS, size=9, color=INK, align=PP_ALIGN.CENTER)
notes(s, "Timing 19:00-19:30. Tie the pipeline back to the problem. The model extracts and ranks; the game turns that ranking into pacing and participation. The final line is the intended shift: from avoiding news to choosing to solve it. Do not overclaim learning gains; this is engagement and comprehension support.")

# ---------------------------------------------------------------- 21 CHALLENGES
s = content_slide(prs, "CHAPTER 04 // REFLECTION", "CHALLENGES FACED", icon="alert", page=21)
challenges = [
    ("1", "LARGE-SCALE LABELLING", "67,647 sentences. 'Important' is hard to define. LLM-assisted labels brought noise and imbalance.", RED),
    ("2", "COURSE VS PERFORMANCE", "The course focuses on classical ML. The best scores came from DistilRoBERTa, so lighter models were also trained for a fair comparison.", GOLD_DARK),
    ("3", "MODEL OUTPUT -> CLUES", "Raw news sentences do not fit a murder mystery. A rewrite step is needed; early clues broke immersion.", NAVY),
    ("4", "ENGINEERING + REPRO", "Crawler, labelling, training, Streamlit and the game had to work together. RSS changes broke the pipeline.", GREEN_DARK),
]
pos = [(0.78, 1.82), (6.82, 1.82), (0.78, 3.95), (6.82, 3.95)]
for (num, title, body, accent), (x, y) in zip(challenges, pos):
    rect(s, x, y, 5.72, 1.9, fill=CREAM_LIGHT, line=INK, line_w=2.4, shadow=True)
    rect(s, x, y, 0.62, 1.9, fill=accent, line=INK, line_w=2)
    text_box(s, num, x, y + 0.66, 0.62, 0.5, font=PRESS, size=24, color=CREAM, align=PP_ALIGN.CENTER)
    text_box(s, title, x + 0.82, y + 0.18, 4.65, 0.3, font=PRESS, size=9.5, color=INK)
    text_box(s, body, x + 0.82, y + 0.6, 4.62, 1.15, font=BODY, size=17, color=INK_SOFT, spacing=0.85)
text_box(s, "EVERY CHALLENGE CHANGED THE PIPELINE, NOT JUST THE MODEL.", 0.8, 6.25, 11.7, 0.28,
         font=PRESS, size=9, color=RED, align=PP_ALIGN.CENTER)
notes(s, "Timing 19:30-20:00. Four challenges, one sentence each. The big one is labelling: 67k sentences from 1,322 articles, with a subjective definition of important. The second is the classical-ML restriction versus stronger reference models. The third is the last mile, and the fourth is reproducibility across five moving parts.")

# ---------------------------------------------------------------- 22 LEARNINGS
s = content_slide(prs, "CHAPTER 04 // REFLECTION", "WHAT THE TEAM LEARNED", icon="book", page=22)
learn = [
    "Pipeline quality beats any single model.",
    "Report both stronger and lighter models.",
    "NLP output must be adapted to the target domain.",
    "Fixed seed + identical splits = fair comparison.",
    "Clear interfaces prevent integration pain.",
    "The last mile is hardest: predictions -> usable clues.",
]
pos = [(0.78, 1.82), (6.82, 1.82), (0.78, 3.03), (6.82, 3.03), (0.78, 4.24), (6.82, 4.24)]
for i, ((x, y), item) in enumerate(zip(pos, learn)):
    rect(s, x, y, 5.72, 0.98, fill=CREAM_LIGHT, line=INK, line_w=2.2, shadow=True)
    rect(s, x, y, 0.62, 0.98, fill=INK, line=None)
    text_box(s, f"{i+1}", x, y + 0.27, 0.62, 0.36, font=PRESS, size=15, color=GOLD, align=PP_ALIGN.CENTER)
    text_box(s, item, x + 0.82, y + 0.23, 4.65, 0.55, font=BODY, size=19, color=INK_SOFT)
rect(s, 0.78, 5.55, 11.72, 0.62, fill=INK, line=GOLD, line_w=2, shadow=True)
text_box(s, "SHIP THE WHOLE PIPELINE, NOT JUST THE MODEL.", 0.98, 5.73, 11.3, 0.28,
         font=PRESS, size=9, color=GOLD, align=PP_ALIGN.CENTER)
notes(s, "Timing 20:00-20:30 if time allows. The six learnings are intentionally short. The final line is the thesis: an education AI system succeeds or fails on the whole pipeline, especially the last mile from prediction to something a learner can use.")

# ---------------------------------------------------------------- 22b LIMITATIONS & FUTURE
s = content_slide(prs, "CHAPTER 04 // REFLECTION", "LIMITATIONS & NEXT STEPS", icon="target")
rect(s, 0.78, 1.82, 5.55, 0.4, fill=RED, line=INK, line_w=1.8)
text_box(s, "LIMITATIONS (HONEST)", 0.92, 1.92, 5.2, 0.22, font=PRESS, size=9, color=CREAM)
bullets(s, 0.9, 2.38, 5.3, 3.0, [
    "Single seed (42) — no stability study yet.",
    "LLM-assisted labels introduce noise.",
    "Scores measure sentence importance, not learning gains.",
], size=18, gap=9)
rect(s, 6.85, 1.82, 5.65, 0.4, fill=GREEN_DARK, line=INK, line_w=1.8)
text_box(s, "FUTURE WORK", 6.99, 1.92, 5.2, 0.22, font=PRESS, size=9, color=CREAM)
bullets(s, 6.97, 2.38, 5.4, 3.0, [
    "Make the clues more directly related to the story.",
    "Add student history and daily streaks for engagement.",
    "Sharpen the news-to-clue mapping (currently not fully focused).",
], size=18, gap=9, bullet_color=GREEN_DARK)
rect(s, 0.78, 5.6, 11.72, 0.66, fill=INK, line=GOLD, line_w=2, shadow=True)
text_box(s, "NEXT ITERATION: THE NEWS SHOULD BE THE MYSTERY, NOT JUST THE BACKDROP.",
         0.98, 5.8, 11.3, 0.28, font=PRESS, size=9, color=GOLD, align=PP_ALIGN.CENTER)
notes(s, "Limitations and next steps. Honest limits: one seed, noisy labels, and the metric measures sentence importance not learning. Future work: tie clues closer to the story, add streaks/history, and sharpen the news-to-clue mapping.")

# ---------------------------------------------------------------- 22c TEAM & ROLES
s = content_slide(prs, "THE TEAM", "SEVEN ROLES, ONE CASE", icon="game")
roles = [
    ("PROJECT LEAD", "Scope, schedule, integration."),
    ("GAME DEVELOPER", "Pixel game, scenes, mechanics."),
    ("CRAWLER & DATA", "RSS fetch, clean, label, merge."),
    ("ML ENGINEER", "Baseline + neural models, eval."),
    ("FRONTEND / UI", "Editor, HUD, presentation UI."),
    ("QA & TESTING", "Pipeline tests, bug hunting."),
    ("DOCS & PITCH", "Slides, report, live demo."),
]
pos = [(0.78, 1.82), (3.74, 1.82), (6.70, 1.82), (9.66, 1.82),
       (0.78, 3.72), (3.74, 3.72), (6.70, 3.72)]
for i, ((x, y), (t, b)) in enumerate(zip(pos, roles)):
    rect(s, x, y, 2.80, 1.68, fill=CREAM_LIGHT, line=INK, line_w=2.2, shadow=True)
    rect(s, x, y, 0.4, 0.4, fill=GOLD_DARK, line=INK, line_w=1.5)
    text_box(s, f"{i+1}", x, y + 0.1, 0.4, 0.2, font=PRESS, size=8, color=CREAM, align=PP_ALIGN.CENTER)
    text_box(s, t, x + 0.14, y + 0.56, 2.52, 0.28, font=PRESS, size=9, color=INK)
    text_box(s, b, x + 0.14, y + 0.94, 2.52, 0.6, font=BODY, size=15, color=INK_SOFT, spacing=0.85)
text_box(s, "GROUP 2  //  CHIU WAI YIU · LAI CHUN KUI · LAI WAN YAU SONYA · MAK TSUN WAI MARSIO · WONG CHING WAI · WONG SUI KI · WONG TSZ CHING",
         0.8, 5.68, 11.7, 0.55, font=BODY, size=12, color=MUTED, align=PP_ALIGN.CENTER, spacing=0.9)
notes(s, "Team slide. Seven members, seven roles. Assign each name to a role before presenting (all names are listed in the footer line).")

# ---------------------------------------------------------------- 23 CLOSING
s = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(s, "bg_title.png")
rect(s, 0.72, 0.74, 11.9, 5.95, fill=INK, line=None)
s.shapes.add_picture(os.path.join(ASSETS, "panel_paper.png"), Inches(0.64), Inches(0.66),
                     width=Inches(11.9), height=Inches(5.95))
rect(s, 0.64, 0.66, 11.9, 5.95, fill=None, line=INK, line_w=4)
for px, py in [(0.64, 0.66), (12.43, 0.66), (0.64, 6.5), (12.43, 6.5)]:
    rect(s, px + 0.04, py + 0.04, 0.14, 0.14, fill=GOLD, line=INK, line_w=1.2)
clickable_label(s, 0.98, 1.0, 2.2, 0.34, "CASE CLOSED", fill=RED, size=9)
text_box(s, "CASE CLOSED.", 0.96, 1.55, 7.8, 0.85, font=PRESS, size=40, color=INK, shadow=(3, "E3A83B"))
text_box(s, "Today's news becomes tomorrow's mystery.", 0.98, 2.5, 7.6, 0.4, font=BODY, size=24, color=RED)
line_h(s, 0.98, 3.05, 7.4, color=INK, weight=2)
summary = [
    "A real news story becomes a playable case.",
    "A classical baseline ranks what matters.",
    "An honest comparison shows the trade-offs.",
]
y = 3.25
for item in summary:
    s.shapes.add_picture(os.path.join(ASSETS, "icons", "check.png"), Inches(0.98), Inches(y + 0.03),
                         width=Inches(0.34), height=Inches(0.34))
    text_box(s, item, 1.47, y, 6.7, 0.36, font=BODY, size=20, color=INK_SOFT)
    y += 0.55
rect(s, 0.98, 5.22, 3.05, 0.68, fill=RED, line=INK, line_w=3, shadow=True)
text_box(s, "THANK YOU", 0.98, 5.39, 3.05, 0.3, font=PRESS, size=12, color=CREAM, align=PP_ALIGN.CENTER)
text_box(s, "QUESTIONS >>", 4.3, 5.35, 3.0, 0.4, font=PRESS, size=14, color=INK)
text_box(s, "GROUP 2  //  CHIU WAI YIU · LAI CHUN KUI · LAI WAN YAU SONYA · MAK TSUN WAI MARSIO\nWONG CHING WAI · WONG SUI KI · WONG TSZ CHING  //  INT4096 · 2026-27 SEM 1", 0.98, 6.0, 7.2, 0.6, font=BODY, size=11, color=MUTED)
notes(s, "Timing last slide. Close with the three summary lines, then invite questions. If the demo is live, open index.html -> Play after the final line.")

# ---------------------------------------------------------------- 24 REFERENCES
s = content_slide(prs, "REFERENCES", "REFERENCES (APA 7TH)", icon="book")
left = [
    "Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. Neural Computation, 9(8), 1735–1780.",
    "Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., Levy, O., Lewis, M., Zettlemoyer, L., & Stoyanov, V. (2019). RoBERTa: A robustly optimized BERT pretraining approach. arXiv:1907.11692.",
    "Media Technology Monitor. (2024). News Alert, 09-05-2024. https://mtm-otm.ca/",
]
right = [
    "Paszke, A., et al. (2019). PyTorch: An imperative style, high-performance deep learning library. Advances in Neural Information Processing Systems, 32.",
    "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
    "Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter. arXiv:1910.01108.",
    "Wolf, T., et al. (2020). Transformers: State-of-the-art natural language processing. arXiv:1910.03771.",
]
rect(s, 0.78, 1.82, 5.72, 4.4, fill=CREAM_LIGHT, line=INK, line_w=2.2, shadow=True)
text_box(s, "\n\n".join(left), 0.95, 2.0, 5.4, 4.05, font=BODY, size=13, color=INK_SOFT, spacing=1.05)
rect(s, 6.85, 1.82, 5.65, 4.4, fill=CREAM_LIGHT, line=INK, line_w=2.2, shadow=True)
text_box(s, "\n\n".join(right), 7.02, 2.0, 5.3, 4.05, font=BODY, size=13, color=INK_SOFT, spacing=1.05)
notes(s, "References in APA 7 format, citing the statistics source, the models, and the libraries used.")

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides))
