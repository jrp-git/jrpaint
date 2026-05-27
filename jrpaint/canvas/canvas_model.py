from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

from ..layers.layer_stack import LayerStack


class CanvasModel(QObject):
    """Document state: layer stack, file path, modification tracking."""

    document_modified = pyqtSignal()
    document_saved = pyqtSignal()

    def __init__(self, width: int = 800, height: int = 600, parent=None):
        super().__init__(parent)
        self.layer_stack = LayerStack(width, height, parent=self)
        self._file_path: str | None = None
        self._modified = False
        # Start with a white background layer
        self.layer_stack.add_layer("Background", index=0, fill=QColor(255, 255, 255))

    @property
    def file_path(self) -> str | None:
        return self._file_path

    @file_path.setter
    def file_path(self, path: str | None):
        self._file_path = path

    @property
    def modified(self) -> bool:
        return self._modified

    @modified.setter
    def modified(self, value: bool):
        self._modified = value
        if value:
            self.document_modified.emit()
        else:
            self.document_saved.emit()

    @property
    def width(self) -> int:
        return self.layer_stack.width

    @property
    def height(self) -> int:
        return self.layer_stack.height

    def new_document(self, width: int, height: int, bg_color: QColor | None = None):
        self.layer_stack = LayerStack(width, height, parent=self)
        fill = bg_color if bg_color else QColor(255, 255, 255)
        self.layer_stack.add_layer("Background", index=0, fill=fill)
        self._file_path = None
        self.modified = False

    def resize_canvas(self, width: int, height: int):
        self.layer_stack.resize_all(width, height)
        self.modified = True
