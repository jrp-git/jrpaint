from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QBrush

from .base_tool import BaseTool


class EllipseTool(BaseTool):
    name = "ellipse"
    icon_text = "\u25CB"
    tooltip = "Ellipse"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._start: QPoint | None = None
        self._end: QPoint | None = None
        self._drawing = False
        self._button = Qt.MouseButton.LeftButton

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        self._canvas.model.layer_stack.snapshot_active()
        self._drawing = True
        self._start = pos
        self._end = pos
        self._button = button

    def on_move(self, pos, button, layer):
        if not self._drawing:
            return
        self._end = pos
        self._canvas.update()

    def on_release(self, pos, button, layer):
        if not self._drawing or layer.locked:
            return
        self._end = pos
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_shape(p)
        p.end()
        self._drawing = False
        self._start = None
        self._end = None
        self._canvas.update()
        self._canvas.model.modified = True

    def _draw_shape(self, p: QPainter):
        color = self._get_color(self._button)
        bg = self.bg_color
        rect = QRect(self._start, self._end).normalized()
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
        p.drawEllipse(rect)

    def paint_preview(self, painter: QPainter):
        if self._drawing and self._start and self._end:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._draw_shape(painter)
