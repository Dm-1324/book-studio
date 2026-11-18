"""Small black-and-white decorations for interior pages, drawn by code (original, no licences).

draw_icon(c, name, x, y, size, grey)  -> name is one of OWN_ICONS or any Material Icons name
                                         (assets/fonts/MaterialIcons-Regular.ttf, Apache 2.0)
draw_sprig(c, cx, y, width, grey)      -> a small leafy divider line
"""
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_CODEPOINTS = {}
try:
    pdfmetrics.registerFont(TTFont("Icons", str(FONTS / "MaterialIcons-Regular.ttf")))
    for line in (FONTS / "MaterialIcons-Regular.codepoints").read_text().splitlines():
        name, cp = line.split()
        _CODEPOINTS[name] = chr(int(cp, 16))
except Exception:  # icons are optional
    pass

# Brand/mascot glyphs that must never be used (trademark risk)
BANNED = {"flutter_dash", "android", "apple", "adobe", "discord", "facebook", "tiktok", "wechat", "snapchat"}


def _bird(c, x, y, s):
    """Songbird perched, facing right; (x, y) is bottom-left of an s x s box."""
    P = lambda u, v: (x + u * s, y + v * s)  # noqa: E731
    p = c.beginPath()
    p.moveTo(*P(0.02, 0.38))                                   # tail tip
    p.curveTo(*P(0.20, 0.44), *P(0.30, 0.50), *P(0.38, 0.56))  # top of tail into back
    p.curveTo(*P(0.48, 0.70), *P(0.58, 0.80), *P(0.70, 0.80))  # back up to head
    p.curveTo(*P(0.80, 0.80), *P(0.86, 0.74), *P(0.88, 0.68))  # crown
    p.lineTo(*P(1.00, 0.64))                                   # beak tip
    p.lineTo(*P(0.87, 0.60))                                   # under beak
    p.curveTo(*P(0.86, 0.46), *P(0.78, 0.32), *P(0.62, 0.27))  # breast
    p.curveTo(*P(0.48, 0.23), *P(0.36, 0.28), *P(0.28, 0.33))  # belly
    p.lineTo(*P(0.04, 0.30))                                   # under tail
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    # legs + perch
    c.setLineWidth(max(s * 0.025, 0.6))
    c.line(*P(0.55, 0.26), *P(0.52, 0.12))
    c.line(*P(0.63, 0.27), *P(0.62, 0.12))
    c.setLineWidth(max(s * 0.04, 0.8))
    c.line(*P(0.25, 0.11), *P(0.92, 0.13))
    # eye (white dot)
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    c.circle(*P(0.76, 0.69), s * 0.035, stroke=0, fill=1)
    c.restoreState()


def _leaf(c, x, y, s, angle=0):
    c.saveState()
    c.translate(x, y)
    c.rotate(angle)
    p = c.beginPath()
    p.moveTo(0, 0)
    p.curveTo(s * 0.35, s * 0.28, s * 0.75, s * 0.25, s, 0)
    p.curveTo(s * 0.75, -s * 0.25, s * 0.35, -s * 0.28, 0, 0)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def _sprig_icon(c, x, y, s):
    c.setLineWidth(max(s * 0.04, 0.8))
    c.line(x + s * 0.1, y + s * 0.1, x + s * 0.85, y + s * 0.85)
    for t, side in ((0.3, 1), (0.45, -1), (0.6, 1), (0.75, -1)):
        _leaf(c, x + s * (0.1 + 0.75 * t), y + s * (0.1 + 0.75 * t), s * 0.32, 45 + side * 50)


OWN_ICONS = {"bird": _bird, "sprig": _sprig_icon}


def draw_icon(c, name, x, y, size, grey=0.3, rgb=None):
    """Draw icon `name` in a size x size box with bottom-left (x, y). Colour: rgb tuple, else grey level."""
    c.saveState()
    col = rgb or (grey, grey, grey)
    c.setFillColorRGB(*col)
    c.setStrokeColorRGB(*col)
    if name in OWN_ICONS:
        OWN_ICONS[name](c, x, y, size)
    elif name in _CODEPOINTS and name not in BANNED:
        c.setFont("Icons", size)
        c.drawString(x, y + size * 0.08, _CODEPOINTS[name])
    c.restoreState()


def draw_sprig(c, cx, y, width, grey=0.55):
    """Horizontal divider: thin line with a pair of leaves at the centre."""
    c.saveState()
    c.setStrokeColorRGB(grey, grey, grey)
    c.setFillColorRGB(grey, grey, grey)
    c.setLineWidth(0.8)
    gap = 26
    c.line(cx - width / 2, y, cx - gap, y)
    c.line(cx + gap, y, cx + width / 2, y)
    _leaf(c, cx - 4, y, 20, 160)
    _leaf(c, cx + 4, y, 20, 20)
    c.circle(cx, y, 2.4, stroke=0, fill=1)
    c.restoreState()
