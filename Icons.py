"""Tabler icon helpers for the Qt UI.

Wraps pytablericons (which renders Tabler SVGs to PIL images with a chosen
colour) and converts them to QIcon for use on buttons / fields. Results are
cached because each load rasterises the SVG.
"""
import os
import re
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # silence pygame import banner

from pytablericons import TablerIcons, OutlineIcon, FilledIcon  # noqa: E402  (re-exported)
import pytablericons as _pytb_pkg
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtSvg import QSvgRenderer

# Default icon colours (mirror the UI palette)
ICON_LIGHT = "#e8edf5"
ICON_SOFT  = "#c3cde0"
ICON_MUTED = "#8a99b3"
ICON_WHITE = "#ffffff"

_pixmap_cache = {}
_icon_cache = {}
_glyph_cache = {}

_TABLER_DIR = os.path.dirname(os.path.abspath(_pytb_pkg.__file__))


def _svg_glyph_pixmap(icon, target_px, color, stroke_width):
    """Render a Tabler SVG directly via QSvgRenderer — crisp at any size."""
    if isinstance(icon, OutlineIcon):
        svg_path = os.path.join(_TABLER_DIR, 'icons', 'outline', icon.value)
    else:
        svg_path = os.path.join(_TABLER_DIR, 'icons', 'filled', icon.value)
    with open(svg_path) as f:
        svg = f.read()
    svg = svg.replace('currentColor', color)
    svg = re.sub(r'stroke-width="[^"]*"', f'stroke-width="{stroke_width}"', svg)
    renderer = QSvgRenderer(svg.encode())
    pm = QPixmap(target_px, target_px)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p)
    p.end()
    return pm


def _trimmed_glyph_pixmap(icon, target_px, color, stroke_width):
    """Render a Tabler glyph, trim to its actual ink, and scale so its longest
    side equals ``target_px``. Works around pytablericons anchoring the glyph to
    the image corner instead of centring it, so callers can centre reliably.
    """
    key = (icon, target_px, color, stroke_width)
    if key in _glyph_cache:
        return _glyph_cache[key]
    # NOTE: pytablericons shrinks the glyph toward a corner as the requested
    # size grows, so render at the target size (where the glyph fills the
    # canvas well) and only rescale the trimmed ink.
    img = TablerIcons.load(icon, size=target_px, color=color, stroke_width=stroke_width)
    bbox = img.getbbox()
    # Some icons (e.g. MICROPHONE) clip against the image boundary at certain
    # sizes. Fall back to QSvgRenderer which renders the SVG directly at any
    # size without clipping.
    w_img, h_img = img.size
    if bbox is None or bbox[2] >= w_img or bbox[3] >= h_img:
        pm = _svg_glyph_pixmap(icon, target_px, color, stroke_width)
        _glyph_cache[key] = pm
        return pm
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    factor = target_px / max(w, h)
    img = img.resize((max(1, round(w * factor)), max(1, round(h * factor))), Image.LANCZOS)
    pm = QPixmap.fromImage(ImageQt(img))
    _glyph_cache[key] = pm
    return pm


def tabler_pixmap(icon, size=18, color=ICON_LIGHT, stroke_width=2.0, pad_ratio=0.12):
    """Return a QPixmap (DPR 2) for a Tabler icon.

    The trimmed glyph is scaled to ``(1 - 2*pad_ratio)`` of ``size`` and centred
    on a transparent ``size`` canvas, so every icon keeps a uniform margin and is
    visually centred regardless of the source glyph's shape.
    """
    key = (icon, size, color, stroke_width, pad_ratio)
    if key in _pixmap_cache:
        return _pixmap_cache[key]
    scale = 2
    box = size * scale
    content = max(1, round(box * (1 - 2 * pad_ratio)))
    glyph_pm = _trimmed_glyph_pixmap(icon, content, color, stroke_width)
    canvas = QPixmap(box, box)
    canvas.fill(QColor(0, 0, 0, 0))
    painter = QPainter(canvas)
    painter.drawPixmap((box - glyph_pm.width()) // 2, (box - glyph_pm.height()) // 2, glyph_pm)
    painter.end()
    canvas.setDevicePixelRatio(scale)
    _pixmap_cache[key] = canvas
    return canvas


def tabler_icon(icon, size=18, color=ICON_LIGHT, stroke_width=2.0):
    """Return a QIcon for a Tabler icon, rendered at 2x for retina crispness."""
    key = (icon, size, color, stroke_width)
    if key in _icon_cache:
        return _icon_cache[key]
    qicon = QIcon(tabler_pixmap(icon, size=size, color=color, stroke_width=stroke_width))
    _icon_cache[key] = qicon
    return qicon


_badge_cache = {}


def badge_pixmap(icon, diameter=26, icon_size=14, icon_color=ICON_WHITE, bg_color="#4A9EFF"):
    """A filled accent circle with a truly-centred white icon, as one pixmap."""
    key = (icon, diameter, icon_size, icon_color, bg_color)
    if key in _badge_cache:
        return _badge_cache[key]
    scale = 2
    d = diameter * scale
    pm = QPixmap(d, d)
    pm.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(bg_color))
    painter.drawEllipse(0, 0, d, d)
    glyph_pm = _trimmed_glyph_pixmap(icon, icon_size * scale, icon_color, 2.0)
    painter.drawPixmap((d - glyph_pm.width()) // 2, (d - glyph_pm.height()) // 2, glyph_pm)
    painter.end()
    pm.setDevicePixelRatio(scale)
    _badge_cache[key] = pm
    return pm
