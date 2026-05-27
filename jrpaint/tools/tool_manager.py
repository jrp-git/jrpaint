from PyQt6.QtCore import QObject, pyqtSignal
from .base_tool import BaseTool


class ToolManager(QObject):
    """Manages registered tools and tracks the active tool."""

    tool_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: dict[str, BaseTool] = {}
        self._active_name: str = ""

    def register(self, name: str, tool: BaseTool):
        self._tools[name] = tool

    def set_active(self, name: str):
        if name not in self._tools:
            return
        if self._active_name and self._active_name in self._tools:
            self._tools[self._active_name].on_deactivate()
        self._active_name = name
        self._tools[name].on_activate()
        self.tool_changed.emit(name)

    @property
    def active(self) -> BaseTool | None:
        return self._tools.get(self._active_name)

    @property
    def active_name(self) -> str:
        return self._active_name

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)
