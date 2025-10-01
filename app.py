from utils import *

# Logging setup
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "log.txt"),
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class SpringbrookUpload:
    def __init__(self, root):
        self.root = root
        self.root.title("Springbrook Upload by D. Tumanyan")
        self.root.geometry("700x600")
        self.export_file_path = None
        self.rni_file_path = None
        self.thread = None

        # === Style Setup ===
        PRIMARY = "#1e90ff"
        SECONDARY = "#f0f0f0"
        TEXT = "#333333"

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TButton",
                        background=PRIMARY,
                        foreground="white",
                        font=("Segoe UI", 10, "bold"),
                        padding=10,
                        borderwidth=0)
        style.map("TButton",
                  background=[("active", "#187bcd"), ("disabled", "#cccccc")])

        style.configure("TProgressbar",
                        troughcolor=SECONDARY,
                        background=PRIMARY,
                        bordercolor=SECONDARY,
                        lightcolor=PRIMARY,
                        darkcolor=PRIMARY)

        style.configure("TNotebook.Tab",
                        font=("Segoe UI", 10),
                        padding=(12, 6, 12, 6),
                        background=SECONDARY,
                        foreground=TEXT)
        style.map("TNotebook.Tab",
                  background=[("selected", PRIMARY)],
                  foreground=[("selected", "white")])
        # Remove focus ring from tabs
        style.layout("TNotebook.Tab", [
            ('Notebook.tab', {
                'sticky': 'nswe',
                'children': [
                    ('Notebook.padding', {
                        'side': 'top',
                        'sticky': 'nswe',
                        'children': [
                            ('Notebook.label', {'side': 'top', 'sticky': ''})
                        ]
                    })
                ]
            })
        ])

        # === Tabs ===
        tab_control = ttk.Notebook(root)
        self.tab_main = ttk.Frame(tab_control)
        self.tab_log = ttk.Frame(tab_control)
        tab_control.add(self.tab_main, text='Main')
        tab_control.add(self.tab_log, text='Logs')
        tab_control.pack(expand=1, fill='both')
        # === Buttons ===
        button_frame = ttk.Frame(self.tab_main, padding=10)
        button_frame.pack(pady=10)

        self.choose_button = ttk.Button(button_frame, text="📂 Choose Files", command=self.open_file, width=25)
        self.choose_button.pack(side=tk.LEFT, padx=10)

        self.generate_button = ttk.Button(button_frame, text="⚙️ Start Generating", command=self.start_generation,
                                          state="disabled", width=25)
        self.generate_button.pack(side=tk.LEFT, padx=10)

        # === Progress Bar ===
        self.progress = ttk.Progressbar(self.tab_main, orient="horizontal", length=600, mode="determinate")
        self.progress.pack(pady=10)

        # === Scrollable Logs ===
        log_frame = ttk.Frame(self.tab_log)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_frame, height=20, font=("Consolas", 10),
                                background="#fafafa", foreground="#333",
                                insertbackground="black", borderwidth=1, relief="solid",
                                state="disabled", wrap="word")
        self.log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # === Status Bar ===
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log_error(self, e):
        logging.error("Exception occurred:\n" + traceback.format_exc())

    def set_progress(self, value):
        self.progress["value"] = value
        self.root.update_idletasks()

    def update_status(self, message, level="info"):
        color_map = {"info": "#333333", "success": "#4caf50", "warning": "#ffc107", "error": "#f44336"}
        color = color_map.get(level, "#333333")

        self.status_var.set(message)
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} — {message}\n", level)
        self.log_text.tag_config(level, foreground=color)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def open_file(self):
        export_file_path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")], title="Choose the Export file")
        if not export_file_path:
            self.update_status("⚠️ Export file not selected.", "warning")
            return

        rni_file_path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")], title="Choose the RNI file")
        if not rni_file_path:
            self.update_status("⚠️ RNI file not selected.", "warning")
            return
        
        self.export_file_path = export_file_path
        self.update_status(f"📄 Selected Export file: {os.path.basename(export_file_path)}")
        self.rni_file_path = rni_file_path
        self.update_status(f"📄 Selected RNI file: {os.path.basename(rni_file_path)}")
        self.generate_button.config(state="normal")

    def start_generation(self):
        if not self.export_file_path or not self.rni_file_path:
            self.update_status("⚠️ No file selected.", "warning")
            return

        self.update_status("⚙️ Generation in progress...")
        self.generate_button.config(state="disabled")
        self.choose_button.config(state="disabled")
        self.thread = threading.Thread(target=self.process_file, daemon=True)
        self.thread.start()
    
    def process_file(self):
        try:
            # main(self.export_file_path, self.rni_file_path)
            self.set_progress(10)
            export_df, rni_df = load_data(self.export_file_path, self.rni_file_path)
            self.set_progress(30)
            export_df, rni_df = preprocess_data(export_df, rni_df)
            self.set_progress(50)
            merged_df = merge_data(export_df, rni_df)
            self.set_progress(70)
            final_df = format_final_df(merged_df)
            self.set_progress(90)
            date_suffix = get_date_suffix()
            final_filename = f"SpringbrookUpload{date_suffix}.csv"
            save_to_csv(final_df, final_filename)
            self.set_progress(100)
            result_text = (
                "✅ Generation completed successfully!"
            )
            self.root.after(0, lambda: self.update_status(result_text, "success"))

        except Exception as e:
            self.log_error(e)
            err = f"❌ Error: {str(e)}."
            err += "\nMake sure uploaded files are correct."
            self.root.after(0, lambda: self.update_status(err, "error"))

        finally:
            self.root.after(0, lambda: self.generate_button.config(state="normal"))
            self.root.after(0, lambda: self.choose_button.config(state="normal"))

    def on_close(self):
        if self.thread and self.thread.is_alive():
            if messagebox.askyesno("Quit", "Processing is running. Exit anyway?"):
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpringbrookUpload(root)
    root.mainloop()
