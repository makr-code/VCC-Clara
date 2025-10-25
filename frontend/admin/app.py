"""
Admin Frontend Application

GUI for system administration, service monitoring, and configuration management.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.shared.components.base_window import BaseWindow
from frontend.shared.api.training_client import TrainingAPIClient
from frontend.shared.api.dataset_client import DatasetAPIClient
import threading
import time


class AdminFrontend(BaseWindow):
    """
    Admin Frontend
    
    Features:
    - Service health monitoring (Training, Dataset, UDS3)
    - System configuration management
    - User management (future)
    - Log viewer with filtering
    - Performance metrics dashboard
    - Service control (start/stop/restart)
    """
    
    def __init__(self):
        self.training_client = TrainingAPIClient()
        self.dataset_client = DatasetAPIClient()
        
        # Service status tracking
        self.service_status = {
            'training': {'status': 'unknown', 'last_check': None},
            'dataset': {'status': 'unknown', 'last_check': None},
            'uds3': {'status': 'unknown', 'last_check': None}
        }
        
        super().__init__("System Administration", width=1400, height=900)
        
        # Start monitoring
        self.start_service_monitoring()
    
    def setup_toolbar_actions(self):
        """Setup toolbar buttons"""
        # Left side - Service controls
        self.add_toolbar_button(
            "▶️ Start All",
            self.start_all_services,
            icon="▶️",
            side="left"
        )
        
        self.add_toolbar_button(
            "⏸️ Stop All",
            self.stop_all_services,
            icon="⏸️",
            side="left"
        )
        
        self.add_toolbar_button(
            "🔄 Restart All",
            self.restart_all_services,
            icon="🔄",
            side="left"
        )
        
        # Right side - Admin tools
        self.add_toolbar_button(
            "📊 Metrics",
            self.show_metrics_dashboard,
            icon="📊",
            side="right"
        )
        
        self.add_toolbar_button(
            "📋 Logs",
            self.show_system_logs,
            icon="📋",
            side="right"
        )
    
    def setup_sidebar_content(self):
        """Setup sidebar navigation"""
        self.add_sidebar_button("🏠 Dashboard", self.show_dashboard, icon="🏠")
        self.add_sidebar_button("🔧 Services", self.show_services, icon="🔧")
        self.add_sidebar_button("⚙️ Configuration", self.show_configuration, icon="⚙️")
        
        # Spacer
        tk.Frame(self.sidebar_content, bg=self.COLORS['sidebar'], height=20).pack()
        
        self.add_sidebar_button("👥 Users", self.show_users, icon="👥")
        self.add_sidebar_button("🔐 Security", self.show_security, icon="🔐")
        self.add_sidebar_button("📊 Analytics", self.show_analytics, icon="📊")
        self.add_sidebar_button("🗃️ Database", self.show_database, icon="🗃️")
        
        # Spacer
        tk.Frame(self.sidebar_content, bg=self.COLORS['sidebar'], height=20).pack()
        
        self.add_sidebar_button("📜 Audit Log", self.show_audit_log, icon="📜")
        self.add_sidebar_button("🚨 Alerts", self.show_alerts, icon="🚨")
    
    def setup_main_content(self):
        """Setup main content area - Dashboard view"""
        self.dashboard_frame = ttk.Frame(self.content_area)
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top: Service status cards
        services_frame = ttk.LabelFrame(
            self.dashboard_frame,
            text="Service Status",
            padding=15
        )
        services_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create service status cards
        self.service_cards = {}
        
        services = [
            ("training", "Training Backend", "45680"),
            ("dataset", "Dataset Backend", "45681"),
            ("uds3", "UDS3 Framework", "Multiple")
        ]
        
        for service_id, service_name, port in services:
            card = self.create_service_card(services_frame, service_id, service_name, port)
            card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
            self.service_cards[service_id] = card
        
        # Middle: Split view for metrics and logs
        paned_window = ttk.PanedWindow(self.dashboard_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # System metrics
        metrics_frame = ttk.LabelFrame(
            paned_window,
            text="System Metrics",
            padding=10
        )
        paned_window.add(metrics_frame, weight=1)
        
        # Metrics notebook
        metrics_notebook = ttk.Notebook(metrics_frame)
        metrics_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Performance tab
        perf_frame = ttk.Frame(metrics_notebook, padding=10)
        metrics_notebook.add(perf_frame, text="Performance")
        
        self.perf_text = scrolledtext.ScrolledText(
            perf_frame,
            height=10,
            wrap=tk.WORD,
            bg=self.COLORS['background']
        )
        self.perf_text.pack(fill=tk.BOTH, expand=True)
        self.perf_text.insert(tk.END, "System metrics loading...\n")
        
        # Jobs tab
        jobs_frame = ttk.Frame(metrics_notebook, padding=10)
        metrics_notebook.add(jobs_frame, text="Jobs Overview")
        
        self.jobs_text = scrolledtext.ScrolledText(
            jobs_frame,
            height=10,
            wrap=tk.WORD,
            bg=self.COLORS['background']
        )
        self.jobs_text.pack(fill=tk.BOTH, expand=True)
        
        # Datasets tab
        datasets_frame = ttk.Frame(metrics_notebook, padding=10)
        metrics_notebook.add(datasets_frame, text="Datasets Overview")
        
        self.datasets_text = scrolledtext.ScrolledText(
            datasets_frame,
            height=10,
            wrap=tk.WORD,
            bg=self.COLORS['background']
        )
        self.datasets_text.pack(fill=tk.BOTH, expand=True)
        
        # System logs
        logs_frame = ttk.LabelFrame(
            paned_window,
            text="System Logs",
            padding=10
        )
        paned_window.add(logs_frame, weight=1)
        
        # Log controls
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(log_controls, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.log_filter_var = tk.StringVar(value="ALL")
        log_filter_combo = ttk.Combobox(
            log_controls,
            textvariable=self.log_filter_var,
            values=["ALL", "INFO", "WARNING", "ERROR", "DEBUG"],
            state="readonly",
            width=10
        )
        log_filter_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            log_controls,
            text="🔄 Refresh Logs",
            command=self.refresh_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            log_controls,
            text="🗑️ Clear",
            command=self.clear_logs
        ).pack(side=tk.RIGHT, padx=5)
        
        # Log viewer
        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            height=15,
            wrap=tk.NONE,
            bg='#1E1E1E',
            fg='#D4D4D4',
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log colors
        self.log_text.tag_configure("INFO", foreground="#4EC9B0")
        self.log_text.tag_configure("WARNING", foreground="#FFC107")
        self.log_text.tag_configure("ERROR", foreground="#F44336")
        self.log_text.tag_configure("DEBUG", foreground="#808080")
        
        # Initial log entry
        self.add_log("INFO", "Admin frontend started")
        self.add_log("INFO", "Service monitoring initialized")
    
    def create_service_card(self, parent, service_id, service_name, port):
        """Create a service status card"""
        card = tk.Frame(
            parent,
            bg='white',
            relief=tk.RAISED,
            borderwidth=2
        )
        
        # Header
        header = tk.Frame(card, bg=self.COLORS['primary'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=service_name,
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['primary'],
            fg=self.COLORS['text_light']
        ).pack(pady=10)
        
        # Content
        content = tk.Frame(card, bg='white', padx=15, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Status indicator
        status_frame = tk.Frame(content, bg='white')
        status_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            status_frame,
            text="Status:",
            font=('Segoe UI', 10),
            bg='white',
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        status_label = tk.Label(
            status_frame,
            text="🔴 Unknown",
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            anchor=tk.E
        )
        status_label.pack(side=tk.RIGHT)
        card.status_label = status_label
        
        # Port info
        port_frame = tk.Frame(content, bg='white')
        port_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            port_frame,
            text="Port:",
            font=('Segoe UI', 10),
            bg='white',
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        tk.Label(
            port_frame,
            text=port,
            font=('Segoe UI', 10),
            bg='white',
            anchor=tk.E,
            fg=self.COLORS['secondary']
        ).pack(side=tk.RIGHT)
        
        # Last check time
        time_frame = tk.Frame(content, bg='white')
        time_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            time_frame,
            text="Last Check:",
            font=('Segoe UI', 9),
            bg='white',
            fg='gray',
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        time_label = tk.Label(
            time_frame,
            text="Never",
            font=('Segoe UI', 9),
            bg='white',
            fg='gray',
            anchor=tk.E
        )
        time_label.pack(side=tk.RIGHT)
        card.time_label = time_label
        
        # Control buttons
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="▶",
            command=lambda: self.start_service(service_id),
            width=3
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="⏸",
            command=lambda: self.stop_service(service_id),
            width=3
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="🔄",
            command=lambda: self.restart_service(service_id),
            width=3
        ).pack(side=tk.LEFT, padx=2)
        
        return card
    
    def start_service_monitoring(self):
        """Start background service monitoring"""
        def monitor():
            while True:
                self.check_all_services()
                time.sleep(5)  # Check every 5 seconds
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def check_all_services(self):
        """Check status of all services"""
        # Training backend
        try:
            health = self.training_client.health_check()
            self.update_service_status('training', 'healthy', health)
        except:
            self.update_service_status('training', 'down', None)
        
        # Dataset backend
        try:
            health = self.dataset_client.health_check()
            self.update_service_status('dataset', 'healthy', health)
        except:
            self.update_service_status('dataset', 'down', None)
        
        # UDS3 (check via dataset backend)
        try:
            health = self.dataset_client.health_check()
            uds3_available = health.get('uds3_available', False)
            self.update_service_status('uds3', 'healthy' if uds3_available else 'down', health)
        except:
            self.update_service_status('uds3', 'down', None)
    
    def update_service_status(self, service_id, status, health_data):
        """Update service status card"""
        self.service_status[service_id] = {
            'status': status,
            'last_check': datetime.now(),
            'health_data': health_data
        }
        
        def update_ui():
            if service_id in self.service_cards:
                card = self.service_cards[service_id]
                
                # Update status indicator
                if status == 'healthy':
                    card.status_label.config(text="🟢 Healthy", fg=self.COLORS['success'])
                elif status == 'degraded':
                    card.status_label.config(text="🟡 Degraded", fg=self.COLORS['warning'])
                else:
                    card.status_label.config(text="🔴 Down", fg=self.COLORS['danger'])
                
                # Update last check time
                now = datetime.now()
                card.time_label.config(text=now.strftime("%H:%M:%S"))
        
        self.after(0, update_ui)
    
    def add_log(self, level, message):
        """Add log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry, level)
        self.log_text.see(tk.END)
    
    def refresh_logs(self):
        """Refresh system logs"""
        self.add_log("INFO", "Log refresh requested")
        # TODO: Fetch actual logs from services
    
    def clear_logs(self):
        """Clear log viewer"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("INFO", "Logs cleared")
    
    # Toolbar actions
    def start_all_services(self):
        """Start all services"""
        self.add_log("INFO", "Starting all services...")
        
        def start_all():
            for service_id in ['training', 'dataset']:
                self.start_service(service_id)
                time.sleep(2)  # Wait between starts
        
        threading.Thread(target=start_all, daemon=True).start()
    
    def stop_all_services(self):
        """Stop all services"""
        if not self.confirm("Stop Services", "Stop all services?\n\nThis will terminate all running jobs and datasets."):
            return
        
        self.add_log("WARNING", "Stopping all services...")
        
        def stop_all():
            for service_id in ['training', 'dataset']:
                try:
                    self._stop_service_impl(service_id)
                    time.sleep(1)
                except Exception as e:
                    self.after(0, lambda sid=service_id, err=str(e): 
                        self.add_log("ERROR", f"Failed to stop {sid}: {err}"))
        
        threading.Thread(target=stop_all, daemon=True).start()
    
    def restart_all_services(self):
        """Restart all services"""
        if not self.confirm("Restart Services", "Restart all services?\n\nThis will temporarily interrupt service."):
            return
        
        self.add_log("INFO", "Restarting all services...")
        
        def restart_all():
            # Stop all
            for service_id in ['training', 'dataset']:
                try:
                    self._stop_service_impl(service_id)
                except:
                    pass
            
            time.sleep(3)  # Wait for clean shutdown
            
            # Start all
            for service_id in ['training', 'dataset']:
                self.start_service(service_id)
                time.sleep(2)
        
        threading.Thread(target=restart_all, daemon=True).start()
    
    def show_metrics_dashboard(self):
        """Show detailed metrics dashboard"""
        self.show_info("Metrics Dashboard", "Detailed metrics dashboard not yet implemented")
    
    def show_system_logs(self):
        """Show system logs dialog"""
        self.show_info("System Logs", "Log viewer already visible in main panel")
    
    # Service control
    def start_service(self, service_id: str):
        """Start specific service"""
        script_map = {
            'training': 'start_training_backend.ps1',
            'dataset': 'start_dataset_backend.ps1'
        }
        
        script = script_map.get(service_id)
        if not script:
            self.add_log("ERROR", f"Unknown service: {service_id}")
            self.show_error("Error", f"Unknown service: {service_id}")
            return
        
        script_path = Path(__file__).parent.parent.parent / script
        
        if not script_path.exists():
            self.add_log("ERROR", f"Script not found: {script_path}")
            self.show_error("Error", f"Start script not found:\n{script_path}")
            return
        
        try:
            self.add_log("INFO", f"Starting {service_id} service...")
            
            # Start in new PowerShell window
            subprocess.Popen(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(script_path.parent)
            )
            
            # Wait for service to come up (max 10 seconds)
            def wait_for_service():
                for i in range(20):
                    time.sleep(0.5)
                    try:
                        if service_id == 'training':
                            health = self.training_client.health_check()
                        elif service_id == 'dataset':
                            health = self.dataset_client.health_check()
                        else:
                            return
                        
                        if health.get('status') == 'healthy':
                            self.after(0, lambda: [
                                self.add_log("SUCCESS", f"✅ {service_id} service started successfully"),
                                self.update_service_status(service_id, 'healthy', health)
                            ])
                            return
                    except:
                        pass
                
                # Timeout
                self.after(0, lambda: 
                    self.add_log("WARNING", f"⚠️ {service_id} service started but health check timed out"))
            
            threading.Thread(target=wait_for_service, daemon=True).start()
            
        except Exception as e:
            self.show_error("Error", f"Failed to start {service_id}:\n\n{str(e)}")
            self.add_log("ERROR", f"❌ Start {service_id} failed: {e}")
    
    def stop_service(self, service_id: str):
        """Stop specific service"""
        if not self.confirm("Stop Service", f"Stop {service_id} service?\n\nThis will terminate all {service_id} operations."):
            return
        
        self.add_log("WARNING", f"Stopping {service_id} service...")
        
        def stop_task():
            try:
                self._stop_service_impl(service_id)
            except Exception as e:
                self.after(0, lambda: [
                    self.show_error("Error", f"Failed to stop {service_id}:\n\n{str(e)}"),
                    self.add_log("ERROR", f"❌ Stop {service_id} failed: {e}")
                ])
        
        threading.Thread(target=stop_task, daemon=True).start()
    
    def _stop_service_impl(self, service_id: str):
        """Internal implementation to stop a service"""
        port_map = {
            'training': 45680,
            'dataset': 45681
        }
        
        port = port_map.get(service_id)
        if not port:
            raise ValueError(f"Unknown service: {service_id}")
        
        # Find and kill process on port
        cmd = f"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue"
        
        result = subprocess.run(
            ['powershell', '-Command', cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Wait a moment for process to die
        time.sleep(1)
        
        # Verify service is stopped
        try:
            if service_id == 'training':
                self.training_client.health_check()
                # If we get here, service is still running
                raise Exception("Service still responding after stop")
            elif service_id == 'dataset':
                self.dataset_client.health_check()
                raise Exception("Service still responding after stop")
        except:
            # Service is stopped (expected)
            self.after(0, lambda: [
                self.add_log("SUCCESS", f"✅ {service_id} service stopped"),
                self.update_service_status(service_id, 'stopped', {})
            ])
    
    def restart_service(self, service_id: str):
        """Restart specific service"""
        self.add_log("INFO", f"Restarting {service_id} service...")
        
        def restart_task():
            try:
                # Stop
                self._stop_service_impl(service_id)
                time.sleep(2)
                
                # Start
                self.after(0, lambda: self.start_service(service_id))
                
            except Exception as e:
                self.after(0, lambda: [
                    self.show_error("Error", f"Failed to restart {service_id}:\n\n{str(e)}"),
                    self.add_log("ERROR", f"❌ Restart {service_id} failed: {e}")
                ])
        
        threading.Thread(target=restart_task, daemon=True).start()
    
    # Sidebar navigation
    def show_dashboard(self):
        """Show main dashboard"""
        self.add_log("INFO", "Switched to Dashboard view")
    
    def show_services(self):
        """Show services management"""
        self.add_log("INFO", "Switched to Services view")
        self.show_info("Services", "Services management view not yet implemented")
    
    def show_configuration(self):
        """Show system configuration manager"""
        self.add_log("INFO", "Opening System Configuration Manager")
        
        # Create window
        window = tk.Toplevel(self)
        window.title("System Configuration Manager")
        window.geometry("1100x700")
        
        # Main container
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(
            main_frame,
            text="⚙️ System Configuration",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=(0, 15))
        
        # Split view: file browser | config editor
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Config file browser
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)
        
        ttk.Label(
            left_panel,
            text="Configuration Files",
            font=("Helvetica", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Config directories to scan
        config_dirs = [
            ('Backend Configs', 'backend/'),
            ('Training Configs', 'configs/'),
            ('Shared Configs', 'shared/')
        ]
        
        # File tree
        tree_frame = ttk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        file_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            selectmode='browse'
        )
        file_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=file_tree.yview)
        
        file_tree['columns'] = ('Type', 'Size')
        file_tree.column('#0', width=250)
        file_tree.column('Type', width=80)
        file_tree.column('Size', width=80)
        
        file_tree.heading('#0', text='File Name')
        file_tree.heading('Type', text='Type')
        file_tree.heading('Size', text='Size')
        
        # Populate file tree
        for dir_name, dir_path in config_dirs:
            full_path = Path(project_root) / dir_path
            if full_path.exists():
                parent = file_tree.insert('', tk.END, text=f"📁 {dir_name}", values=('Folder', ''))
                
                # Add config files
                for config_file in sorted(full_path.rglob('*.yaml')) + sorted(full_path.rglob('*.yml')) + sorted(full_path.rglob('*.json')):
                    if config_file.is_file():
                        size_kb = config_file.stat().st_size / 1024
                        file_type = config_file.suffix.upper()[1:]
                        
                        file_tree.insert(
                            parent,
                            tk.END,
                            text=f"📄 {config_file.name}",
                            values=(file_type, f"{size_kb:.1f} KB"),
                            tags=(str(config_file),)
                        )
        
        # Right panel: Config editor
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=2)
        
        # Editor header
        editor_header = ttk.Frame(right_panel)
        editor_header.pack(fill=tk.X, pady=(0, 10))
        
        current_file_label = ttk.Label(
            editor_header,
            text="No file selected",
            font=("Helvetica", 11, "bold")
        )
        current_file_label.pack(side=tk.LEFT)
        
        # Editor
        editor_frame = ttk.Frame(right_panel)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        editor_scroll_y = ttk.Scrollbar(editor_frame)
        editor_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        editor_scroll_x = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL)
        editor_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        editor = scrolledtext.ScrolledText(
            editor_frame,
            font=("Consolas", 10),
            wrap=tk.NONE,
            yscrollcommand=editor_scroll_y.set,
            xscrollcommand=editor_scroll_x.set
        )
        editor.pack(fill=tk.BOTH, expand=True)
        editor_scroll_y.config(command=editor.yview)
        editor_scroll_x.config(command=editor.xview)
        
        # Disable initially
        editor.insert(tk.END, "Select a configuration file to edit")
        editor.config(state=tk.DISABLED)
        
        # Track current file
        current_file_path = [None]
        
        def load_config_file(file_path):
            """Load config file into editor"""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                editor.config(state=tk.NORMAL)
                editor.delete(1.0, tk.END)
                editor.insert(tk.END, content)
                editor.config(state=tk.NORMAL)
                
                current_file_label.config(text=f"📄 {Path(file_path).name}")
                current_file_path[0] = file_path
                
                self.add_log("INFO", f"Loaded config: {Path(file_path).name}")
                
            except Exception as e:
                self.add_log("ERROR", f"Failed to load {file_path}: {e}")
                editor.config(state=tk.NORMAL)
                editor.delete(1.0, tk.END)
                editor.insert(tk.END, f"Error loading file: {e}")
                editor.config(state=tk.DISABLED)
        
        def on_file_select(event):
            """Handle file selection"""
            selection = file_tree.selection()
            if selection:
                item = selection[0]
                tags = file_tree.item(item, 'tags')
                if tags and tags[0]:
                    file_path = tags[0]
                    load_config_file(file_path)
        
        file_tree.bind('<<TreeviewSelect>>', on_file_select)
        
        # Bottom actions
        actions_frame = ttk.Frame(right_panel)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_config():
            """Save configuration file"""
            if not current_file_path[0]:
                return
            
            try:
                # Validate YAML/JSON syntax
                content = editor.get(1.0, tk.END).strip()
                file_path = Path(current_file_path[0])
                
                if file_path.suffix in ['.yaml', '.yml']:
                    try:
                        import yaml
                        yaml.safe_load(content)
                    except:
                        if tk.messagebox.askyesno(
                            "Validation Warning",
                            "YAML validation failed. Save anyway?",
                            parent=window
                        ):
                            pass
                        else:
                            return
                elif file_path.suffix == '.json':
                    import json
                    json.loads(content)
                
                # Create backup
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                if file_path.exists():
                    import shutil
                    shutil.copy2(file_path, backup_path)
                
                # Save file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.add_log("INFO", f"Saved config: {file_path.name} (backup: {backup_path.name})")
                tk.messagebox.showinfo(
                    "Success",
                    f"Configuration saved successfully!\n\nBackup created: {backup_path.name}",
                    parent=window
                )
                
            except Exception as e:
                self.add_log("ERROR", f"Failed to save config: {e}")
                tk.messagebox.showerror(
                    "Save Error",
                    f"Failed to save configuration:\n{e}",
                    parent=window
                )
        
        def reload_config():
            """Reload configuration from disk"""
            if current_file_path[0]:
                if tk.messagebox.askyesno(
                    "Reload",
                    "Discard unsaved changes and reload from disk?",
                    parent=window
                ):
                    load_config_file(current_file_path[0])
        
        def validate_config():
            """Validate configuration syntax"""
            if not current_file_path[0]:
                return
            
            try:
                content = editor.get(1.0, tk.END).strip()
                file_path = Path(current_file_path[0])
                
                if file_path.suffix in ['.yaml', '.yml']:
                    try:
                        import yaml
                        yaml.safe_load(content)
                        tk.messagebox.showinfo(
                            "Validation",
                            "✅ YAML syntax is valid!",
                            parent=window
                        )
                    except Exception as e:
                        tk.messagebox.showerror(
                            "Validation Error",
                            f"❌ YAML syntax error:\n{e}",
                            parent=window
                        )
                elif file_path.suffix == '.json':
                    import json
                    json.loads(content)
                    tk.messagebox.showinfo(
                        "Validation",
                        "✅ JSON syntax is valid!",
                        parent=window
                    )
                else:
                    tk.messagebox.showinfo(
                        "Validation",
                        "No syntax validation available for this file type",
                        parent=window
                    )
                    
            except Exception as e:
                tk.messagebox.showerror(
                    "Validation Error",
                    f"Syntax error:\n{e}",
                    parent=window
                )
        
        ttk.Button(
            actions_frame,
            text="💾 Save",
            command=save_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="🔄 Reload",
            command=reload_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="✅ Validate",
            command=validate_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="❌ Close",
            command=window.destroy
        ).pack(side=tk.RIGHT)
    
    def show_users(self):
        """Show user management"""
        self.add_log("INFO", "Switched to Users view")
        self.show_info("Users", "User management not yet implemented")
    
    def show_security(self):
        """Show security settings"""
        self.add_log("INFO", "Switched to Security view")
        self.show_info("Security", "Security settings not yet implemented")
    
    def show_analytics(self):
        """Show analytics dashboard"""
        self.add_log("INFO", "Switched to Analytics view")
        self.show_info("Analytics", "Analytics dashboard not yet implemented")
    
    def show_database(self):
        """Show UDS3 backend status and management"""
        self.add_log("INFO", "Opening Database Management UI")
        
        # Create window
        window = tk.Toplevel(self)
        window.title("Database Management - UDS3 Backends")
        window.geometry("900x700")
        
        # Main container
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(
            main_frame,
            text="🗄️ Database Management",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=(0, 15))
        
        # Backend status cards frame
        cards_frame = ttk.Frame(main_frame)
        cards_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure grid
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.rowconfigure(0, weight=1)
        cards_frame.rowconfigure(1, weight=1)
        
        # Backend configurations
        backends = [
            {
                'name': 'PostgreSQL',
                'icon': '🐘',
                'host': '192.168.178.94',
                'port': 5432,
                'type': 'Relational',
                'color': '#336791'
            },
            {
                'name': 'ChromaDB',
                'icon': '🔍',
                'host': '192.168.178.94',
                'port': 8000,
                'type': 'Vector',
                'color': '#ff6b6b'
            },
            {
                'name': 'Neo4j',
                'icon': '🕸️',
                'host': '192.168.178.94',
                'port': 7687,
                'type': 'Graph',
                'color': '#00857d'
            },
            {
                'name': 'CouchDB',
                'icon': '📦',
                'host': '192.168.178.94',
                'port': 32931,
                'type': 'Document',
                'color': '#e42528'
            }
        ]
        
        # Create status cards
        for idx, backend in enumerate(backends):
            row = idx // 2
            col = idx % 2
            
            # Card frame
            card = ttk.LabelFrame(
                cards_frame,
                text=f"{backend['icon']} {backend['name']}",
                padding=15
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Connection info
            info_frame = ttk.Frame(card)
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(
                info_frame,
                text=f"Type: {backend['type']}",
                font=("Helvetica", 10)
            ).pack(anchor=tk.W)
            
            ttk.Label(
                info_frame,
                text=f"Host: {backend['host']}:{backend['port']}",
                font=("Helvetica", 9),
                foreground='#666666'
            ).pack(anchor=tk.W)
            
            # Status indicator
            status_frame = ttk.Frame(card)
            status_frame.pack(fill=tk.X, pady=5)
            
            status_label = ttk.Label(
                status_frame,
                text="● Status: Checking...",
                font=("Helvetica", 10, "bold")
            )
            status_label.pack(anchor=tk.W)
            
            # Metrics frame
            metrics_frame = ttk.Frame(card)
            metrics_frame.pack(fill=tk.X, pady=5)
            
            metrics_text = scrolledtext.ScrolledText(
                metrics_frame,
                height=4,
                width=30,
                font=("Consolas", 9),
                background='#f8f9fa'
            )
            metrics_text.pack(fill=tk.BOTH, expand=True)
            metrics_text.insert(tk.END, "No metrics available")
            metrics_text.config(state=tk.DISABLED)
            
            # Action buttons
            btn_frame = ttk.Frame(card)
            btn_frame.pack(fill=tk.X, pady=(10, 0))
            
            test_btn = ttk.Button(
                btn_frame,
                text="🔗 Test Connection",
                command=lambda b=backend, s=status_label, m=metrics_text: self._test_backend_connection(b, s, m)
            )
            test_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            refresh_btn = ttk.Button(
                btn_frame,
                text="🔄 Refresh",
                command=lambda b=backend, s=status_label, m=metrics_text: self._refresh_backend_metrics(b, s, m)
            )
            refresh_btn.pack(side=tk.LEFT)
        
        # Bottom actions
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            actions_frame,
            text="🔗 Test All Connections",
            command=lambda: self._test_all_backends(cards_frame)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="📊 View Full Metrics",
            command=self._show_full_metrics
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="❌ Close",
            command=window.destroy
        ).pack(side=tk.RIGHT)
    
    def _test_backend_connection(self, backend, status_label, metrics_text):
        """Test connection to a specific backend"""
        import socket
        
        status_label.config(text="● Status: Testing...")
        self.update()
        
        try:
            # Simple TCP connection test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((backend['host'], backend['port']))
            sock.close()
            
            if result == 0:
                status_label.config(
                    text="🟢 Status: Connected",
                    foreground='#16a34a'
                )
                
                # Show basic metrics
                metrics_text.config(state=tk.NORMAL)
                metrics_text.delete(1.0, tk.END)
                metrics_text.insert(tk.END, f"✅ Connection successful\n")
                metrics_text.insert(tk.END, f"Host: {backend['host']}\n")
                metrics_text.insert(tk.END, f"Port: {backend['port']}\n")
                metrics_text.insert(tk.END, f"Type: {backend['type']}")
                metrics_text.config(state=tk.DISABLED)
                
                self.add_log("INFO", f"{backend['name']} connection successful")
            else:
                raise ConnectionError("Connection failed")
                
        except Exception as e:
            status_label.config(
                text="🔴 Status: Disconnected",
                foreground='#dc2626'
            )
            
            metrics_text.config(state=tk.NORMAL)
            metrics_text.delete(1.0, tk.END)
            metrics_text.insert(tk.END, f"❌ Connection failed\n")
            metrics_text.insert(tk.END, f"Error: {str(e)}")
            metrics_text.config(state=tk.DISABLED)
            
            self.add_log("ERROR", f"{backend['name']} connection failed: {e}")
    
    def _refresh_backend_metrics(self, backend, status_label, metrics_text):
        """Refresh metrics for a specific backend"""
        self._test_backend_connection(backend, status_label, metrics_text)
    
    def _test_all_backends(self, cards_frame):
        """Test all backend connections"""
        self.add_log("INFO", "Testing all backend connections...")
        # This would trigger all test buttons
        # For now, just log the action
    
    def _show_full_metrics(self):
        """Show full metrics dashboard"""
        self.add_log("INFO", "Opening full metrics dashboard")
        self.show_info("Metrics", "Full metrics dashboard not yet implemented")
    
    def show_audit_log(self):
        """Show audit log"""
        self.add_log("INFO", "Viewing audit log")
        self.show_info("Audit Log", "Audit log viewer not yet implemented")
    
    def show_alerts(self):
        """Show system alerts"""
        self.add_log("INFO", "Viewing system alerts")
        self.show_info("Alerts", "Alert management not yet implemented")


def main():
    """Main entry point"""
    app = AdminFrontend()
    app.mainloop()


if __name__ == "__main__":
    main()
