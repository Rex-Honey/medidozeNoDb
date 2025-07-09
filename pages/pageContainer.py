# pages/pageContainer.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QSizePolicy, QLabel
from PyQt6.QtCore import Qt

class PageContainer(QWidget):
    def __init__(self, pageName, pageWidget):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        titleLabel = QLabel(pageName)
        titleLabel.setObjectName("pageTitleLabel")
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        titleLabel.setStyleSheet("margin-bottom: 10px; border:1px solid red")

        # Frame for content
        frame = QFrame()
        frame.setStyleSheet("border:1px solid green")
        frame.setObjectName("PageFrame")
        frameLayout = QVBoxLayout(frame)
        frameLayout.setSpacing(0)
        frameLayout.addWidget(titleLabel)
        frameLayout.addWidget(pageWidget)
        layout.addWidget(frame)