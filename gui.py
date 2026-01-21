"""
WebCrawlScrape - Simple Windows GUI
Tkinter interface for the web crawler.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import os
import sys

from config import EXTENSION_PRESETS, DEFAULT_MAX_PAGES
from crawler import crawl


class CrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WebCrawlScrape")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        self.is_crawling = False
        self.create_widgets()

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

        # Preset dropdown
        preset_frame = ttk.Frame(types_frame)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(preset_frame, text="Preset:").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar(value="images")
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=list(EXTENSION_PRESETS.keys()),
            state="readonly",
            width=15
        )
        preset_combo.pack(side=tk.LEFT, padx=(5, 20))
        preset_combo.bind("<<ComboboxSelected>>", self.on_preset_change)

        # Custom extensions entry
        ttk.Label(preset_frame, text="Or custom:").pack(side=tk.LEFT)
        self.custom_ext_var = tk.StringVar()
        self.custom_ext_entry = ttk.Entry(preset_frame, textvariable=self.custom_ext_var, width=30)
        self.custom_ext_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(preset_frame, text="(e.g. .zip,.png)").pack(side=tk.LEFT)

        # --- Output Directory Section ---
        dir_frame = ttk.LabelFrame(main_frame, text="Save To", padding="5")
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        dir_inner = ttk.Frame(dir_frame)
        dir_inner.pack(fill=tk.X, padx=5, pady=5)

        self.dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "downloads"))
        self.dir_entry = ttk.Entry(dir_inner, textvariable=self.dir_var, width=55)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = ttk.Button(dir_inner, text="Browse...", command=self.browse_directory)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))

        # --- Options Section ---
        opts_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        opts_frame.pack(fill=tk.X, pady=(0, 10))

        opts_inner = ttk.Frame(opts_frame)
        opts_inner.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(opts_inner, text="Max pages:").pack(side=tk.LEFT)
        self.max_pages_var = tk.StringVar(value=str(DEFAULT_MAX_PAGES))
        max_pages_spin = ttk.Spinbox(
            opts_inner,
            from_=1,
            to=9999,
            textvariable=self.max_pages_var,
            width=8
        )
        max_pages_spin.pack(side=tk.LEFT, padx=(5, 0))

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

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_preset_change(self, event=None):
        # Clear custom when preset selected
        self.custom_ext_var.set("")

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)

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
        custom = self.custom_ext_var.get().strip()
        if custom:
            # Parse custom extensions
            exts = set()
            for ext in custom.split(","):
                ext = ext.strip().lower()
                if ext and not ext.startswith("."):
                    ext = "." + ext
                if ext:
                    exts.add(ext)
            return exts
        else:
            # Use preset
            preset = self.preset_var.get()
            return EXTENSION_PRESETS.get(preset, set())

    def start_crawl(self):
        url = self.url_var.get().strip()
        if not url or url == "https://":
            self.log("[ERROR] Please enter a URL")
            return

        out_dir = self.dir_var.get().strip()
        if not out_dir:
            self.log("[ERROR] Please select output directory")
            return

        try:
            max_pages = int(self.max_pages_var.get())
        except ValueError:
            max_pages = DEFAULT_MAX_PAGES

        extensions = self.get_extensions()

        self.is_crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        self.log("=" * 50)
        self.log(f"URL: {url}")
        self.log(f"Extensions: {', '.join(sorted(extensions)) if extensions else '(all)'}")
        self.log(f"Output: {out_dir}")
        self.log(f"Max pages: {max_pages}")
        self.log("=" * 50)

        # Run crawler in thread
        thread = threading.Thread(
            target=self.run_crawler,
            args=(url, extensions, out_dir, max_pages),
            daemon=True
        )
        thread.start()

    def run_crawler(self, url, extensions, out_dir, max_pages):
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
                max_pages=max_pages
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
