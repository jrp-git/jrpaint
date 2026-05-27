from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter

from .base_tool import BaseTool


class MoveTool(BaseTool):
    """Move the active layer around relative to the canvas."""

    name = "move"
    icon_text = "\u271B"
    tooltip = "Move Layer"
    cursor = Qt.CursorShape.SizeAllCursor

    def __init__(self, canvas):
        super().__init__(canvas)
        self._dragging = False
        self._drag_start: QPoint | None = None
        self._orig_offset_x = 0
        self._orig_offset_y = 0

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        self._canvas.model.layer_stack.snapshot_active()
        self._dragging = True
        self._drag_start = pos
        self._orig_offset_x = layer.offset_x
        self._orig_offset_y = layer.offset_y

    def on_move(self, pos, button, layer):
        if not self._dragging or not self._drag_start:
            return
        dx = pos.x() - self._drag_start.x()
        dy = pos.y() - self._drag_start.y()
        layer.offset_x = self._orig_offset_x + dx
        layer.offset_y = self._orig_offset_y + dy
        self._canvas.update()

    def on_release(self, pos, button, layer):
        if self._dragging:
            self._dragging = False
            self._drag_start = None
            self._canvas.model.modified = True
            self._canvas.model.layer_stack.layers_changed.emit()
