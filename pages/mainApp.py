from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize
import os
from pages.settings import SettingsWindow
from pages.pageContainer import PageContainer
class MainAppWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        module_dir = os.path.dirname(os.path.dirname(__file__))

        # Main layout: sidebar + main content
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

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
            ("Dashboard", "dash.png"),
            ("Dispense", "dispense.png"),
            ("Instant Dose", "dispense.png"),
            ("Prime Pump", "dispense.png"),
            ("Calibrate Pump", "dispense.png"),
            ("Patients", "patient_icon.png"),
            ("DIN Management", "list.svg"),
            ("Pharmacy Users", "users.svg"),
            ("Stock Management", "list.svg"),
            ("Reports", "list.svg"),
            ("Settings", "setting.svg"),
            ("Logout", "logout.svg"),
        ]

        for idx, (label, icon_file) in enumerate(sidebar_items):
            btn = QPushButton(f"  {label}")
            btn.setIcon(QIcon(os.path.join(module_dir, "images", icon_file)))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setProperty("sidebarButton", True)  # For QSS
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)
            if label == "Settings":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))

        sidebar_layout.addStretch()

        # Central stacked layout for pages
        self.stack = QStackedLayout()
        for label, _ in sidebar_items:
            if label == "Settings":
                page_widget = SettingsWindow()
            else:
                page_widget = QLabel(f"{label} Page")
            self.stack.addWidget(PageContainer(label, page_widget))

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
