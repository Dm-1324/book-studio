"""Build the KDP paperback wrap cover (back + spine + front, with bleed) as one PDF.

usage: python tools/build_cover.py books/<slug>

Reads   book.yaml, dist/build.json (page count), assets/cover-art.png (optional),
        assets/cover.yaml (optional: colours, back-cover blurb)
Writes  dist/cover.pdf, dist/cover-front.png (thumbnail check)

Spine width = pages x 0.002252 in (white paper) or 0.0025 in (cream).
Spine text only when pages >= 79 (KDP rule). Barcode area kept clear on the back (KDP prints it).
"""
import json
import sys
from pathlib import Path

import yaml
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build_book import balanced_lines, draw_wordsearch_grid  # noqa: E402  (also registers fonts)
from ornaments import draw_icon  # noqa: E402
pdfmetrics.registerFont(TTFont("Serif", str(ROOT / "assets" / "fonts" / "BreeSerif-Regular.ttf")))

BLEED = 0.125 * inch
SAFE = 0.375 * inch  # keep text this far from trim edges
ART_FRACTION = 0.48   # default share of the front cover height used by the art (cover.yaml: art_fraction)
PER_PAGE = {"white": 0.002252, "cream": 0.0025}
DEFAULT_STYLE = {
    "bg": [0.07, 0.24, 0.18],       # deep cricket green
    "accent": [0.96, 0.78, 0.25],   # warm gold
    "text": [1, 1, 1],
    "badge": "LARGE PRINT",
    "blurb": "",
}


def rgb(c, col, fill=True):
    (c.setFillColorRGB if fill else c.setStrokeColorRGB)(*col)


def build(book_dir):
    book_dir = Path(book_dir)
    cfg = yaml.safe_load((book_dir / "book.yaml").read_text(encoding="utf-8"))
    info = json.loads((book_dir / "dist" / "build.json").read_text(encoding="utf-8"))
    style = dict(DEFAULT_STYLE)
    cy = book_dir / "assets" / "cover.yaml"
    if cy.exists():
        style.update(yaml.safe_load(cy.read_text(encoding="utf-8")) or {})

    global ART_FRACTION
    ART_FRACTION = float(style.get("art_fraction", ART_FRACTION))
    pages = info["pages"]
    tw, th = cfg["trim"][0] * inch, cfg["trim"][1] * inch
    spine = pages * PER_PAGE[cfg.get("paper", "white")] * inch
    W, H = 2 * BLEED + 2 * tw + spine, 2 * BLEED + th
    out = book_dir / "dist" / "cover.pdf"
    c = canvas.Canvas(str(out), pagesize=(W, H), initialFontName="Body")
    c.setTitle(cfg["title"] + " (cover)")

    rgb(c, style["bg"])
    c.rect(0, 0, W, H, stroke=0, fill=1)

    front_x = BLEED + tw + spine
    art = book_dir / "assets" / "cover-art.png"
    if art.exists():
        # art fills the lower part of the front cover, out to the bleed edge
        img = ImageReader(str(art))
        iw, ih = img.getSize()
        box_w = tw + BLEED
        box_h = th * ART_FRACTION + BLEED
        scale = max(box_w / iw, box_h / ih)
        dw, dh = iw * scale, ih * scale
        c.saveState()
        p = c.beginPath()
        p.rect(front_x, 0, box_w, box_h)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(img, front_x + (box_w - dw) / 2, (box_h - dh) / 2, dw, dh)
        c.restoreState()
    else:
        _placeholder_art(c, front_x, tw, th, style, book_dir, cfg)

    # ---- front: like a real book: one strong title, a short subtitle, a small useful badge ----
    left = front_x + SAFE
    width = tw - 2 * SAFE
    mid = front_x + tw / 2
    top = BLEED + th - SAFE
    badge = style.get("badge")
    if badge:
        rgb(c, style["accent"])
        c.roundRect(left, top - 30, pdfmetrics.stringWidth(badge, "BodyBold", 14) + 28, 30, 15, stroke=0, fill=1)
        rgb(c, style["bg"])
        c.setFont("BodyBold", 14)
        c.drawString(left + 14, top - 21, badge)
    y = top - 58
    kicker = style.get("kicker")
    if kicker:
        rgb(c, style["accent"])
        c.setFont("BodyBold", 15)
        c.drawCentredString(mid, y - 10, kicker.upper())
        y -= 34
    rgb(c, style["text"])
    size = 84
    lines = balanced_lines(cfg["title"].upper(), "Display", size, width)
    while (len(lines) > 2 or max(pdfmetrics.stringWidth(ln, "Display", size) for ln in lines) > width) and size > 40:
        size -= 2
        lines = balanced_lines(cfg["title"].upper(), "Display", size, width)
    y -= size * 0.8
    c.setFont("Display", size)
    for ln in lines:
        c.drawCentredString(mid, y, ln)
        y -= size * 1.02
    rgb(c, style["accent"])
    c.rect(mid - 60, y + size * 0.42, 120, 4, stroke=0, fill=1)
    rgb(c, style["text"])
    y -= 14
    sub_size = 26
    sub = balanced_lines(cfg["subtitle"], "Serif", sub_size, width * 0.92)
    c.setFont("Serif", sub_size)
    for ln in sub:
        c.drawCentredString(mid, y, ln)
        y -= sub_size * 1.25
    art_top = BLEED + th * ART_FRACTION
    if y < art_top + 10:
        raise SystemExit("front cover text runs into the art area; shorten the title or subtitle")
    features = style.get("features")
    if features:
        rgb(c, style["accent"])
        c.setFont("BodyBold", 17)
        c.drawCentredString(mid, y - 4, features)
    # author on a band at the bottom
    rgb(c, style["bg"])
    c.rect(front_x, 0, tw + BLEED, BLEED + 0.7 * inch, stroke=0, fill=1)
    rgb(c, style["text"])
    c.setFont("BodyBold", 18)
    c.drawCentredString(mid, BLEED + 0.27 * inch, cfg["author"])

    # ---- spine ----
    # KDP: spine text only for 79+ pages, with 0.0625 in clear on each side of the text
    fs = min((spine - 2 * 0.0625 * inch) * 0.75, 16)
    if pages >= 79 and fs >= 6:
        c.saveState()
        c.translate(BLEED + tw + spine / 2, BLEED + th / 2)
        c.rotate(-90)
        c.setFont("BodyBold", fs)
        rgb(c, style["text"])
        c.drawCentredString(0, -fs * 0.35, f"{cfg['title'].upper()}   ·   {cfg['author']}")
        c.restoreState()

    # ---- back: hook, short blurb, "inside this book" ticks, a tiny teaser puzzle, publisher ----
    bx = BLEED + SAFE
    bw = tw - 2 * SAFE
    by = BLEED + th - SAFE - 46
    hook = style.get("back_heading", "What's inside")
    rgb(c, style["accent"])
    hs = 34
    for ln in balanced_lines(hook, "Display", hs, bw):
        c.setFont("Display", hs)
        c.drawString(bx, by, ln)
        by -= hs * 1.15
    by -= 14
    rgb(c, style["text"])
    blurb = style.get("blurb") or cfg.get("back_blurb", "")
    for para in blurb.strip().split("\n\n"):
        for ln in _wrap(" ".join(para.split()), "Serif", 18, bw):
            c.setFont("Serif", 18)
            c.drawString(bx, by, ln)
            by -= 26
        by -= 12
    bullets = style.get("back_bullets") or []
    if bullets:
        by -= 6
        rgb(c, style["accent"])
        c.setFont("BodyBold", 15)
        c.drawString(bx, by, "INSIDE THIS BOOK")
        by -= 32
        for item in bullets:
            draw_icon(c, "check_circle", bx, by - 5, 22, grey=None, rgb=tuple(style["accent"]))
            rgb(c, style["text"])
            c.setFont("Body", 17)
            c.drawString(bx + 32, by, item)
            by -= 30
    # teaser: a tiny real word search ("Try one!"), bottom-left; bottom-right stays clear for the barcode
    teaser = style.get("teaser")
    if teaser:
        from puzzles.wordsearch import make_wordsearch
        import random
        ws = make_wordsearch([teaser], 6, cfg.get("difficulty", "easy"), random.Random("teaser"))
        card = 2.0 * inch
        cx0 = bx
        cy0 = max(BLEED + 0.95 * inch, by - 30 - card - 24)          # just under the checklist
        rgb(c, style["accent"])
        c.setFont("BodyBold", 15)
        c.drawString(cx0, cy0 + card + 14, f"TRY ONE: FIND {teaser.upper()}")
        rgb(c, [1, 1, 1])
        c.roundRect(cx0, cy0, card, card, 14, stroke=0, fill=1)
        cell = (card - 30) / 6
        draw_wordsearch_grid(c, ws, cx0 + 15, cy0 + card - 15, cell, cell * 0.6, frame_col=tuple(style["accent"]),
                             ink=tuple(style["bg"]))
    rgb(c, style["text"])
    draw_icon(c, "bird", bx, BLEED + 0.32 * inch, 30, grey=None, rgb=tuple(style["accent"]))
    c.setFont("BodyBold", 15)
    c.drawString(bx + 38, BLEED + 0.42 * inch, cfg["author"])
    # barcode area: KDP prints its barcode bottom-right of the back cover (2 x 1.2 in). Keep it clear.
    c.save()
    _front_png(book_dir, out, tw, spine)
    print(f"wrote {out}  ({W / inch:.3f} x {H / inch:.3f} in, spine {spine / inch:.3f} in, {pages} pages)")


def _placeholder_art(c, fx, tw, th, style, book_dir=None, cfg=None):
    """Theme-neutral art used until Fooocus art exists: a tilted card showing the book's
    first puzzle with three found words circled. Works for any word search book."""
    import math
    import random
    c.saveState()
    art_h = BLEED + th * ART_FRACTION
    rgb(c, style.get("art_bg", [min(1, v + 0.08) for v in style["bg"]]))
    c.rect(fx, 0, tw + BLEED, art_h, stroke=0, fill=1)
    grid, places = None, []
    pj = Path(book_dir) / "dist" / "puzzles.json" if book_dir else None
    if pj and pj.exists():
        # a decoy grid built from words across the book, so the cover gives no answers away
        from puzzles.wordsearch import make_wordsearch
        allp = json.loads(pj.read_text(encoding="utf-8"))
        if allp and "grid" in allp[0]:
            n0 = len(allp[0]["grid"])
            cfg = cfg or {}
            rnd = random.Random("cover")
            pool = sorted({w for p in allp for w in p["words"] if 5 <= len(w.replace(" ", "")) <= n0 - 2})
            for _ in range(20):
                pick = rnd.sample(pool, min(6, len(pool)))
                try:
                    ws = make_wordsearch(pick, n0, cfg.get("difficulty", "medium"), rnd)  # match the book's promise
                    grid, places = ws["grid"], list(ws["placements"].values())
                    break
                except (ValueError, RuntimeError):
                    continue
    if grid is None:
        rnd = random.Random(1)
        grid = [[rnd.choice("ABCDEFGHIKLMNOPRSTUW") for _ in range(12)] for _ in range(12)]
    n = len(grid)
    band = BLEED + 0.7 * inch            # author band at the bottom
    room = art_h - band
    card = min(tw * 0.6, room * 0.82)    # leaves space for the 6 degree tilt
    cx, cy = fx + tw / 2, band + room / 2
    c.translate(cx, cy)
    c.rotate(-6)
    rgb(c, [0, 0, 0])
    c.setFillAlpha(0.25)
    c.roundRect(-card / 2 + 8, -card / 2 - 8, card, card, 14, stroke=0, fill=1)
    c.setFillAlpha(1)
    rgb(c, [1, 1, 1])
    c.roundRect(-card / 2, -card / 2, card, card, 14, stroke=0, fill=1)
    pad = card * 0.07
    cell = (card - 2 * pad) / n
    x0, ytop = -card / 2 + pad, card / 2 - pad
    from puzzles.wordsearch import DIRS
    rgb(c, style["accent"], fill=False)
    c.setLineWidth(cell * 0.09)
    for p in sorted(places, key=lambda q: -q["len"])[:3]:
        dr, dc = DIRS[p["dir"]]
        ax, ay = x0 + (p["col"] + 0.5) * cell, ytop - (p["row"] + 0.5) * cell
        bx = x0 + (p["col"] + dc * (p["len"] - 1) + 0.5) * cell
        by = ytop - (p["row"] + dr * (p["len"] - 1) + 0.5) * cell
        ang = math.atan2(by - ay, bx - ax)
        c.saveState()
        c.translate(ax, ay)
        c.rotate(math.degrees(ang))
        rad = cell * 0.44
        c.roundRect(-rad, -rad, math.hypot(bx - ax, by - ay) + 2 * rad, 2 * rad, rad, stroke=1, fill=0)
        c.restoreState()
    rgb(c, [0.13, 0.13, 0.13])
    fs = cell * 0.6
    c.setFont("BodyBold", fs)
    for r in range(n):
        for col in range(n):
            c.drawCentredString(x0 + (col + 0.5) * cell, ytop - (r + 0.5) * cell - fs * 0.35, grid[r][col])
    c.restoreState()


def _wrap(text, font, size, width):
    words, line, out = text.split(), "", []
    for w in words:
        t = (line + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) > width:
            out.append(line)
            line = w
        else:
            line = t
    out.append(line)
    return out


def _front_png(book_dir, pdf_path, tw, spine):
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return
    img = pdfium.PdfDocument(str(pdf_path))[0].render(scale=1.0).to_pil()
    s = img.width / ((2 * BLEED + 2 * tw + spine))
    left = int((BLEED + tw + spine) * s)
    front = img.crop((left, int(BLEED * s), left + int(tw * s), img.height - int(BLEED * s)))
    front.save(book_dir / "dist" / "cover-front.png")
    front.resize((160, int(160 * front.height / front.width))).save(book_dir / "dist" / "cover-thumb.png")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    build(sys.argv[1])
