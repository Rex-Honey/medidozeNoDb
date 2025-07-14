from PyQt6.QtWidgets import QWidget,QFileDialog
from PyQt6.QtCore import QTimer
from PyQt6 import uic
import os, pyodbc, base64
from otherFiles.common import setState,rootDir,defaultUserImage,roundImage,switchToPage
from pages.pharmacyUsers import PharmacyUsersWindow
from datetime import datetime
from hashlib import sha256

class AddUserWindow(QWidget):
    def __init__(self, config, connString, userData):
        super().__init__()
        self.config = config
        self.connString = connString
        self.userData = userData
        self.local_conn = pyodbc.connect(connString)
        ui_path = os.path.join(rootDir, "uiFiles", "addUser.ui")
        uic.loadUi(ui_path, self)
        self.remove_image()
        self.btnCancel.clicked.connect(lambda: switchToPage(self, PharmacyUsersWindow))
        self.btnLoadImage.clicked.connect(self.load_image)
        self.statusIsAdmin.currentTextChanged.connect(self.changeIsAdmin)
        self.btnRemoveImg.clicked.connect(self.remove_image)
        self.btnAdduser.clicked.connect(self.registerUser)
        self.changeIsAdmin()
        setState(self.txtOatrxId, "ok")


        self.fields = [
        (self.txt_username, self.err_username, "Username can't be blank"),
        (self.txt_password, self.err_password, "Password can't be blank"),
        (self.txt_confirm_password, self.err_confirm_password, "Confirm Password can't be blank"),
        (self.txt_lname, self.err_lname, "Last Name can't be blank"),
        (self.txt_fname, self.err_fname, "First Name can't be blank"),
        ]
        for txtWid,errWid,errMsg in self.fields:
            setState(txtWid, "ok")
            errWid.setText("")

    def load_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if filename:
            with open(filename, 'rb') as f:
                image_data = f.read()
                self.imageStr = base64.b64encode(image_data).decode('utf-8')
            pixmap=roundImage(image_data)
            self.lblImg.setPixmap(pixmap)

    def remove_image(self):
        with open(defaultUserImage, 'rb') as f:
            imageData = f.read()
        pixmap=roundImage(imageData)
        
        self.imageStr = ""
        self.lblImg.setPixmap(pixmap)
        self.chk_remove_image=True

    def changeIsAdmin(self):
        try:
            if self.statusIsAdmin.currentText()=="Yes":
                self.txtOtp.setEnabled(True)
                self.txtOtp.setPlaceholderText("Enter Otp")
                self.txtOtp.setStyleSheet("background:#FFFFFF;font-size: 11pt; border-radius:10%; padding:10px; border:1px solid #e1e4e6;")
            else:
                self.txtOtp.setText("")
                self.txtOtp.setPlaceholderText("")
                self.txtOtp.setDisabled(True)
                self.txtOtp.setStyleSheet("background:lightgrey;font-size: 11pt; border-radius:10%; padding:10px; border:1px solid #e1e4e6;")
        except Exception as e:
            print(e)

    def registerUser(self):
        try:
            for txtWid,errWid,errMsg in self.fields:
                setState(txtWid, "ok")
                errWid.setText("")
                if txtWid.text().strip() == "":
                    setState(txtWid, "err")
                    errWid.setText(errMsg)
                    return

            username=self.txt_username.text()
            password=self.txt_password.text()
            confirm_password=self.txt_confirm_password.text()
            fname=self.txt_fname.text()
            lname=self.txt_lname.text()
            oatrxId=self.txtOatrxId.text()
            otp=self.txtOtp.text()

            if password!=confirm_password:
                setState(self.txt_confirm_password, "err")
                self.err_confirm_password.setText("Password and Confirm Password do not match")
                return

            adminStatus=self.statusIsAdmin.currentText()
            if adminStatus=="Yes":
                isAdmin="Y"
            else:
                isAdmin="N"
            if otp:
                hashOtp=sha256(otp.encode()).hexdigest()
            else:
                hashOtp=None
            
            hashed_password = sha256(password.encode()).hexdigest()
            current_datetime=datetime.now()
            format_created_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            try:
                local_cursor = self.local_conn.cursor()
                query = """ INSERT INTO users ( uid, oatRxId, password, otp, firstName, lastName, image, isAdmin, isActive, isSoftDlt, createdByMedidoze, createdBy, updatedBy, createdDate, updatedDate ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """ 
                params = ( username, oatrxId, hashed_password, hashOtp, fname, lname, self.imageStr, isAdmin, 'Y', 'N','Y', self.userData['uid'], self.userData['uid'], format_created_date, format_created_date )
                local_cursor.execute(query,params)
                self.local_conn.commit()
                # self.local_conn.close()
                self.infoAddUser.setText("New User Registered Successfully !!")
                self.infoAddUser.setStyleSheet("background:lightgreen;color:green;padding:8px;border-radius:none")
                QTimer.singleShot(4000, self.clearInfo)
                self.statusIsAdmin.setCurrentText("No")
                for txtb in (self.txt_username,self.txtOatrxId,self.txt_fname,self.txt_lname,self.txt_password,self.txt_confirm_password):
                    txtb.setText("")
                self.statusIsAdmin.setCurrentText("No")
                self.remove_image()
                self.txt_username.setFocus()
            except pyodbc.IntegrityError as e:
                if 'duplicate key' in str(e).lower():
                    self.err_username.setText("Username already exists")
                else:
                    print(e)
        except Exception as e:
            print(e)

    def clearInfo(self):
        try:
            self.infoAddUser.setText("")
            self.infoAddUser.setStyleSheet("background:none")
        except Exception as e:
            print(e)
