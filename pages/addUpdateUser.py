from PyQt6.QtWidgets import QWidget,QFileDialog
from PyQt6.QtCore import QTimer
from PyQt6 import uic
import os, pyodbc, base64
from otherFiles.common import setState,rootDir,defaultUserImage,roundImage,switchToPage
from pages.pharmacyUsers import PharmacyUsersWindow
from datetime import datetime
from hashlib import sha256

class AddUpdateUserWindow(QWidget):
    def __init__(self, userToEdit=None):
        super().__init__()
        from otherFiles.config import config, connString, userData, medidozeDir, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.connString = connString
        self.userData = userData
        self.userToEdit = userToEdit
        self.localConn = localConn
        self.populationError = False  # Initialize error flag
        uiPath = os.path.join(rootDir, "uiFiles", "addUpdateUser.ui")
        uic.loadUi(uiPath, self)
        self.removeImage()
        self.btnCancel.clicked.connect(self.cancelAndSwitch)
        self.btnLoadImage.clicked.connect(self.loadImage)
        self.statusIsAdmin.currentTextChanged.connect(self.changeIsAdmin)
        self.btnRemoveImg.clicked.connect(self.removeImage)
        self.btnAdduser.clicked.connect(self.addUpdateUser)
        self.changeIsAdmin()
        setState(self.txtOatrxId, "ok")

        self.fields = [
        (self.txt_username, self.err_username, "Username can't be blank"),
        (self.txt_password, self.err_password, "Password can't be blank"),
        (self.txt_confirm_password, self.err_confirm_password, "Confirm Password can't be blank"),
        (self.txt_lname, self.err_lname, "Last Name can't be blank"),
        (self.txt_fname, self.err_fname, "First Name can't be blank"),
        ]
        
        # If in edit mode, populate fields with existing data
        if self.userToEdit is not None:
            self.populateFieldsForEdit()
            self.btnAdduser.setText("Update User")
        else:
            for txtWid,errWid,errMsg in self.fields:
                setState(txtWid, "ok")
                errWid.setText("")

    def populateFieldsForEdit(self):
        """Populate form fields with existing user data for editing"""
        try:
            self.populationError = False  # Initialize error flag
            
            # Convert all values to strings to avoid type errors
            self.txt_username.setText(str(self.userToEdit.get('uid', '')))
            self.txt_username.setEnabled(False)  # Username cannot be changed
            self.txt_fname.setText(str(self.userToEdit.get('firstName', '')))
            self.txt_lname.setText(str(self.userToEdit.get('lastName', '')))
            
            # Handle oatRxId which might be None or integer
            oatRxId = self.userToEdit.get('oatRxId')
            if oatRxId is not None:
                self.txtOatrxId.setText(str(oatRxId))
            else:
                self.txtOatrxId.setText("")
            
            # Set admin status
            isAdmin = self.userToEdit.get('isAdmin', 'N')
            if isAdmin == 'Y':
                self.statusIsAdmin.setCurrentText("Yes")
            else:
                self.statusIsAdmin.setCurrentText("No")
            
            # Set existing image if available
            image = self.userToEdit.get('image')
            if image:
                self.imageStr = image
                binaryData = base64.b64decode(image)
                pixmap = roundImage(binaryData)
                self.lblImg.setPixmap(pixmap)
            else:
                self.removeImage()
            
            # Clear password fields for edit mode
            self.txt_password.setText("")
            self.txt_confirm_password.setText("")
            self.txt_password.setPlaceholderText("Leave blank to keep current password")
            self.txt_confirm_password.setPlaceholderText("Leave blank to keep current password")
            
            # Set all fields to ok state
            for txtWid,errWid,errMsg in self.fields:
                setState(txtWid, "ok")
                errWid.setText("")
                
        except Exception as e:
            print(f"Error populating fields for edit: {e}")
            self.populationError = True  # Set error flag

    def loadImage(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if filename:
            with open(filename, 'rb') as f:
                imageData = f.read()
                self.imageStr = base64.b64encode(imageData).decode('utf-8')
            pixmap=roundImage(imageData)
            self.lblImg.setPixmap(pixmap)

    def removeImage(self):
        with open(defaultUserImage, 'rb') as f:
            imageData = f.read()
        pixmap=roundImage(imageData)
        
        self.imageStr = ""
        self.lblImg.setPixmap(pixmap)
        self.chkRemoveImage=True

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

    def addUpdateUser(self):
        try:
            # Validate required fields
            for txtWid,errWid,errMsg in self.fields:
                setState(txtWid, "ok")
                errWid.setText("")
                
                # Skip password validation in edit mode if passwords are empty
                if (self.userToEdit is not None and 
                    txtWid in [self.txt_password, self.txt_confirm_password] and 
                    txtWid.text().strip() == ""):
                    continue
                    
                if txtWid.text().strip() == "":
                    setState(txtWid, "err")
                    errWid.setText(errMsg)
                    return

            oatrxId=self.txtOatrxId.text()
            if not oatrxId:
                oatrxId=None

            password=self.txt_password.text()
            confirmPassword=self.txt_confirm_password.text()
            if password:
                if password != confirmPassword:
                    setState(self.txt_confirm_password, "err")
                    self.err_confirm_password.setText("Password and Confirm Password do not match")
                    return

            adminStatus=self.statusIsAdmin.currentText()
            if adminStatus=="Yes":
                isAdmin="Y"
            else:
                isAdmin="N"

            otp=self.txtOtp.text()
            if otp:
                hashOtp=sha256(otp.encode()).hexdigest()
            else:
                hashOtp=None
            
            
            username=self.txt_username.text()
            fname=self.txt_fname.text()
            lname=self.txt_lname.text()
            try:
                localCursor = self.localConn.cursor()
                
                if self.userToEdit is not None:
                    # Update existing user
                    if password:  # Only update password if provided
                        hashedPassword = sha256(password.encode()).hexdigest()
                        query = """ UPDATE users SET oatRxId=?, password=?, otp=?, firstName=?, lastName=?, image=?, isAdmin=?, updatedBy=?, updatedDate=? WHERE uid=? """
                        params = (oatrxId, hashedPassword, hashOtp, fname, lname, self.imageStr, isAdmin, self.userData['uid'], datetime.now(), username)
                    else:
                        # Keep existing password
                        query = """ UPDATE users SET oatRxId=?, otp=?, firstName=?, lastName=?, image=?, isAdmin=?, updatedBy=?, updatedDate=? WHERE uid=? """
                        params = (oatrxId, hashOtp, fname, lname, self.imageStr, isAdmin, self.userData['uid'], datetime.now(), username)
                    
                    localCursor.execute(query, params)
                    self.localConn.commit()
                    self.infoAddUser.setText("User Updated Successfully !!")
                else:
                    # Insert new user
                    hashedPassword = sha256(password.encode()).hexdigest()
                    query = """ INSERT INTO users ( uid, oatRxId, password, otp, firstName, lastName, image, isAdmin, isActive, isSoftDlt, createdBy, updatedBy, createdDate, updatedDate ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """
                    params = (username, oatrxId, hashedPassword, hashOtp, fname, lname, self.imageStr, isAdmin, 'Y', 'N', self.userData['uid'], self.userData['uid'], datetime.now(), datetime.now())
                    localCursor.execute(query,params)
                    self.localConn.commit()
                    self.infoAddUser.setText("New User Registered Successfully !!")
                
                self.infoAddUser.setStyleSheet("background:lightgreen;color:green;padding:8px;border-radius:none")
                QTimer.singleShot(4000, self.clearInfo)
                
                if self.userToEdit is None:
                    # Clear form only for new user registration
                    self.statusIsAdmin.setCurrentText("No")
                    for txtb in (self.txt_username,self.txtOatrxId,self.txt_fname,self.txt_lname,self.txt_password,self.txt_confirm_password):
                        txtb.setText("")
                    self.statusIsAdmin.setCurrentText("No")
                    self.removeImage()
                    self.txt_username.setFocus()
                    # For edit mode, stay on the current page after successful update
                    
            except pyodbc.IntegrityError as e:
                if 'duplicate key' in str(e).lower():
                    self.err_username.setText("Username already exists")
                else:
                    print(e)
        except Exception as e:
            print(e)

    def cancelAndSwitch(self):
        """Create a fresh instance of PharmacyUsersWindow and switch to it"""
        try:
            # Create a new instance of PharmacyUsersWindow
            freshPharmacyUsers = PharmacyUsersWindow()
            
            # Find the parent stack widget
            from pages.pageContainer import PageContainer
            parent = self.parentWidget()
            while parent is not None:
                if hasattr(parent, "stack"):
                    break
                parent = parent.parentWidget()
            
            if parent is not None:
                # Create a new PageContainer with the fresh PharmacyUsersWindow
                pageContainer = PageContainer("Pharmacy Users", freshPharmacyUsers)
                
                # Add the new PageContainer to the stack and switch to it
                parent.stack.addWidget(pageContainer)
                parent.stack.setCurrentWidget(pageContainer)
            else:
                print("Main stack not found!")
        except Exception as e:
            print(f"Error creating fresh PharmacyUsersWindow: {e}")

    def clearInfo(self):
        try:
            self.infoAddUser.setText("")
            self.infoAddUser.setStyleSheet("background:none")
        except Exception as e:
            print(e)