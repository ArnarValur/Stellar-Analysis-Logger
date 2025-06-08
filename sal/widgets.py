import tkinter as tk
import myNotebook as nb # type: ignore
def _rc_menu_install(w):
    """Create a context sensitive menu for a text widget"""
    w.menu = tk.Menu(w, tearoff=0)
    w.menu.add_command(label="Cut")
    w.menu.add_command(label="Copy")
    w.menu.add_command(label="Paste")
    w.menu.add_separator()
    w.menu.add_command(label="Select all")

    w.menu.entryconfigure("Cut", command=lambda: w.focus_force() or w.event_generate("<<Cut>>"))
    w.menu.entryconfigure("Copy", command=lambda: w.focus_force() or w.event_generate("<<Copy>>"))
    w.menu.entryconfigure("Paste", command=lambda: w.focus_force() or w.event_generate("<<Paste>>"))
    w.menu.entryconfigure("Select all", command=lambda: w.event_select_all(None)
    )

class EntryPlus(nb.Entry):
    """
    Subclass of nb.Entry to install a context-sensitive menu on right-click
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _rc_menu_install(self)
        self.bind_class("Entry", "<Control-a>", self.event_select_all) 
        self.bind_class("Entry", "<Control-A>", self.event_select_all)
        self.bind("<Button-3><ButtonRelease-3>", self.show_menu)

    def event_select_all(self, event):
        self.focus_force()
        self.selection_range(0, tk.END)
        return "break"

    def show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)
