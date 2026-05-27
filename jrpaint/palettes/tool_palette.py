import sys

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QToolButton, QButtonGroup
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont

from ..icon_loader import get_tool_icon, get_theme_color


TOOLS = [
    ("free_select",   "\u2702", "Free-Form Select \u2014 Draw a freehand selection around an area"),
    ("rect_select",   "\u25A1", "Select \u2014 Select a rectangular area to move, copy, or delete"),
    ("eraser",        "\u2395", "Eraser \u2014 Erase parts of the image to transparent"),
    ("fill",          "\u2B22", "Paint Bucket \u2014 Fill an area with the selected color"),
    ("pick_color",    "\u2710", "Color Picker \u2014 Pick a color from the image"),
    ("magnifier",     "\U0001F50D", "Magnifier \u2014 Zoom in or out on the canvas"),
    ("pencil",        "\u270F", "Pencil \u2014 Draw freehand with a 1px line"),
    ("brush",         "\U0001F58C", "Paintbrush \u2014 Draw freehand with a variable-size brush"),
    ("airbrush",      "\u2601", "Spray Paint \u2014 Spray paint with an airbrush effect"),
    ("text",          "A",  "Text \u2014 Add text to the image"),
    ("line",          "\u2571", "Line \u2014 Draw a straight line"),
    ("curve",         "\u223F", "Curve \u2014 Draw a curved line with control points"),
    ("rectangle",     "\u25AD", "Rectangle \u2014 Draw a rectangle shape"),
    ("polygon",       "\u2B23", "Polygon \u2014 Draw a polygon by clicking vertices"),
    ("ellipse",       "\u25CB", "Ellipse \u2014 Draw an ellipse or circle"),
    ("rounded_rect",  "\u25A2", "Rounded Rectangle \u2014 Draw a rectangle with rounded corners"),
    ("move",          "\u271B", "Move Layer \u2014 Move the active layer around the canvas"),
]

ICON_SIZE = 36


class ToolPalette(QWidget):
    tool_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(96)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(1)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        font_family = "Apple Symbols" if sys.platform == "darwin" else "Segoe UI Symbol"

        for i, (name, icon_text, tooltip) in enumerate(TOOLS):
            row = i // 2
            col = i % 2
            btn = QToolButton()
            btn.setToolTip(tooltip)
            btn.setFixedSize(42, 42)
            btn.setCheckable(True)

            # Try to load an image icon from gui_config.json
            icon = get_tool_icon(name, ICON_SIZE)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
            else:
                btn.setText(icon_text)
                btn.setFont(QFont(font_family, 12))

            btn_bg = get_theme_color("tool_button_background", "#4A4A4E")
            btn.setStyleSheet(
                f"QToolButton {{ border: 1px solid #555; background: {btn_bg}; color: #ddd; }}"
                "QToolButton:checked { border: 2px solid #2a82da; background: #2a4a6b; }"
                "QToolButton:hover { background: #505054; }"
            )
            self.button_group.addButton(btn, i)
            grid.addWidget(btn, row, col)

        self.button_group.idClicked.connect(self._on_tool_clicked)
        layout.addLayout(grid)
        layout.addStretch()

        # Default to pencil
        pencil_btn = self.button_group.button(6)
        if pencil_btn:
            pencil_btn.setChecked(True)

    def _on_tool_clicked(self, tool_id: int):
        name = TOOLS[tool_id][0]
        self.tool_changed.emit(name)

    def select_tool(self, name: str):
        for i, (n, _, _) in enumerate(TOOLS):
            if n == name:
                btn = self.button_group.button(i)
                if btn:
                    btn.setChecked(True)
                    self.tool_changed.emit(name)
                return
