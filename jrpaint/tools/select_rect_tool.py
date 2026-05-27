import math
import logging

from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QBrush, QTransform, QCursor, QPixmap

from .base_tool import BaseTool
from ..canvas.selection import Handle, HANDLE_SIZE, ROTATE_DISTANCE

# Map handles to resize cursors
_HANDLE_CURSORS = {
    Handle.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
    Handle.TOP: Qt.CursorShape.SizeVerCursor,
    Handle.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
    Handle.RIGHT: Qt.CursorShape.SizeHorCursor,
    Handle.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
    Handle.BOTTOM: Qt.CursorShape.SizeVerCursor,
    Handle.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
    Handle.LEFT: Qt.CursorShape.SizeHorCursor,
}


def _make_rotate_cursor() -> QCursor:
    """Create a small rotation cursor (curved arrow)."""
    size = 24
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(0, 0, 0), 2)
    p.setPen(pen)
    # Draw an arc
    from PyQt6.QtCore import QRectF as RF
    p.drawArc(RF(4, 4, 16, 16), 30 * 16, 270 * 16)
    # Arrowhead
    p.drawLine(QPointF(18, 6), QPointF(20, 12))
    p.drawLine(QPointF(18, 6), QPointF(13, 5))
    p.end()
    return QCursor(pm, size // 2, size // 2)

log = logging.getLogger(__name__)


class SelectRectTool(BaseTool):
    name = "rect_select"
    icon_text = "\u25A1"
    tooltip = "Select"
    cursor = Qt.CursorShape.CrossCursor

    def __init__(self, canvas):
        super().__init__(canvas)
        self._start: QPoint | None = None
        self._selecting = False
        self._dragging_selection = False
        self._drag_offset = QPoint()
        self._resizing = False
        self._resize_handle = Handle.NONE
        self._resize_last: QPoint | None = None
        self._rotating = False
        self._rotate_center = QPointF()
        self._rotate_cursor = _make_rotate_cursor()

    def on_press(self, pos, button, layer):
        sel = self._canvas.selection

        if sel.active and sel.has_content():
            # Check resize/rotate handles first
            handle = sel.hit_test_handle(pos)
            if handle == Handle.ROTATE:
                self._rotating = True
                self._rotate_center = QPointF(sel.effective_rect().center())
                return
            if handle != Handle.NONE:
                self._resizing = True
                self._resize_handle = handle
                self._resize_last = pos
                return

        # Clicking inside an existing selection — drag it
        if sel.active and sel.contains(pos):
            if not sel.has_content():
                self._lift_selection(layer)
            self._dragging_selection = True
            self._drag_offset = pos - sel.effective_rect().topLeft()
            return

        # Commit any existing floating selection
        if sel.has_content():
            self._commit_selection(layer)

        # Start a new selection rectangle
        self._selecting = True
        self._start = pos
        sel.clear()

    def on_move(self, pos, button, layer):
        sel = self._canvas.selection

        if self._rotating:
            center = self._rotate_center
            angle = math.degrees(math.atan2(
                pos.y() - center.y(), pos.x() - center.x()
            ))
            sel.rotation = angle + 45
            self._canvas.update()
            return

        if self._resizing and self._resize_last:
            dx = pos.x() - self._resize_last.x()
            dy = pos.y() - self._resize_last.y()
            sel.apply_resize(self._resize_handle, dx, dy)
            self._resize_last = pos
            self._canvas.update()
            return

        if self._dragging_selection:
            new_tl = pos - self._drag_offset
            sel.offset = new_tl - sel.rect.topLeft()
            self._canvas.update()
        elif self._selecting and self._start:
            sel.set_rect(QRect(self._start, pos))
            self._canvas.update()

        # Update cursor based on what's under the mouse
        if sel.active and sel.has_content() and not self._selecting:
            handle = sel.hit_test_handle(pos)
            if handle == Handle.ROTATE:
                self._canvas.setCursor(self._rotate_cursor)
            elif handle in _HANDLE_CURSORS:
                self._canvas.setCursor(_HANDLE_CURSORS[handle])
            elif sel.contains(pos):
                self._canvas.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self._canvas.setCursor(Qt.CursorShape.CrossCursor)
        elif sel.active and not sel.has_content() and sel.contains(pos):
            self._canvas.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self._canvas.setCursor(Qt.CursorShape.CrossCursor)

    def on_release(self, pos, button, layer):
        if self._rotating:
            self._rotating = False
        elif self._resizing:
            self._resizing = False
            self._resize_handle = Handle.NONE
            self._resize_last = None
        elif self._dragging_selection:
            self._dragging_selection = False
        elif self._selecting:
            self._selecting = False
            sel = self._canvas.selection
            if self._start:
                sel.set_rect(QRect(self._start, pos))
            self._start = None
        self._canvas.update()

    def _lift_selection(self, layer):
        sel = self._canvas.selection
        rect = sel.rect
        if rect.isEmpty():
            return
        self._canvas.model.layer_stack.snapshot_active()
        sel.content = layer.image.copy(rect)
        p = QPainter(layer.image)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.eraseRect(rect)
        p.end()
        self._canvas.update()

    def _commit_selection(self, layer):
        sel = self._canvas.selection
        if not sel.has_content():
            return
        self._canvas.model.layer_stack.snapshot_active()
        p = QPainter(layer.image)
        dest = sel.effective_rect()

        if sel.rotation != 0.0:
            # Draw with rotation around the center of the destination rect
            center = dest.center()
            p.translate(center)
            p.rotate(sel.rotation)
            p.translate(-sel.content.width() / 2, -sel.content.height() / 2)
            p.drawImage(0, 0, sel.content)
        else:
            p.drawImage(dest.topLeft(), sel.content)

        p.end()
        sel.clear()
        self._canvas.model.modified = True
        self._canvas.update()

    def on_deactivate(self):
        sel = self._canvas.selection
        if sel.has_content():
            layer = self._canvas.model.layer_stack.active_layer
            if layer:
                self._commit_selection(layer)
        sel.clear()
        self._canvas.setCursor(Qt.CursorShape.CrossCursor)

    def paint_preview(self, painter: QPainter):
        sel = self._canvas.selection
        if not sel.active:
            return

        rect = sel.effective_rect()
        center = rect.center()

        # Apply rotation transform for drawing
        if sel.rotation != 0.0 and sel.has_content():
            painter.save()
            painter.translate(center)
            painter.rotate(sel.rotation)
            painter.translate(-center.x(), -center.y())

        # Draw floating content
        if sel.has_content():
            painter.drawImage(rect.topLeft(), sel.content)

        # Marching ants
        pen = QPen(QColor(0, 0, 0), 1, Qt.PenStyle.DashLine)
        pen.setDashOffset(sel.dash_offset)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
        pen2 = QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine)
        pen2.setDashOffset(sel.dash_offset + 4)
        painter.setPen(pen2)
        painter.drawRect(rect)

        if sel.rotation != 0.0 and sel.has_content():
            painter.restore()

        # Draw resize handles (only when there's floating content)
        if sel.has_content():
            self._draw_handles(painter, sel)

    def _draw_handles(self, painter: QPainter, sel):
        """Draw the 8 resize handles + 1 rotation handle."""
        positions = sel.handle_positions()
        hs = HANDLE_SIZE // 2

        # Apply rotation for handle positions
        rect = sel.effective_rect()
        center = rect.center()
        if sel.rotation != 0.0:
            painter.save()
            painter.translate(center)
            painter.rotate(sel.rotation)
            painter.translate(-center.x(), -center.y())

        for handle, pos in positions.items():
            if handle == Handle.ROTATE:
                # Rotation handle: small circle
                painter.setPen(QPen(QColor(0, 120, 215), 1))
                painter.setBrush(QBrush(QColor(0, 120, 215, 180)))
                painter.drawEllipse(pos, hs + 1, hs + 1)
                # Draw a line from top-right corner to the rotate handle
                tr = QPointF(rect.right(), rect.top())
                painter.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DotLine))
                painter.drawLine(tr, pos)
            else:
                # Resize handles: small white squares with dark border
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawRect(QRectF(pos.x() - hs, pos.y() - hs,
                                        HANDLE_SIZE, HANDLE_SIZE))

        if sel.rotation != 0.0:
            painter.restore()
