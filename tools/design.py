"""'framed' interior design, in colour or black and white.

book.yaml:
  ink: standard_color        # bw | standard_color | premium_color  (standard colour needs 72+ pages)
  design:
    style: framed            # framed (default) | plain
    icon: bird               # book icon: bird, sprig, or a Material Icons name
    badge: EXTRA LARGE PRINT
    palette: garden          # see PALETTES; each puzzle page takes the next colour
    tracker: true            # "My puzzle tracker" page at the front
    certificate: true        # completion certificate at the end
    bonus_url: ""            # if set: QR code page for free bonus puzzles (email list)
puzzles.yaml (per puzzle, optional): icon, fact ("Did you know?" line; must be checked as true)

Repeat-purchase features: tracker page, series collection page with tick boxes, certificate, bonus QR.
"""
from reportlab.pdfbase import pdfmetrics

from ornaments import draw_icon, draw_pattern, draw_sprig

PALETTES = {
    "garden": [(0.11, 0.53, 0.60), (0.91, 0.40, 0.33), (0.38, 0.62, 0.30), (0.93, 0.63, 0.13), (0.52, 0.36, 0.62)],
    "sport": [(0.10, 0.45, 0.30), (0.85, 0.25, 0.22), (0.16, 0.36, 0.66), (0.93, 0.60, 0.10), (0.35, 0.35, 0.40)],
    "ocean": [(0.05, 0.42, 0.62), (0.10, 0.62, 0.62), (0.95, 0.52, 0.38), (0.33, 0.33, 0.62), (0.92, 0.70, 0.25)],
}
NAVY = (0.11, 0.14, 0.22)        # text
SOFT = (0.42, 0.45, 0.52)        # secondary text
WHITE = (1, 1, 1)
PAD = 16                         # frame to content
FOOT = 34                        # footer height inside the frame


def issue(b, kind, msg):
    """Record a layout problem; build_book writes them to dist/layout.json and check_book fails on any."""
    if not hasattr(b, "layout_issues"):
        b.layout_issues = []
    b.layout_issues.append({"page": b.page, "kind": kind, "msg": msg})


def _rgb(c, col, fill=True):
    (c.setFillColorRGB if fill else c.setStrokeColorRGB)(*col)


def tint(col, amount):
    """amount 0 = white, 1 = full colour."""
    return tuple(1 - (1 - v) * amount for v in col)


def is_color(b):
    return "color" in str(b.cfg.get("ink", "bw"))


def palette(b):
    d = b.cfg.get("design") or {}
    pal = PALETTES.get(d.get("palette", "garden"), PALETTES["garden"])
    if not is_color(b):
        return [(0.25, 0.25, 0.25)]
    return pal


def accent(b, i=0):
    pal = palette(b)
    return pal[i % len(pal)]


def icon_of(b, entry=None):
    d = b.cfg.get("design") or {}
    return (entry or {}).get("icon") or d.get("icon") or "sprig"


def illustrated(b):
    return (b.cfg.get("design") or {}).get("style", "framed") == "illustrated"


def motifs_of(b):
    d = b.cfg.get("design") or {}
    if d.get("motifs"):
        return d["motifs"]
    return ["flying_bird", "feather", "leaf", "dot", "flower"] if d.get("icon") == "bird" else ["leaf", "dot", "star", "flower"]


def darker(col, k=0.72):
    return tuple(v * k for v in col)


def frame(b, col=None):
    """Rounded frame on the content box. Returns the inner area (x, y, w, h) above the footer."""
    x, y, cw, ch = b.box
    c = b.c
    col = col or accent(b, 0)
    if illustrated(b):
        b.page_col = col
        return x + 4, y + 30, cw - 8, ch - 30
    c.saveState()
    _rgb(c, col, fill=False)
    c.setLineWidth(1.6)
    c.roundRect(x, y, cw, ch, 16, stroke=1, fill=0)
    _rgb(c, tint(col, 0.35), fill=False)
    c.setLineWidth(0.6)
    c.roundRect(x + 4, y + 4, cw - 8, ch - 8, 13, stroke=1, fill=0)
    # corner dots
    _rgb(c, col)
    for dx, dy in ((x + 14, y + ch - 14), (x + cw - 14, y + ch - 14), (x + 14, y + 14), (x + cw - 14, y + 14)):
        c.circle(dx, dy, 2.2, stroke=0, fill=1)
    c.restoreState()
    b.page_col = col
    return x + PAD, y + PAD + FOOT, cw - 2 * PAD, ch - 2 * PAD - FOOT


def footer(b):
    x, y, cw, ch = b.box
    c = b.c
    col = getattr(b, "page_col", accent(b, 0))
    mid = x + cw / 2
    fy = y + (8 if illustrated(b) else PAD + 10)
    draw_sprig(c, mid, fy, cw * 0.22, grey=0.7)
    c.saveState()
    _rgb(c, col)
    c.circle(mid, fy, 12, stroke=0, fill=1)
    _rgb(c, WHITE)
    c.setFont("BodyBold", 11)
    c.drawCentredString(mid, fy - 4, str(b.page))
    c.restoreState()


def header(b, ix, top, iw, title, label=None, icon=None, h=58, col=None, stars=None):
    """Coloured band: white badge with number, white title, white icon, optional difficulty stars."""
    c = b.c
    col = col or accent(b, 0)
    if illustrated(b):
        return _tab_header(b, ix, top, iw, title, label, icon, h, col, stars)
    c.saveState()
    _rgb(c, col)
    c.roundRect(ix, top - h, iw, h, 14, stroke=0, fill=1)
    tx = ix + 18
    if label is not None:
        r = 20
        cx, cy = ix + 14 + r, top - h / 2
        _rgb(c, WHITE)
        c.circle(cx, cy, r, stroke=0, fill=1)
        _rgb(c, col)
        fs = 17 if len(str(label)) < 3 else 13
        c.setFont("Display", fs)
        c.drawCentredString(cx, cy - fs * 0.36, str(label))
        tx = cx + r + 14
    _rgb(c, WHITE)
    icon_w = h * 0.62 + 16 if icon else 0
    stars_w = 66 if stars else 0
    right = ix + iw - 18 - icon_w - (stars_w + 10 if stars else 0)  # left edge of whatever sits on the right
    room = right - 28 - tx                                           # keep a clear 28 pt gap before it
    size = 23
    while pdfmetrics.stringWidth(title, "Display", size) > room and size > 16:
        size -= 0.5
    if pdfmetrics.stringWidth(title, "Display", size) > room:
        issue(b, "header", f"title '{title}' does not fit the header even at {size} pt")
    c.setFont("Display", size)
    c.drawString(tx, top - h / 2 - size * 0.36, title)
    c.restoreState()
    if stars:
        sx = ix + iw - 18 - icon_w - stars_w
        for k in range(3):
            draw_icon(c, "star" if k < stars else "star_border", sx + k * 20, top - h / 2 - 9, 18,
                      grey=None, rgb=WHITE)
    if icon:
        s = h * 0.62
        draw_icon(c, icon, ix + iw - s - 16, top - h / 2 - s / 2, s, grey=None, rgb=WHITE)
    return top - h


def _tab_header(b, ix, top, iw, title, label, icon, h, col, stars):
    """'illustrated' style: a pale patterned band with a raised white title tab (like a label stuck
    on the page), the puzzle number in a coloured circle, and the theme icon in a white disc."""
    c = b.c
    band_h = h + 22
    y0 = top - band_h
    c.saveState()
    p = c.beginPath()
    p.roundRect(ix, y0, iw, band_h, 18)
    c.clipPath(p, stroke=0, fill=0)
    _rgb(c, tint(col, 0.13))
    c.rect(ix, y0, iw, band_h, stroke=0, fill=1)
    draw_pattern(c, ix, y0, iw, band_h, tint(col, 0.42), motifs_of(b), seed=f"{b.page}-{title}")
    c.restoreState()

    # right side: icon disc (+ stars to its left)
    disc_r = h * 0.5
    right = ix + iw - 18
    if icon:
        cx, cy = right - disc_r, y0 + band_h / 2
        _rgb(c, darker(col, 0.8))
        c.circle(cx + 2, cy - 3, disc_r, stroke=0, fill=1)
        _rgb(c, WHITE)
        _rgb(c, col, fill=False)
        c.setLineWidth(2)
        c.circle(cx, cy, disc_r, stroke=1, fill=1)
        s_ = disc_r * 1.15
        draw_icon(c, icon, cx - s_ / 2, cy - s_ / 2, s_, grey=None, rgb=col)
        right = cx - disc_r - 12
    if stars:
        for k in range(3):
            draw_icon(c, "star" if k < stars else "star_border", right - 60 + k * 20, y0 + band_h / 2 - 9, 18,
                      grey=None, rgb=darker(col))
        right -= 72

    # title tab
    tab_h = h * 0.82
    tx0 = ix + 16
    pad_l = 14
    badge_w = 0
    if label is not None:
        badge_w = tab_h * 0.78 + 12
    max_w = right - 16 - tx0
    size = 24
    while pad_l + badge_w + pdfmetrics.stringWidth(title, "Display", size) + 22 > max_w and size > 16:
        size -= 0.5
    tw = pad_l + badge_w + pdfmetrics.stringWidth(title, "Display", size) + 22
    if tw > max_w:
        issue(b, "header", f"title '{title}' does not fit the header even at {size} pt")
        tw = max_w
    ty = y0 + (band_h - tab_h) / 2
    _rgb(c, darker(col))
    c.roundRect(tx0 + 3, ty - 4, tw, tab_h, tab_h * 0.35, stroke=0, fill=1)   # shadow
    _rgb(c, WHITE)
    _rgb(c, col, fill=False)
    c.setLineWidth(2.2)
    c.roundRect(tx0, ty, tw, tab_h, tab_h * 0.35, stroke=1, fill=1)
    x = tx0 + pad_l
    if label is not None:
        r = tab_h * 0.39
        _rgb(c, col)
        c.circle(x + r, ty + tab_h / 2, r, stroke=0, fill=1)
        _rgb(c, WHITE)
        fs = 16 if len(str(label)) < 3 else 12.5
        c.setFont("Display", fs)
        c.drawCentredString(x + r, ty + tab_h / 2 - fs * 0.36, str(label))
        x += badge_w
    _rgb(c, NAVY)
    c.setFont("Display", size)
    c.drawString(x, ty + tab_h / 2 - size * 0.36, title)
    return y0


def perched_mascot(b, x_right, y, col, size=46):
    """The book's mascot (our bird) sitting on top of a box edge at height y."""
    d = b.cfg.get("design") or {}
    if d.get("mascot") != "bird":
        return
    draw_icon(b.c, "bird", x_right - size, y - size * 0.11, size, grey=None, rgb=col)


# ---------- pages ----------

def title_page(b):
    cfg = b.cfg
    d = cfg.get("design") or {}
    ix, iy, iw, ih = frame(b)
    c = b.c
    mid = ix + iw / 2
    top = iy + ih
    col = accent(b, 0)
    # icon on a coloured disc, with confetti dots in the other palette colours
    cy = top - 150
    if illustrated(b):
        c.saveState()
        p = c.beginPath()
        p.roundRect(ix, cy - 106, iw, 226, 22)
        c.clipPath(p, stroke=0, fill=0)
        _rgb(c, tint(col, 0.1))
        c.rect(ix, cy - 106, iw, 226, stroke=0, fill=1)
        draw_pattern(c, ix, cy - 106, iw, 226, tint(col, 0.35), motifs_of(b), seed="title", spacing=40)
        c.restoreState()
        _rgb(c, WHITE)
        c.circle(mid, cy, 98, stroke=0, fill=1)
    _rgb(c, tint(col, 0.22))
    c.circle(mid, cy, 92, stroke=0, fill=1)
    import random
    rnd = random.Random("title")
    for k in range(18):
        _rgb(c, tint(accent(b, k + 1), 0.8))
        a = rnd.uniform(0, 6.28)
        rr = rnd.uniform(108, 150)
        import math
        c.circle(mid + rr * math.cos(a), cy + rr * math.sin(a) * 0.75, rnd.uniform(2, 5), stroke=0, fill=1)
    draw_icon(c, icon_of(b), mid - 60, cy - 62, 120, grey=None, rgb=col)
    from build_book import balanced_lines
    y = top - 300
    _rgb(c, NAVY)
    c.setFont("Display", 36)
    for ln in balanced_lines(cfg["title"], "Display", 36, iw - 40):
        c.drawCentredString(mid, y, ln)
        y -= 42
    draw_sprig(c, mid, y + 8, iw * 0.5, grey=0.65)
    y -= 28
    _rgb(c, SOFT)
    c.setFont("Body", 16)
    for ln in balanced_lines(cfg["subtitle"], "Body", 16, iw * 0.8):
        c.drawCentredString(mid, y, ln)
        y -= 22
    badge = d.get("badge")
    if badge:
        w = pdfmetrics.stringWidth(badge, "BodyBold", 13) + 32
        y -= 22
        _rgb(c, accent(b, 1))
        c.roundRect(mid - w / 2, y - 8, w, 28, 14, stroke=0, fill=1)
        _rgb(c, WHITE)
        c.setFont("BodyBold", 13)
        c.drawCentredString(mid, y + 1, badge)
    _rgb(c, NAVY)
    c.setFont("BodyBold", 15)
    c.drawCentredString(mid, iy + 24, cfg["author"])
    b.next_page()


def how_to_page(b):
    ix, iy, iw, ih = frame(b)
    c = b.c
    y = header(b, ix, iy + ih, iw, "How to play", icon=icon_of(b))
    _rgb(c, NAVY)
    y = b.text_block(b.cfg["how_to_play"], ix + 10, y - 36, iw - 20, size=16)
    py = iy + 20
    ex = getattr(b, "example", None)
    if ex and getattr(b, "draw_grid", None):
        n = len(ex["grid"])
        space = y - (py + 92) - 40
        cell = min(30, space / (n + 1.6))
        gw = n * cell
        gx, gtop = ix + (iw - gw) / 2, y - 10 - (space - gw) / 2
        c.setFont("BodyBold", 12)
        _rgb(c, accent(b, 0))
        c.drawCentredString(ix + iw / 2, gtop + 16, "EXAMPLE: " + ", ".join(w.upper() for w in ex["words"]))
        _rgb(c, NAVY)
        b.draw_grid(c, ex, gx, gtop, cell, cell * 0.62, answers=True, colors=palette(b) if is_color(b) else None)
    _rgb(c, tint(accent(b, 1), 0.15))
    c.roundRect(ix, py, iw, 92, 14, stroke=0, fill=1)
    _rgb(c, accent(b, 1))
    c.setFont("BodyBold", 12)
    c.drawString(ix + 18, py + 62, "THIS BOOK BELONGS TO")
    _rgb(c, accent(b, 1), fill=False)
    c.setLineWidth(0.9)
    c.line(ix + 18, py + 26, ix + iw - 18, py + 26)
    b.next_page()


def tracker_page(b, count):
    """'My puzzle tracker': numbered circles to colour in as puzzles are finished."""
    ix, iy, iw, ih = frame(b, accent(b, 2))
    c = b.c
    y = header(b, ix, iy + ih, iw, "My puzzle tracker", icon="emoji_events", col=accent(b, 2))
    _rgb(c, NAVY)
    y = b.text_block("Color in a circle each time you finish a puzzle. How fast can you fill the page?",
                     ix + 10, y - 34, iw - 20, size=15)
    cols = 6 if count <= 60 else 8
    rows = (count + cols - 1) // cols
    area_h = y - iy - 20
    cell = min(iw / cols, area_h / max(rows, 1), 74)
    r = cell * 0.36
    x0 = ix + (iw - cols * cell) / 2
    for i in range(count):
        row, col = divmod(i, cols)
        cx = x0 + (col + 0.5) * cell
        cy = y - 10 - (row + 0.5) * cell
        colr = accent(b, i)
        _rgb(c, colr, fill=False)
        c.setLineWidth(2)
        _rgb(c, tint(colr, 0.12))
        c.circle(cx, cy, r, stroke=1, fill=1)
        _rgb(c, colr)
        c.setFont("Display", r * 0.8)
        c.drawCentredString(cx, cy - r * 0.28, str(i + 1))
    b.next_page()


def section_page(b, heading, sub=""):
    col = accent(b, 1)
    ix, iy, iw, ih = frame(b, col)
    c = b.c
    mid = ix + iw / 2
    cy = iy + ih * 0.55
    _rgb(c, tint(col, 0.2))
    c.circle(mid, cy + 80, 62, stroke=0, fill=1)
    draw_icon(c, icon_of(b), mid - 40, cy + 40, 80, grey=None, rgb=col)
    _rgb(c, NAVY)
    c.setFont("Display", 44)
    c.drawCentredString(mid, cy - 30, heading)
    draw_sprig(c, mid, cy - 60, iw * 0.45, grey=0.65)
    if sub:
        _rgb(c, SOFT)
        c.setFont("Body", 16)
        c.drawCentredString(mid, cy - 94, sub)
    b.next_page()


def back_page(b):
    """Thank-you note + 'Collect the series' cards with tick boxes."""
    ix, iy, iw, ih = frame(b)
    c = b.c
    y = header(b, ix, iy + ih, iw, "Collect the whole series", icon="auto_stories")
    _rgb(c, NAVY)
    y = b.text_block(b.cfg["back_page"], ix + 10, y - 34, iw - 20, size=15)
    others = [b.cfg["title"] + " (this book)"] + list(b.cfg.get("also_in_series") or [])
    gap = 14
    card_w = (iw - gap) / 2
    card_h = 96
    for k, name in enumerate(others[:6]):
        col_i, row = k % 2, k // 2
        cx = ix + col_i * (card_w + gap)
        cy = y - 10 - (row + 1) * card_h - row * gap
        colr = accent(b, k)
        _rgb(c, tint(colr, 0.16))
        c.roundRect(cx, cy, card_w, card_h, 14, stroke=0, fill=1)
        _rgb(c, colr)
        c.roundRect(cx, cy, 10, card_h, 5, stroke=0, fill=1)
        draw_icon(c, icon_of(b) if k == 0 else "auto_stories", cx + 22, cy + card_h - 46, 32, grey=None, rgb=colr)
        from build_book import balanced_lines
        _rgb(c, NAVY)
        c.setFont("BodyBold", 13)
        ly = cy + card_h - 26
        for ln in balanced_lines(name, "BodyBold", 13, card_w - 80)[:3]:
            c.drawString(cx + 64, ly, ln)
            ly -= 16
        # "I have it" tick box
        _rgb(c, WHITE)
        _rgb(c, colr, fill=False)
        c.setLineWidth(1.2)
        c.roundRect(cx + 64, cy + 12, 14, 14, 3, stroke=1, fill=1)
        _rgb(c, SOFT)
        c.setFont("Body", 11)
        c.drawString(cx + 84, cy + 15, "I have this one")
    b.next_page()


def certificate_page(b):
    col = accent(b, 3)
    ix, iy, iw, ih = frame(b, col)
    c = b.c
    mid = ix + iw / 2
    top = iy + ih
    _rgb(c, tint(col, 0.14))
    c.roundRect(ix, iy, iw, ih, 14, stroke=0, fill=1)
    draw_icon(c, "emoji_events", mid - 50, top - 140, 100, grey=None, rgb=col)
    _rgb(c, NAVY)
    c.setFont("Display", 34)
    c.drawCentredString(mid, top - 190, "Certificate of")
    c.drawCentredString(mid, top - 230, "Puzzle Mastery")
    draw_sprig(c, mid, top - 255, iw * 0.5, grey=0.6)
    c.setFont("Body", 16)
    _rgb(c, SOFT)
    c.drawCentredString(mid, top - 300, "This is to certify that")
    _rgb(c, col, fill=False)
    c.setLineWidth(1)
    c.line(ix + 70, top - 350, ix + iw - 70, top - 350)
    _rgb(c, SOFT)
    from build_book import balanced_lines
    y = top - 390
    c.drawCentredString(mid, y, "solved every puzzle in")
    y -= 30
    _rgb(c, NAVY)
    c.setFont("BodyBold", 18)
    for ln in balanced_lines(b.cfg["title"], "BodyBold", 18, iw - 100):   # the title never splits mid-line
        c.drawCentredString(mid, y, ln)
        y -= 24
    c.line(ix + 70, iy + 70, ix + iw / 2 - 20, iy + 70)
    c.line(ix + iw / 2 + 20, iy + 70, ix + iw - 70, iy + 70)
    c.setFont("BodyBold", 11)
    c.drawCentredString(ix + 70 + (iw / 2 - 90) / 2, iy + 52, "DATE")
    c.drawCentredString(ix + iw / 2 + 20 + (iw / 2 - 90) / 2, iy + 52, "SIGNED")
    b.next_page()


def bonus_page(b, url):
    from reportlab.graphics import renderPDF
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing
    col = accent(b, 4)
    ix, iy, iw, ih = frame(b, col)
    c = b.c
    y = header(b, ix, iy + ih, iw, "Free bonus puzzles", icon="card_giftcard", col=col)
    _rgb(c, NAVY)
    y = b.text_block("Scan the code with your phone camera to get free printable puzzles and be the first "
                     "to hear about new books in the series.", ix + 10, y - 36, iw - 20, size=16)
    w = qr.QrCodeWidget(url)
    x1, y1, x2, y2 = w.getBounds()
    size = 200
    d = Drawing(size, size, transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0])
    d.add(w)
    renderPDF.draw(d, c, ix + (iw - size) / 2, y - 40 - size)
    _rgb(c, SOFT)
    c.setFont("Body", 13)
    c.drawCentredString(ix + iw / 2, y - 64 - size, url)
    b.next_page()


MIN_LIST_PT = 14   # CLAUDE.md: words to find never below 14 pt


def word_list_layout(words, size, avail_w):
    """Columns sized from the real text widths. Tries 3 columns, shrinking the font down to 14 pt,
    then 2 columns. Returns (cols, rows, size, column_lists, column_widths, gap)."""
    import math
    best = None
    for cols in (4, 3, 2):
        s = float(size)
        while s >= MIN_LIST_PT:
            rows = math.ceil(len(words) / cols)
            groups = [words[i * rows:(i + 1) * rows] for i in range(cols)]
            groups = [g for g in groups if g]
            box = s * 1.1                                  # checkbox + space before the word
            widths = [box + max(pdfmetrics.stringWidth(w.upper(), "Body", s) for w in g) for g in groups]
            min_gap = s * 1.2
            if sum(widths) + min_gap * (len(groups) - 1) <= avail_w:
                gap = (avail_w - sum(widths)) / max(len(groups) - 1, 1)
                return len(groups), rows, s, groups, widths, min(gap, s * 4)
            s -= 0.5
        best = best or (cols, groups, widths)
    return None


def inner_width(b):
    x, y, cw, ch = b.box
    return cw - (8 if illustrated(b) else 2 * PAD)


def ws_panel(b, entry, words, iw):
    """Word-list panel layout for one puzzle: (layout, fact_lines, panel height)."""
    from build_book import balanced_lines
    lay = word_list_layout(words, b.cfg["list_font_size"], iw - 36)
    if lay is None:
        half = (len(words) + 1) // 2
        lay = (2, half, MIN_LIST_PT, [words[:half], words[half:]], [(iw - 36) / 2] * 2, 0)
    rows, size = lay[1], lay[2]
    fact = entry.get("fact")
    fact_lines = balanced_lines(fact, "Body", 13.5, iw - 60) if fact else []
    fact_h = (34 + 18 * len(fact_lines)) if fact else 0
    return lay, fact_lines, 38 + rows * size * 1.45 + fact_h


def plan_wordsearch_pages(b, entries_and_ws):
    """Run before drawing: the tallest word panel in the book sets one panel height for every page,
    so every grid in the book is drawn at exactly the same size."""
    iw = inner_width(b)
    b.ws_panel_h = max(ws_panel(b, e, sorted(ws["words"], key=str.upper), iw)[2] for e, ws in entries_and_ws)


def wordsearch_page(b, num, entry, ws, draw_grid):
    cfg = b.cfg
    col = accent(b, num - 1)
    ix, iy, iw, ih = frame(b, col)
    c = b.c
    stars = getattr(b, "stars_for", {}).get(num)
    y = header(b, ix, iy + ih, iw, entry["title"], label=num, icon=icon_of(b, entry), col=col, stars=stars)
    words = sorted(ws["words"], key=str.upper)
    lay, fact_lines, panel_h = ws_panel(b, entry, words, iw)
    if word_list_layout(words, cfg["list_font_size"], iw - 36) is None:
        issue(b, "word-list", f"puzzle {num}: words do not fit even in 2 columns at {MIN_LIST_PT} pt")
    panel_h = max(panel_h, getattr(b, "ws_panel_h", 0))      # same panel height -> same grid size everywhere
    cols, rows, size, groups, widths, gap = lay
    lh = size * 1.45
    fact = entry.get("fact")
    n = len(ws["grid"])
    avail = y - 16 - (iy + panel_h + 14)
    cell = min(iw / (n + 0.7), avail / (n + 0.7))
    grid_w = n * cell
    if not hasattr(b, "grid_cells"):
        b.grid_cells = []
    b.grid_cells.append(round(cell, 2))
    gx = ix + (iw - grid_w) / 2
    gtop = y - 16 - cell * 0.35
    font = min(cell * 0.6, 30)                       # letters must sit inside their cells
    if font < 16:
        issue(b, "grid", f"puzzle {num}: grid letters only {font:.1f} pt (large print needs 16+); "
                         f"the grid is too small for the page")
    if illustrated(b):
        pad = cell * 0.35
        c.saveState()
        _rgb(c, darker(col, 0.85))
        c.roundRect(gx - pad + 3, gtop - grid_w - pad - 4, grid_w + 2 * pad, grid_w + 2 * pad, cell * 0.4, stroke=0, fill=1)
        _rgb(c, WHITE)
        c.roundRect(gx - pad, gtop - grid_w - pad, grid_w + 2 * pad, grid_w + 2 * pad, cell * 0.4, stroke=0, fill=1)
        c.restoreState()
    elif is_color(b):
        c.saveState()
        _rgb(c, tint(col, 0.08))
        c.roundRect(gx - cell * 0.35, gtop - grid_w - cell * 0.35, grid_w + cell * 0.7, grid_w + cell * 0.7,
                    cell * 0.4, stroke=0, fill=1)
        c.restoreState()
    draw_grid(c, ws, gx, gtop, cell, font, frame_col=col if is_color(b) else None, ink=NAVY)
    if illustrated(b):
        perched_mascot(b, gx + grid_w - cell * 0.6, gtop + cell * 0.25 + 1.2, darker(col, 0.9))
    space_top = gtop - grid_w - cell * 0.35
    py = iy + (space_top - iy - panel_h) / 2
    _rgb(c, tint(col, 0.14))
    c.roundRect(ix, py, iw, panel_h, 14, stroke=0, fill=1)
    _rgb(c, col)
    c.setFont("BodyBold", 11)
    c.drawString(ix + 18, py + panel_h - 20, "FIND THESE WORDS")
    c.setLineWidth(1.1)
    x = ix + 18
    for g, wcol in zip(groups, widths):
        for row, w in enumerate(g):
            wy = py + panel_h - 42 - row * lh
            _rgb(c, WHITE)
            _rgb(c, col, fill=False)
            c.roundRect(x, wy - 2, size * 0.75, size * 0.75, 2.5, stroke=1, fill=1)
            _rgb(c, NAVY)
            c.setFont("Body", size)
            c.drawString(x + size * 1.1, wy, w.upper())
            end = x + size * 1.1 + pdfmetrics.stringWidth(w.upper(), "Body", size)
            if end > ix + iw - 12:
                issue(b, "word-list", f"puzzle {num}: '{w}' runs past the panel edge")
        x += wcol + gap
    if fact:
        fy = py + 14 + 18 * (len(fact_lines) - 1)
        _rgb(c, tint(col, 0.5), fill=False)
        c.setLineWidth(0.6)
        c.line(ix + 18, fy + 40, ix + iw - 18, fy + 40)
        draw_icon(c, "lightbulb", ix + 14, fy + 16, 18, grey=None, rgb=col)
        _rgb(c, col)
        c.setFont("BodyBold", 11.5)
        c.drawString(ix + 36, fy + 20, "DID YOU KNOW?")
        _rgb(c, NAVY)
        c.setFont("Body", 13.5)
        for k, ln in enumerate(fact_lines):
            c.drawString(ix + 36, fy - k * 18, ln)
    b.next_page()


def wordsearch_answers(b, items, draw_grid):
    for i in range(0, len(items), 4):
        chunk = items[i:i + 4]
        col = accent(b, i // 4 + 1)
        ix, iy, iw, ih = frame(b, col)
        first, last = chunk[0][0], chunk[-1][0]
        label = f"Answers  ·  Puzzles {first}–{last}" if first != last else f"Answers  ·  Puzzle {first}"
        y = header(b, ix, iy + ih, iw, label, icon="check_circle", h=46, col=col)
        slot_w, slot_h = iw / 2, (y - 10 - iy) / 2
        for k, (num, ws) in enumerate(chunk):
            sx = ix + (k % 2) * slot_w
            stop = y - 10 - (k // 2) * slot_h
            n = len(ws["grid"])
            cell = min((slot_w - 30) / n, (slot_h - 44) / n)
            gx = sx + (slot_w - n * cell) / 2
            b.c.setFont("BodyBold", 12)
            _rgb(b.c, accent(b, num - 1))
            b.c.drawCentredString(sx + slot_w / 2, stop - 16, f"PUZZLE {num}")
            _rgb(b.c, NAVY)
            draw_grid(b.c, ws, gx, stop - 30, cell, cell * 0.6, answers=True,
                      colors=palette(b) if is_color(b) else None, ink=NAVY)
        b.next_page()


def framed_puzzle_header(b, label, title, icon=None, i=0):
    """For sudoku and maze pages: frame + header band; returns inner area below the band."""
    col = accent(b, i)
    ix, iy, iw, ih = frame(b, col)
    y = header(b, ix, iy + ih, iw, title, label=label, icon=icon or icon_of(b), col=col)
    return ix, iy, iw, y - iy
