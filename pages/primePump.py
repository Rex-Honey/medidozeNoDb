from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import os, pyodbc
from otherFiles.common import sendPcbCommand
from functools import partial



class PrimeWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn, leftPumpMedication, rightPumpMedication
        self.config = config
        self.userData = userData
        self.local_conn = localConn
        self.leftPumpMedication = leftPumpMedication
        self.rightPumpMedication = rightPumpMedication
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "primePump.ui")
        uic.loadUi(ui_path, self)
        self.drugNameLeftPrime.setText(self.leftPumpMedication)
        self.drugNameRightPrime.setText(self.rightPumpMedication)

        self.worker = Worker()
        self.worker.primePump.connect(self.responsePrimePump)
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)
        self.workerStartedSlot = None
        self.btnPrimePumpLeftPrime.clicked.connect(partial(self.primePump,pumpPosition="Left"))
        self.btnPrimePumpRightPrime.clicked.connect(partial(self.primePump,pumpPosition="Right"))

    def primePump(self,pumpPosition=None):
        try:
            print("primePump")
            self.worker.count=0
            self.btnPrimePumpLeftPrime.setDisabled(True)
            self.btnPrimePumpLeftPrime.setStyleSheet("padding:10px 20px;\nborder:none;\nbackground:lightgrey;\ncolor:white;\nborder-radius:6%;\nfont-size:12pt;\nfont-weight:700")
            self.btnPrimePumpRightPrime.setDisabled(True)
            self.btnPrimePumpRightPrime.setStyleSheet("padding:10px 20px;\nborder:none;\nbackground:lightgrey;\ncolor:white;\nborder-radius:6%;\nfont-size:12pt;\nfont-weight:700")
            if self.workerStartedSlot is not None:
                try:
                    self.workerThread.started.disconnect(self.workerStartedSlot)
                except TypeError:
                    pass
                self.workerStartedSlot = None
            if pumpPosition == "Left":
                self.workerStartedSlot = partial(self.worker.primePumpWorker, "dispense_pump_a 50ml")
                self.workerThread.started.connect(self.workerStartedSlot)
                self.workerThread.start()
            else:
                self.workerStartedSlot = partial(self.worker.primePumpWorker, "dispense_pump_b 50ml")
                self.workerThread.started.connect(self.workerStartedSlot)
                self.workerThread.start()
        except Exception as e:
            print(e)

    def responsePrimePump(self, status, msg):
        try:
            self.btnPrimePumpLeftPrime.setDisabled(False)
            self.btnPrimePumpLeftPrime.setStyleSheet("padding:10px 20px;\nborder:none;\nbackground:#48C9E3;\ncolor:white;\nborder-radius:6%;\nfont-size:12pt;\nfont-weight:700")
            self.btnPrimePumpRightPrime.setDisabled(False)
            self.btnPrimePumpRightPrime.setStyleSheet("padding:10px 20px;\nborder:none;\nbackground:#48C9E3;\ncolor:white;\nborder-radius:6%;\nfont-size:12pt;\nfont-weight:700")
            if status=="error":
                print("Error: ",msg)
                if "could not open port" in msg:
                    self.infoPrime.setText("Machine is disconnected. Please connect the machine")
                else:
                    self.infoPrime.setText("Something went wrong. Please try again later.")
                self.infoPrime.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:11px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
            else:
                self.infoPrime.setText("Prime Pump Done")
                self.infoPrime.setStyleSheet("background:lightgreen;border:1px solid lightgreen;color:green;padding:5px;border-radius:none;font-size:9pt")
            QTimer.singleShot(2000, self.clearInfoMessages)
            self.workerThread.quit()
            self.workerThread.wait()
            if self.workerStartedSlot is not None:
                try:
                    self.workerThread.started.disconnect(self.workerStartedSlot)
                except TypeError:
                    pass
                self.workerStartedSlot = None
        except Exception as e:
            print(e)

    def clearInfoMessages(self):
        try:
            self.infoPrime.setText("")
            self.infoPrime.setStyleSheet("background:none")
        except Exception as e:
            print(e)

class Worker(QObject):
    primePump=pyqtSignal(str,str)
    def __init__(self):
        super().__init__()
        from otherFiles.config import pcbComPort
        self.pcbComPort = pcbComPort

    def primePumpWorker(self,command):
        try:
            print(" -- prime Pump Worker --")
            machineResponse = sendPcbCommand(
                self.pcbComPort,
                command,
                logCommand=True,
            )
            if machineResponse == "Success":
                self.primePump.emit('success','ok')
            else:
                self.primePump.emit('error',str(machineResponse))
        except Exception as e:
            self.primePump.emit('error',str(e))
