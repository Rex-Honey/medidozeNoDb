# pages/settings_page.py
from PyQt6.QtWidgets import QWidget, QLabel,QTableWidgetItem,QPushButton,QHBoxLayout, QMessageBox
from PyQt6.QtGui import QFont, QIcon, QPixmap, QImage, QPainter, QPainterPath, QIntValidator
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import dictfetchall,setState
from functools import partial
import base64


def get_rounded_pixmap(pixmap, size):
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
        self.local_conn = pyodbc.connect(connString)
        self.rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(self.rootDir, "uiFiles", "pharmacyUsers.ui")
        uic.loadUi(ui_path, self)
        self.fetch_all_users()
        self.btnAddUser.clicked.connect(self.openAddUserPage)

    def openAddUserPage(self):
        try:
            from pages.addUser import AddUserWindow
            from pages.pageContainer import PageContainer

            # Create the add user page
            add_user_widget = AddUserWindow(self.config, self.connString,self.userData)
            add_user_page = PageContainer("Add User", add_user_widget)

            # Find the main app's stack (walk up the parent chain)
            parent = self.parentWidget()
            while parent is not None:
                if hasattr(parent, "stack"):
                    break
                parent = parent.parentWidget()
            if parent is not None:
                parent.stack.addWidget(add_user_page)
                parent.stack.setCurrentWidget(add_user_page)
            else:
                print("Main stack not found!")
        except Exception as e:
            print(e)

    def delete_user(self,username):
        try:
            reply = QMessageBox.information(None, 'Medidoze alert',
            f"Do you want to delete user '{username}' ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                local_cursor = self.local_conn.cursor()
                local_cursor.execute(f"UPDATE users SET isSoftDlt = 'Y' WHERE uid='{username}'")
                self.local_conn.commit()
                self.infoViewUsers.setText("User deleted successfully!!")
                self.infoViewUsers.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
                QTimer.singleShot(4000, self.clear_info_messages)
                self.fetch_all_users()
        except Exception as e:
            print(e)

    def addDataToUserTable(self,data):
        try:
            self.table_view_user.setRowCount(len(data))
            for row,row_data in enumerate(data):
                
                # ------------ image ------------
                col=0
                self.table_view_user.setColumnWidth(col, 120)
                self.lblImg = QLabel()
                size = 30
                self.lblImg.setFixedSize(size, size)
                self.lblImg.setScaledContents(True)
                if row_data['image']:
                    binary_data = base64.b64decode(row_data['image'])
                    image = QImage.fromData(binary_data)
                    pixmap = QPixmap.fromImage(image).scaled(
                        30, 30, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                    )
                else:
                    default_image_path = os.path.join(self.rootDir, "images", "user.jpg")
                    image = QImage(default_image_path)
                    pixmap = QPixmap.fromImage(image).scaled(
                        30, 30, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                    )

                # Make the pixmap round and set it
                rounded_pixmap = get_rounded_pixmap(pixmap, size)
                self.lblImg.setPixmap(rounded_pixmap)
                self.table_view_user.setCellWidget(row, col, self.lblImg)
                self.lblImg.setStyleSheet("padding-left:5px;border-radius:0px;background-color:transparent")

                # ------------ username ------------
                col+=1
                self.table_view_user.setColumnWidth(col, 250)
                username_wid=QTableWidgetItem(row_data['uid'])
                self.table_view_user.setItem(row,col,username_wid)

                # ------------ name ------------
                col+=1
                self.table_view_user.setColumnWidth(col, 470)
                name_wid=QTableWidgetItem(row_data['firstName']+" "+row_data['lastName'])
                self.table_view_user.setItem(row,col,name_wid)

                # ------------ status ------------
                col+=1
                self.table_view_user.setColumnWidth(col, 100)
                font=QFont()
                font.setBold(True)
                font.setPointSize(8)
                self.btn_status=QPushButton()
                self.btn_status.setFont(font)

                if row_data['isActive']=="Y":
                    self.btn_status.setText(" ACTIVE")
                    self.btn_status.setIcon(QIcon(os.path.join(self.rootDir, "images", "active.png")))
                    self.btn_status.setStyleSheet("background-color:#ecf5d9;color:#7fba00;margin:6px 20px 6px 0px;border-radius:6%")
                else:
                    self.btn_status.setText(" INACTIVE")
                    self.btn_status.setIcon(QIcon(os.path.join(self.rootDir, "images", "deactive.png")))
                    self.btn_status.setStyleSheet("background-color:#fde5de;color:#f25022;margin:6px 20px 6px 0px;border-radius:6%")
                self.table_view_user.setCellWidget(row, col, self.btn_status)

                # ------------ edit and delete ------------
                col+=1
                if row_data['uid']!="admin":
                    btn_edit = QPushButton()
                    btn_edit.setIcon(QIcon(QIcon(os.path.join(self.rootDir, "images", "edit_icon.svg"))))
                    btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)

                    btn_dlt = QPushButton()
                    btn_dlt.setIcon(QIcon(QIcon(os.path.join(self.rootDir, "images", "delete_icon.svg"))))
                    btn_dlt.setStyleSheet("margin-right:15px;padding-right:5px")
                    btn_dlt.setCursor(Qt.CursorShape.PointingHandCursor)

                    layout = QHBoxLayout()
                    layout.addWidget(btn_edit)
                    layout.addWidget(btn_dlt)
                    layout.setContentsMargins(0,0,0,0)
                    
                    widget = QWidget()
                    widget.setLayout(layout)
                    widget.setStyleSheet("border-radius:0px;background-color:transparent")
                    self.table_view_user.setCellWidget(row, col, widget)

                    # btn_edit.clicked.connect(partial(self.switchEditWinrxUser, row_data['uid']))
                    # btn_dlt.clicked.connect(partial(self.delete_user, row_data['uid']))
        except Exception as e:
            print(e)

    def fetch_all_users(self):
        try:
            local_cursor = self.local_conn.cursor()
            local_cursor.execute("SELECT * FROM users where isSoftDlt='N' and uid != 'sys'")
            data=dictfetchall(local_cursor)
            self.addDataToUserTable(data)
        except Exception as e:
            print(e)

    def clear_info_messages(self):
            try:
                self.infoViewUsers.setText("")
                self.infoViewUsers.setStyleSheet("background:none")
            except Exception as e:
                print(e)
