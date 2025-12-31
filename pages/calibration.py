# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
from PyQt6 import uic
import os, pyodbc
from functools import partial
from otherFiles.common import sendPcbCommand, clearInfoMessages

class CalibrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import pcbComPort, leftPumpMedication, rightPumpMedication
        self.pcbComPort = pcbComPort
        self.leftPumpMedication = leftPumpMedication
        self.rightPumpMedication = rightPumpMedication
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "calibration.ui")
        uic.loadUi(ui_path, self)
        self.drugNameLeftCalibration.setText(self.leftPumpMedication)
        self.drugNameRightCalibration.setText(self.rightPumpMedication)
        self.btnCalibrateLeft.clicked.connect(partial(self.popUpCalibration, pumpPosition="Left"))
        self.btnCalibrateRight.clicked.connect(partial(self.popUpCalibration, pumpPosition="Right"))

    def popUpCalibration(self, pumpPosition):
        try:
            if not self.pcbComPort:
                self.infoCalibrationMain.setText("Machine is disconnected. Please connect the machine")
                self.infoCalibrationMain.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:11px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
                QTimer.singleShot(2000, partial(clearInfoMessages, self.infoCalibrationMain))
                return
        except Exception as e:
            print(e)
