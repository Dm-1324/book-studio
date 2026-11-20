"""Make Pinterest pins for a finished book.

usage: python tools/make_pins.py books/<slug> [--count 10]

Reads   book.yaml (title, pins settings, amazon_url), dist/puzzles.json, dist/interior.pdf, dist/cover-front.png,
        content/puzzles.yaml (facts)
Writes  dist/pins/pin-01.png ... (1000 x 1500, 2:3) and dist/pins/pins.json
        (title, description, alt text, board, link for each pin) for tools/post_pins.py

Pin mix per book (default 10): 1 cover, 1 "look inside", 4 "can you find these?" puzzle teasers, 4 bird facts.
Every pin links to the book's Amazon page (book.yaml amazon_url); pins are not posted until it is set.
"""
import json
import random
import sys
from pathlib import Path

import yaml
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_book  # noqa: E402,F401  (registers fonts)
from build_book import balanced_lines, draw_wordsearch_grid  # noqa: E402
from design import NAVY, PALETTES, WHITE, tint  # noqa: E402
from ornaments import draw_icon  # noqa: E402
from puzzles.wordsearch import make_wordsearch  # noqa: E402

W, H = 1000, 1500


def _rgb(c, col):
    c.setFillColorRGB(*col)


def _text(c, text, font, size, x, y, width, col, leading=1.12, align="center", max_lines=4):
    lines = balanced_lines(text, font, size, width)
    while len(lines) > max_lines and size > 20:
        size -= 4
        lines = balanced_lines(text, font, size, width)
    _rgb(c, col)
    c.setFont(font, size)
    for ln in lines:
        if align == "center":
            c.drawCentredString(x, y, ln)
        else:
            c.drawString(x, y, ln)
        y -= size * leading
    return y


def _footer(c, cfg, col):
    _rgb(c, col)
    c.rect(0, 0, W, 120, stroke=0, fill=1)
    _rgb(c, WHITE)
    c.setFont("BodyBold", 30)
    c.drawCentredString(W / 2, 70, cfg["author"].upper())
    c.setFont("Body", 26)
    c.drawCentredString(W / 2, 32, "Find it on Amazon")


def _page_image(book_dir, page_no, scale=1.6):
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(book_dir / "dist" / "interior.pdf"))
    img = pdf[page_no - 1].render(scale=scale).to_pil()
    return ImageReader(img)


def _shadow_image(c, img, x, y, w, h, angle=0):
    c.saveState()
    c.translate(x + w / 2, y + h / 2)
    c.rotate(angle)
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.18)
    c.rect(-w / 2 + 12, -h / 2 - 12, w, h, stroke=0, fill=1)
    c.setFillAlpha(1)
    c.drawImage(img, -w / 2, -h / 2, w, h)
    c.restoreState()


def pin_cover(c, ctx):
    cfg, pal = ctx["cfg"], ctx["pal"]
    _rgb(c, tint(pal[0], 0.18))
    c.rect(0, 0, W, H, stroke=0, fill=1)
    y = _text(c, ctx["pins"].get("headline", cfg["title"]), "Display", 64, W / 2, H - 140, W - 120, NAVY)
    _text(c, ctx["pins"].get("tagline", cfg["subtitle"]), "Body", 34, W / 2, y - 10, W - 160, NAVY, max_lines=3)
    cover = ImageReader(str(ctx["book_dir"] / "dist" / "cover-front.png"))
    cw = 560
    ch = cw * 11 / 8.5
    _shadow_image(c, cover, (W - cw) / 2, 170, cw, ch, angle=-3)
    _footer(c, cfg, pal[0])
    return {"kind": "cover", "title": f"{cfg['title']}: {ctx['pins'].get('gift_line', 'a gift for puzzle lovers')}"}


def pin_inside(c, ctx):
    cfg, pal = ctx["cfg"], ctx["pal"]
    _rgb(c, tint(pal[1], 0.16))
    c.rect(0, 0, W, H, stroke=0, fill=1)
    y = _text(c, "Look inside", "Display", 76, W / 2, H - 150, W - 120, NAVY)
    _text(c, ctx["pins"].get("inside_line", "Big, bold puzzles in full color"), "Body", 36, W / 2, y - 6, W - 140,
          NAVY, max_lines=2)
    pages = ctx["inside_pages"]
    pw = 420
    ph = pw * 11 / 8.5
    spots = [(70, 330, 6), (510, 300, -5), (290, 180, 0)]
    for (x, yy, a), pg in zip(spots, pages):
        _shadow_image(c, _page_image(ctx["book_dir"], pg), x, yy, pw, ph, angle=a)
    _footer(c, cfg, pal[1])
    return {"kind": "inside", "title": f"Inside {cfg['title']}: full-color, large-print puzzle pages"}


def pin_challenge(c, ctx, k):
    cfg, pal = ctx["cfg"], ctx["pal"]
    col = pal[(k + 2) % len(pal)]
    rnd = random.Random(f"pin-{k}")
    p = ctx["puzzles"][(k * 13 + 7) % len(ctx["puzzles"])]          # a different puzzle for each pin
    fits = [w for w in p["words"] if len(w.replace(" ", "")) <= 10]   # the mini grid is 10 x 10
    words = sorted(rnd.sample(fits, 5), key=len, reverse=True)
    ws = make_wordsearch(words, 10, cfg.get("difficulty", "easy"), rnd)  # a fresh mini puzzle, not a book answer
    _rgb(c, col)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    y = _text(c, "Can you find these 5 words?", "Display", 64, W / 2, H - 140, W - 120, WHITE, max_lines=2)
    n = 10
    cell = 64
    panel_top = y - 20
    panel_h = 50 + n * cell + 50 + 2 * 50 + 40
    _rgb(c, WHITE)
    c.roundRect(80, panel_top - panel_h, W - 160, panel_h, 36, stroke=0, fill=1)
    gx = (W - n * cell) / 2
    gtop = panel_top - 50
    draw_wordsearch_grid(c, ws, gx, gtop, cell, cell * 0.58, frame_col=col, ink=NAVY)
    _rgb(c, NAVY)
    c.setFont("BodyBold", 32)
    ly = gtop - n * cell - 70
    for i, w in enumerate(words):
        row, k = divmod(i, 3)
        per = 3 if row == 0 else len(words) - 3
        x = W / 2 + (k - (per - 1) / 2) * 270
        c.drawCentredString(x, ly - row * 50, w.upper())
    _text(c, f"{len(ctx['puzzles'])} more puzzles like this inside", "BodyBold", 34, W / 2,
          panel_top - panel_h - 60, W - 120, WHITE)
    _footer(c, cfg, tint(col, 1.0))
    return {"kind": "challenge", "title": f"Can you find these 5 words? \"{p['title']}\" from {cfg['title']}"}


def pin_fact(c, ctx, k):
    cfg, pal = ctx["cfg"], ctx["pal"]
    col = pal[(k + 4) % len(pal)]
    facts = [e for e in ctx["entries"] if e.get("fact")]
    e = facts[(k * 7) % len(facts)]
    _rgb(c, tint(col, 0.15))
    c.rect(0, 0, W, H, stroke=0, fill=1)
    _rgb(c, col)
    c.circle(W / 2, H - 330, 170, stroke=0, fill=1)
    draw_icon(c, e.get("icon") or (cfg.get("design") or {}).get("icon", "sprig"), W / 2 - 110, H - 440, 220,
              grey=None, rgb=WHITE)
    _text(c, "Did you know?", "Display", 70, W / 2, H - 610, W - 120, col)
    _text(c, e["fact"], "BodyBold", 58, W / 2, H - 730, W - 160, NAVY, leading=1.2, max_lines=6)
    cover = ImageReader(str(ctx["book_dir"] / "dist" / "cover-front.png"))
    cw = 230
    _shadow_image(c, cover, (W - cw) / 2, 225, cw, cw * 11 / 8.5, angle=-3)
    _text(c, f"From “{cfg['title']}”", "Body", 28, W / 2, 175, W - 140, NAVY, max_lines=2)
    _footer(c, cfg, col)
    return {"kind": "fact", "title": f"Did you know? {e['fact']}"[:100]}


def build(book_dir, count=10):
    book_dir = Path(book_dir)
    cfg = yaml.safe_load((book_dir / "book.yaml").read_text(encoding="utf-8"))
    pins_cfg = cfg.get("pins") or {}
    d = cfg.get("design") or {}
    ctx = {
        "cfg": cfg, "pins": pins_cfg, "book_dir": book_dir,
        "pal": PALETTES.get(d.get("palette", "garden"), PALETTES["garden"]),
        "puzzles": json.loads((book_dir / "dist" / "puzzles.json").read_text(encoding="utf-8")),
        "entries": yaml.safe_load((book_dir / "content" / "puzzles.yaml").read_text(encoding="utf-8"))["puzzles"],
        "inside_pages": pins_cfg.get("inside_pages", [6, 7, 5]),
    }
    out = book_dir / "dist" / "pins"
    out.mkdir(parents=True, exist_ok=True)
    plan = ["cover", "inside"] + ["challenge"] * 4 + ["fact"] * 4
    plan = (plan * ((count // len(plan)) + 1))[:count]
    meta = []
    kc = kf = 0
    for i, kind in enumerate(plan, 1):
        pdf_path = out / f"pin-{i:02d}.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=(W, H), initialFontName="Body")
        if kind == "cover":
            m = pin_cover(c, ctx)
        elif kind == "inside":
            m = pin_inside(c, ctx)
        elif kind == "challenge":
            m = pin_challenge(c, ctx, kc)
            kc += 1
        else:
            m = pin_fact(c, ctx, kf)
            kf += 1
        c.save()
        import pypdfium2 as pdfium
        png = out / f"pin-{i:02d}.png"
        pdfium.PdfDocument(str(pdf_path))[0].render(scale=1.0).to_pil().save(png)
        pdf_path.unlink()
        m.update({
            "image": png.name,
            "title": m["title"][:100],
            "description": (pins_cfg.get("description") or
                            f"{cfg['title']}: {cfg['subtitle']}. Large print, answers included. "
                            f"A thoughtful gift. #wordsearch #puzzlebook")[:500],
            "alt": f"Pin for the puzzle book {cfg['title']} ({m['kind']})",
            "board": pins_cfg.get("board", "Puzzle Books for Adults"),
            "link": cfg.get("amazon_url", ""),
        })
        meta.append(m)
    (out / "pins.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {len(meta)} pins to {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    n = int(sys.argv[sys.argv.index("--count") + 1]) if "--count" in sys.argv else 10
    build(sys.argv[1], n)
