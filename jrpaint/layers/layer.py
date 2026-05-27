from PyQt6.QtGui import QImage, QColor, QPainter
from PyQt6.QtCore import Qt


class Layer:
    """A single layer backed by a QImage with ARGB32 format."""

    MAX_UNDO = 20

    def __init__(self, name: str, width: int, height: int, fill: QColor | None = None):
        self.name = name
        self.visible = True
        self.opacity = 1.0
        self.locked = False
        self.offset_x = 0  # Layer offset relative to canvas origin
        self.offset_y = 0
        self.image = QImage(width, height, QImage.Format.Format_ARGB32)
        if fill:
            self.image.fill(fill)
        else:
            self.image.fill(Qt.GlobalColor.transparent)
        self._undo_stack: list[tuple[QImage, int, int]] = []
        self._redo_stack: list[tuple[QImage, int, int]] = []

    @property
    def width(self) -> int:
        return self.image.width()

    @property
    def height(self) -> int:
        return self.image.height()

    def snapshot(self):
        """Save current state (image + offset) for undo."""
        self._undo_stack.append((self.image.copy(), self.offset_x, self.offset_y))
        if len(self._undo_stack) > self.MAX_UNDO:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append((self.image.copy(), self.offset_x, self.offset_y))
        self.image, self.offset_x, self.offset_y = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append((self.image.copy(), self.offset_x, self.offset_y))
        self.image, self.offset_x, self.offset_y = self._redo_stack.pop()
        return True

    def clear(self):
        self.image.fill(Qt.GlobalColor.transparent)

    def resize(self, width: int, height: int):
        new_image = QImage(width, height, QImage.Format.Format_ARGB32)
        new_image.fill(Qt.GlobalColor.transparent)
        p = QPainter(new_image)
        p.drawImage(0, 0, self.image)
        p.end()
        self.image = new_image

    def thumbnail(self, width: int = 48, height: int = 36) -> QImage:
        return self.image.scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
