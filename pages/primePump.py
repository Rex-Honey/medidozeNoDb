from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc

class PrimeWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn
        self.config = config
        self.userData = userData
        self.local_conn = localConn
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "primePump.ui")
        uic.loadUi(ui_path, self)
