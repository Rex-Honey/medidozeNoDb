# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
from PyQt6.QtCore import QObject, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from functools import partial
from dataclasses import dataclass
import os
import re
from datetime import datetime
from typing import Any, Optional
import serial
import time


@dataclass
class PumpContext:
    inputField: Any
    errorLabel: Any
    progressBar: Any
    pumpPosition: str
    commandTemplate: str
    blankError: str = "Quantity can't be blank"


QUANTITY_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")

ENABLED_BUTTON_STYLE = (
    "background:#48C9E3;"
    "color:#FFFFFF;"
    "border-radius:10%;"
    "padding:10px 40px;"
    "font-weight:900;"
    "font-size:11pt;"
)

DISABLED_BUTTON_STYLE = (
    "background:lightgrey;"
    "color:#FFFFFF;"
    "border-radius:10%;"
    "padding:10px 40px;"
    "font-weight:900;"
    "font-size:11pt;"
)

class InstantDoseWindow(QWidget):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.localConn = localConn
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "instantDose.ui")
        uic.loadUi(ui_path, self)

        self.floatValidator = QDoubleValidator()
        self.floatValidator.setRange(1, 999.99, 2)
        self.floatValidator.setNotation(QDoubleValidator.Notation.StandardNotation)

        localCursor = self.localConn.cursor()
        localCursor.execute("SELECT pump_position, medication from din_groups")
        pumpMedicationDict = {row[0]: row[1] for row in localCursor.fetchall()}
        if pumpMedicationDict:
            self.drugNameLeftInstantDose.setText(pumpMedicationDict['Left'])
            self.drugNameRightInstantDose.setText(pumpMedicationDict['Right'])

        self.pumpContext = {
            "LeftPumpBtn": PumpContext(
                inputField=self.txtDoseLeft,
                errorLabel=self.errDoseLeft,
                progressBar=self.progressBarLeft,
                pumpPosition="Left",
                commandTemplate="dispense_pump_a {dose}ml",
            ),
            "RightPumpBtn": PumpContext(
                inputField=self.txtDoseRight,
                errorLabel=self.errDoseRight,
                progressBar=self.progressBarRight,
                pumpPosition="Right",
                commandTemplate="dispense_pump_b {dose}ml",
            ),
        }

        self.fields = [(ctx.inputField, ctx.errorLabel) for ctx in self.pumpContext.values()]

        self._resetFieldStates()

        self.btnFillLeft.clicked.connect(partial(self.fillInstantDose,triggerBy="LeftPumpBtn"))
        self.txtDoseLeft.returnPressed.connect(partial(self.fillInstantDose,triggerBy="LeftPumpBtn"))
        self.txtDoseLeft.setValidator(self.floatValidator)
        self.btnFillRight.clicked.connect(partial(self.fillInstantDose,triggerBy="RightPumpBtn"))
        self.txtDoseRight.returnPressed.connect(partial(self.fillInstantDose,triggerBy="RightPumpBtn"))
        self.txtDoseRight.setValidator(self.floatValidator)
        self._applyButtonStyles()

        self.worker = Worker()
        self.worker.instantFill.connect(self.responseInstantFill)
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)
        self._workerStartedSlot = None

    def _resetFieldStates(self):
        for inputField, errLabel in self.fields:
            self.setState(inputField, "ok")
            errLabel.setText("")

    def _setButtonsEnabled(self, enabled: bool):
        self.btnFillLeft.setEnabled(enabled)
        self.btnFillRight.setEnabled(enabled)
        self._applyButtonStyles()

    def _applyButtonStyles(self):
        if self.btnFillLeft.isEnabled():
            self.btnFillLeft.setStyleSheet(ENABLED_BUTTON_STYLE)
        else:
            self.btnFillLeft.setStyleSheet(DISABLED_BUTTON_STYLE)

        if self.btnFillRight.isEnabled():
            self.btnFillRight.setStyleSheet(ENABLED_BUTTON_STYLE)
        else:
            self.btnFillRight.setStyleSheet(DISABLED_BUTTON_STYLE)

    def setState(self,widget, state):
        widget.setProperty("ok2", state == "ok")
        widget.setProperty("error2", state == "err")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def responseInstantFill(self,status,msg):
        try:
            if status == 'error':
                print("Error: ",msg)
                if "could not open port" in msg:
                    self.infoInstantFill.setText("Machine is disconnected. Please connect the machine")
                else:
                    self.infoInstantFill.setText("Something went wrong. Please try again later.")
                self.infoInstantFill.setStyleSheet("background:#fac8c5;border:1px solid #fac8c5;color:red;padding:9px;border-radius:none;font-size:9pt;font-family:Nirmala UI;")
            else:
                self.infoInstantFill.setText("Filling Done")
                self.infoInstantFill.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
            QTimer.singleShot(4000, self.clearInfoMessages)
            self.progressBarLeft.setRange(0, 100)  # Reset progress bar
            self.progressBarRight.setRange(0, 100)  # Reset progress bar
            self._setButtonsEnabled(True)
            self.workerThread.quit()
            self.workerThread.wait()
            if self._workerStartedSlot is not None:
                try:
                    self.workerThread.started.disconnect(self._workerStartedSlot)
                except TypeError:
                    pass
                self._workerStartedSlot = None
            print("Response Done")
        except Exception as e:
            print(e)
            self._setButtonsEnabled(True)
            self.workerThread.quit()
            self.workerThread.wait()
            if self._workerStartedSlot is not None:
                try:
                    self.workerThread.started.disconnect(self._workerStartedSlot)
                except TypeError:
                    pass
                self._workerStartedSlot = None

    def fillInstantDose(self,triggerBy=None):
        try:
            context = self.pumpContext.get(triggerBy)
            if context is None:
                print(f"Unknown trigger {triggerBy}")
                return

            self._resetFieldStates()

            dose = self._parseDose(context)
            if dose is None:
                return

            localCursor = self.localConn.cursor()
            medicationID = self._fetchMedicationId(localCursor, context)
            if medicationID is None:
                context.errorLabel.setText("Pump configuration missing")
                self.setState(context.inputField, "err")
                return

            lotDetails = self._fetchLotDetails(localCursor, medicationID)
            if (
                lotDetails
                and lotDetails['quantityRemaining'] is not None
                and lotDetails['quantityRemaining'] < dose
            ):
                context.errorLabel.setText(
                    f"Unable to dispense. Only {lotDetails['quantityRemaining']}ml left"
                )
                self.setState(context.inputField, "err")
                return

            if self.workerThread.isRunning():
                print("Worker thread is already running. Ignoring new request.")
                return
            self._setButtonsEnabled(False)
            context.progressBar.setRange(0, 0)
            self.worker.count=0
            command = context.commandTemplate.format(dose=dose)

            job = partial(
                self.worker.fillInstantDoseWorker,
                self.localConn,
                command,
                dose,
                medicationID,
                lotDetails,
                self.userData['uid'],
            )

            if self._workerStartedSlot is not None:
                try:
                    self.workerThread.started.disconnect(self._workerStartedSlot)
                except TypeError:
                    pass

            self._workerStartedSlot = job
            self.workerThread.started.connect(job)
            self.workerThread.start()
        except Exception as e:
            print(e)
            self._setButtonsEnabled(True)

    def _parseDose(self, context: PumpContext) -> Optional[float]:
        rawValue = context.inputField.text().strip()
        if rawValue == "":
            context.errorLabel.setText(context.blankError + " ")
            self.setState(context.inputField, "err")
            return None

        try:
            dose = int(rawValue)
            return float(dose)
        except ValueError:
            try:
                dose = float(rawValue)
            except ValueError:
                context.errorLabel.setText("Only numbers are allowed in quantity")
                self.setState(context.inputField, "err")
                return None

        if not QUANTITY_PATTERN.match(rawValue):
            context.errorLabel.setText("Only 2 digit after decimal are allowed")
            self.setState(context.inputField, "err")
            return None

        return dose

    def _fetchMedicationId(self, cursor, context: PumpContext) -> Optional[int]:
        cursor.execute(
            "SELECT id FROM din_groups WHERE pump_position=?;",
            (context.pumpPosition,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

    def _fetchLotDetails(self, cursor, medicationId: int) -> Optional[dict]:
        cursor.execute(
            "SELECT lotNo, quantityRemaining FROM stock "
            "WHERE dinGroupID=? AND createdAt=("
            "SELECT MAX(createdAt) FROM stock WHERE dinGroupID=?)",
            (medicationId, medicationId),
        )
        lotDetails = cursor.fetchone()
        if lotDetails:
            lotNo, quantityRemaining = lotDetails
            try:
                numericQuantity = float(quantityRemaining)
            except (TypeError, ValueError):
                numericQuantity = None
            return {
                "lotNo": lotNo,
                "quantityRemaining": numericQuantity,
                "rawQuantityRemaining": quantityRemaining,
            }
        return None
    
    def clearInfoMessages(self):
        try:
            self.infoInstantFill.setText("")
            self.infoInstantFill.setStyleSheet("background:none")
        except Exception as e:
            print(e)

class Worker(QObject):
    instantFill=pyqtSignal(str,str)
    def __init__(self):
        super().__init__()
        self.count = 0
        from otherFiles.config import pcbComPort
        self.pcbComPort = pcbComPort
    def sendPcbCommand(self,command):
        try:
            print(command)
            baudrate=115200
            command += '\n'
            with serial.Serial(self.pcbComPort,baudrate, timeout=4) as ser:
                ser.write(command.encode())
                time.sleep(0.1)
                count=1
                while True:
                    response = ser.readline().decode()
                    print(f"send_pcb_command response {count} -- ",response)
                    if "pump - single" in response:
                        print("Single pump connected")
                    if response in ("Press Y for yes and N for no then press Enter\r\n", "put quantity for calibration in ml\r\n","enter Y for yes and N for no\r\n","Machine is Ready to despense\r\n","wrong input. pls put clb qunatity in numaric format"):
                        print("Serial port closed end of commands")
                        break
                    elif response=="":
                        print("Serial port closed blank response")
                        break
                    count+=1
            return "Success"
        except Exception as e:
            print("send_pcb_command error",e)
            return e

    def fillInstantDoseWorker(self,localConn,command,dose,medicationID,lotDetails,loginUser):
        try:
            print(" -- instant Fill Dose Worker --")
            self.count+=1
            if self.count>1:
                return
            machineResponse=self.sendPcbCommand(command)
            if machineResponse == "Success":
                localCursor = localConn.cursor()
                if lotDetails:
                    lotNo=lotDetails['lotNo']
                    totRemaining=lotDetails['quantityRemaining']
                    if totRemaining is not None:
                        remaining=totRemaining-dose
                        query = "UPDATE stock SET quantityRemaining=?, updatedBy=?, updatedAt=? WHERE dinGroupID=? AND lotNo=?"
                        values=(remaining,loginUser,datetime.now(),medicationID,lotNo)
                        localCursor.execute(query,values)
                    else:
                        print("Skipping stock quantity update due to non-numeric remaining quantity")
                else:
                    lotNo=None
                query = "INSERT INTO instantDoseLogs (idlMedicationID,idlDose,idlLotNo,createdBy,updatedBy, createdDate, updatedDate) VALUES (?,?,?,?,?,?,?)"
                values=(medicationID,dose,lotNo,loginUser,loginUser,datetime.now(),datetime.now())
                localCursor.execute(query,values)

                localConn.commit()
                self.instantFill.emit('success','ok')
            else:
                self.instantFill.emit('error',str(machineResponse))
        except Exception as e:
            print(e)
            self.instantFill.emit('error',str(e))
