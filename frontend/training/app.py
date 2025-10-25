"""
Training Frontend Application

GUI for managing training jobs, monitoring progress, and analyzing metrics.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.shared.components.base_window import BaseWindow
from frontend.shared.api.training_client import TrainingAPIClient
import threading
import time

# Try to import matplotlib for metrics visualization
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Metrics charts will be disabled.")


class TrainingFrontend(BaseWindow):
    """
    Training Management Frontend
    
    Features:
    - Create training jobs with config selection
    - Monitor job progress and status
    - View training metrics and logs
    - Manage worker pool
    - Cancel/pause/resume jobs
    """
    
    def __init__(self):
        self.api_client = TrainingAPIClient()
        self.selected_job_id = None
        self.auto_refresh = False
        
        super().__init__("Training Management", width=1400, height=900)
        
        # Start connection check
        self.check_connection()
    
    def setup_toolbar_actions(self):
        """Setup toolbar buttons"""
        # Left side - Job actions
        self.add_toolbar_button(
            "➕ New Job",
            self.create_job_dialog,
            icon="➕",
            side="left"
        )
        
        self.add_toolbar_button(
            "🔄 Refresh",
            self.refresh_jobs,
            icon="🔄",
            side="left"
        )
        
        # Right side - Worker actions
        self.add_toolbar_button(
            "👷 Workers",
            self.show_worker_status,
            icon="👷",
            side="right"
        )
        
        self.add_toolbar_button(
            "📊 Metrics",
            self.show_metrics_dashboard,
            icon="📊",
            side="right"
        )
    
    def setup_sidebar_content(self):
        """Setup sidebar navigation"""
        self.add_sidebar_button("📋 All Jobs", self.show_all_jobs, icon="📋")
        self.add_sidebar_button("⏳ Pending", self.show_pending_jobs, icon="⏳")
        self.add_sidebar_button("▶️ Running", self.show_running_jobs, icon="▶️")
        self.add_sidebar_button("✅ Completed", self.show_completed_jobs, icon="✅")
        self.add_sidebar_button("❌ Failed", self.show_failed_jobs, icon="❌")
        
        # Spacer
        tk.Frame(self.sidebar_content, bg=self.COLORS['sidebar'], height=20).pack()
        
        self.add_sidebar_button("⚙️ Config Manager", self.show_config_manager, icon="⚙️")
        self.add_sidebar_button("📁 Output Files", self.show_output_files, icon="📁")
    
    def setup_main_content(self):
        """Setup main content area"""
        # Split into job list and details
        paned_window = ttk.PanedWindow(self.content_area, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left: Job list
        job_list_frame = ttk.LabelFrame(
            paned_window,
            text="Training Jobs",
            padding=10
        )
        paned_window.add(job_list_frame, weight=2)
        
        # Job list controls
        controls = ttk.Frame(job_list_frame)
        controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(controls, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(
            controls,
            textvariable=self.filter_var,
            values=["all", "pending", "running", "completed", "failed"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_jobs())
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_check = ttk.Checkbutton(
            controls,
            text="Auto-refresh (5s)",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        auto_refresh_check.pack(side=tk.RIGHT, padx=5)
        
        # Job list treeview
        tree_frame = ttk.Frame(job_list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.job_tree = ttk.Treeview(
            tree_frame,
            columns=("job_id", "type", "status", "progress", "created"),
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        
        # Configure columns
        self.job_tree.heading("job_id", text="Job ID")
        self.job_tree.heading("type", text="Type")
        self.job_tree.heading("status", text="Status")
        self.job_tree.heading("progress", text="Progress")
        self.job_tree.heading("created", text="Created")
        
        self.job_tree.column("job_id", width=100)
        self.job_tree.column("type", width=80)
        self.job_tree.column("status", width=80)
        self.job_tree.column("progress", width=100)
        self.job_tree.column("created", width=150)
        
        self.job_tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.job_tree.yview)
        tree_scroll_x.config(command=self.job_tree.xview)
        
        # Bind selection
        self.job_tree.bind("<<TreeviewSelect>>", self.on_job_select)
        
        # Right: Job details
        details_frame = ttk.LabelFrame(
            paned_window,
            text="Job Details",
            padding=10
        )
        paned_window.add(details_frame, weight=1)
        
        # Job info
        info_frame = ttk.Frame(details_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.job_info = tk.Text(
            info_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.COLORS['background']
        )
        self.job_info.pack(fill=tk.X)
        
        # Action buttons
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            action_frame,
            text="❌ Cancel Job",
            command=self.cancel_selected_job,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="📊 View Metrics",
            command=self.view_job_metrics,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        # Logs
        logs_label = ttk.Label(details_frame, text="Job Logs:")
        logs_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.job_logs = scrolledtext.ScrolledText(
            details_frame,
            height=20,
            wrap=tk.WORD,
            bg='#1E1E1E',
            fg='#D4D4D4',
            font=('Consolas', 9)
        )
        self.job_logs.pack(fill=tk.BOTH, expand=True)
        
        # Load initial jobs
        self.refresh_jobs()
    
    def check_connection(self):
        """Check backend connection"""
        def check():
            try:
                health = self.api_client.health_check()
                self.update_connection_status(
                    f"Connected - {health.get('active_jobs', 0)} active jobs",
                    connected=True
                )
            except:
                self.update_connection_status("Disconnected", connected=False)
            
            # Recheck in 10 seconds
            self.after(10000, self.check_connection)
        
        threading.Thread(target=check, daemon=True).start()
    
    def refresh_jobs(self):
        """Refresh job list"""
        def fetch():
            try:
                self.update_status("Loading jobs...")
                
                status_filter = None if self.filter_var.get() == "all" else self.filter_var.get()
                jobs = self.api_client.list_jobs(status=status_filter)
                
                # Update UI in main thread
                self.after(0, lambda: self.update_job_list(jobs))
                
            except Exception as e:
                self.after(0, lambda: self.show_error("Error", f"Failed to load jobs: {e}"))
                self.after(0, lambda: self.update_status("Error loading jobs"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_job_list(self, jobs):
        """Update job tree with job data"""
        # Clear existing
        for item in self.job_tree.get_children():
            self.job_tree.delete(item)
        
        # Add jobs
        for job in jobs:
            job_id = job.get("job_id", "")[:8]
            trainer_type = job.get("trainer_type", "")
            status = job.get("status", "")
            progress = f"{job.get('progress_percent', 0):.1f}%"
            created = job.get("created_at", "")[:19]
            
            self.job_tree.insert(
                "",
                tk.END,
                values=(job_id, trainer_type, status, progress, created),
                tags=(status,)
            )
        
        # Configure tags for status colors
        self.job_tree.tag_configure("pending", foreground=self.COLORS['warning'])
        self.job_tree.tag_configure("running", foreground=self.COLORS['primary'])
        self.job_tree.tag_configure("completed", foreground=self.COLORS['success'])
        self.job_tree.tag_configure("failed", foreground=self.COLORS['danger'])
        
        self.update_status(f"Loaded {len(jobs)} jobs")
    
    def on_job_select(self, event):
        """Handle job selection"""
        selection = self.job_tree.selection()
        if not selection:
            return
        
        item = self.job_tree.item(selection[0])
        job_id_short = item['values'][0]
        
        # Fetch full job details
        # TODO: Need full job_id mapping
        self.update_job_details_placeholder(item['values'])
    
    def update_job_details_placeholder(self, values):
        """Update job details panel (placeholder)"""
        self.job_info.config(state=tk.NORMAL)
        self.job_info.delete(1.0, tk.END)
        self.job_info.insert(tk.END, f"Job ID: {values[0]}\n")
        self.job_info.insert(tk.END, f"Type: {values[1]}\n")
        self.job_info.insert(tk.END, f"Status: {values[2]}\n")
        self.job_info.insert(tk.END, f"Progress: {values[3]}\n")
        self.job_info.insert(tk.END, f"Created: {values[4]}\n")
        self.job_info.config(state=tk.DISABLED)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh mode"""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self.auto_refresh_loop()
    
    def auto_refresh_loop(self):
        """Auto-refresh jobs every 5 seconds"""
        if self.auto_refresh:
            self.refresh_jobs()
            self.after(5000, self.auto_refresh_loop)
    
    def create_job_dialog(self):
        """Show create job dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Create Training Job")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 600) // 2
        y = self.winfo_y() + (self.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Form
        form = ttk.Frame(dialog, padding=20)
        form.pack(fill=tk.BOTH, expand=True)
        
        # Trainer type
        ttk.Label(form, text="Trainer Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        trainer_var = tk.StringVar(value="lora")
        trainer_combo = ttk.Combobox(
            form,
            textvariable=trainer_var,
            values=["lora", "qlora", "full_finetuning"],
            state="readonly",
            width=30
        )
        trainer_combo.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=10)
        
        # Config file
        ttk.Label(form, text="Config File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_var = tk.StringVar()
        config_entry = ttk.Entry(form, textvariable=config_var, width=30)
        config_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        
        def browse_config():
            filename = filedialog.askopenfilename(
                parent=dialog,
                title="Select Config File",
                filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
            )
            if filename:
                config_var.set(filename)
        
        ttk.Button(form, text="Browse...", command=browse_config).grid(row=1, column=2, pady=5)
        
        # Dataset path (optional)
        ttk.Label(form, text="Dataset Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        dataset_var = tk.StringVar()
        dataset_entry = ttk.Entry(form, textvariable=dataset_var, width=30)
        dataset_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        
        def browse_dataset():
            filename = filedialog.askdirectory(parent=dialog, title="Select Dataset Directory")
            if filename:
                dataset_var.set(filename)
        
        ttk.Button(form, text="Browse...", command=browse_dataset).grid(row=2, column=2, pady=5)
        
        # Priority
        ttk.Label(form, text="Priority:").grid(row=3, column=0, sticky=tk.W, pady=5)
        priority_var = tk.IntVar(value=1)
        priority_spin = ttk.Spinbox(form, from_=1, to=10, textvariable=priority_var, width=28)
        priority_spin.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        
        form.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def submit():
            config_path = config_var.get()
            if not config_path:
                self.show_warning("Validation Error", "Please select a config file")
                return
            
            try:
                result = self.api_client.create_job(
                    trainer_type=trainer_var.get(),
                    config_path=config_path,
                    dataset_path=dataset_var.get(),
                    priority=priority_var.get()
                )
                
                if result.get("success"):
                    job_id = result.get("job_id", "")[:8]
                    self.show_info("Success", f"Training job created: {job_id}")
                    dialog.destroy()
                    self.refresh_jobs()
                else:
                    self.show_error("Error", result.get("message", "Unknown error"))
                    
            except Exception as e:
                self.show_error("Error", f"Failed to create job: {e}")
        
        ttk.Button(
            button_frame,
            text="Create Job",
            command=submit,
            style='Primary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
    
    def cancel_selected_job(self):
        """Cancel selected job"""
        if not self.selected_job_id:
            self.show_warning("No Selection", "Please select a job to cancel")
            return
        
        # Get job info for confirmation
        job_info = "Unknown"
        job_status = "unknown"
        for item in self.job_tree.get_children():
            values = self.job_tree.item(item, 'values')
            if values and values[0] == self.selected_job_id[:8]:
                job_info = f"Trainer: {values[1]}, Status: {values[2]}"
                job_status = values[2].lower()
                break
        
        # Check if job can be cancelled
        if job_status in ['completed', 'failed', 'cancelled']:
            self.show_warning(
                "Cannot Cancel",
                f"Job is already {job_status} and cannot be cancelled"
            )
            return
        
        # Confirmation dialog
        if not self.confirm(
            "Cancel Job",
            f"Are you sure you want to cancel this job?\n\n"
            f"ID: {self.selected_job_id[:8]}\n"
            f"{job_info}\n\n"
            f"This will stop the training process immediately."
        ):
            return
        
        # Show progress
        self.update_status(f"Cancelling job {self.selected_job_id[:8]}...")
        
        def cancel_task():
            try:
                # API Call
                result = self.api_client.cancel_job(self.selected_job_id)
                
                if result.get('success'):
                    # Success
                    self.after(0, lambda: [
                        self.show_info("Cancel Complete", f"Job {self.selected_job_id[:8]} cancelled successfully"),
                        self.update_status("Job cancelled"),
                        # Refresh job list to show updated status
                        self.refresh_jobs()
                    ])
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.after(0, lambda: [
                        self.show_error("Cancel Failed", f"Failed to cancel job:\n\n{error_msg}"),
                        self.update_status("Cancel failed")
                    ])
                    
            except Exception as e:
                self.after(0, lambda: [
                    self.show_error("Cancel Error", f"Failed to cancel job:\n\n{str(e)}"),
                    self.update_status("Cancel error")
                ])
        
        # Start cancel in background thread
        threading.Thread(target=cancel_task, daemon=True).start()
    
    def view_job_metrics(self):
        """View job metrics"""
        if not self.selected_job_id:
            self.show_warning("No Selection", "Please select a job to view metrics")
            return
        
        if not MATPLOTLIB_AVAILABLE:
            self.show_warning(
                "Matplotlib Not Available",
                "Metrics visualization requires matplotlib.\n\n"
                "Install with: pip install matplotlib"
            )
            return
        
        # Fetch metrics
        def fetch_metrics():
            try:
                self.update_status(f"Fetching metrics for job {self.selected_job_id[:8]}...")
                metrics = self.api_client.get_job_metrics(self.selected_job_id)
                self.after(0, lambda: self._show_metrics_window(metrics))
            except Exception as e:
                self.after(0, lambda: [
                    self.show_error("Error", f"Failed to fetch metrics:\n\n{str(e)}"),
                    self.update_status("Failed to fetch metrics")
                ])
        
        threading.Thread(target=fetch_metrics, daemon=True).start()
    
    def _show_metrics_window(self, metrics: Dict[str, Any]):
        """Show metrics in new window"""
        window = tk.Toplevel(self)
        window.title(f"Job Metrics - {self.selected_job_id[:8]}")
        window.geometry("1100x750")
        window.transient(self)
        
        self.update_status("Metrics loaded")
        
        # Tabs
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Training Curves
        if metrics.get('epochs'):
            chart_frame = ttk.Frame(notebook)
            notebook.add(chart_frame, text="📊 Training Curves")
            
            fig = Figure(figsize=(10, 7), dpi=100)
            
            # Loss subplot
            ax1 = fig.add_subplot(2, 1, 1)
            epochs = metrics.get('epochs', [])
            train_loss = metrics.get('train_loss', [])
            val_loss = metrics.get('val_loss', [])
            
            if train_loss:
                ax1.plot(epochs, train_loss, label='Training Loss', color='#2563eb', linewidth=2, marker='o', markersize=4)
            if val_loss:
                ax1.plot(epochs, val_loss, label='Validation Loss', color='#dc2626', linewidth=2, marker='s', markersize=4)
            
            ax1.set_xlabel('Epoch', fontsize=10)
            ax1.set_ylabel('Loss', fontsize=10)
            ax1.set_title('Training & Validation Loss', fontsize=12, fontweight='bold')
            ax1.legend(loc='upper right')
            ax1.grid(True, alpha=0.3, linestyle='--')
            
            # Accuracy subplot
            ax2 = fig.add_subplot(2, 1, 2)
            train_acc = metrics.get('train_accuracy', [])
            val_acc = metrics.get('val_accuracy', [])
            
            if train_acc:
                ax2.plot(epochs, train_acc, label='Training Accuracy', color='#16a34a', linewidth=2, marker='o', markersize=4)
            if val_acc:
                ax2.plot(epochs, val_acc, label='Validation Accuracy', color='#ea580c', linewidth=2, marker='s', markersize=4)
            
            ax2.set_xlabel('Epoch', fontsize=10)
            ax2.set_ylabel('Accuracy', fontsize=10)
            ax2.set_title('Training & Validation Accuracy', fontsize=12, fontweight='bold')
            ax2.legend(loc='lower right')
            ax2.grid(True, alpha=0.3, linestyle='--')
            
            fig.tight_layout(pad=3.0)
            
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 2: Hyperparameters
        params_frame = ttk.Frame(notebook)
        notebook.add(params_frame, text="⚙️ Hyperparameters")
        
        # Create scrolled text for params
        params_container = ttk.Frame(params_frame)
        params_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        params_text = scrolledtext.ScrolledText(
            params_container,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#f8fafc',
            fg='#1e293b'
        )
        params_text.pack(fill=tk.BOTH, expand=True)
        
        hyperparams = metrics.get('hyperparameters', {})
        if hyperparams:
            params_text.insert(tk.END, "=" * 60 + "\n")
            params_text.insert(tk.END, "HYPERPARAMETERS\n")
            params_text.insert(tk.END, "=" * 60 + "\n\n")
            
            for key, value in sorted(hyperparams.items()):
                params_text.insert(tk.END, f"{key:30s} : {value}\n")
        else:
            params_text.insert(tk.END, "No hyperparameter data available")
        
        params_text.config(state=tk.DISABLED)
        
        # Tab 3: Resource Usage
        resource_frame = ttk.Frame(notebook)
        notebook.add(resource_frame, text="💻 Resource Usage")
        
        # Create treeview for resource metrics
        tree_container = ttk.Frame(resource_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tree = ttk.Treeview(
            tree_container,
            columns=('Metric', 'Value', 'Unit'),
            show='headings',
            height=15
        )
        tree.heading('Metric', text='Metric')
        tree.heading('Value', text='Value')
        tree.heading('Unit', text='Unit')
        
        tree.column('Metric', width=300)
        tree.column('Value', width=150)
        tree.column('Unit', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate resource usage
        resources = metrics.get('resource_usage', {})
        
        # GPU metrics
        tree.insert('', tk.END, values=('GPU Memory (Peak)', f"{resources.get('peak_gpu_memory_mb', 0):,.0f}", 'MB'), tags=('gpu',))
        tree.insert('', tk.END, values=('GPU Memory (Average)', f"{resources.get('avg_gpu_memory_mb', 0):,.0f}", 'MB'), tags=('gpu',))
        tree.insert('', tk.END, values=('GPU Utilization (Average)', f"{resources.get('avg_gpu_util', 0):.1f}", '%'), tags=('gpu',))
        tree.insert('', tk.END, values=('GPU Utilization (Peak)', f"{resources.get('peak_gpu_util', 0):.1f}", '%'), tags=('gpu',))
        
        # CPU metrics
        tree.insert('', tk.END, values=('CPU Utilization (Average)', f"{resources.get('avg_cpu_util', 0):.1f}", '%'), tags=('cpu',))
        tree.insert('', tk.END, values=('CPU Memory (Peak)', f"{resources.get('peak_cpu_memory_mb', 0):,.0f}", 'MB'), tags=('cpu',))
        
        # Training metrics
        tree.insert('', tk.END, values=('Training Time', f"{resources.get('training_time_s', 0):,.0f}", 'seconds'), tags=('training',))
        tree.insert('', tk.END, values=('Training Time', f"{resources.get('training_time_s', 0) / 60:.1f}", 'minutes'), tags=('training',))
        tree.insert('', tk.END, values=('Samples per Second', f"{resources.get('samples_per_sec', 0):.2f}", 'samples/s'), tags=('training',))
        tree.insert('', tk.END, values=('Total Samples Processed', f"{resources.get('total_samples', 0):,}", 'samples'), tags=('training',))
        
        # Style tags
        tree.tag_configure('gpu', background='#dbeafe')
        tree.tag_configure('cpu', background='#fef3c7')
        tree.tag_configure('training', background='#dcfce7')
        
        # Tab 4: Job Info
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="ℹ️ Job Info")
        
        info_container = ttk.Frame(info_frame)
        info_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(
            info_container,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#f8fafc',
            fg='#1e293b'
        )
        info_text.pack(fill=tk.BOTH, expand=True)
        
        # Job metadata
        job_info = metrics.get('job_info', {})
        info_text.insert(tk.END, "=" * 60 + "\n")
        info_text.insert(tk.END, "JOB INFORMATION\n")
        info_text.insert(tk.END, "=" * 60 + "\n\n")
        
        info_text.insert(tk.END, f"Job ID:          {job_info.get('job_id', 'N/A')}\n")
        info_text.insert(tk.END, f"Trainer Type:    {job_info.get('trainer_type', 'N/A')}\n")
        info_text.insert(tk.END, f"Status:          {job_info.get('status', 'N/A')}\n")
        info_text.insert(tk.END, f"Priority:        {job_info.get('priority', 'N/A')}\n")
        info_text.insert(tk.END, f"Created:         {job_info.get('created_at', 'N/A')}\n")
        info_text.insert(tk.END, f"Started:         {job_info.get('started_at', 'N/A')}\n")
        info_text.insert(tk.END, f"Completed:       {job_info.get('completed_at', 'N/A')}\n")
        info_text.insert(tk.END, f"Config Path:     {job_info.get('config_path', 'N/A')}\n")
        info_text.insert(tk.END, f"Dataset Path:    {job_info.get('dataset_path', 'N/A')}\n\n")
        
        # Tags
        if job_info.get('tags'):
            info_text.insert(tk.END, f"Tags:            {', '.join(job_info.get('tags', []))}\n")
        
        info_text.config(state=tk.DISABLED)
        
        # Close button
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT)
    
    def show_worker_status(self):
        """Show worker pool status"""
        def fetch():
            try:
                self.update_status("Fetching worker status...")
                status = self.api_client.get_worker_status()
                self.after(0, lambda: self._show_worker_status_window(status))
            except Exception as e:
                self.after(0, lambda: [
                    self.show_error("Error", f"Failed to get worker status:\n\n{str(e)}"),
                    self.update_status("Failed to fetch worker status")
                ])
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _show_worker_status_window(self, status: Dict[str, Any]):
        """Show worker status in detailed window"""
        window = tk.Toplevel(self)
        window.title("Worker Pool Status")
        window.geometry("900x600")
        window.transient(self)
        
        self.update_status("Worker status loaded")
        
        # Header with summary
        header_frame = ttk.Frame(window, padding=15)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text="Worker Pool Status",
            font=('Segoe UI', 14, 'bold')
        ).pack(anchor=tk.W)
        
        summary_frame = ttk.Frame(header_frame)
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Summary metrics
        active_workers = status.get('active_workers', 0)
        max_workers = status.get('max_workers', 0)
        idle_workers = max_workers - active_workers
        
        metrics = [
            ("Total Workers", str(max_workers), '#3b82f6'),
            ("Active", str(active_workers), '#16a34a'),
            ("Idle", str(idle_workers), '#94a3b8')
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
                font=('Segoe UI', 18, 'bold'),
                foreground=color
            ).pack(pady=(0, 5))
        
        # Worker list
        list_frame = ttk.LabelFrame(window, text="Worker Details", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Treeview for workers
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        tree = ttk.Treeview(
            tree_container,
            columns=('ID', 'Status', 'Current Job', 'Jobs Completed', 'CPU %', 'Memory MB'),
            show='headings',
            height=15
        )
        
        tree.heading('ID', text='Worker ID')
        tree.heading('Status', text='Status')
        tree.heading('Current Job', text='Current Job')
        tree.heading('Jobs Completed', text='Jobs Completed')
        tree.heading('CPU %', text='CPU %')
        tree.heading('Memory MB', text='Memory (MB)')
        
        tree.column('ID', width=100)
        tree.column('Status', width=100)
        tree.column('Current Job', width=250)
        tree.column('Jobs Completed', width=120)
        tree.column('CPU %', width=80)
        tree.column('Memory MB', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate workers
        workers = status.get('workers', [])
        
        if workers:
            for worker in workers:
                worker_id = worker.get('id', 'Unknown')
                worker_status = worker.get('status', 'unknown')
                current_job = worker.get('current_job_id', 'None')
                if current_job and current_job != 'None':
                    current_job = current_job[:8] + '...'
                jobs_completed = worker.get('jobs_completed', 0)
                cpu_percent = worker.get('cpu_percent', 0)
                memory_mb = worker.get('memory_mb', 0)
                
                tree.insert(
                    '',
                    tk.END,
                    values=(
                        worker_id,
                        worker_status,
                        current_job,
                        jobs_completed,
                        f"{cpu_percent:.1f}",
                        f"{memory_mb:,.0f}"
                    ),
                    tags=(worker_status,)
                )
        else:
            # No worker details available, show summary only
            tree.insert(
                '',
                tk.END,
                values=(
                    'N/A',
                    'Summary Only',
                    f"{active_workers} active",
                    'N/A',
                    'N/A',
                    'N/A'
                )
            )
        
        # Configure tags
        tree.tag_configure('active', background='#dcfce7', foreground='#16a34a')
        tree.tag_configure('idle', background='#f1f5f9', foreground='#64748b')
        tree.tag_configure('error', background='#fee2e2', foreground='#dc2626')
        
        # Buttons
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=15, pady=10)
        
        def refresh_workers():
            window.destroy()
            self.show_worker_status()
        
        ttk.Button(
            button_frame,
            text="Refresh",
            command=refresh_workers,
            style='Primary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
    
    def show_metrics_dashboard(self):
        """Show metrics dashboard"""
        self.show_info("Metrics Dashboard", "Dashboard not yet implemented")
    
    # Sidebar actions
    def show_all_jobs(self):
        self.filter_var.set("all")
        self.refresh_jobs()
    
    def show_pending_jobs(self):
        self.filter_var.set("pending")
        self.refresh_jobs()
    
    def show_running_jobs(self):
        self.filter_var.set("running")
        self.refresh_jobs()
    
    def show_completed_jobs(self):
        self.filter_var.set("completed")
        self.refresh_jobs()
    
    def show_failed_jobs(self):
        self.filter_var.set("failed")
        self.refresh_jobs()
    
    def show_config_manager(self):
        """Show config manager window"""
        window = tk.Toplevel(self)
        window.title("Training Configuration Manager")
        window.geometry("1200x800")
        window.transient(self)
        
        # Split view: file list | editor
        paned = ttk.PanedWindow(window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Config file list
        left_frame = ttk.LabelFrame(paned, text="Configuration Files", padding=10)
        paned.add(left_frame, weight=1)
        
        # File tree
        tree_container = ttk.Frame(left_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        config_tree = ttk.Treeview(
            tree_container,
            columns=('Size', 'Modified'),
            show='tree headings',
            height=25
        )
        
        config_tree.heading('#0', text='File Name')
        config_tree.heading('Size', text='Size')
        config_tree.heading('Modified', text='Modified')
        
        config_tree.column('#0', width=250)
        config_tree.column('Size', width=80)
        config_tree.column('Modified', width=150)
        
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=config_tree.yview)
        config_tree.configure(yscrollcommand=scrollbar.set)
        
        config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right: Editor
        right_frame = ttk.LabelFrame(paned, text="Configuration Editor", padding=10)
        paned.add(right_frame, weight=2)
        
        # File info bar
        info_bar = ttk.Frame(right_frame)
        info_bar.pack(fill=tk.X, pady=(0, 10))
        
        file_label = ttk.Label(info_bar, text="No file selected", font=('Segoe UI', 10, 'bold'))
        file_label.pack(side=tk.LEFT)
        
        # Editor
        editor_frame = ttk.Frame(right_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            selectbackground='#264f78'
        )
        editor.pack(fill=tk.BOTH, expand=True)
        
        # Editor buttons
        button_bar = ttk.Frame(right_frame)
        button_bar.pack(fill=tk.X, pady=(10, 0))
        
        selected_file_path = [None]  # Mutable container for selected file
        
        def load_configs():
            """Load config files from configs/ directory"""
            config_tree.delete(*config_tree.get_children())
            
            configs_dir = Path(__file__).parent.parent.parent / 'configs'
            
            if not configs_dir.exists():
                config_tree.insert('', tk.END, text="configs/ directory not found", values=('', ''))
                return
            
            # List all YAML files
            for config_file in sorted(configs_dir.glob('*.yaml')):
                size_kb = config_file.stat().st_size / 1024
                modified = datetime.fromtimestamp(config_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                config_tree.insert(
                    '',
                    tk.END,
                    text=config_file.name,
                    values=(f"{size_kb:.1f} KB", modified),
                    tags=('config',)
                )
            
            # Also check batch_configs/
            batch_configs_dir = configs_dir / 'batch_configs'
            if batch_configs_dir.exists():
                batch_node = config_tree.insert(
                    '',
                    tk.END,
                    text='batch_configs/',
                    values=('', ''),
                    tags=('folder',)
                )
                
                for config_file in sorted(batch_configs_dir.glob('*.yaml')):
                    size_kb = config_file.stat().st_size / 1024
                    modified = datetime.fromtimestamp(config_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    config_tree.insert(
                        batch_node,
                        tk.END,
                        text=config_file.name,
                        values=(f"{size_kb:.1f} KB", modified),
                        tags=('config',)
                    )
        
        def on_file_select(event):
            """Load selected config file"""
            selection = config_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            item_text = config_tree.item(item, 'text')
            
            # Skip folders
            if item_text.endswith('/'):
                return
            
            # Determine file path
            parent = config_tree.parent(item)
            if parent:
                # File in subfolder
                parent_text = config_tree.item(parent, 'text')
                configs_dir = Path(__file__).parent.parent.parent / 'configs' / parent_text.rstrip('/') / item_text
            else:
                # File in root
                configs_dir = Path(__file__).parent.parent.parent / 'configs' / item_text
            
            if configs_dir.exists():
                try:
                    with open(configs_dir, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Update editor
                    editor.delete(1.0, tk.END)
                    editor.insert(1.0, content)
                    
                    # Update UI
                    file_label.config(text=f"Editing: {configs_dir.name}")
                    selected_file_path[0] = configs_dir
                    
                except Exception as e:
                    file_label.config(text=f"Error loading file: {e}")
        
        def save_config():
            """Save edited config"""
            if not selected_file_path[0]:
                tk.messagebox.showwarning("No File", "Please select a config file first")
                return
            
            content = editor.get(1.0, tk.END)
            
            # Validate YAML syntax
            try:
                import yaml
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                if not tk.messagebox.askyesno(
                    "YAML Validation Error",
                    f"YAML validation failed:\n\n{str(e)}\n\nSave anyway?"
                ):
                    return
            except ImportError:
                # YAML module not available, skip validation
                pass
            
            # Create backup
            backup_path = selected_file_path[0].with_suffix('.yaml.bak')
            try:
                import shutil
                shutil.copy2(selected_file_path[0], backup_path)
            except Exception as e:
                if not tk.messagebox.askyesno(
                    "Backup Failed",
                    f"Failed to create backup:\n\n{str(e)}\n\nSave anyway?"
                ):
                    return
            
            # Save file
            try:
                with open(selected_file_path[0], 'w', encoding='utf-8') as f:
                    f.write(content)
                
                tk.messagebox.showinfo(
                    "Saved",
                    f"Configuration saved successfully!\n\nFile: {selected_file_path[0].name}\nBackup: {backup_path.name}"
                )
                
                # Refresh file list
                load_configs()
                
            except Exception as e:
                tk.messagebox.showerror("Save Error", f"Failed to save config:\n\n{str(e)}")
        
        def new_config():
            """Create new config from template"""
            template = """# Training Configuration
model:
  name: "llama-2-7b"
  type: "lora"

training:
  batch_size: 4
  learning_rate: 2.0e-5
  num_epochs: 3
  warmup_steps: 100

lora:
  r: 8
  alpha: 16
  dropout: 0.1
  target_modules: ["q_proj", "v_proj"]

dataset:
  max_length: 512
  train_split: 0.9

output:
  checkpoint_dir: "checkpoints"
  logging_steps: 10
"""
            
            editor.delete(1.0, tk.END)
            editor.insert(1.0, template)
            file_label.config(text="New Config (not saved)")
            selected_file_path[0] = None
        
        # Bind events
        config_tree.bind('<<TreeviewSelect>>', on_file_select)
        
        # Buttons
        ttk.Button(
            button_bar,
            text="💾 Save",
            command=save_config,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_bar,
            text="🔄 Reload",
            command=lambda: on_file_select(None) if selected_file_path[0] else None
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_bar,
            text="➕ New from Template",
            command=new_config
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_bar,
            text="Close",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        # Load configs on startup
        load_configs()
    
    def show_output_files(self):
        """Show output files browser"""
        window = tk.Toplevel(self)
        window.title("Training Output Files")
        window.geometry("1000x700")
        window.transient(self)
        
        # Split view: file tree | details
        paned = ttk.PanedWindow(window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: File tree
        left_frame = ttk.LabelFrame(paned, text="Output Files (models/)", padding=10)
        paned.add(left_frame, weight=2)
        
        # Filter bar
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        
        filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=filter_var,
            values=["all", ".pt", ".pth", ".safetensors", ".bin"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side=tk.LEFT)
        
        # File tree
        tree_container = ttk.Frame(left_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        file_tree = ttk.Treeview(
            tree_container,
            columns=('Size', 'Modified'),
            show='tree headings',
            height=20
        )
        
        file_tree.heading('#0', text='Name')
        file_tree.heading('Size', text='Size')
        file_tree.heading('Modified', text='Modified')
        
        file_tree.column('#0', width=300)
        file_tree.column('Size', width=100)
        file_tree.column('Modified', width=150)
        
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=file_tree.yview)
        file_tree.configure(yscrollcommand=scrollbar.set)
        
        file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right: File details
        right_frame = ttk.LabelFrame(paned, text="File Details", padding=10)
        paned.add(right_frame, weight=1)
        
        details_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#f8fafc',
            fg='#1e293b',
            height=30
        )
        details_text.pack(fill=tk.BOTH, expand=True)
        
        selected_file = [None]  # Mutable container
        
        def load_files():
            """Load files from models/ directory"""
            file_tree.delete(*file_tree.get_children())
            
            models_dir = Path(__file__).parent.parent.parent / 'models'
            
            if not models_dir.exists():
                file_tree.insert('', tk.END, text="models/ directory not found", values=('', ''))
                return
            
            filter_ext = filter_var.get()
            
            def add_directory(parent, path):
                """Recursively add directory contents"""
                try:
                    items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                    
                    for item in items:
                        # Apply filter
                        if filter_ext != "all" and item.is_file():
                            if not item.name.endswith(filter_ext):
                                continue
                        
                        if item.is_dir():
                            # Add folder
                            folder_node = file_tree.insert(
                                parent,
                                tk.END,
                                text=f"📁 {item.name}",
                                values=('', ''),
                                tags=('folder',)
                            )
                            # Recursively add contents
                            add_directory(folder_node, item)
                        else:
                            # Add file
                            size_mb = item.stat().st_size / (1024 * 1024)
                            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{item.stat().st_size / 1024:.1f} KB"
                            modified = datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                            
                            # Icon based on extension
                            icon = "📄"
                            if item.suffix in ['.pt', '.pth']:
                                icon = "🔥"  # PyTorch
                            elif item.suffix == '.safetensors':
                                icon = "🔒"  # SafeTensors
                            elif item.suffix == '.bin':
                                icon = "⚙️"   # Binary
                            
                            file_tree.insert(
                                parent,
                                tk.END,
                                text=f"{icon} {item.name}",
                                values=(size_str, modified),
                                tags=('file',),
                                iid=str(item)  # Store full path as iid
                            )
                    
                except PermissionError:
                    file_tree.insert(parent, tk.END, text="Access Denied", values=('', ''))
            
            add_directory('', models_dir)
            
            # Count files
            total_files = sum(1 for _ in models_dir.rglob('*') if _.is_file())
            total_size = sum(_.stat().st_size for _ in models_dir.rglob('*') if _.is_file())
            total_size_mb = total_size / (1024 * 1024)
            
            details_text.delete(1.0, tk.END)
            details_text.insert(tk.END, "=" * 60 + "\n")
            details_text.insert(tk.END, "MODELS DIRECTORY SUMMARY\n")
            details_text.insert(tk.END, "=" * 60 + "\n\n")
            details_text.insert(tk.END, f"Location:      {models_dir}\n")
            details_text.insert(tk.END, f"Total Files:   {total_files:,}\n")
            details_text.insert(tk.END, f"Total Size:    {total_size_mb:.2f} MB ({total_size:,} bytes)\n")
        
        def on_file_select(event):
            """Show file details"""
            selection = file_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            
            # Check if it's a file (has iid that is a path)
            try:
                file_path = Path(item)
                if not file_path.exists() or not file_path.is_file():
                    return
            except:
                return
            
            selected_file[0] = file_path
            
            # Show details
            details_text.delete(1.0, tk.END)
            details_text.insert(tk.END, "=" * 60 + "\n")
            details_text.insert(tk.END, "FILE DETAILS\n")
            details_text.insert(tk.END, "=" * 60 + "\n\n")
            
            stat = file_path.stat()
            
            details_text.insert(tk.END, f"Name:          {file_path.name}\n")
            details_text.insert(tk.END, f"Path:          {file_path}\n")
            details_text.insert(tk.END, f"Extension:     {file_path.suffix}\n")
            details_text.insert(tk.END, f"Size:          {stat.st_size / (1024*1024):.2f} MB ({stat.st_size:,} bytes)\n")
            details_text.insert(tk.END, f"Created:       {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n")
            details_text.insert(tk.END, f"Modified:      {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n")
            details_text.insert(tk.END, f"Accessed:      {datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        def open_in_explorer():
            """Open file location in Windows Explorer"""
            if not selected_file[0]:
                messagebox.showwarning("No Selection", "Please select a file first")
                return
            
            import subprocess
            subprocess.run(['explorer', '/select,', str(selected_file[0])])
        
        def delete_file():
            """Delete selected file"""
            if not selected_file[0]:
                messagebox.showwarning("No Selection", "Please select a file first")
                return
            
            if messagebox.askyesno(
                "Delete File",
                f"Are you sure you want to delete this file?\n\n{selected_file[0].name}\n\nThis action cannot be undone!"
            ):
                try:
                    selected_file[0].unlink()
                    messagebox.showinfo("Deleted", "File deleted successfully")
                    selected_file[0] = None
                    load_files()
                except Exception as e:
                    messagebox.showerror("Delete Error", f"Failed to delete file:\n\n{str(e)}")
        
        # Bind events
        file_tree.bind('<<TreeviewSelect>>', on_file_select)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: load_files())
        
        # Buttons
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="📂 Open Location",
            command=open_in_explorer
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🗑️ Delete",
            command=delete_file
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🔄 Refresh",
            command=load_files,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        # Load files on startup
        load_files()


def main():
    """Main entry point"""
    app = TrainingFrontend()
    app.mainloop()


if __name__ == "__main__":
    main()
