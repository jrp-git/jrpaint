from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QMouseEvent, QPaintEvent


CLASSIC_COLORS = [
    "#000000", "#808080", "#800000", "#808000", "#008000", "#008080", "#000080",
    "#800080", "#808040", "#004040", "#0080FF", "#004080", "#4000FF", "#804000",
    "#FFFFFF", "#C0C0C0", "#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF",
    "#FF00FF", "#FFFF80", "#00FF80", "#80FFFF", "#8080FF", "#FF0080", "#FF8040",
]


class FGBGColorWidget(QWidget):
    fg_changed = pyqtSignal(QColor)
    bg_changed = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fg_color = QColor("#000000")
        self.bg_color = QColor("#FFFFFF")
        self.setFixedSize(30, 30)
        self.setToolTip("Click to swap foreground/background colors")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _draw_checker(self, p: QPainter, x: int, y: int, w: int, h: int):
        """Draw a checkerboard pattern to indicate transparency."""
        cs = 4
        for cy in range(y, y + h, cs):
            for cx in range(x, x + w, cs):
                if ((cx - x) // cs + (cy - y) // cs) % 2 == 0:
                    p.fillRect(cx, cy, cs, cs, QColor(255, 255, 255))
                else:
                    p.fillRect(cx, cy, cs, cs, QColor(192, 192, 192))

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        # Background square
        if self.bg_color.alpha() < 255:
            self._draw_checker(p, 8, 8, 18, 18)
        p.setPen(QPen(QColor("#666666"), 1))
        p.setBrush(QBrush(self.bg_color))
        p.drawRect(8, 8, 18, 18)
        # Foreground square
        if self.fg_color.alpha() < 255:
            self._draw_checker(p, 2, 2, 18, 18)
        p.setPen(QPen(QColor("#666666"), 1))
        p.setBrush(QBrush(self.fg_color))
        p.drawRect(2, 2, 18, 18)
        p.end()

    def mousePressEvent(self, event: QMouseEvent):
        self.fg_color, self.bg_color = self.bg_color, self.fg_color
        self.fg_changed.emit(self.fg_color)
        self.bg_changed.emit(self.bg_color)
        self.update()

    def set_fg(self, color: QColor):
        self.fg_color = color
        self.fg_changed.emit(color)
        self.update()

    def set_bg(self, color: QColor):
        self.bg_color = color
        self.bg_changed.emit(color)
        self.update()


class ColorPalette(QWidget):
    foreground_changed = pyqtSignal(QColor)
    background_changed = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        self.fgbg = FGBGColorWidget()
        self.fgbg.fg_changed.connect(self.foreground_changed.emit)
        self.fgbg.bg_changed.connect(self.background_changed.emit)
        layout.addWidget(self.fgbg)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        swatch_widget = QWidget()
        swatch_layout = QGridLayout(swatch_widget)
        swatch_layout.setContentsMargins(0, 0, 0, 0)
        swatch_layout.setSpacing(1)

        for i, hex_color in enumerate(CLASSIC_COLORS):
            row = 0 if i < 14 else 1
            col = i if i < 14 else i - 14
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #555; "
                f"padding: 0px; margin: 0px;"
            )
            btn.setToolTip(hex_color)
            color = QColor(hex_color)
            btn.mousePressEvent = lambda e, c=color: self._swatch_clicked(e, c)
            swatch_layout.addWidget(btn, row, col)

        layout.addWidget(swatch_widget)

        # Transparent color button
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep2)

        self._trans_btn = QPushButton()
        self._trans_btn.setFixedSize(20, 20)
        self._trans_btn.setToolTip("Transparent")
        self._trans_btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 #fff, stop:0.49 #fff,"
            "    stop:0.5 #f44, stop:1.0 #f44);"
            "  border: 1px solid #555; padding: 0px; margin: 0px;"
            "}"
        )
        transparent = QColor(0, 0, 0, 0)
        self._trans_btn.mousePressEvent = lambda e: self._swatch_clicked(e, transparent)
        layout.addWidget(self._trans_btn)

        layout.addStretch()

    def _swatch_clicked(self, event: QMouseEvent, color: QColor):
        if event.button() == Qt.MouseButton.LeftButton:
            self.fgbg.set_fg(color)
            self.foreground_changed.emit(color)
        elif event.button() == Qt.MouseButton.RightButton:
            self.fgbg.set_bg(color)
            self.background_changed.emit(color)
