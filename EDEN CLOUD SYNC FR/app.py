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
# HACK POUR FUSIONNER CUSTOMTKINTER ET TKINTERDND2
# =========================================================
class AppWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# =========================================================
# CLASSE PRINCIPALE DE L'APPLICATION
# =========================================================
class SyncApp(AppWindow):
    def __init__(self):
        super().__init__()

        # --- Configuration de la fenêtre ---
        self.title("Eden Cloud Sync - Tableau de bord")
        self.geometry("700x550")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config_file = "config.json"
        self.config = self.charger_config()
        self.sync_en_cours = False

        self.creer_interface()
        self.verifier_credentials()

        # Lancement du chien de garde automatique
        self.thread_auto = threading.Thread(target=self.chien_de_garde, daemon=True)
        self.thread_auto.start()

    def charger_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        # Config par défaut
        return {
            "dossier_racine_eden": "C:/",
            "fichier_mapping": "mapping_jeux.json",
            "processus_emulateur": "eden.exe",
            "max_archives_drive": 2
        }

    def sauvegarder_config(self, config_data):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        self.config = config_data
        self.log_message("⚙️ Configuration sauvegardée avec succès.")

    # =========================================================
    # INTERFACE GRAPHIQUE
    # =========================================================
    def creer_interface(self):
        # Header
        self.lbl_titre = ctk.CTkLabel(self, text="☁️ Eden Cloud Sync", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titre.pack(pady=(15, 5))

        self.lbl_status = ctk.CTkLabel(self, text="🟢 Auto-Sync Actif (En attente du jeu...)", text_color="#2ECC71")
        self.lbl_status.pack(pady=(0, 15))

        # Zone Drag & Drop (cachée par défaut)
        self.frame_dnd = ctk.CTkFrame(self, fg_color="#3A2F2F", border_color="#E74C3C", border_width=2)
        self.lbl_dnd = ctk.CTkLabel(self.frame_dnd, text="⚠️ Fichier credentials.json manquant !\n\nGlisse-dépose le fichier API Google ici.", text_color="#E74C3C")
        self.lbl_dnd.pack(pady=20, padx=20)
        
        # Boutons principaux
        self.frame_boutons = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_boutons.pack(pady=10)

        self.btn_sync = ctk.CTkButton(self.frame_boutons, text="🚀 Lancer Synchro Manuelle", height=40, font=ctk.CTkFont(weight="bold"), command=self.lancer_synchro_manuelle)
        self.btn_sync.pack(side="left", padx=10)

        self.btn_config = ctk.CTkButton(self.frame_boutons, text="⚙️ Paramètres", height=40, fg_color="#555555", hover_color="#333333", command=self.ouvrir_fenetre_config)
        self.btn_config.pack(side="left", padx=10)

        # Zone de logs (Console)
        self.textbox_log = ctk.CTkTextbox(self, width=650, height=250, font=ctk.CTkFont(family="Consolas", size=12))
        self.textbox_log.pack(pady=15)
        self.textbox_log.insert("0.0", "Bienvenue dans l'interface de synchronisation !\nPrêt à travailler.\n\n")
        self.textbox_log.configure(state="disabled")

    # =========================================================
    # DRAG & DROP API
    # =========================================================
    def verifier_credentials(self):
        if not os.path.exists("credentials.json"):
            self.frame_dnd.pack(pady=10, before=self.frame_boutons)
            self.frame_dnd.drop_target_register(DND_FILES)
            self.frame_dnd.dnd_bind('<<Drop>>', self.recevoir_fichier_dnd)
            self.btn_sync.configure(state="disabled")
        else:
            self.frame_dnd.pack_forget()
            self.btn_sync.configure(state="normal")

    def recevoir_fichier_dnd(self, event):
        fichier_recu = event.data.strip('{}') 
        if fichier_recu.endswith("credentials.json"):
            try:
                shutil.copy(fichier_recu, "credentials.json")
                self.log_message("🔑 Fichier API détecté et installé avec succès !")
                self.verifier_credentials()
            except Exception as e:
                self.log_message(f"❌ Erreur lors de la copie du fichier : {e}")
        else:
            messagebox.showerror("Fichier Invalide", "Tu dois glisser le fichier 'credentials.json' de Google.")

    # =========================================================
    # FENÊTRE PARAMÈTRES
    # =========================================================
    def ouvrir_fenetre_config(self):
        fenetre_cfg = ctk.CTkToplevel(self)
        fenetre_cfg.title("Paramètres")
        fenetre_cfg.geometry("500x380")
        fenetre_cfg.attributes("-topmost", True)

        ctk.CTkLabel(fenetre_cfg, text="Chemin vers le dossier saves (Eden) :").pack(pady=(15, 0), padx=20, anchor="w")
        entry_chemin = ctk.CTkEntry(fenetre_cfg, width=460)
        entry_chemin.pack(pady=5, padx=20)
        entry_chemin.insert(0, self.config.get("dossier_racine_eden", ""))

        ctk.CTkLabel(fenetre_cfg, text="Nom du processus de l'émulateur (ex: eden.exe) :").pack(pady=(15, 0), padx=20, anchor="w")
        entry_proc = ctk.CTkEntry(fenetre_cfg, width=460)
        entry_proc.pack(pady=5, padx=20)
        entry_proc.insert(0, self.config.get("processus_emulateur", "eden.exe"))

        # --- IMPORTATION MANUELLE DU FICHIER API ---
        ctk.CTkLabel(fenetre_cfg, text="Clé API Google (credentials) :").pack(pady=(15, 0), padx=20, anchor="w")
        frame_api = ctk.CTkFrame(fenetre_cfg, fg_color="transparent")
        frame_api.pack(fill="x", padx=20, pady=5)
        
        lbl_api_status = ctk.CTkLabel(frame_api, text="✅ Installé" if os.path.exists("credentials.json") else "❌ Manquant", text_color="#2ECC71" if os.path.exists("credentials.json") else "#E74C3C")
        lbl_api_status.pack(side="left", padx=(0, 15))

        def parcourir_fichier_api():
            chemin_fichier = filedialog.askopenfilename(title="Sélectionner credentials.json", filetypes=[("Fichiers JSON", "*.json")])
            if chemin_fichier:
                if chemin_fichier.endswith("credentials.json"):
                    try:
                        shutil.copy(chemin_fichier, "credentials.json")
                        lbl_api_status.configure(text="✅ Installé", text_color="#2ECC71")
                        self.verifier_credentials()
                        self.log_message("🔑 Fichier credentials importé manuellement.")
                    except Exception as e:
                        messagebox.showerror("Erreur", f"Impossible de copier le fichier :\n{e}")
                else:
                    messagebox.showerror("Fichier Invalide", "Veuillez sélectionner un fichier nommé 'credentials.json'.")

        ctk.CTkButton(frame_api, text="Parcourir / Importer", fg_color="#3498DB", hover_color="#2980B9", command=parcourir_fichier_api).pack(side="left")

        def sauvegarder():
            self.config["dossier_racine_eden"] = entry_chemin.get().replace("\\", "/")
            self.config["processus_emulateur"] = entry_proc.get()
            self.sauvegarder_config(self.config)
            fenetre_cfg.destroy()

        ctk.CTkButton(fenetre_cfg, text="Sauvegarder", fg_color="#27AE60", hover_color="#2ECC71", command=sauvegarder).pack(pady=20)

    # =========================================================
    # GESTION DES LOGS ET DE LA SYNCHRONISATION
    # =========================================================
    def log_message(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def lancer_synchro_manuelle(self):
        if not self.sync_en_cours:
            self.log_message("\n=== Lancement Manuel Demandé ===")
            threading.Thread(target=self.executer_script_sync, daemon=True).start()

    def executer_script_sync(self):
        self.sync_en_cours = True
        self.btn_sync.configure(state="disabled", text="⏳ Synchro en cours...")
        
        try:
            env_custom = os.environ.copy()
            env_custom["PYTHONIOENCODING"] = "utf-8"

            process = subprocess.Popen(
                ["python", "sync_jksv.py"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                env=env_custom
            )
            
            for ligne_bytes in iter(process.stdout.readline, b''):
                ligne = ligne_bytes.decode('utf-8', errors='replace').strip('\r\n')
                self.after(0, self.log_message, ligne)
            
            process.stdout.close()
            process.wait()
        except Exception as e:
            self.after(0, self.log_message, f"❌ Erreur critique : {e}")

        self.sync_en_cours = False
        self.after(0, lambda: self.btn_sync.configure(state="normal", text="🚀 Lancer Synchro Manuelle"))

    # =========================================================
    # CHIEN DE GARDE (AUTO-SYNC EN ARRIÈRE-PLAN)
    # =========================================================
    def est_en_cours(self, nom_processus):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == nom_processus.lower(): return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass
        return False

    def chien_de_garde(self):
        nom_proc = self.config.get("processus_emulateur", "eden.exe")
        en_cours_avant = self.est_en_cours(nom_proc)

        while True:
            nom_proc = self.config.get("processus_emulateur", "eden.exe") 
            en_cours_maintenant = self.est_en_cours(nom_proc)
            
            if en_cours_maintenant and not en_cours_avant:
                self.after(0, lambda: self.lbl_status.configure(text=f"🟡 Jeu en cours ({nom_proc})...", text_color="#F1C40F"))
            
            elif not en_cours_maintenant and en_cours_avant:
                self.after(0, lambda: self.lbl_status.configure(text="🔵 Fermeture détectée. Démarrage Synchro...", text_color="#3498DB"))
                if not self.sync_en_cours:
                    self.executer_script_sync()
                self.after(0, lambda: self.lbl_status.configure(text="🟢 Auto-Sync Actif (En attente du jeu...)", text_color="#2ECC71"))
                
            en_cours_avant = en_cours_maintenant
            time.sleep(5)

if __name__ == "__main__":
    app = SyncApp()
    app.mainloop()