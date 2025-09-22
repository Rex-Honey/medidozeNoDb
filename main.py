from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGridLayout, QStackedLayout, QMessageBox
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtGui import QFont, QIcon
import json, pyodbc, sys, os, resr
from pages.sigin import SignInWindow
from pages.serverConfig import ServerConfigWindow
from pages.mainApp import MainAppWindow
from otherFiles.config import setConfig

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        module_dir = os.path.dirname(__file__)
        self.setWindowTitle("Medidoze Technologies Inc.")
        self.setWindowIcon(QIcon(os.path.join(module_dir, 'images', 'medidoze-icon.ico')))
        self.setObjectName("mainWindow")

        self.setGeometry(250, 100, 1400, 830)
        self.setFixedSize(1400, 830)

        self.stackLayout = QStackedLayout()
        centralWidget = QWidget()
        centralWidget.setLayout(self.stackLayout)
        self.setCentralWidget(centralWidget)

        self.documentsDir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        self.checkConfig()

        self.signInWindow = SignInWindow()
        self.signInWindow.loginSuccess.connect(self.loginSuccess)
        self.stackLayout.addWidget(self.signInWindow)
        self.stackLayout.setCurrentWidget(self.signInWindow)

    def checkConfig(self):
        try:
            with open(os.path.join(self.documentsDir, 'medidoze', 'configAI.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
            connectionString = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['local_database']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
            )
            conn = pyodbc.connect(connectionString)
            print("Connection successful!")
            conn.close()
            
            self.updateServerConfig(config, connectionString)
        except FileNotFoundError:
            print("No JSON config file found.")
            self.serverConfigWindow = ServerConfigWindow()
            self.stackLayout.addWidget(self.serverConfigWindow)
            self.serverConfigWindow.serverSetUpDone.connect(self.updateServerConfig)
            self.stackLayout.setCurrentWidget(self.serverConfigWindow)
        except Exception as e:
            print(f"Error in checkConfig: {e}")
            self.serverConfigWindow = ServerConfigWindow()
            self.stackLayout.addWidget(self.serverConfigWindow)
            self.serverConfigWindow.serverSetUpDone.connect(self.updateServerConfig)
            self.stackLayout.setCurrentWidget(self.serverConfigWindow)

    def updateServerConfig(self, config, connectionString):
        localConn = pyodbc.connect(connectionString)
        setConfig(config, localConn)
        self.config = config

    def loginSuccess(self, userData):
        # Check if user can login based on role and WinRx configuration
        if not self.canUserLogin(userData):
            return
        
        # Update global config with user data
        from otherFiles.config import updateUserData
        updateUserData(userData)
        print(f"User data updated")
        
        # Create MainAppWindow without parameters
        self.mainAppWindow = MainAppWindow()
        # Connect logout signal
        self.mainAppWindow.logoutRequested.connect(self.handleLogout)
        self.stackLayout.addWidget(self.mainAppWindow)
        print("MainAppWindow created successfully!")
        self.stackLayout.setCurrentWidget(self.mainAppWindow)

    def canUserLogin(self, userData):
        """Check if user can login based on role and WinRx configuration"""
        try:
            # Check if user is admin
            isAdmin = userData.get('isAdmin') == 'Y'
            
            # Check if WinRx database is configured
            hasWinRxDatabase = (self.config and 
                              self.config.get('winrxDbName') and 
                              self.config.get('winrxDbName').strip())
            
            if not isAdmin and not hasWinRxDatabase:
                # Non-admin user without WinRx database - cannot login
                QMessageBox.warning(
                    self, 
                    "Login Restricted", 
                    "You cannot login at this time. WinRx database is not configured yet. Please contact your administrator."
                )
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking login permissions: {e}")
            QMessageBox.critical(
                self, 
                "Login Error", 
                "An error occurred while checking login permissions. Please try again."
            )
            return False

    def handleLogout(self):
        """Handle logout request from MainAppWindow"""
        try:
            print("Logout requested")
            
            # Clear the main app window
            if hasattr(self, 'mainAppWindow'):
                self.stackLayout.removeWidget(self.mainAppWindow)
                self.mainAppWindow.deleteLater()
                delattr(self, 'mainAppWindow')
            
            # Reset sign-in window (clear any stored data)
            if hasattr(self.signInWindow, 'clearFields'):
                self.signInWindow.clearFields()
            
            # Switch to sign-in page
            self.stackLayout.setCurrentWidget(self.signInWindow)
            print("Logged out successfully")
            
        except Exception as e:
            print(f"Error during logout: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application font - this applies to ALL widgets
    font = QFont("Nirmala UI", 9)
    app.setFont(font)
    mainWindow = MainWindow()
    qssPath = os.path.join(os.path.dirname(__file__), 'qss', 'style.qss')
    with open(qssPath, 'r') as f:
        app.setStyleSheet(f.read())
    mainWindow.show()
    sys.exit(app.exec())