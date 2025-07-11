# pages/pageContainer.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QSizePolicy, QLabel
from PyQt6.QtCore import Qt

class PageContainer(QWidget):
    def __init__(self, pageName, pageWidget):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        # self.setStyleSheet("border:1px solid red")
        # pageWidget.setStyleSheet("border:1px solid blue")

        titleLabel = QLabel(pageName)
        titleLabel.setObjectName("pageTitleLabel")
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        titleLabel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        # titleLabel.setStyleSheet("border:1px solid red;margin-bottom: 10px;")

        # Frame for content
        frame = QFrame()
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # frame.setStyleSheet("border:1px solid green")
        frame.setObjectName("PageFrame")
        frameLayout = QVBoxLayout(frame)
        frameLayout.setSpacing(0)
        label=QLabel("hello")
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        label.setStyleSheet("border:1px solid blue;")

        frameLayout.addWidget(titleLabel)
        frameLayout.addWidget(pageWidget)
        frameLayout.addWidget(label)
        layout.addWidget(frame)
