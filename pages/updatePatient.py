from PyQt6.QtWidgets import QWidget, QFileDialog
from PyQt6.QtCore import QTimer
from PyQt6 import uic
import os, base64
from otherFiles.common import rootDir,defaultUserImage,roundImage
from datetime import datetime
from pages.patients import PatientsWindow

class UpdatePatientWindow(QWidget):
    def __init__(self, patientToEdit=None):
        super().__init__()
        from otherFiles.config import config, userData, localConn
        if config is None or localConn is None:
            print("Configuration not properly initialized. Please restart the application.")
            return
        self.config = config
        self.userData = userData
        self.patientToEdit = patientToEdit
        self.localConn = localConn
        uiPath = os.path.join(rootDir, "uiFiles", "updatePatient.ui")
        uic.loadUi(uiPath, self)
        self.btnLoadImg.clicked.connect(self.loadImage)
        self.btnRemoveImg.clicked.connect(self.removeImage)
        self.btnUpdate.clicked.connect(self.updatePatient)
        self.btnCancel.clicked.connect(self.cancelAndSwitch)
        self.populateFieldsForEdit()

    def populateFieldsForEdit(self):
        """Populate form fields with existing patient data for editing"""
        try:
            self.imageChanged=False
            self.imageRemoved=False
            self.patientName.setText(f"{self.patientToEdit['firstName']} {self.patientToEdit['lastName']}")
            self.patientPhone.setText(f"{self.patientToEdit['areaCode']}{self.patientToEdit['phone']}")
            
            if self.patientToEdit['image']:
                binary_data = base64.b64decode(self.patientToEdit['image'])
                round_img=roundImage(binary_data)
                self.lblPatientImg.setPixmap(round_img)
                self.patientHasImage=True
            else:
                self.patientHasImage=False
                self.removeImage()
        except Exception as e:
            print(f"Error populating fields for edit: {e}")

    def loadImage(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
            if filename:
                with open(filename, 'rb') as f:
                    imageData = f.read()
                    self.imageStr = base64.b64encode(imageData).decode('utf-8')
                pixmap=roundImage(imageData)
                self.lblPatientImg.setPixmap(pixmap)
                self.imageChanged=True
        except Exception as e:
            print(e)

    def removeImage(self):
        try:
            with open(defaultUserImage, 'rb') as f:
                imageData = f.read()
            pixmap=roundImage(imageData)
            self.lblPatientImg.setPixmap(pixmap)
            self.imageStr=""
            self.imageRemoved=True
        except Exception as e:
            print(e)

    def updatePatient(self):
        try:
            local_cursor = self.localConn.cursor()
            base_query = "UPDATE patient SET updatedBy=?, updatedDate=?"
            parameters = [self.userData['uid'], datetime.now()]

            if self.imageChanged or (self.patientHasImage and self.imageRemoved):
                base_query += ", image=?"
                parameters.append(self.imageStr)

            base_query += " WHERE id=?"
            parameters.append(self.patientToEdit['id'])
            local_cursor.execute(base_query, parameters)
            self.localConn.commit()

            self.infoUpdatePatient.setText("Patient details Updated Successfully !!")
            self.infoUpdatePatient.setStyleSheet("background:lightgreen;color:green;padding:10px;border-radius:none;font-weight: 400;")
            QTimer.singleShot(4000, self.clearInfoMessages)
        except Exception as e:
            print(e)

    def cancelAndSwitch(self):
        """Create a fresh instance of PharmacyUsersWindow and switch to it"""
        try:
            # Create a new instance of PharmacyUsersWindow
            freshPatients = PatientsWindow()
            
            # Find the parent stack widget
            from pages.pageContainer import PageContainer
            parent = self.parentWidget()
            while parent is not None:
                if hasattr(parent, "stack"):
                    break
                parent = parent.parentWidget()
            
            if parent is not None:
                # Create a new PageContainer with the fresh PharmacyUsersWindow
                pageContainer = PageContainer("Patients", freshPatients)
                
                # Add the new PageContainer to the stack and switch to it
                parent.stack.addWidget(pageContainer)
                parent.stack.setCurrentWidget(pageContainer)
            else:
                print("Main stack not found!")
        except Exception as e:
            print(f"Error creating fresh PatientsWindow: {e}")

    def clearInfoMessages(self):
        self.infoUpdatePatient.setText("")
        self.infoUpdatePatient.setStyleSheet("background:None;padding:10px;")

    # def switchEditPatient(self,id):
    #     try:
    #         self.removeImagePatient()
    #         self.changeImagePatient=False
    #         self.editingPatient=id
    #         local_cursor = self.local_conn.cursor()
    #         query = f"select * from patient where id='{id}';"
    #         local_cursor.execute(query)
    #         data = dictfetchall(local_cursor)
    #         self.patientName.setText(f"{data[0]['firstName']} {data[0]['lastName']}")
    #         self.patientPhone.setText(f"{data[0]['areaCode']}{data[0]['phone']}")
    #         if data[0]['image']:
    #             self.patientHasImage=True
    #             binary_data = base64.b64decode(data[0]['image'])
    #             round_img=self.round_image(binary_data)
    #             self.lblPatientImg.setPixmap(round_img)
    #         else:
    #             self.removeImagePatient()
    #             self.patientHasImage=False
    #         print("")
    #     except Exception as e:
    #         print(e)