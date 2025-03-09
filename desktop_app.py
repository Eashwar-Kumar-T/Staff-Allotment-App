import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry, Calendar
import pandas as pd
import json
from datetime import datetime, timedelta
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os
import traceback
from fpdf import FPDF
import calendar
from PIL import Image as PILImage

# Initialize the database files
if not os.path.exists('data'):
    os.makedirs('data')

DB_FILES = {
    'staff': 'data/staff.json',
    'classes': 'data/classes.json',
    'allotment': 'data/allotment.json',
    'settings': 'data/settings.json',
    'halls': 'data/halls.json'
}

# Initialize empty JSON files if they don't exist
for file_path in DB_FILES.values():
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)

class ConfigurationManager:
    def __init__(self):
        self.configurations = {}  # Start empty, don't load anything

    def load_configurations(self):
        """Load configurations from file"""
        try:
            if os.path.exists(DB_FILES['classes']):
                with open(DB_FILES['classes'], 'r') as f:
                    self.configurations = json.load(f)
        except Exception as e:
            print(f"Error loading configurations: {str(e)}")
            self.configurations = {}

    def save_configurations(self):
        """Save configurations to file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(DB_FILES['classes']), exist_ok=True)
            
            # Save configurations
            with open(DB_FILES['classes'], 'w') as f:
                json.dump(self.configurations, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving configurations: {str(e)}")
            return False

    def get_date_config(self, date):
        """Get configuration for a specific date"""
        return self.configurations.get(date, {
            'rooms': [],
            'settings': {
                'reporting_time': '',
                'assessment_name': '',
                'exam_time': '',
                'exam_details': ''
            }
        })

    def set_date_config(self, date, config):
        """Set configuration for a specific date"""
        self.configurations[date] = config
        return self.save_configurations()

    def get_all_dates(self):
        """Get list of all configured dates"""
        return sorted(self.configurations.keys())

    def clear_configurations(self):
        """Clear all configurations"""
        self.configurations = {}
        self.save_configurations()

    def validate_config(self, config):
        """Validate a configuration"""
        try:
            # Check basic structure
            if not isinstance(config, dict):
                return False, "Invalid configuration format"
            if 'rooms' not in config:
                return False, "Missing rooms configuration"
            if 'settings' not in config:
                return False, "Missing settings configuration"

            # Validate rooms
            for room in config['rooms']:
                if not all(key in room for key in ['room_no', 'girls_only', 'single_staff']):
                    return False, f"Invalid room configuration: {room}"

            # Validate settings
            required_settings = ['reporting_time', 'assessment_name', 'exam_time', 'exam_details']
            if not all(key in config['settings'] for key in required_settings):
                return False, "Missing required settings"

            return True, "Configuration is valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def get_configured_dates(self):
        """Get list of all configured dates"""
        return sorted(self.configurations.keys())

class DateSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, dates):
        super().__init__(parent)
        
        self.title("Select Dates")
        self.geometry("500x600")
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Store dates
        self.dates = dates
        self.selected_dates = []
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_label = ctk.CTkLabel(self, 
                               text="Select Dates for Configuration",
                               font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, pady=(20,10), padx=20, sticky="ew")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(self,
                                  text="Choose the dates to apply this configuration to:",
                                  font=ctk.CTkFont(size=16))
        subtitle_label.grid(row=1, column=0, pady=(0,20), padx=20, sticky="ew")
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,20))
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Create checkboxes for dates
        self.date_vars = {}
        for i, date in enumerate(sorted(self.dates)):
            frame = ctk.CTkFrame(scroll_frame)
            frame.grid(row=i, column=0, sticky="ew", pady=5)
            frame.grid_columnconfigure(0, weight=1)
            
            var = tk.BooleanVar()
            cb = ctk.CTkCheckBox(frame,
                             text=date,
                             variable=var,
                             font=ctk.CTkFont(size=14),
                             height=40,
                             checkbox_width=24,
                             checkbox_height=24)
            cb.grid(row=0, column=0, padx=10, sticky="w")
            self.date_vars[date] = var
            
        # Button frame
        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        # Select All button
        def select_all():
            select_all = not all(var.get() for var in self.date_vars.values())
            for var in self.date_vars.values():
                var.set(select_all)
                
        select_all_btn = ctk.CTkButton(btn_frame,
                                   text="Select All",
                                   command=select_all,
                                   font=ctk.CTkFont(size=14),
                                   width=120,
                                   height=40)
        select_all_btn.grid(row=0, column=0, padx=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(btn_frame,
                               text="Cancel",
                               command=self.cancel,
                               font=ctk.CTkFont(size=14),
                               width=120,
                               height=40,
                               fg_color="#FF5555",
                               hover_color="#FF3333")
        cancel_btn.grid(row=0, column=1, padx=10)
        
        # Apply button
        apply_btn = ctk.CTkButton(btn_frame,
                              text="Apply",
                              command=self.apply,
                              font=ctk.CTkFont(size=14),
                              width=120,
                              height=40,
                              fg_color="#00B056",
                              hover_color="#009048")
        apply_btn.grid(row=0, column=2, padx=10)
        
    def cancel(self):
        self.selected_dates = []
        self.destroy()
        
    def apply(self):
        self.selected_dates = [date for date, var in self.date_vars.items() if var.get()]
        if not self.selected_dates:
            messagebox.showerror("Error", "Please select at least one date")
            return
        self.destroy()

class ExamDutyApp:
    def __init__(self):
        """Initialize the application"""
        self.app = ctk.CTk()
        self.app.title("Staff Allotment")
        
        # Get screen dimensions
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        
        # Set window size to full screen
        self.app.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Optional: Start in zoomed/maximized state for Windows
        self.app.state('zoomed')
        
        # Define UI theme constants
        self.UI_THEME = {
            'header_bg': "#000000",
            'header_fg': "#ffffff",
            'content_bg': "#ffffff",
            'button_fg': "#000000",
            'button_bg': "#ffffff",
            'button_hover': "#f0f0f0",
            'button_border': "#000000",
            'error_red': "#FF5555",
            'success_green': "#00B056",
        }

        self.BUTTON_STYLE = {
            'width': 200,
            'height': 40,
            'corner_radius': 8,
            'font': ctk.CTkFont(family="Arial", size=14, weight="bold"),
            'fg_color': self.UI_THEME['button_bg'],
            'text_color': self.UI_THEME['button_fg'],
            'hover_color': self.UI_THEME['button_hover'],
            'border_color': self.UI_THEME['button_border'],
            'border_width': 2
        }
        
        # Initialize variables
        self.selected_dates = []
        self.current_date = None
        self.room_frames = {}
        self.reporting_time_var = tk.StringVar()
        self.assessment_name_var = tk.StringVar()
        self.exam_month_var = tk.StringVar()
        self.exam_details_var = tk.StringVar()
        
        # Configuration manager
        self.config_manager = ConfigurationManager()
        
        # Building and class configuration
        self.buildings = {
            'Cit-first floor': ['F1','F3', 'F4','F7', 'F8', 'F9','F22', 'F23'],
            'Cit-second floor': ['S1', 'S2', 'S3', 'S4', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12','S15', 'S16', 'S17', 'S18', 'S20', 'S21', 'S22', 'S23', 'S24', 'S26', 'S27'],
            'Cit-third floor': ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10',  'T12', 'T13', 'T14', 'T15', 'T16', 'T17', 'T18', 'T20', 'T21'],
            'Cit-MT': ['MT1', 'MT2', 'MT3', 'MT4', 'MT5', 'MT6', 'MT7', 'MT8'],
            'Cit-MS': ['MS1', 'MS2', 'MS3', 'MS4', 'MS5', 'MS6', 'MS7', 'MS8'],
            'Cit-DH': ['DH1', 'DH2', 'DH3', 'DH4', 'DH5', 'DH6', 'DH7', 'DH8', 'DH9', 'DH10'],
            'New Block B': ['101', '102', '202', '203', '204', '205'],
            'New Block C': ['301', '302', '303', '304', '305', '306', '307', '308', '402', 'A', 'B', 'C'],
            'New Block D': ['501', '502', '503', '504', '506', '507', '508', '509', '601', '602', '603', '604', '605', '606', '607', '608']
        }
        
        self.create_home_page()

    def create_home_page(self):
        # Clear existing widgets
        for widget in self.app.winfo_children():
            widget.destroy()

        # Configure the main window
        self.app.configure(fg_color="#ffffff")

        # Create main container with responsive padding
        main_container = ctk.CTkFrame(self.app, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=30)

        # Calculate responsive dimensions
        window_width = self.app.winfo_width()
        window_height = self.app.winfo_height()
        
        # Increased header height
        header_height = min(150, int(window_height * 0.22))  # Increased from 120 to 150
        
        # Increased logo size
        logo_size = min(100, int(header_height * 0.8))  # Increased from 80 to 100 and ratio from 0.7 to 0.8

        # Header Frame with logos - responsive height
        header_frame = ctk.CTkFrame(
            main_container, 
            fg_color="#000000", 
            corner_radius=15,
            height=header_height
        )
        header_frame.pack(fill="x", padx=20, pady=(0, int(window_height * 0.05)))

        # Create a frame for header content with grid layout
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", pady=20, padx=20)  # Increased padding
        header_content.grid_columnconfigure(1, weight=1)

        # Load and add left logo with responsive size
        try:
            left_logo = PILImage.open(r"assets\leftlogo.png")
            left_logo = left_logo.resize((logo_size, logo_size))
            left_logo_ctk = ctk.CTkImage(light_image=left_logo, size=(logo_size, logo_size))
            left_logo_label = ctk.CTkLabel(header_content, image=left_logo_ctk, text="")
            left_logo_label.grid(row=0, column=0, padx=(0, 30))  # Increased padding
        except Exception as e:
            print(f"Error loading left logo: {e}")

        # Title with larger responsive font size
        title_size = max(32, min(42, int(window_height * 0.06)))  # Increased minimum and maximum font sizes
        title = ctk.CTkLabel(
            header_content,
            text="STAFF ALLOTMENT SYSTEM",
            font=ctk.CTkFont(family="Arial", size=title_size, weight="bold"),
            text_color="#ffffff"
        )
        title.grid(row=0, column=1)

        # Load and add right logo with responsive size
        try:
            right_logo = PILImage.open(r"assets\rightlogo.png")
            right_logo = right_logo.resize((logo_size, logo_size))
            right_logo_ctk = ctk.CTkImage(light_image=right_logo, size=(logo_size, logo_size))
            right_logo_label = ctk.CTkLabel(header_content, image=right_logo_ctk, text="")
            right_logo_label.grid(row=0, column=2, padx=(30, 0))  # Increased padding
        except Exception as e:
            print(f"Error loading right logo: {e}")

        # Calculate responsive button dimensions - with minimum sizes to prevent too small buttons
        button_width = max(300, min(380, int(window_width * 0.25)))  # Minimum 300px, Maximum 380px
        button_height = max(150, min(180, int(window_height * 0.25)))  # Minimum 150px, Maximum 180px
        button_font_size = max(14, min(16, int(window_height * 0.023)))  # Minimum 14px
        icon_size = max(48, min(64, int(button_height * 0.4)))  # Minimum 48px

        # Content Frame with better spacing
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=40, pady=20)

        # Create a grid system for better button arrangement
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        # Button styles with responsive dimensions
        button_config = {
            "width": button_width,
            "height": button_height,
            "corner_radius": 15,
            "font": ctk.CTkFont(family="Arial", size=button_font_size, weight="bold"),
            "fg_color": "#ffffff",
            "hover_color": "#f0f0f0",
            "text_color": "#000000",
            "border_color": "#000000",
            "border_width": 2
        }

        # Load and resize button icons
        try:
            # Upload icon
            upload_image = PILImage.open(r"assets\upload staffs.png")
            upload_image = upload_image.resize((icon_size, icon_size))
            upload_image = ctk.CTkImage(light_image=upload_image, size=(icon_size, icon_size))

            # Staff icon
            staff_image = PILImage.open(r"assets\staff details.png")
            staff_image = staff_image.resize((icon_size, icon_size))
            staff_image = ctk.CTkImage(light_image=staff_image, size=(icon_size, icon_size))

            # Configure icon
            configure_image = PILImage.open(r"assets\configure class.png")
            configure_image = configure_image.resize((icon_size, icon_size))
            configure_image = ctk.CTkImage(light_image=configure_image, size=(icon_size, icon_size))

            # Allotment icon
            allotment_image = PILImage.open(r"assets\allotment.png")
            allotment_image = allotment_image.resize((icon_size, icon_size))
            allotment_image = ctk.CTkImage(light_image=allotment_image, size=(icon_size, icon_size))
        except Exception as e:
            upload_image = staff_image = configure_image = allotment_image = None
            print(f"Error loading button icons: {e}")

        # Create buttons using grid layout for better alignment
        upload_btn = ctk.CTkButton(
            content_frame,
            text="UPLOAD STAFF DETAILS",
            image=upload_image,
            command=self.show_upload_staff,
            compound="top",
            **button_config
        )
        upload_btn.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        staff_btn = ctk.CTkButton(
            content_frame,
            text="STAFF DETAILS",
            image=staff_image,
            command=self.show_staff_details,
            compound="top",
            **button_config
        )
        staff_btn.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        config_rooms_btn = ctk.CTkButton(
            content_frame,
            text="CONFIGURE ROOMS",
            image=configure_image,
            command=self.show_room_configuration,
            compound="top",
            **button_config
        )
        config_rooms_btn.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        allotment_btn = ctk.CTkButton(
            content_frame,
            text="GENERATE ALLOTMENT",
            image=allotment_image,
            command=self.select_dates,
            compound="top",
            **button_config
        )
        allotment_btn.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

        # Footer Frame
        footer_frame = ctk.CTkFrame(main_container, fg_color="#f5f5f5", corner_radius=10)
        footer_frame.pack(fill="x", padx=20, pady=(40, 0))
        
        # Version or copyright info
        footer_text = ctk.CTkLabel(
            footer_frame,
            text=" 2024 Staff Allotment System",
            font=ctk.CTkFont(family="Arial", size=12),
            text_color="#666666"
        )
        footer_text.pack(pady=10)

    def create_header(self, container, title_text):
        """Create consistent header with logos and title"""
        header_frame = ctk.CTkFrame(container, fg_color=self.UI_THEME['header_bg'], corner_radius=15)
        header_frame.pack(fill="x", padx=20, pady=(0, 40))
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", pady=15, padx=20)
        header_content.grid_columnconfigure(1, weight=1)

        # Left logo
        try:
            left_logo = PILImage.open(r"assets\leftlogo.png")
            left_logo = left_logo.resize((60, 60))
            left_logo_ctk = ctk.CTkImage(light_image=left_logo, size=(60, 60))
            left_logo_label = ctk.CTkLabel(header_content, image=left_logo_ctk, text="")
            left_logo_label.grid(row=0, column=0, padx=(0, 20))
        except Exception as e:
            print(f"Error loading left logo: {e}")

        # Title
        title = ctk.CTkLabel(
            header_content,
            text=title_text,
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color=self.UI_THEME['header_fg']
        )
        title.grid(row=0, column=1)

        # Right logo
        try:
            right_logo = PILImage.open(r"assets\right logo.png")
            right_logo = right_logo.resize((60, 60))
            right_logo_ctk = ctk.CTkImage(light_image=right_logo, size=(60, 60))
            right_logo_label = ctk.CTkLabel(header_content, image=right_logo_ctk, text="")
            right_logo_label.grid(row=0, column=2, padx=(20, 0))
        except Exception as e:
            print(f"Error loading right logo: {e}")

        return header_frame

    def show_upload_staff(self):
        # Clear existing widgets
        for widget in self.app.winfo_children():
            widget.destroy()

        # Create main container
        main_container = ctk.CTkFrame(self.app, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=30)

        # Add header
        self.create_header(main_container, "UPLOAD STAFF DETAILS")

        # Content Frame with border
        content_frame = ctk.CTkFrame(
            main_container, 
            fg_color=self.UI_THEME['content_bg'],
            corner_radius=15,
            border_width=2,
            border_color=self.UI_THEME['button_border']
        )
        content_frame.pack(fill="both", expand=True, padx=20)

        # Create a center frame for content
        center_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        center_frame.pack(expand=True, fill="both", padx=40, pady=40)

        # Upload icon - make it responsive
        try:
            upload_icon = PILImage.open(r"assets\upload here.png")
            icon_size = min(100, int(self.app.winfo_height() * 0.15))  # Responsive icon size
            upload_icon = upload_icon.resize((icon_size, icon_size))
            upload_icon_ctk = ctk.CTkImage(light_image=upload_icon, size=(icon_size, icon_size))
            upload_icon_label = ctk.CTkLabel(center_frame, image=upload_icon_ctk, text="")
            upload_icon_label.pack(pady=(0, 20))
        except Exception as e:
            print(f"Error loading upload icon: {e}")

        # Instructions with responsive font size
        font_size = min(14, int(self.app.winfo_height() * 0.02))
        instructions = ctk.CTkLabel(
            center_frame,
            text="Upload Excel file with staff details\nEach department should be in a separate sheet",
            font=ctk.CTkFont(family="Arial", size=font_size),
            text_color=self.UI_THEME['button_fg']
        )
        instructions.pack(pady=(0, 40))

        # Buttons frame
        button_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        # Calculate button width based on window size
        button_width = min(200, int(self.app.winfo_width() * 0.2))
        button_style = {
            **self.BUTTON_STYLE,
            'width': button_width,
            'height': 40,
            'font': ctk.CTkFont(family="Arial", size=font_size, weight="bold")
        }

        # Upload button
        upload_btn = ctk.CTkButton(
            button_frame,
            text="CHOOSE EXCEL FILE",
            command=self.upload_staff_file,  # Direct method reference, no lambda
            **button_style
        )
        upload_btn.pack(side="left", padx=10)

        # Back button
        back_btn = ctk.CTkButton(
            button_frame,
            text="BACK TO HOME",
            command=self.create_home_page,
            **button_style
        )
        back_btn.pack(side="left", padx=10)

        # Make the content vertically centered
        center_frame.pack_configure(expand=True)

    def show_staff_details(self):
        try:
            # Clear existing widgets
            for widget in self.app.winfo_children():
                widget.destroy()

            # Configure the main window
            self.app.configure(fg_color="#ffffff")

            # Create main container
            main_container = ctk.CTkFrame(self.app, fg_color="transparent")
            main_container.pack(fill="both", expand=True, padx=40, pady=30)

            # Header Frame
            header_frame = ctk.CTkFrame(main_container, fg_color="#000000", corner_radius=15)
            header_frame.pack(fill="x", padx=20, pady=(0, 40))
            
            # Create a frame for header content with grid layout
            header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
            header_content.pack(fill="x", pady=15, padx=20)
            header_content.grid_columnconfigure(1, weight=1)

            # Load and add left logo
            try:
                left_logo = PILImage.open(r"assets\leftlogo.png")
                left_logo = left_logo.resize((60, 60))
                left_logo_ctk = ctk.CTkImage(light_image=left_logo, size=(60, 60))
                left_logo_label = ctk.CTkLabel(header_content, image=left_logo_ctk, text="")
                left_logo_label.grid(row=0, column=0, padx=(0, 20))
            except Exception as e:
                print(f"Error loading left logo: {e}")

            # Title with enhanced styling
            title = ctk.CTkLabel(
                header_content,
                text="STAFF DETAILS AND STATISTICS",
                font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
                text_color="#ffffff"
            )
            title.grid(row=0, column=1)

            # Load and add right logo
            try:
                right_logo = PILImage.open(r"\assets\right logo.png")
                right_logo = right_logo.resize((60, 60))
                right_logo_ctk = ctk.CTkImage(light_image=right_logo, size=(60, 60))
                right_logo_label = ctk.CTkLabel(header_content, image=right_logo_ctk, text="")
                right_logo_label.grid(row=0, column=2, padx=(20, 0))
            except Exception as e:
                print(f"Error loading right logo: {e}")

            # Content container with two panels
            content_container = ctk.CTkFrame(main_container, fg_color="transparent")
            content_container.pack(fill="both", expand=True)
            content_container.grid_columnconfigure(1, weight=3)
            content_container.grid_rowconfigure(0, weight=1)

            # Left Panel - Staff List
            left_panel = ctk.CTkFrame(content_container, fg_color="#ffffff", corner_radius=15, border_width=2, border_color="#000000")
            left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            # Right Panel - Details and Statistics
            right_panel = ctk.CTkFrame(content_container, fg_color="#ffffff", corner_radius=15, border_width=2, border_color="#000000")
            right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            # Check if staff data exists
            if not os.path.exists("data/staff.json") or os.path.getsize("data/staff.json") == 0:
                # Show message to upload staff details
                message_label = ctk.CTkLabel(
                    main_container,
                    text="No staff details available.\nPlease upload staff details first.",
                    font=ctk.CTkFont(size=16)
                )
                message_label.pack(pady=20)
                
                # Add upload button
                upload_btn = ctk.CTkButton(
                    main_container,
                    text="Upload Staff Details",
                    command=self.show_upload_staff,
                    width=200,
                    height=40,
                    font=ctk.CTkFont(size=14)
                )
                upload_btn.pack(pady=10)
                
                # Back button
                back_btn = ctk.CTkButton(
                    main_container,
                    text="Back to Home",
                    command=self.create_home_page,
                    width=200,
                    height=40,
                    font=ctk.CTkFont(size=14)
                )
                back_btn.pack(pady=10)
                return

            # Load staff data
            with open("data/staff.json", 'r') as f:
                staff_list = json.load(f)

            # Group staff by department
            dept_staff = {}
            for staff in staff_list:
                dept = staff.get('staff_dept', '').strip()
                if dept not in dept_staff:
                    dept_staff[dept] = []
                dept_staff[dept].append(staff)

            # Left Panel - Department-wise Staff List
            left_title = ctk.CTkLabel(
                left_panel,
                text="STAFF LIST BY DEPARTMENT",
                font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                text_color="#000000"
            )
            left_title.pack(pady=15)

            # Create scrollable frame for staff list
            staff_frame = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
            staff_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # Button style for staff list
            staff_button_config = {
                "width": 250,
                "height": 35,
                "corner_radius": 8,
                "font": ctk.CTkFont(family="Arial", size=13)
            }

            # Add staff list department-wise
            for dept in sorted(dept_staff.keys()):
                # Department label with black background
                dept_label_frame = ctk.CTkFrame(staff_frame, fg_color="#000000", corner_radius=8)
                dept_label_frame.pack(fill="x", pady=(10, 5), padx=5)
                
                dept_label = ctk.CTkLabel(
                    dept_label_frame,
                    text=f"{dept} Department",
                    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    text_color="#ffffff"
                )
                dept_label.pack(pady=8)

                # Load excluded staff list
                excluded_staff_file = os.path.join('data', 'excluded_staff.json')
                excluded_staff = set()
                if os.path.exists(excluded_staff_file):
                    try:
                        with open(excluded_staff_file, 'r') as f:
                            excluded_staff = set(json.load(f))
                    except:
                        excluded_staff = set()

                # Staff list
                for staff in sorted(dept_staff[dept], key=lambda x: x['staff_name']):
                    is_excluded = staff['staff_name'].strip() in excluded_staff
                    
                    # Create combined button configuration
                    button_config = staff_button_config.copy()  # Create a copy of base config
                    button_config.update({  # Update with color settings
                        'fg_color': "#ffffff" if is_excluded else "#000000",
                        'text_color': "#000000" if is_excluded else "#ffffff",
                        'hover_color': "#f0f0f0" if is_excluded else "#333333",
                        'border_color': "#000000",
                        'border_width': 2
                    })
                    
                    staff_btn = ctk.CTkButton(
                        staff_frame,
                        text=f"{staff['staff_name']} ({staff['staff_gender']})",
                        command=lambda s=staff: self.show_staff_details_right(s, right_panel),
                        **button_config  # Use single combined configuration
                    )
                    staff_btn.pack(pady=3)

            # Back button at the bottom
            back_btn = ctk.CTkButton(
                left_panel,
                text="BACK TO HOME",
                command=self.create_home_page,
                width=200,
                height=40,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                fg_color="#000000",
                hover_color="#333333",
                corner_radius=8
            )
            back_btn.pack(pady=15)

            # Show initial statistics in right panel
            self.show_staff_details_right(None, right_panel)

        except Exception as e:
            messagebox.showerror("Error", f"Error loading staff details: {str(e)}")
            self.create_home_page()

    def show_staff_details_right(self, staff, right_panel):
        # Clear previous details
        for widget in right_panel.winfo_children():
            widget.destroy()

        # Load excluded staff list
        excluded_staff = set()
        excluded_staff_file = os.path.join('data', 'excluded_staff.json')
        if os.path.exists(excluded_staff_file):
            try:
                with open(excluded_staff_file, 'r') as f:
                    excluded_staff = set(json.load(f))
            except:
                excluded_staff = set()

        if staff is None:
            # Show overall statistics
            stats_title = ctk.CTkLabel(
                right_panel,
                text="STAFF STATISTICS",
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color="#000000"
            )
            stats_title.pack(pady=20)

            try:
                with open("data/staff.json", 'r') as f:
                    staff_list = json.load(f)
            
                # Calculate statistics
                total_staff = len(staff_list)
                available_staff = len([s for s in staff_list if s.get('staff_name', '').strip() not in excluded_staff])
                female_staff = len([s for s in staff_list if s.get('staff_gender', '').upper() in ['F', 'FEMALE'] 
                                  and s.get('staff_name', '').strip() not in excluded_staff])
                male_staff = len([s for s in staff_list if s.get('staff_gender', '').upper() in ['M', 'MALE']
                                and s.get('staff_name', '').strip() not in excluded_staff])

                # Stats boxes with consistent styling
                stats_style = {
                    "fg_color": self.UI_THEME['header_bg'],
                    "corner_radius": 8,
                    "border_width": 1,
                    "border_color": self.UI_THEME['button_border']
                }

                # Create boxes for total, available, male, and female counts
                counts_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
                counts_frame.pack(fill="x", padx=20, pady=10)

                # Total Staff Box
                total_box = ctk.CTkFrame(counts_frame, **stats_style)
                total_box.pack(fill="x", pady=5)
                
                ctk.CTkLabel(
                    total_box,
                    text="Total Staff",
                    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(8, 0))
                
                ctk.CTkLabel(
                    total_box,
                    text=str(total_staff),
                    font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(0, 8))

                # Available Staff Box
                available_box = ctk.CTkFrame(counts_frame, **stats_style)
                available_box.pack(fill="x", pady=5)
                
                ctk.CTkLabel(
                    available_box,
                    text="Available Staff",
                    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(8, 0))
                
                ctk.CTkLabel(
                    available_box,
                    text=str(available_staff),
                    font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(0, 8))

                # Male Staff Box
                male_box = ctk.CTkFrame(counts_frame, **stats_style)
                male_box.pack(fill="x", pady=5)
                
                ctk.CTkLabel(
                    male_box,
                    text="Male Staff Available",
                    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(8, 0))
                
                ctk.CTkLabel(
                    male_box,
                    text=str(male_staff),
                    font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(0, 8))

                # Female Staff Box
                female_box = ctk.CTkFrame(counts_frame, **stats_style)
                female_box.pack(fill="x", pady=5)
                
                ctk.CTkLabel(
                    female_box,
                    text="Female Staff Available",
                    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(8, 0))
                
                ctk.CTkLabel(
                    female_box,
                    text=str(female_staff),
                    font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                    text_color=self.UI_THEME['header_fg']
                ).pack(pady=(0, 8))

                # Department-wise counts title
                dept_title = ctk.CTkLabel(
                    right_panel,
                    text="DEPARTMENT-WISE STAFF COUNT",
                    font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                    text_color="#000000"
                )
                dept_title.pack(pady=(20, 10))

                # Create scrollable frame for department counts
                dept_scroll_container = ctk.CTkFrame(right_panel, fg_color="transparent")
                dept_scroll_container.pack(fill="both", expand=True, padx=20, pady=10)
                dept_scroll_container.grid_columnconfigure(0, weight=1)

                dept_scroll_frame = ctk.CTkScrollableFrame(
                    dept_scroll_container,
                    fg_color="transparent",
                    orientation="vertical"
                )
                dept_scroll_frame.pack(fill="both", expand=True)

                # Configure grid columns for responsive layout
                dept_scroll_frame.grid_columnconfigure((0, 1), weight=1)  # Two columns

                # Calculate department-wise counts
                dept_counts = {}
                for s in staff_list:
                    dept = s.get('staff_dept', '').strip()
                    if dept:
                        if dept not in dept_counts:
                            dept_counts[dept] = {
                                'total': 0,
                                'available': 0
                            }
                        dept_counts[dept]['total'] += 1
                        if s.get('staff_name', '').strip() not in excluded_staff:
                            dept_counts[dept]['available'] += 1

                # Create smaller boxes for each department in a grid
                for idx, dept in enumerate(sorted(dept_counts.keys())):
                    row = idx // 2  # Two columns
                    col = idx % 2
                    
                    # Department box with reduced size
                    dept_box = ctk.CTkFrame(
                        dept_scroll_frame,
                        **stats_style,
                        width=180  # Fixed width for consistency
                    )
                    dept_box.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                    dept_box.grid_columnconfigure(0, weight=1)  # Make content center-aligned
                    
                    # Department name
                    ctk.CTkLabel(
                        dept_box,
                        text=dept,
                        font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
                        text_color=self.UI_THEME['header_fg']
                    ).pack(pady=(8, 0))
                    
                    # Counts frame
                    counts_frame = ctk.CTkFrame(dept_box, fg_color="transparent")
                    counts_frame.pack(pady=(0, 8))
                    
                    # Total count
                    ctk.CTkLabel(
                        counts_frame,
                        text=f"Total: {dept_counts[dept]['total']}",
                        font=ctk.CTkFont(family="Arial", size=12),
                        text_color=self.UI_THEME['header_fg']
                    ).pack(side="left", padx=5)
                    
                    # Available count
                    ctk.CTkLabel(
                        counts_frame,
                        text=f"Available: {dept_counts[dept]['available']}",
                        font=ctk.CTkFont(family="Arial", size=12),
                        text_color=self.UI_THEME['header_fg']
                    ).pack(side="left", padx=5)

            except Exception as e:
                error_label = ctk.CTkLabel(
                    right_panel,
                    text=f"Error loading statistics: {str(e)}",
                    font=ctk.CTkFont(size=14),
                    text_color="#000000"
                )
                error_label.pack(pady=20)

        else:
            # Individual staff details view
            details_title = ctk.CTkLabel(
                right_panel,
                text="STAFF DETAILS",
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color="#000000"
            )
            details_title.pack(pady=20)

            details_frame = ctk.CTkFrame(
                right_panel, 
                fg_color="#f8f8f8", 
                corner_radius=10
            )
            details_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            details = [
                ("Name", staff.get('staff_name', 'N/A')),
                ("Department", staff.get('staff_dept', 'N/A')),
                ("Gender", staff.get('staff_gender', 'N/A'))
            ]

            for label, value in details:
                detail_box = ctk.CTkFrame(
                    details_frame, 
                    fg_color="#000000", 
                    corner_radius=8
                )
                detail_box.pack(fill="x", padx=15, pady=10)
                
                ctk.CTkLabel(
                    detail_box,
                    text=label.upper(),
                    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    text_color="#ffffff"
                ).pack(pady=(10, 0))
                
                ctk.CTkLabel(
                    detail_box,
                    text=str(value),
                    font=ctk.CTkFont(family="Arial", size=16),
                    text_color="#ffffff"
                ).pack(pady=(0, 10))

            # Add Remove/Restore for Allotment button
            staff_name = staff.get('staff_name', '').strip()
            is_excluded = staff_name in excluded_staff
            
            button_text = "Restore for Allotment" if is_excluded else "Remove from Allotment"
            button_colors = {
                'fg_color': "#ffffff" if is_excluded else "#000000",
                'text_color': "#000000" if is_excluded else "#ffffff",
                'hover_color': "#f0f0f0" if is_excluded else "#333333",
                'border_color': "#000000"
            }
            
            allotment_btn = ctk.CTkButton(
                details_frame,
                text=button_text,
                command=lambda: self.toggle_staff_allotment(staff_name, right_panel),
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                width=200,
                height=40,
                corner_radius=8,
                border_width=2,
                **button_colors
            )
            allotment_btn.pack(pady=20)

    def toggle_staff_allotment(self, staff_name, right_panel):
        """Toggle staff inclusion/exclusion from allotment"""
        excluded_staff_file = os.path.join('data', 'excluded_staff.json')
        
        # Load current excluded staff
        excluded_staff = []
        if os.path.exists(excluded_staff_file):
            try:
                with open(excluded_staff_file, 'r') as f:
                    excluded_staff = json.load(f)
            except:
                excluded_staff = []
        
        # Toggle staff status
        if staff_name in excluded_staff:
            excluded_staff.remove(staff_name)
            message = f"{staff_name} has been restored for allotment"
        else:
            excluded_staff.append(staff_name)
            message = f"{staff_name} has been removed from allotment"
        
        # Save updated list
        with open(excluded_staff_file, 'w') as f:
            json.dump(excluded_staff, f)
        
        # Refresh the display
        self.show_staff_details()
        messagebox.showinfo("Success", message)

    def select_dates(self):
        try:
            # Clear existing widgets
            for widget in self.app.winfo_children():
                widget.destroy()

            # Create main container with responsive padding
            main_container = ctk.CTkFrame(self.app, fg_color="transparent")
            main_container.pack(fill="both", expand=True, padx=40, pady=30)

            # Add header with consistent styling
            self.create_header(main_container, "SELECT EXAM DATES")

            # Calculate responsive dimensions
            window_width = self.app.winfo_width()
            window_height = self.app.winfo_height()
            
            # Content frame with border and responsive padding
            content_frame = ctk.CTkFrame(
                main_container,
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=15,
                border_width=2,
                border_color=self.UI_THEME['button_border']
            )
            content_frame.pack(fill="both", expand=True, padx=20)

            # Calendar section with responsive title
            title_size = max(18, min(24, int(window_height * 0.03)))
            calendar_title = ctk.CTkLabel(
                content_frame,
                text="SELECT DATE RANGE",
                font=ctk.CTkFont(family="Arial", size=title_size, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            )
            calendar_title.pack(pady=(20, 10))

            # Date Selection Frame with responsive spacing
            date_selection_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            date_selection_frame.pack(pady=(0, 20), padx=int(window_width * 0.04), fill="x")
            date_selection_frame.grid_columnconfigure((0, 1, 2), weight=1)

            # Calculate responsive dimensions for date frames
            date_frame_width = max(150, min(200, int(window_width * 0.15)))
            date_frame_height = max(100, min(120, int(window_height * 0.15)))

            # Start Date Frame with enhanced styling
            start_date_frame = ctk.CTkFrame(
                date_selection_frame, 
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=10,
                border_width=1,
                border_color=self.UI_THEME['button_border'],
                width=date_frame_width,
                height=date_frame_height
            )
            start_date_frame.grid(row=0, column=0, padx=10, sticky="ew")

            start_date_label = ctk.CTkLabel(
                start_date_frame, 
                text="Start Date",
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            )
            start_date_label.pack(pady=(10, 5))

            start_cal = DateEntry(
                start_date_frame, 
                width=12, 
                background=self.UI_THEME['header_bg'],
                foreground=self.UI_THEME['header_fg'],
                borderwidth=2
            )
            start_cal.pack(pady=(0, 10))

            # End Date Frame with matching style
            end_date_frame = ctk.CTkFrame(
                date_selection_frame, 
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=10,
                border_width=1,
                border_color=self.UI_THEME['button_border'],
                width=date_frame_width,
                height=date_frame_height
            )
            end_date_frame.grid(row=0, column=2, padx=10, sticky="ew")

            end_date_label = ctk.CTkLabel(
                end_date_frame, 
                text="End Date",
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            )
            end_date_label.pack(pady=(10, 5))

            end_cal = DateEntry(
                end_date_frame, 
                width=12, 
                background=self.UI_THEME['header_bg'],
                foreground=self.UI_THEME['header_fg'],
                borderwidth=2
            )
            end_cal.pack(pady=(0, 10))

            # Generate button with responsive sizing
            button_width = max(150, min(180, int(window_width * 0.12)))
            button_height = max(35, min(45, int(window_height * 0.06)))
            
            generate_btn = ctk.CTkButton(
                date_selection_frame,
                text="Generate Dates",
                command=lambda: generate_dates(),
                width=button_width,
                height=button_height,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                border_color=self.UI_THEME['button_border'],
                border_width=2,
                corner_radius=8
            )
            generate_btn.grid(row=0, column=1, padx=20)

            # Selected dates section with responsive title
            dates_title = ctk.CTkLabel(
                content_frame,
                text="SELECTED DATES",
                font=ctk.CTkFont(family="Arial", size=title_size, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            )
            dates_title.pack(pady=(20, 10))

            # Dates display frame with enhanced styling
            dates_display_frame = ctk.CTkFrame(
                content_frame,
                fg_color=self.UI_THEME['content_bg'],
                border_width=1,
                border_color=self.UI_THEME['button_border'],
                corner_radius=10
            )
            dates_display_frame.pack(pady=(0, 20), padx=int(window_width * 0.04), fill="both", expand=True)

            # Scrollable frame with transparent background
            dates_scroll_frame = ctk.CTkScrollableFrame(
                dates_display_frame,
                fg_color="transparent",
                corner_radius=0
            )
            dates_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

            def generate_dates():
                try:
                    start_date = datetime.strptime(start_cal.get_date().strftime("%Y-%m-%d"), "%Y-%m-%d")
                    end_date = datetime.strptime(end_cal.get_date().strftime("%Y-%m-%d"), "%Y-%m-%d")

                    if start_date > end_date:
                        messagebox.showerror("Error", "Start date cannot be after end date")
                        return

                    # Clear existing dates
                    self.selected_dates = []
                    for widget in dates_scroll_frame.winfo_children():
                        widget.destroy()

                    # Generate dates excluding Sundays
                    current_date = start_date
                    while current_date <= end_date:
                        if current_date.weekday() != 6:  # 6 represents Sunday
                            date_str = current_date.strftime("%Y-%m-%d")
                            self.selected_dates.append(date_str)
                            
                            # Create frame for date with enhanced styling
                            date_frame = ctk.CTkFrame(
                                dates_scroll_frame,
                                fg_color=self.UI_THEME['content_bg'],
                                corner_radius=8,
                                border_width=1,
                                border_color=self.UI_THEME['button_border']
                            )
                            date_frame.pack(fill="x", padx=10, pady=5)
                            date_frame.grid_columnconfigure(0, weight=1)
                            
                            # Format date for display
                            formatted_date = current_date.strftime("%d %B %Y (%A)")
                            
                            # Date container frame for better alignment
                            date_container = ctk.CTkFrame(date_frame, fg_color="transparent")
                            date_container.pack(fill="x", padx=10, pady=8)
                            date_container.grid_columnconfigure(0, weight=1)
                            
                            # Date label with enhanced styling
                            date_label = ctk.CTkLabel(
                                date_container, 
                                                  text=formatted_date,
                                font=ctk.CTkFont(family="Arial", size=14),
                                text_color=self.UI_THEME['button_fg']
                            )
                            date_label.pack(side="left")
                            
                            # Remove button with theme-consistent styling
                            remove_btn = ctk.CTkButton(
                                date_container,
                                text="✕",  # Using × symbol instead of text
                                                   width=30,
                                height=30,
                                command=lambda d=date_str, f=date_frame: remove_date(d, f),
                                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                                fg_color=self.UI_THEME['button_bg'],
                                text_color=self.UI_THEME['button_fg'],
                                hover_color=self.UI_THEME['button_hover'],
                                border_color=self.UI_THEME['button_border'],
                                border_width=1,
                                corner_radius=8
                            )
                            remove_btn.pack(side="right")
                            
                        current_date += timedelta(days=1)

                    # Update the dates display frame appearance
                    if self.selected_dates:
                        dates_display_frame.configure(
                            border_width=1,
                            border_color=self.UI_THEME['button_border']
                        )
                    else:
                        dates_display_frame.configure(
                            border_width=0
                        )

                except Exception as e:
                    messagebox.showerror("Error", f"Error generating dates: {str(e)}")

            def remove_date(date_str, date_frame):
                if date_str in self.selected_dates:
                    self.selected_dates.remove(date_str)
                    date_frame.destroy()

            def proceed_to_configure():
                if not self.selected_dates:
                    messagebox.showerror("Error", "Please select at least one date")
                    return
                self.save_selected_dates()

            # Navigation buttons frame with responsive sizing
            nav_buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            nav_buttons_frame.pack(pady=20, padx=int(window_width * 0.04), fill="x")
            nav_buttons_frame.grid_columnconfigure((0, 1), weight=1)

            # Back button with responsive sizing
            back_btn = ctk.CTkButton(
                nav_buttons_frame,
                text="← Back",
                command=self.create_home_page,
                width=button_width,
                height=button_height,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                border_color=self.UI_THEME['button_border'],
                border_width=2,
                corner_radius=8
            )
            back_btn.grid(row=0, column=0, padx=10)

            # Next button with responsive sizing
            next_btn = ctk.CTkButton(
                nav_buttons_frame,
                text="Next →",
                command=lambda: proceed_to_configure(),
                width=button_width,
                height=button_height,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                border_color=self.UI_THEME['button_border'],
                border_width=2,
                corner_radius=8
            )
            next_btn.grid(row=0, column=1, padx=10)

        except Exception as e:
            print(f"Error in select_dates: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error in date selection: {str(e)}")

    def save_selected_dates(self):
        try:
            if not self.selected_dates:
                messagebox.showerror("Error", "Please select at least one date")
                return

            # Save selected dates to settings
            with open(DB_FILES['settings'], 'w') as f:
                json.dump({
                    'dates': self.selected_dates,
                    'reporting_time': '',
                    'assessment_name': '',
                    'exam_time': '',
                    'exam_details': ''
                }, f)

            # Load configurations only for selected dates
            self.config_manager.clear_configurations()
            for date in self.selected_dates:
                self.config_manager.set_date_config(date, {
                    'rooms': [],
                    'settings': {
                        'reporting_time': '',
                        'assessment_name': '',
                        'exam_time': '',
                        'exam_details': ''
                    }
                })

            self.configure_selected_classes()
        except Exception as e:
            print(f"Error saving dates: {str(e)}")
            messagebox.showerror("Error", f"Failed to save dates: {str(e)}")

    def configure_selected_classes(self):
        try:
            # Clear existing widgets
            for widget in self.app.winfo_children():
                widget.destroy()

            # Initialize class variables
            self.building_vars = {}
            self.class_vars = {}
            self.class_modifiers = {}

            # Load halls data from halls.json instead of using self.buildings
            try:
                with open(DB_FILES['halls'], 'r') as f:
                    self.buildings = json.load(f)  # Replace self.buildings with data from halls.json
            except Exception as e:
                print(f"Error loading halls data: {str(e)}")
                self.buildings = {}

            # Calculate staff statistics
            total_staff = 0
            available_staff = 0
            female_staff = 0
            male_staff = 0

            # Load staff data and excluded staff
            try:
                with open("data/staff.json", 'r') as f:
                    staff_list = json.load(f)
                
                excluded_staff_file = os.path.join('data', 'excluded_staff.json')
                excluded_staff = set()
                if os.path.exists(excluded_staff_file):
                    with open(excluded_staff_file, 'r') as f:
                        excluded_staff = set(json.load(f))

                # Calculate statistics
                total_staff = len(staff_list)
                available_staff = len([s for s in staff_list if s.get('staff_name', '').strip() not in excluded_staff])
                female_staff = len([s for s in staff_list if s.get('staff_gender', '').upper() in ['F', 'FEMALE'] 
                                  and s.get('staff_name', '').strip() not in excluded_staff])
                male_staff = len([s for s in staff_list if s.get('staff_gender', '').upper() in ['M', 'MALE']
                                and s.get('staff_name', '').strip() not in excluded_staff])
            except Exception as e:
                print(f"Error loading staff data: {str(e)}")

            # Create main container
            main_container = ctk.CTkFrame(self.app, fg_color="transparent")
            main_container.pack(fill="both", expand=True, padx=40, pady=30)

            # Add header
            self.create_header(main_container, "CONFIGURE CLASSES")

            # Content frame with border
            content_frame = ctk.CTkFrame(
                main_container,
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=15,
                border_width=2,
                border_color=self.UI_THEME['button_border']
            )
            content_frame.pack(fill="both", expand=True, padx=20)

            # Create split container
            split_container = ctk.CTkFrame(content_frame, fg_color="transparent")
            split_container.pack(fill="both", expand=True, padx=20, pady=20)
            split_container.grid_columnconfigure(1, weight=3)  # Right panel takes more space
            split_container.grid_rowconfigure(0, weight=1)

            # Helper functions for updating UI
            def update_classes(building_name):
                # When building checkbox is clicked, update all its classes
                building_state = self.building_vars[building_name].get()
                for class_name in self.buildings[building_name]:
                    self.class_vars[class_name].set(building_state)

            def update_building(building_name):
                # When class checkbox is clicked, check if all classes are checked
                all_checked = all(self.class_vars[c].get() 
                                for c in self.buildings[building_name])
                self.building_vars[building_name].set(all_checked)

            # Left panel for statistics
            left_panel = ctk.CTkFrame(
                split_container,
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=10,
                border_width=1,
                border_color=self.UI_THEME['button_border']
            )
            left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)

            # Available Staff Section
            staff_title = ctk.CTkLabel(
                left_panel,
                text="AVAILABLE STAFF",
                font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            )
            staff_title.pack(pady=(15, 10))

            # Create grid frame for available staff stats
            avail_stats_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
            avail_stats_frame.pack(fill="x", padx=10, pady=5)
            avail_stats_frame.grid_columnconfigure((0, 1), weight=1)

            # Stats style
            stats_style = {
                "fg_color": self.UI_THEME['header_bg'],
                "corner_radius": 8,
                "border_width": 1,
                "border_color": self.UI_THEME['button_border'],
                "width": 120,
                "height": 80
            }

            # Available Staff Box
            available_box = ctk.CTkFrame(avail_stats_frame, **stats_style)
            available_box.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            ctk.CTkLabel(
                available_box,
                text="Total",
                font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(5, 0))
            
            ctk.CTkLabel(
                available_box,
                text=str(available_staff),
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(0, 5))

            # Female Staff Box
            female_box = ctk.CTkFrame(avail_stats_frame, **stats_style)
            female_box.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            ctk.CTkLabel(
                female_box,
                text="Female",
                font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(5, 0))
            
            ctk.CTkLabel(
                female_box,
                text=str(female_staff),
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(0, 5))

            # Male Staff Box
            male_box = ctk.CTkFrame(avail_stats_frame, **stats_style)
            male_box.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
            
            ctk.CTkLabel(
                male_box,
                text="Male",
                font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(5, 0))
            
            ctk.CTkLabel(
                male_box,
                text=str(male_staff),
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(0, 5))

            # Required Staff Section with separator
            separator = ctk.CTkFrame(
                left_panel,
                height=2,
                fg_color=self.UI_THEME['button_border']
            )
            separator.pack(fill="x", padx=20, pady=15)

            required_title = ctk.CTkLabel(
                left_panel,
                text="REQUIRED STAFF",
                font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            )
            required_title.pack(pady=(10, 10))

            # Create grid frame for required staff stats
            req_stats_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
            req_stats_frame.pack(fill="x", padx=10, pady=5)
            req_stats_frame.grid_columnconfigure((0, 1), weight=1)

            # Required Total Box
            required_box = ctk.CTkFrame(req_stats_frame, **stats_style)
            required_box.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(
                required_box,
                text="Total",
                font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(5, 0))

            self.required_total_label = ctk.CTkLabel(
                required_box,
                text="0",
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            )
            self.required_total_label.pack(pady=(0, 5))

            # Female Required Box
            female_req_box = ctk.CTkFrame(req_stats_frame, **stats_style)
            female_req_box.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(
                female_req_box,
                text="Female",
                font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(5, 0))

            self.required_female_label = ctk.CTkLabel(
                female_req_box,
                text="0",
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            )
            self.required_female_label.pack(pady=(0, 5))

            # Male Possible Box
            male_req_box = ctk.CTkFrame(req_stats_frame, **stats_style)
            male_req_box.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(
                male_req_box,
                text="Male",
                font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            ).pack(pady=(5, 0))

            self.required_male_label = ctk.CTkLabel(
                male_req_box,
                text="0",
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color=self.UI_THEME['header_fg']
            )
            self.required_male_label.pack(pady=(0, 5))

            # Right panel for class selection and configuration
            self.right_panel = ctk.CTkFrame(  # Store as class attribute
                split_container,
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=10,
                border_width=1,
                border_color=self.UI_THEME['button_border']
            )
            self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)

                # Title for class selection
            class_title = ctk.CTkLabel(
                self.right_panel,  # Use self.right_panel
                    text="SELECT CLASSES",
                font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                    text_color=self.UI_THEME['button_fg']
                )
            class_title.pack(pady=(15, 10))

                # Create scrollable frame for buildings and classes
            scroll_frame = ctk.CTkScrollableFrame(
                self.right_panel,  # Use self.right_panel
                fg_color="transparent"
            )
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # Style for building frames
            building_style = {
                "fg_color": self.UI_THEME['header_bg'],
                "corner_radius": 8,
                "border_width": 1,
                "border_color": self.UI_THEME['button_border']
            }

            # Add buildings and their classes
            for building_name in sorted(self.buildings.keys()):
                # Building frame
                building_frame = ctk.CTkFrame(scroll_frame, **building_style)
                building_frame.pack(fill="x", pady=5)
                
                # Building header frame
                header_frame = ctk.CTkFrame(
                    building_frame, 
                    fg_color="#000000",  # Black background for the header
                    corner_radius=8
                )
                header_frame.pack(fill="x", padx=10, pady=5)
                
                # Building checkbox
                building_var = tk.BooleanVar()
                self.building_vars[building_name] = building_var
                
                # Building checkbox style
                building_checkbox_style = {
                    "font": ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    "text_color": "#ffffff",  # White text for building name
                    "fg_color": "#ffffff",    # White when checked
                    "hover_color": "#cccccc", # Light gray on hover
                    "border_color": "#ffffff", # White border
                    "border_width": 2,
                    "checkmark_color": "#000000"  # Black checkmark for contrast
                }
                
                building_cb = ctk.CTkCheckBox(
                    header_frame,
                                             text=building_name,
                    variable=building_var,
                                             command=lambda b=building_name: update_classes(b),
                    **building_checkbox_style
                    )
                building_cb.pack(side="left", padx=10, pady=8)

                    # Classes container
                classes_frame = ctk.CTkFrame(building_frame, fg_color="transparent")
                classes_frame.pack(fill="x", padx=20, pady=(0, 10))
                
                # Create grid for classes (3 columns)
                classes_frame.grid_columnconfigure((0, 1, 2), weight=1)
                
                # Add classes in a grid
                for i, class_name in enumerate(sorted(self.buildings[building_name])):
                    row = i // 3
                    col = i % 3
                    
                    # Class frame with white background and black border
                    class_frame = ctk.CTkFrame(
                        classes_frame,
                        fg_color=self.UI_THEME['content_bg'],
                        corner_radius=6,
                        border_width=1,
                        border_color=self.UI_THEME['button_border']
                    )
                    class_frame.grid(row=row, column=col, padx=5, pady=3, sticky="ew")
                    
                    # Class checkbox
                    class_var = tk.BooleanVar()
                    self.class_vars[class_name] = class_var
                    
                    # Class checkbox style
                    class_checkbox_style = {
                        "font": ctk.CTkFont(family="Arial", size=12),
                        "text_color": self.UI_THEME['button_fg'],
                        "fg_color": "#000000",  # Color when checked
                        "hover_color": "#333333",  # Slightly lighter black on hover
                        "border_color": self.UI_THEME['button_border'],
                        "border_width": 2,
                        "checkmark_color": "#ffffff"  # White checkmark
                    }
                        
                    class_cb = ctk.CTkCheckBox(
                        class_frame,
                                              text=class_name,
                        variable=class_var,
                            command=lambda b=building_name: update_building(b),
                        **class_checkbox_style
                    )
                    class_cb.pack(padx=8, pady=5)

            # Button frame at bottom
            button_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
            button_frame.pack(fill="x", padx=10, pady=10)
            button_frame.grid_columnconfigure((0, 1), weight=1)

            # Back button
            back_btn = ctk.CTkButton(
                button_frame,
                text="← Back",
                command=self.create_home_page,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                width=120,
                height=35,
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                            border_color=self.UI_THEME['button_border'],
                border_width=2,
                corner_radius=8
                        )
            back_btn.grid(row=0, column=0, padx=5)

                # Next button
            next_btn = ctk.CTkButton(
                button_frame,
                text="Next →",
                command=lambda: self.show_class_configuration(),  # Changed from configure_selected_rooms
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                width=120,
                height=35,
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                border_color=self.UI_THEME['button_border'],
                border_width=2,
                corner_radius=8
            )
            next_btn.grid(row=0, column=1, padx=5)

        except Exception as e:
            print(f"Error in configure_selected_classes: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error in class configuration: {str(e)}")

    def show_class_configuration(self):
        try:
            # Get selected classes
            selected_classes = [class_name for class_name, var in self.class_vars.items() 
                              if var.get()]
            
            if not selected_classes:
                messagebox.showerror("Error", "Please select at least one class")
                return

            # Clear right panel
            for widget in self.right_panel.winfo_children():
                widget.destroy()

            # Title for configuration
            class_title = ctk.CTkLabel(
                self.right_panel,
                text="CONFIGURE CLASS SETTINGS",
                font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            )
            class_title.pack(pady=(15, 10))

            # Create scrollable frame for class configurations
            scroll_frame = ctk.CTkScrollableFrame(
                self.right_panel,
                fg_color="transparent"
            )
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # Create configuration frames for each selected class
            for class_name in selected_classes:
                # Initialize modifiers if not exists
                if class_name not in self.class_modifiers:
                    self.class_modifiers[class_name] = {
                        'selected': self.class_vars[class_name],
                        'girls_only': tk.BooleanVar(value=False),
                        'single_staff': tk.BooleanVar(value=False)
                    }

                # Create frame for this class
                class_frame = ctk.CTkFrame(
                    scroll_frame,
                    fg_color=self.UI_THEME['content_bg'],
                    corner_radius=8,
                    border_width=1,
                    border_color=self.UI_THEME['button_border']
                )
                class_frame.pack(fill="x", padx=5, pady=5)

                # Class name label
                class_label = ctk.CTkLabel(
                    class_frame,
                    text=class_name,
                    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                    text_color=self.UI_THEME['button_fg']
                )
                class_label.pack(side="left", padx=15, pady=10)

                # Checkboxes container
                checkbox_frame = ctk.CTkFrame(class_frame, fg_color="transparent")
                checkbox_frame.pack(side="right", padx=10)

                # Single Staff checkbox
                single_staff_cb = ctk.CTkCheckBox(
                    checkbox_frame,
                    text="Single Staff",
                    variable=self.class_modifiers[class_name]['single_staff'],
                    command=self.update_requirements,
                    font=ctk.CTkFont(family="Arial", size=12),
                    text_color=self.UI_THEME['button_fg'],
                    fg_color=self.UI_THEME['button_bg'],
                    hover_color=self.UI_THEME['button_hover'],
                    border_color=self.UI_THEME['button_border']
                )
                single_staff_cb.pack(side="right", padx=10)

                # Girls Only checkbox
                girls_only_cb = ctk.CTkCheckBox(
                    checkbox_frame,
                    text="Girls Only",
                    variable=self.class_modifiers[class_name]['girls_only'],
                    command=self.update_requirements,
                    font=ctk.CTkFont(family="Arial", size=12),
                    text_color=self.UI_THEME['button_fg'],
                    fg_color=self.UI_THEME['button_bg'],
                    hover_color=self.UI_THEME['button_hover'],
                    border_color=self.UI_THEME['button_border']
                )
                girls_only_cb.pack(side="right", padx=10)

            # Button frame
            button_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
            button_frame.pack(fill="x", padx=10, pady=10)
            button_frame.grid_columnconfigure((0, 1), weight=1)

            # Back button
            back_btn = ctk.CTkButton(
                button_frame,
                text="← Back",
                command=self.create_home_page,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                width=150,
                height=35,
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                border_color=self.UI_THEME['button_border'],
                border_width=2,
                corner_radius=8
            )
            back_btn.pack(side="left", padx=5)

            # Save Configuration button
            save_btn = ctk.CTkButton(
                button_frame,
                text="Save Configuration →",
                command=self.save_configuration,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                width=150,
                height=35,
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                border_color=self.UI_THEME['button_border'],
                border_width=2,
                corner_radius=8
            )
            save_btn.pack(side="right", padx=5)

            # Update requirements based on current configuration
            self.update_requirements()

        except Exception as e:
            print(f"Error in show_class_configuration: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error configuring classes: {str(e)}")

    def add_exam_details(self):
        try:
            # Clear existing widgets
            for widget in self.app.winfo_children():
                widget.destroy()

            # Create main container
            main_container = ctk.CTkFrame(self.app, fg_color="transparent")
            main_container.pack(fill="both", expand=True, padx=40, pady=30)

            # Add header
            self.create_header(main_container, "EXAMINATION DETAILS")

            # Content frame with border
            content_frame = ctk.CTkFrame(
                main_container,
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=15,
                border_width=2,
                border_color=self.UI_THEME['button_border']
            )
            content_frame.pack(fill="both", expand=True, padx=20)

            # Form container with padding
            form_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            form_frame.pack(fill="both", expand=True, padx=40, pady=30)

            # Common styles
            label_style = {
                "font": ctk.CTkFont(family="Arial", size=14, weight="bold"),
                "text_color": self.UI_THEME['button_fg']
            }

            entry_style = {
                "font": ctk.CTkFont(family="Arial", size=13),
                "height": 40,
                "corner_radius": 8,
                "border_width": 2,
                "border_color": self.UI_THEME['button_border'],
                "fg_color": "#ffffff",
                "text_color": "#000000",
                "placeholder_text_color": "#666666"
            }

            # Create input fields with consistent spacing
            input_fields = [
                {
                    "label": "Assessment Name",
                    "placeholder": "Enter assessment name (e.g., Assessment - 1)...",
                    "variable": "assessment_name_var"
                },
                {
                    "label": "Reporting Time",
                    "placeholder": "Enter reporting time (e.g., 9:00 AM)...",
                    "variable": "reporting_time_var"
                },
                {
                    "label": "Examination Time",
                    "placeholder": "Enter examination time (e.g., January 2025)...",
                    "variable": "exam_month_var"
                }
            ]

            # Create input fields
            for field in input_fields:
                # Label
                ctk.CTkLabel(
                    form_frame, 
                    text=field["label"], 
                    **label_style
                ).pack(anchor="w", pady=(0, 5))

                # Entry
                entry = ctk.CTkEntry(
                    form_frame,
                    placeholder_text=field["placeholder"],
                    **entry_style
                )
                entry.pack(fill="x", pady=(0, 20))
                setattr(self, field["variable"], entry)

            # Additional Details section
            ctk.CTkLabel(
                form_frame, 
                text="Additional Details", 
                **label_style
            ).pack(anchor="w", pady=(0, 5))

            # Details textbox
            details_text = ctk.CTkTextbox(
                form_frame,
                height=120,
                font=ctk.CTkFont(family="Arial", size=13),
                fg_color="#ffffff",
                text_color="#000000",
                corner_radius=8,
                border_width=2,
                border_color=self.UI_THEME['button_border']
            )
            details_text.pack(fill="x", pady=(0, 30))
            
            # Add placeholder text
            details_text.insert("1.0", "Enter any additional examination details...")
            details_text.configure(text_color="#666666")
            
            # Bind focus events
            details_text.bind("<FocusIn>", lambda e: self.on_textbox_focus_in(details_text))
            details_text.bind("<FocusOut>", lambda e: self.on_textbox_focus_out(details_text))
            self._is_placeholder_visible = True

            # Button frame
            button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=10)
            button_frame.grid_columnconfigure((0, 1), weight=1)

            # Button style
            button_style = {
                "font": ctk.CTkFont(family="Arial", size=14, weight="bold"),
                "width": 150,
                "height": 40,
                "corner_radius": 8,
                "border_width": 2,
                "border_color": self.UI_THEME['button_border']
            }

            # Back button
            back_btn = ctk.CTkButton(
                button_frame,
                text="← Back",
                command=self.configure_selected_classes,
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                **button_style
            )
            back_btn.grid(row=0, column=0, padx=10)

            # Generate button
            generate_btn = ctk.CTkButton(
                button_frame,
                text="Generate PDFs →",
                command=lambda: self.generate_both(),
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                **button_style
            )
            generate_btn.grid(row=0, column=1, padx=10)

        except Exception as e:
            print(f"Error in add_exam_details: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error adding exam details: {str(e)}")

    def on_textbox_focus_in(self, textbox):
        """Handle textbox focus in - clear placeholder"""
        if self._is_placeholder_visible:
            textbox.delete("1.0", "end")
            textbox.configure(text_color="#000000")
            self._is_placeholder_visible = False

    def on_textbox_focus_out(self, textbox):
        """Handle textbox focus out - restore placeholder if empty"""
        if not textbox.get("1.0", "end-1c"):
            textbox.configure(text_color="#666666")
            textbox.insert("1.0", "Enter any additional examination details...")
            self._is_placeholder_visible = True

    def get_staff_statistics(self):
        """
        Get statistics about uploaded staff data
        Returns: tuple (total_staff, female_staff, male_staff)
        """
        try:
            with open(DB_FILES['staff'], 'r') as f:
                staff_data = json.load(f)
            
            total_staff = len(staff_data)
            female_staff = len([s for s in staff_data if s.get('staff_gender', '').upper() in ['F', 'FEMALE']])
            male_staff = len([s for s in staff_data if s.get('staff_gender', '').upper() in ['M', 'MALE']])
            
            print(f"Staff statistics - Total: {total_staff}, Female: {female_staff}, Male: {male_staff}")
            return total_staff, female_staff, male_staff
        except Exception as e:
            print(f"Error getting staff statistics: {str(e)}")
            return 0, 0, 0

    def calculate_staff_requirements(self):
        """
        Calculate the required number of staff based on current room configurations
        Returns: tuple (total_required, female_required, male_possible)
        """
        try:
            total_required = 0
            female_required = 0
            
            for room_no in self.available_classes:
                girls_only = self.room_frames[room_no].winfo_children()[1].variable.get()
                single_staff = self.room_frames[room_no].winfo_children()[2].variable.get()
                
                if single_staff:
                    # Single staff required
                    total_required += 1
                    if girls_only:
                        female_required += 1
                else:
                    # Two staff required
                    total_required += 2
                    if girls_only:
                        female_required += 2
            
            # Male staff can fill any non-female-required positions
            male_possible = total_required - female_required
            
            return total_required, female_required, male_possible
        except Exception as e:
            print(f"Error calculating requirements: {str(e)}")
            return 0, 0, 0

    def allocate_staff(self, staff_list, classes_list, date):
        """
        Allocate staff to classes based on room modifiers:
        - No modifiers: Two staff members (any gender)
        - Girls Only: Two female staff members
        - Single Staff: One staff member (any gender)
        - Both modifiers (Girls Only + Single Staff): One female staff member
        """
        try:
            # Load excluded staff
            excluded_staff_file = os.path.join('data', 'excluded_staff.json')
            if os.path.exists(excluded_staff_file):
                with open(excluded_staff_file, 'r') as f:
                    excluded_staff = set(json.load(f))
                
                # Remove excluded staff from the allocation pool
                staff_list = [s for s in staff_list if s['staff_name'].strip() not in excluded_staff]

            # Randomize staff list to ensure fair distribution
            random.shuffle(staff_list)
            
            # Initialize allotments list
            allotments = []
            
            # Process each room
            for class_info in classes_list:
                room_no = class_info['room_no']
                girls_only = class_info['girls_only']
                single_staff = class_info['single_staff']
                
                # Filter eligible staff based on room requirements
                eligible_staff = []
                if girls_only:
                    eligible_staff = [s for s in staff_list if s.get('staff_gender', '').upper() in ['F', 'FEMALE']]
                else:
                    eligible_staff = staff_list.copy()
                
                # Determine number of staff needed
                staff_needed = 1 if single_staff else 2
                
                # Select required number of staff
                selected_staff = []
                while len(selected_staff) < staff_needed and eligible_staff:
                    staff = eligible_staff.pop(0)
                    selected_staff.append(staff)
                    staff_list.remove(staff)  # Remove from main available pool
                
                # Add to allotments if staff was assigned
                if selected_staff:
                    allotments.append({
                        'room_no': room_no,
                        'staff': selected_staff
                    })
            
            return allotments

        except Exception as e:
            print(f"Error in allocate_staff: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            raise

    def enter_details(self):
        """Enter assessment details page"""
        try:
            # Clear existing widgets
            for widget in self.app.winfo_children():
                widget.destroy()

            # Create main container
            main_container = ctk.CTkFrame(self.app)
            main_container.pack(padx=20, pady=20, fill="both", expand=True)

            # Title
            title_label = ctk.CTkLabel(main_container, 
                                   text="Enter Assessment Details", 
                                   font=ctk.CTkFont(size=20, weight="bold"))
            title_label.pack(pady=20)

            # Create form frame
            form_frame = ctk.CTkFrame(main_container)
            form_frame.pack(pady=20, padx=60, fill="x")

            # Exam Month
            month_label = ctk.CTkLabel(form_frame, text="Exam Month:", font=ctk.CTkFont(size=14))
            month_label.pack(anchor="w", pady=(0, 5))

            self.exam_month_var = tk.StringVar(value="")
            month_entry = ctk.CTkEntry(form_frame, textvariable=self.exam_month_var, width=200)
            month_entry.pack(anchor="w", pady=(0, 15))

            # Assessment Name
            assessment_label = ctk.CTkLabel(form_frame, text="Assessment Name:", font=ctk.CTkFont(size=14))
            assessment_label.pack(anchor="w", pady=(0, 5))
            self.assessment_name_var = tk.StringVar(value="")
            assessment_entry = ctk.CTkEntry(form_frame, textvariable=self.assessment_name_var, width=200)
            assessment_entry.pack(anchor="w", pady=(0, 15))

            # Reporting Time
            time_label = ctk.CTkLabel(form_frame, text="Reporting Time:", font=ctk.CTkFont(size=14))
            time_label.pack(anchor="w", pady=(0, 5))
            self.reporting_time_var = tk.StringVar(value="")
            time_entry = ctk.CTkEntry(form_frame, textvariable=self.reporting_time_var, width=200)
            time_entry.pack(anchor="w", pady=(0, 15))

            # Buttons frame
            buttons_frame = ctk.CTkFrame(main_container)
            buttons_frame.pack(pady=20)

            # Back button
            back_btn = ctk.CTkButton(buttons_frame, 
                                  text="Back", 
                                  command=self.create_home_page,
                                  font=ctk.CTkFont(size=14))
            back_btn.pack(side="left", padx=10)

            # Generate Staff Report button
            staff_report_btn = ctk.CTkButton(buttons_frame, 
                                         text="Generate Staff Report", 
                                         command=self.generate_staff_report,
                                         font=ctk.CTkFont(size=14))
            staff_report_btn.pack(side="left", padx=10)

            # Next button
            next_btn = ctk.CTkButton(buttons_frame, 
                                  text="Next", 
                                  command=self.save_and_preview,
                                  font=ctk.CTkFont(size=14))
            next_btn.pack(side="left", padx=10)

        except Exception as e:
            messagebox.showerror("Error", f"Error loading assessment details: {str(e)}")
            self.create_home_page()

    def generate_allotment_pdf(self):
        try:
            # Get settings for selected dates
            with open(DB_FILES['settings'], 'r') as f:
                settings = json.load(f)
                selected_dates = settings.get('dates', [])

            if not selected_dates:
                messagebox.showerror("Error", "No dates selected")
                return

            # Create output directory if it doesn't exist
            output_dir = os.path.join('data', 'allotments')
            os.makedirs(output_dir, exist_ok=True)

            # Load staff data
            with open(DB_FILES['staff'], 'r') as f:
                staff_list = json.load(f)

            # Generate allotments for each date
            self.allotments = {}
            for date_str in selected_dates:
                # Get configuration for this date
                config = self.config_manager.get_date_config(date_str)
                if not config or 'rooms' not in config:
                    continue

                # Generate allotment for this date
                self.allotments[date_str] = self.allocate_staff(staff_list.copy(), config['rooms'], date_str)

                # Generate PDF for this date
                pdf_settings = {
                    'date': date_str,
                    'assessment_name': config['settings'].get('assessment_name', ''),
                    'exam_time': config['settings'].get('exam_time', ''),
                    'reporting_time': config['settings'].get('reporting_time', '')
                }
                self.generate_pdf(self.allotments[date_str], pdf_settings)

            # Save all allotments
            with open(DB_FILES['allotment'], 'w') as f:
                json.dump(self.allotments, f, indent=4)

            messagebox.showinfo("Success", "Allotment PDFs generated successfully")
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")

    def generate_pdf(self, allotments, settings):
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.join('data', 'allotments')
            os.makedirs(output_dir, exist_ok=True)

            # Create PDF
            date_str = datetime.strptime(settings['date'], '%Y-%m-%d').strftime('%d-%m-%Y')
            pdf_path = os.path.join(output_dir, f'allotment_{date_str}.pdf')
            
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            elements = []

            # Add logo
            logo_path = r"assets\logo.jpg"
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=400, height=55)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 20))

            # Title with complete details
            month = datetime.strptime(settings['date'], '%Y-%m-%d').strftime('%B')
            year = datetime.strptime(settings['date'], '%Y-%m-%d').strftime('%Y')
            title_text = f"""Office of the Controller of Examinations<br/>{month} - {year} {settings['assessment_name']} Examination Duty List<br/>Reporting Time-{settings['reporting_time']}<br/>Date of Examination-{date_str}"""

            styles = getSampleStyleSheet()
            title_style = styles['Title']
            title_style.alignment = 1  # Center alignment
            title_style.spaceAfter = 30
            title_style.fontSize = 12
            title_style.leading = 16

            elements.append(Paragraph(title_text, title_style))

            # Create table data
            table_data = [['S. No.', 'Staff Name', 'Dept', 'Hall', 'Reporting Time', 'Signature']]
            
            # Convert allotments list to room-based dictionary if needed
            room_allotments = {}
            if isinstance(allotments, list):
                for allot in allotments:
                    room_no = allot['room_no']
                    room_allotments[room_no] = allot['staff']
            else:
                room_allotments = allotments
            
            
            idx = 1
            for room_no in room_allotments:
                staff_list = room_allotments[room_no]
                for staff in staff_list:
                    table_data.append([
                        idx,
                        staff.get('staff_name', staff.get('name', '')).strip(),
                        staff.get('staff_dept', staff.get('department', '')).strip(),
                        room_no.strip(),
                        '',  # Empty reporting time column
                        ''   # Empty signature column
                    ])
                    idx += 1
            if len(table_data) > 1:
                first_row = table_data[0]  # Store first element
                sorted_data = sorted(table_data[1:], key=lambda x: x[2])  # Sort by department
                table_data = [first_row] + sorted_data  # Reconstruct with first row unchanged

            # Update serial numbers after sorting
            for idx, row in enumerate(table_data[1:], start=1):
                row[0] = idx  # Assign new serial number

            # Create table with specific column widths
            table = Table(table_data, colWidths=[35, 140, 100, 60, 105, 85])
            
            # Add style
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Content style
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Alternate row colors
                *[('BACKGROUND', (0, i), (-1, i), colors.whitesmoke) for i in range(2, len(table_data), 2)]
            ])
            
            table.setStyle(style)
            elements.append(table)
            
            # Add signature
            signature_path = r"assets\signature.jpg"
            if os.path.exists(signature_path):
                elements.append(Spacer(1, 50))
                signature = Image(signature_path, width=100, height=50)
                signature.hAlign = 'RIGHT'
                elements.append(signature)
            
            # Build PDF
            doc.build(elements)

        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            raise

    def generate_staff_report(self):
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.join('data', 'staff_reports')
            os.makedirs(output_dir, exist_ok=True)

            # Load all staff data
            with open(DB_FILES['staff'], 'r') as f:
                staff_list = json.load(f)

            # Group staff by department
            dept_staff = {}
            for staff in staff_list:
                dept = staff.get('staff_dept', '').strip()
                if dept not in dept_staff:
                    dept_staff[dept] = []
                dept_staff[dept].append(staff)

            # Load allotments
            with open(DB_FILES['allotment'], 'r') as f:
                all_allotments = json.load(f)

            # Generate report for each department
            for dept in sorted(dept_staff.keys()):
                # Create PDF
                pdf_path = os.path.join(output_dir, f'staff_report_{dept}.pdf')
                doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                elements = []

                # Add logo
                logo_path = r"assets\logo.jpg"
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=400, height=55)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 20))

                # Add title
                title_text = f"""Office of the Controller of Examinations<br/>
                               Staff Duty Report - {dept} Department<br/>
                               {self.exam_month_var.get()} {self.assessment_name_var.get()}<br/>"""
                styles = getSampleStyleSheet()
                title_style = styles['Title']
                title_style.alignment = 1  # Center alignment
                title = Paragraph(title_text, title_style)
                elements.append(title)
                elements.append(Spacer(1, 20))

                # Get all dates
                dates = sorted(all_allotments.keys())
                
                # Calculate dates per page (considering fixed column widths and minimum date column width)
                fixed_width = 200  # Width for S.No, Name, Gender columns
                available_width = 520  # Total available width for letter size
                min_date_width = 60  # Minimum width for each date column
                dates_per_page = (available_width - fixed_width) // min_date_width
                
                # Split dates into chunks
                date_chunks = [dates[i:i + dates_per_page] for i in range(0, len(dates), dates_per_page)]
                
                # Create tables for each chunk of dates
                for page_num, date_chunk in enumerate(date_chunks):
                    if page_num > 0:
                        elements.append(PageBreak())
                        elements.append(Paragraph(title_text, title_style))
                        elements.append(Spacer(1, 20))
                    
                    # Create headers for this chunk
                    headers = ['S.No', 'Staff Name', 'Gender'] + [
                        datetime.strptime(date, '%Y-%m-%d').strftime('%d-%m-%Y') 
                        for date in date_chunk
                    ]
                    
                    # Prepare table data
                    data = [headers]
                    
                    # Add staff rows
                    for idx, staff in enumerate(sorted(dept_staff[dept], key=lambda x: x['staff_name']), 1):
                        staff_name = staff['staff_name'].strip()
                        staff_gender = staff['staff_gender'].strip()
                        
                        date_allocations = []
                        for date in date_chunk:
                            allocated = '-'
                            date_allotments = all_allotments.get(date, [])
                            if isinstance(date_allotments, dict):
                                for room_no, room_staff in date_allotments.items():
                                    for s in room_staff:
                                        if s.get('staff_name', '').strip() == staff_name:
                                            allocated = f"{room_no}"
                                            break
                                    if allocated != '-':
                                        break
                            else:
                                for allotment in date_allotments:
                                    room_no = allotment.get('room_no', '')
                                    for s in allotment.get('staff', []):
                                        if s.get('staff_name', '').strip() == staff_name:
                                            allocated = f"{room_no}"
                                            break
                                    if allocated != '-':
                                        break
                            date_allocations.append(allocated)
                        
                        row = [str(idx), staff_name, staff_gender] + date_allocations
                        data.append(row)

                    # Calculate column widths for this chunk
                    date_width = min(70, (available_width - fixed_width) / len(date_chunk))
                    col_widths = [30, 120, 50] + [date_width] * len(date_chunk)
                    
                    # Create and style table
                    table = Table(data, colWidths=col_widths)
                    table.setStyle(TableStyle([
                        # Header style
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        
                        # Content style
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        
                        # Alternate row colors
                        *[('BACKGROUND', (0, i), (-1, i), colors.whitesmoke) 
                          for i in range(2, len(data), 2)]
                    ]))
                    
                    elements.append(table)
                    
                    # Add signature only on the last page
                    if page_num == len(date_chunks) - 1:
                        signature_path = r"assets\signature.jpg"
                        if os.path.exists(signature_path):
                            elements.append(Spacer(1, 50))
                            signature = Image(signature_path, width=100, height=50)
                            signature.hAlign = 'RIGHT'
                            elements.append(signature)
                
                # Build PDF
                doc.build(elements)

            messagebox.showinfo("Success", f"Staff reports have been generated in {output_dir} folder!")
            os.startfile(output_dir)

        except Exception as e:
            print(f"Error generating staff report: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error generating staff report: {str(e)}")

    def show_room_configuration(self):
        # Clear main content area
        for widget in self.app.winfo_children():
            widget.destroy()

        # Create main container with black background
        main_container = ctk.CTkFrame(self.app, fg_color="#000000")
        main_container.pack(fill="both", expand=True)

        # Header content with black background
        header_content = ctk.CTkFrame(main_container, fg_color="#000000", height=80)
        header_content.pack(fill="x")
        header_content.grid_columnconfigure(1, weight=1)

        # Back button with white background and black border
        back_btn = ctk.CTkButton(
            header_content,
            text="← Back",
            command=self.create_home_page,
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            width=100,
            height=40,
            fg_color="#ffffff",
            text_color="#000000",
            hover_color="#f0f0f0",
            border_color="#000000",
            border_width=2,
            corner_radius=10
        )
        back_btn.grid(row=0, column=0, padx=20, pady=20)

        # Title with white text
        title_label = ctk.CTkLabel(
            header_content,
            text="ROOM CONFIGURATION",
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color="#ffffff"
        )
        title_label.grid(row=0, column=1)

        # Content area with white background
        content_frame = ctk.CTkFrame(main_container, fg_color="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create split view with 1:2 ratio
        left_panel = ctk.CTkFrame(content_frame, fg_color="#ffffff", border_color="#000000", border_width=2, corner_radius=15)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = ctk.CTkFrame(content_frame, fg_color="#ffffff", border_color="#000000", border_width=2, corner_radius=15)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Left Panel - List of Halls
        left_title = ctk.CTkLabel(
            left_panel,
            text="HALLS",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#000000"
        )
        left_title.pack(pady=(20, 10), anchor="n")

        # Create scrollable frame for halls list
        halls_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        halls_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Load halls data
        try:
            with open(DB_FILES['halls'], 'r') as f:
                halls = json.load(f)
        except:
            halls = {}

        # Add hall buttons with white background and black border
        for hall_name in sorted(halls.keys()):
            hall_btn = ctk.CTkButton(
                halls_scroll,
                text=hall_name,
                command=lambda h=hall_name: self.refresh_hall_details(h, right_panel),
                height=40,
                font=ctk.CTkFont(family="Arial", size=14),
                fg_color="#ffffff",
                text_color="#000000",
                hover_color="#f0f0f0",
                border_color="#000000",
                border_width=2,
                corner_radius=8
            )
            hall_btn.pack(fill="x", pady=5)

        # Add "Add Hall" button at the bottom of left panel
        add_hall_btn = ctk.CTkButton(
            left_panel,
            text="+ Add New Hall",
            command=lambda: self.show_add_hall_form(halls_scroll, right_panel),
            height=40,
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            fg_color="#ffffff",
            text_color="#000000",
            hover_color="#f0f0f0",
            border_color="#000000",
            border_width=2,
            corner_radius=10
        )
        add_hall_btn.pack(fill="x", padx=10, pady=10)

        # Right Panel - Initial Message
        welcome_label = ctk.CTkLabel(
            right_panel,
            text="Select a hall from the left panel\nor add a new hall to begin",
            font=ctk.CTkFont(family="Arial", size=16),
            text_color="#000000",
            justify="center"
        )
        welcome_label.pack(anchor="n", pady=20)

    def refresh_hall_details(self, hall_name, right_panel):
        # Clear right panel
        for widget in right_panel.winfo_children():
            widget.destroy()

        try:
            # Load halls data
            with open(DB_FILES['halls'], 'r') as f:
                self.buildings = json.load(f)  # Load into self.buildings to maintain compatibility

            # Create title frame at the top
            title_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
            title_frame.pack(fill="x", padx=20, pady=(20,10), anchor="n")

            # Add hall name title
            title = ctk.CTkLabel(
                title_frame,
                text=f"{hall_name} Configuration",
                font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
                text_color="#000000"
            )
            title.pack(side="left")

            # Add delete hall button
            delete_hall_btn = ctk.CTkButton(
                title_frame,
                text="Delete Hall",
                command=lambda: self.delete_hall(hall_name, right_panel),
                fg_color="#ffffff",
                text_color="#000000",
                hover_color="#f0f0f0",
                border_color="#FF0000",
                border_width=2,
                corner_radius=8,
                width=120,
                height=35,
                font=ctk.CTkFont(family="Arial", size=14)
            )
            delete_hall_btn.pack(side="right")

            # Create content frame
            content_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=20, pady=(0,20))

            # Create scrollable frame for rooms
            rooms_frame = ctk.CTkScrollableFrame(content_frame, fg_color="transparent")
            rooms_frame.pack(fill="both", expand=True)

            # Add rooms list
            if hall_name in self.buildings:  # Using self.buildings which now has data from halls.json
                rooms = self.buildings[hall_name]
                for room in sorted(rooms):
                    room_frame = ctk.CTkFrame(rooms_frame, fg_color="#ffffff", border_color="#000000", border_width=1, corner_radius=8)
                    room_frame.pack(fill="x", padx=5, pady=5)

                    room_label = ctk.CTkLabel(
                        room_frame,
                        text=room,
                        font=ctk.CTkFont(family="Arial", size=14),
                        text_color="#000000"
                    )
                    room_label.pack(side="left", padx=10, pady=10)

                    delete_btn = ctk.CTkButton(
                        room_frame,
                        text="Delete",
                        command=lambda r=room: self.delete_room(hall_name, r, right_panel),
                        fg_color="#ffffff",
                        text_color="#000000",
                        hover_color="#f0f0f0",
                        border_color="#FF0000",
                        border_width=2,
                        corner_radius=8,
                        width=80,
                        height=30,
                        font=ctk.CTkFont(family="Arial", size=12)
                    )
                    delete_btn.pack(side="right", padx=10, pady=10)

            # Add new room section at the bottom
            add_room_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            add_room_frame.pack(fill="x", pady=(20,0))

            room_var = tk.StringVar()
            room_entry = ctk.CTkEntry(
                add_room_frame,
                textvariable=room_var,
                placeholder_text="Enter room number",
                width=200,
                height=35,
                font=ctk.CTkFont(family="Arial", size=14),
                border_color="#000000",
                border_width=2
            )
            room_entry.pack(side="left", padx=(0,10))

            add_btn = ctk.CTkButton(
                add_room_frame,
                text="+ Add Room",
                command=lambda: self.add_room(hall_name, room_var, right_panel),
                width=120,
                height=35,
                font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                fg_color="#ffffff",
                text_color="#000000",
                hover_color="#f0f0f0",
                border_color="#000000",
                border_width=2,
                corner_radius=8
            )
            add_btn.pack(side="left")

        except Exception as e:
            print(f"Error refreshing hall details: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh hall details: {str(e)}")

    def delete_room(self, hall_name, room, right_panel):
        try:
            with open(DB_FILES['halls'], 'r') as f:
                halls = json.load(f)
            
            if hall_name in halls and room in halls[hall_name]:
                halls[hall_name].remove(room)
                
                with open(DB_FILES['halls'], 'w') as f:
                    json.dump(halls, f, indent=4)
                
                self.refresh_hall_details(hall_name, right_panel)
                messagebox.showinfo("Success", f"Room {room} has been deleted from {hall_name}")
            else:
                messagebox.showerror("Error", "Room not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete room: {str(e)}")

    def add_room(self, hall_name, room_var, right_panel):
        room = room_var.get().strip()
        
        if not room:
            messagebox.showerror("Error", "Please enter a room number")
            return
            
        try:
            with open(DB_FILES['halls'], 'r') as f:
                halls = json.load(f)
            
            if hall_name not in halls:
                halls[hall_name] = []
                
            if room in halls[hall_name]:
                messagebox.showerror("Error", f"Room {room} already exists in {hall_name}")
                return
                
            halls[hall_name].append(room)
            
            with open(DB_FILES['halls'], 'w') as f:
                json.dump(halls, f, indent=4)
            
            room_var.set("")  # Clear the entry
            self.refresh_hall_details(hall_name, right_panel)
            messagebox.showinfo("Success", f"Room {room} has been added to {hall_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add room: {str(e)}")    

    def show_add_hall_form(self, halls_scroll, right_panel):
        # Clear right panel
        for widget in right_panel.winfo_children():
            widget.destroy()

        # Configure grid for right panel
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)

        # Create form container with white background
        form_frame = ctk.CTkFrame(right_panel, fg_color="#ffffff")
        form_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=30)
        form_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            form_frame,
            text="Add New Hall",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#000000"
        )
        title.grid(row=0, column=0, columnspan=2, pady=(20, 20))

        # Input frame
        input_frame = ctk.CTkFrame(form_frame, fg_color="#ffffff")
        input_frame.grid(row=1, column=0, sticky="ew", pady=10)
        input_frame.grid_columnconfigure(1, weight=1)  # Make text box column expandable

        # Hall name input with label next to text box
        name_label = ctk.CTkLabel(input_frame,
                              text="Hall Name",
                              font=ctk.CTkFont(family="Arial", size=14),
                              text_color="#000000")
        name_label.grid(row=0, column=0, padx=(0, 10), pady=10)

        name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(input_frame,
                              textvariable=name_var,
                              placeholder_text="Enter hall name",
                              width=300,
                              height=40,
                              font=ctk.CTkFont(family="Arial", size=14),
                              border_color="#000000",
                              border_width=2)
        name_entry.grid(row=0, column=1, sticky="w", pady=10)

        # Add buttons frame
        button_frame = ctk.CTkFrame(input_frame, fg_color="#ffffff")
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Create Hall button with white background and black border
        add_btn = ctk.CTkButton(button_frame,
                            text="Create Hall",
                            command=lambda: self.add_hall(hall_name=name_var, halls_scroll=halls_scroll, right_panel=right_panel),
                            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
                            width=140,
                            height=40,
                            fg_color="#ffffff",
                            text_color="#000000",
                            hover_color="#f0f0f0",
                            border_color="#000000",
                            border_width=2,
                            corner_radius=8)
        add_btn.grid(row=0, column=0, padx=5)

        # Cancel button with white background and gray border
        cancel_btn = ctk.CTkButton(button_frame,
                               text="Cancel",
                               command=lambda: self.refresh_hall_details(None, right_panel),
                               font=ctk.CTkFont(family="Arial", size=14),
                               width=140,
                               height=40,
                               fg_color="#ffffff",
                               text_color="#000000",
                               hover_color="#f0f0f0",
                               border_color="#666666",
                               border_width=2,
                               corner_radius=8)
        cancel_btn.grid(row=0, column=1, padx=5)    

    def add_hall(self, hall_name, halls_scroll, right_panel):
        hall_name = hall_name.get().strip()
        
        if not hall_name:
            messagebox.showerror("Error", "Please enter a hall name")
            return
            
        try:
            with open(DB_FILES['halls'], 'r') as f:
                halls = json.load(f)
            
            if hall_name in halls:
                messagebox.showerror("Error", f"Hall '{hall_name}' already exists")
                return
                
            halls[hall_name] = []
            
            with open(DB_FILES['halls'], 'w') as f:
                json.dump(halls, f, indent=4)
            
            # Add new hall button to the list with white background and black border
            hall_btn = ctk.CTkButton(halls_scroll,
                                 text=hall_name,
                                 command=lambda h=hall_name: self.refresh_hall_details(h, right_panel),
                                 font=ctk.CTkFont(family="Arial", size=14),
                                 height=40,
                                 fg_color="#ffffff",
                                 text_color="#000000",
                                 hover_color="#f0f0f0",
                                 border_color="#000000",
                                 border_width=2,
                                 corner_radius=8)
            hall_btn.pack(fill="x", pady=5, padx=10)

            # Show the new hall's details
            self.refresh_hall_details(hall_name, right_panel)
            
            messagebox.showinfo("Success", f"Hall '{hall_name}' has been created")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create hall: {str(e)}")    

    def delete_hall(self, hall_name, right_panel):
        try:
            # Check if hall has any classes assigned
            with open(DB_FILES['allotment'], 'r') as f:
                allotment = json.load(f)
                
            hall_has_classes = False
            if isinstance(allotment, dict):  # Make sure allotment is a dictionary
                for class_name, data in allotment.items():
                    if isinstance(data, dict) and data.get('hall') == hall_name:  # Check if data is a dictionary and has 'hall'
                        hall_has_classes = True
                        break
            
            if hall_has_classes:
                messagebox.showerror("Error", f"Cannot delete hall '{hall_name}' as it has classes assigned to it")
                return
            
            # Delete hall from halls.json
            with open(DB_FILES['halls'], 'r') as f:
                halls = json.load(f)
            
            if hall_name in halls:
                del halls[hall_name]
                
                with open(DB_FILES['halls'], 'w') as f:
                    json.dump(halls, f, indent=4)
                
                # Refresh the halls list
                self.show_room_configuration()
                
                messagebox.showinfo("Success", f"Hall '{hall_name}' has been deleted")
            else:
                messagebox.showerror("Error", f"Hall '{hall_name}' not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete hall: {str(e)}")    

    def generate_both(self):
        """Generate both allotment PDF and staff report"""
        try:
            # Validate inputs first
            assessment_name = self.assessment_name_var.get().strip()
            exam_time = self.exam_month_var.get().strip()
            reporting_time = self.reporting_time_var.get().strip()

            if not all([assessment_name, exam_time, reporting_time]):
                messagebox.showerror("Error", "Please fill in all fields")
                return

            # Save configuration for all dates
            for date in self.config_manager.get_configured_dates():
                config = self.config_manager.get_date_config(date)
                if config:
                    config['settings'] = {
                        'assessment_name': assessment_name,
                        'exam_time': exam_time,
                        'reporting_time': reporting_time
                    }
                    self.config_manager.set_date_config(date, config)

            # Generate both PDFs
            self.generate_allotment_pdf()
            self.generate_staff_report()
            
            messagebox.showinfo("Success", "Both PDFs have been generated successfully!")
            
            # Open the output directory
            output_dir = os.path.join('data')
            if os.path.exists(output_dir):
                os.startfile(output_dir)
                
        except Exception as e:
            print(f"Error generating PDFs: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to generate PDFs: {str(e)}")

    def run(self):
        self.app.mainloop()

    def update_requirements(self):
        """Update the required staff counts based on selected class configurations"""
        try:
            total_req = 0
            female_req = 0
            
            # Count requirements based on selected classes and modifiers
            for class_name, modifiers in self.class_modifiers.items():
                if modifiers['selected'].get():
                    if modifiers['single_staff'].get():
                        total_req += 1
                        if modifiers['girls_only'].get():
                            female_req += 1
                    else:
                        total_req += 2
                        if modifiers['girls_only'].get():
                            female_req += 2
            
            male_pos = total_req - female_req
            
            # Update labels with new counts
            if hasattr(self, 'required_total_label'):
                self.required_total_label.configure(text=str(total_req))
                
            if hasattr(self, 'required_female_label'):
                self.required_female_label.configure(text=f"{female_req}")
                
            if hasattr(self, 'required_male_label'):
                self.required_male_label.configure(text=f"{male_pos}")

        except Exception as e:
            print(f"Error updating requirements: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")

    def save_configuration(self):
        """Save the class configuration for selected dates"""
        try:
            # Get selected classes with their modifiers
            config = {
                'rooms': []
            }

            for class_name, modifiers in self.class_modifiers.items():
                if modifiers['selected'].get():
                    config['rooms'].append({
                        'room_no': class_name,
                        'girls_only': modifiers['girls_only'].get(),
                        'single_staff': modifiers['single_staff'].get()
                    })

            if not config['rooms']:
                messagebox.showerror("Error", "No classes configured")
                return

            # Show date selection dialog
            date_dialog = DateSelectionDialog(self.app, self.selected_dates)
            self.app.wait_window(date_dialog)
            
            if date_dialog.selected_dates:
                # Save configuration for selected dates
                for date in date_dialog.selected_dates:
                    config = self.config_manager.get_date_config(date)
                    if config:
                        config['settings'] = {
                            'reporting_time': '',
                            'assessment_name': '',
                            'exam_time': '',
                            'exam_details': ''
                        }
                    else:
                        config = {
                            'rooms': [],
                            'settings': {
                                'reporting_time': '',
                                'assessment_name': '',
                                'exam_time': '',
                                'exam_details': ''
                            }
                        }
                    config['rooms'] = [
                        {
                            'room_no': class_name,
                            'girls_only': modifiers['girls_only'].get(),
                            'single_staff': modifiers['single_staff'].get()
                        } for class_name, modifiers in self.class_modifiers.items() 
                        if modifiers['selected'].get()
                    ]
                    self.config_manager.set_date_config(date, config)

                # Remove configured dates from selected_dates
                for date in date_dialog.selected_dates:
                    if date in self.selected_dates:
                        self.selected_dates.remove(date)
                
                if not self.selected_dates:
                    # All dates configured, move to add details
                    self.add_exam_details()
                else:
                    # More dates to configure, refresh the page
                    self.configure_selected_classes()

                messagebox.showinfo("Success", "Configuration saved successfully!")

        except Exception as e:
            print(f"Error in save_configuration: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def download_template(self):
        """Download Excel template for staff details"""
        try:
            # Template structure
            template_data = {
                'staff_name': ['Example: John Doe'],
                'staff_dept': ['Example: CSE'],
                'staff_gender': ['Example: M/F']
            }
            df = pd.DataFrame(template_data)
            
            # Get save location
            file_path = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Template As",
                initialfile="staff_template.xlsx"
            )
            
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", "Template downloaded successfully!")
        
        except Exception as e:
            print(f"Error downloading template: {str(e)}")
            messagebox.showerror("Error", f"Failed to download template: {str(e)}")

    def upload_staff_file(self):
        """Upload and process staff details from Excel file with multiple department sheets"""
        try:
            # Get file path
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls")],
                title="Select Staff Details File"
            )
            
            if not file_path:
                return

            # Read all sheet names from the Excel file
            xl = pd.ExcelFile(file_path)
            departments = xl.sheet_names
            
            staff_data = []
            
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Process each department sheet
            for dept in departments:
                try:
                    df = pd.read_excel(file_path, sheet_name=dept)
                    if df.empty:
                        continue  # Skip empty sheets
                    
                    # Validate columns
                    if not all(col in df.columns for col in ['Name', 'Gender']):
                        messagebox.showerror(
                            "Error", 
                            f"Invalid format in {dept} sheet. Required columns: Name, Gender"
                        )
                        return

                    # Convert DataFrame to list of dictionaries
                    for index, row in df.iterrows():
                        staff_member = {
                            'staff_name': str(row['Name']).strip(),
                            'staff_dept': dept.strip(),  # Use sheet name as department name
                            'staff_gender': str(row['Gender']).strip().upper()
                        }
                        
                        # Normalize gender values
                        if staff_member['staff_gender'] in ['M', 'MALE', 'MR']:
                            staff_member['staff_gender'] = 'M'
                        elif staff_member['staff_gender'] in ['F', 'FEMALE', 'MS', 'MRS']:
                            staff_member['staff_gender'] = 'F'
                        
                        # Only add if we have valid name and gender
                        if staff_member['staff_name'] and staff_member['staff_gender'] in ['M', 'F']:
                            staff_data.append(staff_member)
                            
                except ValueError:
                    continue  # Skip if sheet does not exist
                except Exception as e:
                    print(f"Error processing {dept} sheet: {str(e)}")
                    continue
            
            if not staff_data:
                messagebox.showerror(
                    "Error", 
                    "No valid staff data found in the Excel file. Please check the file format."
                )
                return
            
            # Save to JSON file
            with open('data/staff.json', 'w') as f:
                json.dump(staff_data, f, indent=4)
            
            messagebox.showinfo(
                "Success", 
                f"Staff details uploaded successfully! {len(staff_data)} staff members imported."
            )
            
            # Return to home page
            self.create_home_page()
        
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", "The selected file is empty")
        except Exception as e:
            print(f"Error uploading staff details: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to upload staff details: {str(e)}")

    def upload_staff_details(self):
        """Create the upload staff details page"""
        try:
            # Clear existing widgets
            for widget in self.app.winfo_children():
                widget.destroy()

            # Create main container
            main_container = ctk.CTkFrame(self.app, fg_color="transparent")
            main_container.pack(fill="both", expand=True, padx=40, pady=30)

            # Add header
            self.create_header(main_container, "UPLOAD STAFF DETAILS")

            # Content frame with border
            content_frame = ctk.CTkFrame(
                main_container,
                fg_color=self.UI_THEME['content_bg'],
                corner_radius=15,
                border_width=2,
                border_color=self.UI_THEME['button_border']
            )
            content_frame.pack(fill="both", expand=True, padx=20)

            # Instructions section
            instruction_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            instruction_frame.pack(fill="x", padx=40, pady=(30, 20))

            # Instructions title
            ctk.CTkLabel(
                instruction_frame,
                text="Instructions:",
                font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                text_color=self.UI_THEME['button_fg']
            ).pack(anchor="w", pady=(0, 10))

            # Instructions
            instructions = [
                "1. Download the template Excel file",
                "2. Fill in the staff details in the template:",
                "   • staff_name: Full name of the staff member",
                "   • staff_dept: Department name (e.g., CSE, ECE)",
                "   • staff_gender: Gender (M/F or MALE/FEMALE)",
                "3. Save the Excel file after filling details",
                "4. Upload the filled Excel file using the button below"
            ]

            for instruction in instructions:
                ctk.CTkLabel(
                    instruction_frame,
                    text=instruction,
                    font=ctk.CTkFont(family="Arial", size=14),
                    text_color=self.UI_THEME['button_fg']
                ).pack(anchor="w", pady=5)

            # Button frame
            button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            button_frame.pack(fill="x", padx=40, pady=30)

            # Button style
            button_style = {
                "font": ctk.CTkFont(family="Arial", size=14, weight="bold"),
                "width": 200,
                "height": 40,
                "corner_radius": 8,
                "border_width": 2,
                "border_color": self.UI_THEME['button_border']
            }

            # Download Template button
            download_btn = ctk.CTkButton(
                button_frame,
                text="↓ Download Template",
                command=self.download_template,  # Direct method reference, no lambda
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                **button_style
            )
            download_btn.pack(pady=10)

            # Upload File button
            upload_btn = ctk.CTkButton(
                button_frame,
                text="↑ Upload Staff Details",
                command=self.upload_staff_file,  # Direct method reference, no lambda
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                **button_style
            )
            upload_btn.pack(pady=10)

            # Back button
            back_btn = ctk.CTkButton(
                button_frame,
                text="← Back",
                command=self.create_home_page,  # Direct method reference, no lambda
                fg_color=self.UI_THEME['button_bg'],
                text_color=self.UI_THEME['button_fg'],
                hover_color=self.UI_THEME['button_hover'],
                **button_style
            )
            back_btn.pack(pady=10)

        except Exception as e:
            print(f"Error in upload_staff_details: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error in upload staff details: {str(e)}")

if __name__ == "__main__":
    app = ExamDutyApp()
    app.run()
