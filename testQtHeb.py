from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore import Qt
import sys

class HebrewInputTest(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hebrew-English Input Test")
        self.setLayoutDirection(Qt.RightToLeft)  # Set RTL layout

        layout = QVBoxLayout()

        label = QLabel("הכנס טקסט בעברית ובאנגלית:")
        label.setAlignment(Qt.AlignRight)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type Hebrew and English here...")
        self.input_field.setLayoutDirection(Qt.RightToLeft)  # RTL input field

        layout.addWidget(label)
        layout.addWidget(self.input_field)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HebrewInputTest()
    window.show()
    sys.exit(app.exec_())