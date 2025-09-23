# pages/settings_page.py
from PyQt6.QtWidgets import QWidget, QLabel,QTableWidgetItem,QPushButton,QHBoxLayout, QMessageBox
from PyQt6.QtGui import QFont, QIcon, QPixmap, QImage, QPainter, QPainterPath, QIntValidator
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import dictfetchall,setState,medidozeDir
from functools import partial
import base64
from datetime import datetime

def getRoundedPixmap(pixmap, size):
    rounded = QPixmap(size, size)
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
    painter.end()
    return rounded

class PharmacyUsersWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        from otherFiles.config import config, userData, localConn, liveConn
        if config is None or localConn is None:
            QMessageBox.critical(self, "Configuration Error", "Configuration not properly initialized. Please restart the application.")
            return          

        self.config = config
        self.userData = userData
        self.medidozeDir = medidozeDir
        self.local_conn = localConn
        self.liveConn = liveConn

        self.rootDir = os.path.dirname(os.path.dirname(__file__))
        uiPath = os.path.join(self.rootDir, "uiFiles", "pharmacyUsers.ui")
        uic.loadUi(uiPath, self)

        self.txtSearchUser.textChanged.connect(self.fetchAllUsers)
        self.btnAddUser.clicked.connect(lambda: self.openAddEditUserPage())
        self.btnSyncUsers.clicked.connect(self.syncPharmacyUsers)
        self.fetchAllUsers()

    def syncPharmacyUsers(self):
        try:
            liveCursor=self.liveConn.cursor()
            liveCursor.execute(f"select * from EMPLOYEE")
            data=dictfetchall(liveCursor)
            local_cursor = self.local_conn.cursor()
            if data:
                for row in data:
                    query = """ 
                    IF EXISTS (SELECT 1 FROM users WHERE uid = ?)
                    UPDATE users SET uid = ?, password=?, firstName=?, lastName = ?, updatedBy = ?, updatedDate = ? WHERE uid = ?
                    ELSE
                    INSERT INTO users (uid, password, firstName, lastName, isAdmin, isActive, isSoftDlt, createdByMedidoze, createdBy, updatedBy, createdDate, updatedDate) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """ 
                    params = (row['EMUSERID'],row['EMUSERID'],row['EMPASSWORD'],row['EMNAME'],row['EMSURNAME'],self.userData['uid'],datetime.now(),row['EMUSERID'],row['EMUSERID'],row['EMPASSWORD'],row['EMNAME'],row['EMSURNAME'],'N','Y','N','N', self.userData['uid'],self.userData['uid'],datetime.now(),datetime.now())
                    local_cursor.execute(query,params)
            self.local_conn.commit()
            self.infoViewUsers.setText("Users synced successfully!!")
            self.infoViewUsers.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
            QTimer.singleShot(4000, self.clearInfoMessages)
        except Exception as e:
            print(e)

    def openAddEditUserPage(self, userToEdit=None):
        try:
            from pages.addUpdateUser import AddUpdateUserWindow
            from pages.pageContainer import PageContainer

            # Create the add/edit user page
            addEditUserWidget = AddUpdateUserWindow(userToEdit=userToEdit)
            
            # Check if there was an error during field population (for edit mode)
            if userToEdit and hasattr(addEditUserWidget, 'populationError') and addEditUserWidget.populationError:
                # Show error message and don't navigate
                self.infoViewUsers.setText("Error loading user data. Please try again.")
                self.infoViewUsers.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:10px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
                QTimer.singleShot(4000, self.clearInfoMessages)
                return
            
            # Set page title based on mode
            pageTitle = "Edit User" if userToEdit else "Add User"
            addEditUserPage = PageContainer(pageTitle, addEditUserWidget)

            # Find the main app's stack (walk up the parent chain)
            parent = self.parentWidget()
            while parent is not None:
                if hasattr(parent, "stack"):
                    break
                parent = parent.parentWidget()
            if parent is not None:
                parent.stack.addWidget(addEditUserPage)
                parent.stack.setCurrentWidget(addEditUserPage)
            else:
                print("Main stack not found!")
        except Exception as e:
            print(f"Error opening add/edit user page: {e}")
            # Show error message to user
            self.infoViewUsers.setText("Error opening user form. Please try again.")
            self.infoViewUsers.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:10px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
            QTimer.singleShot(4000, self.clearInfoMessages)

    def deleteUser(self,username):
        try:
            reply = QMessageBox.information(None, 'Medidoze alert',
            f"Do you want to delete user '{username}' ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                localCursor = self.local_conn.cursor()
                localCursor.execute(f"UPDATE users SET isSoftDlt = 'Y' WHERE uid='{username}'")
                self.local_conn.commit()
                self.infoViewUsers.setText("User deleted successfully!!")
                self.infoViewUsers.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
                QTimer.singleShot(4000, self.clearInfoMessages)
                self.fetchAllUsers()
        except Exception as e:
            print(e)

    def addDataToUserTable(self,data):
        try:
            self.table_view_user.setRowCount(len(data))
            for row,rowData in enumerate(data):
                
                # ------------ image ------------
                col=0
                self.table_view_user.setColumnWidth(col, 120)
                self.lblImg = QLabel()
                size = 30
                self.lblImg.setFixedSize(size, size)
                self.lblImg.setScaledContents(True)
                if rowData['image']:
                    binaryData = base64.b64decode(rowData['image'])
                    image = QImage.fromData(binaryData)
                    pixmap = QPixmap.fromImage(image).scaled(
                        30, 30, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                    )
                else:
                    defaultImagePath = os.path.join(self.rootDir, "images", "user.jpg")
                    image = QImage(defaultImagePath)
                    pixmap = QPixmap.fromImage(image).scaled(
                        30, 30, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                    )

                # Make the pixmap round and set it
                roundedPixmap = getRoundedPixmap(pixmap, size)
                self.lblImg.setPixmap(roundedPixmap)
                self.table_view_user.setCellWidget(row, col, self.lblImg)
                self.lblImg.setStyleSheet("padding-left:5px;border-radius:0px;background-color:transparent")

                # ------------ username ------------
                col+=1
                self.table_view_user.setColumnWidth(col, 250)
                usernameWid=QTableWidgetItem(rowData['uid'])
                self.table_view_user.setItem(row,col,usernameWid)

                # ------------ name ------------
                col+=1
                self.table_view_user.setColumnWidth(col, 470)
                nameWid=QTableWidgetItem(rowData['firstName']+" "+rowData['lastName'])
                self.table_view_user.setItem(row,col,nameWid)

                # ------------ status ------------
                col+=1
                self.table_view_user.setColumnWidth(col, 100)
                font=QFont()
                font.setBold(True)
                font.setPointSize(8)
                self.btnStatus=QPushButton()
                self.btnStatus.setFont(font)

                if rowData['isActive']=="Y":
                    self.btnStatus.setText(" ACTIVE")
                    self.btnStatus.setIcon(QIcon(os.path.join(self.rootDir, "images", "active.png")))
                    self.btnStatus.setStyleSheet("background-color:#ecf5d9;color:#7fba00;margin:6px 20px 6px 0px;border-radius:6%")
                else:
                    self.btnStatus.setText(" INACTIVE")
                    self.btnStatus.setIcon(QIcon(os.path.join(self.rootDir, "images", "deactive.png")))
                    self.btnStatus.setStyleSheet("background-color:#fde5de;color:#f25022;margin:6px 20px 6px 0px;border-radius:6%")
                self.table_view_user.setCellWidget(row, col, self.btnStatus)

                # ------------ edit and delete ------------
                col+=1
                if rowData['uid']!="admin":
                    btnEdit = QPushButton()
                    btnEdit.setIcon(QIcon(QIcon(os.path.join(self.rootDir, "images", "edit_icon.svg"))))
                    btnEdit.setCursor(Qt.CursorShape.PointingHandCursor)

                    btnDlt = QPushButton()
                    btnDlt.setIcon(QIcon(QIcon(os.path.join(self.rootDir, "images", "delete_icon.svg"))))
                    btnDlt.setStyleSheet("margin-right:15px;padding-right:5px")
                    btnDlt.setCursor(Qt.CursorShape.PointingHandCursor)

                    layout = QHBoxLayout()
                    layout.addWidget(btnEdit)
                    layout.addWidget(btnDlt)
                    layout.setContentsMargins(0,0,0,0)
                    
                    widget = QWidget()
                    widget.setLayout(layout)
                    widget.setStyleSheet("border-radius:0px;background-color:transparent")
                    self.table_view_user.setCellWidget(row, col, widget)

                    # Connect edit button to open edit page with user data
                    btnEdit.clicked.connect(partial(self.openAddEditUserPage, rowData))
                    btnDlt.clicked.connect(partial(self.deleteUser, rowData['uid']))
                else:
                    self.table_view_user.setCellWidget(row, col, QWidget())
        except Exception as e:
            print(e)

    def fetchAllUsers(self):
        try:
            print("--Fetching All Users..")
            localCursor = self.local_conn.cursor()
            searchText = self.txtSearchUser.text().strip()
            baseQuery = "SELECT * FROM users where isSoftDlt='N' and uid != 'sys'"
            if searchText:
                localCursor.execute(baseQuery + " and (firstName like ? or lastName like ?)", (f"%{searchText}%", f"%{searchText}%"))
            else:
                localCursor.execute(baseQuery)
            data=dictfetchall(localCursor)
            self.addDataToUserTable(data)
        except Exception as e:
            print(e)

    def clearInfoMessages(self):
            try:
                self.infoViewUsers.setText("")
                self.infoViewUsers.setStyleSheet("background:none")
            except Exception as e:
                print(e)