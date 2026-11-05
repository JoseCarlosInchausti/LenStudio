import math
import os
import random
import time

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFileDialog, QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor

from Assets import SvgWidget, show_popup_window, load_recent, format_recent_date
from Icons import tabler_icon, OutlineIcon, ICON_WHITE

BG        = "#0a1628"
CARD      = "#152238"
BORDER    = "#27364d"
ACCENT    = "#4A9EFF"
TXT       = "#ffffff"
TXT_SOFT  = "#c3cde0"
TXT_MUTE  = "#8a99b3"


# ── Star field data ────────────────────────────────────────────────────────────

_STAR_COLORS = [
    (220, 232, 255),
    (220, 232, 255),
    (210, 225, 255),
    (240, 245, 255),
    (255, 248, 225),
    (180, 212, 255),
]


def _make_stars(seed=137):
    rng = random.Random(seed)
    stars = []

    for _ in range(220):
        stars.append({'type': 'dot', 'x': rng.random(), 'y': rng.random(),
                      'base_r': rng.uniform(0.4, 1.1), 'base_a': rng.randint(20, 75),
                      'phase': rng.uniform(0, math.tau), 'speed': rng.uniform(0.15, 0.5),
                      'color': rng.choice(_STAR_COLORS)})

    for _ in range(65):
        stars.append({'type': 'dot', 'x': rng.random(), 'y': rng.random(),
                      'base_r': rng.uniform(1.1, 2.0), 'base_a': rng.randint(55, 135),
                      'phase': rng.uniform(0, math.tau), 'speed': rng.uniform(0.4, 1.1),
                      'color': rng.choice(_STAR_COLORS)})

    for _ in range(18):
        stars.append({'type': 'glow', 'x': rng.random(), 'y': rng.random(),
                      'base_r': rng.uniform(1.8, 3.2), 'base_a': rng.randint(160, 220),
                      'glow_r': rng.uniform(4, 7), 'glow_a': rng.randint(10, 22),
                      'phase': rng.uniform(0, math.tau), 'speed': rng.uniform(0.25, 0.65),
                      'color': rng.choice(_STAR_COLORS)})

    for _ in range(6):
        n = rng.choice([6, 6, 4])
        stars.append({'type': 'spike', 'x': rng.random(), 'y': rng.random(),
                      'base_r': rng.uniform(2.5, 4.0), 'base_a': rng.randint(200, 245),
                      'glow_r': rng.uniform(6, 11), 'glow_a': rng.randint(14, 28),
                      'spike_n': n, 'spike_rot': rng.uniform(0, math.pi / n),
                      'spike_len': rng.uniform(20, 42),
                      'phase': rng.uniform(0, math.tau), 'speed': rng.uniform(0.20, 0.45),
                      'spike_phase': rng.uniform(0, math.tau),
                      'spike_speed': rng.uniform(0.12, 0.32),
                      'color': rng.choice(_STAR_COLORS[:4])})

    for _ in range(3):
        stars.append({'type': 'galaxy', 'x': rng.random(), 'y': rng.random(),
                      'w': rng.uniform(22, 55), 'h': rng.uniform(8, 22),
                      'rot': rng.uniform(0, math.pi), 'alpha': rng.randint(12, 32),
                      'color': (55, 90, 148)})

    return stars


_STARS = _make_stars()


# ── Recent file row ────────────────────────────────────────────────────────────

class _RecentRow(QFrame):
    def __init__(self, entry: dict, on_click, parent=None):
        super().__init__(parent)
        self._on_click = on_click
        self._path     = entry['path']

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)
        self._set_style(hover=False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(0)

        # File icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(tabler_icon(OutlineIcon.FILE_TYPE_CSV, size=16,
                                       color=TXT_MUTE).pixmap(16, 16))
        icon_lbl.setFixedWidth(26)
        icon_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(icon_lbl)

        # Name + path column
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        fname = os.path.basename(self._path)
        name_lbl = QLabel(fname)
        name_lbl.setStyleSheet(f"color: {TXT_SOFT}; font-size: 13px;"
                                f" font-weight: 600; background: transparent;")
        name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        dir_lbl = QLabel(os.path.dirname(self._path))
        dir_lbl.setStyleSheet(f"color: {TXT_MUTE}; font-size: 11px; background: transparent;")
        dir_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        text_col.addWidget(name_lbl)
        text_col.addWidget(dir_lbl)
        lay.addLayout(text_col)

        # Date
        date_lbl = QLabel(format_recent_date(entry.get('opened_at', '')))
        date_lbl.setStyleSheet(f"color: {TXT_MUTE}; font-size: 11px; background: transparent;")
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(date_lbl)

    def _set_style(self, hover: bool):
        bg = "#1a2d48" if hover else "transparent"
        self.setStyleSheet(f"QFrame {{ background: {bg}; border-radius: 8px; }}")

    def enterEvent(self, e):
        self._set_style(hover=True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._set_style(hover=False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._on_click(self._path)
        super().mousePressEvent(e)


# ── Main screen widget ─────────────────────────────────────────────────────────

class LoadDataWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setObjectName("loadPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#loadPage {{ background-color: {BG}; }}
            QFrame#welcomeCard {{ background-color: {CARD}; border: 1px solid {BORDER};
                                  border-radius: 16px; }}
            QLabel {{ background: transparent; }}
            QLabel#tagline  {{ color: {TXT_MUTE}; font-size: 12px; }}
            QLabel#title    {{ color: {TXT}; font-size: 26px; font-weight: 700; }}
            QLabel#subtitle {{ color: {TXT_MUTE}; font-size: 14px; }}
            QLabel#section  {{ color: {TXT_MUTE}; font-size: 10px; letter-spacing: 1px; }}
            QPushButton#cta {{ background: {ACCENT}; color: white; border: none;
                               border-radius: 10px; padding: 12px 34px;
                               font-size: 15px; font-weight: 700; }}
            QPushButton#cta:hover   {{ background: #5fb0ff; }}
            QPushButton#cta:pressed {{ background: #3d8de0; }}
        """)

        # ── Centre column: card + recent files ────────────────────────────
        centre = QVBoxLayout()
        centre.setSpacing(0)
        centre.addWidget(self._build_card())

        recent = load_recent()
        if recent:
            centre.addSpacing(16)
            sec = QLabel("RECENT FILES")
            sec.setObjectName("section")
            centre.addWidget(sec)
            centre.addSpacing(6)
            for entry in recent[:3]:
                if os.path.exists(entry['path']):
                    rr = _RecentRow(entry, self._open_path)
                    rr.setFixedWidth(460)
                    centre.addWidget(rr)

        outer = QVBoxLayout(self)
        outer.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        row.addLayout(centre)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(33)
        self._anim_timer.timeout.connect(self.update)
        self._anim_timer.start()

    # ── Card ──────────────────────────────────────────────────────────────

    def _build_card(self):
        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setFixedWidth(460)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(48, 40, 48, 40)
        lay.setSpacing(0)

        # Logo
        logo = SvgWidget(self.main_window.GRAPHICS_ADDRESSES['large app icon'])
        logo.setFixedSize(84, 84)
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo)
        logo_row.addStretch()
        lay.addLayout(logo_row)

        # Tagline
        lay.addSpacing(10)
        tagline = QLabel("Gravitational lens inspection")
        tagline.setObjectName("tagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(tagline)

        # Title
        lay.addSpacing(16)
        title = QLabel("Welcome to LenStudio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        # Subtitle
        lay.addSpacing(8)
        subtitle = QLabel("To start or open an inspection, load a CSV catalog.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        lay.addWidget(subtitle)

        # Divider
        lay.addSpacing(22)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {BORDER}; border: none;")
        lay.addWidget(divider)

        # CTA button
        lay.addSpacing(22)
        button = QPushButton("  Open CSV file")
        button.setObjectName("cta")
        button.setIcon(tabler_icon(OutlineIcon.FILE_TYPE_CSV, size=18, color=ICON_WHITE))
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.open_file_browser)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(button)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        return card

    # ── Star field ────────────────────────────────────────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        t = time.monotonic()
        W = self.width()
        H = self.height()

        for star in _STARS:
            sx = star['x'] * W
            sy = star['y'] * H
            r, g, b = star['color']

            if star['type'] == 'galaxy':
                p.save()
                p.translate(sx, sy)
                p.rotate(math.degrees(star['rot']))
                p.setPen(Qt.PenStyle.NoPen)
                rc, gc, bc = star['color']
                for i in range(6):
                    frac = i / 5
                    a  = int(star['alpha'] * (1 - frac) ** 1.8)
                    sw = star['w'] * (1 - frac * 0.45)
                    sh = star['h'] * (1 - frac * 0.45)
                    p.setBrush(QColor(rc, gc, bc, a))
                    p.drawEllipse(QRectF(-sw / 2, -sh / 2, sw, sh))
                p.restore()
                continue

            twinkle = 0.62 + 0.38 * math.sin(t * star['speed'] + star['phase'])

            if star['type'] == 'dot':
                radius = star['base_r'] * (0.82 + 0.18 * twinkle)
                alpha  = int(star['base_a'] * twinkle)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(r, g, b, alpha))
                p.drawEllipse(QRectF(sx - radius, sy - radius, radius * 2, radius * 2))

            elif star['type'] in ('glow', 'spike'):
                gr = star['glow_r'] * (0.78 + 0.22 * twinkle)
                ga = int(star['glow_a'] * twinkle)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(r, g, b, ga))
                p.drawEllipse(QRectF(sx - gr, sy - gr, gr * 2, gr * 2))

                cr = star['base_r'] * twinkle
                ca = int(star['base_a'] * twinkle)
                p.setBrush(QColor(r, g, b, ca))
                p.drawEllipse(QRectF(sx - cr, sy - cr, cr * 2, cr * 2))

                if star['type'] == 'spike':
                    spike_tw  = 0.55 + 0.45 * math.sin(
                        t * star['spike_speed'] + star['spike_phase'])
                    spike_len = star['spike_len'] * spike_tw
                    n         = star['spike_n']
                    for i in range(n):
                        angle = star['spike_rot'] + i * (math.pi / (n / 2))
                        for sign in (1.0, -1.0):
                            steps = 8
                            for j in range(steps):
                                t0   = j / steps
                                t1   = (j + 1) / steps
                                fade = (1.0 - t0) ** 1.7
                                a    = int(ca * fade * 0.9)
                                w    = max(0.3, 1.5 * (1.0 - t0))
                                pen  = QPen(QColor(r, g, b, a), w)
                                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                                p.setPen(pen)
                                p.drawLine(
                                    QPointF(sx + math.cos(angle) * sign * spike_len * t0,
                                            sy + math.sin(angle) * sign * spike_len * t0),
                                    QPointF(sx + math.cos(angle) * sign * spike_len * t1,
                                            sy + math.sin(angle) * sign * spike_len * t1),
                                )
        p.end()

    # ── File loading ───────────────────────────────────────────────────────

    def open_file_browser(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV catalog", "", "CSV files (*.csv)")
        if path:
            self._open_path(path)

    def _open_path(self, path: str):
        if not path.lower().endswith('.csv'):
            show_popup_window(title='Wrong file type', text='Please select a .CSV file.',
                              parent=self)
            return
        self._anim_timer.stop()
        self.main_window.csv_path = path
        self.main_window.load_csv()
        self.main_window.switch_screens(1)
