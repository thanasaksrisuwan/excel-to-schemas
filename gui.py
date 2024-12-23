import os
import json
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from database import connect_to_database
import pandas as pd

class ExcelToSchemasGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel to Schemas")

        self.config = self.load_config()

        self.create_widgets()

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
        tk.Button(button_frame, text="View Logs", command=self.view_logs).grid(row=0, column=2, padx=5)

        # Move log display and progress bar
        self.log_display = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_display.grid(row=13, column=0, columnspan=3, pady=10)

        # Add progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=14, column=0, columnspan=3, sticky='ew', padx=10, pady=5)

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
            self.sheet_combo['values'] = xls.sheet_names
            if xls.sheet_names:
                self.sheet_combo.set(xls.sheet_names[0])
        except Exception as e:
            messagebox.showerror("Error", f"Error reading Excel sheets: {str(e)}")

    def preview_sheet(self):
        if not self.file_path_entry.get():
            messagebox.showerror("Error", "Please select an Excel file first")
            return
            
        try:
            df = pd.read_excel(self.file_path_entry.get(), sheet_name=self.sheet_var.get())
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Preview: {self.sheet_var.get()}")
            
            text = scrolledtext.ScrolledText(preview_window, width=100, height=30)
            text.pack(padx=10, pady=10)
            text.insert(tk.END, df.head(10).to_string())
            text.configure(state='disabled')
            
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

        if not self.sheet_var.get():
            messagebox.showerror("Error", "Please select a sheet")
            return

        if not self.update_config_from_gui():
            return
        
        self.config['selected_sheet'] = self.sheet_var.get()
        self.config['export_type'] = self.export_var.get()
        self.save_config()
        
        try:
            self.details_text.delete(1.0, tk.END)
            self.update_status("Starting process...")
            
            if self.export_var.get() == "script":
                self.update_status("Generating SQL script...", "Reading Excel data...")
                self.generate_sql_script()
            else:
                self.update_status("Importing to database...", "Connecting to database...")
                from main import main as run_main
                run_main(progress_callback=self.update_progress)
            
            self.update_status("Operation completed successfully!")
            messagebox.showinfo("Success", "Operation completed successfully!")
            
        except Exception as e:
            self.update_status("Error occurred!", str(e))
            messagebox.showerror("Error", str(e))

    def generate_sql_script(self):
        from main import process_sheet
        from validation import generate_schema
        
        try:
            self.update_status("Processing Excel data...")
            result = process_sheet(self.config)
            if not result:
                raise ValueError("No data to process")
            
            self.update_status("Generating SQL script...", "Creating table structure...")
            sql_script = generate_schema(result['df'])
            
            # Get output file path
            output_path = filedialog.asksaveasfilename(
                defaultextension=".sql",
                filetypes=[("SQL files", "*.sql"), ("All files", "*.*")],
                initialfile=f"{self.sheet_var.get()}.sql"
            )
            
            if output_path:
                self.update_status("Saving SQL script...", f"Writing to {output_path}")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                self.update_status("SQL script generated successfully!", f"Saved to {output_path}")
                logging.info(f"SQL script saved to {output_path}")
        except Exception as e:
            self.update_status("Error generating SQL script!", str(e))
            raise

    def update_progress(self, value):
        self.progress_var.set(value)
        self.update_status("Processing...", f"Progress: {value:.1f}%")
        self.root.update_idletasks()

    def view_logs(self):
        log_path = 'app.log'
        if os.path.exists(log_path):
            with open(log_path, 'r') as log_file:
                self.log_display.delete(1.0, tk.END)
                self.log_display.insert(tk.END, log_file.read())
        else:
            messagebox.showerror("Error", "Log file not found.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToSchemasGUI(root)
    root.mainloop()
