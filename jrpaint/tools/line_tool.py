from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen

from .base_tool import BaseTool


class LineTool(BaseTool):
    name = "line"
    icon_text = "\u2571"
    tooltip = "Line"

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
        # Commit the line to the layer
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self._get_color(self._button)
        pen = QPen(color, self.line_width, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(self._start, self._end)
        p.end()
        self._drawing = False
        self._start = None
        self._end = None
        self._canvas.update()
        self._canvas.model.modified = True

    def paint_preview(self, painter: QPainter):
        if self._drawing and self._start and self._end:
            color = self._get_color(self._button)
            pen = QPen(color, self.line_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.drawLine(self._start, self._end)
