
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os

class DinWindow(QWidget):
    def __init__(self):
        super().__init__()
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "din.ui")
        uic.loadUi(ui_path, self)
