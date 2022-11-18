import time

from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QFrame,\
    QLabel


class MainWidget(QDialog):
    submit_retag_entry = Signal(str)
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        #self.setAttribute(Qt.WA_X11NetWmWindowTypeDock) # no effect
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        # the next may be used to bypass i3 and make it always on top
        # no matter what. But, no direct keyboard input, no mouse dragging.
        #self.setWindowFlag(Qt.X11BypassWindowManagerHint)
        #self.setWindowFlag(Qt.BypassWindowManagerHint)
        #self.setAttribute(Qt.WA_AlwaysStackOnTop)
        #self.setWindowFlag(Qt.Tool)
        #self.setWindowFlag(Qt.WindowStaysOnTopHint)


    def reappear(self):
        self.update_time_in_title()
        self.adjustSize()
        self.show()

    def self_reset(self):
        self.hide()

    def clear(self):
        for i in reversed(range(self.layout.count())):
            self.layout.takeAt(i).widget().deleteLater()

    def move_(self, x, y):
        try:
            self.move(x, y)
        except OverflowError:
            pass

    def show_retag_entry(self):
        self.entry = QLineEdit()
        self.entry.returnPressed.connect(self.on_submit_retag_entry)
        self.layout.addWidget(self.entry)
        self.entry.setFocus()

    def on_submit_retag_entry(self):
        entry = self.entry.text()
        self.submit_retag_entry.emit(entry)

    def add_label(self, text, sunken=False, raised=False, color=None):
        label = QLabel(text, self)
        label.setStyleSheet(f'color: {color};')
        if sunken:
            label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        elif raised:
            label.setFrameStyle(QFrame.Panel | QFrame.Raised)
        label.setLineWidth(2)
        self.layout.addWidget(label)

    def update_time_in_title(self):
        time_ = time.localtime()
        time_cs = time.strftime("%H:%M %d.%B %d.%m.",time_)
        time_en = time.asctime(time_)
        self.setWindowTitle(' '.join([time_cs, time_en]))
