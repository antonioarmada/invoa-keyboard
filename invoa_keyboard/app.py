from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from PySide6.QtCore import Qt, QTimer, Signal, QByteArray, QSize
from PySide6.QtGui import (
    QFont,
    QFontMetrics,
    QTextCursor,
    QPainter,
    QPen,
    QBrush,
    QIcon,
    QPixmap,
    QPainterPath,
    QColor,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QStackedLayout,
)

from .logic import LETTERS, label_for_group, split_into_groups
from .output import GlobalKeyboardOutput, OutputResult
from .settings import Settings
from .speech import SpeechOutput


def svg_icon(svg: str, size: int) -> QIcon:
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


SPEAKER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M11 5L6 9H3v6h3l5 4V5z" fill="{color}" />
  <path d="M15 9a4 4 0 0 1 0 6" />
  <path d="M18 7a7 7 0 0 1 0 10" />
</svg>
"""

MOVE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2v20M2 12h20" />
  <path d="M12 2l-3 3M12 2l3 3M12 22l-3-3M12 22l3-3M2 12l3-3M2 12l3 3M22 12l-3-3M22 12l-3 3" />
</svg>
"""

RESIZE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 18l12-12" />
  <path d="M14 4h6v6" />
  <path d="M4 14v6h6" />
</svg>
"""

KEYBOARD_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="5" width="18" height="14" rx="2" ry="2" />
  <path d="M7 9h2M11 9h2M15 9h2M7 13h2M11 13h6" />
</svg>
"""

MINIMIZE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 19h14" />
</svg>
"""

CLOSE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 6l12 12M18 6l-12 12" />
</svg>
"""

SEND_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 2L11 13" />
  <path d="M22 2l-7 20-4-9-9-4z" />
</svg>
"""

BACKSPACE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M19 12H5" />
  <path d="M11 6l-6 6 6 6" />
</svg>
"""

BUTTON_HOVER_SCALE = 1.0
BUTTON_WIDTH_FACTOR = 1.2
MIN_GROUP_COLOR_CONTRAST = 7.0
GROUP_SEED_COLORS = [
    "#0072F5",
    "#00A63E",
    "#8C4DFF",
    "#C44A00",
    "#008C8C",
    "#2E6DFF",
    "#B04A00",
    "#006699",
    "#666600",
    "#006666",
]


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return 0.0, 0.0, 0.0
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return r, g, b


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    r = max(0, min(255, int(round(rgb[0] * 255))))
    g = max(0, min(255, int(round(rgb[1] * 255))))
    b = max(0, min(255, int(round(rgb[2] * 255))))
    return f"#{r:02X}{g:02X}{b:02X}"


def _mix_rgb(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _linearize(c: float) -> float:
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_linearize(rgb[0]), _linearize(rgb[1]), _linearize(rgb[2]))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    la = _relative_luminance(a)
    lb = _relative_luminance(b)
    lighter = max(la, lb)
    darker = min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _adjust_color_for_contrast(hex_color: str, bg_hex: str, min_contrast: float) -> str:
    color = _hex_to_rgb(hex_color)
    background = _hex_to_rgb(bg_hex)
    initial_hex = _rgb_to_hex(color)
    if _contrast_ratio(_hex_to_rgb(initial_hex), background) >= min_contrast:
        return initial_hex

    white = (1.0, 1.0, 1.0)
    black = (0.0, 0.0, 0.0)
    best_candidate = color
    best_t = 2.0
    for target in (white, black):
        for step in range(1, 101):
            t = step / 100.0
            mixed = _mix_rgb(color, target, t)
            hex_mixed = _rgb_to_hex(mixed)
            if _contrast_ratio(_hex_to_rgb(hex_mixed), background) >= min_contrast:
                if t < best_t:
                    best_t = t
                    best_candidate = _hex_to_rgb(hex_mixed)
                break
        else:
            mixed = target
            if _contrast_ratio(mixed, background) > _contrast_ratio(best_candidate, background):
                best_candidate = mixed
    return _rgb_to_hex(best_candidate)


def generate_group_colors(count: int, bg_hex: str, min_contrast: float = MIN_GROUP_COLOR_CONTRAST) -> list[str]:
    usable = max(0, min(count, len(GROUP_SEED_COLORS)))
    return [_adjust_color_for_contrast(seed, bg_hex, min_contrast) for seed in GROUP_SEED_COLORS[:usable]]


class SelectionButton(QPushButton):
    shortClicked = Signal()
    longClicked = Signal()
    hoverEntered = Signal()

    def __init__(
        self, long_click_ms: int, colors: dict[str, str], accent_color: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._long_click_ms = long_click_ms
        self._colors = colors
        self._accent = accent_color
        self._press_time: float | None = None
        self._long_fired = False
        self._hovered = False
        self._base_diameter = 0
        self._base_font_size = 0
        self._base_width = 0
        self._base_height = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fire_long)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _fire_long(self) -> None:
        if self._press_time is None:
            return
        self._long_fired = True
        self.longClicked.emit()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._press_time = time.monotonic()
            self._long_fired = False
            self._timer.start(self._long_click_ms)
            self.setDown(True)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton and self._press_time is not None:
            self._timer.stop()
            if not self._long_fired:
                self.shortClicked.emit()
            self._press_time = None
            self.setDown(False)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_style()
        self.hoverEntered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def set_base_style(self, diameter: int, font_size: int) -> None:
        self._base_diameter = max(1, diameter)
        self._base_font_size = max(1, font_size)
        self._base_height = self._base_diameter
        self._base_width = max(1, int(self._base_diameter * BUTTON_WIDTH_FACTOR))
        self.setMaximumSize(self._base_width, self._base_height)
        self.setMinimumSize(44, 40)
        self.update()

    def _apply_style(self) -> None:
        self.update()

    def set_accent(self, accent_color: str) -> None:
        self._accent = accent_color
        self.update()

    def _label_scale(self) -> float:
        text = self.text().strip()
        if not text:
            return 1.0
        if len(text) == 1:
            return 1.35
        if "-" in text or "·" in text:
            return 0.95
        return 1.0

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if self._base_diameter <= 0:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        width = max(1, int(self._base_width or self._base_diameter))
        height = max(1, int(self._base_height or self._base_diameter))
        font_size = max(1, int(self._base_font_size * self._label_scale()))

        rect = self.rect()
        center_x = rect.center().x()
        center_y = rect.center().y()
        radius = max(16, int(min(width, height) * 0.22))

        fg = QColor(self._colors["fg"])
        bg = QColor(self._colors["bg"])
        accent = QColor(self._accent)
        if self._hovered:
            fill = fg
            text_color = bg
        else:
            fill = bg
            text_color = fg
        stroke = accent

        painter.setBrush(QBrush(fill))
        stroke_width = max(4, int(min(width, height) * 0.06))
        pen = QPen(stroke)
        pen.setWidth(stroke_width)
        painter.setPen(pen)
        inset = stroke_width / 2.0
        rect_left = center_x - width // 2 + inset
        rect_top = center_y - height // 2 + inset
        rect_w = width - stroke_width
        rect_h = height - stroke_width
        painter.drawRoundedRect(rect_left, rect_top, rect_w, rect_h, radius, radius)

        font = QFont()
        font.setPointSize(font_size)
        font.setBold(True)
        pad_x = max(12, int(width * 0.09))
        pad_y = max(6, int(height * 0.06))
        text_rect = rect.adjusted(pad_x, pad_y, -pad_x, -pad_y)

        metrics = QFontMetrics(font)
        label = self.text()
        if label:
            bounds = metrics.boundingRect(label)
            avail_w = max(1, text_rect.width())
            avail_h = max(1, text_rect.height())
            scale_w = avail_w / max(1, bounds.width())
            scale_h = avail_h / max(1, bounds.height())
            scale = min(1.0, scale_w, scale_h) * 0.98
            if scale < 1.0:
                font.setPointSize(max(1, int(font_size * scale)))
                metrics = QFontMetrics(font)

        painter.setFont(font)
        painter.setPen(QPen(text_color))
        painter.drawText(text_rect, Qt.AlignCenter, label)

    def sizeHint(self) -> QSize:  # type: ignore[override]
        width = self._base_width or int((self._base_diameter or 120) * BUTTON_WIDTH_FACTOR)
        height = self._base_height or self._base_diameter or 120
        return QSize(width, height)

    def minimumSizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(70, 60)


class IconButton(QPushButton):
    def __init__(self, svg_template: str, colors: dict[str, str], base_bg: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self._svg_template = svg_template
        self._base_bg = base_bg
        self._base_size = 0
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setIcon(QIcon())
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def set_base_size(self, size: int) -> None:
        self._base_size = max(1, size)
        self.setMaximumSize(self._base_size, self._base_size)
        self.setMinimumSize(36, 36)
        self._icon_size = int(self._base_size * 0.6)
        self.setIconSize(QSize(self._icon_size, self._icon_size))
        self._apply_style()

    def _apply_style(self) -> None:
        radius = self._base_size // 4 if self._base_size else 6
        fg = self._colors["fg"]
        bg = self._base_bg
        if self._hovered:
            bg, fg = fg, bg
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 3px solid {fg};
                border-radius: {radius}px;
            }}
            """
        )
        if self._base_size:
            self.setIcon(svg_icon(self._svg_template.format(color=fg), max(16, self._icon_size)))

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(self._base_size or 72, self._base_size or 72)

    def minimumSizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(36, 36)


class MoveHandle(QPushButton):
    def __init__(self, svg_template: str, colors: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self._svg_template = svg_template
        self._base_size = 0
        self._icon_size = 0
        self._hovered = False
        self.setCursor(Qt.SizeAllCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self._drag_origin = None
        self._window_origin = None
        self._apply_style()

    def set_base_size(self, size: int) -> None:
        self._base_size = max(1, size)
        self.setFixedSize(self._base_size, self._base_size)
        self._icon_size = int(self._base_size * 0.6)
        self.setIconSize(QSize(self._icon_size, self._icon_size))
        self._apply_style()

    def _apply_style(self) -> None:
        bg = self._colors["bg"]
        fg = self._colors["fg"]
        if self._hovered:
            bg, fg = fg, bg
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 2px solid {fg};
                border-radius: 6px;
            }}
            """
        )
        size = max(16, self._icon_size or 16)
        self.setIcon(svg_icon(self._svg_template.format(color=fg), size))

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._drag_origin = event.globalPosition().toPoint()
            self._window_origin = self.window().pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_origin is None or self._window_origin is None:
            super().mouseMoveEvent(event)
            return
        delta = event.globalPosition().toPoint() - self._drag_origin
        self.window().move(self._window_origin + delta)
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_origin = None
        self._window_origin = None
        super().mouseReleaseEvent(event)


class ResizeHandle(QPushButton):
    def __init__(self, svg_template: str, colors: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self._svg_template = svg_template
        self._base_size = 0
        self._icon_size = 0
        self._hovered = False
        self.setCursor(Qt.SizeFDiagCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self._drag_origin = None
        self._size_origin = None
        self._apply_style()

    def set_base_size(self, size: int) -> None:
        self._base_size = max(1, size)
        self.setFixedSize(self._base_size, self._base_size)
        self._icon_size = int(self._base_size * 0.6)
        self.setIconSize(QSize(self._icon_size, self._icon_size))
        self._apply_style()

    def _apply_style(self) -> None:
        bg = self._colors["bg"]
        fg = self._colors["fg"]
        if self._hovered:
            bg, fg = fg, bg
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 2px solid {fg};
                border-radius: 6px;
            }}
            """
        )
        size = max(16, self._icon_size or 16)
        self.setIcon(svg_icon(self._svg_template.format(color=fg), size))

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._drag_origin = event.globalPosition().toPoint()
            self._size_origin = self.window().size()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_origin is None or self._size_origin is None:
            super().mouseMoveEvent(event)
            return
        delta = event.globalPosition().toPoint() - self._drag_origin
        new_width = max(self.window().minimumWidth(), self._size_origin.width() + delta.x())
        new_height = max(self.window().minimumHeight(), self._size_origin.height() + delta.y())
        self.window().resize(new_width, new_height)
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_origin = None
        self._size_origin = None
        super().mouseReleaseEvent(event)


class AlphabetStrip(QWidget):
    def __init__(self, letters: Iterable[str], colors: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._letters = list(letters)
        self._highlight_groups: list[set[str]] = [set(self._letters)]
        self._highlight_colors: list[QColor] = [QColor("#0072F5")]
        self._colors = colors
        self.setMinimumHeight(48)

    def set_highlight_groups(self, groups: Iterable[Iterable[str]], colors: Iterable[str]) -> None:
        self._highlight_groups = [set(group) for group in groups]
        self._highlight_colors = [QColor(color) for color in colors]
        if len(self._highlight_colors) < len(self._highlight_groups):
            missing = len(self._highlight_groups) - len(self._highlight_colors)
            self._highlight_colors.extend([QColor("#0072F5")] * missing)
        self.update()

    def set_colors(self, colors: dict[str, str]) -> None:
        self._colors = colors
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        fg = QColor("#000000")
        outline = QColor(self._colors["fg"])

        height = self.height()
        width = self.width()
        font_size = max(10, int(height * 0.6))

        while font_size > 10:
            font = QFont()
            font.setPointSize(font_size)
            font.setBold(True)
            metrics = QFontMetrics(font)
            spacing = max(4, int(font_size * 0.15))
            total = sum(metrics.horizontalAdvance(letter) for letter in self._letters) + spacing * (
                len(self._letters) - 1
            )
            if total <= width - 12:
                break
            font_size -= 1

        font = QFont()
        font.setPointSize(font_size)
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        spacing = max(4, int(font_size * 0.15))
        total = sum(metrics.horizontalAdvance(letter) for letter in self._letters) + spacing * (len(self._letters) - 1)
        start_x = max(6, (width - total) // 2)
        baseline = int((height + metrics.ascent() - metrics.descent()) / 2)

        positions: list[tuple[int, int]] = []
        x = start_x
        for letter in self._letters:
            positions.append((x, metrics.horizontalAdvance(letter)))
            x += metrics.horizontalAdvance(letter) + spacing

        def draw_bar(indices: list[int], color: QColor) -> None:
            if not indices:
                return
            start_i = min(indices)
            end_i = max(indices)
            left_x = positions[start_i][0]
            right_x = positions[end_i][0] + positions[end_i][1]
            pad_x = max(2, int(font_size * 0.2))
            pad_y = max(2, int(font_size * 0.25))
            bar_left = left_x - pad_x
            bar_right = right_x + pad_x
            bar_top = baseline - metrics.ascent() - pad_y
            bar_height = metrics.height() + pad_y * 2
            bar_color = QColor(color)
            bar_color.setAlpha(170)
            painter.setBrush(QBrush(bar_color))
            painter.setPen(Qt.NoPen)
            radius = bar_height // 2
            painter.drawRoundedRect(bar_left, bar_top, bar_right - bar_left, bar_height, radius, radius)

        for idx, highlight_group in enumerate(self._highlight_groups):
            if not highlight_group:
                continue
            indices = [i for i, letter in enumerate(self._letters) if letter in highlight_group]
            color = self._highlight_colors[idx] if idx < len(self._highlight_colors) else QColor("#0072F5")
            draw_bar(indices, color)

        x = start_x
        for idx, letter in enumerate(self._letters):
            path = QPainterPath()
            path.addText(x, baseline, font, letter)
            stroke_width = max(2, int(font_size * 0.12))
            pen = QPen(outline)
            pen.setWidth(stroke_width)
            painter.strokePath(path, pen)
            fill = fg
            painter.fillPath(path, QBrush(fill))
            x += metrics.horizontalAdvance(letter) + spacing


@dataclass
class SelectionState:
    group: list[str]
    history: list[list[str]]


class KeyboardWindow(QMainWindow):
    def __init__(self, settings: Settings, output: GlobalKeyboardOutput) -> None:
        super().__init__()
        self._settings = settings
        self._output = output
        self._speech = SpeechOutput()
        self._state = SelectionState(group=LETTERS.copy(), history=[])
        self._typed_text = ""
        self._current_groups: list[list[str]] = []
        self._group_colors: list[str] = []
        self._selection_buttons: list[SelectionButton] = []
        self._active_button_count = 0
        self._last_hover_spoken_label = ""
        self._last_hover_spoken_at = 0.0
        self._minimized = False
        self._previous_geometry = None
        self._bubble_diameter = 0

        self.setWindowTitle("Teclado Ocular Binario")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self._settings.window.always_on_top)
        self.setWindowFlag(Qt.FramelessWindowHint, self._settings.window.frameless)
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, self._settings.window.ignore_focus)
        self.setWindowFlag(Qt.Tool, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, self._settings.window.ignore_focus)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.NoFocus)
        self._on_top_timer = QTimer(self)
        self._on_top_timer.setInterval(self._settings.window.on_top_refresh_ms)
        self._on_top_timer.timeout.connect(self._ensure_on_top)
        if self._settings.window.always_on_top:
            self._on_top_timer.start()
        self._build_ui()
        self._apply_styles()
        self._update_view()
        self._notify_accessibility_if_needed()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if self._settings.window.always_on_top:
            self._ensure_on_top()

    def _ensure_on_top(self) -> None:
        if not self._settings.window.always_on_top:
            return
        if not (self.windowFlags() & Qt.WindowStaysOnTopHint):
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.show()
        self.raise_()

    def _notify_accessibility_if_needed(self) -> None:
        if not self._settings.accessibility.show_macos_permission_prompt:
            return
        trusted = self._output.macos_accessibility_trusted()
        if trusted is False:
            message = (
                "Para escribir en otras apps, habilita Accesibilidad para esta aplicación.\n"
                "macOS: Ajustes del Sistema → Privacidad y seguridad → Accesibilidad.\n"
                "Si ejecutás desde Terminal, habilitá Terminal o la app .app.\n"
            )
            QMessageBox.information(self, "Accesibilidad requerida", message)

    def _build_ui(self) -> None:
        colors = self._settings.resolved_colors()
        central = QWidget(self)
        central.setAutoFillBackground(False)
        central.setAttribute(Qt.WA_TranslucentBackground, True)
        central.setFocusPolicy(Qt.NoFocus)
        self._stack = QStackedLayout(central)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self._main_panel = QWidget(central)
        layout = QVBoxLayout(self._main_panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self._alphabet_strip = AlphabetStrip(LETTERS, colors, self)

        self._buttons_container = QWidget(self)
        self._buttons_grid = QGridLayout(self._buttons_container)
        self._buttons_grid.setContentsMargins(0, 0, 0, 0)
        self._buttons_grid.setHorizontalSpacing(18)
        self._buttons_grid.setVerticalSpacing(18)
        self._buttons_grid.setAlignment(Qt.AlignCenter)

        default_group_colors = generate_group_colors(10, colors["bg"], MIN_GROUP_COLOR_CONTRAST)
        for index in range(10):
            accent = default_group_colors[index]
            button = SelectionButton(self._settings.interaction.long_click_ms, colors, accent, self)
            button.shortClicked.connect(lambda idx=index: self._on_group_short(idx))
            button.longClicked.connect(self._on_long_click)
            button.hoverEntered.connect(lambda idx=index: self._on_group_hover(idx))
            button.setVisible(False)
            self._selection_buttons.append(button)

        self._relayout_selection_buttons(0)

        self._text_view = QPlainTextEdit(self)
        self._text_view.setReadOnly(True)
        self._text_view.setMaximumBlockCount(self._settings.typing.max_visible_blocks)
        self._text_view.setFocusPolicy(Qt.NoFocus)
        self._text_view.setViewportMargins(0, 0, 0, 0)
        self._text_view.document().setDocumentMargin(4)

        self._speak_button = IconButton(SPEAKER_SVG, colors, colors["bg"], self)
        self._speak_button.clicked.connect(self._on_speak)

        self._send_button = IconButton(SEND_SVG, colors, colors["bg"], self)
        self._send_button.clicked.connect(self._on_send)

        self._backspace_button = IconButton(BACKSPACE_SVG, colors, colors["bg"], self)
        self._backspace_button.clicked.connect(self._on_backspace)

        text_row = QHBoxLayout()
        text_row.setSpacing(16)
        text_row.addWidget(self._text_view, 1)
        text_row.addStretch(0)

        self._actions_container = QWidget(self)
        actions_row = QHBoxLayout(self._actions_container)
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(18)
        actions_row.addStretch(1)
        actions_row.addWidget(self._backspace_button, 0)
        actions_row.addWidget(self._send_button, 0)
        actions_row.addWidget(self._speak_button, 0)
        actions_row.addStretch(1)
        action_flags = self._settings.ui.show_actions
        self._backspace_button.setVisible(action_flags.backspace)
        self._send_button.setVisible(action_flags.send)
        self._speak_button.setVisible(action_flags.speak)
        self._actions_container.setVisible(any([action_flags.backspace, action_flags.send, action_flags.speak]))

        self._move_handle = MoveHandle(MOVE_SVG, colors, self)
        self._resize_handle = ResizeHandle(RESIZE_SVG, colors, self)
        self._move_handle.setVisible(self._settings.window.movable)
        self._resize_handle.setVisible(self._settings.window.resizable)
        self._close_button = IconButton(CLOSE_SVG, colors, colors["bg"], self)
        self._close_button.clicked.connect(self._on_close)
        self._minimize_button = IconButton(MINIMIZE_SVG, colors, colors["bg"], self)
        self._minimize_button.clicked.connect(self._on_minimize)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)
        controls_row.addStretch(1)
        controls_row.addWidget(self._close_button, 0)
        controls_row.addWidget(self._minimize_button, 0)
        controls_row.addWidget(self._move_handle, 0)
        controls_row.addWidget(self._resize_handle, 0)

        layout.addWidget(self._alphabet_strip, 0)
        self._alphabet_strip.setVisible(self._settings.ui.show_alphabet_strip)
        layout.addWidget(self._buttons_container, 1)
        layout.addLayout(text_row, 0)
        layout.addWidget(self._actions_container, 0)
        layout.addLayout(controls_row, 0)

        self._min_panel = QWidget(central)
        min_layout = QVBoxLayout(self._min_panel)
        min_layout.setContentsMargins(0, 0, 0, 0)
        min_layout.setSpacing(0)
        self._floating_button = IconButton(KEYBOARD_SVG, colors, colors["bg"], self)
        self._floating_button.clicked.connect(self._on_restore)
        min_layout.addWidget(self._floating_button, 0, Qt.AlignCenter)

        self._stack.addWidget(self._main_panel)
        self._stack.addWidget(self._min_panel)
        self._stack.setCurrentWidget(self._main_panel)

        self.setCentralWidget(central)

    def _apply_styles(self) -> None:
        colors = self._settings.resolved_colors()
        self.setStyleSheet(
            f"""
            QMainWindow {{ background-color: transparent; }}
            QWidget {{ background-color: transparent; }}
            """
        )
        self._apply_text_style()

    def _apply_text_style(self) -> None:
        colors = self._settings.resolved_colors()
        bg = colors["bg"]
        fg = colors["fg"]
        radius = max(12, int(self._text_view.height() * 0.28)) if self._text_view else 24
        self._text_view.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {bg};
                color: {fg};
                border: 2px solid {fg};
                border-radius: {radius}px;
                padding: 2px 16px;
            }}
            """
        )

    def _group_grid_shape(self, count: int) -> tuple[int, int]:
        if count <= 0:
            return 2, 1
        if count == 2:
            return 2, 1
        if count == 3:
            return 3, 1
        if count == 4:
            return 2, 2
        if count <= 6:
            return 3, 2
        if count <= 8:
            return 4, 2
        if count == 9:
            return 3, 3
        return 5, 2

    def _relayout_selection_buttons(self, visible_count: int) -> None:
        self._active_button_count = max(0, min(visible_count, len(self._selection_buttons)))
        while self._buttons_grid.count():
            item = self._buttons_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self._buttons_container)

        columns, _ = self._group_grid_shape(max(2, self._active_button_count))
        for index, button in enumerate(self._selection_buttons):
            is_visible = index < self._active_button_count
            button.setVisible(is_visible)
            if not is_visible:
                continue
            row = index // columns
            col = index % columns
            self._buttons_grid.addWidget(button, row, col)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._update_fonts_and_sizes()

    def _update_fonts_and_sizes(self) -> None:
        if self._minimized:
            self._apply_minimized_size()
            return

        colors = self._settings.resolved_colors()
        scale = max(self._settings.ui.font_scale, 0.5)

        panel = getattr(self, "_main_panel", self)
        panel_layout = panel.layout()
        if panel_layout is not None:
            m = panel_layout.contentsMargins()
            w_inner = max(240, panel.width() - m.left() - m.right())
            h_inner = max(200, panel.height() - m.top() - m.bottom())
            v_spacing = panel_layout.spacing()
            if v_spacing < 0:
                v_spacing = 18
        else:
            w_inner = max(240, self.width())
            h_inner = max(200, self.height())
            v_spacing = 18

        visible_count = max(1, self._active_button_count)
        columns, rows = self._group_grid_shape(visible_count)
        h_gap = self._buttons_grid.horizontalSpacing()
        v_gap = self._buttons_grid.verticalSpacing()
        if h_gap < 0:
            h_gap = 18
        if v_gap < 0:
            v_gap = 18
        max_widget_d = max(90, int((w_inner - h_gap * (columns - 1)) / (columns * BUTTON_WIDTH_FACTOR)))

        for _ in range(6):
            base_d = max(64, int(max_widget_d / BUTTON_HOVER_SCALE))
            font_size = max(16, int(base_d * 0.48 * scale))
            alphabet_h = max(52, int(font_size * 1.35))
            handle_size = max(32, int(base_d * 0.30))
            action_size = max(58, int(base_d * 0.70))
            text_h = max(54, int(font_size * 1.45))
            buttons_h = rows * max_widget_d + max(0, rows - 1) * v_gap
            actions_h = action_size if self._actions_container.isVisible() else 0
            total_h = alphabet_h + buttons_h + text_h + actions_h + handle_size + v_spacing * 4
            if total_h <= h_inner:
                break
            shrink = h_inner / max(total_h, 1)
            max_widget_d = max(80, int(max_widget_d * shrink))

        base_d = max(64, int(max_widget_d / BUTTON_HOVER_SCALE))
        base_d = int(base_d * 1.05)
        self._bubble_diameter = base_d
        font_size = max(16, int(base_d * 0.48 * scale))
        alphabet_h = max(52, int(font_size * 1.35))
        handle_size = max(32, int(base_d * 0.30))
        action_size = max(58, int(base_d * 0.70))
        text_h = max(54, int(font_size * 1.45))

        for index in range(self._active_button_count):
            self._selection_buttons[index].set_base_style(base_d, font_size)

        text_font = QFont()
        text_font.setPointSize(font_size)
        text_font.setBold(True)
        self._text_view.setFont(text_font)
        self._text_view.setMaximumHeight(text_h)
        self._text_view.setMinimumHeight(50)
        self._apply_text_style()

        self._alphabet_strip.set_colors(colors)
        self._alphabet_strip.setMaximumHeight(alphabet_h)
        self._alphabet_strip.setMinimumHeight(40)

        self._backspace_button.set_base_size(action_size)
        self._send_button.set_base_size(action_size)
        self._speak_button.set_base_size(action_size)
        if self._actions_container is not None:
            if self._actions_container.isVisible():
                self._actions_container.setMaximumHeight(action_size + 6)
                self._actions_container.setMinimumHeight(40)
            else:
                self._actions_container.setMaximumHeight(0)
                self._actions_container.setMinimumHeight(0)

        self._move_handle.set_base_size(handle_size)
        self._resize_handle.set_base_size(handle_size)
        self._close_button.set_base_size(handle_size)
        self._minimize_button.set_base_size(handle_size)

    def _update_view(self) -> None:
        group = self._state.group
        colors = self._settings.resolved_colors()
        accent_colors = generate_group_colors(max(1, len(group)), colors["bg"], MIN_GROUP_COLOR_CONTRAST)

        if len(group) <= 1:
            self._current_groups = []
            self._group_colors = accent_colors[:1]
            self._alphabet_strip.set_highlight_groups([group], self._group_colors)
            self._relayout_selection_buttons(0)
            return

        self._current_groups = split_into_groups(group, self._settings.interaction.group_count)
        self._group_colors = accent_colors[: len(self._current_groups)]
        self._alphabet_strip.set_highlight_groups(self._current_groups, self._group_colors)
        self._relayout_selection_buttons(len(self._current_groups))

        for index, subgroup in enumerate(self._current_groups):
            button = self._selection_buttons[index]
            button.setText(label_for_group(subgroup))
            button.setEnabled(True)
            button.set_accent(self._group_colors[index])

        self._update_fonts_and_sizes()

    def _on_group_short(self, index: int) -> None:
        if index < 0 or index >= len(self._current_groups):
            return
        self._handle_selection(self._current_groups[index])

    def _spoken_text_for_group(self, group: list[str]) -> str:
        if not group:
            return ""
        if len(group) == 1:
            return group[0]
        return f"{group[0]} a {group[-1]}"

    def _on_group_hover(self, index: int) -> None:
        if not self._settings.speech.enabled:
            return
        if not self._settings.speech.read_group_on_hover:
            return
        if index < 0 or index >= len(self._current_groups):
            return

        spoken = self._spoken_text_for_group(self._current_groups[index]).strip()
        if not spoken:
            return

        now = time.monotonic()
        debounce_seconds = max(0, self._settings.speech.hover_read_debounce_ms) / 1000.0
        if spoken == self._last_hover_spoken_label and (now - self._last_hover_spoken_at) < debounce_seconds:
            return

        self._last_hover_spoken_label = spoken
        self._last_hover_spoken_at = now
        self._speech.speak(spoken, loud=self._settings.speech.read_group_on_hover_loud)

    def _on_long_click(self) -> None:
        if not self._settings.interaction.undo_on_long_click:
            return
        if not self._state.history:
            return
        self._state.group = self._state.history.pop()
        self._update_view()

    def _handle_selection(self, group: list[str]) -> None:
        if len(group) == 1:
            letter = group[0]
            self._typed_text += letter
            self._text_view.setPlainText(self._typed_text)
            self._text_view.moveCursor(QTextCursor.End)
            self._reset_to_root()
            return

        self._state.history.append(self._state.group)
        self._state.group = group
        self._update_view()

    def _reset_to_root(self) -> None:
        self._state.group = LETTERS.copy()
        self._state.history = []
        self._update_view()

    def _show_output_error(self, result: OutputResult) -> None:
        message = (
            "No se pudo escribir en el sistema.\n"
            "En macOS, habilita los permisos de Accesibilidad para esta app.\n"
            "En Windows, ejecuta como administrador si es necesario.\n\n"
            f"Detalle: {result.error or 'desconocido'}"
        )
        QMessageBox.warning(self, "Permisos requeridos", message)

    def _on_speak(self) -> None:
        if not self._settings.speech.enabled:
            return
        text = self._typed_text.strip()
        if not text:
            return
        self._speech.speak(text)

    def _on_backspace(self) -> None:
        if not self._typed_text:
            return
        self._typed_text = self._typed_text[:-1]
        self._text_view.setPlainText(self._typed_text)
        self._text_view.moveCursor(QTextCursor.End)

    def _on_send(self) -> None:
        if not self._settings.output.enabled:
            return
        text = self._typed_text
        if self._settings.typing.trim_before_send:
            text = text.strip()
        if not text:
            return
        result = self._output.send_text(text)
        if not result.ok:
            self._show_output_error(result)
            return
        if self._settings.typing.clear_after_send:
            self._typed_text = ""
            self._text_view.setPlainText("")

    def _on_minimize(self) -> None:
        if self._minimized:
            return
        self._minimized = True
        self._previous_geometry = self.geometry()
        self._stack.setCurrentWidget(self._min_panel)
        self._apply_minimized_size()
        self._ensure_on_top()

    def _on_close(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()
            return
        self.close()

    def _on_restore(self) -> None:
        if not self._minimized:
            return
        self._minimized = False
        self._stack.setCurrentWidget(self._main_panel)
        self.setMinimumSize(320, 280)
        self.setMaximumSize(16777215, 16777215)
        if self._previous_geometry is not None:
            self.setGeometry(self._previous_geometry)
        self._update_fonts_and_sizes()
        self._ensure_on_top()

    def _apply_minimized_size(self) -> None:
        size = max(80, int(self._bubble_diameter or 120))
        self._floating_button.set_base_size(size)
        self.setFixedSize(size, size)


def run_app(settings: Settings, fullscreen: bool) -> int:
    app = QApplication([])
    output = GlobalKeyboardOutput()
    window = KeyboardWindow(settings, output)
    start_fullscreen = fullscreen or settings.window.start_fullscreen
    if start_fullscreen:
        window.showFullScreen()
    else:
        window.show()
        if settings.window.start_minimized:
            window._on_minimize()
    return app.exec()
