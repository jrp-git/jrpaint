from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygon

from .base_tool import BaseTool


class SelectFreeTool(BaseTool):
    name = "free_select"
    icon_text = "\u2702"
    tooltip = "Free-Form Select"
    cursor = Qt.CursorShape.CrossCursor

    def __init__(self, canvas):
        super().__init__(canvas)
        self._points: list[QPoint] = []
        self._selecting = False

    def on_press(self, pos, button, layer):
        sel = self._canvas.selection
        # Commit any existing floating selection
        if sel.has_content():
            self._commit_selection(layer)
        sel.clear()
        self._selecting = True
        self._points = [pos]

    def on_move(self, pos, button, layer):
        if self._selecting:
            self._points.append(pos)
            self._canvas.update()

    def on_release(self, pos, button, layer):
        if not self._selecting:
            return
        self._selecting = False
        if len(self._points) < 3:
            self._points.clear()
            return
        # Calculate bounding rect of the polygon
        polygon = QPolygon(self._points)
        rect = polygon.boundingRect()
        sel = self._canvas.selection
        sel.set_rect(rect)
        self._points.clear()
        self._canvas.update()

    def _commit_selection(self, layer):
        sel = self._canvas.selection
        if sel.has_content():
            self._canvas.model.layer_stack.snapshot_active()
            p = QPainter(layer.image)
            dest = sel.effective_rect()
            p.drawImage(dest.topLeft(), sel.content)
            p.end()
            sel.clear()
            self._canvas.model.modified = True

    def on_deactivate(self):
        sel = self._canvas.selection
        if sel.has_content():
            layer = self._canvas.model.layer_stack.active_layer
            if layer:
                self._commit_selection(layer)
        sel.clear()

    def paint_preview(self, painter: QPainter):
        # Draw lasso while selecting
        if self._selecting and len(self._points) > 1:
            pen = QPen(QColor(0, 0, 0), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            for i in range(len(self._points) - 1):
                painter.drawLine(self._points[i], self._points[i + 1])
            return

        # Draw selection rectangle
        sel = self._canvas.selection
        if sel.active:
            rect = sel.effective_rect()
            if sel.has_content():
                painter.drawImage(rect.topLeft(), sel.content)
            pen = QPen(QColor(0, 0, 0), 1, Qt.PenStyle.DashLine)
            pen.setDashOffset(sel.dash_offset)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)
