from PyQt6.QtWidgets import QWidget, QLineEdit
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic
import os


class SignInWindow(QWidget):
    loginSuccess = pyqtSignal(str,int,str)
    def __init__(self):
        super().__init__()
        rootDir=os.path.dirname(os.path.dirname(__file__))
        uic.loadUi(os.path.join(rootDir, 'uiFiles', 'signin.ui'), self)

        self.txtPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.lblHideEye.setVisible(False)

        self.lblShowEye.mousePressEvent = self.toggle_password_visibility
        self.lblHideEye.mousePressEvent = self.toggle_password_visibility

    def toggle_password_visibility(self, event):
        if self.txtPassword.echoMode() == QLineEdit.EchoMode.Password:
            self.txtPassword.setEchoMode(QLineEdit.EchoMode.Normal)
            self.lblShowEye.setVisible(False)
            self.lblHideEye.setVisible(True)
        else:
            self.txtPassword.setEchoMode(QLineEdit.EchoMode.Password)
            self.lblShowEye.setVisible(True)
            self.lblHideEye.setVisible(False)