import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from receiptGen import create_receipt

DB_DIR = r"G:\My Drive\Rentals\RentalsDB"
HISTORY_FILE = os.path.join(DB_DIR, "history.json")


class RecreateReceiptApp(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True)
        os.makedirs(DB_DIR, exist_ok=True)
        self.history = {}
        self.selected_key = None
        self.selected_customer = None
        # filters
        self.filter_customer = tk.StringVar(value="All")
        self.filter_date = tk.StringVar()
        self.load_history()
        self.build_ui()

    def load_history(self):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception:
            self.history = {}

    def build_ui(self):
        left = tk.Frame(self)
        left.pack(side="left", fill="y", padx=8, pady=8)
        right = tk.Frame(self)
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        # Filter controls
        filter_frame = tk.Frame(left)
        filter_frame.pack(fill="x", pady=(0,6))
        tk.Label(filter_frame, text="Customer:").pack(side="left")
        self.customer_option = tk.OptionMenu(filter_frame, self.filter_customer, "All")
        self.customer_option.pack(side="left")
        tk.Label(filter_frame, text="Date contains:").pack(side="left", padx=(8,0))
        self.date_entry = tk.Entry(filter_frame, textvariable=self.filter_date, width=12)
        self.date_entry.pack(side="left")
        tk.Button(filter_frame, text="Filter", command=self.apply_filters).pack(side="left", padx=4)
        tk.Button(filter_frame, text="Clear", command=self.clear_filters).pack(side="left")

        self.listbox = tk.Listbox(left, width=30)
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Reload", command=self.reload_history).pack(side="left", fill="x", expand=True)
        tk.Button(btn_frame, text="Regenerate", command=self.regenerate_selected).pack(side="left", fill="x", expand=True)

        # details
        self.details = tk.Text(right, wrap="word")
        self.details.pack(fill="both", expand=True)

        self.refresh_list()

    def refresh_list(self):
        # Populate listbox applying filters (keep index->key mapping)
        self.listbox.delete(0, tk.END)
        self.list_keys = []
        # build available customers for option menu
        customers = set()
        for key in sorted(self.history.keys()):
            entry = self.history.get(key, {})
            if isinstance(entry, dict) and entry:
                cust = list(entry.keys())[0]
                customers.add(cust)
        # update customer_option menu
        menu = self.customer_option["menu"]
        menu.delete(0, "end")
        menu.add_command(label="All", command=lambda v="All": self.filter_customer.set(v))
        for c in sorted(customers):
            menu.add_command(label=c, command=lambda v=c: self.filter_customer.set(v))

        fcust = self.filter_customer.get()
        fdate = self.filter_date.get().strip()
        # detect month/year input like '6/2025', '06-25', '06/2025'
        import re
        month_year_mode = False
        fy_month = None
        fy_year = None
        if fdate:
            m = re.match(r"^\s*(\d{1,2})\s*[/\-]\s*(\d{2,4})\s*$", fdate)
            if m:
                month = int(m.group(1))
                year_raw = m.group(2)
                year = int(year_raw)
                # normalize 2-digit year
                if year < 100:
                    # assume 2000s for two-digit years
                    year += 2000
                fy_month = month
                fy_year = year
                month_year_mode = True
        for key in sorted(self.history.keys()):
            entry = self.history.get(key, {})
            if isinstance(entry, dict) and entry:
                cust = list(entry.keys())[0]
                data = entry[cust]
            else:
                cust = ""
                data = {}
            date = data.get("Date", "") if isinstance(data, dict) else ""
            # apply filters
            if fcust and fcust != "All" and cust != fcust:
                continue
            if fdate:
                if month_year_mode:
                    # try to parse date like dd/mm/YYYY or similar
                    dm = re.match(r"^\s*(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\s*$", date)
                    if not dm:
                        # no match => skip
                        continue
                    entry_month = int(dm.group(2))
                    entry_year = int(dm.group(3))
                    if entry_year < 100:
                        entry_year += 2000
                    if entry_month != fy_month or entry_year != fy_year:
                        continue
                else:
                    if fdate not in date:
                        continue
            display = f"{key} | {cust} | {date}"
            self.listbox.insert(tk.END, display)
            self.list_keys.append(key)

    def reload_history(self):
        # Reload the internal cache and refresh the list silently
        self.load_history()
        self.refresh_list()

    def apply_filters(self):
        self.refresh_list()

    def clear_filters(self):
        self.filter_customer.set("All")
        self.filter_date.set("")
        self.refresh_list()

    def on_select(self, evt=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        try:
            key = self.list_keys[idx]
        except Exception:
            return
        self.selected_key = key
        entry = self.history.get(key, {})
        # entry expected to be {customer: data}
        if isinstance(entry, dict) and entry:
            cust_name = list(entry.keys())[0]
            self.selected_customer = cust_name
            data = entry[cust_name]
        else:
            self.selected_customer = None
            data = {}
        self.details.delete(1.0, tk.END)
        self.details.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))

    def regenerate_selected(self):
        if not self.selected_key:
            messagebox.showwarning("No selection", "Select a history entry to regenerate.")
            return
        entry = self.history.get(self.selected_key, {})
        if not entry:
            messagebox.showerror("Error", "Selected history entry is empty or malformed.")
            return
        cust_name = list(entry.keys())[0]
        data = entry[cust_name]
        # Ask where to save - default to SaveFolder/filename if present
        default_folder = data.get("SaveFolder") or DB_DIR
        default_filename = f"{cust_name} {data.get('recipeNum','')}.pdf"
        initial = os.path.join(default_folder, default_filename) if default_folder else ""
        save_path = filedialog.asksaveasfilename(title="Save regenerated receipt as", initialdir=default_folder, initialfile=default_filename, defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if not save_path:
            return
        # Ensure file name ends with _recreate.pdf
        base, ext = os.path.splitext(save_path)
        if not base.endswith("_recreate"):
            save_path = f"{base}_recreate{ext or '.pdf'}"
        try:
            create_receipt(data, save_path)
            messagebox.showinfo("Success", f"Regenerated receipt saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to regenerate receipt: {e}")


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Recreate Receipt from History")
    app = RecreateReceiptApp(root)
    root.geometry('800x500')
    root.mainloop()
