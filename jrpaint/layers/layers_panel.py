from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QListWidget, QListWidgetItem, QCheckBox,
    QLineEdit, QStackedWidget, QMenu,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QImage, QMouseEvent, QAction

from .layer_stack import LayerStack
from ..icon_loader import get_layer_icon


class LayerItemWidget(QWidget):
    visibility_changed = pyqtSignal(int, bool)
    name_changed = pyqtSignal(int, str)

    def __init__(self, index: int, name: str, visible: bool = True,
                 thumbnail: QImage | None = None, parent=None):
        super().__init__(parent)
        self._index = index
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Visibility toggle
        self.vis_checkbox = QCheckBox()
        self.vis_checkbox.setChecked(visible)
        self.vis_checkbox.setToolTip("Toggle visibility")
        self.vis_checkbox.setFixedSize(20, 20)
        self.vis_checkbox.toggled.connect(
            lambda checked: self.visibility_changed.emit(self._index, checked)
        )
        layout.addWidget(self.vis_checkbox)

        # Thumbnail
        thumb_label = QLabel()
        if thumbnail:
            thumb_label.setPixmap(QPixmap.fromImage(thumbnail))
        else:
            px = QPixmap(48, 36)
            px.fill(Qt.GlobalColor.white)
            thumb_label.setPixmap(px)
        thumb_label.setFixedSize(50, 38)
        thumb_label.setStyleSheet("border: 1px solid #555;")
        thumb_label.setScaledContents(True)
        layout.addWidget(thumb_label)

        # Layer name: stacked label (display) / line edit (rename)
        self._name_stack = QStackedWidget()

        self.name_label = QLabel(name)
        self.name_label.setMinimumWidth(60)
        self.name_label.setStyleSheet("color: #ddd;")
        self._name_stack.addWidget(self.name_label)  # index 0

        self.name_edit = QLineEdit(name)
        self.name_edit.setStyleSheet(
            "QLineEdit { background: #3c3c3f; color: #ddd; border: 1px solid #2a82da; }"
        )
        self.name_edit.returnPressed.connect(self._finish_rename)
        self.name_edit.editingFinished.connect(self._finish_rename)
        self._name_stack.addWidget(self.name_edit)  # index 1

        self._name_stack.setCurrentIndex(0)
        layout.addWidget(self._name_stack, 1)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click on the layer item to rename it."""
        self._start_rename()

    def _start_rename(self):
        self.name_edit.setText(self.name_label.text())
        self._name_stack.setCurrentIndex(1)
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def _finish_rename(self):
        if self._name_stack.currentIndex() != 1:
            return
        new_name = self.name_edit.text().strip()
        if new_name and new_name != self.name_label.text():
            self.name_label.setText(new_name)
            self.name_changed.emit(self._index, new_name)
        self._name_stack.setCurrentIndex(0)


class LayersPanel(QDockWidget):
    layer_selected = pyqtSignal(int)
    add_layer = pyqtSignal()
    remove_layer = pyqtSignal()
    move_up = pyqtSignal()
    move_down = pyqtSignal()
    duplicate = pyqtSignal()
    merge_down = pyqtSignal()
    opacity_changed = pyqtSignal(int)
    visibility_toggled = pyqtSignal(int, bool)
    layer_renamed = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__("Layers", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.setMinimumWidth(200)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Opacity slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        self.opacity_slider.valueChanged.connect(self._on_opacity)
        opacity_layout.addWidget(self.opacity_label)
        layout.addLayout(opacity_layout)

        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.layer_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.layer_list.setStyleSheet(
            "QListWidget { background: #2d2d30; border: 1px solid #555; }"
            "QListWidget::item:selected { background: #2a4a6b; }"
            "QListWidget::item:hover { background: #3e3e42; }"
        )
        self.layer_list.currentRowChanged.connect(self._on_row_changed)
        self.layer_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.layer_list, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        buttons = [
            ("add", "+", "Add Layer \u2014 Create a new empty layer", self.add_layer),
            ("delete", "\u2212", "Delete Layer \u2014 Remove the selected layer", self.remove_layer),
            ("move_up", "\u2191", "Move Up \u2014 Move layer up in the stack", self.move_up),
            ("move_down", "\u2193", "Move Down \u2014 Move layer down in the stack", self.move_down),
            ("duplicate", "\u29C9", "Duplicate \u2014 Make a copy of the selected layer", self.duplicate),
            ("merge_down", "\u2B73", "Merge Down \u2014 Merge into the layer below", self.merge_down),
        ]
        for icon_key, text, tooltip, signal in buttons:
            btn = QPushButton()
            btn.setFixedSize(42, 36)
            btn.setToolTip(tooltip)
            icon = get_layer_icon(icon_key, 27)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(27, 27))
            else:
                btn.setText(text)
            btn.clicked.connect(signal.emit)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setWidget(container)
        self._updating = False
        self._layer_stack: LayerStack | None = None

    def _on_opacity(self, value: int):
        self.opacity_label.setText(f"{value}%")
        self.opacity_changed.emit(value)

    def _on_row_changed(self, row: int):
        if not self._updating and row >= 0:
            self.layer_selected.emit(row)

    def _show_context_menu(self, pos: QPoint):
        item = self.layer_list.itemAt(pos)
        if not item or not self._layer_stack:
            return
        row = self.layer_list.row(item)
        if row < 0 or row >= len(self._layer_stack.layers):
            return
        layer = self._layer_stack.layers[row]

        menu = QMenu(self)
        # Rename
        rename_action = menu.addAction("Rename")
        menu.addSeparator()
        # Show/Hide
        if layer.visible:
            vis_action = menu.addAction("Hide")
        else:
            vis_action = menu.addAction("Show")
        menu.addSeparator()
        # Delete (disabled if only one layer)
        delete_action = menu.addAction("Delete")
        if len(self._layer_stack.layers) <= 1:
            delete_action.setEnabled(False)

        chosen = menu.exec(self.layer_list.mapToGlobal(pos))
        if chosen == rename_action:
            widget = self.layer_list.itemWidget(item)
            if isinstance(widget, LayerItemWidget):
                widget._start_rename()
        elif chosen == vis_action:
            self.visibility_toggled.emit(row, not layer.visible)
        elif chosen == delete_action:
            self.layer_selected.emit(row)
            self.remove_layer.emit()

    def refresh(self, layer_stack: LayerStack):
        self._layer_stack = layer_stack
        self._updating = True
        self.layer_list.clear()
        for i, layer in enumerate(layer_stack.layers):
            item = QListWidgetItem()
            thumb = layer.thumbnail(48, 36)
            widget = LayerItemWidget(i, layer.name, layer.visible, thumb)
            widget.visibility_changed.connect(self.visibility_toggled.emit)
            widget.name_changed.connect(self.layer_renamed.emit)
            item.setSizeHint(widget.sizeHint())
            self.layer_list.addItem(item)
            self.layer_list.setItemWidget(item, widget)
        # Select active layer
        if 0 <= layer_stack.active_index < self.layer_list.count():
            self.layer_list.setCurrentRow(layer_stack.active_index)
        # Update opacity slider
        active = layer_stack.active_layer
        if active:
            self.opacity_slider.setValue(int(active.opacity * 100))
        self._updating = False
