import tkinter as tk
from gui import ExcelToSchemasGUI

def main():
    root = tk.Tk()
    root.title("Excel to Schemas")
    # Set minimum window size
    root.minsize(800, 600)
    # Center the window
    window_width = 800
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = ExcelToSchemasGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
