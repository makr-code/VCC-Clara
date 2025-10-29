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
import psutil
from collections import deque

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.shared.components.base_window import BaseWindow
from frontend.shared.api.training_client import TrainingAPIClient
from frontend.shared.api.dataset_client import DatasetAPIClient
import threading
import time

# Matplotlib imports for real-time charts
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


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
        
        # Setup feature-specific keyboard shortcuts
        self._setup_admin_shortcuts()
    
    def _setup_admin_shortcuts(self):
        """Setup Admin Frontend specific keyboard shortcuts"""
        # Start all services: Ctrl+Shift+S
        self.bind('<Control-Shift-S>', lambda e: self.start_all_services())
        
        # Stop all services: Ctrl+Shift+X
        self.bind('<Control-Shift-X>', lambda e: self.stop_all_services())
        
        # Restart all services: Ctrl+Shift+R
        self.bind('<Control-Shift-R>', lambda e: self.restart_all_services())
        
        # Database management: Ctrl+D
        self.bind('<Control-d>', lambda e: self.show_database())
        
        # Configuration: Ctrl+Shift+C
        self.bind('<Control-Shift-C>', lambda e: self.show_configuration())
    
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
        """Show real-time system metrics dashboard with live charts"""
        if not MATPLOTLIB_AVAILABLE:
            self.show_error("Matplotlib Required", 
                          "Please install matplotlib: pip install matplotlib")
            return
        
        # Create window
        window = tk.Toplevel(self)
        window.title("Real-Time System Metrics Dashboard")
        window.geometry("1400x900")
        
        # Main container
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(
            main_frame,
            text="📊 Real-Time System Metrics",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=(0, 10))
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Refresh interval
        ttk.Label(control_frame, text="Refresh Interval:").pack(side=tk.LEFT, padx=(0, 5))
        interval_var = tk.StringVar(value="2")
        interval_combo = ttk.Combobox(
            control_frame,
            textvariable=interval_var,
            values=["1", "2", "5", "10"],
            width=5,
            state="readonly"
        )
        interval_combo.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(control_frame, text="seconds").pack(side=tk.LEFT, padx=(0, 20))
        
        # Auto-refresh toggle
        auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(
            control_frame,
            text="Auto-Refresh",
            variable=auto_refresh_var
        )
        auto_refresh_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # Manual refresh button
        refresh_btn = ttk.Button(
            control_frame,
            text="🔄 Refresh Now",
            command=lambda: update_metrics()
        )
        refresh_btn.pack(side=tk.LEFT)
        
        # Data storage (keep last 60 data points)
        max_points = 60
        time_data = deque(maxlen=max_points)
        cpu_data = deque(maxlen=max_points)
        memory_data = deque(maxlen=max_points)
        disk_read_data = deque(maxlen=max_points)
        disk_write_data = deque(maxlen=max_points)
        
        # Create figure with 4 subplots
        fig = Figure(figsize=(14, 8), dpi=80)
        
        # CPU subplot
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.set_title('CPU Usage (%)', fontweight='bold')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Usage (%)')
        ax1.set_ylim(0, 100)
        ax1.grid(True, alpha=0.3)
        line1, = ax1.plot([], [], 'b-', linewidth=2, label='CPU')
        ax1.legend()
        
        # Memory subplot
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.set_title('Memory Usage (%)', fontweight='bold')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Usage (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        line2, = ax2.plot([], [], 'g-', linewidth=2, label='Memory')
        ax2.legend()
        
        # Disk I/O subplot
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.set_title('Disk I/O (MB/s)', fontweight='bold')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('MB/s')
        ax3.grid(True, alpha=0.3)
        line3, = ax3.plot([], [], 'r-', linewidth=2, label='Read')
        line4, = ax3.plot([], [], 'orange', linewidth=2, label='Write')
        ax3.legend()
        
        # System info subplot (text-based)
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.axis('off')
        info_text = ax4.text(0.05, 0.95, '', verticalalignment='top', 
                            fontfamily='monospace', fontsize=10)
        
        fig.tight_layout(pad=2.0)
        
        # Embed figure in tkinter
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Track last disk I/O for delta calculation
        last_disk_io = {'read': 0, 'write': 0, 'time': time.time()}
        
        def update_metrics():
            """Update all metrics and charts"""
            try:
                current_time = time.time()
                
                # Get CPU and Memory
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                # Get Disk I/O
                disk_io = psutil.disk_io_counters()
                time_delta = current_time - last_disk_io['time']
                
                if time_delta > 0:
                    read_mb_s = (disk_io.read_bytes - last_disk_io['read']) / (1024 * 1024) / time_delta
                    write_mb_s = (disk_io.write_bytes - last_disk_io['write']) / (1024 * 1024) / time_delta
                else:
                    read_mb_s = 0
                    write_mb_s = 0
                
                last_disk_io['read'] = disk_io.read_bytes
                last_disk_io['write'] = disk_io.write_bytes
                last_disk_io['time'] = current_time
                
                # Append data
                time_data.append(len(time_data))
                cpu_data.append(cpu_percent)
                memory_data.append(memory.percent)
                disk_read_data.append(max(0, read_mb_s))
                disk_write_data.append(max(0, write_mb_s))
                
                # Update CPU chart
                line1.set_data(list(time_data), list(cpu_data))
                ax1.set_xlim(max(0, len(time_data) - max_points), len(time_data))
                
                # Update Memory chart
                line2.set_data(list(time_data), list(memory_data))
                ax2.set_xlim(max(0, len(time_data) - max_points), len(time_data))
                
                # Update Disk I/O chart
                line3.set_data(list(time_data), list(disk_read_data))
                line4.set_data(list(time_data), list(disk_write_data))
                ax3.set_xlim(max(0, len(time_data) - max_points), len(time_data))
                max_io = max(max(disk_read_data, default=10), max(disk_write_data, default=10))
                ax3.set_ylim(0, max_io * 1.2)
                
                # Update system info text
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                disk_usage = psutil.disk_usage('/')
                net_io = psutil.net_io_counters()
                
                info_str = f"""SYSTEM INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CPU:
  Cores: {cpu_count} ({psutil.cpu_count(logical=False)} physical)
  Frequency: {cpu_freq.current:.0f} MHz
  Usage: {cpu_percent:.1f}%

MEMORY:
  Total: {memory.total / (1024**3):.1f} GB
  Used: {memory.used / (1024**3):.1f} GB
  Available: {memory.available / (1024**3):.1f} GB
  Usage: {memory.percent:.1f}%

DISK:
  Total: {disk_usage.total / (1024**3):.1f} GB
  Used: {disk_usage.used / (1024**3):.1f} GB
  Free: {disk_usage.free / (1024**3):.1f} GB
  Usage: {disk_usage.percent:.1f}%

NETWORK:
  Sent: {net_io.bytes_sent / (1024**3):.2f} GB
  Received: {net_io.bytes_recv / (1024**3):.2f} GB
  Packets Sent: {net_io.packets_sent:,}
  Packets Recv: {net_io.packets_recv:,}
"""
                info_text.set_text(info_str)
                
                # Redraw canvas
                canvas.draw()
                
            except Exception as e:
                print(f"Error updating metrics: {e}")
        
        def auto_refresh_loop():
            """Auto-refresh loop running in background"""
            while window.winfo_exists():
                if auto_refresh_var.get():
                    try:
                        update_metrics()
                    except Exception as e:
                        print(f"Auto-refresh error: {e}")
                
                try:
                    interval = float(interval_var.get())
                except:
                    interval = 2.0
                
                time.sleep(interval)
        
        # Initial update
        update_metrics()
        
        # Start auto-refresh thread
        refresh_thread = threading.Thread(target=auto_refresh_loop, daemon=True)
        refresh_thread.start()
        
        # Close button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="Close",
            command=window.destroy
        ).pack(side=tk.RIGHT)
    
    def show_system_logs(self):
        """Show enhanced system logs dialog with filtering"""
        # Create window
        window = tk.Toplevel(self)
        window.title("System Logs - Enhanced Viewer")
        window.geometry("1000x700")
        
        # Main container
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(
            main_frame,
            text="📋 System Logs",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=(0, 15))
        
        # Filter controls
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Level filter
        level_frame = ttk.Frame(filter_frame)
        level_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(level_frame, text="Level:").pack(side=tk.LEFT, padx=(0, 5))
        
        level_var = tk.StringVar(value="ALL")
        levels = ["ALL", "INFO", "WARNING", "ERROR", "DEBUG"]
        level_combo = ttk.Combobox(
            level_frame,
            textvariable=level_var,
            values=levels,
            width=12,
            state='readonly'
        )
        level_combo.pack(side=tk.LEFT)
        
        # Search filter
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT)
        
        # Auto-scroll checkbox
        autoscroll_var = tk.BooleanVar(value=True)
        autoscroll_cb = ttk.Checkbutton(
            filter_frame,
            text="Auto-scroll",
            variable=autoscroll_var
        )
        autoscroll_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # Action buttons
        ttk.Button(
            filter_frame,
            text="🔄 Refresh",
            command=lambda: update_log_view()
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            filter_frame,
            text="💾 Export",
            command=lambda: export_logs()
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            filter_frame,
            text="🗑️ Clear",
            command=lambda: clear_logs()
        ).pack(side=tk.RIGHT)
        
        # Log viewer
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        log_scroll_y = ttk.Scrollbar(log_frame)
        log_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        log_scroll_x = ttk.Scrollbar(log_frame, orient=tk.HORIZONTAL)
        log_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Text widget with colors
        log_text = tk.Text(
            log_frame,
            wrap=tk.NONE,
            font=("Consolas", 9),
            yscrollcommand=log_scroll_y.set,
            xscrollcommand=log_scroll_x.set
        )
        log_text.pack(fill=tk.BOTH, expand=True)
        
        log_scroll_y.config(command=log_text.yview)
        log_scroll_x.config(command=log_text.xview)
        
        # Configure tags for log levels
        log_text.tag_config("INFO", foreground="#2196F3")
        log_text.tag_config("WARNING", foreground="#FF9800")
        log_text.tag_config("ERROR", foreground="#F44336", font=("Consolas", 9, "bold"))
        log_text.tag_config("DEBUG", foreground="#9E9E9E")
        log_text.tag_config("TIMESTAMP", foreground="#666666")
        
        def update_log_view():
            """Update log view with filters applied"""
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            
            # Get log content from main log viewer
            if hasattr(self, 'log_viewer'):
                all_logs = self.log_viewer.get(1.0, tk.END).strip().split('\n')
            else:
                all_logs = []
            
            # Apply filters
            level_filter = level_var.get()
            search_filter = search_var.get().lower()
            
            filtered_count = 0
            for log_line in all_logs:
                if not log_line.strip():
                    continue
                
                # Level filter
                if level_filter != "ALL":
                    if f"[{level_filter}]" not in log_line:
                        continue
                
                # Search filter
                if search_filter and search_filter not in log_line.lower():
                    continue
                
                # Determine log level for coloring
                level_tag = "INFO"
                if "[ERROR]" in log_line:
                    level_tag = "ERROR"
                elif "[WARNING]" in log_line:
                    level_tag = "WARNING"
                elif "[DEBUG]" in log_line:
                    level_tag = "DEBUG"
                
                # Insert with color
                log_text.insert(tk.END, log_line + "\n", level_tag)
                filtered_count += 1
            
            log_text.config(state=tk.DISABLED)
            
            # Auto-scroll to bottom
            if autoscroll_var.get():
                log_text.see(tk.END)
            
            # Update status
            status_label.config(
                text=f"Showing {filtered_count} logs (Level: {level_filter}, Search: '{search_filter or 'none'}')"
            )
        
        def export_logs():
            """Export filtered logs to file"""
            from tkinter import filedialog
            from datetime import datetime
            
            filename = filedialog.asksaveasfilename(
                parent=window,
                title="Export Logs",
                defaultextension=".log",
                initialfile=f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                try:
                    content = log_text.get(1.0, tk.END)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    messagebox.showinfo("Export Success", f"Logs exported to:\n{filename}", parent=window)
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export logs:\n{e}", parent=window)
        
        def clear_logs():
            """Clear all logs"""
            if messagebox.askyesno("Confirm", "Clear all system logs?", parent=window):
                log_text.config(state=tk.NORMAL)
                log_text.delete(1.0, tk.END)
                log_text.config(state=tk.DISABLED)
                if hasattr(self, 'log_viewer'):
                    self.log_viewer.delete(1.0, tk.END)
                status_label.config(text="Logs cleared")
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        status_label = ttk.Label(
            status_frame,
            text="Loading logs...",
            font=("Helvetica", 9),
            foreground="#666666"
        )
        status_label.pack(side=tk.LEFT)
        
        # Close button
        ttk.Button(
            status_frame,
            text="❌ Close",
            command=window.destroy
        ).pack(side=tk.RIGHT)
        
        # Bind filter updates
        level_combo.bind('<<ComboboxSelected>>', lambda e: update_log_view())
        search_entry.bind('<KeyRelease>', lambda e: update_log_view())
        
        # Initial load
        update_log_view()
    
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
        
        # Search bar
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=25)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
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
        
        def populate_file_tree():
            """Populate file tree with optional search filter"""
            file_tree.delete(*file_tree.get_children())
            search_term = search_var.get().lower()
            
            # Populate file tree
            for dir_name, dir_path in config_dirs:
                full_path = Path(project_root) / dir_path
                if full_path.exists():
                    parent = file_tree.insert('', tk.END, text=f"📁 {dir_name}", values=('Folder', ''))
                    
                    has_children = False
                    # Add config files
                    for config_file in sorted(full_path.rglob('*.yaml')) + sorted(full_path.rglob('*.yml')) + sorted(full_path.rglob('*.json')):
                        if config_file.is_file():
                            # Apply search filter
                            if search_term and search_term not in config_file.name.lower():
                                continue
                            
                            has_children = True
                            size_kb = config_file.stat().st_size / 1024
                            file_type = config_file.suffix.upper()[1:]
                            
                            file_tree.insert(
                                parent,
                                tk.END,
                                text=f"📄 {config_file.name}",
                                values=(file_type, f"{size_kb:.1f} KB"),
                                tags=(str(config_file),)
                            )
                    
                    # Remove empty folders when searching
                    if search_term and not has_children:
                        file_tree.delete(parent)
        
        # Initial population
        populate_file_tree()
        
        # Bind search
        search_entry.bind('<KeyRelease>', lambda e: populate_file_tree())
        
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
        """Show audit log viewer"""
        self.add_log("INFO", "Opening Audit Log Viewer")
        
        # Create window
        window = tk.Toplevel(self)
        window.title("Audit Log - User Actions Tracking")
        window.geometry("1100x700")
        
        # Main container
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(
            main_frame,
            text="🔍 Audit Log",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=(0, 15))
        
        # Filter controls
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Action type filter
        action_frame = ttk.Frame(filter_frame)
        action_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(action_frame, text="Action:").pack(side=tk.LEFT, padx=(0, 5))
        
        action_var = tk.StringVar(value="ALL")
        actions = ["ALL", "CREATE", "UPDATE", "DELETE", "EXPORT", "LOGIN", "LOGOUT", "CONFIG_CHANGE"]
        action_combo = ttk.Combobox(
            action_frame,
            textvariable=action_var,
            values=actions,
            width=15,
            state='readonly'
        )
        action_combo.pack(side=tk.LEFT)
        
        # User filter
        user_frame = ttk.Frame(filter_frame)
        user_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(user_frame, text="User:").pack(side=tk.LEFT, padx=(0, 5))
        
        user_var = tk.StringVar()
        user_entry = ttk.Entry(user_frame, textvariable=user_var, width=20)
        user_entry.pack(side=tk.LEFT)
        
        # Refresh button
        ttk.Button(
            filter_frame,
            text="🔄 Refresh",
            command=lambda: load_audit_logs()
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            filter_frame,
            text="💾 Export",
            command=lambda: export_audit_logs()
        ).pack(side=tk.RIGHT)
        
        # Audit log table
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        table_scroll_y = ttk.Scrollbar(table_frame)
        table_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        table_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        table_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns = ('timestamp', 'user', 'action', 'resource', 'details', 'ip_address')
        audit_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=table_scroll_y.set,
            xscrollcommand=table_scroll_x.set
        )
        
        # Configure columns
        audit_tree.heading('timestamp', text='Timestamp')
        audit_tree.heading('user', text='User')
        audit_tree.heading('action', text='Action')
        audit_tree.heading('resource', text='Resource')
        audit_tree.heading('details', text='Details')
        audit_tree.heading('ip_address', text='IP Address')
        
        audit_tree.column('timestamp', width=150)
        audit_tree.column('user', width=100)
        audit_tree.column('action', width=100)
        audit_tree.column('resource', width=150)
        audit_tree.column('details', width=300)
        audit_tree.column('ip_address', width=120)
        
        audit_tree.pack(fill=tk.BOTH, expand=True)
        
        table_scroll_y.config(command=audit_tree.yview)
        table_scroll_x.config(command=audit_tree.xview)
        
        # Make sortable
        self.make_treeview_sortable(audit_tree)
        
        def load_audit_logs():
            """Load audit logs from file"""
            from pathlib import Path
            import json
            from datetime import datetime
            
            # Clear existing
            for item in audit_tree.get_children():
                audit_tree.delete(item)
            
            # Load from audit/audit_log.jsonl
            audit_file = Path("audit/audit_log.jsonl")
            
            if not audit_file.exists():
                status_label.config(text="No audit log file found")
                return
            
            # Apply filters
            action_filter = action_var.get()
            user_filter = user_var.get().lower()
            
            count = 0
            try:
                with open(audit_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            entry = json.loads(line)
                            
                            # Apply filters
                            if action_filter != "ALL" and entry.get('action', '').upper() != action_filter:
                                continue
                            
                            if user_filter and user_filter not in entry.get('user', '').lower():
                                continue
                            
                            # Insert into tree
                            audit_tree.insert('', tk.END, values=(
                                entry.get('timestamp', 'N/A'),
                                entry.get('user', 'system'),
                                entry.get('action', 'UNKNOWN'),
                                entry.get('resource', 'N/A'),
                                entry.get('details', ''),
                                entry.get('ip_address', 'N/A')
                            ))
                            count += 1
                            
                        except json.JSONDecodeError:
                            continue
                
                status_label.config(text=f"Loaded {count} audit log entries")
                
            except Exception as e:
                status_label.config(text=f"Error loading audit log: {e}")
        
        def export_audit_logs():
            """Export filtered audit logs"""
            from tkinter import filedialog
            from datetime import datetime
            
            filename = filedialog.asksaveasfilename(
                parent=window,
                title="Export Audit Log",
                defaultextension=".csv",
                initialfile=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filename:
                return
            
            try:
                import csv
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Header
                    writer.writerow(['Timestamp', 'User', 'Action', 'Resource', 'Details', 'IP Address'])
                    
                    # Data
                    for item in audit_tree.get_children():
                        values = audit_tree.item(item, 'values')
                        writer.writerow(values)
                
                messagebox.showinfo("Export Success", f"Audit log exported to:\n{filename}", parent=window)
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export audit log:\n{e}", parent=window)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        status_label = ttk.Label(
            status_frame,
            text="Loading audit logs...",
            font=("Helvetica", 9),
            foreground="#666666"
        )
        status_label.pack(side=tk.LEFT)
        
        ttk.Button(
            status_frame,
            text="❌ Close",
            command=window.destroy
        ).pack(side=tk.RIGHT)
        
        # Bind filter updates
        action_combo.bind('<<ComboboxSelected>>', lambda e: load_audit_logs())
        user_entry.bind('<KeyRelease>', lambda e: load_audit_logs())
        
        # Initial load
        load_audit_logs()
    
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
