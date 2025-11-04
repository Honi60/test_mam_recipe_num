import re
import tkinter as tk
from tkinter import font, ttk
from bidi.algorithm import get_display

RLM = "\u200F"

def wrap_numbers_with_rlm(text: str) -> str:
    # Wrap sequences of digits (and optional decimal/comma) with RLM
    return re.sub(r'([0-9]+(?:[.,][0-9]+)*)', lambda m: f"{RLM}{m.group(1)}{RLM}", text)

def visual_for_print(text: str, wrap_numbers=True):
    t = wrap_numbers_with_rlm(text) if wrap_numbers else text
    return get_display(t)

class HebrewEditor(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=8, pady=8)

        # Prefer bundled Alef if available
        available = font.families()
        f = "Alef" if "Alef" in available else "Segoe UI"  # fallback on Windows
        self.hebrew_font = (f, 12)

        tk.Label(self, text="Edit (logical):").pack(anchor='w')
        self.entry = tk.Entry(self, justify='right', font=self.hebrew_font)
        self.entry.pack(fill='x', pady=4)

        tk.Label(self, text="Multi-line edit:").pack(anchor='w', pady=(6,0))
        self.text = tk.Text(self, height=6, wrap='word', font=self.hebrew_font)
        # right alignment in Text isn't native; we still keep logical text and show preview
        self.text.pack(fill='both', pady=4, expand=True)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill='x', pady=6)
        tk.Button(btn_frame, text="Preview for print", command=self.update_preview).pack(side='left')
        self.wrap_chk = tk.BooleanVar(value=True)
        tk.Checkbutton(btn_frame, text="Wrap numbers (RLM)", variable=self.wrap_chk).pack(side='left', padx=8)
        # live preview toggle (off by default to avoid interfering with typing)
        self.live_preview = tk.BooleanVar(value=False)
        tk.Checkbutton(btn_frame, text="Live preview", variable=self.live_preview, command=self._toggle_live_preview).pack(side='left', padx=8)

        tk.Label(self, text="Preview (visual order for printing):").pack(anchor='w', pady=(6,0))
        self.preview = tk.Label(self, anchor='e', justify='right', font=self.hebrew_font, bg='white', relief='sunken')
        self.preview.pack(fill='both', expand=False, pady=4)

        # update on focus-out so editing is non-disruptive
        self.entry.bind("<FocusOut>", lambda e: self.update_preview())
        self.text.bind("<FocusOut>", lambda e: self.update_preview())

        # live preview while typing is optional (disabled by default). Toggle via checkbox.
        # when enabled we bind KeyRelease to update_preview; otherwise we don't bind to avoid any chance
        # of cursor issues while typing.
        # initial state: disabled

        self.update_preview()

    def _toggle_live_preview(self):
        # bind or unbind key events for live preview
        if self.live_preview.get():
            self.entry.bind("<KeyRelease>", lambda e: self.update_preview())
            self.text.bind("<KeyRelease>", lambda e: self.update_preview())
        else:
            try:
                self.entry.unbind("<KeyRelease>")
            except Exception:
                pass
            try:
                self.text.unbind("<KeyRelease>")
            except Exception:
                pass

    def update_preview(self):
        raw = self.entry.get().strip()
        t2 = self.text.get("1.0", "end").strip()
        combined = raw
        if t2:
            combined += "\n" + t2
        processed = visual_for_print(combined, wrap_numbers=self.wrap_chk.get())
        # show preview right-aligned (Label can't change layout direction; align text to right)
        self.preview.config(text=processed, anchor='e', justify='right')

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("700x400")
    root.title("Tk Hebrew edit + preview demo")
    HebrewEditor(root)
    root.mainloop()