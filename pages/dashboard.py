# pages/dashboard.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc

class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn   
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.local_conn = localConn
        
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "dashboard.ui")
        uic.loadUi(ui_path, self)
