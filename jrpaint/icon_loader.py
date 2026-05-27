"""Loads icon images from gui_config.json config, scaling to fit any target size."""

import json
import logging
import os

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage

log = logging.getLogger(__name__)

_config: dict | None = None
_base_dir: str = ""
_icon_cache: dict[tuple[str, int], QIcon] = {}


def _load_config():
    """Load gui_config.json once and cache it."""
    global _config, _base_dir
    if _config is not None:
        return

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "gui_config.json")
    _base_dir = os.path.join(project_root, "jrpaint", "resources", "icons")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                _config = json.load(f)
            log.info("Loaded icon config from %s", config_path)
        except Exception:
            log.exception("Failed to load gui_config.json")
            _config = {}
    else:
        log.warning("gui_config.json not found at %s", config_path)
        _config = {}


def get_theme_color(key: str, default: str = "#2D2D30") -> str:
    """Get a theme color hex string from gui_config.json. Keys: app_background, tool_button_background."""
    _load_config()
    theme = _config.get("theme", {})
    return theme.get(key, default)


def get_tool_icon(tool_name: str, size: int = 24) -> QIcon | None:
    _load_config()
    tools = _config.get("tools", {})
    filename = tools.get(tool_name)
    return _load_icon(filename, size)


def get_layer_icon(action_name: str, size: int = 20) -> QIcon | None:
    _load_config()
    layers = _config.get("layers", {})
    filename = layers.get(action_name)
    return _load_icon(filename, size)


def _load_icon(filename: str | None, size: int) -> QIcon | None:
    """Load an image file and return a QIcon scaled to fit a square of `size`."""
    if not filename:
        return None

    cache_key = (filename, size)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    path = os.path.join(_base_dir, filename)
    if not os.path.exists(path):
        log.warning("Icon file not found: %s", path)
        return None

    pixmap = QPixmap(path)
    if pixmap.isNull():
        log.warning("Failed to load icon: %s", path)
        return None

    # Scale to fit the target size, preserving aspect ratio
    scaled = pixmap.scaled(
        QSize(size, size),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    icon = QIcon(scaled)
    _icon_cache[cache_key] = icon
    return icon
