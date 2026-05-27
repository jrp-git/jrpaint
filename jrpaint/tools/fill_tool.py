import logging
import os
from collections import deque

from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QColor, QImage, QPixmap, QCursor

from .base_tool import BaseTool

log = logging.getLogger(__name__)

def _make_bucket_cursor() -> QCursor:
    """Create a paint bucket cursor from the Fill icon."""
    icon_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "icons")
    path = os.path.join(icon_dir, "Fill_1.png")
    if os.path.exists(path):
        pm = QPixmap(path)
        if not pm.isNull():
            scaled = pm.scaled(QSize(32, 32),
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
            # Hotspot at bottom-center (where paint pours)
            return QCursor(scaled, scaled.width() // 2, scaled.height() - 2)
    return QCursor(Qt.CursorShape.CrossCursor)


class FillTool(BaseTool):
    name = "fill"
    icon_text = "\u2B22"
    tooltip = "Fill With Color"
    cursor = Qt.CursorShape.CrossCursor

    def __init__(self, canvas):
        super().__init__(canvas)
        self._bucket_cursor = _make_bucket_cursor()

    def on_activate(self):
        self._canvas.setCursor(self._bucket_cursor)

    def on_deactivate(self):
        self._canvas.setCursor(Qt.CursorShape.CrossCursor)

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        x, y = pos.x(), pos.y()
        if x < 0 or x >= layer.width or y < 0 or y >= layer.height:
            return
        self._canvas.model.layer_stack.snapshot_active()
        color = self._get_color(button)
        try:
            self._flood_fill(layer.image, x, y, color)
        except Exception:
            log.exception("Error in flood fill")
        self._canvas.update()
        self._canvas.model.modified = True

    def on_move(self, pos, button, layer):
        pass

    def on_release(self, pos, button, layer):
        pass

    def _flood_fill(self, image: QImage, x: int, y: int, fill_color: QColor):
        w, h = image.width(), image.height()

        # Use pixel() / setPixel() which work with unsigned ARGB ints — much
        # faster than pixelColor() / setPixelColor().
        target_rgba = image.pixel(x, y)
        fill_rgba = fill_color.rgba()
        if target_rgba == fill_rgba:
            return

        # Scanline flood fill using a deque (no recursion, no visited set)
        # We mark pixels as filled by writing fill_rgba directly.
        queue = deque()
        queue.append((x, y))

        while queue:
            cx, cy = queue.popleft()
            if cy < 0 or cy >= h:
                continue
            if cx < 0 or cx >= w:
                continue
            if image.pixel(cx, cy) != target_rgba:
                continue

            # Scan left
            lx = cx
            while lx > 0 and image.pixel(lx - 1, cy) == target_rgba:
                lx -= 1

            # Scan right
            rx = cx
            while rx < w - 1 and image.pixel(rx + 1, cy) == target_rgba:
                rx += 1

            # Fill the span and enqueue neighbors above/below
            for fx in range(lx, rx + 1):
                image.setPixel(fx, cy, fill_rgba)
                if cy > 0 and image.pixel(fx, cy - 1) == target_rgba:
                    queue.append((fx, cy - 1))
                if cy < h - 1 and image.pixel(fx, cy + 1) == target_rgba:
                    queue.append((fx, cy + 1))
