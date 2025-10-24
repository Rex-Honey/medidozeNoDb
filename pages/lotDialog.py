from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QTimer, QDateTime,QTime
from PyQt6.QtGui import QIntValidator
from PyQt6 import uic
import os,time
from datetime import datetime
from otherFiles.common import dictfetchall

class LotDialog(QDialog):
    def __init__(self):
        super().__init__()
        from otherFiles.config import config, userData, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.localConn = localConn
        module_dir = os.path.dirname(__file__)
        uic.loadUi(os.path.join(module_dir, 'uiFiles', 'lotDialog.ui'), self)
        self.infoMsgMetadol.setText("")
        self.infoMsgMethadose.setText("")
        self.loginUser=self.userData['uid']
        self.localCursor=self.localConn.cursor()
        self.btnSaveLotMetadol.clicked.connect(self.saveLotMetadol)
        self.btnSaveLotMethadose.clicked.connect(self.saveLotMethadose)
        self.metadolFields = [
                (self.txtLotMetadol, self.errLotMetadol, "Lot number can't be blank"),
                (self.txtQtyMetadol, self.errQtyMetadol, "Quantity can't be blank"),
            ]

        self.methadoseFields = [
                (self.txtLotMethadose, self.errLotMethadose, "Lot number can't be blank"),
                (self.txtQtyMethadose, self.errQtyMethadose, "Quantity can't be blank"),
            ]
        for txtBox, errLabel, errMsg in self.metadolFields:
            txtBox.setStyleSheet("border-radius:10%;padding:8px;border:1px solid #e1e4e6;font-size:10pt")
            errLabel.setText("")
            if txtBox == self.txtQtyMetadol:
                txtBox.setValidator(QIntValidator())
        for txtBox, errLabel, errMsg in self.methadoseFields:
            txtBox.setStyleSheet("border-radius:10%;padding:8px;border:1px solid #e1e4e6;font-size:10pt")
            errLabel.setText("")
            if txtBox == self.txtQtyMethadose:
                txtBox.setValidator(QIntValidator())
        self.loadLatestLotDetails()

    def loadLatestLotDetails(self):
        try:
            self.localCursor.execute("SELECT * from din_groups")
            dinGroupDict=dictfetchall(self.localCursor)
            for dinGroup in dinGroupDict:
                if dinGroup['medication']=='Metadol':
                    metadolID=dinGroup['id']
                elif dinGroup['medication']=='Methadose':
                    methadoseID=dinGroup['id']

            self.localCursor.execute("SELECT lotNo, quantityRemaining, expiryDate FROM stock WHERE dinGroupID=? AND createdAt=(SELECT MAX(createdAt) FROM stock WHERE dinGroupID=?)", (metadolID,metadolID))
            metadolLotDetails=self.localCursor.fetchone()
            if metadolLotDetails:
                self.txtLotMetadol.setText(metadolLotDetails[0])
                self.txtQtyMetadol.setText(str(metadolLotDetails[1]))
                self.expiryMetadol.setDate(metadolLotDetails[2])

            self.localCursor.execute("SELECT lotNo, quantityRemaining, expiryDate FROM stock WHERE dinGroupID=? AND createdAt=(SELECT MAX(createdAt) FROM stock WHERE dinGroupID=?)", (methadoseID,methadoseID))
            methadoseLotDetails=self.localCursor.fetchone()
            if methadoseLotDetails:
                self.txtLotMethadose.setText(methadoseLotDetails[0])
                self.txtQtyMethadose.setText(str(methadoseLotDetails[1]))
                self.expiryMethadose.setDate(methadoseLotDetails[2])
        except Exception as e:
            print(e)

    def saveLotMetadol(self):
        try:
            fieldsEmpty=False
            for txtBox, errLabel, errMsg in self.metadolFields:
                errLabel.setText("")
                txtBox.setStyleSheet("border-radius:10%;padding:8px;border:1px solid #e1e4e6;font-size:10pt")
                if txtBox.text()=="":
                    errLabel.setText(errMsg)
                    txtBox.setStyleSheet("border-radius:10%;padding:8px;border:1px solid red;font-size:10pt")
                    fieldsEmpty=True
            if fieldsEmpty:
                return

            self.localCursor.execute("SELECT id FROM din_groups WHERE medication='Metadol'")
            metadolID=self.localCursor.fetchone()[0]
            
            metadolLot=self.txtLotMetadol.text()
            metadolQty=self.txtQtyMetadol.text()
            expiryMetadol=QDateTime(self.expiryMetadol.date(),QTime(0,0)).toPyDateTime()
            query="""
                INSERT INTO stock (dinGroupID, lotNo, quantityTotal, quantityRemaining, expiryDate, createdBy, updatedBy, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            paramValues=(metadolID, metadolLot, metadolQty, metadolQty, expiryMetadol, self.loginUser, self.loginUser, datetime.now(), datetime.now())
            self.localCursor.execute(query, paramValues)
            self.localConn.commit()
            self.infoMsgMetadol.setText("Lot saved successfully")
            self.infoMsgMetadol.setStyleSheet("background:#c5fac5;color:green;padding:8px;border-radius:none;font-size:9pt")
            QTimer.singleShot(4000, self.clear_info_messages)
        except Exception  as e:
            self.infoMsgMetadol.setText("Error saving lot")
            self.infoMsgMetadol.setStyleSheet("background:#fac8c5;color:red;padding:8px;border-radius:none;font-size:9pt")
            QTimer.singleShot(4000, self.clear_info_messages)
            print(e)

    def saveLotMethadose(self):
        try:
            fieldsEmpty=False
            for txtBox, errLabel, errMsg in self.methadoseFields:
                errLabel.setText("")
                txtBox.setStyleSheet("border-radius:10%;padding:8px;border:1px solid #e1e4e6;font-size:10pt")
                if txtBox.text()=="":
                    errLabel.setText(errMsg)
                    txtBox.setStyleSheet("border-radius:10%;padding:8px;border:1px solid red;font-size:10pt")
                    fieldsEmpty=True
            if fieldsEmpty:
                return

            self.localCursor.execute("SELECT id FROM din_groups WHERE medication='Methadose'")
            methadoseID=self.localCursor.fetchone()[0]
            
            methadoseLot=self.txtLotMethadose.text()
            methadoseQty=self.txtQtyMethadose.text()
            expiryMethadose=QDateTime(self.expiryMethadose.date(),QTime(0,0)).toPyDateTime()
            query="""
                INSERT INTO stock (dinGroupID, lotNo, quantityTotal, quantityRemaining, expiryDate, createdBy, updatedBy, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            paramValues=(methadoseID, methadoseLot, methadoseQty, methadoseQty, expiryMethadose, self.loginUser, self.loginUser, datetime.now(), datetime.now())
            self.localCursor.execute(query, paramValues)
            self.localConn.commit()

            self.infoMsgMethadose.setText("Lot saved successfully")
            self.infoMsgMethadose.setStyleSheet("background:#c5fac5;color:green;padding:8px;border-radius:none;font-size:9pt")
            QTimer.singleShot(4000, self.clear_info_messages)
        except Exception as e:
            self.infoMsgMethadose.setText("Error saving lot")
            self.infoMsgMethadose.setStyleSheet("background:#fac8c5;color:red;padding:8px;border-radius:none;font-size:9pt")
            QTimer.singleShot(4000, self.clear_info_messages)
            print(e)

    def clear_info_messages(self):
        self.infoMsgMetadol.setText("")
        self.infoMsgMetadol.setStyleSheet("padding:8px;")
        self.infoMsgMethadose.setText("")
        self.infoMsgMethadose.setStyleSheet("padding:8px;")

