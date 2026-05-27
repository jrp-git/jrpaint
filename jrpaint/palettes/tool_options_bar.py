from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSpinBox, QComboBox, QFrame,
    QPushButton, QFontComboBox, QCheckBox, QDoubleSpinBox,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont


class ToolOptionsBar(QWidget):
    line_width_changed = pyqtSignal(int)
    fill_mode_changed = pyqtSignal(int)

    # Text tool signals
    font_family_changed = pyqtSignal(str)
    font_size_changed = pyqtSignal(int)
    font_bold_changed = pyqtSignal(bool)
    font_italic_changed = pyqtSignal(bool)
    font_kerning_changed = pyqtSignal(bool)
    font_spacing_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 2, 8, 2)
        self._layout.setSpacing(8)

        # --- Drawing tool controls ---
        self._label = QLabel("Line width:")
        self._layout.addWidget(self._label)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 500)
        self._width_spin.setValue(1)
        self._width_spin.setSuffix(" px")
        self._width_spin.valueChanged.connect(self.line_width_changed.emit)
        self._layout.addWidget(self._width_spin)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.Shape.VLine)
        self._sep.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(self._sep)

        self._fill_label = QLabel("Fill:")
        self._layout.addWidget(self._fill_label)
        self._fill_combo = QComboBox()
        self._fill_combo.addItems(["Outline only", "Outline + Fill", "Fill only"])
        self._fill_combo.currentIndexChanged.connect(self.fill_mode_changed.emit)
        self._layout.addWidget(self._fill_combo)

        # --- Text tool controls ---
        self._font_combo = QFontComboBox()
        self._font_combo.setCurrentFont(QFont("Arial"))
        self._font_combo.currentFontChanged.connect(
            lambda f: self.font_family_changed.emit(f.family())
        )
        self._layout.addWidget(self._font_combo)

        self._font_size = QSpinBox()
        self._font_size.setRange(4, 400)
        self._font_size.setValue(24)
        self._font_size.setSuffix(" pt")
        self._font_size.valueChanged.connect(self.font_size_changed.emit)
        self._layout.addWidget(self._font_size)

        self._bold_btn = QPushButton("B")
        self._bold_btn.setCheckable(True)
        self._bold_btn.setFixedSize(28, 24)
        self._bold_btn.setStyleSheet(
            "QPushButton { font-weight: bold; }"
            "QPushButton:checked { background: #2a82da; color: white; }"
        )
        self._bold_btn.toggled.connect(self.font_bold_changed.emit)
        self._layout.addWidget(self._bold_btn)

        self._italic_btn = QPushButton("I")
        self._italic_btn.setCheckable(True)
        self._italic_btn.setFixedSize(28, 24)
        self._italic_btn.setStyleSheet(
            "QPushButton { font-style: italic; }"
            "QPushButton:checked { background: #2a82da; color: white; }"
        )
        self._italic_btn.toggled.connect(self.font_italic_changed.emit)
        self._layout.addWidget(self._italic_btn)

        self._sep2 = QFrame()
        self._sep2.setFrameShape(QFrame.Shape.VLine)
        self._sep2.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(self._sep2)

        self._kerning_cb = QCheckBox("Kerning")
        self._kerning_cb.setChecked(True)
        self._kerning_cb.toggled.connect(self.font_kerning_changed.emit)
        self._layout.addWidget(self._kerning_cb)

        self._spacing_label = QLabel("Spacing:")
        self._layout.addWidget(self._spacing_label)

        self._spacing_spin = QDoubleSpinBox()
        self._spacing_spin.setRange(-20.0, 50.0)
        self._spacing_spin.setValue(0.0)
        self._spacing_spin.setSingleStep(0.5)
        self._spacing_spin.setSuffix(" px")
        self._spacing_spin.valueChanged.connect(self.font_spacing_changed.emit)
        self._layout.addWidget(self._spacing_spin)

        self._layout.addStretch()

        # Collect widget groups for show/hide
        self._draw_widgets = [self._label, self._width_spin]
        self._shape_widgets = [self._sep, self._fill_label, self._fill_combo]
        self._text_widgets = [
            self._font_combo, self._font_size, self._bold_btn, self._italic_btn,
            self._sep2, self._kerning_cb, self._spacing_label, self._spacing_spin,
        ]

    def set_tool(self, tool_name: str):
        is_shape = tool_name in ("rectangle", "ellipse", "rounded_rect", "polygon")
        is_line = tool_name in ("line", "curve")
        is_brush = tool_name in ("brush", "airbrush", "eraser")
        is_text = tool_name == "text"

        show_draw = is_shape or is_line or is_brush
        for w in self._draw_widgets:
            w.setVisible(show_draw)
        for w in self._shape_widgets:
            w.setVisible(is_shape)
        for w in self._text_widgets:
            w.setVisible(is_text)

        if is_brush:
            self._label.setText("Size:")
        else:
            self._label.setText("Line width:")

        # Hide the entire bar when no controls are relevant
        self.setVisible(show_draw or is_shape or is_text)
