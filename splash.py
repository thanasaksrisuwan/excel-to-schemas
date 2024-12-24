import tkinter as tk
from tkinter import ttk
from version import format_version_string

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window size and position
        width = 300
        height = 150
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Create main frame
        frame = ttk.Frame(self.root)
        frame.pack(fill='both', expand=True)
        
        # Add app name and version
        title = ttk.Label(
            frame, 
            text=format_version_string(),
            font=('Helvetica', 12, 'bold')
        )
        title.pack(pady=20)
        
        # Add loading text
        self.status_label = ttk.Label(
            frame,
            text="Loading...",
            font=('Helvetica', 10)
        )
        self.status_label.pack()
        
        # Add progress bar
        self.progress = ttk.Progressbar(
            frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(pady=20)
        self.progress.start()
        
        # Center the window on screen
        self.root.update_idletasks()
        
        # Make window appear on top
        self.root.attributes('-topmost', True)
        
        # Style window
        if 'vista' in self.root.tk.call('tk', 'windowingsystem'):
            self.root.attributes('-alpha', 0.9)
        
    def destroy(self):
        self.progress.stop()
        self.root.destroy()

    def update_status(self, text):
        """Update the loading text"""
        self.status_label.config(text=text)
        self.root.update()
