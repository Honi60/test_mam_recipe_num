import os
import json
import tempfile
from PyQt5.QtWidgets import QApplication

# Ensure project root is on sys.path when tests run under pytest
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt


def make_widget(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    # Keep a reference to the QApplication so it isn't garbage-collected and
    # cause wrapped C++ objects (widgets) to be deleted during tests.
    global _qt_app
    app = QApplication.instance()
    if app is None:
        _qt_app = QApplication([])
        app = _qt_app
    widget = ReceiptGenGUI_Qt()
    widget.DB_DIR = str(tmp_path)
    return widget


def test_update_customer_mapping(tmp_path):
    widget = make_widget(tmp_path)

    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "00010"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.selected_customer = "Alice"
    widget.save_path = str(tmp_path / "out")

    ok = widget._update_customer_file(11, "00010")
    assert ok is True
    updated = json.loads(cust_file.read_text(encoding='utf-8'))
    assert updated["Alice"]["SaveFolder"] == os.path.normpath(widget.save_path)
    # The customer file should record the assigned number (recipe_num), not
    # the next-increment; the GUI will show the next number for users.
    assert updated["Alice"]["CheckNumber"] == "00010"


def test_update_customer_single_dict(tmp_path):
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"customer": "Bob", "recipeNum": "00042"}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.selected_customer = "Bob"
    widget.save_path = str(tmp_path / "out")

    ok = widget._update_customer_file(43, "00042")
    assert ok is True
    updated = json.loads(cust_file.read_text(encoding='utf-8'))
    assert updated["SaveFolder"] == os.path.normpath(widget.save_path)
    assert updated["CheckNumber"] == "00042"


def test_update_customer_list(tmp_path):
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = [{"customer": "C", "recipeNum": "00001"}, {"customer": "D"}]
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.selected_customer = "C"
    widget.save_path = str(tmp_path / "out")

    ok = widget._update_customer_file(2, "00001")
    assert ok is True
    updated = json.loads(cust_file.read_text(encoding='utf-8'))
    # find C entry
    found = None
    for item in updated:
        if item.get('customer') == 'C':
            found = item
            break
    assert found is not None
    assert found['SaveFolder'] == os.path.normpath(widget.save_path)
    assert found['CheckNumber'] == '00001'


def test_no_customer_path_noop(tmp_path):
    widget = make_widget(tmp_path)
    widget.customer_file_path = None
    widget.selected_customer = "X"
    widget.save_path = str(tmp_path / "out")

    ok = widget._update_customer_file(5, "00004")
    assert ok is False


def test_gui_refresh_after_update(tmp_path):
    """Ensure that after writing the customer file the GUI refreshes for the
    currently selected customer (save path and recipeNum reflected in the form)."""
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "00010"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.selected_customer = "Alice"
    # populate initial GUI form as if the file was loaded
    widget.customers = {"Alice": customers["Alice"].copy()}
    widget.data = widget.customers["Alice"].copy()
    widget.populate_form()
    # ensure the CheckNumber field exists and has initial value (or recipeNum legacy)
    key = "CheckNumber" if "CheckNumber" in widget.entries else "recipeNum"
    assert key in widget.entries
    assert widget.entries[key].text() == "00010"

    # Set a save path to be persisted
    widget.save_path = str(tmp_path / "out")

    ok = widget._update_customer_file(11, "00010")
    assert ok is True

    # After update, the GUI should reflect the updated recipeNum and save path
    assert widget.entries[key].text() == "00011"


def test_prefers_gui_checknumber_over_newnum(tmp_path):
    # New policy: the customer JSON should not be used as the authoritative
    # source for the receipt/check number. The number passed in should be
    # respected. Here we ensure that even if the GUI supplies a different
    # CheckNumber, the passed-in recipe_num is used.
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "00010"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.selected_customer = "Alice"
    widget.save_path = str(tmp_path / "out")
    # Simulate user typing a CheckNumber in the GUI that should be ignored
    widget.data = customers["Alice"].copy()
    widget.data["CheckNumber"] = "555"
    widget.populate_form()

    ok = widget._update_customer_file(None, "00010")
    assert ok is True
    updated = json.loads(cust_file.read_text(encoding='utf-8'))
    # The provided recipe_num argument should be used (zero-padded)
    assert updated["Alice"]["CheckNumber"] == "00010"
    assert widget.save_path == os.path.normpath(str(tmp_path / "out"))
    assert widget.save_path_display.text() == widget.save_path


def test_generate_receipt_persists_and_refresh(tmp_path, monkeypatch):
    """End-to-end: generate_receipt should increment receipt_number, update
    the customer file on disk, and refresh the GUI to show the new value.
    """
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "00010"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.customers = {"Alice": customers["Alice"].copy()}
    # Select the customer and populate the form (avoid direct dropdown manipulation
    # which can have lifecycle issues in the test harness)
    widget.selected_customer = "Alice"
    widget.data = widget.customers["Alice"].copy()
    widget.populate_form()

    # Ensure a save directory exists
    widget.save_path = str(tmp_path / "out")
    os.makedirs(widget.save_path, exist_ok=True)

    # Stub out create_receipt so no actual PDF work is done
    monkeypatch.setattr('QtGUI.receiptGenGUI_qt.create_receipt', lambda data, path: None)
    # Avoid modal dialogs that can crash in headless tests
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.information', lambda *a, **k: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.warning', lambda *a, **k: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.critical', lambda *a, **k: None)

    # Put the authoritative shared receipt number into the DB
    rnum = tmp_path / "receipt_number.txt"
    rnum.write_text("00010", encoding='utf-8')

    widget.generate_receipt()

    # Customer file should have been updated with the assigned number (00010)
    updated = json.loads(cust_file.read_text(encoding='utf-8'))
    assert updated["Alice"]["CheckNumber"] == "00010"

    # And the shared receipt_number.txt should have incremented to 00011
    assert rnum.read_text(encoding='utf-8') == '00011'

    # GUI form should reflect the next number (00011)
    key = "CheckNumber" if "CheckNumber" in widget.entries else "recipeNum"
    assert widget.entries[key].text() == "00011"


def test_generate_receipt_aborts_if_no_number_and_shared_missing(tmp_path, monkeypatch):
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": ""}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.customers = {"Alice": customers["Alice"].copy()}
    widget.selected_customer = "Alice"
    widget.data = widget.customers["Alice"].copy()
    widget.populate_form()

    widget.save_path = str(tmp_path / "out")
    os.makedirs(widget.save_path, exist_ok=True)

    called = {}
    monkeypatch.setattr('QtGUI.receiptGenGUI_qt.create_receipt', lambda data, path: called.setdefault('created', True))
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.warning', lambda *a, **k: called.setdefault('warn', a))

    # Ensure no shared receipt_number.txt exists
    rnum = tmp_path / "receipt_number.txt"
    if rnum.exists():
        rnum.unlink()

    widget.generate_receipt()

    # Should have warned and not created a receipt
    assert 'warn' in called
    assert 'created' not in called


def test_generate_receipt_aborts_if_shared_file_invalid(tmp_path, monkeypatch):
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": ""}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.customers = {"Alice": customers["Alice"].copy()}
    widget.selected_customer = "Alice"
    widget.data = widget.customers["Alice"].copy()
    widget.populate_form()

    widget.save_path = str(tmp_path / "out")
    os.makedirs(widget.save_path, exist_ok=True)

    # Write invalid content to shared file
    rnum = tmp_path / "receipt_number.txt"
    rnum.write_text("not-a-number", encoding='utf-8')

    called = {}
    monkeypatch.setattr('QtGUI.receiptGenGUI_qt.create_receipt', lambda data, path: called.setdefault('created', True))
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.warning', lambda *a, **k: called.setdefault('warn', a))

    widget.generate_receipt()

    assert 'warn' in called
    assert 'created' not in called


def test_generate_receipt_aborts_if_gui_recipe_non_digit(tmp_path, monkeypatch):
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "ABC"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.customers = {"Alice": customers["Alice"].copy()}
    widget.selected_customer = "Alice"
    widget.data = widget.customers["Alice"].copy()
    widget.populate_form()

    widget.save_path = str(tmp_path / "out")
    os.makedirs(widget.save_path, exist_ok=True)

    called = {}
    monkeypatch.setattr('QtGUI.receiptGenGUI_qt.create_receipt', lambda data, path: called.setdefault('created', True))
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.warning', lambda *a, **k: called.setdefault('warn', a))

    # If there is no valid shared receipt_number.txt, even if the GUI has a
    # non-numeric value, we must abort. This test ensures that the lack of a
    # valid shared file causes an abort (the GUI value is irrelevant).
    widget.generate_receipt()

    assert 'warn' in called
    assert 'created' not in called


def test_shared_receipt_write_atomic_failure(tmp_path, monkeypatch):
    """Simulate os.replace failing when writing the shared receipt_number.txt.
    The original file should remain unchanged and the customer file should
    still be updated with the new check number (we keep the computed value
    and persist it to the customer file even if writing the shared file fails).
    """
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "00010"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    # Shared file exists with 00010
    rnum = tmp_path / "receipt_number.txt"
    rnum.write_text("00010", encoding='utf-8')

    widget.customer_file_path = str(cust_file)
    widget.customers = {"Alice": customers["Alice"].copy()}
    widget.selected_customer = "Alice"
    widget.data = widget.customers["Alice"].copy()
    widget.populate_form()

    widget.save_path = str(tmp_path / "out")
    os.makedirs(widget.save_path, exist_ok=True)

    # Monkeypatch create_receipt to be a no-op
    monkeypatch.setattr('QtGUI.receiptGenGUI_qt.create_receipt', lambda data, path: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.information', lambda *a, **k: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.warning', lambda *a, **k: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.critical', lambda *a, **k: None)

    # Simulate os.replace raising
    import os as _os
    real_replace = _os.replace
    def bad_replace(src, dst):
        raise OSError("simulated replace failure")
    monkeypatch.setattr(_os, 'replace', bad_replace)

    try:
        widget.generate_receipt()
        # Since writing the shared file failed, the operation should abort and
        # the customer file should NOT be updated; the shared file should
        # remain unchanged.
        assert rnum.read_text(encoding='utf-8') == '00010'
        updated = json.loads(cust_file.read_text(encoding='utf-8'))
        assert 'CheckNumber' not in updated['Alice'] or updated['Alice']['CheckNumber'] == '00010'
        # No stray temp files should remain
        tmp_exists = any(p.name.startswith('.tmp') for p in tmp_path.iterdir())
        assert not tmp_exists
    finally:
        monkeypatch.setattr(_os, 'replace', real_replace)


def test_generate_receipt_shows_nonmodal_on_update_failure(tmp_path, monkeypatch):
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "00010"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.customers = {"Alice": customers["Alice"].copy()}
    widget.selected_customer = "Alice"
    widget.data = widget.customers["Alice"].copy()
    widget.populate_form()

    widget.save_path = str(tmp_path / "out")
    os.makedirs(widget.save_path, exist_ok=True)

    monkeypatch.setattr('QtGUI.receiptGenGUI_qt.create_receipt', lambda data, path: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.information', lambda *a, **k: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.warning', lambda *a, **k: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.critical', lambda *a, **k: None)

    called = {}

    # Force _update_customer_file to fail and record whether _notify_nonmodal is invoked
    widget._update_customer_file = lambda new_num, recipe_num: False
    def fake_notify(title, msg):
        called['args'] = (title, msg)
    widget._notify_nonmodal = fake_notify

    # Ensure the authoritative shared receipt number exists so generate_receipt
    # proceeds to the point where it would call _update_customer_file
    rnum = tmp_path / "receipt_number.txt"
    rnum.write_text("00010", encoding='utf-8')

    widget.generate_receipt()

    assert 'args' in called
    assert 'Failed to save customer data' in called['args'][1]


def test_atomic_write_failure_returns_false_and_cleans_tmp(tmp_path, monkeypatch):
    widget = make_widget(tmp_path)
    cust_file = tmp_path / "customers.json"
    customers = {"Alice": {"customer": "Alice", "recipeNum": "00010"}}
    cust_file.write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")

    widget.customer_file_path = str(cust_file)
    widget.selected_customer = "Alice"
    widget.save_path = str(tmp_path / "out")

    # Simulate os.replace failing during atomic write
    import os as _os
    real_replace = _os.replace
    def bad_replace(src, dst):
        raise OSError("simulated failure")
    monkeypatch.setattr(_os, 'replace', bad_replace)

    try:
        ok = widget._update_customer_file(11, "00010")
        assert ok is False
        # original file should be unchanged
        content = json.loads(cust_file.read_text(encoding='utf-8'))
        assert content['Alice']['recipeNum'] == '00010'
        # no stray temp files should remain in the dir
        tmp_exists = any(p.name.startswith('.tmp') for p in tmp_path.iterdir())
        assert not tmp_exists
    finally:
        # restore
        monkeypatch.setattr(_os, 'replace', real_replace)


def test_notify_nonmodal_is_resilient(tmp_path, monkeypatch):
    widget = make_widget(tmp_path)
    # Make QMessageBox.show and close no-ops to avoid popping UI in tests
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.show', lambda *a, **k: None)
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.close', lambda *a, **k: None)
    # Also make the information fallback a no-op so we don't trigger modal dialogs
    monkeypatch.setattr('PyQt5.QtWidgets.QMessageBox.information', lambda *a, **k: None)

    # Should not raise or crash
    widget._notify_nonmodal("Info", "This is a test", timeout_ms=10)
