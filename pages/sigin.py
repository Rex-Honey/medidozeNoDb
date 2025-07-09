from PyQt6.QtWidgets import QWidget, QLineEdit
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic
import os,pyodbc
from hashlib import sha256
from otherFiles.common import dictfetchall, setState

class SignInWindow(QWidget):
    loginSuccess = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        rootDir=os.path.dirname(os.path.dirname(__file__))
        uic.loadUi(os.path.join(rootDir, 'uiFiles', 'signin.ui'), self)

        self.txtPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.lblHideEye.setVisible(False)

        self.lblShowEye.mousePressEvent = self.toggle_password_visibility
        self.lblHideEye.mousePressEvent = self.toggle_password_visibility
        self.btnSignin.clicked.connect(self.SignIn)
        self.errUsername.setText("")
        self.errPassword.setText("")
        for frm in (self.frame_6, self.frame_7):
            setState(frm, "ok")

    def setConfig(self,connString):
        try:
            self.local_conn = pyodbc.connect(connString)
        except Exception as e:
            print(e)

    def toggle_password_visibility(self, event):
        if self.txtPassword.echoMode() == QLineEdit.EchoMode.Password:
            self.txtPassword.setEchoMode(QLineEdit.EchoMode.Normal)
            self.lblShowEye.setVisible(False)
            self.lblHideEye.setVisible(True)
        else:
            self.txtPassword.setEchoMode(QLineEdit.EchoMode.Password)
            self.lblShowEye.setVisible(True)
            self.lblHideEye.setVisible(False)

    def keyPressEvent(self, event):
        try:
            print("keyPressEvent")
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.SignIn()
        except Exception as e:
            print(e)

    def SignIn(self):
        try:
            fields = [
                (self.frame_6, self.txtUsername, self.errUsername, "Username can't be blank"),
                (self.frame_7, self.txtPassword, self.errPassword, "Password can't be blank"),
            ]
            fieldsEmpty=False
            for frame, widget, error_label, error_msg in fields:
                setState(frame, "ok")
                error_label.setText("")
                if widget.text().strip() == "":
                    setState(frame, "err")
                    error_label.setText(error_msg)
                    fieldsEmpty=True
            if fieldsEmpty:
                return

            username = self.txtUsername.text()
            password = self.txtPassword.text()
            # username="admin"
            # password="admin"
            hashed_password = sha256(password.encode()).hexdigest()
            local_cursor = self.local_conn.cursor()
            query = f"select * from users where uid='{username}';"
            local_cursor.execute(query)
            data=dictfetchall(local_cursor)
            if data:
                row=data[0]
            else:
                self.errUsername.setText("User does not exist")
                return
                # print(row)
            get_hashed_password=row['password']
            status=row['isActive']

            if status!='Y':
                self.errPassword.setText("Sorry, you do not have permission to access this resource. Please contact the administrator for assistance.")
            elif hashed_password!=get_hashed_password:
                self.errPassword.setText("Invalid Credentials")
            else:
                print('Login Successfull')
                self.txtUsername.setText("")
                self.txtPassword.setText("")
                self.txtUsername.setFocus()
                self.loginSuccess.emit(row)
        except Exception as e:
            print(e)