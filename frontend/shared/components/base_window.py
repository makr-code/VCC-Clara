"""
Base Window Component

Abstract base class for all tkinter windows with standard UI components.
Provides MenuBar, ToolBar, StatusBar, and Sidebar infrastructure.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Callable
from datetime import datetime


class BaseWindow(tk.Tk, ABC):
    """
    Abstract Base Window for Clara Frontend Applications
    
    Features:
    - Menu Bar with standard menus
    - Tool Bar with icon buttons
    - Status Bar with connection status
    - Left Sidebar for navigation
    - Main content area
    - Standard styling and theming
    
    Subclasses must implement:
    - setup_toolbar_actions()
    - setup_sidebar_content()
    - setup_main_content()
    """
    
    # VCC Corporate Identity Colors
    COLORS = {
        'primary': '#0066CC',      # VCC Blue
        'secondary': '#004499',    # Dark Blue
        'success': '#28A745',      # Green
        'warning': '#FFC107',      # Yellow
        'danger': '#DC3545',       # Red
        'background': '#F5F5F5',   # Light Gray
        'sidebar': '#2C3E50',      # Dark Gray
        'text': '#212529',         # Almost Black
        'text_light': '#FFFFFF',   # White
        'border': '#DEE2E6'        # Border Gray
    }
    
    def __init__(self, title: str, width: int = 1200, height: int = 800):
        """
        Initialize Base Window
        
        Args:
            title: Window title
            width: Window width in pixels
            height: Window height in pixels
        """
        super().__init__()
        
        self.title(f"Clara AI - {title}")
        self.geometry(f"{width}x{height}")
        
        # Center window on screen
        self.center_window(width, height)
        
        # Window state
        self.connection_status = "Disconnected"
        self.status_message = "Ready"
        
        # Setup UI components
        self._setup_styles()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_main_container()
        self._create_status_bar()
        
        # Allow subclasses to populate content
        self.setup_toolbar_actions()
        self.setup_sidebar_content()
        self.setup_main_content()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def center_window(self, width: int, height: int):
        """Center window on screen"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button styles
        style.configure(
            'Primary.TButton',
            background=self.COLORS['primary'],
            foreground=self.COLORS['text_light'],
            borderwidth=0,
            focuscolor='none',
            padding=10
        )
        
        style.configure(
            'Secondary.TButton',
            background=self.COLORS['secondary'],
            foreground=self.COLORS['text_light'],
            borderwidth=0,
            focuscolor='none',
            padding=10
        )
        
        # Frame styles
        style.configure('Sidebar.TFrame', background=self.COLORS['sidebar'])
        style.configure('Toolbar.TFrame', background='white', relief='raised')
    
    def _create_menu_bar(self):
        """Create standard menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_view)
        view_menu.add_command(label="Toggle Sidebar", command=self.toggle_sidebar)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="API Documentation", command=self.open_api_docs)
        tools_menu.add_command(label="System Health", command=self.show_system_health)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        
        self.menubar = menubar
    
    def _create_toolbar(self):
        """Create toolbar frame (populated by subclass)"""
        self.toolbar = ttk.Frame(self, style='Toolbar.TFrame', height=50)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.toolbar.pack_propagate(False)
        
        # Toolbar title/icon area (left)
        self.toolbar_left = ttk.Frame(self.toolbar)
        self.toolbar_left.pack(side=tk.LEFT, fill=tk.Y)
        
        # Toolbar actions area (right)
        self.toolbar_right = ttk.Frame(self.toolbar)
        self.toolbar_right.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_main_container(self):
        """Create main container with sidebar and content area"""
        self.main_container = ttk.Frame(self)
        self.main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Left Sidebar
        self.sidebar = ttk.Frame(
            self.main_container,
            style='Sidebar.TFrame',
            width=250
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # Sidebar header
        sidebar_header = tk.Frame(
            self.sidebar,
            bg=self.COLORS['primary'],
            height=60
        )
        sidebar_header.pack(side=tk.TOP, fill=tk.X)
        sidebar_header.pack_propagate(False)
        
        tk.Label(
            sidebar_header,
            text="CLARA AI",
            font=('Segoe UI', 18, 'bold'),
            fg=self.COLORS['text_light'],
            bg=self.COLORS['primary']
        ).pack(pady=15)
        
        # Sidebar content (populated by subclass)
        self.sidebar_content = tk.Frame(
            self.sidebar,
            bg=self.COLORS['sidebar']
        )
        self.sidebar_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Main Content Area
        self.content_area = ttk.Frame(self.main_container)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = tk.Frame(
            self,
            bg=self.COLORS['sidebar'],
            height=30
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)
        
        # Status message (left)
        self.status_label = tk.Label(
            self.status_bar,
            text=self.status_message,
            bg=self.COLORS['sidebar'],
            fg=self.COLORS['text_light'],
            anchor=tk.W,
            padx=10
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Connection status (right)
        self.connection_label = tk.Label(
            self.status_bar,
            text=f"🔴 {self.connection_status}",
            bg=self.COLORS['sidebar'],
            fg=self.COLORS['text_light'],
            anchor=tk.E,
            padx=10
        )
        self.connection_label.pack(side=tk.RIGHT)
    
    def add_sidebar_button(
        self,
        text: str,
        command: Callable,
        icon: str = "▶"
    ) -> tk.Button:
        """
        Add navigation button to sidebar
        
        Args:
            text: Button text
            command: Click handler
            icon: Unicode icon
            
        Returns:
            Created button widget
        """
        btn = tk.Button(
            self.sidebar_content,
            text=f"{icon}  {text}",
            font=('Segoe UI', 11),
            bg=self.COLORS['sidebar'],
            fg=self.COLORS['text_light'],
            activebackground=self.COLORS['primary'],
            activeforeground=self.COLORS['text_light'],
            relief=tk.FLAT,
            anchor=tk.W,
            padx=20,
            pady=12,
            cursor='hand2',
            command=command
        )
        btn.pack(fill=tk.X, pady=2)
        
        # Hover effect
        def on_enter(e):
            btn.config(bg=self.COLORS['primary'])
        def on_leave(e):
            btn.config(bg=self.COLORS['sidebar'])
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def add_toolbar_button(
        self,
        text: str,
        command: Callable,
        icon: str = "▶",
        side: str = "right"
    ) -> tk.Button:
        """
        Add button to toolbar
        
        Args:
            text: Button text
            command: Click handler
            icon: Unicode icon
            side: 'left' or 'right'
            
        Returns:
            Created button widget
        """
        parent = self.toolbar_left if side == "left" else self.toolbar_right
        
        btn = tk.Button(
            parent,
            text=f"{icon} {text}",
            font=('Segoe UI', 10),
            bg=self.COLORS['primary'],
            fg=self.COLORS['text_light'],
            activebackground=self.COLORS['secondary'],
            activeforeground=self.COLORS['text_light'],
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2',
            command=command
        )
        btn.pack(side=tk.LEFT, padx=5)
        
        return btn
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_message = message
        self.status_label.config(text=message)
        self.update_idletasks()
    
    def update_connection_status(self, status: str, connected: bool = False):
        """
        Update connection status indicator
        
        Args:
            status: Status text
            connected: Connection state
        """
        self.connection_status = status
        icon = "🟢" if connected else "🔴"
        self.connection_label.config(text=f"{icon} {status}")
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.sidebar.winfo_ismapped():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y, before=self.content_area)
    
    def show_info(self, title: str, message: str):
        """Show info message box"""
        messagebox.showinfo(title, message, parent=self)
    
    def show_warning(self, title: str, message: str):
        """Show warning message box"""
        messagebox.showwarning(title, message, parent=self)
    
    def show_error(self, title: str, message: str):
        """Show error message box"""
        messagebox.showerror(title, message, parent=self)
    
    def confirm(self, title: str, message: str) -> bool:
        """Show confirmation dialog"""
        return messagebox.askyesno(title, message, parent=self)
    
    # Abstract methods (must be implemented by subclasses)
    
    @abstractmethod
    def setup_toolbar_actions(self):
        """Setup toolbar buttons and actions"""
        pass
    
    @abstractmethod
    def setup_sidebar_content(self):
        """Setup sidebar navigation"""
        pass
    
    @abstractmethod
    def setup_main_content(self):
        """Setup main content area"""
        pass
    
    # Standard menu actions (can be overridden)
    
    def show_settings(self):
        """Show settings dialog"""
        self.show_info("Settings", "Settings dialog not implemented yet")
    
    def refresh_view(self):
        """Refresh current view"""
        self.update_status("Refreshing...")
        # Subclass should override
        self.update_status("Ready")
    
    def open_api_docs(self):
        """Open API documentation in browser"""
        import webbrowser
        webbrowser.open("http://localhost:45680/docs")
    
    def show_system_health(self):
        """Show system health dialog"""
        self.show_info("System Health", "Health check not implemented yet")
    
    def show_help(self):
        """Show help documentation"""
        self.show_info("Help", "Documentation available in /docs folder")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Clara AI System v2.0
        
        Clean Architecture Microservices
        
        • Training Backend (Port 45680)
        • Dataset Backend (Port 45681)
        • Modern tkinter UI
        
        © 2025 VCC Clara Development Team
        """
        self.show_info("About Clara AI", about_text)
    
    def on_closing(self):
        """Handle window close event"""
        if self.confirm("Exit", "Are you sure you want to exit?"):
            self.quit()
            self.destroy()
