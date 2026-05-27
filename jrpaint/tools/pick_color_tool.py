from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor

from .base_tool import BaseTool


class PickColorTool(BaseTool):
    name = "pick_color"
    icon_text = "\u2710"
    tooltip = "Pick Color"
    cursor = Qt.CursorShape.CrossCursor

    def __init__(self, canvas):
        super().__init__(canvas)

    def on_press(self, pos, button, layer):
        self._pick(pos, button, layer)

    def on_move(self, pos, button, layer):
        pass

    def on_release(self, pos, button, layer):
        pass

    def _pick(self, pos: QPoint, button, layer):
        x, y = pos.x(), pos.y()
        if 0 <= x < layer.width and 0 <= y < layer.height:
            color = layer.image.pixelColor(x, y)
            if button == Qt.MouseButton.LeftButton:
                self._canvas.set_fg_color(color)
            else:
                self._canvas.set_bg_color(color)
