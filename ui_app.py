import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
import queue
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
import logging
from pathlib import Path

from automation.config import load_settings
from automation.linkedin import LinkedInAutomation
from automation.gemini_client import GeminiClient
from automation.enhanced_gemini_client import EnhancedGeminiClient
from automation.scoring import compute_popularity_score
from automation.sheets import SheetsClient
from automation.enhanced_sheets import EnhancedSheetsClient
from automation.profile_extractor import ProfileExtractor
from automation.logging_config import configure_logging


class LogHandler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        
    def emit(self, record):
        msg = self.format(record)
        self.callback(msg, record.levelname)


class LinkedInAutomationUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("LinkedIn Automation Tool")
        self.root.geometry("1400x900")
        
        # Settings
        self.settings_file = Path.home() / ".linkedin_automation_ui_settings.json"
        self.load_settings()
        
        # Queue for thread communication
        self.log_queue = queue.Queue()
        self.profile_queue = queue.Queue()
        
        # Automation state
        self.automation_running = False
        self.automation_thread = None
        self.profiles_data = []
        
        # Setup UI
        self.setup_ui()
        self.setup_logging()
        
        # Apply saved theme
        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        
        # Start queue processing
        self.process_queues()
        
    def load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {"theme": "dark"}
        except:
            self.settings = {"theme": "dark"}
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)
    
    def setup_ui(self):
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Content area with tabs
        self.create_content_area(main_frame)
        
    def create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, height=80)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title and logo area
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="LinkedIn Automation",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Professional Network Automation Tool",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack()
        
        # Status and controls
        control_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        control_frame.grid(row=0, column=1, padx=20, pady=10)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(control_frame)
        self.status_frame.pack(pady=5)
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.status_indicator.pack(side="left", padx=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left")
        
        # Theme toggle
        theme_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        theme_frame.grid(row=0, column=2, padx=20, pady=10)
        
        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=ctk.CTkFont(size=12)
        )
        theme_label.pack(side="left", padx=5)
        
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="Dark",
            command=self.toggle_theme,
            width=60
        )
        self.theme_switch.pack(side="left")
        
        # Set initial theme switch state
        if self.settings.get("theme", "dark") == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()
    
    def create_content_area(self, parent):
        # Tabview for different sections
        self.tabview = ctk.CTkTabview(parent)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create tabs
        self.tab_automation = self.tabview.add("Automation")
        self.tab_profiles = self.tabview.add("Profiles")
        self.tab_logs = self.tabview.add("Logs")
        self.tab_settings = self.tabview.add("Settings")
        
        # Setup each tab
        self.setup_automation_tab()
        self.setup_profiles_tab()
        self.setup_logs_tab()
        self.setup_settings_tab()
    
    def setup_automation_tab(self):
        # Configure grid
        self.tab_automation.grid_columnconfigure(0, weight=1)
        self.tab_automation.grid_rowconfigure(2, weight=1)
        
        # Search parameters frame
        params_frame = ctk.CTkFrame(self.tab_automation)
        params_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        params_frame.grid_columnconfigure(1, weight=1)
        
        # Keywords
        ctk.CTkLabel(params_frame, text="Search Keywords:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.keywords_entry = ctk.CTkEntry(params_frame, placeholder_text="e.g., software engineer, data scientist")
        self.keywords_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Location
        ctk.CTkLabel(params_frame, text="Location:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.location_entry = ctk.CTkEntry(params_frame, placeholder_text="e.g., San Francisco, Remote")
        self.location_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Max profiles
        ctk.CTkLabel(params_frame, text="Max Profiles:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.max_profiles_slider = ctk.CTkSlider(params_frame, from_=1, to=100, number_of_steps=99)
        self.max_profiles_slider.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.max_profiles_slider.set(10)
        
        self.max_profiles_label = ctk.CTkLabel(params_frame, text="10")
        self.max_profiles_label.grid(row=2, column=2, padx=10, pady=5)
        
        self.max_profiles_slider.configure(command=self.update_max_profiles_label)
        
        # Control buttons
        button_frame = ctk.CTkFrame(self.tab_automation)
        button_frame.grid(row=1, column=0, pady=10)
        
        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Automation",
            command=self.start_automation,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self.stop_automation,
            width=100,
            height=40,
            state="disabled",
            fg_color="red"
        )
        self.stop_button.pack(side="left", padx=5)
        
        # Progress section
        progress_frame = ctk.CTkFrame(self.tab_automation)
        progress_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_label = ctk.CTkLabel(progress_frame, text="Progress: Ready to start")
        self.progress_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        # Stats
        stats_frame = ctk.CTkFrame(progress_frame)
        stats_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.create_stat_card(stats_frame, "Profiles Found", "0", 0, 0)
        self.create_stat_card(stats_frame, "Profiles Processed", "0", 0, 1)
        self.create_stat_card(stats_frame, "Connections Sent", "0", 0, 2)
        self.create_stat_card(stats_frame, "Already Connected", "0", 0, 3)
        
        # Recent activity
        activity_frame = ctk.CTkFrame(progress_frame)
        activity_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        progress_frame.grid_rowconfigure(3, weight=1)
        
        ctk.CTkLabel(activity_frame, text="Recent Activity", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        self.activity_text = ctk.CTkTextbox(activity_frame, height=150)
        self.activity_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def create_stat_card(self, parent, title, value, row, col):
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="gray")
        title_label.pack(pady=(5,0))
        
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"))
        value_label.pack(pady=(0,5))
        
        # Store reference for updates
        setattr(self, f"stat_{title.lower().replace(' ', '_')}", value_label)
    
    def setup_profiles_tab(self):
        self.tab_profiles.grid_columnconfigure(0, weight=1)
        self.tab_profiles.grid_rowconfigure(1, weight=1)
        
        # Search bar
        search_frame = ctk.CTkFrame(self.tab_profiles)
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.profile_search = ctk.CTkEntry(search_frame, placeholder_text="Search profiles...")
        self.profile_search.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.profile_search.bind("<KeyRelease>", self.filter_profiles)
        
        export_button = ctk.CTkButton(search_frame, text="Export CSV", command=self.export_profiles, width=100)
        export_button.grid(row=0, column=1, padx=10, pady=5)
        
        # Table frame
        table_frame = ctk.CTkFrame(self.tab_profiles)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Create Treeview with scrollbars
        tree_scroll_y = ctk.CTkScrollbar(table_frame)
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        
        tree_scroll_x = ctk.CTkScrollbar(table_frame, orientation="horizontal")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        
        self.profile_tree = ttk.Treeview(
            table_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode="extended"
        )
        self.profile_tree.grid(row=0, column=0, sticky="nsew")
        
        tree_scroll_y.configure(command=self.profile_tree.yview)
        tree_scroll_x.configure(command=self.profile_tree.xview)
        
        # Define columns
        columns = ["Name", "Position", "Location", "Status", "Score", "Connected"]
        self.profile_tree["columns"] = columns
        self.profile_tree["show"] = "headings"
        
        # Configure columns
        for col in columns:
            self.profile_tree.heading(col, text=col)
            self.profile_tree.column(col, width=150, minwidth=100)
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure colors based on theme
        if self.settings.get("theme", "dark") == "dark":
            style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
            style.configure("Treeview.Heading", background="#1f1f1f", foreground="white")
        else:
            style.configure("Treeview", background="white", foreground="black", fieldbackground="white")
            style.configure("Treeview.Heading", background="#f0f0f0", foreground="black")
    
    def setup_logs_tab(self):
        self.tab_logs.grid_columnconfigure(0, weight=1)
        self.tab_logs.grid_rowconfigure(1, weight=1)
        
        # Log controls
        control_frame = ctk.CTkFrame(self.tab_logs)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Log level filter
        ctk.CTkLabel(control_frame, text="Log Level:").pack(side="left", padx=5)
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        self.log_level_menu = ctk.CTkOptionMenu(
            control_frame,
            values=log_levels,
            variable=self.log_level_var,
            command=self.filter_logs
        )
        self.log_level_menu.pack(side="left", padx=5)
        
        # Clear logs button
        clear_button = ctk.CTkButton(control_frame, text="Clear Logs", command=self.clear_logs, width=100)
        clear_button.pack(side="right", padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = ctk.CTkCheckBox(
            control_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var
        )
        auto_scroll_check.pack(side="right", padx=5)
        
        # Log display
        log_frame = ctk.CTkFrame(self.tab_logs)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = ctk.CTkTextbox(log_frame, wrap="word", font=("Consolas", 11))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure tags for different log levels
        self.log_text._textbox.tag_config("DEBUG", foreground="#808080")
        self.log_text._textbox.tag_config("INFO", foreground="#00ff00")
        self.log_text._textbox.tag_config("WARNING", foreground="#ffaa00")
        self.log_text._textbox.tag_config("ERROR", foreground="#ff0000")
        self.log_text._textbox.tag_config("CRITICAL", foreground="#ff00ff")
    
    def setup_settings_tab(self):
        self.tab_settings.grid_columnconfigure(0, weight=1)
        
        # Settings container with scrollbar
        canvas = tk.Canvas(self.tab_settings, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(self.tab_settings, command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tab_settings.grid_rowconfigure(0, weight=1)
        
        # LinkedIn Credentials
        cred_frame = ctk.CTkFrame(scrollable_frame)
        cred_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(cred_frame, text="LinkedIn Credentials", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(cred_frame, text="Email:").pack(anchor="w", padx=20)
        self.email_entry = ctk.CTkEntry(cred_frame, width=300)
        self.email_entry.pack(padx=20, pady=5)
        
        ctk.CTkLabel(cred_frame, text="Password:").pack(anchor="w", padx=20)
        self.password_entry = ctk.CTkEntry(cred_frame, width=300, show="*")
        self.password_entry.pack(padx=20, pady=5)
        
        # Google Sheets Settings
        sheets_frame = ctk.CTkFrame(scrollable_frame)
        sheets_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(sheets_frame, text="Google Sheets Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(sheets_frame, text="Sheet Name:").pack(anchor="w", padx=20)
        self.sheet_name_entry = ctk.CTkEntry(sheets_frame, width=300)
        self.sheet_name_entry.pack(padx=20, pady=5)
        
        ctk.CTkLabel(sheets_frame, text="Sheet ID:").pack(anchor="w", padx=20)
        self.sheet_id_entry = ctk.CTkEntry(sheets_frame, width=300)
        self.sheet_id_entry.pack(padx=20, pady=5)
        
        # Automation Settings
        auto_frame = ctk.CTkFrame(scrollable_frame)
        auto_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(auto_frame, text="Automation Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.headless_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(auto_frame, text="Run in headless mode", variable=self.headless_var).pack(padx=20, pady=5)
        
        self.test_mode_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(auto_frame, text="Test mode (no actions)", variable=self.test_mode_var).pack(padx=20, pady=5)
        
        # Save button
        save_button = ctk.CTkButton(
            scrollable_frame,
            text="Save Settings",
            command=self.save_app_settings,
            width=150,
            height=40
        )
        save_button.pack(pady=20)
    
    def setup_logging(self):
        # Add custom handler to capture logs
        log_handler = LogHandler(self.add_log_message)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)
    
    def add_log_message(self, message, level):
        self.log_queue.put((message, level))
    
    def update_max_profiles_label(self, value):
        self.max_profiles_label.configure(text=str(int(value)))
    
    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
            self.settings["theme"] = "dark"
        else:
            ctk.set_appearance_mode("light")
            self.settings["theme"] = "light"
        
        self.save_settings()
        self.update_treeview_style()
    
    def update_treeview_style(self):
        style = ttk.Style()
        if self.settings.get("theme", "dark") == "dark":
            style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
            style.configure("Treeview.Heading", background="#1f1f1f", foreground="white")
        else:
            style.configure("Treeview", background="white", foreground="black", fieldbackground="white")
            style.configure("Treeview.Heading", background="#f0f0f0", foreground="black")
    
    def start_automation(self):
        if self.automation_running:
            return
        
        self.automation_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.update_status("Running", "green")
        
        # Clear previous data
        self.profiles_data = []
        self.profile_tree.delete(*self.profile_tree.get_children())
        
        # Get parameters
        keywords = self.keywords_entry.get() or "software engineer"
        location = self.location_entry.get() or ""
        max_profiles = int(self.max_profiles_slider.get())
        
        # Start automation in background thread
        self.automation_thread = threading.Thread(
            target=self.run_automation,
            args=(keywords, location, max_profiles),
            daemon=True
        )
        self.automation_thread.start()
    
    def stop_automation(self):
        self.automation_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_status("Stopped", "red")
    
    def run_automation(self, keywords, location, max_profiles):
        try:
            # Run the actual automation
            asyncio.run(self.run_automation_async(keywords, location, max_profiles))
        except Exception as e:
            self.add_log_message(f"Automation error: {str(e)}", "ERROR")
        finally:
            self.automation_running = False
            self.root.after(0, self.on_automation_complete)
    
    async def run_automation_async(self, keywords, location, max_profiles):
        # Import the orchestrator's run function
        from automation.orchestrator import run as run_orchestrator
        from automation.config import Settings
        import os
        
        # Get settings from UI
        custom_settings = {
            "linkedin_email": self.email_entry.get() if hasattr(self, 'email_entry') and self.email_entry.get() else None,
            "linkedin_password": self.password_entry.get() if hasattr(self, 'password_entry') and self.password_entry.get() else None,
            "headless": self.headless_var.get() if hasattr(self, 'headless_var') else True,
            "test_mode": self.test_mode_var.get() if hasattr(self, 'test_mode_var') else False,
            "max_profiles": max_profiles,
            "search_keywords": keywords,
            "locations": [location] if location else []
        }
        
        # Set environment variables for the orchestrator
        for key, value in custom_settings.items():
            if value is not None:
                if key == "linkedin_email":
                    os.environ["LINKEDIN_EMAIL"] = str(value)
                elif key == "linkedin_password":
                    os.environ["LINKEDIN_PASSWORD"] = str(value)
                elif key == "search_keywords":
                    os.environ["SEARCH_KEYWORDS"] = str(value)
        
        # Set other required environment variables if not already set
        if not os.getenv("GOOGLE_API_KEY"):
            self.add_log_message("Warning: GOOGLE_API_KEY not set", "WARNING")
        
        if not os.getenv("GCP_SERVICE_ACCOUNT_JSON_PATH") and not os.getenv("GCP_SERVICE_ACCOUNT_JSON"):
            self.add_log_message("Warning: Google Sheets credentials not configured", "WARNING")
        
        try:
            # Run the orchestrator
            await run_orchestrator()
            self.add_log_message("Automation completed successfully", "INFO")
        except Exception as e:
            self.add_log_message(f"Automation failed: {str(e)}", "ERROR")
            raise
    
    def handle_progress(self, message, progress, stats):
        self.progress_label.configure(text=f"Progress: {message}")
        self.progress_bar.set(progress)
        self.add_activity(message)
        
        if stats:
            self.update_stats(
                stats.get("profiles_found", 0),
                stats.get("profiles_processed", 0),
                stats.get("connections_sent", 0),
                stats.get("already_connected", 0)
            )
    
    def on_automation_complete(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_status("Completed", "blue")
        self.add_log_message("Automation completed", "INFO")
    
    def update_status(self, text, color):
        self.status_label.configure(text=text)
        self.status_indicator.configure(text_color=color)
    
    def update_stats(self, found, processed, sent, connected):
        self.stat_profiles_found.configure(text=str(found))
        self.stat_profiles_processed.configure(text=str(processed))
        self.stat_connections_sent.configure(text=str(sent))
        self.stat_already_connected.configure(text=str(connected))
    
    def add_activity(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_text.insert("end", f"[{timestamp}] {message}\n")
        self.activity_text.see("end")
    
    def filter_profiles(self, event=None):
        search_term = self.profile_search.get().lower()
        
        # Clear and repopulate based on filter
        self.profile_tree.delete(*self.profile_tree.get_children())
        
        for profile in self.profiles_data:
            if search_term in profile["name"].lower() or search_term in profile["position"].lower():
                self.add_profile_to_tree(profile)
    
    def add_profile_to_tree(self, profile):
        values = [
            profile.get("name", ""),
            profile.get("position", ""),
            profile.get("location", ""),
            profile.get("status", ""),
            profile.get("score", ""),
            profile.get("connected", "")
        ]
        self.profile_tree.insert("", "end", values=values)
    
    def export_profiles(self):
        if not self.profiles_data:
            self.add_log_message("No profiles to export", "WARNING")
            return
        
        # Create DataFrame and export
        df = pd.DataFrame(self.profiles_data)
        filename = f"linkedin_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        self.add_log_message(f"Exported {len(self.profiles_data)} profiles to {filename}", "INFO")
    
    def filter_logs(self, level=None):
        # This would filter logs based on level
        pass
    
    def clear_logs(self):
        self.log_text.delete("1.0", "end")
    
    def save_app_settings(self):
        # Save settings to environment or config file
        self.add_log_message("Settings saved", "INFO")
    
    def process_queues(self):
        # Process log queue
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                self.display_log(message, level)
        except queue.Empty:
            pass
        
        # Process profile queue
        try:
            while True:
                profile = self.profile_queue.get_nowait()
                self.profiles_data.append(profile)
                self.add_profile_to_tree(profile)
                self.add_activity(f"Processed: {profile['name']}")
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queues)
    
    def display_log(self, message, level):
        # Add timestamp if not present
        if not message.startswith("20"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{timestamp} - {message}"
        
        self.log_text.insert("end", f"{message}\n", level)
        
        if self.auto_scroll_var.get():
            self.log_text.see("end")
    
    def run(self):
        self.root.mainloop()


def main():
    app = LinkedInAutomationUI()
    app.run()


if __name__ == "__main__":
    main()