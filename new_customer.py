import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog

DB_DIR = r"G:\My Drive\Rentals\RentalsDB"
CUSTOMERS_FILE = os.path.join(DB_DIR, "customers_data.json")
SAMPLE_KEYS = [
    "recipeNum",
    "discription",
    "invoice_no",
    "customer",
    "payment",
    "mamVal",
    "bankAccount",
    "BankNumber",
    "CheckNumber",
    "Date",
    "SaveFolder"
]


class CustomerEditor(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True)
        os.makedirs(DB_DIR, exist_ok=True)
        self.customers = {}
        self.current = None
        self.load_customers()
        self.build_ui()

    def load_customers(self):
        try:
            with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
                self.customers = json.load(f)
        except Exception:
            self.customers = {}

    def backup_customers(self):
        try:
            if os.path.exists(CUSTOMERS_FILE):
                import shutil, datetime
                ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                shutil.copy2(CUSTOMERS_FILE, f"{CUSTOMERS_FILE}.bak.{ts}")
        except Exception:
            pass

    def save_customers(self):
        try:
            self.backup_customers()
            with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.customers, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Saved", "Customers saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save customers: {e}")

    def build_ui(self):
        left = tk.Frame(self)
        left.pack(side="left", fill="y", padx=8, pady=8)
        right = tk.Frame(self)
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.listbox = tk.Listbox(left, width=30)
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Add", command=self.add_customer).pack(side="left", fill="x", expand=True)
        tk.Button(btn_frame, text="Delete", command=self.delete_customer).pack(side="left", fill="x", expand=True)
        tk.Button(btn_frame, text="Save", command=self.save_customers).pack(side="left", fill="x", expand=True)

        # Form fields on the right
        self.fields = {}
        for key in SAMPLE_KEYS:
            row = tk.Frame(right)
            row.pack(fill="x", pady=2)
            lbl = tk.Label(row, text=key, width=15, anchor="w")
            lbl.pack(side="left")
            ent = tk.Entry(row)
            ent.pack(side="left", fill="x", expand=True)
            self.fields[key] = ent

        action_frame = tk.Frame(right)
        action_frame.pack(fill="x", pady=6)
        tk.Button(action_frame, text="Update", command=self.update_customer).pack(side="left", padx=4)
        tk.Button(action_frame, text="Rename Key", command=self.rename_customer).pack(side="left", padx=4)

        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for name in sorted(self.customers.keys()):
            self.listbox.insert(tk.END, name)

    def on_select(self, evt=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        self.current = name
        data = self.customers.get(name, {})
        for k in SAMPLE_KEYS:
            self.fields[k].delete(0, tk.END)
            self.fields[k].insert(0, data.get(k, ""))

    def add_customer(self):
        name = simpledialog.askstring("Customer Name", "Enter new customer key/name:")
        if not name:
            return
        if name in self.customers:
            messagebox.showwarning("Exists", "Customer already exists.")
            return
        # Create entry populated with defaults
        self.customers[name] = {k: "" for k in SAMPLE_KEYS}
        self.customers[name]["customer"] = name
        self.refresh_list()
        # select new
        idx = list(sorted(self.customers.keys())).index(name)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.see(idx)
        self.on_select()

    def delete_customer(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        if messagebox.askyesno("Delete", f"Delete customer '{name}'?"):
            try:
                del self.customers[name]
            except KeyError:
                pass
            self.refresh_list()
            for f in self.fields.values():
                f.delete(0, tk.END)
            # clear current selection state
            self.current = None

    def update_customer(self):
        sel = self.listbox.curselection()
        # If the listbox selection was lost (e.g. user clicked into a field), fall back to the last known selection
        if not sel:
            if not self.current:
                messagebox.showwarning("No selection", "Select a customer to update or use 'New Blank' to create one.")
                return
            name = self.current
        else:
            name = self.listbox.get(sel[0])
        data = {}
        for k, ent in self.fields.items():
            data[k] = ent.get()
        # Do not force the 'customer' field to match the dict key; allow editing independently
        self.customers[name] = data
        messagebox.showinfo("Updated", f"Customer '{name}' updated.")
        # Refresh list and reselect the updated customer so the UI keeps context
        self.refresh_list()
        try:
            idx = list(sorted(self.customers.keys())).index(name)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self.current = name
        except Exception:
            self.current = None

    def rename_customer(self):
        sel = self.listbox.curselection()
        if not sel:
            if not self.current:
                messagebox.showwarning("No selection", "Select a customer to rename.")
                return
            old_name = self.current
        else:
            old_name = self.listbox.get(sel[0])
        new_name = simpledialog.askstring("Rename", f"Enter new key/name for customer '{old_name}':", initialvalue=old_name)
        if not new_name or new_name == old_name:
            return
        if new_name in self.customers:
            messagebox.showwarning("Exists", "A customer with that key already exists.")
            return
        # Move the data to the new key and refresh
        self.customers[new_name] = self.customers.pop(old_name)
        # Optionally update the 'customer' field to match new key; we won't force it, but set if empty
        if not self.customers[new_name].get('customer'):
            self.customers[new_name]['customer'] = new_name
        self.refresh_list()
        try:
            idx = list(sorted(self.customers.keys())).index(new_name)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self.current = new_name
        except Exception:
            self.current = None

    # 'New Blank' removed per user request; create new customers via 'Add' and then edit fields


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Customer Editor")
    app = CustomerEditor(root)
    root.geometry('800x500')
    root.mainloop()
