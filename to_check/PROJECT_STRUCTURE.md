# Project Structure Guide

## Folder Organization

```
reciptGen/
├── resources/                  # Static files (fonts, icons, templates, images)
│   ├── fonts/
│   │   ├── Alef-Bold.ttf
│   │   └── Alef-Regular.ttf
│   ├── icons/
│   │   └── receiptCreat.ico
│   ├── templates/
│   │   ├── receipt_template.svg
│   │   ├── receipt_template_TP.svg
│   │   ├── recipt_template.svg
│   │   └── recipt_template_TP.svg
│   ├── images/
│   │   └── HoniSigneture.jpg
│   └── data/
│       └── sample_data.json
│
├── logic/                      # Core business logic & utilities
│   ├── __init__.py
│   ├── receiptGen.py           # Receipt generation logic
│   ├── mamAPI.py               # API integration
│   ├── database.py             # Database operations (create if needed)
│   └── utils.py                # Utility functions (create if needed)
│
├── tkGUI/                      # Tkinter-based GUI (legacy)
│   ├── __init__.py
│   ├── main.py                 # Tkinter main entry point
│   ├── receiptGenGUI.py        # Receipt generator GUI
│   ├── new_customer.py         # Customer editor GUI
│   ├── recrate_receipt.py      # Recreate receipt GUI
│   └── to_excel.py             # Excel export GUI
│
├── QtGUI/                      # PyQt5-based GUI (modern)
│   ├── __init__.py
│   ├── main_qt.py              # PyQt5 main entry point
│   ├── receiptGenGUI_qt.py     # Receipt generator GUI
│   ├── new_customer_qt.py      # Customer editor GUI
│   ├── recrate_receipt_qt.py   # Recreate receipt GUI
│   └── to_excel_qt.py          # Excel export GUI
│
├── config/                     # Configuration files
│   ├── __init__.py
│   ├── settings.py             # Application settings
│   └── paths.py                # Path configurations
│
├── main_qt.py                  # Main entry point (launcher)
├── create_shortcut.py          # Shortcut creation utility
├── receipt_number.txt          # Data file
├── receipt.pdf                 # Generated receipt
├── OFL.txt                     # Font license
├── PROJECT_STRUCTURE.md        # This file
│
└── My Drive/                   # Google Drive data folder
```

## File Organization Instructions

### 1. Resources Folder
Move to `resources/`:
- **Fonts**: `Alef-Bold.ttf`, `Alef-Regular.ttf` → `resources/fonts/`
- **Icons**: `receiptCreat.ico` → `resources/icons/`
- **Templates**: `receipt_template.svg`, `recipt_template.svg`, etc. → `resources/templates/`
- **Images**: `HoniSigneture.jpg` → `resources/images/`
- **Data**: `sample_data.json` → `resources/data/`

### 2. Logic Folder
Move to `logic/`:
- `receiptGen.py` - Core receipt generation
- `mamAPI.py` - API integration
- Create `__init__.py` for package initialization

### 3. tkGUI Folder
Move to `tkGUI/`:
- `main.py`
- `receiptGenGUI.py`
- `new_customer.py`
- `recrate_receipt.py`
- `to_excel.py`
- Create `__init__.py`

### 4. QtGUI Folder
Move to `QtGUI/`:
- `main_qt.py`
- `receiptGenGUI_qt.py`
- `new_customer_qt.py`
- `recrate_receipt_qt.py`
- `to_excel_qt.py`
- Create `__init__.py`

### 5. Config Folder
Create configuration files:
- `settings.py` - Application settings
- `paths.py` - Path configurations
- Create `__init__.py`

### 6. Keep at Root
- `create_shortcut.py` - Deployment utility
- `receipt_number.txt` - Runtime data
- `receipt.pdf` - Generated output
- `OFL.txt` - License
- `My Drive/` - Data folder

## Import Updates Required

After moving files, update imports in all files:

```python
# Example conversions:
from receiptGen import create_receipt
# Becomes:
from logic.receiptGen import create_receipt

from receiptGenGUI_qt import ReceiptGenGUI_Qt
# Becomes:
from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt

# For resource paths:
os.path.join(os.path.dirname(__file__), 'receiptCreat.ico')
# Becomes:
os.path.join(os.path.dirname(__file__), 'resources/icons/receiptCreat.ico')
```

## Benefits of This Structure

✓ **Organization**: Clear separation of concerns
✓ **Maintainability**: Easy to locate and update code
✓ **Scalability**: Simple to add new features
✓ **Reusability**: Logic is decoupled from UI
✓ **Testing**: Easier to test logic independently
✓ **Collaboration**: Clear structure for team development
