import os
import json
import tempfile
import sys
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
# Ensure project root is on sys.path so package imports like QtGUI.* and logic.* work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from PyQt5.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])
# In tests/headless mode, QMessageBox can block waiting for user interaction.
# Monkeypatch the static dialog methods to be no-ops so script runs non-interactively.
from PyQt5.QtWidgets import QMessageBox
QMessageBox.information = lambda *a, **k: None
QMessageBox.warning = lambda *a, **k: None
QMessageBox.critical = lambda *a, **k: None
from QtGUI.receiptGenGUI_qt import ReceiptGenGUI_Qt
w = ReceiptGenGUI_Qt()
# isolated temp DB
tmpdir = tempfile.mkdtemp()
w.DB_DIR = tmpdir
w.prefs_file = os.path.join(w.DB_DIR, 'prefs.json')
# prepare customer file
cust_file = os.path.join(tmpdir,'customers.json')
customers = {'Alice': {'customer':'Alice','recipeNum':'00099'}}
with open(cust_file,'w',encoding='utf-8') as f:
    json.dump(customers,f,ensure_ascii=False,indent=2)
# wire widget to use this file
w.customer_file_path = cust_file
w.customers = customers
w.selected_customer = 'Alice'
w.data = customers['Alice'].copy()
# create QLineEdit entries for fields
from PyQt5.QtWidgets import QLineEdit
w.entries = {}
for k,v in w.data.items():
    e = QLineEdit()
    e.setText(str(v))
    w.entries[k] = e
# set save_path
out = os.path.join(tmpdir,'out'); os.makedirs(out,exist_ok=True)
w.save_path = out
# monkeypatch create_receipt
import logic.receiptGen as rg
import QtGUI.receiptGenGUI_qt as gui
# Override the create_receipt used by the GUI module so generate_receipt uses our simple writer
gui.create_receipt = lambda data, path: open(path, 'wb').write(b'pdf')
# run generate
print('calling generate_receipt')
try:
    w.generate_receipt()
    print('generate_receipt returned')
except Exception as e:
    print('generate_receipt raised:', repr(e))
# read back customer file
with open(cust_file,'r',encoding='utf-8') as cf:
    updated = json.load(cf)
print('updated customer:', updated)
print('last_saved_file:', getattr(w,'last_saved_file',None))
# check receipt_number file
rnum = os.path.join(tmpdir,'receipt_number.txt')
print('receipt_number.txt exists:', os.path.exists(rnum))
if os.path.exists(rnum):
    print('receipt_number content:', open(rnum).read())
print('done')
