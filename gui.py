import os
import json
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from ttkthemes import ThemedStyle  # Add this import
from database import connect_to_database
from validation import generate_schema  # Add this import
from version import format_version_string, get_version_info
import pandas as pd

class SheetSelectionDialog:
    def __init__(self, parent, sheets, current_selections=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Sheets")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.sheets = sheets
        self.selected_sheets = current_selections or []
        
        # Selection mode frame - simplified to just multiple selection mode
        self.mode_frame = ttk.LabelFrame(self.dialog, text="Sheet Selection")
        self.mode_frame.pack(fill="x", padx=10, pady=5)
        
        # Quick selection buttons
        quick_frame = ttk.Frame(self.mode_frame)
        quick_frame.pack(fill="x", padx=5)
        ttk.Button(quick_frame, text="Select All", 
                  command=self.select_all).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="Select None", 
                  command=self.select_none).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="Invert Selection", 
                  command=self.invert_selection).pack(side="left", padx=2)

        # Search box
        search_frame = ttk.Frame(self.dialog)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_sheets)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True)
        
        # Sheet list with counter
        list_frame = ttk.LabelFrame(self.dialog, text="Available Sheets")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add sheet count
        self.count_label = ttk.Label(list_frame, text="")
        self.count_label.pack(anchor="w", padx=5, pady=2)
        
        # Create scrollable frame for sheets
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.sheet_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_frame = canvas.create_window((0, 0), window=self.sheet_frame, anchor="nw")
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.sheet_frame.bind("<Configure>", on_frame_configure)
        
        # Create checkboxes
        self.sheet_vars = []
        self.sheet_checkboxes = []
        for sheet in sheets:
            var = tk.BooleanVar(value=sheet in self.selected_sheets)
            self.sheet_vars.append(var)
            cb = ttk.Checkbutton(self.sheet_frame, text=sheet, variable=var,
                               command=self.update_selection)
            cb.pack(anchor="w", padx=5, pady=2)
            self.sheet_checkboxes.append(cb)
        
        # Selection info with styling
        info_frame = ttk.LabelFrame(self.dialog, text="Selection Summary")
        info_frame.pack(fill="x", padx=10, pady=5)
        self.info_label = ttk.Label(info_frame, text="", wraplength=450)
        self.info_label.pack(fill="x", padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="OK", command=self.ok).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side="right", padx=5)
        
        self.result = None
        self.update_selection_mode()
        self.update_selection()

    def filter_sheets(self, *args):
        search_term = self.search_var.get().lower()
        for i, (sheet, checkbox) in enumerate(zip(self.sheets, self.sheet_checkboxes)):
            if search_term in sheet.lower():
                checkbox.pack(anchor="w", padx=5, pady=2)
            else:
                checkbox.pack_forget()
        self.update_count()

    def clear_all(self):
        for var in self.sheet_vars:
            var.set(False)
        self.update_selection()

    def select_all(self):
        """Select all visible sheets"""
        for var, cb in zip(self.sheet_vars, self.sheet_checkboxes):
            if str(cb.winfo_manager()) != "":  # Only if checkbox is visible
                var.set(True)
        self.update_selection()

    def select_none(self):
        """Deselect all sheets"""
        for var in self.sheet_vars:
            var.set(False)
        self.update_selection()

    def invert_selection(self):
        """Invert current selection"""
        for var, cb in zip(self.sheet_vars, self.sheet_checkboxes):
            if str(cb.winfo_manager()) != "":  # Only if checkbox is visible
                var.set(not var.get())
        self.update_selection()

    def update_count(self):
        visible_count = sum(1 for cb in self.sheet_checkboxes if str(cb.winfo_manager()) != "")
        selected_count = sum(var.get() for var in self.sheet_vars)
        self.count_label.config(
            text=f"Showing {visible_count} of {len(self.sheets)} sheets | {selected_count} selected"
        )

    def update_selection_mode(self): 
        pass  # No longer needed
        
    def update_selection(self):
        """Update selection state and display"""
        selected = [sheet for sheet, var in zip(self.sheets, self.sheet_vars) 
                   if var.get()]

        # Update selection display
        selection_text = "Selected: " + (
            ", ".join(selected[:3] + ["..."] if len(selected) > 3 else selected)
            if selected else "None"
        )
        self.info_label.config(text=selection_text)
        self.update_count()
        
    def ok(self):
        self.selected_sheets = [sheet for sheet, var in zip(self.sheets, self.sheet_vars) 
                              if var.get()]
        self.result = self.selected_sheets
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()

class ExcelToSchemasGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.apply_theme()
        
        self.config = self.load_config()
        self.create_widgets()
        self.setup_logging()
        
        # Auto-load all settings from config
        self.load_settings_from_config()

    def load_settings_from_config(self):
        """Load all settings from config file"""
        try:
            # Load database settings
            if 'database' in self.config:
                db_config = self.config['database']
                self.driver_var.set(db_config.get('driver', ''))
                
                self.server_entry.delete(0, tk.END)
                self.server_entry.insert(0, db_config.get('server', ''))
                
                self.database_entry.delete(0, tk.END)
                self.database_entry.insert(0, db_config.get('database', ''))
                
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, db_config.get('username', ''))
                
                self.password_entry.delete(0, tk.END)
                self.password_entry.insert(0, db_config.get('password', ''))

            # Load performance settings
            self.batch_size_entry.delete(0, tk.END)
            self.batch_size_entry.insert(0, str(self.config.get('batch_size', 1000)))
            
            self.timeout_entry.delete(0, tk.END)
            self.timeout_entry.insert(0, str(self.config.get('timeout', 30)))
            
            self.retry_attempts_entry.delete(0, tk.END)
            self.retry_attempts_entry.insert(0, str(self.config.get('retry_attempts', 3)))
            
            self.log_level_entry.delete(0, tk.END)
            self.log_level_entry.insert(0, self.config.get('log_level', 'INFO'))

            # Load export settings
            self.export_var.set(self.config.get('export_type', 'database'))

            # Load Excel file and sheets
            if self.config.get('file_path'):
                self.file_path_entry.delete(0, tk.END)
                self.file_path_entry.insert(0, self.config['file_path'])
                self.update_sheet_list()
                
                if self.config.get('selected_sheets'):
                    self.update_sheets_display()
                    self.validate_selected_sheets()

            logging.info("Settings loaded from config successfully")
            self.update_status("Ready", "Settings loaded from config")
            
        except Exception as e:
            logging.error(f"Error loading settings from config: {e}")
            self.update_status("Warning", "Could not load all settings from config")

    def setup_window(self):
        # Set window title with version
        self.root.title(format_version_string())
        
        # Configure window properties
        self.root.minsize(1024, 768)  # Larger minimum size
        
        # Center the window
        window_width = 1200  # Wider default window
        window_height = 900  # Taller default window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Configure expansion behavior
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Add menu bar
        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Excel File", command=self.browse_file)
        file_menu.add_command(label="Save Settings", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Reset Window Size", 
                            command=lambda: self.root.geometry("1200x900"))
        view_menu.add_command(label="Clear Logs", 
                            command=lambda: self.log_display.delete(1.0, tk.END))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Driver Help", command=self.show_driver_help)

    def apply_theme(self):
        try:
            # Try to use ttkthemes if available
            style = ThemedStyle(self.root)
            available_themes = style.theme_names()
            
            # Try preferred themes in order
            preferred_themes = ['azure', 'winnative', 'clam', 'alt', 'default']
            selected_theme = 'default'
            
            for theme in preferred_themes:
                if theme in available_themes:
                    selected_theme = theme
                    break
            
            style.set_theme(selected_theme)
            logging.info(f"Applied theme: {selected_theme}")
            
        except Exception as e:
            logging.warning(f"Failed to apply custom theme: {e}. Using default theme.")
            # Fall back to basic ttk styling
            style = ttk.Style()
            style.theme_use('default')
        
        # Apply consistent styling regardless of theme
        default_font = ('Segoe UI', 10)
        header_font = ('Segoe UI', 12, 'bold')
        title_font = ('Segoe UI', 14, 'bold')
        
        style = ttk.Style()
        style.configure(".", font=default_font)
        style.configure("Header.TLabel", font=header_font)
        style.configure("Status.TLabel", font=default_font)
        style.configure("Title.TLabel", font=title_font)
        
        # Configure Treeview styles
        style.configure("Treeview",
                       rowheight=25,
                       font=default_font)
        style.configure("Treeview.Heading",
                       font=header_font)

        # Add custom button styles with icons and better visibility
        style.configure("Primary.TButton",
                      font=('Segoe UI', 10, 'bold'),
                      padding=10)
        style.configure("Action.TButton",
                      font=('Segoe UI', 11, 'bold'),
                      padding=10,
                      background="#28a745",
                      foreground="white")
        
        # Make buttons more visible
        style.map("Action.TButton",
                 background=[('active', '#218838'), ('disabled', '#6c757d')])
        style.map("Primary.TButton",
                 background=[('active', '#0056b3'), ('disabled', '#6c757d')])

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as config_file:
                return json.load(config_file)
        else:
            return {
                "database": {
                    "driver": "ODBC Driver 17 for SQL Server",
                    "server": "",
                    "database": "",
                    "username": "",
                    "password": ""
                },
                "file_path": "",
                "batch_size": 1000,
                "timeout": 30,
                "retry_attempts": 3,
                "log_level": "INFO"
            }

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'w') as config_file:
            json.dump(self.config, config_file, indent=4)

    def create_widgets(self):
        # Create main scrollable container
        self.canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        
        # Main container that holds everything
        self.main_container = ttk.Frame(self.canvas, padding="10")
        
        # Top action bar with main buttons
        action_bar = ttk.Frame(self.main_container)
        action_bar.pack(fill="x", pady=(0, 10))
        
        # Left side: Save button
        ttk.Button(
            action_bar,
            text="💾 Save Settings",
            command=self.save_config,
            style="Primary.TButton"
        ).pack(side="left", padx=5)
        
        # Right side: Run button
        ttk.Button(
            action_bar,
            text="▶ Run Process",
            command=self.run,
            style="Primary.TButton"
        ).pack(side="right", padx=5)
        
        # Configure canvas scrolling
        self.main_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.main_container, anchor="nw")
        
        # Configure canvas and scrollbar
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure root grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Add mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Header with version info and help menu
        header_frame = self.create_header(self.main_container)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Create tabbed interface
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # Create and add tabs
        self.setup_database_tab()
        self.setup_excel_tab()
        self.setup_settings_tab()
        
        # Status and progress section
        status_frame = self.create_status_frame(self.main_container)
        status_frame.pack(fill="x", pady=(10, 0))
        
        # Add log display
        log_frame = ttk.LabelFrame(self.main_container, text="Logs", padding="10")
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        self.log_display = scrolledtext.ScrolledText(
            log_frame,
            width=80,
            height=10,
            font=('Consolas', 9)
        )
        self.log_display.pack(fill="both", expand=True)
        self.log_display.configure(state='disabled')
        
        # Remove the old button frame since buttons are now in action bar
        # Comment out or remove: button_frame = self.create_button_frame(self.main_container)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_header(self, parent):
        header = ttk.Frame(parent)
        
        # Title and version
        version_info = get_version_info()
        title_label = ttk.Label(
            header,
            text=f"{version_info['app_name']}",
            style="Title.TLabel"
        )
        title_label.pack(side="left")
        
        version_label = ttk.Label(
            header,
            text=f"v{version_info['version']} ({version_info['release_date']})",
            style="Status.TLabel"
        )
        version_label.pack(side="left", padx=(5, 0))
        
        return header

    def setup_database_tab(self):
        db_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(db_frame, text='Database Connection')
        
        # Create groups for better organization
        conn_group = ttk.LabelFrame(db_frame, text="Connection Details", padding="10")
        conn_group.pack(fill="x", padx=5, pady=5)
        
        # Common database drivers
        self.common_drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server",
            "MySQL ODBC 8.0 Driver",
            "MySQL ODBC 5.3 Driver",
            "PostgreSQL ODBC Driver",
            "PostgreSQL ANSI",
            "Oracle ODBC Driver",
        ]
        
        # Driver selection
        ttk.Label(conn_group, text="Driver:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.driver_var = tk.StringVar()
        self.driver_combo = ttk.Combobox(
            conn_group, 
            textvariable=self.driver_var,
            values=self.common_drivers,
            width=47
        )
        self.driver_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=3)
        
        # Add help button for driver info
        ttk.Button(
            conn_group, 
            text="?",
            width=3,
            command=self.show_driver_help
        ).grid(row=0, column=2, padx=5, pady=3)
        
        # Rest of the connection fields
        fields = [
            ("Server:", "server_entry"),
            ("Database:", "database_entry"),
            ("Username:", "username_entry"),
            ("Password:", "password_entry")
        ]
        
        for i, (label_text, entry_name) in enumerate(fields, start=1):
            ttk.Label(conn_group, text=label_text).grid(row=i, column=0, sticky="e", padx=5, pady=3)
            entry = ttk.Entry(conn_group, width=50)
            entry.grid(row=i, column=1, columnspan=2, sticky="ew", padx=5, pady=3)
            setattr(self, entry_name, entry)
            
            if entry_name == "password_entry":
                entry.configure(show="*")

        # Add driver info text
        info_frame = ttk.LabelFrame(db_frame, text="Driver Information", padding="10")
        info_frame.pack(fill="x", padx=5, pady=5)
        
        info_text = """To find available ODBC drivers on your system:

Windows:
1. Open "ODBC Data Sources" from Windows Admin Tools
2. Click "Add" in System DSN tab
3. View list of installed drivers

Linux/Mac:
1. Run 'odbcinst -q -d' in terminal
2. Check installed drivers in /etc/odbcinst.ini"""

        info_label = ttk.Label(
            info_frame, 
            text=info_text,
            wraplength=550,
            justify="left"
        )
        info_label.pack(fill="x", padx=5, pady=5)
        
        # Test connection button
        ttk.Button(db_frame, text="Test Connection", command=self.test_connection).pack(
            pady=10
        )

    def show_driver_help(self):
        help_text = """Common Database Driver Names:

SQL Server:
- ODBC Driver 18 for SQL Server (Latest)
- ODBC Driver 17 for SQL Server
- SQL Server

MySQL:
- MySQL ODBC 8.0 Driver
- MySQL ODBC 5.3 Driver

PostgreSQL:
- PostgreSQL ODBC Driver
- PostgreSQL ANSI

Oracle:
- Oracle ODBC Driver
- Oracle in OraClient12Home1

Note: Available drivers depend on what's installed on your system.
Check ODBC Data Source Administrator for exact driver names."""

        messagebox.showinfo("Database Drivers Help", help_text)

    def setup_excel_tab(self):
        excel_frame = ttk.Frame(self.notebook)
        self.notebook.add(excel_frame, text='Excel Settings')
        
        # Create paned window for split view
        paned = ttk.PanedWindow(excel_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side: File and sheet selection
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # File selection group
        file_group = ttk.LabelFrame(left_frame, text="Excel File", padding="10")
        file_group.pack(fill="x", padx=5, pady=5)
        
        file_frame = ttk.Frame(file_group)
        file_frame.pack(fill="x", padx=5, pady=5)
        
        self.file_path_entry = ttk.Entry(file_frame)
        self.file_path_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(file_frame, text="Browse", 
                  command=self.browse_file,
                  style="Primary.TButton").pack(side="right", padx=5)

        # Sheet selection group
        sheet_group = ttk.LabelFrame(left_frame, text="Available Sheets", padding="10")
        sheet_group.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Search box
        search_frame = ttk.Frame(sheet_group)
        search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.sheet_search_var = tk.StringVar()
        self.sheet_search_var.trace("w", self.filter_sheets)
        ttk.Entry(search_frame, textvariable=self.sheet_search_var).pack(
            side="left", fill="x", expand=True, padx=5)

        # Sheet list with scrollbar
        list_frame = ttk.Frame(sheet_group)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.sheet_list = tk.Listbox(list_frame, 
                                    selectmode="multiple",
                                    yscrollcommand=scrollbar.set,
                                    height=10,
                                    exportselection=False)
        self.sheet_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.sheet_list.yview)
        
        # Selection summary
        self.sheet_summary = ttk.Label(
            sheet_group,
            text="No sheets selected",
            wraplength=550,
            justify="left",
            style="Status.TLabel"
        )
        self.sheet_summary.pack(fill="x", padx=5, pady=5)
        
        # Quick actions
        btn_frame = ttk.Frame(sheet_group)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Select All", 
                  command=self.select_all_sheets).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self.clear_all_sheets).pack(side="left", padx=2)

        # Right side: Preview
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        preview_group = ttk.LabelFrame(right_frame, text="Sheet Preview", padding="10")
        preview_group.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Preview controls
        preview_controls = ttk.Frame(preview_group)
        preview_controls.pack(fill="x", padx=5, pady=5)
        
        self.sheet_var = tk.StringVar()
        ttk.Label(preview_controls, text="Selected Sheet:").pack(side="left")
        self.sheet_combo = ttk.Combobox(preview_controls, 
                                       textvariable=self.sheet_var,
                                       state='readonly',
                                       width=40)
        self.sheet_combo.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(preview_controls, text="Preview",
                  command=self.preview_sheet,
                  style="Primary.TButton").pack(side="right")

        # Bind selection event
        self.sheet_list.bind('<<ListboxSelect>>', self.update_sheet_selection)

    def setup_settings_tab(self):
        settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_frame, text='Settings')
        
        # Performance settings
        perf_group = ttk.LabelFrame(settings_frame, text="Performance Settings", padding="10")
        perf_group.pack(fill="x", padx=5, pady=5)
        
        fields = [
            ("Batch Size:", "batch_size_entry"),
            ("Timeout:", "timeout_entry"),
            ("Retry Attempts:", "retry_attempts_entry"),
            ("Log Level:", "log_level_entry")
        ]
        
        for i, (label_text, entry_name) in enumerate(fields):
            ttk.Label(perf_group, text=label_text).grid(row=i, column=0, sticky="e", padx=5, pady=3)
            entry = ttk.Entry(perf_group, width=50)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=3)
            setattr(self, entry_name, entry)
        
        # Export options
        export_group = ttk.LabelFrame(settings_frame, text="Export Options", padding="10")
        export_group.pack(fill="x", padx=5, pady=5)
        
        self.export_var = tk.StringVar(value="database")
        ttk.Radiobutton(export_group, text="Import to Database", variable=self.export_var, value="database").pack(side="left", padx=5, pady=3)
        ttk.Radiobutton(export_group, text="Generate SQL Script", variable=self.export_var, value="script").pack(side="left", padx=5, pady=3)

    def create_status_frame(self, parent):
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        
        # Status message
        self.status_text = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_text,
            style="Status.TLabel"
        )
        self.status_label.pack(fill="x")
        
        # Add details text area
        self.details_text = scrolledtext.ScrolledText(
            status_frame,
            height=3,
            font=('Consolas', 9)
        )
        self.details_text.pack(fill="x", pady=(5, 0))
        
        # Progress bar with percentage
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill="x", pady=(5, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)
        
        self.progress_label = ttk.Label(
            progress_frame,
            text="0%",
            style="Status.TLabel"
        )
        self.progress_label.pack(side="left", padx=(5, 0))
        
        return status_frame

    def show_about(self):
        """Show about dialog with version info"""
        info = get_version_info()
        about_text = f"""
{info['app_name']}
Version: {info['version']}
Release Date: {info['release_date']}

{info['description']}

© 2024 Your Company Name
"""
        messagebox.showinfo("About", about_text)

    def setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[self.TkinterHandler(self.log_display)]
        )

    class TkinterHandler(logging.Handler):
        def __init__(self, text_widget):
            super().__init__()
            self.text_widget = text_widget

        def emit(self, record):
            msg = self.format(record)
            def append():
                self.text_widget.configure(state='normal')
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.configure(state='disabled')
                self.text_widget.yview(tk.END)
            self.text_widget.after(0, append)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)
            self.config['file_path'] = file_path
            self.save_config()
            self.update_sheet_list()

    def update_sheet_list(self):
        try:
            xls = pd.ExcelFile(self.file_path_entry.get())
            self.all_sheets = xls.sheet_names
            
            # Clear and repopulate sheet list
            self.sheet_list.delete(0, tk.END)
            for sheet in self.all_sheets:
                self.sheet_list.insert(tk.END, sheet)
            
            # Restore previous selections if any
            if self.config.get('selected_sheets'):
                for i, sheet in enumerate(self.all_sheets):
                    if sheet in self.config['selected_sheets']:
                        self.sheet_list.selection_set(i)
            
            # Bind selection event
            self.sheet_list.bind('<<ListboxSelect>>', self.update_sheet_selection)
            
            # Update display
            self.update_sheet_selection()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error reading Excel sheets: {str(e)}")
            logging.error(f"Error loading sheets: {e}")

    def update_sheets_display(self):
        """Update the display of selected sheets in the GUI"""
        if 'selected_sheets' not in self.config or not self.config['selected_sheets']:
            self.sheet_var.set('')
            self.sheet_summary.config(text="No sheets selected")
            return

        # Update combobox with selected sheets
        self.sheet_combo['values'] = self.config['selected_sheets']
        self.sheet_var.set(self.config['selected_sheets'][0])
        
        # Show selection summary
        count = len(self.config['selected_sheets'])
        if count <= 5:
            sheets_str = ", ".join(self.config['selected_sheets'])
        else:
            visible_sheets = ", ".join(self.config['selected_sheets'][:5])
            sheets_str = f"{visible_sheets} and {count-5} more..."
        
        summary_text = f"Selected {count} sheet(s):\n{sheets_str}"
        self.sheet_summary.config(text=summary_text)
        
        # Update status
        self.update_status("Sheets Selected", f"Selected {count} sheet(s)")

    def validate_selected_sheets(self):
        """Validate selected sheets and update status"""
        if not hasattr(self.config, 'selected_sheets'):
            return
            
        def validate_sheet(file_path, sheet_name):
            """Basic sheet validation"""
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                return not df.empty
            except Exception:
                return False
                
        invalid_sheets = []
        for sheet in self.config['selected_sheets']:
            if not validate_sheet(self.file_path_entry.get(), sheet):
                invalid_sheets.append(sheet)
                
        if invalid_sheets:
            msg = f"Invalid sheets will be skipped: {', '.join(invalid_sheets)}"
            self.update_status("Warning", msg)
            logging.warning(msg)
            
        valid_sheets = [s for s in self.config['selected_sheets'] if s not in invalid_sheets]
        if not valid_sheets:
            self.update_status("Error", "No valid sheets selected")
        else:
            self.update_status("Ready", f"Valid sheets: {', '.join(valid_sheets)}")

    def preview_sheet(self):
        if not self.file_path_entry.get():
            messagebox.showerror("Error", "Please select an Excel file first")
            return
            
        try:
            df = pd.read_excel(self.file_path_entry.get(), sheet_name=self.sheet_var.get())
            
            # Create preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Preview: {self.sheet_var.get()}")
            preview_window.geometry("800x600")

            # Create frame for the table
            frame = ttk.Frame(preview_window)
            frame.pack(fill='both', expand=True, padx=10, pady=10)

            # Create style for the treeview
            style = ttk.Style()
            style.configure("Treeview",
                          rowheight=25,
                          borderwidth=1,
                          relief="solid",
                          font=('Arial', 10))
            style.configure("Treeview.Heading",
                          font=('Arial', 10, 'bold'),
                          relief="solid",
                          borderwidth=1,
                          background="#e0e0e0")
            
            # Create treeview with scrollbars
            tree = ttk.Treeview(frame, style="Treeview")
            vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            # Grid layout with borders
            tree.grid(column=0, row=0, sticky='nsew', padx=1, pady=1)
            vsb.grid(column=1, row=0, sticky='ns')
            hsb.grid(column=0, row=1, sticky='ew')
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)

            # Configure columns
            tree["columns"] = list(df.columns)
            tree["show"] = "headings"

            # Set column headings with improved styling
            for column in df.columns:
                tree.heading(column, text=column)
                # Calculate column width based on header and content
                max_width = max(
                    len(str(column)),
                    df[column].astype(str).str.len().max()
                )
                column_width = min(max_width * 10, 300)  # limit width to 300 pixels
                tree.column(column, width=column_width, minwidth=50)

            # Add alternating row colors
            style.configure("Treeview", background="#ffffff", 
                          fieldbackground="#ffffff",
                          foreground="#000000")
            style.map("Treeview",
                     background=[('selected', '#0078d7')],
                     foreground=[('selected', '#ffffff')])

            # Add data rows with alternating colors
            for idx, row in df.head(100).iterrows():
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                tree.insert("", "end", values=list(row), tags=(tag,))

            # Configure row tags for alternating colors
            tree.tag_configure('oddrow', background='#f0f0f0')
            tree.tag_configure('evenrow', background='#ffffff')

            # Add row count label with better styling
            count_label = ttk.Label(
                preview_window, 
                text=f"Showing {min(100, len(df))} of {len(df)} rows",
                font=('Arial', 10)
            )
            count_label.pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error previewing sheet: {str(e)}")

    def test_connection(self):
        # Update config with current values
        self.update_config_from_gui()
        
        # Test connection
        connection = connect_to_database(self.config['database'])
        if connection:
            messagebox.showinfo("Success", "Database connection successful!")
            connection.close()
        else:
            messagebox.showerror("Error", "Failed to connect to database")

    def update_config_from_gui(self):
        try:
            self.config['database']['driver'] = self.driver_var.get()
            self.config['database']['server'] = self.server_entry.get()
            self.config['database']['database'] = self.database_entry.get()
            self.config['database']['username'] = self.username_entry.get()
            self.config['database']['password'] = self.password_entry.get()
            self.config['file_path'] = self.file_path_entry.get()
            self.config['batch_size'] = int(self.batch_size_entry.get())
            self.config['timeout'] = int(self.timeout_entry.get())
            self.config['retry_attempts'] = int(self.retry_attempts_entry.get())
            self.config['log_level'] = self.log_level_entry.get()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid value: {str(e)}")
            return False
        return True

    def update_status(self, status, details=None):
        """Update status display with current operation information"""
        self.status_text.set(status)
        if details:
            self.details_text.insert(tk.END, f"{details}\n")
            self.details_text.see(tk.END)
        self.root.update_idletasks()

    def run(self):
        if not self.file_path_entry.get():
            messagebox.showerror("Error", "Please select an Excel file first")
            return

        if not self.config.get('selected_sheets'):
            messagebox.showerror("Error", "Please select sheets to process")
            return

        if not self.update_config_from_gui():
            return
        
        # No longer need to set selected_sheet since we're using selected_sheets
        self.config['export_type'] = self.export_var.get()
        self.save_config()
        
        try:
            self.details_text.delete(1.0, tk.END)
            self.update_status("Starting process...")
            
            if self.export_var.get() == "script":
                self.update_status("Generating SQL scripts...", "Reading Excel data...")
                self.generate_sql_scripts()
            else:
                self.update_status("Importing to database...", "Connecting to database...")
                from main import main as run_main
                run_main(progress_callback=self.update_progress)
            
            self.update_status("Operation completed successfully!")
            messagebox.showinfo("Success", "Operation completed successfully!")
            
        except Exception as e:
            self.update_status("Error occurred!", str(e))
            messagebox.showerror("Error", str(e))

    def generate_sql_scripts(self):
        from main import process_sheets
        from validation import generate_schema  # Add this import if you prefer local import
        
        try:
            self.update_status("Processing Excel data...")
            results = process_sheets(self.config)
            if not results:
                raise ValueError("No data to process")
            
            # Create a directory for SQL scripts
            directory = filedialog.askdirectory(title="Select Directory for SQL Scripts")
            if not directory:
                return
                
            for result in results:
                sheet_name = result['sheet_name']
                self.update_status(f"Generating SQL script for {sheet_name}...")
                
                # Use generate_schema with the correct parameters
                sql_script = generate_schema(
                    result['df']  # Pass the DataFrame from the result
                )
                
                output_path = os.path.join(directory, f"{sheet_name}.sql")
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                    
                self.update_status("Success", f"Generated SQL script for {sheet_name}")
                logging.info(f"SQL script saved to {output_path}")
                
            self.update_status("All SQL scripts generated successfully!")
            
        except Exception as e:
            self.update_status("Error generating SQL scripts!", str(e))
            raise

    def update_progress(self, value):
        self.progress_var.set(value)
        self.progress_label.config(text=f"{int(value)}%")
        self.update_status("Processing...", f"Progress: {value:.1f}%")
        self.root.update_idletasks()

    def filter_sheets(self, *args):
        """Filter sheets based on search text"""
        if not hasattr(self, 'all_sheets'):
            return
            
        search_term = self.sheet_search_var.get().lower()
        self.sheet_list.delete(0, tk.END)
        
        for sheet in self.all_sheets:
            if search_term in sheet.lower():
                self.sheet_list.insert(tk.END, sheet)
                if sheet in self.config.get('selected_sheets', []):
                    idx = self.sheet_list.size() - 1
                    self.sheet_list.selection_set(idx)

    def select_all_sheets(self):
        """Select all visible sheets"""
        self.sheet_list.select_set(0, tk.END)
        self.update_sheet_selection()

    def clear_all_sheets(self):
        """Clear all sheet selections"""
        self.sheet_list.selection_clear(0, tk.END)
        self.update_sheet_selection()

    def update_sheet_selection(self, *args):
        """Update the selected sheets in config and UI"""
        selected_indices = self.sheet_list.curselection()
        selected_sheets = [self.sheet_list.get(i) for i in selected_indices]
        self.config['selected_sheets'] = selected_sheets
        self.save_config()
        
        # Update display
        if selected_sheets:
            self.sheet_combo['values'] = selected_sheets
            self.sheet_var.set(selected_sheets[0])
            
            # Update summary
            count = len(selected_sheets)
            if count <= 5:
                sheets_str = ", ".join(selected_sheets)
            else:
                visible_sheets = ", ".join(selected_sheets[:5])
                sheets_str = f"{visible_sheets} and {count-5} more..."
            
            summary_text = f"Selected {count} sheet(s):\n{sheets_str}"
            self.sheet_summary.config(text=summary_text)
            self.update_status("Sheets Selected", f"Selected {count} sheet(s)")
        else:
            self.sheet_combo['values'] = []
            self.sheet_var.set('')
            self.sheet_summary.config(text="No sheets selected")
            self.update_status("Warning", "No sheets selected")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToSchemasGUI(root)
    root.mainloop()
