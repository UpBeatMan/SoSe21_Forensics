import tkinter as tk
from tkinter import ttk

from View.menu import MainMenu
from View.toolbar import Toolbar
from View.sidebar import SideBar
from View.content import Content
from Model.util import resource_path

class View(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.geometry("1500x900")
        icon = tk.PhotoImage(file=resource_path("View/icons/Logo.png"))
        self.iconphoto(False, icon)

        self.controller = controller
        self.menu = None
        self.toolbar = None
        self.sidebar = None
        self.content = None

        self.body()

    
    def main(self):
        self.mainloop()

    def body(self):      
        self.content = Content(self)
        self.sidebar = SideBar(self)
        self.menu = MainMenu(self)
        self.toolbar = Toolbar(self)
        
        self.config(menu=self.menu)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="nwes")
        self.sidebar.grid(row=1, column=0, sticky="nwes")
        self.content.grid(row=1, column=1, sticky="wens")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)