from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor

from .base_tool import BaseTool


class BrushTool(BaseTool):
    name = "brush"
    icon_text = "\U0001F58C"
    tooltip = "Brush"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._last_pos: QPoint | None = None
        self._drawing = False
        self._button = Qt.MouseButton.LeftButton

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        self._canvas.model.layer_stack.snapshot_active()
        self._drawing = True
        self._last_pos = pos
        self._button = button
        self._draw_at(pos, layer)

    def on_move(self, pos, button, layer):
        if not self._drawing or layer.locked:
            return
        p = QPainter(layer.image)
        self._setup_painter_for_color(p, self._button, self.line_width)
        if self._last_pos:
            p.drawLine(self._last_pos, pos)
        p.end()
        self._last_pos = pos
        self._canvas.update()

    def on_release(self, pos, button, layer):
        self._drawing = False
        self._last_pos = None
        self._canvas.model.modified = True

    def _draw_at(self, pos: QPoint, layer):
        p = QPainter(layer.image)
        self._setup_painter_for_color(p, self._button, self.line_width)
        p.drawPoint(pos)
        p.end()
        self._canvas.update()
