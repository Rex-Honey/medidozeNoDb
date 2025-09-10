# pages/settings_page.py
from PyQt6.QtWidgets import QWidget, QLabel,QTableWidgetItem,QPushButton,QHBoxLayout, QMessageBox
from PyQt6.QtGui import QFont, QIcon, QPixmap, QImage, QPainter, QPainterPath, QIntValidator
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import dictfetchall,setState
from functools import partial
import base64


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
    def __init__(self, config, connString, userData):
        super().__init__()
        self.config = config
        self.connString = connString
        self.userData = userData
        self.localConn = pyodbc.connect(connString)
        self.rootDir = os.path.dirname(os.path.dirname(__file__))
        uiPath = os.path.join(self.rootDir, "uiFiles", "pharmacyUsers.ui")
        uic.loadUi(uiPath, self)
        self.fetchAllUsers()
        self.btnAddUser.clicked.connect(self.openAddUserPage)

    def openAddUserPage(self):
        try:
            from pages.addUser import AddUserWindow
            from pages.pageContainer import PageContainer

            # Create the add user page
            addUserWidget = AddUserWindow(self.config, self.connString,self.userData)
            addUserPage = PageContainer("Add User", addUserWidget)

            # Find the main app's stack (walk up the parent chain)
            parent = self.parentWidget()
            while parent is not None:
                if hasattr(parent, "stack"):
                    break
                parent = parent.parentWidget()
            if parent is not None:
                parent.stack.addWidget(addUserPage)
                parent.stack.setCurrentWidget(addUserPage)
            else:
                print("Main stack not found!")
        except Exception as e:
            print(e)

    def deleteUser(self,username):
        try:
            reply = QMessageBox.information(None, 'Medidoze alert',
            f"Do you want to delete user '{username}' ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                localCursor = self.localConn.cursor()
                localCursor.execute(f"UPDATE users SET isSoftDlt = 'Y' WHERE uid='{username}'")
                self.localConn.commit()
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

                    # btnEdit.clicked.connect(partial(self.switchEditWinrxUser, rowData['uid']))
                    # btnDlt.clicked.connect(partial(self.deleteUser, rowData['uid']))
        except Exception as e:
            print(e)

    def fetchAllUsers(self):
        try:
            print("--Fetching All Users..")
            localCursor = self.localConn.cursor()
            localCursor.execute("SELECT * FROM users where isSoftDlt='N' and uid != 'sys'")
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