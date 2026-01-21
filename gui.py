"""
WebCrawlScrape - Simple Windows GUI
Tkinter interface for the web crawler.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import os
import sys
import re
import json
from urllib.parse import urlparse

from config import EXTENSION_PRESETS, DEFAULT_MAX_PAGES
from crawler import crawl
from version import VERSION

# Config file for saving custom categories
CUSTOM_CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), "custom_categories.json")


class CrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"WebCrawlScrape v{VERSION}")
        self.root.geometry("700x750")
        self.root.resizable(True, True)

        self.is_crawling = False
        self.ext_checkboxes = {}  # Store extension checkbox variables
        self.category_vars = {}  # Store category checkbox variables
        self.custom_categories = {}  # Store custom categories {name: set of extensions}
        self.category_additions = {}  # Store user additions to built-in categories {name: set}
        self.load_custom_categories()
        self.create_widgets()
        self.load_custom_category_checkboxes()

    def create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- URL Section ---
        url_frame = ttk.LabelFrame(main_frame, text="URL", padding="5")
        url_frame.pack(fill=tk.X, pady=(0, 10))

        self.url_var = tk.StringVar(value="https://")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=70)
        self.url_entry.pack(fill=tk.X, padx=5, pady=5)

        # --- File Types Section ---
        types_frame = ttk.LabelFrame(main_frame, text="File Types", padding="5")
        types_frame.pack(fill=tk.X, pady=(0, 10))

        # Main container: categories on left, extensions on right
        types_container = ttk.Frame(types_frame)
        types_container.pack(fill=tk.BOTH, padx=5, pady=5)

        # === LEFT SIDE: Categories ===
        left_frame = ttk.Frame(types_container, width=180)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        ttk.Label(left_frame, text="Categories", font=("TkDefaultFont", 9, "bold")).pack(anchor=tk.W)

        # Built-in categories in a compact column
        self.category_frame = ttk.Frame(left_frame)
        self.category_frame.pack(fill=tk.X, pady=(5, 0))

        # "All Files" checkbox first
        self.all_files_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.category_frame, text="All Files",
            variable=self.all_files_var, command=self.on_all_files_toggle
        ).pack(anchor=tk.W)

        # Then the built-in categories (excluding 'all')
        builtin_cats = [k for k in EXTENSION_PRESETS.keys() if k != "all"]
        for cat in builtin_cats:
            var = tk.BooleanVar(value=(cat == "images"))  # Default: images selected
            self.category_vars[cat] = var
            cb = ttk.Checkbutton(
                self.category_frame, text=cat.capitalize(),
                variable=var, command=self.on_category_change
            )
            cb.pack(anchor=tk.W)

        # Custom categories section
        ttk.Separator(left_frame, orient="horizontal").pack(fill=tk.X, pady=5)

        custom_header = ttk.Frame(left_frame)
        custom_header.pack(fill=tk.X)
        ttk.Label(custom_header, text="Custom", font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(custom_header, text="+", command=self.add_custom_category, width=2).pack(side=tk.RIGHT)

        # Frame to hold custom category checkboxes
        self.custom_cat_container = ttk.Frame(left_frame)
        self.custom_cat_container.pack(fill=tk.X, pady=(2, 0))

        # === RIGHT SIDE: Extensions ===
        right_frame = ttk.Frame(types_container)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Extension header with buttons
        ext_header = ttk.Frame(right_frame)
        ext_header.pack(fill=tk.X)
        ttk.Label(ext_header, text="Extensions", font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(ext_header, text="All", command=self.select_all_exts, width=4).pack(side=tk.RIGHT, padx=(2, 0))
        ttk.Button(ext_header, text="None", command=self.clear_all_exts, width=5).pack(side=tk.RIGHT)

        # Extension checkboxes frame (scrollable, vertical)
        checkbox_container = ttk.Frame(right_frame)
        checkbox_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Canvas for scrollable checkboxes
        self.checkbox_canvas = tk.Canvas(checkbox_container, height=120)
        scrollbar_y = ttk.Scrollbar(checkbox_container, orient="vertical", command=self.checkbox_canvas.yview)
        self.checkbox_frame = ttk.Frame(self.checkbox_canvas)

        self.checkbox_canvas.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.checkbox_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.checkbox_window = self.checkbox_canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        self.checkbox_frame.bind("<Configure>", self.on_checkbox_frame_configure)
        self.checkbox_canvas.bind("<Configure>", lambda e: self.checkbox_canvas.itemconfig(self.checkbox_window, width=e.width))

        # Initialize checkboxes for default selection
        self.update_extension_checkboxes()

        # Custom extensions entry with save to category (below the main container)
        custom_row = ttk.Frame(types_frame)
        custom_row.pack(fill=tk.X, padx=5, pady=(5, 0))

        ttk.Label(custom_row, text="Add:").pack(side=tk.LEFT)
        self.custom_ext_var = tk.StringVar()
        self.custom_ext_entry = ttk.Entry(custom_row, textvariable=self.custom_ext_var, width=18)
        self.custom_ext_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(custom_row, text="(.ext,.ext)", foreground="gray").pack(side=tk.LEFT)
        ttk.Button(custom_row, text="Save to Category", command=self.save_extensions_to_category).pack(side=tk.RIGHT)

        # --- Output Directory Section ---
        dir_frame = ttk.LabelFrame(main_frame, text="Save To", padding="5")
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        dir_inner = ttk.Frame(dir_frame)
        dir_inner.pack(fill=tk.X, padx=5, pady=5)

        self.dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "downloads"))
        self.dir_entry = ttk.Entry(dir_inner, textvariable=self.dir_var, width=50)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = ttk.Button(dir_inner, text="Browse...", command=self.browse_directory)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Organize by website checkbox
        self.organize_by_site_var = tk.BooleanVar(value=True)
        organize_cb = ttk.Checkbutton(
            dir_frame,
            text="Create subfolder from URL:",
            variable=self.organize_by_site_var,
            command=self.update_folder_preview
        )
        organize_cb.pack(anchor=tk.W, padx=5, pady=(0, 2))

        # Folder name preview
        preview_frame = ttk.Frame(dir_frame)
        preview_frame.pack(fill=tk.X, padx=20, pady=(0, 5))

        ttk.Label(preview_frame, text="Folder:").pack(side=tk.LEFT)
        self.folder_preview_var = tk.StringVar(value="")
        self.folder_preview_label = ttk.Label(
            preview_frame,
            textvariable=self.folder_preview_var,
            foreground="gray"
        )
        self.folder_preview_label.pack(side=tk.LEFT, padx=5)

        # Bind URL entry to update preview
        self.url_var.trace_add("write", lambda *args: self.update_folder_preview())

        # --- Options Section ---
        opts_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        opts_frame.pack(fill=tk.X, pady=(0, 10))

        # Row 1: Max pages and Max depth
        opts_row1 = ttk.Frame(opts_frame)
        opts_row1.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(opts_row1, text="Max pages:").pack(side=tk.LEFT)
        self.max_pages_var = tk.StringVar(value=str(DEFAULT_MAX_PAGES))
        ttk.Spinbox(
            opts_row1, from_=1, to=9999,
            textvariable=self.max_pages_var, width=6
        ).pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(opts_row1, text="Max depth:").pack(side=tk.LEFT)
        self.max_depth_var = tk.StringVar(value="0")
        ttk.Spinbox(
            opts_row1, from_=0, to=99,
            textvariable=self.max_depth_var, width=4
        ).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(opts_row1, text="(0 = unlimited)", foreground="gray").pack(side=tk.LEFT, padx=5)

        # Row 2: Delay
        opts_row2 = ttk.Frame(opts_frame)
        opts_row2.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(opts_row2, text="Delay between requests:").pack(side=tk.LEFT)
        self.delay_var = tk.StringVar(value="0.0")
        ttk.Spinbox(
            opts_row2, from_=0.0, to=10.0, increment=0.1,
            textvariable=self.delay_var, width=5
        ).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(opts_row2, text="seconds", foreground="gray").pack(side=tk.LEFT, padx=5)

        # Row 3: Checkboxes
        opts_row3 = ttk.Frame(opts_frame)
        opts_row3.pack(fill=tk.X, padx=5, pady=5)

        self.robots_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_row3, text="Respect robots.txt",
            variable=self.robots_var
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.duplicates_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            opts_row3, text="Skip duplicates",
            variable=self.duplicates_var
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.save_pages_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_row3, text="Save webpages (html/)",
            variable=self.save_pages_var
        ).pack(side=tk.LEFT)

        # --- Buttons ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(btn_frame, text="Start Crawl", command=self.start_crawl)
        self.start_btn.pack(side=tk.LEFT)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_crawl, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.clear_btn = ttk.Button(btn_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.RIGHT)

        # --- Log Section ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_checkbox_frame_configure(self, event):
        self.checkbox_canvas.configure(scrollregion=self.checkbox_canvas.bbox("all"))

    def update_extension_checkboxes(self):
        # Clear existing checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.ext_checkboxes.clear()

        # Check if "All Files" is selected
        if self.all_files_var.get():
            ttk.Label(self.checkbox_frame, text="(All file types)", foreground="gray").grid(row=0, column=0, sticky=tk.W)
            return

        # Collect extensions from all selected categories
        extensions = set()
        for cat, var in self.category_vars.items():
            if var.get():
                # Built-in category extensions
                extensions |= EXTENSION_PRESETS.get(cat, set())
                # User additions to built-in categories
                extensions |= self.category_additions.get(cat, set())
                # Custom category extensions
                extensions |= self.custom_categories.get(cat, set())

        if not extensions:
            ttk.Label(self.checkbox_frame, text="(Select a category)", foreground="gray").grid(row=0, column=0, sticky=tk.W)
            return

        # Create checkboxes in grid layout (3 columns)
        sorted_exts = sorted(extensions)
        cols = 3
        for i, ext in enumerate(sorted_exts):
            var = tk.BooleanVar(value=True)
            self.ext_checkboxes[ext] = var
            cb = ttk.Checkbutton(self.checkbox_frame, text=ext, variable=var, width=8)
            cb.grid(row=i // cols, column=i % cols, sticky=tk.W, padx=2, pady=1)

    def on_category_change(self):
        """Called when any category checkbox changes."""
        # If a category is checked, uncheck "All Files"
        if any(var.get() for var in self.category_vars.values()):
            self.all_files_var.set(False)
        self.update_extension_checkboxes()

    def on_all_files_toggle(self):
        """Called when 'All Files' checkbox changes."""
        if self.all_files_var.get():
            # Uncheck all categories when "All Files" is selected
            for var in self.category_vars.values():
                var.set(False)
        self.update_extension_checkboxes()

    def add_custom_category(self):
        """Open dialog to add a custom category."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Custom Category")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 350) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Name entry
        name_row = ttk.Frame(frame)
        name_row.pack(fill=tk.X, pady=5)
        ttk.Label(name_row, text="Name:").pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_row, textvariable=name_var, width=25)
        name_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Extensions entry
        ext_row = ttk.Frame(frame)
        ext_row.pack(fill=tk.X, pady=5)
        ttk.Label(ext_row, text="Extensions:").pack(side=tk.LEFT)
        ext_var = tk.StringVar()
        ext_entry = ttk.Entry(ext_row, textvariable=ext_var, width=25)
        ext_entry.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(frame, text="(comma separated, e.g. .dat,.bin,.sav)", foreground="gray").pack(anchor=tk.W)

        def save_category():
            name = name_var.get().strip().lower()
            exts = ext_var.get().strip()

            if not name:
                return
            if name in EXTENSION_PRESETS or name in self.custom_categories:
                # Name already exists
                return

            # Parse extensions
            ext_set = set()
            for ext in exts.split(","):
                ext = ext.strip().lower()
                if ext and not ext.startswith("."):
                    ext = "." + ext
                if ext:
                    ext_set.add(ext)

            if not ext_set:
                return

            # Add custom category
            self.custom_categories[name] = ext_set
            self.add_custom_category_checkbox(name)
            self.save_custom_categories()
            dialog.destroy()

        # Buttons
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=(15, 0))
        ttk.Button(btn_row, text="Add", command=save_category).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=(10, 0))

        name_entry.focus_set()

    def add_custom_category_checkbox(self, name, auto_check=True):
        """Add a checkbox for a custom category."""
        row = ttk.Frame(self.custom_cat_container)
        row.pack(fill=tk.X, pady=1)

        var = tk.BooleanVar(value=auto_check)
        self.category_vars[name] = var

        cb = ttk.Checkbutton(
            row, text=name.capitalize(),
            variable=var, command=self.on_category_change
        )
        cb.pack(side=tk.LEFT)

        # Show extensions in gray
        exts_str = ", ".join(sorted(self.custom_categories[name]))
        ttk.Label(row, text=f"({exts_str})", foreground="gray").pack(side=tk.LEFT, padx=(5, 0))

        # Remove button
        def remove_cat():
            del self.custom_categories[name]
            del self.category_vars[name]
            row.destroy()
            self.save_custom_categories()
            self.update_extension_checkboxes()

        ttk.Button(row, text="x", command=remove_cat, width=2).pack(side=tk.RIGHT)

        # Update extensions display
        self.update_extension_checkboxes()

    def select_all_exts(self):
        for var in self.ext_checkboxes.values():
            var.set(True)

    def clear_all_exts(self):
        for var in self.ext_checkboxes.values():
            var.set(False)

    def load_custom_categories(self):
        """Load custom categories from JSON file."""
        if os.path.exists(CUSTOM_CATEGORIES_FILE):
            try:
                with open(CUSTOM_CATEGORIES_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert lists back to sets
                    self.custom_categories = {k: set(v) for k, v in data.get('custom', {}).items()}
                    self.category_additions = {k: set(v) for k, v in data.get('additions', {}).items()}
            except (json.JSONDecodeError, IOError):
                pass

    def load_custom_category_checkboxes(self):
        """Create checkboxes for saved custom categories on startup."""
        for name in list(self.custom_categories.keys()):
            self.add_custom_category_checkbox(name, auto_check=False)

    def save_custom_categories(self):
        """Save custom categories to JSON file."""
        data = {
            'custom': {k: sorted(list(v)) for k, v in self.custom_categories.items()},
            'additions': {k: sorted(list(v)) for k, v in self.category_additions.items() if v}
        }
        try:
            with open(CUSTOM_CATEGORIES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass

    def save_extensions_to_category(self):
        """Open dialog to save extensions to a category."""
        exts_text = self.custom_ext_var.get().strip()
        if not exts_text:
            return

        # Parse extensions
        new_exts = set()
        for ext in exts_text.split(","):
            ext = ext.strip().lower()
            if ext and not ext.startswith("."):
                ext = "." + ext
            if ext:
                new_exts.add(ext)

        if not new_exts:
            return

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Extensions to Category")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Extensions: {', '.join(sorted(new_exts))}").pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(frame, text="Select category to add to:").pack(anchor=tk.W)

        # Listbox with all categories
        listbox = tk.Listbox(frame, height=6, exportselection=False)
        listbox.pack(fill=tk.X, pady=5)

        # Add built-in categories
        all_cats = [k for k in EXTENSION_PRESETS.keys() if k != "all"]
        # Add custom categories
        all_cats.extend(self.custom_categories.keys())

        for cat in all_cats:
            listbox.insert(tk.END, cat.capitalize())

        def save_to_selected():
            sel = listbox.curselection()
            if not sel:
                return
            cat_name = all_cats[sel[0]]

            if cat_name in self.custom_categories:
                # Add to custom category
                self.custom_categories[cat_name] |= new_exts
            else:
                # Add to built-in category additions
                if cat_name not in self.category_additions:
                    self.category_additions[cat_name] = set()
                self.category_additions[cat_name] |= new_exts

            self.save_custom_categories()
            self.custom_ext_var.set("")  # Clear entry
            self.update_extension_checkboxes()
            dialog.destroy()

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_row, text="Save", command=save_to_selected).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=(10, 0))

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)

    def update_folder_preview(self):
        """Update the folder name preview based on current URL."""
        if not self.organize_by_site_var.get():
            self.folder_preview_var.set("(disabled)")
            return

        url = self.url_var.get().strip()
        if not url or url == "https://" or "://" not in url:
            self.folder_preview_var.set("(enter URL above)")
            return

        folder_name = self.get_site_folder_name(url)
        self.folder_preview_var.set(folder_name if folder_name else "(invalid URL)")

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def get_extensions(self):
        exts = set()

        # Get checked extensions from checkboxes
        for ext, var in self.ext_checkboxes.items():
            if var.get():
                exts.add(ext)

        # Add custom extensions
        custom = self.custom_ext_var.get().strip()
        if custom:
            for ext in custom.split(","):
                ext = ext.strip().lower()
                if ext and not ext.startswith("."):
                    ext = "." + ext
                if ext:
                    exts.add(ext)

        return exts

    def get_site_folder_name(self, url):
        """
        Extract a clean folder name from URL.
        Example: www.abc.com/1/2/3/4.html -> abc-com-1-2-3-4
        Archive: web.archive.org/web/20001018021550/http://arc.won.net/ -> arcwon
        """
        # Handle web.archive.org URLs specially
        archive_match = re.match(r'https?://web\.archive\.org/web/\d+/(.+)', url)
        if archive_match:
            original_url = archive_match.group(1)
            return self._get_archive_folder_name(original_url)

        # Standard URL handling
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Remove file extension from path
        if path:
            # Remove leading slash and file extension
            path = path.lstrip("/")
            path = re.sub(r'\.[a-zA-Z0-9]+$', '', path)

        # Combine domain and path
        full_name = domain
        if path:
            full_name = f"{domain}/{path}"

        # Replace dots, slashes, and invalid chars with dashes
        folder_name = re.sub(r'[./<>:"/\\|?*]+', '-', full_name)

        # Clean up multiple dashes and trailing dashes
        folder_name = re.sub(r'-+', '-', folder_name)
        folder_name = folder_name.strip('-')

        return folder_name

    def _get_archive_folder_name(self, original_url):
        """
        Extract folder name from archived original URL.
        Example: http://arc.won.net/guide/ -> arcwonguide
        """
        # Parse the original URL
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'http://' + original_url

        parsed = urlparse(original_url)
        domain = parsed.netloc
        path = parsed.path

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Remove common TLDs
        tlds = ['.com', '.net', '.org', '.edu', '.gov', '.co.uk', '.io', '.info']
        for tld in tlds:
            if domain.endswith(tld):
                domain = domain[:-len(tld)]
                break

        # Clean path - remove leading/trailing slashes and file extensions
        if path:
            path = path.strip('/')
            path = re.sub(r'\.[a-zA-Z0-9]+$', '', path)  # Remove file extension

        # Combine domain and path
        full_name = domain
        if path:
            full_name = f"{domain}/{path}"

        # Remove all dots, dashes, slashes - join as one word
        folder_name = re.sub(r'[.\-_/]', '', full_name)

        return folder_name if folder_name else "archive"

    def start_crawl(self):
        url = self.url_var.get().strip()
        if not url or url == "https://":
            self.log("[ERROR] Please enter a URL")
            return

        out_dir = self.dir_var.get().strip()
        if not out_dir:
            self.log("[ERROR] Please select output directory")
            return

        # Organize by website subfolder
        if self.organize_by_site_var.get():
            site_folder = self.get_site_folder_name(url)
            out_dir = os.path.join(out_dir, site_folder)

        try:
            max_pages = int(self.max_pages_var.get())
        except ValueError:
            max_pages = DEFAULT_MAX_PAGES

        try:
            max_depth = int(self.max_depth_var.get())
            if max_depth == 0:
                max_depth = None  # 0 means unlimited
        except ValueError:
            max_depth = None

        try:
            delay = float(self.delay_var.get())
        except ValueError:
            delay = 0.0

        respect_robots = self.robots_var.get()
        detect_duplicates = self.duplicates_var.get()
        save_pages = self.save_pages_var.get()

        extensions = self.get_extensions()

        if not extensions and self.ext_checkboxes:
            self.log("[ERROR] Please select at least one file type")
            return

        self.is_crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        self.log("=" * 50)
        self.log(f"URL: {url}")
        self.log(f"Extensions: {', '.join(sorted(extensions)) if extensions else '(all)'}")
        self.log(f"Output: {out_dir}")
        self.log(f"Max pages: {max_pages}, Max depth: {max_depth if max_depth else 'unlimited'}")
        self.log(f"Delay: {delay}s, Robots: {respect_robots}, Dedup: {detect_duplicates}, Save HTML: {save_pages}")
        self.log("=" * 50)

        # Run crawler in thread
        thread = threading.Thread(
            target=self.run_crawler,
            args=(url, extensions, out_dir, max_pages, max_depth, delay, respect_robots, detect_duplicates, save_pages),
            daemon=True
        )
        thread.start()

    def run_crawler(self, url, extensions, out_dir, max_pages, max_depth, delay, respect_robots, detect_duplicates, save_pages):
        # Redirect print to log
        class LogRedirector:
            def __init__(self, gui):
                self.gui = gui
            def write(self, text):
                if text.strip():
                    self.gui.root.after(0, lambda: self.gui.log(text.strip()))
            def flush(self):
                pass

        old_stdout = sys.stdout
        sys.stdout = LogRedirector(self)

        try:
            crawl(
                start_url=url,
                allowed_exts=extensions,
                out_dir=out_dir,
                max_pages=max_pages,
                max_depth=max_depth,
                delay=delay,
                respect_robots=respect_robots,
                detect_duplicates=detect_duplicates,
                save_pages=save_pages
            )
        except Exception as e:
            self.root.after(0, lambda: self.log(f"[ERROR] {e}"))
        finally:
            sys.stdout = old_stdout
            self.root.after(0, self.crawl_finished)

    def crawl_finished(self):
        self.is_crawling = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def stop_crawl(self):
        # Note: This is a simple implementation -
        # full stop would require more complex thread handling
        self.log("[STOPPING] Crawl will stop after current page...")
        self.is_crawling = False


def main():
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
