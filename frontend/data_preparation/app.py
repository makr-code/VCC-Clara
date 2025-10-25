"""
Data Preparation Frontend Application

GUI for dataset creation, management, and export.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import sys
from pathlib import Path
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.shared.components.base_window import BaseWindow
from frontend.shared.api.dataset_client import DatasetAPIClient
import threading


class DataPreparationFrontend(BaseWindow):
    """
    Data Preparation Frontend
    
    Features:
    - Create datasets from search queries
    - Manage dataset collection
    - Export datasets in multiple formats
    - Preview dataset contents
    - Monitor dataset processing status
    """
    
    def __init__(self):
        self.api_client = DatasetAPIClient()
        self.selected_dataset_id = None
        
        super().__init__("Data Preparation", width=1400, height=900)
        
        # Start connection check
        self.check_connection()
    
    def setup_toolbar_actions(self):
        """Setup toolbar buttons"""
        # Left side - Dataset actions
        self.add_toolbar_button(
            "➕ New Dataset",
            self.create_dataset_dialog,
            icon="➕",
            side="left"
        )
        
        self.add_toolbar_button(
            "🔄 Refresh",
            self.refresh_datasets,
            icon="🔄",
            side="left"
        )
        
        # Right side - Export actions
        self.add_toolbar_button(
            "📤 Export",
            self.export_selected_dataset,
            icon="📤",
            side="right"
        )
        
        self.add_toolbar_button(
            "🔍 Search UDS3",
            self.show_uds3_search,
            icon="🔍",
            side="right"
        )
    
    def setup_sidebar_content(self):
        """Setup sidebar navigation"""
        self.add_sidebar_button("📚 All Datasets", self.show_all_datasets, icon="📚")
        self.add_sidebar_button("⏳ Processing", self.show_processing_datasets, icon="⏳")
        self.add_sidebar_button("✅ Completed", self.show_completed_datasets, icon="✅")
        self.add_sidebar_button("❌ Failed", self.show_failed_datasets, icon="❌")
        
        # Spacer
        tk.Frame(self.sidebar_content, bg=self.COLORS['sidebar'], height=20).pack()
        
        self.add_sidebar_button("🎯 Query Builder", self.show_query_builder, icon="🎯")
        self.add_sidebar_button("📊 Statistics", self.show_statistics, icon="📊")
        self.add_sidebar_button("🗄️ Exported Files", self.show_exported_files, icon="🗄️")
    
    def setup_main_content(self):
        """Setup main content area"""
        # Split into dataset list and details
        paned_window = ttk.PanedWindow(self.content_area, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left: Dataset list
        dataset_list_frame = ttk.LabelFrame(
            paned_window,
            text="Datasets",
            padding=10
        )
        paned_window.add(dataset_list_frame, weight=2)
        
        # Search bar
        search_frame = ttk.Frame(dataset_list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_datasets())
        
        # Dataset list treeview
        tree_frame = ttk.Frame(dataset_list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dataset_tree = ttk.Treeview(
            tree_frame,
            columns=("name", "status", "size", "created"),
            show="headings",
            yscrollcommand=tree_scroll_y.set
        )
        
        # Configure columns
        self.dataset_tree.heading("name", text="Dataset Name")
        self.dataset_tree.heading("status", text="Status")
        self.dataset_tree.heading("size", text="Size")
        self.dataset_tree.heading("created", text="Created")
        
        self.dataset_tree.column("name", width=200)
        self.dataset_tree.column("status", width=100)
        self.dataset_tree.column("size", width=80)
        self.dataset_tree.column("created", width=150)
        
        self.dataset_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll_y.config(command=self.dataset_tree.yview)
        
        # Bind selection
        self.dataset_tree.bind("<<TreeviewSelect>>", self.on_dataset_select)
        
        # Right: Dataset details
        details_frame = ttk.LabelFrame(
            paned_window,
            text="Dataset Details",
            padding=10
        )
        paned_window.add(details_frame, weight=1)
        
        # Dataset info
        info_frame = ttk.Frame(details_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dataset_info = tk.Text(
            info_frame,
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.COLORS['background']
        )
        self.dataset_info.pack(fill=tk.X)
        
        # Action buttons
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            action_frame,
            text="📤 Export JSONL",
            command=lambda: self.export_dataset("jsonl"),
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="📤 Export Parquet",
            command=lambda: self.export_dataset("parquet"),
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="🗑️ Delete",
            command=self.delete_selected_dataset,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        # Search query display
        query_label = ttk.Label(details_frame, text="Search Query:")
        query_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.query_text = scrolledtext.ScrolledText(
            details_frame,
            height=8,
            wrap=tk.WORD,
            bg=self.COLORS['background']
        )
        self.query_text.pack(fill=tk.X, pady=(0, 10))
        
        # Dataset preview
        preview_label = ttk.Label(details_frame, text="Dataset Preview:")
        preview_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.dataset_preview = scrolledtext.ScrolledText(
            details_frame,
            height=15,
            wrap=tk.NONE,
            bg='#1E1E1E',
            fg='#D4D4D4',
            font=('Consolas', 9)
        )
        self.dataset_preview.pack(fill=tk.BOTH, expand=True)
        
        # Load initial datasets
        self.refresh_datasets()
    
    def check_connection(self):
        """Check backend connection"""
        def check():
            try:
                health = self.api_client.health_check()
                datasets_count = health.get('datasets_count', 0)
                uds3_status = "✓" if health.get('uds3_available') else "✗"
                self.update_connection_status(
                    f"Connected - {datasets_count} datasets, UDS3: {uds3_status}",
                    connected=True
                )
            except:
                self.update_connection_status("Disconnected", connected=False)
            
            # Recheck in 10 seconds
            self.after(10000, self.check_connection)
        
        threading.Thread(target=check, daemon=True).start()
    
    def refresh_datasets(self):
        """Refresh dataset list"""
        def fetch():
            try:
                self.update_status("Loading datasets...")
                
                # Get all datasets
                all_datasets = self.api_client.list_datasets()
                
                # Apply status filter if set
                status_filter = getattr(self, 'status_filter', None)
                if status_filter and status_filter != 'all':
                    datasets = [d for d in all_datasets if d.get('status') == status_filter]
                else:
                    datasets = all_datasets
                
                # Update UI in main thread
                self.after(0, lambda: self.update_dataset_list(datasets))
                
            except Exception as e:
                self.after(0, lambda: self.show_error("Error", f"Failed to load datasets: {e}"))
                self.after(0, lambda: self.update_status("Error loading datasets"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_dataset_list(self, datasets):
        """Update dataset tree with data"""
        # Clear existing
        for item in self.dataset_tree.get_children():
            self.dataset_tree.delete(item)
        
        # Add datasets
        for dataset in datasets:
            name = dataset.get("name", "")
            status = dataset.get("status", "")
            size = f"{dataset.get('document_count', 0)} docs"
            created = dataset.get("created_at", "")[:19]
            
            self.dataset_tree.insert(
                "",
                tk.END,
                values=(name, status, size, created),
                tags=(status,)
            )
        
        # Configure tags for status colors
        self.dataset_tree.tag_configure("pending", foreground=self.COLORS['warning'])
        self.dataset_tree.tag_configure("processing", foreground=self.COLORS['primary'])
        self.dataset_tree.tag_configure("completed", foreground=self.COLORS['success'])
        self.dataset_tree.tag_configure("failed", foreground=self.COLORS['danger'])
        
        self.update_status(f"Loaded {len(datasets)} datasets")
    
    def filter_datasets(self):
        """Filter datasets by search term"""
        search_term = self.search_var.get().lower()
        
        for item in self.dataset_tree.get_children():
            values = self.dataset_tree.item(item)['values']
            name = values[0].lower()
            
            if search_term in name:
                self.dataset_tree.reattach(item, '', 'end')
            else:
                self.dataset_tree.detach(item)
    
    def on_dataset_select(self, event):
        """Handle dataset selection"""
        selection = self.dataset_tree.selection()
        if not selection:
            return
        
        item = self.dataset_tree.item(selection[0])
        dataset_name = item['values'][0]
        
        # Update details panel (placeholder)
        self.update_dataset_details_placeholder(item['values'])
    
    def update_dataset_details_placeholder(self, values):
        """Update dataset details panel (placeholder)"""
        self.dataset_info.config(state=tk.NORMAL)
        self.dataset_info.delete(1.0, tk.END)
        self.dataset_info.insert(tk.END, f"Name: {values[0]}\n")
        self.dataset_info.insert(tk.END, f"Status: {values[1]}\n")
        self.dataset_info.insert(tk.END, f"Size: {values[2]}\n")
        self.dataset_info.insert(tk.END, f"Created: {values[3]}\n")
        self.dataset_info.config(state=tk.DISABLED)
        
        # Mock query
        self.query_text.delete(1.0, tk.END)
        self.query_text.insert(tk.END, "Query: Sample search query\n")
        self.query_text.insert(tk.END, "Top K: 100\n")
        self.query_text.insert(tk.END, "Min Score: 0.5\n")
        
        # Mock preview
        self.dataset_preview.delete(1.0, tk.END)
        self.dataset_preview.insert(tk.END, "Dataset preview not yet available...")
    
    def create_dataset_dialog(self):
        """Show create dataset dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Create Dataset")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 700) // 2
        y = self.winfo_y() + (self.winfo_height() - 600) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Form
        form = ttk.Frame(dialog, padding=20)
        form.pack(fill=tk.BOTH, expand=True)
        
        # Dataset name
        ttk.Label(form, text="Dataset Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(form, textvariable=name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=10)
        
        # Description
        ttk.Label(form, text="Description:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        desc_text = tk.Text(form, height=3, width=40)
        desc_text.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        
        # Search query
        ttk.Label(form, text="Search Query:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        query_var = tk.StringVar()
        query_entry = ttk.Entry(form, textvariable=query_var, width=40)
        query_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        
        # Top K
        ttk.Label(form, text="Top K Results:").grid(row=3, column=0, sticky=tk.W, pady=5)
        topk_var = tk.IntVar(value=100)
        topk_spin = ttk.Spinbox(form, from_=1, to=1000, textvariable=topk_var, width=38)
        topk_spin.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        
        # Min quality score
        ttk.Label(form, text="Min Quality Score:").grid(row=4, column=0, sticky=tk.W, pady=5)
        score_var = tk.DoubleVar(value=0.5)
        score_spin = ttk.Spinbox(form, from_=0.0, to=1.0, increment=0.1, textvariable=score_var, width=38)
        score_spin.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=10)
        
        # Search types
        ttk.Label(form, text="Search Types:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        search_types_frame = ttk.Frame(form)
        search_types_frame.grid(row=5, column=1, sticky=tk.W, pady=5, padx=10)
        
        vector_var = tk.BooleanVar(value=True)
        graph_var = tk.BooleanVar(value=True)
        relational_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(search_types_frame, text="Vector", variable=vector_var).pack(anchor=tk.W)
        ttk.Checkbutton(search_types_frame, text="Graph", variable=graph_var).pack(anchor=tk.W)
        ttk.Checkbutton(search_types_frame, text="Relational", variable=relational_var).pack(anchor=tk.W)
        
        # Export formats
        ttk.Label(form, text="Export Formats:").grid(row=6, column=0, sticky=tk.NW, pady=5)
        export_formats_frame = ttk.Frame(form)
        export_formats_frame.grid(row=6, column=1, sticky=tk.W, pady=5, padx=10)
        
        jsonl_var = tk.BooleanVar(value=True)
        parquet_var = tk.BooleanVar(value=False)
        csv_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(export_formats_frame, text="JSONL", variable=jsonl_var).pack(anchor=tk.W)
        ttk.Checkbutton(export_formats_frame, text="Parquet", variable=parquet_var).pack(anchor=tk.W)
        ttk.Checkbutton(export_formats_frame, text="CSV", variable=csv_var).pack(anchor=tk.W)
        
        form.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def submit():
            name = name_var.get().strip()
            query = query_var.get().strip()
            
            if not name or not query:
                self.show_warning("Validation Error", "Please fill in all required fields")
                return
            
            # Build search types list
            search_types = []
            if vector_var.get():
                search_types.append("vector")
            if graph_var.get():
                search_types.append("graph")
            if relational_var.get():
                search_types.append("relational")
            
            # Build export formats list
            export_formats = []
            if jsonl_var.get():
                export_formats.append("jsonl")
            if parquet_var.get():
                export_formats.append("parquet")
            if csv_var.get():
                export_formats.append("csv")
            
            try:
                result = self.api_client.create_dataset(
                    name=name,
                    description=desc_text.get(1.0, tk.END).strip(),
                    query_text=query,
                    top_k=topk_var.get(),
                    min_quality_score=score_var.get(),
                    search_types=search_types,
                    export_formats=export_formats
                )
                
                if result.get("success"):
                    dataset_id = result.get("dataset_id", "")[:8]
                    self.show_info("Success", f"Dataset created: {dataset_id}")
                    dialog.destroy()
                    self.refresh_datasets()
                else:
                    self.show_error("Error", result.get("message", "Unknown error"))
                    
            except Exception as e:
                self.show_error("Error", f"Failed to create dataset: {e}")
        
        ttk.Button(
            button_frame,
            text="Create Dataset",
            command=submit,
            style='Primary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
    
    def export_dataset(self, format: str):
        """Export selected dataset"""
        if not self.selected_dataset_id:
            self.show_warning("No Selection", "Please select a dataset to export")
            return
        
        # Get dataset info for filename
        dataset_name = "dataset"
        for item in self.dataset_tree.get_children():
            values = self.dataset_tree.item(item, 'values')
            if values and values[0] == self.selected_dataset_id[:8]:
                dataset_name = values[1].replace(" ", "_")
                break
        
        # Ask for save location
        default_filename = f"{dataset_name}.{format}"
        
        filetypes = {
            'jsonl': [("JSONL files", "*.jsonl"), ("All files", "*.*")],
            'parquet': [("Parquet files", "*.parquet"), ("All files", "*.*")],
            'csv': [("CSV files", "*.csv"), ("All files", "*.*")]
        }
        
        filename = filedialog.asksaveasfilename(
            parent=self,
            title=f"Export Dataset as {format.upper()}",
            defaultextension=f".{format}",
            initialfile=default_filename,
            filetypes=filetypes.get(format, [("All files", "*.*")])
        )
        
        if not filename:
            return
        
        # Show progress dialog
        progress_dialog = tk.Toplevel(self)
        progress_dialog.title("Exporting Dataset")
        progress_dialog.geometry("450x180")
        progress_dialog.transient(self)
        progress_dialog.grab_set()
        
        # Center dialog
        progress_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 450) // 2
        y = self.winfo_y() + (self.winfo_height() - 180) // 2
        progress_dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(
            progress_dialog,
            text=f"Exporting dataset to {format.upper()}...",
            font=('Segoe UI', 10),
            padding=20
        ).pack()
        
        status_label = ttk.Label(
            progress_dialog,
            text="Preparing export...",
            font=('Segoe UI', 9),
            foreground='gray'
        )
        status_label.pack()
        
        progress_bar = ttk.Progressbar(
            progress_dialog,
            mode='indeterminate',
            length=350
        )
        progress_bar.pack(pady=20, padx=20)
        progress_bar.start(10)
        
        def export_task():
            try:
                # Update status
                self.after(0, lambda: status_label.config(text="Requesting export from backend..."))
                
                # API Call
                result = self.api_client.export_dataset(
                    dataset_id=self.selected_dataset_id,
                    format=format
                )
                
                if result.get('success'):
                    # Update status
                    self.after(0, lambda: status_label.config(text="Downloading file..."))
                    
                    # Download exported file
                    download_url = result.get('download_url')
                    
                    # For local backend, construct full URL
                    if download_url.startswith('/'):
                        download_url = f"{self.api_client.base_url}{download_url}"
                    
                    response = requests.get(download_url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    # Get file size for progress (if available)
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # Save to selected location
                    downloaded = 0
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress text
                                if total_size > 0:
                                    percent = (downloaded / total_size) * 100
                                    mb_downloaded = downloaded / (1024 * 1024)
                                    mb_total = total_size / (1024 * 1024)
                                    self.after(0, lambda p=percent, d=mb_downloaded, t=mb_total: 
                                        status_label.config(text=f"Downloaded {d:.1f} MB / {t:.1f} MB ({p:.0f}%)"))
                    
                    # Success
                    self.after(0, lambda: [
                        progress_dialog.destroy(),
                        self.show_info("Export Complete", f"Dataset exported successfully:\n\n{filename}\n\nFormat: {format.upper()}\nSize: {downloaded / (1024*1024):.2f} MB")
                    ])
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.after(0, lambda: [
                        progress_dialog.destroy(),
                        self.show_error("Export Failed", f"Backend returned error:\n\n{error_msg}")
                    ])
                    
            except requests.RequestException as e:
                self.after(0, lambda: [
                    progress_dialog.destroy(),
                    self.show_error("Network Error", f"Failed to download dataset:\n\n{str(e)}")
                ])
            except Exception as e:
                self.after(0, lambda: [
                    progress_dialog.destroy(),
                    self.show_error("Export Error", f"Failed to export dataset:\n\n{str(e)}")
                ])
        
        # Start export in background thread
        threading.Thread(target=export_task, daemon=True).start()
    
    def export_selected_dataset(self):
        """Export selected dataset (default format)"""
        if not self.selected_dataset_id:
            self.show_warning("No Selection", "Please select a dataset to export")
            return
        
        # Show format selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Export Dataset")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 250) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(
            dialog,
            text="Select Export Format:",
            font=('Segoe UI', 11, 'bold'),
            padding=20
        ).pack()
        
        format_var = tk.StringVar(value="jsonl")
        
        # Format options with descriptions
        formats = [
            ("jsonl", "JSONL (JSON Lines)", "One JSON object per line, widely supported"),
            ("parquet", "Parquet", "Columnar format, efficient for large datasets"),
            ("csv", "CSV (Comma-Separated)", "Simple tabular format, Excel compatible")
        ]
        
        for value, label, desc in formats:
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            ttk.Radiobutton(
                frame,
                text=label,
                variable=format_var,
                value=value
            ).pack(anchor=tk.W)
            
            ttk.Label(
                frame,
                text=desc,
                font=('Segoe UI', 8),
                foreground='gray'
            ).pack(anchor=tk.W, padx=20)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def do_export():
            dialog.destroy()
            self.export_dataset(format_var.get())
        
        ttk.Button(
            button_frame,
            text="Export",
            command=do_export,
            style='Primary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
    
    def delete_selected_dataset(self):
        """Delete selected dataset"""
        if not self.selected_dataset_id:
            self.show_warning("No Selection", "Please select a dataset to delete")
            return
        
        # Get dataset name for confirmation
        dataset_name = "Unknown"
        for item in self.dataset_tree.get_children():
            values = self.dataset_tree.item(item, 'values')
            if values and values[0] == self.selected_dataset_id[:8]:
                dataset_name = values[1]
                break
        
        # Confirmation dialog
        if not self.confirm(
            "Delete Dataset",
            f"Are you sure you want to delete this dataset?\n\n"
            f"Name: {dataset_name}\n"
            f"ID: {self.selected_dataset_id[:8]}\n\n"
            f"This action cannot be undone!"
        ):
            return
        
        # Show progress
        self.update_status(f"Deleting dataset {self.selected_dataset_id[:8]}...")
        
        def delete_task():
            try:
                # API Call
                result = self.api_client.delete_dataset(self.selected_dataset_id)
                
                if result.get('success'):
                    # Success
                    self.after(0, lambda: [
                        self.show_info("Delete Complete", f"Dataset '{dataset_name}' deleted successfully"),
                        self.update_status("Dataset deleted"),
                        # Clear selection
                        setattr(self, 'selected_dataset_id', None),
                        # Refresh list
                        self.refresh_datasets()
                    ])
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.after(0, lambda: [
                        self.show_error("Delete Failed", f"Failed to delete dataset:\n\n{error_msg}"),
                        self.update_status("Delete failed")
                    ])
                    
            except Exception as e:
                self.after(0, lambda: [
                    self.show_error("Delete Error", f"Failed to delete dataset:\n\n{str(e)}"),
                    self.update_status("Delete error")
                ])
        
        # Start delete in background thread
        threading.Thread(target=delete_task, daemon=True).start()
    
    def show_uds3_search(self):
        """Show UDS3 search interface"""
        self.show_info("UDS3 Search", "UDS3 search interface not yet implemented")
    
    # Sidebar actions
    def show_all_datasets(self):
        """Show all datasets"""
        self.status_filter = 'all'
        self.search_var.set("")
        self.refresh_datasets()
    
    def show_processing_datasets(self):
        """Show only processing datasets"""
        self.status_filter = 'processing'
        self.search_var.set("")
        self.refresh_datasets()
    
    def show_completed_datasets(self):
        """Show only completed datasets"""
        self.status_filter = 'completed'
        self.search_var.set("")
        self.refresh_datasets()
    
    def show_failed_datasets(self):
        """Show only failed datasets"""
        self.status_filter = 'failed'
        self.search_var.set("")
        self.refresh_datasets()
    
    def show_query_builder(self):
        """Show visual query builder"""
        self.show_info("Query Builder", "Visual query builder not yet implemented")
    
    def show_statistics(self):
        """Show dataset statistics"""
        if not self.selected_dataset_id:
            self.show_warning("No Selection", "Please select a dataset to view statistics")
            return
        
        # Fetch dataset details
        def fetch_stats():
            try:
                self.update_status(f"Fetching statistics for dataset {self.selected_dataset_id[:8]}...")
                dataset = self.api_client.get_dataset(self.selected_dataset_id)
                self.after(0, lambda: self._show_statistics_window(dataset))
            except Exception as e:
                self.after(0, lambda: [
                    self.show_error("Error", f"Failed to fetch statistics:\n\n{str(e)}"),
                    self.update_status("Failed to fetch statistics")
                ])
        
        threading.Thread(target=fetch_stats, daemon=True).start()
    
    def _show_statistics_window(self, dataset: dict):
        """Show statistics in detailed window"""
        window = tk.Toplevel(self)
        window.title(f"Dataset Statistics - {dataset.get('name', 'Unknown')}")
        window.geometry("900x700")
        window.transient(self)
        
        self.update_status("Statistics loaded")
        
        # Header
        header_frame = ttk.Frame(window, padding=15)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text=f"Dataset: {dataset.get('name', 'Unknown')}",
            font=('Segoe UI', 14, 'bold')
        ).pack(anchor=tk.W)
        
        ttk.Label(
            header_frame,
            text=f"ID: {self.selected_dataset_id[:8]} | Status: {dataset.get('status', 'unknown')}",
            font=('Segoe UI', 10),
            foreground='gray'
        ).pack(anchor=tk.W)
        
        # Summary cards
        summary_frame = ttk.Frame(header_frame)
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        doc_count = dataset.get('document_count', 0)
        avg_quality = dataset.get('average_quality_score', 0.0)
        total_size_mb = dataset.get('total_size_bytes', 0) / (1024 * 1024)
        
        metrics = [
            ("Total Documents", f"{doc_count:,}", '#3b82f6'),
            ("Avg Quality Score", f"{avg_quality:.3f}", '#16a34a'),
            ("Total Size", f"{total_size_mb:.2f} MB", '#f59e0b')
        ]
        
        for label, value, color in metrics:
            card = ttk.Frame(summary_frame, relief=tk.RIDGE, borderwidth=1)
            card.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            ttk.Label(
                card,
                text=label,
                font=('Segoe UI', 9),
                foreground='gray'
            ).pack(pady=(5, 0))
            
            ttk.Label(
                card,
                text=value,
                font=('Segoe UI', 16, 'bold'),
                foreground=color
            ).pack(pady=(0, 5))
        
        # Tabs
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Tab 1: Overview
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="📊 Overview")
        
        overview_text = scrolledtext.ScrolledText(
            overview_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#f8fafc',
            fg='#1e293b'
        )
        overview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Overview info
        overview_text.insert(tk.END, "=" * 70 + "\n")
        overview_text.insert(tk.END, "DATASET OVERVIEW\n")
        overview_text.insert(tk.END, "=" * 70 + "\n\n")
        
        overview_text.insert(tk.END, f"Name:                {dataset.get('name', 'N/A')}\n")
        overview_text.insert(tk.END, f"Description:         {dataset.get('description', 'N/A')}\n")
        overview_text.insert(tk.END, f"Status:              {dataset.get('status', 'N/A')}\n")
        overview_text.insert(tk.END, f"Created:             {dataset.get('created_at', 'N/A')}\n")
        overview_text.insert(tk.END, f"Last Updated:        {dataset.get('updated_at', 'N/A')}\n\n")
        
        overview_text.insert(tk.END, "Document Statistics:\n")
        overview_text.insert(tk.END, f"  Total Documents:   {doc_count:,}\n")
        overview_text.insert(tk.END, f"  Total Size:        {total_size_mb:.2f} MB\n")
        overview_text.insert(tk.END, f"  Avg Size/Doc:      {total_size_mb / max(doc_count, 1) * 1024:.2f} KB\n\n")
        
        overview_text.insert(tk.END, "Quality Metrics:\n")
        overview_text.insert(tk.END, f"  Average Score:     {avg_quality:.3f}\n")
        overview_text.insert(tk.END, f"  Min Score:         {dataset.get('min_quality_score', 0.0):.3f}\n")
        overview_text.insert(tk.END, f"  Max Score:         {dataset.get('max_quality_score', 0.0):.3f}\n\n")
        
        # Search query info
        search_query = dataset.get('search_query', {})
        if search_query:
            overview_text.insert(tk.END, "Search Query:\n")
            overview_text.insert(tk.END, f"  Query Text:        {search_query.get('query_text', 'N/A')}\n")
            overview_text.insert(tk.END, f"  Top K:             {search_query.get('top_k', 'N/A')}\n")
            overview_text.insert(tk.END, f"  Min Quality:       {search_query.get('min_quality_score', 'N/A')}\n")
            overview_text.insert(tk.END, f"  Search Types:      {', '.join(search_query.get('search_types', []))}\n\n")
        
        # Export info
        export_formats = dataset.get('export_formats', [])
        if export_formats:
            overview_text.insert(tk.END, f"Export Formats:      {', '.join(export_formats)}\n")
        
        overview_text.config(state=tk.DISABLED)
        
        # Tab 2: Quality Distribution
        dist_frame = ttk.Frame(notebook)
        notebook.add(dist_frame, text="📈 Quality Distribution")
        
        # Quality score breakdown
        dist_container = ttk.Frame(dist_frame)
        dist_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(
            dist_container,
            text="Quality Score Distribution",
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Treeview for quality buckets
        tree = ttk.Treeview(
            dist_container,
            columns=('Range', 'Count', 'Percentage'),
            show='headings',
            height=10
        )
        
        tree.heading('Range', text='Quality Score Range')
        tree.heading('Count', text='Document Count')
        tree.heading('Percentage', text='Percentage')
        
        tree.column('Range', width=200)
        tree.column('Count', width=150)
        tree.column('Percentage', width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Quality distribution data (mock if not available)
        quality_dist = dataset.get('quality_distribution', {})
        
        if quality_dist:
            for range_key, count in sorted(quality_dist.items()):
                percentage = (count / max(doc_count, 1)) * 100
                tree.insert('', tk.END, values=(
                    range_key,
                    f"{count:,}",
                    f"{percentage:.1f}%"
                ))
        else:
            # Generate mock distribution
            ranges = [
                "0.0 - 0.2", "0.2 - 0.4", "0.4 - 0.6", 
                "0.6 - 0.8", "0.8 - 1.0"
            ]
            for r in ranges:
                tree.insert('', tk.END, values=(r, "N/A", "N/A"))
        
        # Tab 3: Search Types
        search_frame = ttk.Frame(notebook)
        notebook.add(search_frame, text="🔍 Search Types")
        
        search_container = ttk.Frame(search_frame)
        search_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(
            search_container,
            text="Documents by Search Type",
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Search type breakdown
        search_tree = ttk.Treeview(
            search_container,
            columns=('Type', 'Count', 'Percentage'),
            show='headings',
            height=8
        )
        
        search_tree.heading('Type', text='Search Type')
        search_tree.heading('Count', text='Document Count')
        search_tree.heading('Percentage', text='Percentage')
        
        search_tree.column('Type', width=200)
        search_tree.column('Count', width=150)
        search_tree.column('Percentage', width=150)
        
        search_tree.pack(fill=tk.BOTH, expand=True)
        
        # Search type data
        search_types_data = dataset.get('search_types_breakdown', {})
        
        if search_types_data:
            for search_type, count in sorted(search_types_data.items()):
                percentage = (count / max(doc_count, 1)) * 100
                search_tree.insert('', tk.END, values=(
                    search_type.title(),
                    f"{count:,}",
                    f"{percentage:.1f}%"
                ), tags=(search_type,))
        else:
            # Show configured search types
            for st in search_query.get('search_types', []):
                search_tree.insert('', tk.END, values=(
                    st.title(),
                    "N/A",
                    "N/A"
                ))
        
        # Style tags
        search_tree.tag_configure('vector', background='#dbeafe')
        search_tree.tag_configure('graph', background='#fef3c7')
        search_tree.tag_configure('relational', background='#dcfce7')
        
        # Close button
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT)
    
    def show_exported_files(self):
        """Show exported files browser"""
        window = tk.Toplevel(self)
        window.title("Exported Dataset Files")
        window.geometry("1000x650")
        window.transient(self)
        
        # Main container
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text="Exported Dataset Files",
            font=('Segoe UI', 14, 'bold')
        ).pack(side=tk.LEFT)
        
        # File list
        list_frame = ttk.LabelFrame(main_frame, text="Export Files (data/exports/)", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        file_tree = ttk.Treeview(
            tree_container,
            columns=('Format', 'Size', 'Created', 'Dataset'),
            show='headings',
            height=15
        )
        
        file_tree.heading('Format', text='File Name')
        file_tree.heading('Size', text='Size')
        file_tree.heading('Created', text='Created')
        file_tree.heading('Dataset', text='Dataset Name')
        
        file_tree.column('Format', width=300)
        file_tree.column('Size', width=100)
        file_tree.column('Created', width=150)
        file_tree.column('Dataset', width=250)
        
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=file_tree.yview)
        file_tree.configure(yscrollcommand=scrollbar.set)
        
        file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Details panel
        details_frame = ttk.LabelFrame(main_frame, text="File Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(10, 0))
        
        details_text = tk.Text(
            details_frame,
            height=6,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#f8fafc',
            fg='#1e293b'
        )
        details_text.pack(fill=tk.BOTH, expand=True)
        
        selected_file = [None]
        
        def load_exports():
            """Load exported files"""
            file_tree.delete(*file_tree.get_children())
            
            exports_dir = Path(__file__).parent.parent.parent / 'data' / 'exports'
            
            if not exports_dir.exists():
                exports_dir.mkdir(parents=True, exist_ok=True)
                file_tree.insert('', tk.END, values=('No exports found', '', '', ''))
                return
            
            # Load all export files
            export_files = []
            for ext in ['*.jsonl', '*.parquet', '*.csv']:
                export_files.extend(exports_dir.glob(ext))
            
            if not export_files:
                file_tree.insert('', tk.END, values=('No exports found', '', '', ''))
                return
            
            # Sort by modified time (newest first)
            export_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file_path in export_files:
                # Extract info
                stat = file_path.stat()
                size_mb = stat.st_size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{stat.st_size / 1024:.1f} KB"
                created = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M')
                
                # Try to extract dataset name from filename
                # Format: dataset_name_20250101_120000.ext
                name = file_path.stem
                dataset_name = "Unknown"
                
                # Common patterns
                if '_' in name:
                    parts = name.split('_')
                    # Remove timestamp-like parts
                    dataset_parts = [p for p in parts if not (p.isdigit() and len(p) >= 8)]
                    dataset_name = '_'.join(dataset_parts) if dataset_parts else name
                else:
                    dataset_name = name
                
                # Determine format/extension
                format_icon = "📄"
                if file_path.suffix == '.jsonl':
                    format_icon = "📋"
                elif file_path.suffix == '.parquet':
                    format_icon = "📊"
                elif file_path.suffix == '.csv':
                    format_icon = "📈"
                
                file_tree.insert(
                    '',
                    tk.END,
                    values=(
                        f"{format_icon} {file_path.name}",
                        size_str,
                        created,
                        dataset_name
                    ),
                    tags=(file_path.suffix[1:],),
                    iid=str(file_path)
                )
            
            # Configure tags
            file_tree.tag_configure('jsonl', background='#dbeafe')
            file_tree.tag_configure('parquet', background='#fef3c7')
            file_tree.tag_configure('csv', background='#dcfce7')
            
            # Update summary
            total_size = sum(f.stat().st_size for f in export_files)
            total_size_mb = total_size / (1024 * 1024)
            
            details_text.delete(1.0, tk.END)
            details_text.insert(tk.END, f"Total Exports: {len(export_files):,} files\n")
            details_text.insert(tk.END, f"Total Size: {total_size_mb:.2f} MB\n")
            details_text.insert(tk.END, f"Location: {exports_dir}")
        
        def on_file_select(event):
            """Show file details"""
            selection = file_tree.selection()
            if not selection:
                return
            
            try:
                file_path = Path(selection[0])
                if not file_path.exists():
                    return
            except:
                return
            
            selected_file[0] = file_path
            
            # Show details
            stat = file_path.stat()
            
            details_text.delete(1.0, tk.END)
            details_text.insert(tk.END, f"Name: {file_path.name}\n")
            details_text.insert(tk.END, f"Format: {file_path.suffix.upper()[1:]}\n")
            details_text.insert(tk.END, f"Size: {stat.st_size / (1024*1024):.2f} MB ({stat.st_size:,} bytes)\n")
            details_text.insert(tk.END, f"Created: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n")
            details_text.insert(tk.END, f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n")
            details_text.insert(tk.END, f"Path: {file_path}")
        
        def open_location():
            """Open file location in Explorer"""
            if not selected_file[0]:
                tk.messagebox.showwarning("No Selection", "Please select a file first")
                return
            
            import subprocess
            subprocess.run(['explorer', '/select,', str(selected_file[0])])
        
        def delete_file():
            """Delete selected file"""
            if not selected_file[0]:
                tk.messagebox.showwarning("No Selection", "Please select a file first")
                return
            
            if tk.messagebox.askyesno(
                "Delete Export",
                f"Are you sure you want to delete this export file?\n\n{selected_file[0].name}\n\nThis action cannot be undone!"
            ):
                try:
                    selected_file[0].unlink()
                    tk.messagebox.showinfo("Deleted", "Export file deleted successfully")
                    selected_file[0] = None
                    load_exports()
                except Exception as e:
                    tk.messagebox.showerror("Delete Error", f"Failed to delete file:\n\n{str(e)}")
        
        def open_file():
            """Open file with default application"""
            if not selected_file[0]:
                tk.messagebox.showwarning("No Selection", "Please select a file first")
                return
            
            import subprocess
            subprocess.run(['start', '', str(selected_file[0])], shell=True)
        
        # Bind events
        file_tree.bind('<<TreeviewSelect>>', on_file_select)
        
        # Buttons
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="📂 Open Location",
            command=open_location
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📄 Open File",
            command=open_file
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🗑️ Delete",
            command=delete_file
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🔄 Refresh",
            command=load_exports,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        # Load exports on startup
        load_exports()


def main():
    """Main entry point"""
    app = DataPreparationFrontend()
    app.mainloop()


if __name__ == "__main__":
    main()
