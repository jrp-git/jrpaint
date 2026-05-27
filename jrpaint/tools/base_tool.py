from abc import ABC, abstractmethod
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QPainter, QPen, QColor


class BaseTool(ABC):
    """Abstract base for all drawing/selection tools."""

    name: str = ""
    icon_text: str = ""
    tooltip: str = ""
    cursor = Qt.CursorShape.CrossCursor

    def __init__(self, canvas):
        self._canvas = canvas

    @property
    def fg_color(self) -> QColor:
        return self._canvas.fg_color

    @property
    def bg_color(self) -> QColor:
        return self._canvas.bg_color

    @property
    def line_width(self) -> int:
        return self._canvas.line_width

    @property
    def fill_mode(self) -> int:
        return self._canvas.fill_mode

    @abstractmethod
    def on_press(self, pos: QPoint, button: Qt.MouseButton, layer) -> None:
        ...

    @abstractmethod
    def on_move(self, pos: QPoint, button: Qt.MouseButton, layer) -> None:
        ...

    @abstractmethod
    def on_release(self, pos: QPoint, button: Qt.MouseButton, layer) -> None:
        ...

    def paint_preview(self, painter: QPainter) -> None:
        """Draw a live preview overlay (e.g., rubber-band shape)."""
        pass

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def _get_color(self, button: Qt.MouseButton) -> QColor:
        """Left button = foreground, right button = background."""
        if button == Qt.MouseButton.RightButton:
            return self.bg_color
        return self.fg_color

    def _is_transparent(self, button: Qt.MouseButton) -> bool:
        """Check if the active color is fully transparent."""
        return self._get_color(button).alpha() == 0

    def _setup_painter_for_color(self, p: QPainter, button: Qt.MouseButton,
                                  width: int = 1,
                                  cap=Qt.PenCapStyle.RoundCap,
                                  join=Qt.PenJoinStyle.RoundJoin):
        """Configure a QPainter for the active color, using Clear mode for transparent."""
        color = self._get_color(button)
        if color.alpha() == 0:
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        pen = QPen(color, width, Qt.PenStyle.SolidLine, cap, join)
        p.setPen(pen)
