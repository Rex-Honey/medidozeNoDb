from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import dictfetchall,medidozeDir
from hashlib import sha256
from pages.settings import SettingsWindow

class SettingsAuthWindow(QWidget):
    authenticated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, connString, userData, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.connString = connString
        self.userData = userData
        self.medidozeDir = medidozeDir
        self.local_conn = localConn
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "settingsAuth.ui")
        uic.loadUi(ui_path, self)
        self.checkSettings()
        self.txtAuthOtp.setText("")
        self.errAuth.setText("")

        self.btnAuthenticate.clicked.connect(self.authenticateForSettings)

    def checkSettings(self):
        try:
            local_cursor = self.local_conn.cursor()
            query = f"select * from users where uid=?;"
            local_cursor.execute(query,self.userData['uid'])
            userData=dictfetchall(local_cursor)
            self.userOtp=userData[0]['otp']
            if not self.userOtp:
                # No OTP set, emit signal to go directly to settings
                self.authenticated.emit()
        except Exception as e:
            print(e)

    def authenticateForSettings(self):
        try:
            otp=self.txtAuthOtp.text()
            if sha256(otp.encode()).hexdigest()==self.userOtp:
                self.authenticated.emit()
            else:
                self.errAuth.setText("Invalid Otp")
        except Exception as e:
            print(e)