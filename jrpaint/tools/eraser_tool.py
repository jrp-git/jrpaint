from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush

from .base_tool import BaseTool


class EraserTool(BaseTool):
    name = "eraser"
    icon_text = "\u2395"
    tooltip = "Eraser/Color Eraser"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._last_pos: QPoint | None = None
        self._drawing = False

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        self._canvas.model.layer_stack.snapshot_active()
        self._drawing = True
        self._last_pos = pos
        self._erase_at(pos, layer)

    def on_move(self, pos, button, layer):
        if not self._drawing or layer.locked:
            return
        # Draw a line of eraser between last and current pos
        if self._last_pos:
            p = QPainter(layer.image)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            size = max(self.line_width, 4)
            pen = QPen(Qt.GlobalColor.transparent, size, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
            p.setPen(pen)
            p.drawLine(self._last_pos, pos)
            p.end()
        self._last_pos = pos
        self._canvas.update()

    def on_release(self, pos, button, layer):
        self._drawing = False
        self._last_pos = None
        self._canvas.model.modified = True

    def _erase_at(self, pos: QPoint, layer):
        p = QPainter(layer.image)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        size = max(self.line_width, 4)
        half = size // 2
        p.eraseRect(QRect(pos.x() - half, pos.y() - half, size, size))
        p.end()
        self._canvas.update()
