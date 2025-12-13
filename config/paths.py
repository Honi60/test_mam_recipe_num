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

# Data directories
DB_DIR = r"E:\MyGoogleDrive\Rentals\RentalsDB"
HISTORY_DIR = os.path.join(DB_DIR, "History")
CUSTOMERS_FILE = os.path.join(DB_DIR, "customers_data.json")
HISTORY_FILE = os.path.join(DB_DIR, "history.json")

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
