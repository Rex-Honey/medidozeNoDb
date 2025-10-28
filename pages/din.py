from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QPushButton, QWidget, QHBoxLayout, QMessageBox, QDialog, QVBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QIntValidator
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import dictfetchall
from functools import partial
from datetime import datetime


class DinWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn, updateLeftPump, updateRightPump
        self.config = config
        self.userData = userData
        self.local_conn = localConn
        self.updateLeftPump = updateLeftPump
        self.updateRightPump = updateRightPump
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "din.ui")
        uic.loadUi(ui_path, self)
        
        self.comboBoxLeftPump.currentTextChanged.connect(self.medicationChanged)
        self.btnAddDinLeft.clicked.connect(partial(self.popUpAddDin,pumpPosition="Left"))
        self.btnAddDinRight.clicked.connect(partial(self.popUpAddDin,pumpPosition="Right"))
        self.btnSaveMedications.clicked.connect(self.saveMedications)
        self.switchViewDins()


    def switchViewDins(self):
        try:
            self.infoViewDins.setText("")
            self.infoViewDins.setStyleSheet("background:none;padding:12px;")
    
            query = f"select id, medication,pump_position from din_groups"
            localCursor = self.local_conn.cursor()
            localCursor.execute(query)
            data=dictfetchall(localCursor)
            if data:
                self.comboBoxLeftPump.clear()
                for row in data:
                    self.comboBoxLeftPump.addItem(row['medication'])
                    if row['pump_position']=='Left':
                        leftPumpMedication=row['medication']
                self.comboBoxLeftPump.setCurrentText(leftPumpMedication)
        except Exception as e:
            print(e)

    def addDinToTable(self,din,drugName,strength,table):
        try:
            row=table.rowCount()
            table.setRowCount(row+1)

            col=0
            table.setColumnWidth(col,240)
            dinWid=QTableWidgetItem(str(din))
            dinWid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row,col,dinWid)

            col+=1
            table.setColumnWidth(col,436)
            drugWid=QTableWidgetItem(drugName)
            drugWid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row,col,drugWid)

            col+=1
            table.setColumnWidth(col,200)
            strengthWid=QTableWidgetItem(strength)
            strengthWid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row,col,strengthWid)

            col+=1
            btnRemoveDin = QPushButton("Remove")
            btnRemoveDin.setStyleSheet("background-color:#fde5de;color:#f25022;margin:9px 80px 6px 0px;border-radius:6%;font-weight:400;font-size:10pt;padding:0px")
            btnRemoveDin.setFixedSize(160,40)
            btnRemoveDin.setCursor(Qt.CursorShape.PointingHandCursor)
            btnRemoveDin.clicked.connect(partial(self.removeDinFromTable,table,din,row))
            
            buttonWidget = QWidget()
            buttonWidget.setStyleSheet("background: transparent;")
            table.setCellWidget(row, col, buttonWidget)

            buttonLayout = QHBoxLayout(buttonWidget)
            buttonLayout.addStretch() 
            buttonLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the layout
            buttonLayout.setContentsMargins(10, 0, 5, 0)
            buttonLayout.addWidget(btnRemoveDin)
        except Exception as e:
            print(e)

    def medicationChanged(self):
        try:
            self.dinTableLeft.setRowCount(0)
            self.dinTableRight.setRowCount(0)
            leftMedication=self.comboBoxLeftPump.currentText()
            query = f"select din_groups.medication, din.din_number, din.strength, din.din_group_id from din join din_groups on din.din_group_id=din_groups.id"
            local_cursor = self.local_conn.cursor()
            local_cursor.execute(query)
            data=dictfetchall(local_cursor)
            print("")
            if data:
                for row in data:
                    if row['medication']==leftMedication:
                        self.addDinToTable(row['din_number'], row['medication'], row['strength'],self.dinTableLeft)
                    else:
                        self.addDinToTable(row['din_number'], row['medication'], row['strength'],self.dinTableRight)
                        self.lblRightMedication.setText(row['medication'])
        except Exception as e:
            print(e)

    def removeDinFromTable(self,table,din,row):
        try:
            module_dir = os.path.dirname(__file__)
            reply = QMessageBox() #right qmessagebox
            reply.setWindowIcon(QIcon(os.path.join(module_dir, 'images', 'medidoze-icon.ico')))
            reply.setIcon(QMessageBox.Icon.Warning)
            reply.setWindowTitle('Medidoze alert')
            reply.setText("Do you want to remove this DIN?")
            reply.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            reply.setDefaultButton(QMessageBox.StandardButton.No)
            result = reply.exec()

            if result == QMessageBox.StandardButton.Yes:
                for i in range(table.rowCount()):
                    if table.item(i, 0) and table.item(i, 0).text() == str(din):
                        query = f"DELETE FROM din WHERE din_number = {din}"
                        local_cursor = self.local_conn.cursor()
                        local_cursor.execute(query)
                        self.local_conn.commit()
                        table.removeRow(i)
                        self.infoViewDins.setText("DIN removed successfully")
                        self.infoViewDins.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
                        QTimer.singleShot(4000, self.clearinfoViewDins)
                        break
        except Exception as e:
            print(e)

    def popUpAddDin(self,pumpPosition):
        try:
            if pumpPosition=="Left":
                medication=self.comboBoxLeftPump.currentText()
            else:
                medication=self.lblRightMedication.text()
            dinLabel = QLabel("DIN")
            dinLabel.setStyleSheet("font-size: 14px; font-weight: bold;font-family: Nirmala UI;")

            dinInput = QLineEdit()
            dinInput.setValidator(QIntValidator())
            dinInput.setMaxLength(12)
            dinInput.setPlaceholderText("Enter DIN")
            dinInput.setStyleSheet("padding:7px;border:1px solid #e1e4e6;font-size:11pt;border-radius:10%") 

            errDin = QLabel("")
            errDin.setStyleSheet("color:red;")

            strengthLabel = QLabel("Strength")
            strengthLabel.setStyleSheet("font-size: 14px; font-weight: bold;font-family: Nirmala UI;")

            strengthInput = QLineEdit()
            strengthInput.setPlaceholderText("Enter Strength")
            strengthInput.setStyleSheet("padding:7px;border:1px solid #e1e4e6;font-size:11pt;border-radius:10%")

            errStrength = QLabel("")
            errStrength.setStyleSheet("color: red;")

            saveButton = QPushButton("Add")
            saveButton.setStyleSheet("border-radius:10%;background:#033E89;font-weight: 700;color:white;padding:9px;font-size:10pt")
            saveButton.setCursor(Qt.CursorShape.PointingHandCursor)
            saveButton.clicked.connect(partial(self.saveDin,dinInput,strengthInput,medication,errDin,errStrength))

            self.tempLbl=QLabel("")
            self.tempLbl.setStyleSheet("padding:2px;")

            dinLayout = QVBoxLayout()
            dinLayout.setSpacing(2)
            dinLayout.addWidget(dinLabel)
            dinLayout.addWidget(dinInput)
            dinLayout.addWidget(errDin)

            strengthLayout = QVBoxLayout()
            strengthLayout.setSpacing(2)
            strengthLayout.addWidget(strengthLabel)
            strengthLayout.addWidget(strengthInput)
            strengthLayout.addWidget(errStrength)

            btnLayout = QVBoxLayout()
            btnLayout.setSpacing(4)
            btnLayout.addWidget(self.tempLbl)
            btnLayout.addWidget(saveButton)

            dialogLayout = QVBoxLayout()
            dialogLayout.setSpacing(10)
            dialogLayout.addLayout(dinLayout)
            dialogLayout.addLayout(strengthLayout)
            dialogLayout.addLayout(btnLayout)

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Add DIN to {medication}")
            dialog.setFixedSize(300, 260)
            dialog.setStyleSheet("background:#FFFFFF;")
            dialog.setModal(True)
            dialog.setLayout(dialogLayout)
            dialog.exec()
        except Exception as e:
            print(e)

    def saveDin(self,dinWidget,strengthWidget,medication,errDin,errStrength):
        try:
            errDin.setText("")
            errStrength.setText("")

            din=dinWidget.text()
            strength=strengthWidget.text()
            if str(din).strip()=='':
                errDin.setText("DIN is required")
                return
            if str(strength).strip()=='':
                errStrength.setText("Strength is required")
                return
            
            query = f"select id from din_groups where medication='{medication}'"
            localCursor = self.local_conn.cursor()
            localCursor.execute(query)
            data=dictfetchall(localCursor)
            if data:
                dinGroupID=data[0]['id']
                query = f"insert into din (din_number, strength, din_group_id, createdBy, updatedBy, createdDate, updatedDate) values (?,?,?,?,?,?,?)"
                localCursor.execute(query, (din,strength,dinGroupID,self.userData['uid'],self.userData['uid'],datetime.now(),datetime.now()))
                self.local_conn.commit()
                self.tempLbl.setText("DIN added successfully !!")
                self.tempLbl.setStyleSheet("background:lightgreen;color:green;padding:2px;border-radius:none")
                QTimer.singleShot(900, self.clearTempLbl)
            dinWidget.setText("")
            strengthWidget.setText("")
        except Exception as e:
            print(e)

    def saveMedications(self):
        try:
            leftMedication=self.comboBoxLeftPump.currentText()
            local_cursor = self.local_conn.cursor()
            if leftMedication=='Metadol':
                query = f"update din_groups set pump_position='Left' where medication='Metadol'"
                local_cursor.execute(query)

                query = f"update din_groups set pump_position='Right' where medication='Methadose'"
                local_cursor.execute(query)
                self.updateLeftPump('Metadol')
                self.updateRightPump('Methadose')
            else:
                query = f"update din_groups set pump_position='Left' where medication='Methadose'"
                local_cursor.execute(query)

                query = f"update din_groups set pump_position='Right' where medication='Metadol'"
                local_cursor.execute(query)
                self.updateLeftPump('Methadose')
                self.updateRightPump('Metadol')
            self.local_conn.commit()
            self.infoViewDins.setText("Medications saved successfully")
            self.infoViewDins.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
            QTimer.singleShot(4000, self.clearinfoViewDins)
        except Exception as e:
            print(e)

    def clearinfoViewDins(self):
        self.infoViewDins.setText("")
        self.infoViewDins.setStyleSheet("background:none;padding:12px;")

    def clearTempLbl(self):
        self.tempLbl.setText("")
        self.tempLbl.setStyleSheet("background:none;padding:2px;")