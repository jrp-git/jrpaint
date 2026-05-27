import json
import zipfile
import io
import tempfile
import os

from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import Qt, QBuffer, QIODevice

from ..canvas.canvas_model import CanvasModel
from ..layers.layer import Layer


def save_jrp(path: str, model: CanvasModel) -> bool:
    """Save layered document as .jrp (ZIP with PNGs + manifest)."""
    try:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest = {
                "version": 1,
                "app": "JRPaint",
                "canvas": {
                    "width": model.width,
                    "height": model.height,
                },
                "layers": [],
            }
            for i, layer in enumerate(model.layer_stack.layers):
                layer_file = f"layers/{i}.png"
                manifest["layers"].append({
                    "index": i,
                    "name": layer.name,
                    "visible": layer.visible,
                    "opacity": layer.opacity,
                    "locked": layer.locked,
                    "offset_x": layer.offset_x,
                    "offset_y": layer.offset_y,
                    "file": layer_file,
                })
                # Write layer image as PNG to zip
                buf = QBuffer()
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                layer.image.save(buf, "PNG")
                zf.writestr(layer_file, buf.data().data())

            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        return True
    except Exception:
        return False


def load_jrp(path: str, model: CanvasModel) -> bool:
    """Load a .jrp layered document."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            canvas = manifest["canvas"]
            width = canvas["width"]
            height = canvas["height"]

            model.layer_stack._layers.clear()
            model.layer_stack._width = width
            model.layer_stack._height = height

            for layer_info in manifest["layers"]:
                layer = Layer(
                    layer_info["name"],
                    width,
                    height,
                )
                layer.visible = layer_info.get("visible", True)
                layer.opacity = layer_info.get("opacity", 1.0)
                layer.locked = layer_info.get("locked", False)
                layer.offset_x = layer_info.get("offset_x", 0)
                layer.offset_y = layer_info.get("offset_y", 0)

                # Load image
                png_data = zf.read(layer_info["file"])
                layer.image.loadFromData(png_data, "PNG")

                model.layer_stack._layers.append(layer)

            if not model.layer_stack._layers:
                model.layer_stack.add_layer("Background", index=0,
                                            fill=QColor(255, 255, 255))

            model.layer_stack._active_index = 0
            model.layer_stack.layers_changed.emit()
            model.file_path = path
            model.modified = False
            return True
    except Exception:
        return False
