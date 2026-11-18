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

from ornaments import draw_icon, draw_sprig

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


def frame(b, col=None):
    """Rounded frame on the content box. Returns the inner area (x, y, w, h) above the footer."""
    x, y, cw, ch = b.box
    c = b.c
    col = col or accent(b, 0)
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
    fy = y + PAD + 10
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
    size = 23
    room = iw - (tx - ix) - (64 if icon else 18) - (70 if stars else 0)
    while pdfmetrics.stringWidth(title, "Display", size) > room and size > 14:
        size -= 1
    c.setFont("Display", size)
    c.drawString(tx, top - h / 2 - size * 0.36, title)
    c.restoreState()
    if stars:
        sx = ix + iw - (64 if icon else 18) - 66
        for k in range(3):
            draw_icon(c, "star" if k < stars else "star_border", sx + k * 20, top - h / 2 - 9, 18,
                      grey=None, rgb=WHITE)
    if icon:
        s = h * 0.62
        draw_icon(c, icon, ix + iw - s - 16, top - h / 2 - s / 2, s, grey=None, rgb=WHITE)
    return top - h


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
    for ln in balanced_lines(f"solved every puzzle in {b.cfg['title']}", "Body", 16, iw - 100):
        c.drawCentredString(mid, y, ln)
        y -= 22
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


def wordsearch_page(b, num, entry, ws, draw_grid):
    cfg = b.cfg
    col = accent(b, num - 1)
    ix, iy, iw, ih = frame(b, col)
    c = b.c
    stars = {"easy": 1, "medium": 2, "hard": 3}.get(cfg.get("difficulty"))
    y = header(b, ix, iy + ih, iw, entry["title"], label=num, icon=icon_of(b, entry), col=col, stars=stars)
    words = sorted(ws["words"], key=str.upper)
    cols = 3
    rows = (len(words) + cols - 1) // cols
    size = cfg["list_font_size"]
    lh = size * 1.55
    fact = entry.get("fact")
    from build_book import balanced_lines
    fact_lines = balanced_lines(fact, "Body", 13.5, iw - 60) if fact else []
    fact_h = (34 + 18 * len(fact_lines)) if fact else 0
    panel_h = 38 + rows * lh + fact_h
    n = len(ws["grid"])
    avail = y - 16 - (iy + panel_h + 14)
    cell = min(iw / (n + 0.7), avail / (n + 0.7))
    grid_w = n * cell
    gx = ix + (iw - grid_w) / 2
    gtop = y - 16 - cell * 0.35
    font = max(cfg["grid_font_size"], min(cell * 0.55, 30))
    if is_color(b):
        c.saveState()
        _rgb(c, tint(col, 0.08))
        c.roundRect(gx - cell * 0.35, gtop - grid_w - cell * 0.35, grid_w + cell * 0.7, grid_w + cell * 0.7,
                    cell * 0.4, stroke=0, fill=1)
        c.restoreState()
    draw_grid(c, ws, gx, gtop, cell, font, frame_col=col if is_color(b) else None, ink=NAVY)
    space_top = gtop - grid_w - cell * 0.35
    py = iy + (space_top - iy - panel_h) / 2
    _rgb(c, tint(col, 0.14))
    c.roundRect(ix, py, iw, panel_h, 14, stroke=0, fill=1)
    _rgb(c, col)
    c.setFont("BodyBold", 11)
    c.drawString(ix + 18, py + panel_h - 20, "FIND THESE WORDS")
    col_w = (iw - 36) / cols
    c.setFont("Body", size)
    c.setLineWidth(1.1)
    for i, w in enumerate(words):
        cc, row = divmod(i, rows)
        wx, wy = ix + 18 + cc * col_w, py + panel_h - 42 - row * lh
        _rgb(c, WHITE)
        _rgb(c, col, fill=False)
        c.roundRect(wx, wy - 2, size * 0.75, size * 0.75, 2.5, stroke=1, fill=1)
        _rgb(c, NAVY)
        c.drawString(wx + size * 1.1, wy, w.upper())
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
