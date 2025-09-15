# pages/settings_page.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os, pyodbc

class SettingsWindow(QWidget):
    def __init__(self, config, connString, userData):
        super().__init__()
        self.config = config
        self.connString = connString
        self.userData = userData
        self.local_conn = pyodbc.connect(connString)
        rootDir = os.path.dirname(os.path.dirname(__file__))
        ui_path = os.path.join(rootDir, "uiFiles", "settings.ui")
        uic.loadUi(ui_path, self)


    # def SaveOatRxSettings(self):
    #     try:
    #         self.config['oatRxPharmacyId']=self.txtOatrxPharmacyId.text().strip()
    #         self.config['webhookFillApiUrl']=self.txtWebhookUrl.text().strip()
    #         self.config['oatRxGetAiDatesApiUrl']=self.txtAiDateUrl.text().strip()
    #         self.config['oatApiToken']=self.txtApiToken.text().strip()
    #         with open(os.path.join(self.medidozeDir, 'config.json'), 'w', encoding='utf-8') as f:
    #             json.dump(self.config, f, indent=4)
    #         self.infoSettings.setText(f"OatRx settings saved successfully")
    #         self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
    #         QTimer.singleShot(4000, self.clear_info_messages)
    #     except Exception as e:
    #         print(e)

    # def changeLabelType(self):
    #     try:
    #         if self.comboLabelType.currentText()=="Normal Label":
    #             self.spinLeftMargin.setValue(self.normalLeftMargin)
    #             self.spinTopMargin.setValue(self.normalTopMargin)
    #             self.spinParaWidth.setValue(self.normalParaWidth)
    #             self.spinLineSpacing.setValue(self.normalLineSpacing)
    #             self.spinSideTextBottomMargin.setValue(self.normalSideTextBottomMargin)
    #         else:
    #             self.spinLeftMargin.setValue(self.invertedLeftMargin)
    #             self.spinTopMargin.setValue(self.invertedTopMargin)
    #             self.spinParaWidth.setValue(self.invertedParaWidth)
    #             self.spinLineSpacing.setValue(self.invertedLineSpacing)
    #             self.spinSideTextBottomMargin.setValue(self.invertedSideTextBottomMargin)
    #     except Exception as e:
    #         print(e)

    # def loadLabelSettings(self):
    #     try:
    #         with open(os.path.join(self.medidozeDir, 'lblSettings.json'), 'r', encoding='utf-8') as f:
    #             lblSettings=json.load(f)

    #         print("Label settings file found")
    #         self.defaultPrinter=lblSettings['printer']
    #         self.labelFontSize=lblSettings['fontSize']
    #         self.labelType=lblSettings['labelType']
    #         self.normalLeftMargin=lblSettings['normalLeftMargin']
    #         self.normalTopMargin=lblSettings['normalTopMargin']
    #         self.normalParaWidth=lblSettings['normalParaWidth']
    #         self.normalLineSpacing=lblSettings['normalLineSpacing']
    #         self.normalSideTextBottomMargin=lblSettings['normalSideTextBottomMargin']

    #         self.invertedLeftMargin=lblSettings['invertedLeftMargin']
    #         self.invertedTopMargin=lblSettings['invertedTopMargin']
    #         self.invertedParaWidth=lblSettings['invertedParaWidth']
    #         self.invertedLineSpacing=lblSettings['invertedLineSpacing']
    #         self.invertedSideTextBottomMargin=lblSettings['invertedSideTextBottomMargin']

    #     except FileNotFoundError:
    #         print("Label settings file not found")
    #         self.defaultPrinter=win32print.GetDefaultPrinter()
    #         self.labelFontSize=10
    #         self.labelType='normal'
    #         self.normalLeftMargin=0
    #         self.normalTopMargin=0
    #         self.normalParaWidth=260
    #         self.normalLineSpacing=12
    #         self.normalSideTextBottomMargin=50

    #         self.invertedLeftMargin=0
    #         self.invertedTopMargin=0
    #         self.invertedParaWidth=260
    #         self.invertedLineSpacing=12
    #         self.invertedSideTextBottomMargin=50
    #         lblSettings={
    #             'printer':self.defaultPrinter,
    #             'fontSize':self.labelFontSize,
    #             'labelType':self.labelType,

    #             'normalLeftMargin':self.normalLeftMargin,
    #             'normalTopMargin':self.normalTopMargin,
    #             'normalParaWidth':self.normalParaWidth,
    #             'normalLineSpacing':self.normalLineSpacing,
    #             'normalSideTextBottomMargin':self.normalSideTextBottomMargin,

    #             'invertedLeftMargin':self.invertedLeftMargin,
    #             'invertedTopMargin':self.invertedTopMargin,
    #             'invertedParaWidth':self.invertedParaWidth,
    #             'invertedLineSpacing':self.invertedLineSpacing,
    #             'invertedSideTextBottomMargin':self.invertedSideTextBottomMargin
    #         }
    #         with open(os.path.join(self.medidozeDir, 'lblSettings.json'), 'w', encoding='utf-8') as f:
    #             json.dump(lblSettings, f, indent=4)
    #     except Exception as e:
    #         print(e)
    #         return

    # def saveLabelSettings(self):
    #     try:
    #         self.defaultPrinter=self.selectPrinterCombo.currentText()
    #         self.labelFontSize=int(self.comboFontSize.currentText())
    #         self.labelType=("normal" if self.comboLabelType.currentText()=="Normal Label" else "inverted")
    #         if self.labelType=="normal":
    #             self.normalLeftMargin=self.spinLeftMargin.value()
    #             self.normalTopMargin=self.spinTopMargin.value()
    #             self.normalParaWidth=self.spinParaWidth.value()
    #             self.normalLineSpacing=self.spinLineSpacing.value()
    #             self.normalSideTextBottomMargin=self.spinSideTextBottomMargin.value()
    #         else:
    #             self.invertedLeftMargin=self.spinLeftMargin.value()
    #             self.invertedTopMargin=self.spinTopMargin.value()
    #             self.invertedParaWidth=self.spinParaWidth.value()
    #             self.invertedLineSpacing=self.spinLineSpacing.value()
    #             self.invertedSideTextBottomMargin=self.spinSideTextBottomMargin.value()
    #         lblSettings={
    #             'printer':self.defaultPrinter,
    #             'fontSize':self.labelFontSize,
    #             "labelType":self.labelType,
    #             'normalLeftMargin':self.normalLeftMargin,
    #             'normalTopMargin':self.normalTopMargin,
    #             'normalParaWidth':self.normalParaWidth,
    #             'normalLineSpacing':self.normalLineSpacing,
    #             'normalSideTextBottomMargin':self.normalSideTextBottomMargin,

    #             'invertedLeftMargin':self.invertedLeftMargin,
    #             'invertedTopMargin':self.invertedTopMargin,
    #             'invertedParaWidth':self.invertedParaWidth,
    #             'invertedLineSpacing':self.invertedLineSpacing,
    #             'invertedSideTextBottomMargin':self.invertedSideTextBottomMargin
    #         }
    #         with open(os.path.join(self.medidozeDir, 'lblSettings.json'), 'w', encoding='utf-8') as f:
    #             json.dump(lblSettings, f, indent=4)
    #         self.infoSettings.setText(f"Label settings saved successfully")
    #         self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
    #         QTimer.singleShot(4000, self.clear_info_messages)
    #     except Exception as e:
    #         print(e)
            
    # def getPrinterList(self):
    #     try:
    #         printers = []
    #         printersList=[]
    #         for i in range(self.selectPrinterCombo.count()):
    #             if i>0:
    #                 self.selectPrinterCombo.removeItem(1)
    #         for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
    #             printer_info = {
    #                 'name': printer[2],  # Printer name
    #                 'port': printer[1],  # Port name
    #                 'description': printer[2],  # Description
    #                 'is_default': printer[2] == win32print.GetDefaultPrinter()  # Check if it's the default printer
    #             }
    #             printers.append(printer_info)
    #             printersList.append(printer[2])
    #             self.selectPrinterCombo.addItem(printer[2])
            
    #         if self.defaultPrinter and self.defaultPrinter in printersList:
    #             self.selectPrinterCombo.setCurrentText(self.defaultPrinter)
    #         print()
    #     except Exception as e:
    #         print(e)

    # def responseUpdateDispenseData(self,status,message,triggerBy):
    #     try:
    #         self.syncMovie.stop()
    #         if triggerBy=="Save":
    #             self.frameSettingBtns.show()
    #             self.frameSync.hide()
    #             self.infoSettings.setText(message)
    #             self.infoSettings.show()
    #             if status=="success":
    #                 self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
    #                 self.config['winrxDbName']=self.txt_database.text()
    #                 with open(os.path.join(self.medidozeDir, 'config.json'), 'w', encoding='utf-8') as f:
    #                     json.dump(self.config, f, indent=4)
    #                 self.cancel_settings_event()
    #                 for btn in (self.sbtn_dash,self.sbtn_dispense,self.sbtnInstantDose,self.sbtn_primePump,self.sbtnCalibrate,self.sbtn_patients,self.sbtn_view_din,self.sbtn_view_users,self.sbtn_stock,self.sbtn_reports):
    #                     btn.show()

    #             else:
    #                 self.infoSettings.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
    #         else:
    #             self.animateLbl.hide()
    #             self.btnSync.show()
    #             self.infoViewDispense.setText(message)
    #             self.infoViewDispense.show()
    #             if status=="success":
    #                 self.infoViewDispense.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
    #             else:
    #                 self.infoViewDispense.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
    #         QTimer.singleShot(4000, self.clear_info_messages)
    #         self.worker_thread.quit()
    #         self.worker_thread.wait()
    #         self.worker_thread.disconnect()
    #     except Exception as e:
    #         print(e)

    # def save_database_credential(self,triggerBy=None):
    #     try:
    #         module_dir = os.path.dirname(__file__)
    #         self.syncMovie = QMovie(os.path.join(module_dir, 'images', 'diagram3.gif'))
    #         if triggerBy=="Save":
    #             self.err_database.setText("")
    #             self.txt_database.setStyleSheet("border:1px solid  #e1e4e6;font-weight: 500;padding:10px;")
    #             database=self.txt_database.text()
    #             if str(database).strip() =="":
    #                 self.err_database.setText("Database name can't be blank")
    #                 self.txt_database.setStyleSheet("border:1px solid red;font-weight: 500;border-radius:10%;padding:10px;")
    #                 return
                
    #             self.infoSettings.setText(f"Connected to {database} database")
    #             self.infoSettings.setStyleSheet("background:lightgreen;color:green;padding:12px;border-radius:none")
    #             QTimer.singleShot(4000, self.clear_info_messages)
    #             self.animateLblSettings.setMovie(self.syncMovie)
    #             self.frameSettingBtns.hide()
    #             self.frameSync.show()
    #         else:
    #             database=self.config['winrxDbName']
    #             self.animateLbl.setMovie(self.syncMovie)
    #             self.animateLbl.show()
    #             self.btnSync.hide()
    #         try:
    #             live_db = f'DRIVER={{SQL Server}};SERVER={self.config['server']};DATABASE={database};UID={self.config['username']};PWD={self.config['password']};'
    #             self.live_conn = pyodbc.connect(live_db)
    #             self.syncMovie.start()
    #             self.worker.count=0
    #             self.worker_thread.start()
    #             self.worker_thread.started.connect(partial(self.worker.update_dispense_data,self.local_conn,self.live_conn,self.loginUser,triggerBy,self.config['oatRxGetAiDatesApiUrl'],self.config['oatRxPharmacyId'],self.config['oatApiToken']))
    #         except Exception as e:
    #             self.syncMovie.stop()
    #             self.frameSettingBtns.show()
    #             self.frameSync.hide()
    #             print("Error connecting to SQL Server:", e)
    #             self.infoSettings.setText(f"Error connecting to {database} database")
    #             self.infoSettings.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
    #             self.infoViewDispense.show()
    #             self.infoViewDispense.setText(f"Error connecting to database")
    #             self.infoViewDispense.setStyleSheet("background:#fac8c5;color:red;padding:12px;border-radius:none")
    #             return
    #         print("updated")
    #     except Exception as e:
    #         print(e)

    # def edit_database_credential(self):
    #     try:
    #         self.btn_edit_db.setDisabled(True)
    #         self.btn_edit_db.setStyleSheet("padding:7px 20px;border:none;background:grey;color:lightgrey;border-radius:6%;font-family:Nirmala UI;font-size:10pt;font-weight:700")
    #         self.btn_save_db.setEnabled(True)
    #         self.btn_save_db.setStyleSheet("padding:7px 20px;border:none;background:#48C9E3;color:white;border-radius:6%;font-family:Nirmala UI;font-size:10pt;font-weight:700")
    #         self.btn_cancel_settings.setEnabled(True)
    #         self.btn_cancel_settings.setStyleSheet("padding:7px 20px;border:none;background:#48C9E3;color:white;border-radius:6%;font-family:Nirmala UI;font-size:10pt;font-weight:700")
    #         self.txt_database.setEnabled(True)
    #     except Exception as e:
    #         print(e)

    # def cancel_settings_event(self):
    #     self.btn_edit_db.setEnabled(True)
    #     self.btn_edit_db.setStyleSheet("padding:7px 20px;border:none;background:#48C9E3;color:white;border-radius:6%;font-family:Nirmala UI;font-size:10pt;font-weight:700")
    #     self.btn_save_db.setDisabled(True)
    #     self.btn_save_db.setStyleSheet("padding:7px 20px;border:none;background:grey;color:lightgrey;border-radius:6%;font-family:Nirmala UI;font-size:10pt;font-weight:700")
    #     self.btn_cancel_settings.setDisabled(True)
    #     self.btn_cancel_settings.setStyleSheet("padding:7px 20px;border:none;background:grey;color:lightgrey;border-radius:6%;font-family:Nirmala UI;font-size:10pt;font-weight:700")
    #     self.txt_database.setText(self.config['winrxDbName'])
    #     self.txt_database.setDisabled(True)

    # def switch_settings(self):
    #     try:
    #         self.settings.raise_()
    #         self.frameSync.hide()
    #         self.cancel_settings_event()
    #         self.err_database.setText("")   
    #         self.txt_database.setStyleSheet("border:1px solid  #e1e4e6;font-weight: 500;padding:10px;")
    #         self.getPrinterList()
    #         self.btnSaveLblSettings.clicked.connect(self.saveLabelSettings)
    #         self.selectPrinterCombo.setCurrentText(self.defaultPrinter)
    #         self.comboFontSize.setCurrentText(str(self.labelFontSize))

    #         if self.labelType=="normal":
    #             self.comboLabelType.setCurrentText("Normal Label")
    #             self.spinLeftMargin.setValue(self.normalLeftMargin)
    #             self.spinTopMargin.setValue(self.normalTopMargin)
    #             self.spinParaWidth.setValue(self.normalParaWidth)
    #             self.spinLineSpacing.setValue(self.normalLineSpacing)
    #             self.spinSideTextBottomMargin.setValue(self.normalSideTextBottomMargin)
    #         else:
    #             self.comboLabelType.setCurrentText("Inverted Label")
    #             self.spinLeftMargin.setValue(self.invertedLeftMargin)
    #             self.spinTopMargin.setValue(self.invertedTopMargin)
    #             self.spinParaWidth.setValue(self.invertedParaWidth)
    #             self.spinLineSpacing.setValue(self.invertedLineSpacing)
    #             self.spinSideTextBottomMargin.setValue(self.invertedSideTextBottomMargin)

    #         self.txt_database.setText(self.config['winrxDbName'])

    #         self.txtOatrxPharmacyId.setText(self.config['oatRxPharmacyId'])
    #         self.txtWebhookUrl.setText(self.config['webhookFillApiUrl'])
    #         self.txtAiDateUrl.setText(self.config['oatRxGetAiDatesApiUrl'])
    #         self.txtApiToken.setText(self.config['oatApiToken'])

    #     except Exception as e:
    #         print(e)
