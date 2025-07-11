# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os

class PrimeWindow(QWidget):
    def __init__(self):
        super().__init__()
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "primePump.ui")
        uic.loadUi(ui_path, self)
