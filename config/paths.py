"""Application paths configuration"""
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Resource paths
RESOURCES_DIR = os.path.join(PROJECT_ROOT, 'resources')
FONTS_DIR = os.path.join(RESOURCES_DIR, 'fonts')
ICONS_DIR = os.path.join(RESOURCES_DIR, 'icons')
TEMPLATES_DIR = os.path.join(RESOURCES_DIR, 'templates')
IMAGES_DIR = os.path.join(RESOURCES_DIR, 'images')
DATA_DIR = os.path.join(RESOURCES_DIR, 'data')

# Data directories - Support development/simulation mode
# Set to True for simulation (E:\simulation_rentals) or False for production (E:\My Drive\Rentals)
USE_SIMULATION = True    # Change to True for development/testing

if USE_SIMULATION:
    RECIEPT_ROOT = "E:\\simulation_rentals"
    DB_DIR = "E:\\simulation_rentals\\RentalsDB"
else:
    RECIEPT_ROOT = "E:\\My Drive\\Rentals"
    DB_DIR = "E:\\My Drive\\Rentals\\RentalsDB"
HISTORY_DIR = os.path.join(DB_DIR, "History")
CUSTOMERS_FILE = os.path.join(DB_DIR, "customers_data.json")
HISTORY_FILE = os.path.join(DB_DIR, "history.json")
recreat_receipt_folder = os.path.join(RECIEPT_ROOT, "recreat_receipts")

# Icon paths
MAIN_ICON = os.path.join(ICONS_DIR, 'receiptCreat.ico')

# Font paths
FONT_ALEF_REGULAR = os.path.join(FONTS_DIR, 'Alef-Regular.ttf')
FONT_ALEF_BOLD = os.path.join(FONTS_DIR, 'Alef-Bold.ttf')

# Template paths
RECEIPT_TEMPLATE = os.path.join(TEMPLATES_DIR, 'receipt_template.svg')
RECEIPT_TEMPLATE_TP = os.path.join(TEMPLATES_DIR, 'receipt_template_TP.svg')

# Image paths
HONI_SIGNATURE = os.path.join(IMAGES_DIR, 'HoniSigneture.jpg')


def ensure_directories_exist():
    """Create necessary directories if they don't exist"""
    os.makedirs(FONTS_DIR, exist_ok=True)
    os.makedirs(ICONS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)


def get_data_mode():
    """Return current data mode: 'SIMULATION' or 'OPERATIONAL'"""
    return 'SIMULATION' if USE_SIMULATION else 'OPERATIONAL'


def print_config():
    """Print current configuration (useful for debugging)"""
    print(f"Data Mode: {get_data_mode()}")
    print(f"Receipt Root: {RECIEPT_ROOT}")
    print(f"Database Dir: {DB_DIR}")
    if USE_SIMULATION:
        print("⚠️ SIMULATION MODE ACTIVE - Using test data directory")


def get_mode_indicator_html():
    """Return HTML styled mode indicator for GUI display"""
    if USE_SIMULATION:
        return '<span style="color: blue; font-weight: bold;">🔵 SIMULATION</span>'
    else:
        return '<span style="color: green; font-weight: bold;">🟢 OPERATIONAL</span>'


def get_mode_label():
    """Return plain text mode label"""
    return "SIMULATION" if USE_SIMULATION else "OPERATIONAL"
