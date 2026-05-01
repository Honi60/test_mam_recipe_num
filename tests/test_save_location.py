import os
import json
import tempfile
from PyQt5.QtWidgets import QApplication
import sys
import os
# Ensure project root is on sys.path so imports like QtGUI.* work when pytest sets a different CWD
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def test_choose_save_location_and_generate(monkeypatch, tmp_path):
    # Use offscreen platform to avoid needing a display during tests
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt

    widget = ReceiptGenGUI_Qt()
    # Isolate DB files to the temp path so tests don't touch the real receipt_number.txt
    widget.DB_DIR = str(tmp_path)
    # Isolate DB files to the temp path so tests don't touch the real receipt_number.txt
    widget.DB_DIR = str(tmp_path)
    # Isolate DB files to the temp path so tests don't touch the real receipt_number.txt
    widget.DB_DIR = str(tmp_path)
    # Isolate DB files to the temp path so tests don't touch the real receipt_number.txt
    widget.DB_DIR = str(tmp_path)

    test_dir = str(tmp_path)

    # Monkeypatch the file dialog to return our test dir
    import QtGUI.receiptGenGUI_qt as gui_mod
    monkeypatch.setattr(gui_mod.QFileDialog, "getExistingDirectory", lambda *a, **k: test_dir)

    # Replace create_receipt with a fake that writes a tiny file so we can assert it was called
    saved = {}

    def fake_create_receipt(data, output_path):
        with open(output_path, "wb") as f:
            f.write(b"PDF")
        saved["path"] = output_path

    monkeypatch.setattr(gui_mod, "create_receipt", fake_create_receipt)

    # Prevent modal dialogs in headless tests
    monkeypatch.setattr(gui_mod.QMessageBox, 'information', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'warning', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'critical', lambda *a, **k: None)

    # Choose a save location and assert the widget updated its internal state and display
    widget.choose_save_location()
    assert widget.save_path == test_dir
    assert widget.save_path_display.text() == test_dir

    # If the customer data contains a Save-folder-like key, it should NOT create a duplicate entry
    widget.customers = {"Bob": {"customer": "Bob", "Save folder": "C:\\old"}}
    widget.customer_dropdown.clear()
    widget.customer_dropdown.addItems(["Bob"])
    widget.customer_dropdown.setCurrentIndex(0)
    # The form entries should not include 'Save folder'
    assert "Save folder" not in widget.entries

    # If the customer data contains a Save-path, it should become the default save location
    test_path = str(tmp_path / "out")
    widget.customers = {"Carl": {"customer": "Carl", "SavePath": test_path}}
    widget.customer_dropdown.clear()
    widget.customer_dropdown.addItems(["Carl"])
    widget.customer_dropdown.setCurrentIndex(0)
    assert widget.save_path == os.path.normpath(test_path)
    assert widget.save_path_display.text() == os.path.normpath(test_path)


def test_relative_savefolder_resolves_under_receipt_root(monkeypatch, tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt
    widget = ReceiptGenGUI_Qt()
    # Simulate relative SaveFolder from JSON
    widget.customers = {"Carl": {"customer": "Carl", "SaveFolder": "reports"}}
    widget.customer_dropdown.clear()
    widget.customer_dropdown.addItems(["Carl"])
    widget.customer_dropdown.setCurrentIndex(0)
    from config.paths import RECIEPT_ROOT
    assert widget.save_path == os.path.normpath(os.path.join(RECIEPT_ROOT, "reports"))


def test_recipe_num_prefill_and_increment(monkeypatch, tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt
    widget = ReceiptGenGUI_Qt()
    # Isolate DB files to the temp path so tests don't touch the real receipt_number.txt
    widget.DB_DIR = str(tmp_path)
    # Isolate DB files to the temp path so tests don't touch the real receipt_number.txt
    widget.DB_DIR = str(tmp_path)

    # Use a temp DB_DIR so we don't touch the user's real files
    widget.DB_DIR = str(tmp_path)
    recipe_file = os.path.join(widget.DB_DIR, "receipt_number.txt")
    with open(recipe_file, "w", encoding="utf-8") as f:
        f.write("00042")

    # Customer with empty recipeNum so it should be prefilled from the file
    widget.customers = {"D": {"customer": "D", "recipeNum": ""}}
    widget.customer_dropdown.clear()
    widget.customer_dropdown.addItems(["D"])
    widget.customer_dropdown.setCurrentIndex(0)
    # After selection, entries['recipeNum'] should contain the file value
    assert widget.entries["recipeNum"].text() == "00042"

    # Set a save path so generate_receipt doesn't prompt the dialog
    out_dir = str(tmp_path / "out")
    os.makedirs(out_dir, exist_ok=True)
    widget.save_path = out_dir

    # Monkeypatch create_receipt and message boxes for headless tests
    import QtGUI.receiptGenGUI_qt as gui_mod
    monkeypatch.setattr(gui_mod, "create_receipt", lambda data, path: open(path, "wb").write(b"pdf"))
    monkeypatch.setattr(gui_mod.QMessageBox, 'information', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'warning', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'critical', lambda *a, **k: None)

    # Generate and verify receipt creation and increment of the recipe number
    widget.generate_receipt()
    # After generation, the receipt_number.txt should be incremented to 00043
    with open(recipe_file, "r", encoding="utf-8") as f:
        new = f.read().strip()
    assert new == "00043"


def test_customer_file_updated_on_save(monkeypatch, tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt
    widget = ReceiptGenGUI_Qt()

    # Prepare a temp customers file as a dict mapping
    cust_file = tmp_path / "customers.json"
    customers = {
        "Alice": {"customer": "Alice", "recipeNum": "00099"}
    }
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    # Load into widget by setting attributes directly (avoids QFileDialog)
    widget.customer_file_path = str(cust_file)
    widget.customers = customers
    widget.selected_customer = "Alice"
    # Ensure the widget's data is set as if a customer was selected
    widget.data = customers["Alice"].copy()
    # Ensure the widget uses an isolated DB_DIR so it doesn't read a
    # system-wide receipt_number.txt during the test.
    widget.DB_DIR = str(tmp_path)
    widget.populate_form()

    # Set a save path and monkeypatch create_receipt
    out_dir = str(tmp_path / "out")
    os.makedirs(out_dir, exist_ok=True)
    widget.save_path = out_dir
    import QtGUI.receiptGenGUI_qt as gui_mod
    # Prevent QMessageBox from blocking in headless test runs
    monkeypatch.setattr(gui_mod.QMessageBox, 'information', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'warning', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'critical', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod, "create_receipt", lambda data, path: open(path, "wb").write(b"pdf"))

    # Trigger generation
    # Ensure the authoritative shared receipt number exists for this test
    rfile = os.path.join(widget.DB_DIR, "receipt_number.txt")
    with open(rfile, "w", encoding="utf-8") as rf:
        rf.write("00099")

    widget.generate_receipt()

    # Read back the customers file and assert updates
    content = json.loads(cust_file.read_text(encoding="utf-8"))
    assert content["Alice"]["SaveFolder"] == os.path.normpath(out_dir)
    # recipeNum should have been incremented from 00099 to 00100
    assert content["Alice"]["recipeNum"] == "00100"


def test_prefs_remember_last_customer_dir(monkeypatch, tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt
    widget = ReceiptGenGUI_Qt()

    # Create a fake customers file in a nested dir
    nested = tmp_path / "data_sub"
    nested.mkdir()
    cust_file = nested / "customers.json"
    cust_file.write_text(json.dumps({"X": {"customer": "X"}}), encoding="utf-8")

    # Monkeypatch QFileDialog to return our file path
    import QtGUI.receiptGenGUI_qt as gui_mod
    monkeypatch.setattr(gui_mod.QFileDialog, 'getOpenFileName', lambda *a, **k: (str(cust_file), 'JSON Files (*.json)'))

    # Prevent QMessageBox from blocking/crashing in headless pytest runs
    monkeypatch.setattr(gui_mod.QMessageBox, 'information', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'warning', lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.QMessageBox, 'critical', lambda *a, **k: None)

    # Call load_customer_file which should store last_customer_dir in prefs.json
    widget.load_customer_file()
    # prefs file should exist and contain last_customer_dir
    assert os.path.exists(widget.prefs_file)
    with open(widget.prefs_file, 'r', encoding='utf-8') as pf:
        prefs = json.load(pf)
    assert prefs.get('last_customer_dir') == str(nested)

    # Prepare a minimal customer and generate a receipt
    widget.customers = {"Alice": {"customer": "Alice"}}
    widget.customer_dropdown.clear()
    widget.customer_dropdown.addItems(["Alice"])
    widget.customer_dropdown.setCurrentIndex(0)
    # Ensure selected customer and data are set
    widget.selected_customer = "Alice"
    widget.data = {"customer": "Alice"}
    # Set a save path and monkeypatch create_receipt to capture the saved path
    out_dir = str(nested / "out")
    os.makedirs(out_dir, exist_ok=True)
    widget.save_path = out_dir
    saved = {}
    def fake_create(data, path):
        with open(path, "wb") as f:
            f.write(b"pdf")
        saved.setdefault("path", path)
    monkeypatch.setattr(gui_mod, "create_receipt", fake_create)
    # Ensure receipt_number file exists, as generate_receipt requires it
    with open(os.path.join(widget.DB_DIR, "receipt_number.txt"), "w", encoding="utf-8") as rf:
        rf.write("00001")

    widget.generate_receipt()

    assert "path" in saved
    assert saved["path"].startswith(str(nested))
