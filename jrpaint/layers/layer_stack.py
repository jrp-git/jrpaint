from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPainter, QColor

from .layer import Layer


class LayerStack(QObject):
    """Manages an ordered stack of layers with compositing."""

    layers_changed = pyqtSignal()
    active_layer_changed = pyqtSignal(int)

    def __init__(self, width: int = 800, height: int = 600, parent=None):
        super().__init__(parent)
        self._width = width
        self._height = height
        self._layers: list[Layer] = []
        self._active_index = 0
        # Track which layer was last modified for global undo
        self._undo_log: list[int] = []
        self._redo_log: list[int] = []

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def layers(self) -> list[Layer]:
        return self._layers

    @property
    def active_index(self) -> int:
        return self._active_index

    @active_index.setter
    def active_index(self, index: int):
        if 0 <= index < len(self._layers):
            self._active_index = index
            self.active_layer_changed.emit(index)

    @property
    def active_layer(self) -> Layer | None:
        if 0 <= self._active_index < len(self._layers):
            return self._layers[self._active_index]
        return None

    def add_layer(self, name: str | None = None, index: int | None = None,
                  fill: QColor | None = None) -> Layer:
        if name is None:
            name = f"Layer {len(self._layers) + 1}"
        layer = Layer(name, self._width, self._height, fill=fill)
        if index is None:
            index = self._active_index
        self._layers.insert(index, layer)
        self._active_index = index
        self.layers_changed.emit()
        self.active_layer_changed.emit(self._active_index)
        return layer

    def remove_layer(self, index: int):
        if len(self._layers) <= 1:
            return
        self._layers.pop(index)
        if self._active_index >= len(self._layers):
            self._active_index = len(self._layers) - 1
        self.layers_changed.emit()
        self.active_layer_changed.emit(self._active_index)

    def move_layer(self, from_idx: int, to_idx: int):
        if from_idx == to_idx:
            return
        layer = self._layers.pop(from_idx)
        self._layers.insert(to_idx, layer)
        self._active_index = to_idx
        self.layers_changed.emit()
        self.active_layer_changed.emit(self._active_index)

    def duplicate_layer(self, index: int):
        src = self._layers[index]
        layer = Layer(f"{src.name} copy", self._width, self._height)
        layer.image = src.image.copy()
        layer.opacity = src.opacity
        layer.visible = src.visible
        layer.offset_x = src.offset_x
        layer.offset_y = src.offset_y
        self._layers.insert(index, layer)
        self._active_index = index
        self.layers_changed.emit()
        self.active_layer_changed.emit(self._active_index)

    def merge_down(self, index: int):
        if index >= len(self._layers) - 1:
            return
        upper = self._layers[index]
        lower = self._layers[index + 1]
        lower.snapshot()
        p = QPainter(lower.image)
        p.setOpacity(upper.opacity)
        # Account for relative offset between layers
        dx = upper.offset_x - lower.offset_x
        dy = upper.offset_y - lower.offset_y
        p.drawImage(dx, dy, upper.image)
        p.end()
        self._layers.pop(index)
        self._active_index = index
        if self._active_index >= len(self._layers):
            self._active_index = len(self._layers) - 1
        self.layers_changed.emit()
        self.active_layer_changed.emit(self._active_index)

    def composite(self) -> QImage:
        """Composite all visible layers into a single image."""
        result = QImage(self._width, self._height, QImage.Format.Format_ARGB32)
        result.fill(Qt.GlobalColor.transparent)
        p = QPainter(result)
        # Bottom layer is last in list, top layer is first
        for layer in reversed(self._layers):
            if layer.visible and not layer.image.isNull():
                p.setOpacity(layer.opacity)
                p.drawImage(layer.offset_x, layer.offset_y, layer.image)
        p.end()
        return result

    def flatten(self) -> QImage:
        return self.composite()

    def snapshot_active(self):
        """Take undo snapshot of the active layer and log it."""
        layer = self.active_layer
        if layer:
            layer.snapshot()
            self._undo_log.append(self._active_index)
            self._redo_log.clear()

    def global_undo(self) -> bool:
        if not self._undo_log:
            return False
        layer_idx = self._undo_log.pop()
        if 0 <= layer_idx < len(self._layers):
            if self._layers[layer_idx].undo():
                self._redo_log.append(layer_idx)
                self.layers_changed.emit()
                return True
        return False

    def global_redo(self) -> bool:
        if not self._redo_log:
            return False
        layer_idx = self._redo_log.pop()
        if 0 <= layer_idx < len(self._layers):
            if self._layers[layer_idx].redo():
                self._undo_log.append(layer_idx)
                self.layers_changed.emit()
                return True
        return False

    def resize_all(self, width: int, height: int):
        self._width = width
        self._height = height
        for layer in self._layers:
            layer.resize(width, height)
        self.layers_changed.emit()
