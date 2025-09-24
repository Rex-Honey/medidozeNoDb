
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