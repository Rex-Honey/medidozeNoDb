# pages/settings_page.py
from PyQt6.QtWidgets import QWidget, QFileDialog, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QLineEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QImage, QPixmap
from datetime import datetime
from functools import partial
from PyQt6 import uic
import os, pyodbc,base64
from otherFiles.common import dictfetchall

class PatientsWindow(QWidget):
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
        ui_path = os.path.join(rootDir, "uiFiles", "patients.ui")
        uic.loadUi(ui_path, self)

        self.user_img = os.path.join(rootDir, 'images', 'user.jpg')
        self.edit_icon = os.path.join(rootDir, 'images', 'edit_icon.svg')


        # self.btnLoadImgPatient.clicked.connect(self.loadImagePatient)
        # self.btnRemoveImgPatient.clicked.connect(self.removeImagePatient)
        # self.btnUpdatePatient.clicked.connect(self.updatePatient)
        # self.txtSearchPatient.keyPressEvent = self.searchPatient
        # self.btn_cancel_patient.clicked.connect(self.switchViewPatient)
        self.fetchPatients()

    def addDataToPatientTable(self,data):
        try:
            self.tablePatients.setRowCount(len(data))
            for row,row_data in enumerate(data):
                name_wid=QTableWidgetItem(row_data['firstName']+" "+row_data['lastName'])
                phone_wid=QTableWidgetItem(str(row_data['areaCode'])+str(row_data['phone']))
                phn_wid=QTableWidgetItem(str(row_data['id']))

                col=0
                lblImgPatientTable=QLabel()
                lblImgPatientTable.setFixedSize(35, 35)
                lblImgPatientTable.setScaledContents(True)
                lblImgPatientTable.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if row_data['image']:
                    try:
                        binary_data = base64.b64decode(row_data['image'])
                        image = QImage.fromData(binary_data)
                        if not image.isNull():
                            pixmap = QPixmap.fromImage(image)
                            # Scale the pixmap to fit the label
                            scaled_pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            lblImgPatientTable.setPixmap(scaled_pixmap)
                        else:
                            # If image is null, use default
                            pixmap = QPixmap(self.user_img)
                            scaled_pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            lblImgPatientTable.setPixmap(scaled_pixmap)
                    except Exception as e:
                        print(f"Error loading patient image: {e}")
                        # Use default image on error
                        pixmap = QPixmap(self.user_img)
                        scaled_pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        lblImgPatientTable.setPixmap(scaled_pixmap)
                else:
                    pixmap = QPixmap(self.user_img)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        lblImgPatientTable.setPixmap(scaled_pixmap)
                    else:
                        print(f"Default user image not found: {self.user_img}")
                
                self.tablePatients.setColumnWidth(col, 60)
                self.tablePatients.setCellWidget(row, col, lblImgPatientTable)
                lblImgPatientTable.setStyleSheet("padding:2px;background-color:transparent")

                col+=1
                self.tablePatients.setColumnWidth(col, 330)
                self.tablePatients.setItem(row,col,name_wid)

                col+=1
                self.tablePatients.setColumnWidth(col, 230)
                self.tablePatients.setItem(row,col,phn_wid)

                col+=1
                self.tablePatients.setColumnWidth(col, 230)
                self.tablePatients.setItem(row,col,phone_wid)

                col+=1
                btn_edit = QPushButton()
                btn_edit.setIcon(QIcon(self.edit_icon))
                btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
                # btn_edit.clicked.connect(partial(self.editPatient, row_data['id']))
                layout = QHBoxLayout()
                layout.addWidget(btn_edit)
                layout.setContentsMargins(0,0,0,0)
                widget = QWidget()
                widget.setLayout(layout)
                # widget.setFixedWidth(50)
                widget.setStyleSheet("border-radius:0px;background-color:transparent")
                self.tablePatients.setCellWidget(row, col, widget)

        except Exception as e:
            print(e)
    
    def fetchPatients(self):
        try:
            local_cursor = self.local_conn.cursor()
            local_cursor.execute("SELECT * FROM patient")
            data=dictfetchall(local_cursor)
            self.addDataToPatientTable(data)
        except Exception as e:
            print(e)
    
    def editPatient(self, patient_id):
        """Handle edit patient button click"""
        try:
            print(f"Edit patient with ID: {patient_id}")
            # TODO: Implement patient editing functionality
            # This could open an edit dialog or navigate to an edit page
        except Exception as e:
            print(f"Error editing patient: {e}")
        