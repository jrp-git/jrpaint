import math
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QFileDialog, QMessageBox, QInputDialog,
    QApplication,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import (
    QAction, QKeySequence, QColor, QImage, QPainter, QTransform, QClipboard,
)

from .canvas.canvas_model import CanvasModel
from .canvas.canvas_widget import CanvasWidget
from .layers.layers_panel import LayersPanel
from .palettes.tool_palette import ToolPalette
from .palettes.color_palette import ColorPalette
from .palettes.tool_options_bar import ToolOptionsBar
from .tools.tool_manager import ToolManager
from .tools.pencil_tool import PencilTool
from .tools.brush_tool import BrushTool
from .tools.eraser_tool import EraserTool
from .tools.fill_tool import FillTool
from .tools.pick_color_tool import PickColorTool
from .tools.magnifier_tool import MagnifierTool
from .tools.line_tool import LineTool
from .tools.curve_tool import CurveTool
from .tools.rect_tool import RectTool
from .tools.ellipse_tool import EllipseTool
from .tools.rounded_rect_tool import RoundedRectTool
from .tools.polygon_tool import PolygonTool
from .tools.airbrush_tool import AirbrushTool
from .tools.text_tool import TextTool
from .tools.select_rect_tool import SelectRectTool
from .tools.select_free_tool import SelectFreeTool
from .tools.move_tool import MoveTool
from .file_io.image_io import load_image, save_image
from .file_io.jrp_format import save_jrp, load_jrp
from .dialogs.resize_dialog import ResizeCanvasDialog, FlipRotateDialog, StretchSkewDialog
from .dialogs.about_dialog import show_about


IMAGE_FILTERS = (
    "All Supported (*.png *.jpg *.jpeg *.bmp *.jrp);;"
    "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;"
    "JRPaint Layered (*.jrp);;All Files (*)"
)

SAVE_FILTERS = (
    "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;"
    "JRPaint Layered (*.jrp);;All Files (*)"
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Untitled - JRPaint")
        self.resize(1024, 768)

        # Data model
        self.model = CanvasModel(800, 600)
        self.model.document_modified.connect(self._update_title)
        self.model.document_saved.connect(self._update_title)

        # Canvas
        self.canvas_widget = CanvasWidget(self.model)

        # Tool manager
        self.tool_manager = ToolManager(self)
        self._register_tools()
        self.canvas_widget.set_tool_manager(self.tool_manager)

        # UI panels
        self.tool_options_bar = ToolOptionsBar()
        self.tool_palette = ToolPalette()
        self.color_palette = ColorPalette()
        self.layers_panel = LayersPanel(self)

        # Wire signals
        self._connect_signals()

        # Build layout
        self._build_layout()
        self._create_menus()
        self._create_status_bar()

        # Dock the layers panel
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layers_panel)
        self.layers_panel.hide()

        # Refresh layers panel
        self._refresh_layers()

        # Set default tool
        self.tool_manager.set_active("pencil")
        self.tool_options_bar.set_tool("pencil")

    # ── Tool Registration ────────────────────────────────────────────────

    def _register_tools(self):
        cw = self.canvas_widget
        tools = [
            ("pencil", PencilTool(cw)),
            ("brush", BrushTool(cw)),
            ("eraser", EraserTool(cw)),
            ("fill", FillTool(cw)),
            ("pick_color", PickColorTool(cw)),
            ("magnifier", MagnifierTool(cw)),
            ("line", LineTool(cw)),
            ("curve", CurveTool(cw)),
            ("rectangle", RectTool(cw)),
            ("ellipse", EllipseTool(cw)),
            ("rounded_rect", RoundedRectTool(cw)),
            ("polygon", PolygonTool(cw)),
            ("airbrush", AirbrushTool(cw)),
            ("text", TextTool(cw)),
            ("rect_select", SelectRectTool(cw)),
            ("free_select", SelectFreeTool(cw)),
            ("move", MoveTool(cw)),
        ]
        for name, tool in tools:
            self.tool_manager.register(name, tool)

    # ── Signal Wiring ────────────────────────────────────────────────────

    def _connect_signals(self):
        # Tool palette -> tool manager
        self.tool_palette.tool_changed.connect(self._on_tool_changed)

        # Color palette -> canvas
        self.color_palette.foreground_changed.connect(self.canvas_widget.set_fg_color)
        self.color_palette.foreground_changed.connect(self._on_fg_color_changed)
        self.color_palette.background_changed.connect(self.canvas_widget.set_bg_color)

        # Tool options -> canvas
        self.tool_options_bar.line_width_changed.connect(
            lambda w: setattr(self.canvas_widget, 'line_width', w)
        )
        self.tool_options_bar.fill_mode_changed.connect(
            lambda m: setattr(self.canvas_widget, 'fill_mode', m)
        )

        # Text tool options -> text tool
        self.tool_options_bar.font_family_changed.connect(self._on_font_changed)
        self.tool_options_bar.font_size_changed.connect(self._on_font_changed)
        self.tool_options_bar.font_bold_changed.connect(self._on_font_changed)
        self.tool_options_bar.font_italic_changed.connect(self._on_font_changed)
        self.tool_options_bar.font_kerning_changed.connect(self._on_font_changed)
        self.tool_options_bar.font_spacing_changed.connect(self._on_font_changed)

        # Canvas signals
        self.canvas_widget.cursor_moved.connect(self._on_cursor_moved)
        self.canvas_widget.zoom_changed.connect(self._on_zoom_changed)
        self.canvas_widget.context_cut.connect(self._edit_cut)
        self.canvas_widget.context_copy.connect(self._edit_copy)
        self.canvas_widget.context_paste.connect(self._edit_paste)
        self.canvas_widget.context_delete.connect(self._edit_clear_selection)
        self.canvas_widget.context_select_all.connect(self._edit_select_all)

        # Layer stack changes -> refresh panel
        self.model.layer_stack.layers_changed.connect(self._refresh_layers)
        self.model.layer_stack.layers_changed.connect(self.canvas_widget.update)

        # Layers panel signals
        self.layers_panel.layer_selected.connect(self._on_layer_selected)
        self.layers_panel.add_layer.connect(self._add_layer)
        self.layers_panel.remove_layer.connect(self._remove_layer)
        self.layers_panel.move_up.connect(self._move_layer_up)
        self.layers_panel.move_down.connect(self._move_layer_down)
        self.layers_panel.duplicate.connect(self._duplicate_layer)
        self.layers_panel.merge_down.connect(self._merge_down)
        self.layers_panel.opacity_changed.connect(self._on_opacity_changed)
        self.layers_panel.layer_renamed.connect(self._on_layer_renamed)
        self.layers_panel.visibility_toggled.connect(self._on_visibility_toggled)

    # ── Layout ───────────────────────────────────────────────────────────

    def _build_layout(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.tool_options_bar)

        middle = QHBoxLayout()
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(0)
        middle.addWidget(self.tool_palette)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.canvas_widget)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e;")
        middle.addWidget(self.scroll_area, 1)

        main_layout.addLayout(middle, 1)
        main_layout.addWidget(self.color_palette)

        self.setCentralWidget(central)

    # ── Menus ────────────────────────────────────────────────────────────

    def _create_menus(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")
        self._action(file_menu, "&New", "Ctrl+N", self._file_new)
        self._action(file_menu, "&Open...", "Ctrl+O", self._file_open)
        self._action(file_menu, "&Save", "Ctrl+S", self._file_save)
        self._action(file_menu, "Save &As...", "Ctrl+Shift+S", self._file_save_as)
        file_menu.addSeparator()
        self._action(file_menu, "E&xit", "Alt+F4", self.close)

        # Edit
        edit_menu = menubar.addMenu("&Edit")
        self._action(edit_menu, "&Undo", "Ctrl+Z", self._edit_undo)
        self._action(edit_menu, "&Redo", "Ctrl+Y", self._edit_redo)
        edit_menu.addSeparator()
        self._action(edit_menu, "Cu&t", "Ctrl+X", self._edit_cut)
        self._action(edit_menu, "&Copy", "Ctrl+C", self._edit_copy)
        self._action(edit_menu, "&Paste", "Ctrl+V", self._edit_paste)
        clear_sel_action = self._action(edit_menu, "C&lear Selection", "Delete", self._edit_clear_selection)
        # On Mac, the "Delete" key is Backspace — add it as an additional shortcut
        clear_sel_action.setShortcuts([QKeySequence("Delete"), QKeySequence("Backspace")])
        self._action(edit_menu, "Select &All", "Ctrl+A", self._edit_select_all)

        # View
        view_menu = menubar.addMenu("&View")
        self._toolbox_action = self._check_action(
            view_menu, "&Tool Box", True, self.tool_palette.setVisible)
        self._colorbox_action = self._check_action(
            view_menu, "&Color Box", True, self.color_palette.setVisible)
        self._statusbar_action = self._check_action(
            view_menu, "&Status Bar", True, lambda v: self.statusBar().setVisible(v))
        view_menu.addSeparator()
        self._layers_action = self._check_action(
            view_menu, "&Layers Panel", False, self.layers_panel.setVisible, "F7")
        self.layers_panel.visibilityChanged.connect(self._layers_action.setChecked)
        view_menu.addSeparator()
        self._action(view_menu, "Zoom &In", "Ctrl+=", lambda: self.canvas_widget.zoom_in())
        self._action(view_menu, "Zoom &Out", "Ctrl+-", lambda: self.canvas_widget.zoom_out())
        zoom_menu = view_menu.addMenu("&Zoom")
        for level in [1, 2, 4, 8]:
            self._action(zoom_menu, f"{level}x", None,
                         lambda checked, l=level: self.canvas_widget.set_zoom(float(l)))
        view_menu.addSeparator()
        self._grid_action = self._check_action(
            view_menu, "Show &Grid", False,
            lambda v: setattr(self.canvas_widget, 'show_grid', v))

        # Image
        image_menu = menubar.addMenu("&Image")
        self._action(image_menu, "&Flip/Rotate...", "Ctrl+R", self._image_flip_rotate)
        self._action(image_menu, "&Stretch/Skew...", "Ctrl+W", self._image_stretch_skew)
        image_menu.addSeparator()
        self._action(image_menu, "&Invert Colors", "Ctrl+I", self._image_invert)
        self._action(image_menu, "&Attributes...", "Ctrl+E", self._image_attributes)
        image_menu.addSeparator()
        self._action(image_menu, "&Clear Image", None, self._image_clear)

        # Colors
        colors_menu = menubar.addMenu("&Colors")
        self._action(colors_menu, "&Edit Colors...", None, self._colors_edit)

        # Help
        help_menu = menubar.addMenu("&Help")
        self._action(help_menu, "&About JRPaint", None, lambda: show_about(self))

    def _action(self, menu, text, shortcut, callback):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(callback)
        menu.addAction(a)
        return a

    def _check_action(self, menu, text, checked, callback, shortcut=None):
        a = QAction(text, self)
        a.setCheckable(True)
        a.setChecked(checked)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.toggled.connect(callback)
        menu.addAction(a)
        return a

    # ── Status Bar ───────────────────────────────────────────────────────

    def _create_status_bar(self):
        sb = self.statusBar()
        sb.setStyleSheet("QStatusBar { border-top: 1px solid #555; color: #ddd; }")

        self._pos_label = QLabel("  Pos: (0, 0)")
        self._pos_label.setMinimumWidth(120)
        sb.addPermanentWidget(self._pos_label)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        sb.addPermanentWidget(sep1)

        self._size_label = QLabel(f"  {self.model.width} x {self.model.height} px")
        self._size_label.setMinimumWidth(120)
        sb.addPermanentWidget(self._size_label)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        sb.addPermanentWidget(sep2)

        self._zoom_label = QLabel("  Zoom: 100%  ")
        sb.addPermanentWidget(self._zoom_label)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.VLine)
        sep3.setFrameShadow(QFrame.Shadow.Sunken)
        sb.addPermanentWidget(sep3)

        self._layer_label = QLabel("  Layer: Background  ")
        self._layer_label.setMinimumWidth(140)
        sb.addPermanentWidget(self._layer_label)

    def _on_cursor_moved(self, x: int, y: int):
        self._pos_label.setText(f"  Pos: ({x}, {y})")

    def _on_zoom_changed(self, zoom: float):
        self._zoom_label.setText(f"  Zoom: {int(zoom * 100)}%  ")

    # ── Tool Handling ────────────────────────────────────────────────────

    def _on_tool_changed(self, tool_name: str):
        self.tool_manager.set_active(tool_name)
        self.tool_options_bar.set_tool(tool_name)

    def _on_fg_color_changed(self, color):
        """Forward foreground color changes to the text tool if active."""
        from .tools.text_tool import TextTool
        tool = self.tool_manager.get("text")
        if isinstance(tool, TextTool):
            tool.update_color(color)

    def _on_font_changed(self, *_args):
        """Forward font option changes to the text tool."""
        from .tools.text_tool import TextTool
        tool = self.tool_manager.get("text")
        if not isinstance(tool, TextTool):
            return
        bar = self.tool_options_bar
        tool.set_font_family(bar._font_combo.currentFont().family())
        tool.set_font_size(bar._font_size.value())
        tool.set_bold(bar._bold_btn.isChecked())
        tool.set_italic(bar._italic_btn.isChecked())
        tool.set_kerning(bar._kerning_cb.isChecked())
        tool.set_letter_spacing(bar._spacing_spin.value())

    # ── Layer Operations ─────────────────────────────────────────────────

    def _refresh_layers(self):
        self.layers_panel.refresh(self.model.layer_stack)
        self._size_label.setText(
            f"  {self.model.width} x {self.model.height} px"
        )
        active = self.model.layer_stack.active_layer
        if active:
            self._layer_label.setText(f"  Layer: {active.name}  ")

    def _on_layer_selected(self, index: int):
        self.model.layer_stack.active_index = index
        self._refresh_layers()

    def _add_layer(self):
        self.model.layer_stack.add_layer()
        self.model.modified = True

    def _remove_layer(self):
        self.model.layer_stack.remove_layer(self.model.layer_stack.active_index)
        self.model.modified = True

    def _move_layer_up(self):
        idx = self.model.layer_stack.active_index
        if idx > 0:
            self.model.layer_stack.move_layer(idx, idx - 1)
            self.model.modified = True

    def _move_layer_down(self):
        idx = self.model.layer_stack.active_index
        if idx < len(self.model.layer_stack.layers) - 1:
            self.model.layer_stack.move_layer(idx, idx + 1)
            self.model.modified = True

    def _duplicate_layer(self):
        self.model.layer_stack.duplicate_layer(self.model.layer_stack.active_index)
        self.model.modified = True

    def _merge_down(self):
        self.model.layer_stack.merge_down(self.model.layer_stack.active_index)
        self.model.modified = True

    def _on_opacity_changed(self, value: int):
        layer = self.model.layer_stack.active_layer
        if layer:
            layer.opacity = value / 100.0
            self.model.layer_stack.layers_changed.emit()
            self.model.modified = True

    def _on_visibility_toggled(self, index: int, visible: bool):
        layers = self.model.layer_stack.layers
        if 0 <= index < len(layers):
            layers[index].visible = visible
            self.model.layer_stack.layers_changed.emit()
            self.model.modified = True

    def _on_layer_renamed(self, index: int, new_name: str):
        layers = self.model.layer_stack.layers
        if 0 <= index < len(layers):
            layers[index].name = new_name
            self.model.modified = True

    # ── File Operations ──────────────────────────────────────────────────

    def _confirm_save(self) -> bool:
        """Returns True if OK to proceed (saved or discarded)."""
        if not self.model.modified:
            return True
        reply = QMessageBox.question(
            self, "JRPaint",
            "Save changes to the current image?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Save:
            return self._file_save()
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _file_new(self):
        if not self._confirm_save():
            return
        dlg = ResizeCanvasDialog(self.model.width, self.model.height, self)
        if dlg.exec():
            w, h = dlg.get_size()
            self.model.new_document(w, h)
            self.canvas_widget.canvas_size_changed()
            self._refresh_layers()
            self._update_title()

    def _file_open(self):
        if not self._confirm_save():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open", "", IMAGE_FILTERS)
        if not path:
            return
        if path.lower().endswith(".jrp"):
            ok = load_jrp(path, self.model)
        else:
            ok = load_image(path, self.model)
        if ok:
            self.canvas_widget.canvas_size_changed()
            self._refresh_layers()
            self._update_title()
        else:
            QMessageBox.warning(self, "Error", f"Could not open {path}")

    def _file_save(self) -> bool:
        if self.model.file_path:
            return self._save_to(self.model.file_path)
        return self._file_save_as()

    def _file_save_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", "", SAVE_FILTERS)
        if not path:
            return False
        return self._save_to(path)

    def _save_to(self, path: str) -> bool:
        if path.lower().endswith(".jrp"):
            ok = save_jrp(path, self.model)
        else:
            if len(self.model.layer_stack.layers) > 1:
                reply = QMessageBox.question(
                    self, "JRPaint",
                    "Saving as an image will flatten all layers.\n"
                    "Layer information will be lost. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return False
            ok = save_image(path, self.model)
        if ok:
            self.model.file_path = path
            self.model.modified = False
            self._update_title()
        else:
            QMessageBox.warning(self, "Error", f"Could not save to {path}")
        return ok

    def _update_title(self):
        name = "Untitled"
        if self.model.file_path:
            name = os.path.basename(self.model.file_path)
        modified = " *" if self.model.modified else ""
        self.setWindowTitle(f"{name}{modified} - JRPaint")

    # ── Edit Operations ──────────────────────────────────────────────────

    def _edit_undo(self):
        self.model.layer_stack.global_undo()
        self.canvas_widget.update()

    def _edit_redo(self):
        self.model.layer_stack.global_redo()
        self.canvas_widget.update()

    def _edit_cut(self):
        self._edit_copy()
        self._edit_clear_selection()

    def _edit_copy(self):
        sel = self.canvas_widget.selection
        layer = self.model.layer_stack.active_layer
        if not layer:
            return
        if sel.has_content():
            # Copy the floating selection content directly
            cropped = sel.content.copy()
        elif sel.active:
            rect = sel.effective_rect()
            cropped = layer.image.copy(rect)
        else:
            cropped = layer.image.copy()
        clipboard = QApplication.clipboard()
        clipboard.setImage(cropped)

    def _edit_paste(self):
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if image.isNull():
            return
        # Grow canvas if pasted image is larger in either dimension
        new_w = max(self.model.width, image.width())
        new_h = max(self.model.height, image.height())
        if new_w != self.model.width or new_h != self.model.height:
            self.model.resize_canvas(new_w, new_h)
            self.canvas_widget.canvas_size_changed()
        # Create a new layer with the pasted content
        self.model.layer_stack.add_layer("Pasted")
        layer = self.model.layer_stack.active_layer
        if layer:
            p = QPainter(layer.image)
            p.drawImage(0, 0, image)
            p.end()
            self.model.modified = True
            self._refresh_layers()
            self.canvas_widget.update()

    def _edit_clear_selection(self):
        sel = self.canvas_widget.selection
        layer = self.model.layer_stack.active_layer
        if not layer:
            return
        if sel.has_content():
            # Discard the floating selection (pixels already removed from layer)
            sel.clear()
            self.model.modified = True
            self.canvas_widget.update()
        elif sel.active:
            # Clear the selected area on the layer
            self.model.layer_stack.snapshot_active()
            rect = sel.effective_rect()
            p = QPainter(layer.image)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            p.eraseRect(rect)
            p.end()
            sel.clear()
            self.model.modified = True
            self.canvas_widget.update()

    def _edit_select_all(self):
        from PyQt6.QtCore import QRect
        sel = self.canvas_widget.selection
        sel.set_rect(QRect(0, 0, self.model.width, self.model.height))
        self.tool_palette.select_tool("rect_select")
        self.canvas_widget.update()

    # ── Image Operations ─────────────────────────────────────────────────

    def _image_flip_rotate(self):
        dlg = FlipRotateDialog(self)
        if not dlg.exec():
            return
        op, all_layers = dlg.get_operation()
        layers = self.model.layer_stack.layers if all_layers else [
            self.model.layer_stack.active_layer]

        for layer in layers:
            if not layer:
                continue
            layer.snapshot()
            if op == 0:  # Flip H
                layer.image = layer.image.mirrored(True, False)
            elif op == 1:  # Flip V
                layer.image = layer.image.mirrored(False, True)
            elif op == 2:  # Rotate 90
                layer.image = layer.image.transformed(QTransform().rotate(90))
            elif op == 3:  # Rotate 180
                layer.image = layer.image.transformed(QTransform().rotate(180))
            elif op == 4:  # Rotate 270
                layer.image = layer.image.transformed(QTransform().rotate(270))

        self.model.modified = True
        self.model.layer_stack.layers_changed.emit()
        self.canvas_widget.update()

    def _image_stretch_skew(self):
        dlg = StretchSkewDialog(self)
        if not dlg.exec():
            return
        sh, sv, skh, skv = dlg.get_values()
        layer = self.model.layer_stack.active_layer
        if not layer:
            return
        layer.snapshot()

        w = layer.width
        h = layer.height
        new_w = int(w * sh / 100)
        new_h = int(h * sv / 100)

        transform = QTransform()
        transform.scale(sh / 100.0, sv / 100.0)
        if skh != 0:
            transform.shear(math.tan(math.radians(skh)), 0)
        if skv != 0:
            transform.shear(0, math.tan(math.radians(skv)))

        layer.image = layer.image.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.model.modified = True
        self.model.layer_stack.layers_changed.emit()
        self.canvas_widget.update()

    def _image_invert(self):
        layer = self.model.layer_stack.active_layer
        if not layer:
            return
        self.model.layer_stack.snapshot_active()
        layer.image.invertPixels()
        self.model.modified = True
        self.canvas_widget.update()

    def _image_attributes(self):
        dlg = ResizeCanvasDialog(self.model.width, self.model.height, self)
        if dlg.exec():
            w, h = dlg.get_size()
            self.model.resize_canvas(w, h)
            self.canvas_widget.canvas_size_changed()
            self._refresh_layers()

    def _image_clear(self):
        layer = self.model.layer_stack.active_layer
        if not layer:
            return
        self.model.layer_stack.snapshot_active()
        layer.clear()
        self.model.modified = True
        self.canvas_widget.update()

    # ── Colors ───────────────────────────────────────────────────────────

    def _colors_edit(self):
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(
            self.canvas_widget.fg_color, self, "Choose Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            self.canvas_widget.set_fg_color(color)
            self.color_palette.fgbg.set_fg(color)

    # ── Close Event ──────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._confirm_save():
            event.accept()
        else:
            event.ignore()
