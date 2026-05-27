import math
from enum import Enum, auto

from PyQt6.QtCore import QRect, QRectF, QPoint, QPointF, Qt
from PyQt6.QtGui import QImage, QColor, QTransform


class Handle(Enum):
    NONE = auto()
    TOP_LEFT = auto()
    TOP = auto()
    TOP_RIGHT = auto()
    RIGHT = auto()
    BOTTOM_RIGHT = auto()
    BOTTOM = auto()
    BOTTOM_LEFT = auto()
    LEFT = auto()
    ROTATE = auto()  # Outside the corner — rotation handle


HANDLE_SIZE = 7  # Pixels for each grab handle
ROTATE_DISTANCE = 16  # Pixels outside the corner for the rotation handle


class SelectionState:
    """Tracks rectangular selection with move, resize, and rotate."""

    def __init__(self):
        self.active = False
        self.rect = QRect()
        self.content: QImage | None = None
        self.offset = QPoint(0, 0)
        self.rotation = 0.0  # Degrees
        self._dash_offset = 0

    def set_rect(self, rect: QRect):
        self.rect = rect.normalized()
        self.active = not self.rect.isEmpty()

    def clear(self):
        self.active = False
        self.rect = QRect()
        self.content = None
        self.offset = QPoint(0, 0)
        self.rotation = 0.0

    def contains(self, point: QPoint) -> bool:
        if not self.active:
            return False
        r = self.effective_rect()
        if self.rotation == 0.0:
            return r.contains(point)
        # For rotated selections, test against the un-rotated space
        center = r.center()
        t = QTransform()
        t.translate(center.x(), center.y())
        t.rotate(-self.rotation)
        t.translate(-center.x(), -center.y())
        mapped = t.map(QPointF(point))
        return r.contains(mapped.toPoint())

    @property
    def dash_offset(self) -> int:
        return self._dash_offset

    def advance_marching_ants(self):
        self._dash_offset = (self._dash_offset + 1) % 8

    def has_content(self) -> bool:
        return self.content is not None

    def effective_rect(self) -> QRect:
        return self.rect.translated(self.offset)

    def hit_test_handle(self, point: QPoint) -> Handle:
        """Test if a point hits a resize/rotate handle. Returns Handle enum."""
        if not self.active:
            return Handle.NONE

        rect = self.effective_rect()

        # If rotated, transform the point into un-rotated space
        if self.rotation != 0.0:
            center = rect.center()
            t = QTransform()
            t.translate(center.x(), center.y())
            t.rotate(-self.rotation)
            t.translate(-center.x(), -center.y())
            pf = t.map(QPointF(point))
            px, py = pf.x(), pf.y()
        else:
            px, py = point.x(), point.y()

        hs = HANDLE_SIZE
        left, top = rect.left(), rect.top()
        right, bottom = rect.right(), rect.bottom()
        cx, cy = (left + right) / 2, (top + bottom) / 2

        # Check rotation handle (outside top-right corner)
        rot_x = right + ROTATE_DISTANCE
        rot_y = top - ROTATE_DISTANCE
        if abs(px - rot_x) <= hs and abs(py - rot_y) <= hs:
            return Handle.ROTATE

        # Corner handles
        if abs(px - left) <= hs and abs(py - top) <= hs:
            return Handle.TOP_LEFT
        if abs(px - right) <= hs and abs(py - top) <= hs:
            return Handle.TOP_RIGHT
        if abs(px - left) <= hs and abs(py - bottom) <= hs:
            return Handle.BOTTOM_LEFT
        if abs(px - right) <= hs and abs(py - bottom) <= hs:
            return Handle.BOTTOM_RIGHT

        # Edge handles (midpoints)
        if abs(px - cx) <= hs and abs(py - top) <= hs:
            return Handle.TOP
        if abs(px - cx) <= hs and abs(py - bottom) <= hs:
            return Handle.BOTTOM
        if abs(px - left) <= hs and abs(py - cy) <= hs:
            return Handle.LEFT
        if abs(px - right) <= hs and abs(py - cx) <= hs:
            return Handle.RIGHT

        return Handle.NONE

    def handle_positions(self) -> dict[Handle, QPointF]:
        """Returns the positions of all resize/rotate handles."""
        rect = QRectF(self.effective_rect())
        cx = rect.center().x()
        cy = rect.center().y()
        positions = {
            Handle.TOP_LEFT: rect.topLeft(),
            Handle.TOP: QPointF(cx, rect.top()),
            Handle.TOP_RIGHT: rect.topRight(),
            Handle.RIGHT: QPointF(rect.right(), cy),
            Handle.BOTTOM_RIGHT: rect.bottomRight(),
            Handle.BOTTOM: QPointF(cx, rect.bottom()),
            Handle.BOTTOM_LEFT: rect.bottomLeft(),
            Handle.LEFT: QPointF(rect.left(), cy),
            Handle.ROTATE: QPointF(rect.right() + ROTATE_DISTANCE,
                                   rect.top() - ROTATE_DISTANCE),
        }
        return positions

    def apply_resize(self, handle: Handle, delta_x: int, delta_y: int):
        """Resize the effective rect by moving the given handle."""
        r = self.effective_rect()
        left, top = r.left(), r.top()
        right, bottom = r.right(), r.bottom()

        if handle in (Handle.TOP_LEFT, Handle.TOP, Handle.TOP_RIGHT):
            top += delta_y
        if handle in (Handle.BOTTOM_LEFT, Handle.BOTTOM, Handle.BOTTOM_RIGHT):
            bottom += delta_y
        if handle in (Handle.TOP_LEFT, Handle.LEFT, Handle.BOTTOM_LEFT):
            left += delta_x
        if handle in (Handle.TOP_RIGHT, Handle.RIGHT, Handle.BOTTOM_RIGHT):
            right += delta_x

        # Enforce minimum size
        if right - left < 2:
            right = left + 2
        if bottom - top < 2:
            bottom = top + 2

        new_rect = QRect(QPoint(left, top), QPoint(right, bottom))
        self.rect = QRect(QPoint(0, 0), new_rect.size())
        self.offset = new_rect.topLeft()

        # Scale the content to match
        if self.content and not self.content.isNull():
            self.content = self.content.scaled(
                new_rect.width(), new_rect.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

    def get_transformed_content(self) -> QImage | None:
        """Returns the content with rotation applied."""
        if not self.content or self.content.isNull():
            return self.content
        if self.rotation == 0.0:
            return self.content
        t = QTransform()
        t.rotate(self.rotation)
        return self.content.transformed(t, Qt.TransformationMode.SmoothTransformation)
