from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QPushButton, QWidget, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import dictfetchall
from functools import partial


class DinWindow(QWidget):
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
        ui_path = os.path.join(rootDir, "uiFiles", "din.ui")
        uic.loadUi(ui_path, self)
        
        self.comboBoxLeftPump.currentTextChanged.connect(self.medicationChanged)
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

    def clearinfoViewDins(self):
        self.infoViewDins.setText("")
        self.infoViewDins.setStyleSheet("background:none;padding:12px;")