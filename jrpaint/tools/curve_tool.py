from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QPainterPath

from .base_tool import BaseTool


class CurveTool(BaseTool):
    """Classic Paint curve: draw a line, then click twice to set control points."""

    name = "curve"
    icon_text = "\u223F"
    tooltip = "Curve"

    STATE_IDLE = 0
    STATE_LINE = 1        # Drawing the initial line
    STATE_CONTROL1 = 2    # Adjusting first control point
    STATE_CONTROL2 = 3    # Adjusting second control point

    def __init__(self, canvas):
        super().__init__(canvas)
        self._state = self.STATE_IDLE
        self._p1: QPoint | None = None
        self._p2: QPoint | None = None
        self._cp1: QPoint | None = None
        self._cp2: QPoint | None = None
        self._button = Qt.MouseButton.LeftButton

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        if self._state == self.STATE_IDLE:
            self._canvas.model.layer_stack.snapshot_active()
            self._state = self.STATE_LINE
            self._p1 = pos
            self._p2 = pos
            self._cp1 = None
            self._cp2 = None
            self._button = button
        elif self._state == self.STATE_CONTROL1:
            self._cp1 = pos
        elif self._state == self.STATE_CONTROL2:
            self._cp2 = pos

    def on_move(self, pos, button, layer):
        if self._state == self.STATE_LINE:
            self._p2 = pos
        elif self._state == self.STATE_CONTROL1:
            self._cp1 = pos
        elif self._state == self.STATE_CONTROL2:
            self._cp2 = pos
        self._canvas.update()

    def on_release(self, pos, button, layer):
        if layer.locked:
            return
        if self._state == self.STATE_LINE:
            self._p2 = pos
            self._cp1 = QPoint((self._p1.x() + self._p2.x()) // 2,
                               (self._p1.y() + self._p2.y()) // 2)
            self._cp2 = QPoint(self._cp1)
            self._state = self.STATE_CONTROL1
        elif self._state == self.STATE_CONTROL1:
            self._cp1 = pos
            self._state = self.STATE_CONTROL2
        elif self._state == self.STATE_CONTROL2:
            self._cp2 = pos
            self._commit(layer)
        self._canvas.update()

    def _commit(self, layer):
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_curve(p)
        p.end()
        self._state = self.STATE_IDLE
        self._canvas.update()
        self._canvas.model.modified = True

    def _draw_curve(self, p: QPainter):
        if not all([self._p1, self._p2, self._cp1, self._cp2]):
            return
        color = self._get_color(self._button)
        p.setPen(QPen(color, self.line_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap))
        path = QPainterPath(QPointF(self._p1))
        path.cubicTo(QPointF(self._cp1), QPointF(self._cp2), QPointF(self._p2))
        p.drawPath(path)

    def on_deactivate(self):
        if self._state != self.STATE_IDLE:
            layer = self._canvas.model.layer_stack.active_layer
            if layer and self._p1 and self._p2:
                self._commit(layer)
        self._state = self.STATE_IDLE

    def paint_preview(self, painter: QPainter):
        if self._state == self.STATE_LINE and self._p1 and self._p2:
            color = self._get_color(self._button)
            painter.setPen(QPen(color, self.line_width))
            painter.drawLine(self._p1, self._p2)
        elif self._state in (self.STATE_CONTROL1, self.STATE_CONTROL2):
            self._draw_curve(painter)
