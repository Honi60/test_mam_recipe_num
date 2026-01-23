import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from receiptGen import create_receipt
from bidi.algorithm import get_display

class ReceiptGenGUI:
    def __init__(self, master):
        # Central DB directory for shared files
        self.DB_DIR = r"G:\My Drive\Rentals\RentalsDB"
        # Ensure DB_DIR exists when needed (writes will create it as necessary)
        try:
            os.makedirs(self.DB_DIR, exist_ok=True)
        except Exception:
            pass
        self.master = master
        # If master is a root window, set its title; if it's a Frame, skip
        try:
            if isinstance(master, tk.Tk):
                master.title("Receipt Generator")
        except Exception:
            pass
        self.data = {}
        self.entries = {}
        self.save_path = None
        self.customers = {}
        self.selected_customer = tk.StringVar()
        parent = master
        self.customer_file_btn = tk.Button(parent, text="Load Customer Data File", command=self.load_customer_file)
        self.customer_file_btn.pack(pady=10)
        self.customer_select_frame = tk.Frame(parent)
        self.customer_select_frame.pack(pady=10)
        self.customer_dropdown = None
        self.form_frame = tk.Frame(parent)
        self.form_frame.pack(fill="x", expand=True, pady=10)
        self.save_btn = tk.Button(parent, text="Choose Save Location", command=self.choose_save_location)
        self.save_btn.pack(pady=10)
        self.gen_btn = tk.Button(parent, text="Generate and Save", command=self.generate_receipt)
        self.gen_btn.pack(pady=10)
        self.open_folder_btn = tk.Button(parent, text="Open Receipt Folder", command=self.open_receipt_folder, state="disabled")
        self.open_folder_btn.pack(pady=10)
    
    def open_receipt_folder(self):
        import os
        import subprocess
        if self.save_path:
            # Normalize path for Windows
            win_path = os.path.normpath(os.path.abspath(self.save_path))
            try:
                subprocess.Popen(f'explorer /select,"{win_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        else:
            messagebox.showwarning("Warning", "No receipt file generated yet.")

    def load_customer_file(self):
        self.save_path= None
        # Start file dialog in the shared DB directory
        file_path = filedialog.askopenfilename(title="Select Customer Data File", initialdir=self.DB_DIR, filetypes=[("JSON Files", "*.json")])
        if not file_path:
            # If the user cancels, try loading the default customers_data.json from DB_DIR
            default_path = os.path.join(self.DB_DIR, "customers_data.json")
            if os.path.exists(default_path):
                file_path = default_path
            else:
                return
            return
        try:
            with open(file_path, encoding="utf-8") as f:
                loaded = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            return
        # If loaded is a dict of customers, set self.customers
        if isinstance(loaded, dict) and all(isinstance(v, dict) for v in loaded.values()):
            self.customers = loaded
            self.show_customer_dropdown()
        else:
            self.data = loaded
            self.create_form()
    
    def show_customer_dropdown(self):
        for widget in self.customer_select_frame.winfo_children():
            widget.destroy()
        customer_names = list(self.customers.keys())
        if not customer_names:
            messagebox.showerror("Error", "No customers found in file.")
            return
        self.selected_customer.set(customer_names[0])
        label = tk.Label(self.customer_select_frame, text="Select Customer:")
        label.pack(side="left")
        self.customer_dropdown = tk.OptionMenu(self.customer_select_frame, self.selected_customer, *customer_names, command=self.on_customer_selected)
        self.customer_dropdown.pack(side="left")
        self.on_customer_selected(self.selected_customer.get())

    def on_customer_selected(self, customer_name):
        self.save_path = None
        self.data = self.customers[customer_name]
        print(customer_name)
        print(self.data['customer'])
        # Disable the "Open Receipt Folder" button when switching customers
        try:
            self.open_folder_btn.config(state="disabled")
        except Exception:
            pass
        self.create_form()

    def create_form(self):
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.entries.clear()
        # Read recipeNum from receipt_number.txt if present in DB_DIR
        recipe_num_path = os.path.join(self.DB_DIR, "receipt_number.txt")
        try:
            with open(recipe_num_path, "r", encoding="utf-8") as f:
                next_num = f.read().strip()
        except Exception:
            next_num = None
        # Use grid layout for responsive resizing
        self.form_frame.columnconfigure(1, weight=1)
        for i, (key, value) in enumerate(self.data.items()):
            label = tk.Label(self.form_frame, text=key, width=20, anchor="w")
            label.grid(row=i, column=0, sticky="w", padx=2, pady=2)
            entry = tk.Entry(self.form_frame)
            if key == "recipeNum" and next_num:
                entry.insert(0, next_num)
            else:
                entry.insert(0, str(value))
            entry.grid(row=i, column=1, sticky="ew", padx=2, pady=2)
            self.entries[key] = entry

    def choose_save_location(self):
        import os
        path = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            self.save_path = path
            self.save_btn.config(text=f"Save Path Selected:\n{os.path.basename(path)}")

    def generate_receipt(self):
        if not self.data:
            messagebox.showwarning("Warning", "No customer data loaded.")
            return
        if isinstance(self.customers, dict) and self.customers and not self.selected_customer.get():
            messagebox.showwarning("Warning", "No customer selected.")
            return
        # If user did not choose a save location, generate default path from customer, recipeNum, and Date
        if not self.save_path:
            customer_name = self.selected_customer.get() if self.selected_customer.get() else self.data.get('customer', '')
            # Use actual receipt number from receipt_number.txt in DB_DIR
            recipe_num_path = os.path.join(self.DB_DIR, "receipt_number.txt")
            try:
                with open(recipe_num_path, "r", encoding="utf-8") as f:
                    recipe_num = f.read().strip()
            except Exception:
                recipe_num = self.data.get('recipeNum', '')
            date_str = self.data.get('Date', '')
            month_year = ''
            try:
                if date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        month = int(parts[1])
                        year = parts[2][-2:]
                        import calendar
                        month_name = calendar.month_abbr[month].lower()
                        month_year = f"{month_name} {year}"
            except Exception:
                pass
            filename = f"{customer_name} {recipe_num} {month_year}.pdf".strip()
            # If SaveFolder is relative or empty, save into DB_DIR by default
            save_folder = self.data.get('SaveFolder') or self.DB_DIR
            if not os.path.isabs(save_folder):
                save_folder = self.DB_DIR
            self.save_path = os.path.join(save_folder, filename)
        data = {k: v.get() for k, v in self.entries.items()}
        try:
            create_receipt(data, self.save_path)
            # Append this receipt to history.json
            try:
                history_path = os.path.join(self.DB_DIR, "history.json")
                # Load existing history if possible
                try:
                    with open(history_path, "r", encoding="utf-8") as hf:
                        import json as _json
                        existing = _json.load(hf)
                except Exception:
                    # If file missing or malformed, start fresh
                    existing = {}
                # Use recipeNum as the top-level key (zero-padded if possible)
                recipe_key = data.get("recipeNum", "")
                if recipe_key and recipe_key.isdigit():
                    # keep same formatting as receipt_number (e.g. 00001)
                    recipe_key = f"{int(recipe_key):05d}"
                # Group under customer name so the structure matches existing samples
                customer_name = data.get("customer", "Unknown")
                existing[recipe_key] = {customer_name: data}
                # Before writing back, create a timestamped backup of the existing history file if it exists
                try:
                    import shutil, datetime
                    if os.path.exists(history_path):
                        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                        backup_path = f"{history_path}.bak.{ts}"
                        shutil.copy2(history_path, backup_path)
                except Exception:
                    # Backup failure shouldn't block saving history
                    pass
                # Write back
                with open(history_path, "w", encoding="utf-8") as hf:
                    import json as _json
                    _json.dump(existing, hf, ensure_ascii=False, indent=2)
            except Exception:
                # Don't prevent successful receipt creation if history update fails
                pass
            # Increment recipeNum in receipt_number.txt
            recipe_num_path = os.path.join(self.DB_DIR, "receipt_number.txt")
            new_num = None
            if "recipeNum" in data:
                try:
                    num = int(data["recipeNum"])
                    new_num = num + 1
                    with open(recipe_num_path, "w", encoding="utf-8") as f:
                        f.write(f"{new_num:05d}")
                except Exception:
                    pass
            messagebox.showinfo("Success", f"Receipt saved to {self.save_path}")
            # Update GUI with new receipt number
            if new_num:
                if "recipeNum" in self.entries:
                    self.entries["recipeNum"].delete(0, tk.END)
                    self.entries["recipeNum"].insert(0, f"{new_num:05d}")
            # Enable open folder button only after successful save
            self.open_folder_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate receipt: {e}")
            self.open_folder_btn.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiptGenGUI(root)
    root.mainloop()
