import logging

from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QSize, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QFont, QColor, QFontMetrics, QImage, QTextCursor,
    QMouseEvent,
)
from PyQt6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel

from .base_tool import BaseTool

log = logging.getLogger(__name__)


class FloatingTextWidget(QWidget):
    """Container widget with a drag handle bar + text editor."""

    moved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Drag handle bar
        self._handle = QWidget()
        self._handle.setFixedHeight(14)
        self._handle.setStyleSheet(
            "background: #2a82da; border-top-left-radius: 3px; "
            "border-top-right-radius: 3px;"
        )
        self._handle.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(self._handle)

        # Handle label
        self._handle_label = QLabel("  drag to move")
        self._handle_label.setStyleSheet(
            "color: rgba(255,255,255,180); font-size: 9px; background: transparent;"
        )
        self._handle_label.setFixedHeight(12)
        self._handle.setLayout(QHBoxLayout())
        self._handle.layout().setContentsMargins(0, 0, 0, 0)
        self._handle.layout().addWidget(self._handle_label)

        # Text editor
        self.editor = QTextEdit()
        self.editor.setFrameStyle(0)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor.setStyleSheet(
            "QTextEdit { background: rgba(255,255,255,200); "
            "border: 1px dashed #2a82da; border-top: none; "
            "color: black; padding: 4px; }"
        )
        self.editor.setAcceptRichText(False)
        self.editor.setMinimumSize(80, 30)
        layout.addWidget(self.editor)

        # Drag state
        self._drag_active = False
        self._drag_start = QPoint()

        self._handle.mousePressEvent = self._handle_press
        self._handle.mouseMoveEvent = self._handle_move
        self._handle.mouseReleaseEvent = self._handle_release

    def _handle_press(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_start = event.globalPosition().toPoint() - self.pos()

    def _handle_move(self, event: QMouseEvent):
        if self._drag_active:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            self.move(new_pos)
            self.moved.emit()

    def _handle_release(self, event: QMouseEvent):
        self._drag_active = False

    def set_font_props(self, font: QFont, color: QColor):
        self.editor.setFont(font)
        self.editor.setTextColor(color)
        # Update the stylesheet color to match
        r, g, b = color.red(), color.green(), color.blue()
        self.editor.setStyleSheet(
            f"QTextEdit {{ background: rgba(255,255,255,200); "
            f"border: 1px dashed #2a82da; border-top: none; "
            f"color: rgb({r},{g},{b}); padding: 4px; }}"
        )
        # Re-apply to existing text
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = cursor.charFormat()
        fmt.setFont(font)
        fmt.setForeground(color)
        cursor.mergeCharFormat(fmt)
        cursor.clearSelection()
        self.editor.setTextCursor(cursor)


class TextTool(BaseTool):
    name = "text"
    icon_text = "A"
    tooltip = "Text \u2014 Add text to the image"
    cursor = Qt.CursorShape.IBeamCursor

    def __init__(self, canvas):
        super().__init__(canvas)
        self.font = QFont("Arial", 24)
        self.font.setKerning(True)
        self._widget: FloatingTextWidget | None = None
        self._canvas_pos = QPoint(0, 0)
        self._committed = True
        self._color = QColor(0, 0, 0)

    # ── Font property setters (called from tool options bar) ─────────

    def set_font_family(self, family: str):
        self.font.setFamily(family)
        self._update_editor()

    def set_font_size(self, size: int):
        self.font.setPointSize(max(1, size))
        self._update_editor()
        self._resize_editor()

    def set_bold(self, bold: bool):
        self.font.setBold(bold)
        self._update_editor()

    def set_italic(self, italic: bool):
        self.font.setItalic(italic)
        self._update_editor()

    def set_kerning(self, enabled: bool):
        self.font.setKerning(enabled)
        self._update_editor()

    def set_letter_spacing(self, spacing: float):
        self.font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        self._update_editor()

    def update_color(self, color: QColor):
        """Called when foreground color changes while editor is open."""
        self._color = color
        self._update_editor()

    def _update_editor(self):
        if self._widget:
            self._widget.set_font_props(self._scaled_font(), self._color)

    # ── Helpers ──────────────────────────────────────────────────────

    def _scaled_font(self) -> QFont:
        f = QFont(self.font)
        f.setPointSizeF(self.font.pointSizeF() * self._canvas.zoom)
        return f

    def _screen_pos(self) -> QPoint:
        z = self._canvas.zoom
        return QPoint(int(self._canvas_pos.x() * z),
                      int(self._canvas_pos.y() * z))

    def _resize_editor(self):
        if not self._widget:
            return
        doc = self._widget.editor.document()
        doc.setTextWidth(-1)
        w = max(120, int(doc.idealWidth()) + 24)
        h = max(30, int(doc.size().height()) + 12)
        self._widget.setFixedSize(w, h + 14)  # +14 for drag handle
        self._widget.editor.setFixedSize(w, h)

    def _pos_from_widget(self):
        """Update canvas_pos from current widget screen position."""
        if self._widget:
            z = self._canvas.zoom
            sp = self._widget.pos()
            self._canvas_pos = QPoint(int(sp.x() / z), int((sp.y() + 14) / z))

    # ── Tool interface ───────────────────────────────────────────────

    def on_press(self, pos, button, layer):
        if layer.locked:
            return

        # If editor is open and click is outside it, commit the text
        if self._widget and not self._committed:
            self._pos_from_widget()
            self._commit(layer)
            return

        # Place a new text editor
        self._canvas_pos = pos
        self._color = self.fg_color
        self._create_editor()

    def on_move(self, pos, button, layer):
        pass

    def on_release(self, pos, button, layer):
        pass

    def _create_editor(self):
        if self._widget:
            self._widget.deleteLater()

        self._widget = FloatingTextWidget(self._canvas)
        self._widget.set_font_props(self._scaled_font(), self._color)
        self._widget.move(self._screen_pos() - QPoint(0, 14))  # offset for handle
        self._widget.setFixedSize(200, 54)
        self._widget.editor.setFixedSize(200, 40)
        self._widget.show()
        self._widget.editor.setFocus()
        self._widget.editor.textChanged.connect(self._on_text_changed)
        self._widget.moved.connect(self._pos_from_widget)
        self._committed = False

    def _on_text_changed(self):
        self._resize_editor()

    def _commit(self, layer=None):
        if not self._widget or self._committed:
            return

        text = self._widget.editor.toPlainText()
        if not text.strip():
            self._cleanup_editor()
            return

        if layer is None:
            layer = self._canvas.model.layer_stack.active_layer
        if not layer:
            self._cleanup_editor()
            return

        self._canvas.model.layer_stack.snapshot_active()

        p = QPainter(layer.image)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setFont(self.font)
        p.setPen(QPen(self._color))

        fm = QFontMetrics(self.font)
        x = self._canvas_pos.x()
        y = self._canvas_pos.y() + fm.ascent()
        for line in text.split('\n'):
            p.drawText(x, y, line)
            y += fm.lineSpacing()

        p.end()
        self._canvas.model.modified = True
        self._cleanup_editor()
        self._canvas.update()

    def _cleanup_editor(self):
        if self._widget:
            self._widget.hide()
            self._widget.deleteLater()
            self._widget = None
        self._committed = True

    def on_deactivate(self):
        if self._widget:
            self._pos_from_widget()
        layer = self._canvas.model.layer_stack.active_layer
        if layer:
            self._commit(layer)
        self._cleanup_editor()

    def paint_preview(self, painter: QPainter):
        pass
