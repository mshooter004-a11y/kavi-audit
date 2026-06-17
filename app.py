# app.py
"""
Main application for KaviAudit - Financial Transaction Audit Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logging
from pathlib import Path
import os
import csv
from datetime import datetime

# Import our modules
from crypto_utils import verify_license
from database import DatabaseManager
from audit_engine import AuditEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KaviAuditApp:
    """Main application class for KaviAudit."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("KaviAudit - Financial Transaction Audit Tool")
        self.root.geometry("1000x700")
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.audit_engine = AuditEngine()
        
        # License file paths
        self.license_file = "admin_license.kvl"
        self.public_key_file = "client_public_key.pem"
        
        # Debug: Print file existence
        print(f"License file exists: {os.path.exists(self.license_file)}")
        print(f"Public key file exists: {os.path.exists(self.public_key_file)}")
        
        # Check license on startup
        if not self.check_license():
            messagebox.showerror("License Error", "Invalid or missing license. Please contact administrator.")
            self.root.quit()
            return
            
        # Create UI
        self.create_widgets()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")
    
    def check_license(self):
        """Verify the license file."""
        print(f"Checking license file: {self.license_file}")
        print(f"Checking public key file: {self.public_key_file}")
        
        if not os.path.exists(self.license_file):
            print("License file does not exist")
            return False
        if not os.path.exists(self.public_key_file):
            print("Public key file does not exist")
            return False
            
        result = verify_license(self.license_file, self.public_key_file)
        print(f"License verification result: {result}")
        return result
    
    def create_widgets(self):
        """Create all UI elements."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="KaviAudit - Financial Transaction Audit", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Transaction File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Select CSV File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_btn.grid(row=0, column=2)
        
        # Run audit button
        run_btn = ttk.Button(main_frame, text="Run Audit", command=self.run_audit_task)
        run_btn.grid(row=2, column=0, pady=(0, 20))
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="Audit Results", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview for results
        columns = ("Type", "Severity", "Description", "Timestamp")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Export buttons
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(export_frame, text="Export to CSV", command=lambda: self.export_results("csv")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_frame, text="Export to Excel", command=lambda: self.export_results("excel")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_frame, text="Export to TXT", command=lambda: self.export_results("txt")).pack(side=tk.LEFT)
        
        # Clear database button
        ttk.Button(main_frame, text="Clear Database", command=self.clear_database).grid(row=5, column=0, pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=(10, 0))
    
    def browse_file(self):
        """Open file dialog to select CSV file."""
        file_path = filedialog.askopenfilename(
            title="Select Transaction CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def run_audit_task(self):
        """Run audit in background thread."""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a CSV file first.")
            return
            
        # Disable UI during processing
        self.root.update_idletasks()
        self.status_var.set("Processing...")
        self.root.update()
        
        # Run in separate thread to avoid freezing GUI
        thread = threading.Thread(target=self.process_audit, args=(file_path,))
        thread.daemon = True
        thread.start()
    
    def process_audit(self, file_path):
        """Process audit in background thread."""
        try:
            # Run audit
            exceptions, total_records = self.audit_engine.run_audit(file_path)
            
            # Save to database
            audit_run_id = self.save_audit_result(file_path, total_records, exceptions)
            
            # Update UI on main thread
            self.root.after(0, lambda: self.display_results(audit_run_id))
            
            # Update status
            self.root.after(0, lambda: self.status_var.set(f"Audit completed. Found {len(exceptions)} exceptions."))
            
        except Exception as e:
            logger.error(f"Audit processing error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Audit failed: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Error occurred"))
    
    def save_audit_result(self, file_path, total_records, exceptions):
        """Save audit results to database."""
        # In a real implementation, we would save each record with its hash
        # For this demo, we'll just save the audit run info
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_runs (file_path, total_records, flagged_records) VALUES (?, ?, ?)",
                (file_path, total_records, len(exceptions))
            )
            audit_run_id = cursor.lastrowid
            
            # Save exceptions
            for exception in exceptions:
                # We would normally associate with a record here
                # For simplicity, we'll just save the exception details
                cursor.execute(
                    "INSERT INTO exceptions (record_id, exception_type, severity, description) VALUES (?, ?, ?, ?)",
                    (None, exception["type"], exception["severity"], exception["description"])
                )
            
            conn.commit()
            return audit_run_id
    
    def display_results(self, audit_run_id):
        """Display audit results in treeview."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Get exceptions from database
        exceptions = self.db_manager.get_exceptions(audit_run_id)
        
        # Insert data into treeview
        for exception in exceptions:
            self.results_tree.insert("", tk.END, values=(
                exception["exception_type"],
                exception["severity"],
                exception["description"],
                exception["timestamp"]
            ))
    
    def export_results(self, format_type):
        """Export results to different formats."""
        try:
            exceptions = self.db_manager.get_exceptions()
            if not exceptions:
                messagebox.showinfo("Export", "No data to export.")
                return
                
            filetypes = {
                "csv": ("CSV files", "*.csv"),
                "excel": ("Excel files", "*.xlsx"),
                "txt": ("Text files", "*.txt")
            }
            
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[filetypes[format_type]]
            )
            
            if filename:
                if format_type == "csv":
                    with open(filename, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(["Type", "Severity", "Description", "Timestamp"])
                        for exception in exceptions:
                            writer.writerow([
                                exception["exception_type"],
                                exception["severity"],
                                exception["description"],
                                exception["timestamp"]
                            ])
                elif format_type == "txt":
                    with open(filename, 'w') as txtfile:
                        txtfile.write("Audit Results\n")
                        txtfile.write("=" * 50 + "\n")
                        for exception in exceptions:
                            txtfile.write(f"Type: {exception['exception_type']}\n")
                            txtfile.write(f"Severity: {exception['severity']}\n")
                            txtfile.write(f"Description: {exception['description']}\n")
                            txtfile.write(f"Timestamp: {exception['timestamp']}\n")
                            txtfile.write("-" * 30 + "\n")
                elif format_type == "excel":
                    # For Excel export, we'd need to install openpyxl
                    # This is a placeholder for demonstration
                    messagebox.showinfo("Export", "Excel export requires openpyxl package.")
                
                messagebox.showinfo("Export", f"Results exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def clear_database(self):
        """Clear all database entries."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all database entries?"):
            self.db_manager.clear_all()
            # Clear treeview
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            self.status_var.set("Database cleared.")

def main():
    root = tk.Tk()
    app = KaviAuditApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()