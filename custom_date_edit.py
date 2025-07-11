from PyQt6.QtWidgets import QDateEdit
from PyQt6.QtCore import QEvent,Qt,QPointF
from PyQt6.QtGui import QMouseEvent

class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
    
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.lineEdit().clearFocus()  # Ensure focus is removed from the line edit part
