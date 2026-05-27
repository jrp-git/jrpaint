from PyQt6.QtWidgets import QMessageBox


def show_about(parent):
    QMessageBox.about(
        parent,
        "About JRPaint",
        "JRPaint\nVersion 1.0\n\n"
        "A cross-platform paint application\n"
        "inspired by classic Microsoft Paint.\n\n"
        "Supports layers, transparency,\n"
        "and the .jrp layered file format.",
    )
