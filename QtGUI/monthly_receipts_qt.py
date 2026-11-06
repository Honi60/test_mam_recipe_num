import ctypes
import os
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.paths import ACCOUNT_BOOK, RECIEPT_ROOT, FONT_ALEF_REGULAR
from config.customer_defaults import (
    get_default_save_folder, set_default_save_folder,
    get_default_description, set_default_description,
)
try:
    from logic.receiptGen import create_receipt
except ModuleNotFoundError:
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent not in sys.path:
        sys.path.insert(0, parent)
    from logic.receiptGen import create_receipt


def _as_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _as_amount(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _as_month(value):
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        try:
            return int(str(value).split('.')[0])
        except Exception:
            return None


def _format_date(value):
    if isinstance(value, datetime):
        return value.strftime('%d/%m/%Y')
    s = _as_text(value)
    if not s:
        return ''
    for fmt in ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).strftime('%d/%m/%Y')
        except ValueError:
            continue
    return s


class MonthlyReceiptsApp_Qt(QWidget):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Month selection
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel('Month:'))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(1)
        header_layout.addWidget(self.month_spin)

        self.load_btn = QPushButton('Load')
        self.load_btn.clicked.connect(self.on_load_clicked)
        header_layout.addWidget(self.load_btn)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Receipt rows table
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ['Index', 'Receipt', 'Customer', 'Amount', 'Date', 'Ref / Check', 'Account', 'Allocation', 'Description']
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 180)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 200)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.table)

        # Generation controls
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QLabel('Generate index:'))
        self.index_spin = QSpinBox()
        self.index_spin.setRange(1, 1)
        self.index_spin.setValue(1)
        self.index_spin.valueChanged.connect(self.on_index_changed)
        gen_layout.addWidget(self.index_spin)

        self.generate_btn = QPushButton('Generate and Save')
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        gen_layout.addWidget(self.generate_btn)
        gen_layout.addStretch()
        main_layout.addLayout(gen_layout)

        # Description editor for the selected row
        desc_layout = QHBoxLayout()
        self.set_last_btn = QPushButton('Set last')
        self.set_last_btn.setToolTip('Copy the last saved description for this customer')
        self.set_last_btn.clicked.connect(self.on_set_last_clicked)
        desc_layout.addWidget(self.set_last_btn)
        desc_layout.addWidget(QLabel('Description:'))
        self.desc_edit = QLineEdit()
        self.desc_edit.textChanged.connect(self.on_desc_changed)
        desc_layout.addWidget(self.desc_edit)
        main_layout.addLayout(desc_layout)

        # Hebrew-friendly font
        QFontDatabase.addApplicationFont(FONT_ALEF_REGULAR)
        hebrew_font = QFont('Alef', 10)
        if not hebrew_font.exactMatch():
            for name in ('Segoe UI', 'Tahoma', 'Arial'):
                hebrew_font.setFamily(name)
                if hebrew_font.exactMatch():
                    break
        self.setFont(hebrew_font)
        self.table.setFont(hebrew_font)
        self.desc_edit.setFont(hebrew_font)
        self.desc_edit.setLayoutDirection(Qt.RightToLeft)
        self.desc_edit.setAlignment(Qt.AlignRight)

    def on_load_clicked(self):
        month = self.month_spin.value()
        self.load_month(month)

    def load_month(self, month):
        self.rows = []
        self.table.setRowCount(0)
        self.index_spin.setRange(1, 1)
        self.desc_edit.clear()

        if not os.path.exists(ACCOUNT_BOOK):
            QMessageBox.critical(self, 'Error', f'Account book not found:\n{ACCOUNT_BOOK}')
            return

        try:
            import openpyxl
            wb = openpyxl.load_workbook(ACCOUNT_BOOK, data_only=True)
            ws = wb['Receipt Matrix'] if 'Receipt Matrix' in wb.sheetnames else wb.active
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load Excel:\n{e}')
            return

        # Build column name -> index map from header row
        header = []
        for cell in next(ws.iter_rows(min_row=1, max_row=1, values_only=True)):
            header.append(_as_text(cell))
        col_map = {name: idx for idx, name in enumerate(header)}

        required = [
            'Month', 'Customer Name', 'Receipt 1', 'amaount', 'date',
            'check num', 'Referance', 'bank account', 'bank', 'alloc',
        ]
        missing = [c for c in required if c not in col_map]
        if missing:
            QMessageBox.critical(self, 'Error', f'Missing columns: {", ".join(missing)}')
            return

        month_idx = col_map['Month']
        customer_idx = col_map['Customer Name']
        receipt_idx = col_map['Receipt 1']
        amount_idx = col_map['amaount']
        date_idx = col_map['date']
        check_idx = col_map['check num']
        referance_idx = col_map['Referance']
        bank_account_idx = col_map['bank account']
        bank_idx = col_map['bank']
        alloc_idx = col_map['alloc']

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row:
                continue

            if _as_month(row[month_idx]) != month:
                continue

            customer_val = _as_text(row[customer_idx])
            receipt_val = _as_text(row[receipt_idx])
            amount_val = _as_amount(row[amount_idx])

            if not customer_val or amount_val is None or not receipt_val:
                continue

            # Skip summary/total-looking rows
            if receipt_val.lower() == 'total':
                continue

            date_val = _format_date(row[date_idx])
            alloc_val = _as_text(row[alloc_idx])
            check_val = _as_text(row[check_idx])
            referance_val = _as_text(row[referance_idx])
            bank_account_val = _as_text(row[bank_account_idx])
            bank_val = _as_text(row[bank_idx])

            if referance_val:
                bank_fields = {
                    'bank_transfer_referance': referance_val,
                    'transfer_bankAccount': bank_account_val,
                    'bankAccount': '',
                    'BankNumber': '',
                    'CheckNumber': '',
                }
            elif check_val:
                bank_fields = {
                    'bank_transfer_referance': '',
                    'transfer_bankAccount': '',
                    'bankAccount': bank_account_val,
                    'BankNumber': bank_val,
                    'CheckNumber': check_val,
                }
            else:
                bank_fields = {
                    'bank_transfer_referance': '',
                    'transfer_bankAccount': '',
                    'bankAccount': '',
                    'BankNumber': '',
                    'CheckNumber': '',
                }

            data = {
                'recipeNum': receipt_val,
                'customer': customer_val,
                'payment': str(int(amount_val)) if amount_val == int(amount_val) else str(amount_val),
                'Date': date_val,
                'allocation': alloc_val if alloc_val else None,
                'discription': '',
            }
            data.update(bank_fields)

            self.rows.append(data)

        if not self.rows:
            QMessageBox.information(self, 'No rows', f'No receipt rows found for month {month}.')
            return

        self.populate_table()
        self.index_spin.setRange(1, len(self.rows))
        self.index_spin.setValue(1)

    def populate_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.rows))
        for i, row in enumerate(self.rows):
            index_item = QTableWidgetItem(str(i + 1))
            index_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            index_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

            receipt_item = QTableWidgetItem(row['recipeNum'])
            receipt_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            receipt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            customer_item = QTableWidgetItem(row['customer'])
            customer_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            customer_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            amount_item = QTableWidgetItem(row['payment'])
            amount_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            date_item = QTableWidgetItem(row['Date'])
            date_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            date_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            ref_text = row['bank_transfer_referance'] or row.get('CheckNumber', '')
            ref_item = QTableWidgetItem(ref_text)
            ref_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            ref_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            account_text = row['transfer_bankAccount'] or row.get('bankAccount', '')
            account_item = QTableWidgetItem(account_text)
            account_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            account_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            alloc_value = row['allocation'] if row['allocation'] is not None else ''
            alloc_item = QTableWidgetItem(alloc_value)
            alloc_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            alloc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            desc_item = QTableWidgetItem(row['discription'])
            desc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(i, 0, index_item)
            self.table.setItem(i, 1, receipt_item)
            self.table.setItem(i, 2, customer_item)
            self.table.setItem(i, 3, amount_item)
            self.table.setItem(i, 4, date_item)
            self.table.setItem(i, 5, ref_item)
            self.table.setItem(i, 6, account_item)
            self.table.setItem(i, 7, alloc_item)
            self.table.setItem(i, 8, desc_item)
        self.table.blockSignals(False)
        self.table.selectRow(0)

    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        if row < 0 or row >= len(self.rows):
            return
        self.index_spin.blockSignals(True)
        self.index_spin.setValue(row + 1)
        self.index_spin.blockSignals(False)

        desc = self.rows[row]['discription']
        self.desc_edit.blockSignals(True)
        self.desc_edit.setText(desc)
        self.desc_edit.blockSignals(False)

    def on_index_changed(self, value):
        if 1 <= value <= len(self.rows):
            self.table.selectRow(value - 1)

    def on_item_changed(self, item):
        if item.column() == 8:
            row = item.row()
            if 0 <= row < len(self.rows):
                self.rows[row]['discription'] = item.text()
                if self.table.currentRow() == row:
                    self.desc_edit.blockSignals(True)
                    self.desc_edit.setText(item.text())
                    self.desc_edit.blockSignals(False)

    def on_set_last_clicked(self):
        row = self.index_spin.value() - 1
        if 0 <= row < len(self.rows):
            customer = self.rows[row]['customer']
            desc = get_default_description(customer)
            self.rows[row]['discription'] = desc
            desc_item = self.table.item(row, 8)
            if desc_item:
                self.table.blockSignals(True)
                desc_item.setText(desc)
                self.table.blockSignals(False)
            self.desc_edit.blockSignals(True)
            self.desc_edit.setText(desc)
            self.desc_edit.blockSignals(False)

    def on_desc_changed(self, text):
        row = self.index_spin.value() - 1
        if 0 <= row < len(self.rows):
            self.rows[row]['discription'] = text
            desc_item = self.table.item(row, 8)
            if desc_item:
                self.table.blockSignals(True)
                desc_item.setText(text)
                self.table.blockSignals(False)

    def on_generate_clicked(self):
        if not self.rows:
            QMessageBox.warning(self, 'Error', 'Load a month first.')
            return

        idx = self.index_spin.value() - 1
        if idx < 0 or idx >= len(self.rows):
            QMessageBox.warning(self, 'Error', 'Invalid row index.')
            return

        row = self.rows[idx]
        customer = row['customer']

        default_folder = get_default_save_folder(customer) or RECIEPT_ROOT or ''
        if default_folder and not os.path.isdir(default_folder):
            os.makedirs(default_folder, exist_ok=True)
        folder = QFileDialog.getExistingDirectory(
            self,
            'Select Save Folder',
            default_folder,
            QFileDialog.DontUseNativeDialog
        )
        if not folder:
            return

        output_path = os.path.join(folder, f"{row['recipeNum']}.pdf")

        try:
            create_receipt(row, output_path)
            set_default_save_folder(customer, folder)
            set_default_description(customer, row['discription'])
            QMessageBox.information(
                self,
                'Success',
                f'Saved receipt {row["recipeNum"]} for {customer}\nto {output_path}'
            )
            # Open the save folder with the new file highlighted
            if os.name == 'nt' and os.path.exists(output_path):
                _open_file_in_explorer(output_path)
            if idx + 1 < len(self.rows):
                self.index_spin.setValue(idx + 2)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to create receipt:\n{e}')


def _open_file_in_explorer(path):
    """Open the containing folder in Windows Explorer and select the file."""
    if os.name != 'nt' or not os.path.exists(path):
        return
    path = os.path.normpath(path)
    ctypes.windll.ole32.CoInitialize(None)
    try:
        ctypes.windll.shell32.ILCreateFromPathW.restype = ctypes.c_void_p
        ctypes.windll.shell32.ILCreateFromPathW.argtypes = [ctypes.c_wchar_p]
        ctypes.windll.shell32.SHOpenFolderAndSelectItems.restype = ctypes.HRESULT
        ctypes.windll.shell32.SHOpenFolderAndSelectItems.argtypes = [
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_ulong
        ]
        ctypes.windll.shell32.ILFree.restype = None
        ctypes.windll.shell32.ILFree.argtypes = [ctypes.c_void_p]
        pidl = ctypes.windll.shell32.ILCreateFromPathW(path)
        if pidl:
            ctypes.windll.shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
            ctypes.windll.shell32.ILFree(pidl)
    finally:
        ctypes.windll.ole32.CoUninitialize()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MonthlyReceiptsApp_Qt()
    w.setWindowTitle('Monthly Receipts')
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec_())
