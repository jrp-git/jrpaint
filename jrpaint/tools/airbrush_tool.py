import logging
import random

from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor

from .base_tool import BaseTool

log = logging.getLogger(__name__)


class AirbrushTool(BaseTool):
    name = "airbrush"
    icon_text = "\u2601"
    tooltip = "Airbrush"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._spraying = False
        self._pos: QPoint | None = None
        self._button = Qt.MouseButton.LeftButton
        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._spray)

    def on_press(self, pos, button, layer):
        if layer.locked:
            return
        self._canvas.model.layer_stack.snapshot_active()
        self._spraying = True
        self._pos = pos
        self._button = button
        self._spray()
        self._timer.start()

    def on_move(self, pos, button, layer):
        self._pos = pos

    def on_release(self, pos, button, layer):
        self._spraying = False
        self._timer.stop()
        self._canvas.model.modified = True

    def on_deactivate(self):
        self._timer.stop()
        self._spraying = False

    def _spray(self):
        if not self._spraying or not self._pos:
            return
        # Get the current active layer fresh each tick (avoids stale reference)
        layer = self._canvas.model.layer_stack.active_layer
        if not layer or layer.image.isNull():
            return
        try:
            p = QPainter(layer.image)
            color = self._get_color(self._button)
            p.setPen(QPen(color, 1))
            radius = max(self.line_width * 2, 10)
            for _ in range(radius):
                dx = random.gauss(0, radius / 3)
                dy = random.gauss(0, radius / 3)
                x = int(self._pos.x() + dx)
                y = int(self._pos.y() + dy)
                if 0 <= x < layer.width and 0 <= y < layer.height:
                    p.drawPoint(x, y)
            p.end()
            self._canvas.update()
        except Exception:
            log.exception("Error in airbrush spray")
            self._timer.stop()
            self._spraying = False
