import os
import json
import shutil
import threading
import subprocess
import time
import psutil
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import messagebox, filedialog

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# =========================================================
# CUSTOMTKINTER AND TKINTERDND2 HACK
# =========================================================
class AppWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# =========================================================
# MAIN APPLICATION CLASS
# =========================================================
class SyncApp(AppWindow):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("Eden Cloud Sync - Dashboard")
        self.geometry("700x550")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config_file = "config.json"
        self.config = self.load_config()
        self.sync_in_progress = False

        self.create_interface()
        self.check_credentials()

        # Background watchdog for auto-sync
        self.thread_auto = threading.Thread(target=self.watchdog_process, daemon=True)
        self.thread_auto.start()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        # Default config
        return {
            "dossier_racine_eden": "C:/",
            "fichier_mapping": "mapping_jeux.json",
            "processus_emulateur": "eden.exe",
            "max_archives_drive": 2
        }

    def save_config(self, config_data):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        self.config = config_data
        self.log_message("⚙️ Configuration saved successfully.")

    # =========================================================
    # GRAPHICAL INTERFACE
    # =========================================================
    def create_interface(self):
        # Header
        self.lbl_title = ctk.CTkLabel(self, text="☁️ Eden Cloud Sync", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=(15, 5))

        self.lbl_status = ctk.CTkLabel(self, text="🟢 Auto-Sync Active (Waiting for game...)", text_color="#2ECC71")
        self.lbl_status.pack(pady=(0, 15))

        # Drag & Drop Zone (hidden by default)
        self.frame_dnd = ctk.CTkFrame(self, fg_color="#3A2F2F", border_color="#E74C3C", border_width=2)
        self.lbl_dnd = ctk.CTkLabel(self.frame_dnd, text="⚠️ Missing credentials.json file!\n\nDrag and drop the Google API file here.", text_color="#E74C3C")
        self.lbl_dnd.pack(pady=20, padx=20)
        
        # Main Buttons
        self.frame_buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_buttons.pack(pady=10)

        self.btn_sync = ctk.CTkButton(self.frame_buttons, text="🚀 Start Manual Sync", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_manual_sync)
        self.btn_sync.pack(side="left", padx=10)

        self.btn_config = ctk.CTkButton(self.frame_buttons, text="⚙️ Settings", height=40, fg_color="#555555", hover_color="#333333", command=self.open_settings_window)
        self.btn_config.pack(side="left", padx=10)

        # Log Textbox (Console)
        self.textbox_log = ctk.CTkTextbox(self, width=650, height=250, font=ctk.CTkFont(family="Consolas", size=12))
        self.textbox_log.pack(pady=15)
        self.textbox_log.insert("0.0", "Welcome to the synchronization interface!\nReady to work.\n\n")
        self.textbox_log.configure(state="disabled")

    # =========================================================
    # DRAG & DROP API
    # =========================================================
    def check_credentials(self):
        if not os.path.exists("credentials.json"):
            self.frame_dnd.pack(pady=10, before=self.frame_buttons)
            self.frame_dnd.drop_target_register(DND_FILES)
            self.frame_dnd.dnd_bind('<<Drop>>', self.receive_dnd_file)
            self.btn_sync.configure(state="disabled")
        else:
            self.frame_dnd.pack_forget()
            self.btn_sync.configure(state="normal")

    def receive_dnd_file(self, event):
        received_file = event.data.strip('{}') 
        if received_file.endswith("credentials.json"):
            try:
                shutil.copy(received_file, "credentials.json")
                self.log_message("🔑 API file detected and installed successfully!")
                self.check_credentials()
            except Exception as e:
                self.log_message(f"❌ Error copying file: {e}")
        else:
            messagebox.showerror("Invalid File", "You must drag and drop the Google 'credentials.json' file.")

    # =========================================================
    # SETTINGS WINDOW
    # =========================================================
    def open_settings_window(self):
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("Settings")
        settings_win.geometry("500x380")
        settings_win.attributes("-topmost", True)

        ctk.CTkLabel(settings_win, text="Path to saves folder (Eden):").pack(pady=(15, 0), padx=20, anchor="w")
        entry_path = ctk.CTkEntry(settings_win, width=460)
        entry_path.pack(pady=5, padx=20)
        entry_path.insert(0, self.config.get("dossier_racine_eden", ""))

        ctk.CTkLabel(settings_win, text="Emulator process name (e.g., eden.exe):").pack(pady=(15, 0), padx=20, anchor="w")
        entry_proc = ctk.CTkEntry(settings_win, width=460)
        entry_proc.pack(pady=5, padx=20)
        entry_proc.insert(0, self.config.get("processus_emulateur", "eden.exe"))

        # --- MANUAL API FILE IMPORT ---
        ctk.CTkLabel(settings_win, text="Google API Credentials:").pack(pady=(15, 0), padx=20, anchor="w")
        frame_api = ctk.CTkFrame(settings_win, fg_color="transparent")
        frame_api.pack(fill="x", padx=20, pady=5)
        
        lbl_api_status = ctk.CTkLabel(frame_api, text="✅ Installed" if os.path.exists("credentials.json") else "❌ Missing", text_color="#2ECC71" if os.path.exists("credentials.json") else "#E74C3C")
        lbl_api_status.pack(side="left", padx=(0, 15))

        def browse_api_file():
            filepath = filedialog.askopenfilename(title="Select credentials.json", filetypes=[("JSON Files", "*.json")])
            if filepath:
                if filepath.endswith("credentials.json"):
                    try:
                        shutil.copy(filepath, "credentials.json")
                        lbl_api_status.configure(text="✅ Installed", text_color="#2ECC71")
                        self.check_credentials()
                        self.log_message("🔑 Credentials manually imported.")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not copy file:\n{e}")
                else:
                    messagebox.showerror("Invalid File", "Please select a file named 'credentials.json'.")

        ctk.CTkButton(frame_api, text="Browse / Import", fg_color="#3498DB", hover_color="#2980B9", command=browse_api_file).pack(side="left")

        def save():
            self.config["dossier_racine_eden"] = entry_path.get().replace("\\", "/")
            self.config["processus_emulateur"] = entry_proc.get()
            self.save_config(self.config)
            settings_win.destroy()

        ctk.CTkButton(settings_win, text="Save Settings", fg_color="#27AE60", hover_color="#2ECC71", command=save).pack(pady=20)

    # =========================================================
    # LOG & SYNC EXECUTION
    # =========================================================
    def log_message(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def start_manual_sync(self):
        if not self.sync_in_progress:
            self.log_message("\n=== Manual Sync Requested ===")
            threading.Thread(target=self.execute_sync_script, daemon=True).start()

    def execute_sync_script(self):
        self.sync_in_progress = True
        self.btn_sync.configure(state="disabled", text="⏳ Sync in progress...")
        
        try:
            env_custom = os.environ.copy()
            env_custom["PYTHONIOENCODING"] = "utf-8"

            process = subprocess.Popen(
                ["python", "sync_jksv.py"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                env=env_custom
            )
            
            for line_bytes in iter(process.stdout.readline, b''):
                line = line_bytes.decode('utf-8', errors='replace').strip('\r\n')
                self.after(0, self.log_message, line)
            
            process.stdout.close()
            process.wait()
        except Exception as e:
            self.after(0, self.log_message, f"❌ Critical error: {e}")

        self.sync_in_progress = False
        self.after(0, lambda: self.btn_sync.configure(state="normal", text="🚀 Start Manual Sync"))

    # =========================================================
    # WATCHDOG (BACKGROUND AUTO-SYNC)
    # =========================================================
    def is_running(self, process_name):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == process_name.lower(): return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass
        return False

    def watchdog_process(self):
        proc_name = self.config.get("processus_emulateur", "eden.exe")
        running_before = self.is_running(proc_name)

        while True:
            proc_name = self.config.get("processus_emulateur", "eden.exe") 
            running_now = self.is_running(proc_name)
            
            if running_now and not running_before:
                self.after(0, lambda: self.lbl_status.configure(text=f"🟡 Game running ({proc_name})...", text_color="#F1C40F"))
            
            elif not running_now and running_before:
                self.after(0, lambda: self.lbl_status.configure(text="🔵 Closure detected. Starting Sync...", text_color="#3498DB"))
                if not self.sync_in_progress:
                    self.execute_sync_script()
                self.after(0, lambda: self.lbl_status.configure(text="🟢 Auto-Sync Active (Waiting for game...)", text_color="#2ECC71"))
                
            running_before = running_now
            time.sleep(5)

if __name__ == "__main__":
    app = SyncApp()
    app.mainloop()