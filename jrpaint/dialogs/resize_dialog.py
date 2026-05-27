from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QDialogButtonBox, QGroupBox, QGridLayout, QComboBox,
    QCheckBox,
)


class ResizeCanvasDialog(QDialog):
    def __init__(self, current_w: int, current_h: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attributes")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        group = QGroupBox("Canvas Size")
        grid = QGridLayout(group)

        grid.addWidget(QLabel("Width:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(current_w)
        self.width_spin.setSuffix(" px")
        grid.addWidget(self.width_spin, 0, 1)

        grid.addWidget(QLabel("Height:"), 1, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(current_h)
        self.height_spin.setSuffix(" px")
        grid.addWidget(self.height_spin, 1, 1)

        layout.addWidget(group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_size(self) -> tuple[int, int]:
        return self.width_spin.value(), self.height_spin.value()


class FlipRotateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flip/Rotate")
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)

        self.combo = QComboBox()
        self.combo.addItems([
            "Flip Horizontal",
            "Flip Vertical",
            "Rotate 90\u00B0",
            "Rotate 180\u00B0",
            "Rotate 270\u00B0",
        ])
        layout.addWidget(self.combo)

        self.all_layers = QCheckBox("Apply to all layers")
        layout.addWidget(self.all_layers)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_operation(self) -> tuple[int, bool]:
        return self.combo.currentIndex(), self.all_layers.isChecked()


class StretchSkewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stretch/Skew")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        stretch_group = QGroupBox("Stretch")
        sg = QGridLayout(stretch_group)
        sg.addWidget(QLabel("Horizontal:"), 0, 0)
        self.stretch_h = QSpinBox()
        self.stretch_h.setRange(1, 500)
        self.stretch_h.setValue(100)
        self.stretch_h.setSuffix("%")
        sg.addWidget(self.stretch_h, 0, 1)
        sg.addWidget(QLabel("Vertical:"), 1, 0)
        self.stretch_v = QSpinBox()
        self.stretch_v.setRange(1, 500)
        self.stretch_v.setValue(100)
        self.stretch_v.setSuffix("%")
        sg.addWidget(self.stretch_v, 1, 1)
        layout.addWidget(stretch_group)

        skew_group = QGroupBox("Skew")
        skg = QGridLayout(skew_group)
        skg.addWidget(QLabel("Horizontal:"), 0, 0)
        self.skew_h = QSpinBox()
        self.skew_h.setRange(-89, 89)
        self.skew_h.setValue(0)
        self.skew_h.setSuffix("\u00B0")
        skg.addWidget(self.skew_h, 0, 1)
        skg.addWidget(QLabel("Vertical:"), 1, 0)
        self.skew_v = QSpinBox()
        self.skew_v.setRange(-89, 89)
        self.skew_v.setValue(0)
        self.skew_v.setSuffix("\u00B0")
        skg.addWidget(self.skew_v, 1, 1)
        layout.addWidget(skew_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> tuple[int, int, int, int]:
        return (
            self.stretch_h.value(), self.stretch_v.value(),
            self.skew_h.value(), self.skew_v.value(),
        )
