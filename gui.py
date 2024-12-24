import os
import json
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from database import connect_to_database
from validation import generate_schema  # Add this import
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
        ttk.Button(btn_frame, text="Select All", command=lambda: self.mode_var.set("all")).pack(side="left", padx=5)
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
        self.root.title("Excel to Schemas")

        self.config = self.load_config()

        self.create_widgets()
        self.setup_logging()

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
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        # Database settings tab
        self.db_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.db_frame, text='Database Settings')

        tk.Label(self.db_frame, text="Database Settings").grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(self.db_frame, text="Driver:").grid(row=1, column=0, sticky=tk.E)
        self.driver_entry = tk.Entry(self.db_frame, width=50)
        self.driver_entry.grid(row=1, column=1)
        self.driver_entry.insert(0, self.config['database']['driver'])

        tk.Label(self.db_frame, text="Server:").grid(row=2, column=0, sticky=tk.E)
        self.server_entry = tk.Entry(self.db_frame, width=50)
        self.server_entry.grid(row=2, column=1)
        self.server_entry.insert(0, self.config['database']['server'])

        tk.Label(self.db_frame, text="Database:").grid(row=3, column=0, sticky=tk.E)
        self.database_entry = tk.Entry(self.db_frame, width=50)
        self.database_entry.grid(row=3, column=1)
        self.database_entry.insert(0, self.config['database']['database'])

        tk.Label(self.db_frame, text="Username:").grid(row=4, column=0, sticky=tk.E)
        self.username_entry = tk.Entry(self.db_frame, width=50)
        self.username_entry.grid(row=4, column=1)
        self.username_entry.insert(0, self.config['database']['username'])

        tk.Label(self.db_frame, text="Password:").grid(row=5, column=0, sticky=tk.E)
        self.password_entry = tk.Entry(self.db_frame, show="*", width=50)
        self.password_entry.grid(row=5, column=1)
        self.password_entry.insert(0, self.config['database']['password'])

        # Add test connection button
        tk.Button(self.db_frame, text="Test Connection", command=self.test_connection).grid(row=6, column=1, pady=5)

        # Excel file and sheet selection
        excel_frame = ttk.LabelFrame(self.root, text="Excel Settings")
        excel_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        tk.Label(excel_frame, text="Excel File:").grid(row=0, column=0, sticky=tk.E)
        self.file_path_entry = tk.Entry(excel_frame, width=50)
        self.file_path_entry.grid(row=0, column=1)
        self.file_path_entry.insert(0, self.config['file_path'])
        tk.Button(excel_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)

        tk.Label(excel_frame, text="Sheet:").grid(row=1, column=0, sticky=tk.E)
        self.sheet_var = tk.StringVar()
        self.sheet_combo = ttk.Combobox(excel_frame, textvariable=self.sheet_var, state='readonly')
        self.sheet_combo.grid(row=1, column=1, sticky="ew")

        # Preview button
        tk.Button(excel_frame, text="Preview Sheet", command=self.preview_sheet).grid(row=1, column=2)

        # Performance settings
        tk.Label(self.root, text="Batch Size:").grid(row=7, column=0, sticky=tk.E)
        self.batch_size_entry = tk.Entry(self.root, width=50)
        self.batch_size_entry.grid(row=7, column=1)
        self.batch_size_entry.insert(0, self.config['batch_size'])

        tk.Label(self.root, text="Timeout:").grid(row=8, column=0, sticky=tk.E)
        self.timeout_entry = tk.Entry(self.root, width=50)
        self.timeout_entry.grid(row=8, column=1)
        self.timeout_entry.insert(0, self.config['timeout'])

        tk.Label(self.root, text="Retry Attempts:").grid(row=9, column=0, sticky=tk.E)
        self.retry_attempts_entry = tk.Entry(self.root, width=50)
        self.retry_attempts_entry.grid(row=9, column=1)
        self.retry_attempts_entry.insert(0, self.config['retry_attempts'])

        # Log level
        tk.Label(self.root, text="Log Level:").grid(row=10, column=0, sticky=tk.E)
        self.log_level_entry = tk.Entry(self.root, width=50)
        self.log_level_entry.grid(row=10, column=1)
        self.log_level_entry.insert(0, self.config['log_level'])

        # Add export options
        self.export_var = tk.StringVar(value="database")
        export_frame = ttk.LabelFrame(self.root, text="Export Options")
        export_frame.grid(row=10, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        
        ttk.Radiobutton(export_frame, text="Import to Database", 
                       variable=self.export_var, value="database").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(export_frame, text="Generate SQL Script", 
                       variable=self.export_var, value="script").grid(row=0, column=1, padx=5)

        # Add status display area
        status_frame = ttk.LabelFrame(self.root, text="Status")
        status_frame.grid(row=11, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        
        self.status_text = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_text)
        self.status_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Add operation details display
        self.details_text = scrolledtext.ScrolledText(status_frame, width=80, height=5)
        self.details_text.grid(row=1, column=0, padx=5, pady=5)

        # Move existing buttons to new position
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=12, column=0, columnspan=3, pady=10)
        
        tk.Button(button_frame, text="Save Config", command=self.save_config).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Run", command=self.run).grid(row=0, column=1, padx=5)

        # Remove "View Logs" button
        # tk.Button(button_frame, text="View Logs", command=self.view_logs).grid(row=0, column=2, padx=5)

        # Move log display and progress bar
        self.log_display = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_display.grid(row=13, column=0, columnspan=3, pady=10)

        # Add progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=14, column=0, columnspan=3, sticky='ew', padx=10, pady=5)

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
            # Show sheet selection dialog
            self.select_sheets()

    def update_sheet_list(self):
        try:
            xls = pd.ExcelFile(self.file_path_entry.get())
            self.sheet_combo['values'] = xls.sheet_names
            if xls.sheet_names:
                self.sheet_combo.set(xls.sheet_names[0])
        except Exception as e:
            messagebox.showerror("Error", f"Error reading Excel sheets: {str(e)}")

    def select_sheets(self):
        try:
            xls = pd.ExcelFile(self.file_path_entry.get())
            current_selections = self.config.get('selected_sheets', [])
            dialog = SheetSelectionDialog(self.root, xls.sheet_names, current_selections)
            self.root.wait_window(dialog.dialog)
            if dialog.result:
                self.config['selected_sheets'] = dialog.result
                self.save_config()
                self.update_sheets_display()
                self.validate_selected_sheets()
        except Exception as e:
            messagebox.showerror("Error", f"Error selecting sheets: {str(e)}")

    def update_sheets_display(self):
        """Update the display of selected sheets in the GUI"""
        if 'selected_sheets' not in self.config or not self.config['selected_sheets']:
            self.sheet_var.set('')
            return

        # Update combobox with selected sheets
        self.sheet_combo['values'] = self.config['selected_sheets']
        self.sheet_var.set(self.config['selected_sheets'][0])
        
        # Show selection summary in status
        count = len(self.config['selected_sheets'])
        sheets_str = ', '.join(self.config['selected_sheets'][:3])
        if count > 3:
            sheets_str += f' and {count-3} more'
        self.update_status("Sheets Selected", f"Selected {count} sheet(s): {sheets_str}")

    def validate_selected_sheets(self):
        """Validate selected sheets and update status"""
        if not hasattr(self.config, 'selected_sheets'):
            return
            
        from excel import validate_sheet
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
            self.config['database']['driver'] = self.driver_entry.get()
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
        self.update_status("Processing...", f"Progress: {value:.1f}%")
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToSchemasGUI(root)
    root.mainloop()
