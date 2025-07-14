from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize
import pyodbc,os
from pages.settings import SettingsWindow
from pages.primePump import PrimeWindow
from pages.calibration import CalibrationWindow
from pages.pageContainer import PageContainer
from pages.dashboard import DashboardWindow
from pages.din import DinWindow
from pages.patients import PatientsWindow
from pages.pharmacyUsers import PharmacyUsersWindow
from pages.instantDose import InstantDoseWindow
from pages.dispense import DispenseWindow

class MainAppWindow(QWidget):
    def __init__(self, config, connString):
        super().__init__()
        self.config = config
        self.connString = connString
        self.local_conn = pyodbc.connect(connString)
        self.initUI()

    def initUI(self):
        module_dir = os.path.dirname(os.path.dirname(__file__))

        # Main layout: sidebar + main content
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Sidebar
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("SidebarWidget")
        sidebar_widget.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(0)

        # Logo
        logo = QLabel()
        logo.setObjectName("SidebarLogo")
        logo_pixmap = QPixmap(os.path.join(module_dir, "images", "dashboardLogo.png"))
        logo.setPixmap(logo_pixmap)
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(self._divider())
        sidebar_layout.addSpacing(10)

        # Sidebar buttons (icon, label)
        self.buttons = []
        sidebar_items = [
            ("Dashboard", "dash.png", DashboardWindow(self.config, self.connString)),
            ("Dispense", "dispense.png",DispenseWindow(self.config, self.connString)),
            ("Instant Dose", "dispense.png", InstantDoseWindow(self.config, self.connString)),
            ("Prime Pump", "dispense.png", PrimeWindow(self.config, self.connString)),
            ("Calibrate Pump", "dispense.png", CalibrationWindow(self.config, self.connString)),
            ("Patients", "patient_icon.png", PatientsWindow(self.config, self.connString)),
            ("DIN Management", "list.svg", DinWindow(self.config, self.connString)),
            ("Pharmacy Users", "users.svg", PharmacyUsersWindow(self.config, self.connString)),
            ("Stock Management", "list.svg", PrimeWindow(self.config, self.connString)),
            ("Reports", "list.svg", PrimeWindow(self.config, self.connString)),
            ("Settings", "setting.svg", SettingsWindow(self.config, self.connString)),
            ("Logout", "logout.svg", PrimeWindow(self.config, self.connString)),
        ]

        self.stack = QStackedLayout()
        for idx, (label, icon_file, page_widget) in enumerate(sidebar_items):
            btn = QPushButton(f"  {label}")
            btn.setIcon(QIcon(os.path.join(module_dir, "images", icon_file)))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setProperty("sidebarButton", True)  # For QSS
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)
            self.stack.addWidget(PageContainer(label, page_widget))
        self.switch_page(0)

        sidebar_layout.addStretch()

        # Add sidebar and stack to main layout
        main_layout.addWidget(sidebar_widget)

        content_widget = QWidget()
        content_widget.setContentsMargins(0, 0, 0, 0)
        content_widget.setLayout(self.stack)
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(content_widget, stretch=1)
        self.setLayout(main_layout)

    def _divider(self):
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #2b5e9e; margin: 8px 0;")
        return line

    def switch_page(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)
