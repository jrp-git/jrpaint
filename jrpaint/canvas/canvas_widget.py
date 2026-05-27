import logging

from PyQt6.QtWidgets import QWidget, QGestureEvent, QMenu
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QRect, QPointF
from PyQt6.QtGui import QAction
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, QImage,
    QMouseEvent, QPaintEvent, QWheelEvent, QTransform,
    QNativeGestureEvent,
)

from .canvas_model import CanvasModel
from .selection import SelectionState

log = logging.getLogger(__name__)


class CanvasWidget(QWidget):
    """Main canvas widget: renders composited layers, handles tool dispatch."""

    cursor_moved = pyqtSignal(int, int)
    zoom_changed = pyqtSignal(float)
    context_cut = pyqtSignal()
    context_copy = pyqtSignal()
    context_paste = pyqtSignal()
    context_delete = pyqtSignal()
    context_select_all = pyqtSignal()

    # Smooth zoom levels for stepping via menu/magnifier
    ZOOM_STEPS = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]

    def __init__(self, model: CanvasModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.selection = SelectionState()

        # Drawing state
        self._fg_color = QColor(0, 0, 0)
        self._bg_color = QColor(255, 255, 255)
        self._line_width = 1
        self._fill_mode = 0  # 0=outline, 1=outline+fill, 2=fill only
        self._zoom = 1.0
        self._show_grid = False
        self._tool_manager = None

        # Pinch zoom tracking
        self._pinch_accumulator = 0.0

        # Checkerboard pattern for transparency
        self._checker = self._make_checker(16)

        # Marching ants timer
        self._ants_timer = QTimer(self)
        self._ants_timer.setInterval(150)
        self._ants_timer.timeout.connect(self._advance_ants)
        self._ants_timer.start()

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self._update_size()

    def set_tool_manager(self, tm):
        self._tool_manager = tm

    # ── Properties exposed to tools ──────────────────────────────────────

    @property
    def fg_color(self) -> QColor:
        return self._fg_color

    @property
    def bg_color(self) -> QColor:
        return self._bg_color

    @property
    def line_width(self) -> int:
        return self._line_width

    @line_width.setter
    def line_width(self, w: int):
        self._line_width = max(1, w)

    @property
    def fill_mode(self) -> int:
        return self._fill_mode

    @fill_mode.setter
    def fill_mode(self, m: int):
        self._fill_mode = m

    @property
    def zoom(self) -> float:
        return self._zoom

    @property
    def show_grid(self) -> bool:
        return self._show_grid

    @show_grid.setter
    def show_grid(self, val: bool):
        self._show_grid = val
        self.update()

    def set_fg_color(self, color: QColor):
        self._fg_color = color

    def set_bg_color(self, color: QColor):
        self._bg_color = color

    def set_zoom(self, level: float):
        self._zoom = max(0.25, min(level, 16.0))
        self._update_size()
        self.zoom_changed.emit(self._zoom)
        self.update()

    def zoom_in(self):
        # Step to the next discrete zoom level
        for level in self.ZOOM_STEPS:
            if level > self._zoom + 0.01:
                self.set_zoom(level)
                return
        self.set_zoom(self.ZOOM_STEPS[-1])

    def zoom_out(self):
        for level in reversed(self.ZOOM_STEPS):
            if level < self._zoom - 0.01:
                self.set_zoom(level)
                return
        self.set_zoom(self.ZOOM_STEPS[0])

    # ── Size management ──────────────────────────────────────────────────

    def _update_size(self):
        w = int(self.model.width * self._zoom)
        h = int(self.model.height * self._zoom)
        self.setFixedSize(w, h)

    def canvas_size_changed(self):
        self._update_size()
        self.update()

    # ── Coordinate conversion ────────────────────────────────────────────

    def screen_to_canvas(self, pos: QPoint) -> QPoint:
        return QPoint(int(pos.x() / self._zoom), int(pos.y() / self._zoom))

    # ── Painting ─────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        try:
            p = QPainter(self)
            p.scale(self._zoom, self._zoom)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self._zoom < 1)

            cw, ch = self.model.width, self.model.height

            # 1. Checkerboard
            for y in range(0, ch, self._checker.height()):
                for x in range(0, cw, self._checker.width()):
                    p.drawPixmap(x, y, self._checker)

            # 2. Composite layers
            composite = self.model.layer_stack.composite()
            p.drawImage(0, 0, composite)

            # 3. Tool preview overlay
            if self._tool_manager and self._tool_manager.active:
                try:
                    self._tool_manager.active.paint_preview(p)
                except Exception:
                    log.exception("Error in paint_preview")

            # 4. Grid at high zoom
            if self._show_grid and self._zoom >= 4:
                p.setPen(QPen(QColor(128, 128, 128, 60), 0))
                for x in range(0, cw + 1):
                    p.drawLine(x, 0, x, ch)
                for y in range(0, ch + 1):
                    p.drawLine(0, y, cw, y)

            # 5. Canvas border
            p.setPen(QPen(QColor(100, 100, 100), 0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(0, 0, cw - 1, ch - 1)

            p.end()
        except Exception:
            log.exception("Error in paintEvent")

    def _make_checker(self, size: int) -> QPixmap:
        px = QPixmap(size * 2, size * 2)
        p = QPainter(px)
        p.fillRect(0, 0, size * 2, size * 2, QColor(255, 255, 255))
        p.fillRect(0, 0, size, size, QColor(204, 204, 204))
        p.fillRect(size, size, size, size, QColor(204, 204, 204))
        p.end()
        return px

    def _advance_ants(self):
        if self.selection.active:
            self.selection.advance_marching_ants()
            self.update()

    # ── Coordinate helpers ────────────────────────────────────────────────

    def _tool_pos(self, canvas_pos: QPoint, layer) -> QPoint:
        """Adjust canvas position for the layer's offset.
        Drawing tools work in layer-local coordinates.
        Move tool and selection tools use canvas coordinates directly."""
        tool = self._tool_manager.active if self._tool_manager else None
        if tool and tool.name in ("move", "rect_select", "free_select",
                                   "magnifier", "pick_color"):
            return canvas_pos
        return QPoint(canvas_pos.x() - layer.offset_x,
                      canvas_pos.y() - layer.offset_y)

    # ── Mouse events ─────────────────────────────────────────────────────

    def _dispatch(self, method_name: str, pos: QPoint, button, layer):
        """Safely dispatch a tool method, logging any exceptions."""
        tool = self._tool_manager.active
        try:
            getattr(tool, method_name)(pos, button, layer)
        except Exception:
            log.exception("Error in %s.%s()", type(tool).__name__, method_name)

    def mousePressEvent(self, event: QMouseEvent):
        pos = self.screen_to_canvas(event.pos())
        layer = self.model.layer_stack.active_layer
        if layer and self._tool_manager and self._tool_manager.active:
            tool_pos = self._tool_pos(pos, layer)
            self._dispatch("on_press", tool_pos, event.button(), layer)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = self.screen_to_canvas(event.pos())
        self.cursor_moved.emit(pos.x(), pos.y())
        layer = self.model.layer_stack.active_layer
        if layer and self._tool_manager and self._tool_manager.active:
            buttons = event.buttons()
            btn = Qt.MouseButton.LeftButton
            if buttons & Qt.MouseButton.RightButton:
                btn = Qt.MouseButton.RightButton
            tool_pos = self._tool_pos(pos, layer)
            self._dispatch("on_move", tool_pos, btn, layer)

    def mouseReleaseEvent(self, event: QMouseEvent):
        pos = self.screen_to_canvas(event.pos())
        layer = self.model.layer_stack.active_layer
        if layer and self._tool_manager and self._tool_manager.active:
            tool_pos = self._tool_pos(pos, layer)
            self._dispatch("on_release", tool_pos, event.button(), layer)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        has_sel = self.selection.active

        cut_action = menu.addAction("Cut")
        cut_action.setShortcut("Ctrl+X")
        cut_action.setEnabled(has_sel)

        copy_action = menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(has_sel)

        paste_action = menu.addAction("Paste")
        paste_action.setShortcut("Ctrl+V")

        menu.addSeparator()

        delete_action = menu.addAction("Delete")
        delete_action.setShortcut("Del")
        delete_action.setEnabled(has_sel)

        menu.addSeparator()

        select_all_action = menu.addAction("Select All")
        select_all_action.setShortcut("Ctrl+A")

        chosen = menu.exec(event.globalPos())
        if chosen == cut_action:
            self.context_cut.emit()
        elif chosen == copy_action:
            self.context_copy.emit()
        elif chosen == paste_action:
            self.context_paste.emit()
        elif chosen == delete_action:
            self.context_delete.emit()
        elif chosen == select_all_action:
            self.context_select_all.emit()

    def wheelEvent(self, event: QWheelEvent):
        # Ctrl+scroll or trackpad pinch (which macOS sends as angleDelta with phase)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        elif event.phase() in (Qt.ScrollPhase.NoScrollPhase,):
            # Regular scroll, pass through
            super().wheelEvent(event)
        else:
            super().wheelEvent(event)

    def event(self, event):
        # Handle native pinch-to-zoom gestures on macOS trackpad
        try:
            if isinstance(event, QNativeGestureEvent):
                gesture_type = event.gestureType()
                if gesture_type == Qt.NativeGestureType.ZoomNativeGesture:
                    delta = event.value()
                    new_zoom = self._zoom * (1.0 + delta)
                    self.set_zoom(max(0.25, min(new_zoom, 16.0)))
                    event.accept()
                    return True
                elif gesture_type == Qt.NativeGestureType.SmartZoomNativeGesture:
                    if self._zoom < 2.0:
                        self.set_zoom(4.0)
                    else:
                        self.set_zoom(1.0)
                    event.accept()
                    return True
        except Exception:
            log.exception("Error handling gesture event")
        return super().event(event)
