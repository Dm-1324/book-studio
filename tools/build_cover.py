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
from build_book import balanced_lines  # noqa: E402  (also registers fonts)

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

    # ---- front: badge, title, subtitle, author ----
    left = front_x + SAFE
    width = tw - 2 * SAFE
    mid = front_x + tw / 2
    top = BLEED + th - SAFE
    rgb(c, style["accent"])
    c.roundRect(left, top - 30, pdfmetrics.stringWidth(style["badge"], "BodyBold", 14) + 28, 30, 15, stroke=0, fill=1)
    rgb(c, style["bg"])
    c.setFont("BodyBold", 14)
    c.drawString(left + 14, top - 21, style["badge"])

    rgb(c, style["text"])
    size = 58
    lines = balanced_lines(cfg["title"].upper(), "Display", size, width)
    while len(lines) > 2 and size > 40:
        size -= 4
        lines = balanced_lines(cfg["title"].upper(), "Display", size, width)
    y = top - 60 - size * 0.8
    c.setFont("Display", size)
    for ln in lines:
        c.drawCentredString(mid, y, ln)
        y -= size * 1.05
    rgb(c, style["accent"])
    c.rect(mid - 60, y + size * 0.35, 120, 4, stroke=0, fill=1)
    rgb(c, style["text"])
    sub = balanced_lines(cfg["subtitle"], "Body", 20, width * 0.9)
    y -= 10
    c.setFont("Body", 20)
    for ln in sub:
        c.drawCentredString(mid, y, ln)
        y -= 27
    art_top = BLEED + th * ART_FRACTION
    if y - 8 < art_top + 24:
        raise SystemExit("front cover text runs into the art area; shorten the subtitle")
    features = style.get("features") or f"{info['count']} PUZZLES  \u00b7  ANSWERS INCLUDED"
    rgb(c, style["accent"])
    c.setFont("BodyBold", 17)
    c.drawCentredString(mid, y - 8, features)
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

    # ---- back ----
    bx = BLEED + SAFE
    bw = tw - 2 * SAFE
    by = BLEED + th - SAFE - 40
    blurb = style["blurb"] or cfg.get("back_blurb", "")
    if blurb:
        c.setFont("Display", 26)
        rgb(c, style["accent"])
        c.drawString(bx, by, style.get("back_heading", "What's inside"))
        rgb(c, style["text"])
        by -= 44
        for para in blurb.strip().split("\n\n"):
            for ln in _wrap(para, "Body", 17, bw):
                c.setFont("Body", 17)
                c.drawString(bx, by, ln)
                by -= 25
            by -= 12
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
