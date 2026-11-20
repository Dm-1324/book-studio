"""Render chosen pages of dist/interior.pdf (or the cover) to PNGs for visual checks.

usage: python tools/render_pages.py books/<slug> 1,5,30        -> dist/preview/page-001.png ...
       python tools/render_pages.py books/<slug> all            -> every page
       python tools/render_pages.py books/<slug> cover          -> dist/preview/cover.png
"""
import sys
from pathlib import Path

import pypdfium2 as pdfium


def render(book_dir, which, scale=1.4):
    book_dir = Path(book_dir)
    out = book_dir / "dist" / "preview"
    out.mkdir(parents=True, exist_ok=True)
    tokens = which.split(",")
    if "cover" in tokens:
        tokens.remove("cover")
        cpdf = pdfium.PdfDocument(str(book_dir / "dist" / "cover.pdf"))
        path = out / "cover.png"
        cpdf[0].render(scale=scale * 0.6).to_pil().save(path)
        print(path)
    if not tokens:
        return
    pdf = pdfium.PdfDocument(str(book_dir / "dist" / "interior.pdf"))
    pages = len(pdf)
    if tokens == ["all"]:
        tokens = [str(i) for i in range(1, pages + 1)]
    for token in tokens:
        n = pages if token == "last" else int(token)
        if not 1 <= n <= pages:
            print(f"skip page {n}: book has {pages} pages")
            continue
        path = out / f"page-{n:03d}.png"
        pdf[n - 1].render(scale=scale).to_pil().save(path)
        print(path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    render(sys.argv[1], sys.argv[2])
