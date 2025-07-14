# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc

class PatientsWindow(QWidget):
    def __init__(self, config, connString, userData):
        super().__init__()
        self.config = config
        self.connString = connString
        self.userData = userData
        self.local_conn = pyodbc.connect(connString)
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "patients.ui")
        uic.loadUi(ui_path, self)
