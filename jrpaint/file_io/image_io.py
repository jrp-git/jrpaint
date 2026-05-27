from PyQt6.QtGui import QImage, QColor, QPainter
from PyQt6.QtCore import Qt

from ..canvas.canvas_model import CanvasModel


def load_image(path: str, model: CanvasModel) -> bool:
    """Load an image file into the model as a single layer."""
    image = QImage(path)
    if image.isNull():
        return False
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    model.new_document(image.width(), image.height())
    layer = model.layer_stack.layers[0]
    layer.image = image
    layer.name = "Background"
    model.file_path = path
    model.modified = False
    return True


def save_image(path: str, model: CanvasModel) -> bool:
    """Save the composited image (flattened) to a file."""
    composite = model.layer_stack.flatten()
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "png"

    if ext in ("jpg", "jpeg", "bmp"):
        # No alpha — composite onto white
        opaque = QImage(composite.width(), composite.height(),
                        QImage.Format.Format_RGB32)
        opaque.fill(QColor(255, 255, 255))
        p = QPainter(opaque)
        p.drawImage(0, 0, composite)
        p.end()
        return opaque.save(path)
    else:
        return composite.save(path)
