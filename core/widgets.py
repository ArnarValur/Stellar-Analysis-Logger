import tkinter as tk
import myNotebook as nb # ADDED

def _rc_menu_install(w):
    """Create a context sensitive menu for a text widget"""
    w.menu = tk.Menu(w, tearoff=0)
    # For simplicity, using English strings directly. 
    # In a larger app, these would be internationalized (e.g., using gettext _()).
    w.menu.add_command(label="Cut")
    w.menu.add_command(label="Copy")
    w.menu.add_command(label="Paste")
    w.menu.add_separator()
    w.menu.add_command(label="Select all")

    w.menu.entryconfigure("Cut", command=lambda: w.focus_force() or w.event_generate("<<Cut>>"))
    w.menu.entryconfigure("Copy", command=lambda: w.focus_force() or w.event_generate("<<Copy>>"))
    w.menu.entryconfigure("Paste", command=lambda: w.focus_force() or w.event_generate("<<Paste>>"))
    w.menu.entryconfigure("Select all", command=lambda: w.event_select_all(None) # Pass None for event if not used by method
    )

# class EntryPlus(ttk.Entry): # OLD
class EntryPlus(nb.Entry): # MODIFIED: Inherit from nb.Entry
    """
    Subclass of nb.Entry to install a context-sensitive menu on right-click
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _rc_menu_install(self)
        # Overwrite default class binding so we don't need to return "break"
        # For Entry, select_all is usually bound to <Control-a> or <Control-A>
        # We ensure our method is compatible.
        self.bind_class("Entry", "<Control-a>", self.event_select_all) 
        self.bind_class("Entry", "<Control-A>", self.event_select_all) # For completeness
        self.bind("<Button-3><ButtonRelease-3>", self.show_menu)

    def event_select_all(self, event): # Add event argument
        self.focus_force()
        self.selection_range(0, tk.END)
        return "break" # Important to prevent default behavior if any

    def show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)
