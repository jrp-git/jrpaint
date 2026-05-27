from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QPolygon

from .base_tool import BaseTool


class PolygonTool(BaseTool):
    name = "polygon"
    icon_text = "\u2B23"
    tooltip = "Polygon"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._points: list[QPoint] = []
        self._current: QPoint | None = None
        self._button = Qt.MouseButton.LeftButton

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        if not self._points:
            self._canvas.model.layer_stack.snapshot_active()
            self._button = button
        self._points.append(pos)
        self._current = pos
        self._canvas.update()

    def on_move(self, pos, button, layer):
        if self._points:
            self._current = pos
            self._canvas.update()

    def on_release(self, pos, button, layer):
        if not self._points or layer.locked:
            return
        # Check if close to first point (double-click or close polygon)
        if len(self._points) >= 3:
            first = self._points[0]
            dx = abs(pos.x() - first.x())
            dy = abs(pos.y() - first.y())
            if dx < 8 and dy < 8:
                self._commit(layer)
                return
        self._canvas.update()

    def _commit(self, layer):
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self._get_color(self._button)
        bg = self.bg_color
        polygon = QPolygon(self._points)
        fill_mode = self.fill_mode
        if fill_mode == 0:
            p.setPen(QPen(color, self.line_width))
            p.setBrush(Qt.BrushStyle.NoBrush)
        elif fill_mode == 1:
            p.setPen(QPen(color, self.line_width))
            p.setBrush(QBrush(bg))
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
        p.drawPolygon(polygon)
        p.end()
        self._points.clear()
        self._current = None
        self._canvas.update()
        self._canvas.model.modified = True

    def on_deactivate(self):
        if self._points:
            layer = self._canvas.model.layer_stack.active_layer
            if layer:
                self._commit(layer)
        self._points.clear()
        self._current = None

    def paint_preview(self, painter: QPainter):
        if not self._points:
            return
        color = self._get_color(self._button)
        painter.setPen(QPen(color, self.line_width))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i in range(len(self._points) - 1):
            painter.drawLine(self._points[i], self._points[i + 1])
        if self._current and self._points:
            painter.drawLine(self._points[-1], self._current)
