import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Import the four PyQt5 GUI modules
from receiptGenGUI_qt import ReceiptGenGUI_Qt
from new_customer_qt import CustomerEditor_Qt
from recrate_receipt_qt import RecreateReceiptApp_Qt
from to_excel_qt import ToExcelApp_Qt

os.makedirs(r"E:\MyGoogleDrive\Rentals\RentalsDB\History", exist_ok=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Receipt Tools")
        self.setGeometry(100, 100, 1200, 750)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'receiptCreat.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Receipt generator
        self.gen_app = ReceiptGenGUI_Qt()
        self.tabs.addTab(self.gen_app, "Generate Receipt")
        
        # Tab 2: Customer editor
        self.cust_app = CustomerEditor_Qt()
        self.tabs.addTab(self.cust_app, "Customers")
        
        # Tab 3: Recreate receipt
        self.rec_app = RecreateReceiptApp_Qt()
        self.tabs.addTab(self.rec_app, "Recreate Receipt")
        
        # Tab 4: Export to Excel
        self.excel_app = ToExcelApp_Qt()
        self.tabs.addTab(self.excel_app, "Export to Excel")
        
        # Connect tab changed signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def on_tab_changed(self, index):
        """Reload data when user switches to certain tabs"""
        tab_widget = self.tabs.widget(index)
        try:
            if hasattr(self.rec_app, 'reload_history') and tab_widget == self.rec_app:
                self.rec_app.reload_history()
            elif hasattr(self.excel_app, 'reload_history') and tab_widget == self.excel_app:
                self.excel_app.reload_history()
        except Exception as e:
            print(f"Error reloading tab: {e}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
