# JRPaint — Project Context

> **IMPORTANT FOR LLMs:** This file must be kept up to date. After every session
> where changes are made to the project, update this file to reflect the current
> state — what was changed, what's working, what's broken, and any open issues.
> Read this file at the start of every session to understand where things stand.

## What Is This

JRPaint is a cross-platform desktop paint application inspired by classic
Microsoft Paint (pre-2017 version). Built with **Python 3 + PyQt6**. It extends
classic Paint with:

- Alpha channel / transparent background support
- A Photoshop-style layer system (add, delete, reorder, merge, duplicate, opacity, visibility)
- Collapsible layers panel (hidden by default to match classic Paint look, toggle with F7)
- Dark mode UI theme

## How to Run

```bash
cd /Users/jrp/Desktop/jrpaint
python3 main.py
```

## Dependencies

- **Python 3.10+** (uses `X | None` union syntax)
- **PyQt6 >= 6.5** — installed at `/opt/homebrew/lib/python3.13/site-packages/PyQt6/`
- No other dependencies. Install with: `pip install PyQt6`

## Project Structure

```
jrpaint/
├── main.py                          # Entry point, dark theme, logging, faulthandler
├── requirements.txt                 # PyQt6
├── context.md                       # THIS FILE — project context for LLMs
├── mockup.py                        # Phase 1 UI mockup (standalone, can be deleted)
├── logs/                            # Runtime logs (gitignored)
│   ├── jrpaint_YYYYMMDD_HHMMSS.log # Python-level error logs (one per run)
│   └── crash.log                    # C-level segfault tracebacks (faulthandler)
│
├── jrpaint/                         # Main package
│   ├── main_window.py               # QMainWindow — menus, layout, all signal wiring
│   │
│   ├── canvas/
│   │   ├── canvas_widget.py         # CanvasWidget — rendering, zoom, mouse dispatch
│   │   ├── canvas_model.py          # CanvasModel — document state (layer stack, file path)
│   │   └── selection.py             # SelectionState — rect, marching ants, floating content
│   │
│   ├── layers/
│   │   ├── layer.py                 # Layer — QImage wrapper, offset, undo stack
│   │   ├── layer_stack.py           # LayerStack — ordered list, compositing, global undo
│   │   └── layers_panel.py          # LayersPanel — QDockWidget UI for layer management
│   │
│   ├── tools/
│   │   ├── base_tool.py             # BaseTool ABC — interface all tools implement
│   │   ├── tool_manager.py          # ToolManager — registry, active tool switching
│   │   ├── pencil_tool.py           # Freehand 1px drawing
│   │   ├── brush_tool.py            # Variable-size brush
│   │   ├── eraser_tool.py           # Erases to transparent
│   │   ├── fill_tool.py             # Scanline flood fill
│   │   ├── pick_color_tool.py       # Eyedropper
│   │   ├── magnifier_tool.py        # Click to zoom in/out
│   │   ├── line_tool.py             # Straight line with preview
│   │   ├── curve_tool.py            # 3-step cubic bezier (classic Paint style)
│   │   ├── rect_tool.py             # Rectangle with fill modes
│   │   ├── ellipse_tool.py          # Ellipse with fill modes
│   │   ├── rounded_rect_tool.py     # Rounded rectangle with fill modes
│   │   ├── polygon_tool.py          # Click vertices, close near first point
│   │   ├── airbrush_tool.py         # Gaussian spray pattern on timer
│   │   ├── text_tool.py             # Click to place text (QInputDialog)
│   │   ├── select_rect_tool.py      # Rectangular selection, lift & move pixels
│   │   ├── select_free_tool.py      # Free-form lasso selection
│   │   └── move_tool.py             # Move active layer (changes offset_x/y)
│   │
│   ├── palettes/
│   │   ├── tool_palette.py          # Left-side 2-column tool button grid
│   │   ├── color_palette.py         # Bottom bar: FG/BG display + 28 color swatches
│   │   └── tool_options_bar.py      # Context-sensitive options (line width, fill mode)
│   │
│   ├── dialogs/
│   │   ├── resize_dialog.py         # Canvas size, flip/rotate, stretch/skew dialogs
│   │   └── about_dialog.py          # About JRPaint dialog
│   │
│   ├── file_io/
│   │   ├── image_io.py              # Load/save PNG, JPEG, BMP (flattened)
│   │   └── jrp_format.py            # .jrp layered format (ZIP of PNGs + JSON manifest)
│   │
│   └── resources/
│       ├── icons/                   # (empty — tool icons use Unicode text)
│       └── cursors/                 # (empty — uses Qt built-in cursors)
```

## Architecture Overview

### Data Flow

```
User input (mouse/keyboard)
    → CanvasWidget (converts screen coords to canvas coords, adjusts for layer offset)
        → ToolManager.active tool (on_press / on_move / on_release)
            → QPainter draws on Layer.image (QImage ARGB32)
                → LayerStack.composite() blends all visible layers
                    → CanvasWidget.paintEvent() renders to screen
```

### Key Concepts

- **Layer** (`layer.py`): Wraps a `QImage(Format_ARGB32)`. Has `offset_x`, `offset_y`
  for positioning relative to canvas. Has its own undo/redo stack that saves both the
  image and offsets.

- **LayerStack** (`layer_stack.py`): Ordered list of layers. `composite()` renders all
  visible layers bottom-to-top using `QPainter` with `CompositionMode_SourceOver`.
  Maintains a global undo log that records which layer index was modified, so
  Ctrl+Z undoes the right layer.

- **CanvasWidget** (`canvas_widget.py`): The central QWidget. Handles zoom (including
  macOS trackpad pinch via `QNativeGestureEvent`), mouse event dispatch to tools,
  checkerboard transparency pattern, and grid overlay. Tool dispatch is wrapped in
  try/except to prevent crashes.

- **Tools** (`tools/*.py`): Each tool extends `BaseTool` and implements `on_press`,
  `on_move`, `on_release`, and optionally `paint_preview` for rubber-band previews.
  Drawing tools receive layer-local coordinates (adjusted for layer offset). Move,
  selection, magnifier, and pick-color tools receive canvas coordinates.

- **Selection** (`selection.py`): Tracks a selection rectangle with marching ants.
  When the user drags inside a selection (SelectRectTool), pixels are "lifted" from
  the layer into `selection.content` (a QImage), leaving transparency. Dropping
  commits them back.

### File Formats

- **PNG/JPEG/BMP**: Flattened export via `QImage.save()`. JPEG/BMP composite onto
  white background (no alpha). PNG preserves alpha.
- **.jrp**: ZIP archive containing `manifest.json` + `layers/N.png` per layer.
  Manifest stores canvas size, layer names, visibility, opacity, locked state,
  and offset_x/offset_y.

## How to Make Changes

### Adding a New Tool

1. Create `jrpaint/tools/my_tool.py` extending `BaseTool`
2. Implement `on_press`, `on_move`, `on_release` (and `paint_preview` if needed)
3. Add the tool to the `TOOLS` list in `jrpaint/palettes/tool_palette.py`
4. Import and register it in `MainWindow._register_tools()` in `jrpaint/main_window.py`
5. If the tool needs canvas-space coords (not layer-local), add its name to the
   exception list in `CanvasWidget._tool_pos()`

### Adding a Menu Action

1. Add the action in `MainWindow._create_menus()` using `self._action(menu, text, shortcut, callback)`
2. Implement the callback method on `MainWindow`

### Modifying the UI Layout

- **Tool palette**: Edit `TOOLS` list in `jrpaint/palettes/tool_palette.py`
- **Color palette**: Edit `CLASSIC_COLORS` in `jrpaint/palettes/color_palette.py`
- **Dark theme colors**: Edit `apply_dark_theme()` in `main.py`
- **Layers panel layout**: Edit `LayersPanel.__init__()` in `jrpaint/layers/layers_panel.py`
- **Tool options bar**: Edit `ToolOptionsBar` in `jrpaint/palettes/tool_options_bar.py`

### Modifying Layer Behavior

- Layer data model: `jrpaint/layers/layer.py`
- Layer management (add/remove/reorder/composite): `jrpaint/layers/layer_stack.py`
- Layer panel UI: `jrpaint/layers/layers_panel.py`
- If you add new layer properties, also update:
  - `jrp_format.py` save/load to persist them
  - `Layer.snapshot()`/`undo()`/`redo()` to preserve them in undo history
  - `LayerStack.duplicate_layer()` to copy them

## Logging & Debugging

- Logs go to `logs/jrpaint_YYYYMMDD_HHMMSS.log` (one per run) and stderr
- C-level crash tracebacks go to `logs/crash.log` (via `faulthandler`)
- Tool errors during mouse events are caught and logged (app keeps running)
- `paintEvent` errors are caught and logged
- Uncaught Python exceptions show a dialog with "Copy to Clipboard" button
- To increase verbosity, change `level=logging.DEBUG` in `main.py`

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New document |
| Ctrl+O | Open file |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+X | Cut |
| Ctrl+C | Copy |
| Ctrl+V | Paste (creates new layer, grows canvas if needed) |
| Ctrl+A | Select All |
| Delete / Backspace | Clear Selection |
| Ctrl+= | Zoom In |
| Ctrl+- | Zoom Out |
| Ctrl+Scroll | Zoom |
| Trackpad Pinch | Smooth zoom |
| F7 | Toggle Layers Panel |
| Ctrl+R | Flip/Rotate |
| Ctrl+W | Stretch/Skew |
| Ctrl+I | Invert Colors |
| Ctrl+E | Canvas Attributes (resize) |

## Current Status (2026-04-17)

### Working Features
- All 17 tools (pencil, brush, eraser, fill, color picker, magnifier, line, curve,
  rectangle, ellipse, rounded rectangle, polygon, airbrush, text, rect select,
  free-form select, move layer)
- Layer system (add, delete, reorder, duplicate, merge down, opacity, visibility,
  **rename by double-clicking** the layer name in the panel)
- Layer offsets (move layers relative to each other)
- Selection with lift-and-move, **resize** (drag corner/edge handles), and
  **rotate** (drag the rotation handle outside the top-right corner)
- Copy/paste with clipboard (paste creates new layer, canvas auto-grows)
- Undo/redo (per-layer snapshots with global undo log)
- File I/O: PNG, JPEG, BMP (flattened), .jrp (layered ZIP format)
- Image operations: flip, rotate, stretch, skew, invert colors, resize canvas, clear
- Zoom: menu, Ctrl+scroll, trackpad pinch-to-zoom, magnifier tool
- Dark mode theme
- Robust error logging and crash capture

### Known Issues / Open Items
- No print support (menu item exists but not implemented)
- `mockup.py` in project root is the original UI prototype — can be deleted
- `temp/` folder contains icon generation scripts and raw/intermediate icon files

### UI Interactions Reference
- **Right-click canvas**: Context menu with Cut, Copy, Paste, Delete, Select All
- **Right-click layer panel**: Context menu with Rename, Show/Hide, Delete
- **Double-click layer name**: Inline rename editor
- **Selection handles**: 8 white resize squares + 1 blue rotation circle (appears
  after lifting pixels). Cursor changes to indicate resize direction or rotation.
- **Transparent color**: Red/white diagonal swatch at end of color bar. Works with
  fill tool, pencil, and brush (uses CompositionMode_Clear).
- **Text tool**: Click on canvas to place a floating text editor with a blue drag
  handle. Type directly, drag handle to move, click away to commit. Font controls
  appear in the tool options bar. Color changes apply live while editing.
- **Tool options bar**: Auto-hides when the active tool has no options. Shows
  size/fill controls for brushes/shapes, font controls for text tool.

### Configuration Files
- **`gui_config.json`** (project root): Central config file for icons and theme.
  - `theme.app_background`: Main window background hex color
  - `theme.tool_button_background`: Tool button background hex color
  - `tools.*`: Maps tool names to icon filenames in `jrpaint/resources/icons/`
  - `layers.*`: Maps layer button names to icon filenames
  - Set any icon to `null` to fall back to Unicode text

### Session History
1. **Initial build**: Created full application from mockup — all tools, layers, file I/O,
   menus, dark mode theme, status bar
2. **Paste auto-resize**: Canvas grows to fit pasted images (max of current and paste dimensions)
3. **Zoom + Move + Selection**: Added pinch-to-zoom, Zoom In/Out menu items, Move Layer
   tool with layer offsets, selection lift-and-move for rect select
4. **Crash hardening**: Added logging system (per-run log files + faulthandler for segfaults),
   wrapped tool dispatch and paintEvent in try/except, rewrote flood fill for performance,
   fixed airbrush stale layer reference, added null image guards to compositing
5. **Context file**: Created this file for session continuity
6. **Layer rename + Selection resize/rotate**: Double-click layer name to rename.
   Selection now has 8 resize handles (corners + edges) and a rotation handle
   (blue circle outside top-right corner). Drag handles to resize content, drag
   rotation handle to rotate. Content is scaled/rotated when committed back to layer.
7. **Layer right-click context menu**: Right-click a layer in the panel to get a
   context menu with Rename, Show/Hide (text adapts to current state), and Delete
   (disabled when only one layer remains).
8. **Inline text tool**: Replaced QInputDialog popup with FloatingTextWidget — a
   draggable container with blue handle bar + inline text editor. Supports font
   family, size, bold, italic, kerning, letter spacing. Color updates live when
   foreground color changes. Click away to render to layer.
9. **Usability batch**: Line/brush/eraser size max raised to 500px. Transparent
   color swatch added to color bar (checkerboard diagonal button). Fill tool works
   with transparent color. Pencil/brush use CompositionMode_Clear when painting
   with transparent. Right-click canvas shows context menu with Cut, Copy, Paste,
   Delete, Select All. Copy works with floating selections. Delete discards
   floating selections or clears the selected region.
10. **Selection cursors + Mac delete**: Resize handles show directional double-arrow
    cursors (diagonal/horizontal/vertical). Rotation handle shows a custom curved-arrow
    cursor. Hovering inside a selection shows move cursor. Mac Backspace key now works
    for deleting selections (in addition to forward-delete).
11. **Descriptive tooltips**: All tool buttons and layer panel buttons show descriptive
    hover tooltips (e.g. "Pencil — Draw freehand with a 1px line").
12. **Icon system**: AI-generated icons with green-screen backgrounds, post-processed
    with chroma key removal (flood-fill from edges, shadow preservation, despill),
    cropped to content, centered in square PNGs with alpha. 115 icons (23 types x 5
    variants) in `jrpaint/resources/icons/`. Config in `gui_config.json` (renamed from
    `icons.json`). Icon loader caches loaded icons, scales to fit any button size.
13. **Theme in config**: `app_background` and `tool_button_background` colors moved to
    `gui_config.json` theme section. Tool palette reads button color from config.
    Tool buttons enlarged to 42x42px (icons 36x36), layer buttons to 42x36px (icons 27x27).
14. **Tool options bar auto-hide**: Bar hides completely when active tool has no
    configurable options (pencil, fill, color picker, magnifier, select, move).
    Fixed startup bug where bar showed all controls before a tool was set.
15. **Text tool improvements**: Added drag handle bar for moving text. Font color
    updates live when foreground color is changed from the palette. Fixed dragging
    by using a dedicated handle widget instead of fighting with QTextEdit's input.
16. **Paint bucket cursor**: Fill tool now shows a 32x32 paint bucket cursor
    (from Fill_1.png icon) with hotspot at the pour point.
17. **Active layer indicator**: Status bar now shows the active layer name
    (e.g. "Layer: Background") so it's always clear which layer you're drawing on.
