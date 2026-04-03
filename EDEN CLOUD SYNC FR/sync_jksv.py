import os
import sys

# --- LE BOUCLIER ANTI-CRASH EMOJI ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
    
import zipfile
import tempfile
import json
import shutil
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

os.chdir(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ['https://www.googleapis.com/auth/drive']

# --- CHARGEMENT DE LA CONFIGURATION GLOBALE ---
if not os.path.exists("config.json"):
    print("❌ Erreur : Le fichier 'config.json' est introuvable.")
    exit()

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DOSSIER_RACINE_EDEN = config["dossier_racine_eden"]
FICHIER_MAPPING = config["fichier_mapping"]
MAX_ARCHIVES = config.get("max_archives_drive", 2)
ETAT_SYNC_FILE = "sync_state.json"

def demander_choix_conflit(nom_jeu):
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    msg = (f"⚠️ CONFLIT DÉTECTÉ POUR : {nom_jeu} ⚠️\n\n"
           "Tu as joué sur PC ET sur la Switch sans synchroniser !\n\n"
           "• OUI : Garder la partie PC (Écrase la sauvegarde Cloud)\n"
           "• NON : Garder la partie Switch (Écrase la sauvegarde PC)\n"
           "• ANNULER : Ne rien faire (Ignorer pour le moment)")
    choix = messagebox.askyesnocancel("Conflit de Sauvegarde", msg, icon='warning')
    root.destroy()
    
    if choix is True: return "UPLOAD"
    elif choix is False: return "DOWNLOAD"
    else: return "SKIP"

def charger_etat_sync():
    if os.path.exists(ETAT_SYNC_FILE):
        with open(ETAT_SYNC_FILE, "r") as f: return json.load(f)
    return {}

def sauvegarder_etat_sync(etat):
    with open(ETAT_SYNC_FILE, "w") as f: json.dump(etat, f, indent=4)

def trouver_dossier_jeu(racine, id_jeu):
    for chemin_racine, dossiers, _ in os.walk(racine):
        for nom_dossier in dossiers:
            if nom_dossier.upper() == id_jeu.upper():
                return os.path.join(chemin_racine, nom_dossier)
    return None

def get_derniere_modification_locale(dossier):
    max_mtime = 0
    for racine, _, fichiers in os.walk(dossier):
        for fichier in fichiers:
            chemin = os.path.join(racine, fichier)
            mtime = os.path.getmtime(chemin)
            if mtime > max_mtime: max_mtime = mtime
    return max_mtime

def compresser_sauvegarde(dossier_source, chemin_zip):
    with zipfile.ZipFile(chemin_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for racine, dossiers, fichiers in os.walk(dossier_source):
            for fichier in fichiers:
                chemin_complet = os.path.join(racine, fichier)
                chemin_relatif = os.path.relpath(chemin_complet, dossier_source)
                zipf.write(chemin_complet, chemin_relatif)

def authentifier_google_drive():
    creds = None
    if os.path.exists('token.json'): creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token: token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def chercher_element_drive(service, query):
    res = service.files().list(q=query, spaces='drive', fields='files(id, name, modifiedTime)').execute()
    return res.get('files', [])[0] if res.get('files') else None

def creer_ou_trouver_dossier(service, nom, parent_id):
    query = f"name='{nom}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    dossier = chercher_element_drive(service, query)
    if dossier: return dossier['id']
    metadata = {'name': nom, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    return service.files().create(body=metadata, fields='id').execute()['id']

def nettoyer_anciennes_versions(service, file_id):
    try:
        revisions = service.revisions().list(fileId=file_id).execute().get('revisions', [])
        if len(revisions) > 1:
            for rev in revisions[:-1]:
                try: service.revisions().delete(fileId=file_id, revisionId=rev['id']).execute()
                except Exception: pass
    except Exception: pass

def nettoyer_archives_eden(service, id_dossier_archive, max_archives):
    try:
        query = f"'{id_dossier_archive}' in parents and mimeType contains 'zip' and trashed=false"
        fichiers = service.files().list(q=query, spaces='drive', fields='files(id, name, createdTime)').execute().get('files', [])
        if len(fichiers) > max_archives:
            fichiers.sort(key=lambda x: x.get('createdTime', ''), reverse=True)
            for f in fichiers[max_archives:]:
                try: service.files().delete(fileId=f['id']).execute()
                except Exception: pass
    except Exception: pass

def main():
    print("=== 🚀 Démarrage de la Sync Cloud ===")
    
    rapport = {"upload": [], "download": [], "skip": [], "introuvable": [], "erreur": []}
    
    try:
        with open(FICHIER_MAPPING, 'r', encoding='utf-8') as f: mapping_jeux = json.load(f)
    except Exception:
        print(f"❌ Erreur avec {FICHIER_MAPPING}.")
        return

    service = authentifier_google_drive()
    etat_sync = charger_etat_sync()

    query_jksv = "name='JKSV' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    dossier_jksv = chercher_element_drive(service, query_jksv)
    if not dossier_jksv:
        print("❌ Erreur : Dossier JKSV introuvable sur Drive.")
        return

    for id_eden, nom_jeu_drive in mapping_jeux.items():
        dossier_local_jeu = trouver_dossier_jeu(DOSSIER_RACINE_EDEN, id_eden)
        if not dossier_local_jeu:
            rapport["introuvable"].append(nom_jeu_drive)
            continue

        nom_jeu_echappe = nom_jeu_drive.replace("'", "\\'")
        dossier_jeu = chercher_element_drive(service, f"name='{nom_jeu_echappe}' and '{dossier_jksv['id']}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false")
        if not dossier_jeu:
            rapport["erreur"].append(f"{nom_jeu_drive} (Pas de dossier Drive)")
            continue

        fichier_sauvegarde = chercher_element_drive(service, f"name='transfert.zip' and '{dossier_jeu['id']}' in parents and mimeType contains 'zip' and trashed=false")
        if not fichier_sauvegarde:
            rapport["erreur"].append(f"{nom_jeu_drive} (Pas de transfert.zip)")
            continue

        drive_time_str = fichier_sauvegarde.get('modifiedTime')
        if not drive_time_str: continue

        drive_mtime = datetime.fromisoformat(drive_time_str.replace('Z', '+00:00')).timestamp()
        local_mtime = get_derniere_modification_locale(dossier_local_jeu)

        state = etat_sync.get(id_eden)
        action = "SKIP"

        if not state:
            action = "UPLOAD" if local_mtime > drive_mtime else "DOWNLOAD"
        else:
            pc_modifie = (local_mtime - state["last_local"]) > 2
            drive_modifie = (drive_mtime - state["last_drive"]) > 2

            if pc_modifie and drive_modifie:
                action = demander_choix_conflit(nom_jeu_drive)
            elif pc_modifie: action = "UPLOAD"
            elif drive_modifie: action = "DOWNLOAD"
            else:
                action = "SKIP"

        if action == "SKIP":
            rapport["skip"].append(nom_jeu_drive)
            continue

        print(f"\n🎮 Traitement de : {nom_jeu_drive}")
        
        if action == "UPLOAD":
            print(f"   ⬆️ Upload vers le Drive...")
            try:
                fichier_zip_temp = os.path.join(tempfile.gettempdir(), f"save_{id_eden}.zip")
                compresser_sauvegarde(dossier_local_jeu, fichier_zip_temp)

                media = MediaFileUpload(fichier_zip_temp, mimetype='application/zip', resumable=True)
                fichier_mis_a_jour = service.files().update(fileId=fichier_sauvegarde['id'], media_body=media, fields='modifiedTime').execute()
                
                nouveau_drive_mtime = datetime.fromisoformat(fichier_mis_a_jour['modifiedTime'].replace('Z', '+00:00')).timestamp()
                etat_sync[id_eden] = {"last_local": local_mtime, "last_drive": nouveau_drive_mtime}
                sauvegarder_etat_sync(etat_sync)
                
                nettoyer_anciennes_versions(service, fichier_sauvegarde['id'])
                if os.path.exists(fichier_zip_temp):
                    try: os.remove(fichier_zip_temp)
                    except: pass
                    
                rapport["upload"].append(nom_jeu_drive)
                print("   ✅ Succès !")
            except Exception as e:
                print(f"   ❌ Erreur d'upload : {e}")
                rapport["erreur"].append(nom_jeu_drive)

        elif action == "DOWNLOAD":
            print(f"   ⬇️ Téléchargement et Restauration sur Eden...")
            try:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_zip_nom, archive_zip_chemin = f"archive_pc_{timestamp_str}.zip", os.path.join(tempfile.gettempdir(), f"archive_pc_{timestamp_str}.zip")
                compresser_sauvegarde(dossier_local_jeu, archive_zip_chemin)

                id_dossier_archive = creer_ou_trouver_dossier(service, "archive eden", dossier_jeu['id'])
                media_archive = MediaFileUpload(archive_zip_chemin, mimetype='application/zip')
                service.files().create(body={'name': archive_zip_nom, 'parents': [id_dossier_archive]}, media_body=media_archive).execute()
                nettoyer_archives_eden(service, id_dossier_archive, MAX_ARCHIVES)

                download_path = os.path.join(tempfile.gettempdir(), "download_transfert.zip")
                with open(download_path, 'wb') as fh: fh.write(service.files().get_media(fileId=fichier_sauvegarde['id']).execute())

                for item in os.listdir(dossier_local_jeu):
                    chemin_item = os.path.join(dossier_local_jeu, item)
                    shutil.rmtree(chemin_item) if os.path.isdir(chemin_item) else os.remove(chemin_item)

                with zipfile.ZipFile(download_path, 'r') as zip_ref: zip_ref.extractall(dossier_local_jeu)

                for racine, _, fichiers in os.walk(dossier_local_jeu):
                    for fichier in fichiers: os.utime(os.path.join(racine, fichier), (drive_mtime, drive_mtime))

                etat_sync[id_eden] = {"last_local": drive_mtime, "last_drive": drive_mtime}
                sauvegarder_etat_sync(etat_sync)

                for temp_file in [archive_zip_chemin, download_path]:
                    if os.path.exists(temp_file):
                        try: os.remove(temp_file)
                        except: pass
                
                rapport["download"].append(nom_jeu_drive)
                print("   ✅ Succès !")
            except Exception as e:
                print(f"   ❌ Erreur de download : {e}")
                rapport["erreur"].append(nom_jeu_drive)

    print("\n" + "="*55)
    print("📊 COMPTE RENDU DE SYNCHRONISATION")
    print("="*55)
    
    if rapport["upload"]:
        print(f"⬆️  Envoyés vers Drive ({len(rapport['upload'])}) :")
        for jeu in rapport["upload"]: print(f"    - {jeu}")
        print()
    if rapport["download"]:
        print(f"⬇️  Téléchargés sur PC ({len(rapport['download'])}) :")
        for jeu in rapport["download"]: print(f"    - {jeu}")
        print()
    if rapport["skip"]:
        print(f"⏭️  Déjà à jour ({len(rapport['skip'])}) :")
        for jeu in rapport["skip"]: print(f"    - {jeu}")
        print()
    if rapport["erreur"]:
        print(f"❌ Erreurs rencontrées ({len(rapport['erreur'])}) :")
        for jeu in rapport["erreur"]: print(f"    - {jeu}")
        print()
    if rapport["introuvable"]:
        print(f"👻 {len(rapport['introuvable'])} jeux de la base ignorés.")
        
    print("="*55)
    # LIGNE INPUT RETIREE ICI

if __name__ == '__main__':
    main()