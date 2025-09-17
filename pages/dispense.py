# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc

class DispenseWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, connString, userData, medidozeDir, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.connString = connString
        self.userData = userData
        self.medidozeDir = medidozeDir
        self.local_conn = localConn
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "dispense.ui")
        uic.loadUi(ui_path, self)

        # self.btnExport.clicked.connect(self.exportDataToExcel)

