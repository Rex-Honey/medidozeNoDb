from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGridLayout, QStackedLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
import sys, os
from pages.sigin import SignInWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        module_dir = os.path.dirname(__file__)
        self.setWindowTitle("Medidoze Technologies Inc.")
        self.setWindowIcon(QIcon(os.path.join(module_dir, 'images', 'medidoze-icon.ico')))
        self.setStyleSheet("background-color: lightblue;")
        self.setGeometry(250, 100, 1400, 830)
        self.setFixedSize(1400, 830)

        self.signInWindow = SignInWindow()
        self.signInWindow.loginSuccess.connect(self.loginSuccess)
        self.stackLayout = QStackedLayout()
        self.stackLayout.addWidget(self.signInWindow)
        
        centralWidget = QWidget()
        centralWidget.setLayout(self.stackLayout)
        self.setCentralWidget(centralWidget)

        self.createTables()

    def loginSuccess(self, username, password):
        print(f"Login successful: {username}, {password}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())