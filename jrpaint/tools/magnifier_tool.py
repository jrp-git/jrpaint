from PyQt6.QtCore import Qt, QPoint

from .base_tool import BaseTool


class MagnifierTool(BaseTool):
    name = "magnifier"
    icon_text = "\U0001F50D"
    tooltip = "Magnifier"
    cursor = Qt.CursorShape.CrossCursor

    ZOOM_LEVELS = [1.0, 2.0, 4.0, 8.0]

    def __init__(self, canvas):
        super().__init__(canvas)

    def on_press(self, pos, button, layer):
        current = self._canvas.zoom
        if button == Qt.MouseButton.LeftButton:
            # Zoom in
            for level in self.ZOOM_LEVELS:
                if level > current:
                    self._canvas.set_zoom(level)
                    return
        else:
            # Zoom out
            for level in reversed(self.ZOOM_LEVELS):
                if level < current:
                    self._canvas.set_zoom(level)
                    return

    def on_move(self, pos, button, layer):
        pass

    def on_release(self, pos, button, layer):
        pass
