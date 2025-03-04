from tkinter import *
import tkinter as tk

root = tk.Tk()
root.title("Audio Typing Test")

#to get screen size
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.geometry(f"{screen_width}x{screen_height}")

#grid layout
mainframe = tk.Frame(root)
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)  # Sidebar
root.columnconfigure(1, weight=3)  # Main Typing Box
root.columnconfigure(2, weight=1)  # Buttons
root.rowconfigure(0, weight=1)  # Progress Bar
root.rowconfigure(1, weight=4)  # Typing Area
root.rowconfigure(2, weight=1)  # Bottom row 

#Title
tk.Label(root, text="Audio Typing Test", font=("Times New Roman", 16, "bold")).grid(row=0, column=1, pady=10, sticky="n")

# Sidebar
sidebar = tk.Frame(root, bg="#ddd", width=150)
sidebar.grid(row=0, column=0, rowspan=3, sticky="ns")

# Typing Box
typing_box = tk.Text(root, height=10, width=50, font=("Arial", 14))
typing_box.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

#run command
root.mainloop()
