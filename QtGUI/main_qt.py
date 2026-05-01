import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

# Add the project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import configuration
from config.paths import ensure_directories_exist, MAIN_ICON, HISTORY_DIR, get_mode_label, USE_SIMULATION

# Import the four PyQt5 GUI modules
from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt
from QtGUI.new_customer_qt import CustomerEditor_Qt
from QtGUI.recrate_receipt_qt import RecreateReceiptApp_Qt
from QtGUI.to_excel_qt import ToExcelApp_Qt

# Ensure necessary directories exist
ensure_directories_exist()
os.makedirs(HISTORY_DIR, exist_ok=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        mode_text = f"[{get_mode_label()}]" if USE_SIMULATION else f"[{get_mode_label()}]"
        title = f"Receipt Tools {mode_text}"
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1200, 750)
        
        # Set window icon
        if os.path.exists(MAIN_ICON):
            self.setWindowIcon(QIcon(MAIN_ICON))
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setElideMode(Qt.ElideNone)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(16, 16))
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
        tab_name = self.tabs.tabText(index)
        
        try:
            # Check if switching to tabs that need customer data reload
            if tab_widget == self.gen_app or tab_widget == self.cust_app:
                # Ask user if they want to reload customer file
                reply = QMessageBox.question(
                    self,
                    "Reload Customer File",
                    f"Do you want to reload the customer file for '{tab_name}' tab?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    if hasattr(self.gen_app, 'read_customers_data') and tab_widget == self.gen_app:
                        # For ReceiptGenGUI - reload from CUSTOMERS_FILE
                        from config.paths import DB_DIR
                        customers_file = os.path.join(DB_DIR, "customers_data.json")
                        if os.path.exists(customers_file):
                            self.gen_app.read_customers_data(customers_file, popup=False)
                            QMessageBox.information(self, "Success", "Customer file reloaded for Generate Receipt tab")
                    elif hasattr(self.cust_app, 'load_customers') and tab_widget == self.cust_app:
                        # For CustomerEditor - reload customers
                        self.cust_app.load_customers()
                        self.cust_app.refresh_list()
                        self.cust_app.on_customer_selected()
                        QMessageBox.information(self, "Success", "Customer file reloaded for Customers tab")
            
            # Reload history for other tabs
            if hasattr(self.rec_app, 'reload_history') and tab_widget == self.rec_app:
                self.rec_app.reload_history()
            elif hasattr(self.excel_app, 'reload_history') and tab_widget == self.excel_app:
                self.excel_app.reload_history()
        except Exception as e:
            print(f"Error reloading tab: {e}")


def get_stylesheet():
    """Return a modern colorful stylesheet for the application."""
    return """
    QMainWindow {
        background-color: #f5f5f5;
    }
    
    QWidget {
        background-color: #ffffff;
        color: #333333;
    }
    
    QTabWidget::pane {
        border: 2px solid #e0e0e0;
        margin: 0px;
    }
    
    QTabBar {
        margin: 0px;
        padding: 0px;
    }
    
    QTabBar::tab {
        background-color: #e8f4f8;
        color: #1a5f7a;
        padding: 10px 30px;
        margin-right: 2px;
        border: 1px solid #d0d0d0;
        border-bottom: none;
        font-weight: bold;
        font-size: 11pt;
        min-width: 130px;
        min-height: 35px;
    }
    
    QTabBar::tab:selected {
        background-color: #2196F3;
        color: #ffffff;
        border: 1px solid #1976D2;
    }
    
    QTabBar::tab:hover {
        background-color: #64B5F6;
    }
    
    QPushButton {
        background-color: #2196F3;
        color: #ffffff;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 11pt;
    }
    
    QPushButton:hover {
        background-color: #1976D2;
    }
    
    QPushButton:pressed {
        background-color: #1565C0;
    }
    
    QPushButton:disabled {
        background-color: #cccccc;
        color: #999999;
    }
    
    QLineEdit {
        background-color: #ffffff;
        color: #333333;
        border: 2px solid #e0e0e0;
        border-radius: 4px;
        padding: 6px;
        font-size: 10pt;
    }
    
    QLineEdit:focus {
        border: 2px solid #2196F3;
    }
    
    QComboBox {
        background-color: #ffffff;
        color: #333333;
        border: 2px solid #e0e0e0;
        border-radius: 4px;
        padding: 6px;
        font-size: 10pt;
    }
    
    QComboBox:focus {
        border: 2px solid #2196F3;
    }
    
    QComboBox::drop-down {
        border: none;
        background-color: #2196F3;
        width: 30px;
    }
    
    QComboBox::down-arrow {
        color: #ffffff;
    }
    
    QLabel {
        color: #333333;
        font-size: 10pt;
    }
    
    QMessageBox QLabel {
        color: #333333;
    }
    
    QMessageBox QPushButton {
        min-width: 60px;
    }
    
    QListWidget {
        background-color: #ffffff;
        color: #333333;
        border: 2px solid #e0e0e0;
        border-radius: 4px;
    }
    
    QListWidget::item:selected {
        background-color: #2196F3;
        color: #ffffff;
    }
    
    QListWidget::item:hover {
        background-color: #e3f2fd;
    }
    
    QTableWidget {
        background-color: #ffffff;
        alternate-background-color: #f5f5f5;
        gridline-color: #e0e0e0;
        border: 2px solid #e0e0e0;
    }
    
    QTableWidget::item:selected {
        background-color: #2196F3;
        color: #ffffff;
    }
    
    QHeaderView::section {
        background-color: #1976D2;
        color: #ffffff;
        padding: 5px;
        border: 1px solid #1565C0;
        font-weight: bold;
    }
    
    QFrame {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
    }
    
    QScrollArea {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
    }
    
    QSpinBox {
        background-color: #ffffff;
        color: #333333;
        border: 2px solid #e0e0e0;
        border-radius: 4px;
        padding: 6px;
    }
    
    QSpinBox:focus {
        border: 2px solid #2196F3;
    }
    
    QSpinBox::up-button {
        background-color: #2196F3;
        width: 20px;
        subcontrol-position: top right;
        border: 1px solid #1976D2;
    }
    
    QSpinBox::down-button {
        background-color: #2196F3;
        width: 20px;
        subcontrol-position: bottom right;
        border: 1px solid #1976D2;
    }
    
    QSpinBox::up-arrow {
        image: none;
        width: 8px;
        height: 8px;
        background-color: #ffffff;
        border-radius: 1px;
    }
    
    QSpinBox::down-arrow {
        image: none;
        width: 8px;
        height: 8px;
        background-color: #ffffff;
        border-radius: 1px;
    }
    """


def main():
    app = QApplication(sys.argv)
    
    # Apply stylesheet to application
    app.setStyle('Fusion')
    app.setStyleSheet(get_stylesheet())
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
