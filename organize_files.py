"""
File organization script - Moves files to appropriate folders
Run this script once from the project root to organize all files
"""
import os
import shutil
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Define file organization mapping
FILE_MOVES = {
    # Resources - Fonts
    'Alef-Bold.ttf': 'resources/fonts/',
    'Alef-Regular.ttf': 'resources/fonts/',
    
    # Resources - Icons
    'receiptCreat.ico': 'resources/icons/',
    
    # Resources - Images
    'HoniSigneture.jpg': 'resources/images/',
    
    # Resources - Templates
    'receipt_template.svg': 'resources/templates/',
    'receipt_template_TP.svg': 'resources/templates/',
    'recipt_template.svg': 'resources/templates/',
    'recipt_template_TP.svg': 'resources/templates/',
    
    # Resources - Data
    'sample_data.json': 'resources/data/',
    
    # Logic
    'receiptGen.py': 'logic/',
    'mamAPI.py': 'logic/',
    
    # tkGUI
    'main.py': 'tkGUI/',
    'receiptGenGUI.py': 'tkGUI/',
    'new_customer.py': 'tkGUI/',
    'recrate_receipt.py': 'tkGUI/',
    'to_excel.py': 'tkGUI/',
    
    # QtGUI
    'receiptGenGUI_qt.py': 'QtGUI/',
    'new_customer_qt.py': 'QtGUI/',
    'recrate_receipt_qt.py': 'QtGUI/',
    'to_excel_qt.py': 'QtGUI/',
    
    # Test/Utility files (optional - keep in root or move to a tests folder)
    # 't.py': 'tests/',
    # 'testQtHeb.py': 'tests/',
    # 'test_heb_input.py': 'tests/',
}

# Files that should stay in root
KEEP_IN_ROOT = {
    'main_qt.py',  # Main entry point
    'create_shortcut.py',  # Deployment utility
    'OFL.txt',  # License
    'PROJECT_STRUCTURE.md',  # Documentation
    'receipt_number.txt',  # Runtime data
    'receipt.pdf',  # Generated output
    'חשבונית מס.docx',  # Document
}

def ensure_directories():
    """Create all necessary directories"""
    directories = [
        'resources/fonts',
        'resources/icons',
        'resources/images',
        'resources/templates',
        'resources/data',
        'logic',
        'tkGUI',
        'QtGUI',
    ]
    
    for dir_path in directories:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"✓ Directory exists: {dir_path}")

def move_files():
    """Move files to their designated folders"""
    moved_count = 0
    skipped_count = 0
    
    for filename, destination in FILE_MOVES.items():
        source = os.path.join(PROJECT_ROOT, filename)
        dest_dir = os.path.join(PROJECT_ROOT, destination)
        dest_file = os.path.join(dest_dir, filename)
        
        if os.path.exists(source):
            try:
                shutil.move(source, dest_file)
                print(f"✓ Moved: {filename} → {destination}")
                moved_count += 1
            except Exception as e:
                print(f"✗ Error moving {filename}: {e}")
        else:
            print(f"- Skipped: {filename} (not found)")
            skipped_count += 1
    
    return moved_count, skipped_count

def create_init_files():
    """Create __init__.py files for packages if they don't exist"""
    packages = ['logic', 'tkGUI', 'QtGUI', 'resources']
    
    for package in packages:
        init_file = os.path.join(PROJECT_ROOT, package, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write(f'"""{package} package"""\n')
            print(f"✓ Created: {package}/__init__.py")
        else:
            print(f"- Exists: {package}/__init__.py")

def main():
    """Main execution"""
    print("=" * 60)
    print("PROJECT FILE ORGANIZATION SCRIPT")
    print("=" * 60)
    print()
    
    print("Step 1: Creating directories...")
    ensure_directories()
    print()
    
    print("Step 2: Creating __init__.py files...")
    create_init_files()
    print()
    
    print("Step 3: Moving files...")
    moved, skipped = move_files()
    print()
    
    print("=" * 60)
    print(f"SUMMARY: {moved} files moved, {skipped} files skipped/not found")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update imports in your Python files")
    print("2. Update resource paths using config/paths.py")
    print("3. Review the PROJECT_STRUCTURE.md for complete organization")
    print()

if __name__ == '__main__':
    main()
