
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc

class DinWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, connString, userData, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.connString = connString
        self.userData = userData
        self.local_conn = localConn
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "din.ui")
        uic.loadUi(ui_path, self)
