
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import setState,rootDir,defaultUserImage,round_image
from PyQt6.QtGui import QImage, QPixmap, QPainter, QBrush, QWindow
from PyQt6.QtCore import Qt, QRect

class AddUserWindow(QWidget):
    def __init__(self, config, connString):
        super().__init__()
        self.config = config
        self.connString = connString
        self.local_conn = pyodbc.connect(connString)
        ui_path = os.path.join(rootDir, "uiFiles", "addUser.ui")
        uic.loadUi(ui_path, self)
        for wid in (self.txt_username, self.txt_password, self.txt_confirm_password, self.txt_fname, self.txt_lname, self.txtOatrxId, self.txtOtp):
            setState(wid, "ok")
        self.remove_image()

    def remove_image(self):
        with open(defaultUserImage, 'rb') as f:
            imageData = f.read()
        pixmap=round_image(imageData)
        
        self.imageStr = ""
        self.lbl_img.setPixmap(pixmap)
        self.chk_remove_image=True
