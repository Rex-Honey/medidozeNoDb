
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc
from otherFiles.common import dictfetchall

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
            table.setColumnWidth(col,250)
            dinWid=QTableWidgetItem(str(din))
            dinWid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row,col,dinWid)

            col+=1
            table.setColumnWidth(col,446)
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
            btnRemoveDin.setStyleSheet("background-color:#fde5de;color:#f25022;margin:6px 80px 6px 0px;border-radius:6%")
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