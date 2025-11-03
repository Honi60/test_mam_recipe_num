import tkinter as tk
from tkinter import ttk

# Import the three components
from receiptGenGUI import ReceiptGenGUI
from new_customer import CustomerEditor
from recrate_receipt import RecreateReceiptApp
from to_excel import ToExcelApp


def main():
	root = tk.Tk()
	root.title("Receipt Tools")
	root.geometry('1000x700')

	notebook = ttk.Notebook(root)
	notebook.pack(fill='both', expand=True)

	# Tab 1: Receipt generator - wrap existing ReceiptGenGUI
	tab1 = tk.Frame(notebook)
	notebook.add(tab1, text='Generate Receipt')
	# instantiate ReceiptGenGUI using tab1 as master
	gen_app = ReceiptGenGUI(tab1)

	# Tab 2: Customer editor
	tab2 = tk.Frame(notebook)
	notebook.add(tab2, text='Customers')
	cust_app = CustomerEditor(tab2)

	# Tab 3: Recreate receipt
	tab3 = tk.Frame(notebook)
	notebook.add(tab3, text='Recreate Receipt')
	rec_app = RecreateReceiptApp(tab3)

	# Tab 4: Export to Excel
	tab4 = tk.Frame(notebook)
	notebook.add(tab4, text='Export to Excel')
	excel_app = ToExcelApp(tab4)

	# When user switches tabs, reload history in the relevant tabs
	def on_tab_changed(event):
		selected = event.widget.select()
		tab_text = event.widget.tab(selected, "text")
		try:
			if tab_text == 'Recreate Receipt':
				rec_app.reload_history()
			elif tab_text == 'Export to Excel':
				excel_app.reload_history()
		except Exception:
			pass

	notebook.bind('<<NotebookTabChanged>>', on_tab_changed)

	root.mainloop()


if __name__ == '__main__':
	main()

