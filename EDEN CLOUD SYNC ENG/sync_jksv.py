import os
import sys

# --- ENCODING SHIELD ---
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

# --- GLOBAL CONFIGURATION LOAD ---
if not os.path.exists("config.json"):
    print("❌ Error: The 'config.json' file is missing.")
    exit()

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DOSSIER_RACINE_EDEN = config["dossier_racine_eden"]
FICHIER_MAPPING = config["fichier_mapping"]
MAX_ARCHIVES = config.get("max_archives_drive", 2)
ETAT_SYNC_FILE = "sync_state.json"

def ask_conflict_choice(game_name):
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    msg = (f"⚠️ CONFLICT DETECTED FOR: {game_name} ⚠️\n\n"
           "You played on PC AND on the Switch without syncing!\n\n"
           "• YES: Keep PC save (Overwrites Cloud save)\n"
           "• NO: Keep Switch save (Overwrites PC save)\n"
           "• CANCEL: Do nothing (Skip for now)")
    choice = messagebox.askyesnocancel("Save Conflict", msg, icon='warning')
    root.destroy()
    
    if choice is True: return "UPLOAD"
    elif choice is False: return "DOWNLOAD"
    else: return "SKIP"

def load_sync_state():
    if os.path.exists(ETAT_SYNC_FILE):
        with open(ETAT_SYNC_FILE, "r") as f: return json.load(f)
    return {}

def save_sync_state(state):
    with open(ETAT_SYNC_FILE, "w") as f: json.dump(state, f, indent=4)

def find_game_folder(root_path, game_id):
    for dirpath, dirnames, _ in os.walk(root_path):
        for dirname in dirnames:
            if dirname.upper() == game_id.upper():
                return os.path.join(dirpath, dirname)
    return None

def get_latest_local_modification(folder):
    max_mtime = 0
    for root_dir, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root_dir, file)
            mtime = os.path.getmtime(file_path)
            if mtime > max_mtime: max_mtime = mtime
    return max_mtime

def compress_save(source_folder, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root_dir, dirnames, files in os.walk(source_folder):
            for file in files:
                full_path = os.path.join(root_dir, file)
                relative_path = os.path.relpath(full_path, source_folder)
                zipf.write(full_path, relative_path)

def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'): creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token: token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def search_drive_item(service, query):
    res = service.files().list(q=query, spaces='drive', fields='files(id, name, modifiedTime)').execute()
    return res.get('files', [])[0] if res.get('files') else None

def create_or_find_folder(service, name, parent_id):
    query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder = search_drive_item(service, query)
    if folder: return folder['id']
    metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    return service.files().create(body=metadata, fields='id').execute()['id']

def clean_old_versions(service, file_id):
    try:
        revisions = service.revisions().list(fileId=file_id).execute().get('revisions', [])
        if len(revisions) > 1:
            for rev in revisions[:-1]:
                try: service.revisions().delete(fileId=file_id, revisionId=rev['id']).execute()
                except Exception: pass
    except Exception: pass

def clean_eden_archives(service, archive_folder_id, max_archives):
    try:
        query = f"'{archive_folder_id}' in parents and mimeType contains 'zip' and trashed=false"
        files = service.files().list(q=query, spaces='drive', fields='files(id, name, createdTime)').execute().get('files', [])
        if len(files) > max_archives:
            files.sort(key=lambda x: x.get('createdTime', ''), reverse=True)
            for f in files[max_archives:]:
                try: service.files().delete(fileId=f['id']).execute()
                except Exception: pass
    except Exception: pass

def main():
    print("=== 🚀 Starting Cloud Sync ===")
    
    report = {"upload": [], "download": [], "skip": [], "not_found": [], "error": []}
    
    try:
        with open(FICHIER_MAPPING, 'r', encoding='utf-8') as f: mapping_games = json.load(f)
    except Exception:
        print(f"❌ Error loading {FICHIER_MAPPING}.")
        return

    service = authenticate_google_drive()
    sync_state = load_sync_state()

    query_jksv = "name='JKSV' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_jksv = search_drive_item(service, query_jksv)
    if not folder_jksv:
        print("❌ Error: 'JKSV' folder not found on Google Drive.")
        return

    for game_id, drive_game_name in mapping_games.items():
        local_game_folder = find_game_folder(DOSSIER_RACINE_EDEN, game_id)
        if not local_game_folder:
            report["not_found"].append(drive_game_name)
            continue

        escaped_game_name = drive_game_name.replace("'", "\\'")
        drive_game_folder = search_drive_item(service, f"name='{escaped_game_name}' and '{folder_jksv['id']}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false")
        if not drive_game_folder:
            report["error"].append(f"{drive_game_name} (No Drive folder)")
            continue

        save_file = search_drive_item(service, f"name='transfert.zip' and '{drive_game_folder['id']}' in parents and mimeType contains 'zip' and trashed=false")
        if not save_file:
            report["error"].append(f"{drive_game_name} (No transfert.zip)")
            continue

        drive_time_str = save_file.get('modifiedTime')
        if not drive_time_str: continue

        drive_mtime = datetime.fromisoformat(drive_time_str.replace('Z', '+00:00')).timestamp()
        local_mtime = get_latest_local_modification(local_game_folder)

        state = sync_state.get(game_id)
        action = "SKIP"

        if not state:
            action = "UPLOAD" if local_mtime > drive_mtime else "DOWNLOAD"
        else:
            pc_modified = (local_mtime - state["last_local"]) > 2
            drive_modified = (drive_mtime - state["last_drive"]) > 2

            if pc_modified and drive_modified:
                action = ask_conflict_choice(drive_game_name)
            elif pc_modified: action = "UPLOAD"
            elif drive_modified: action = "DOWNLOAD"
            else:
                action = "SKIP"

        if action == "SKIP":
            report["skip"].append(drive_game_name)
            continue

        print(f"\n🎮 Processing: {drive_game_name}")
        
        if action == "UPLOAD":
            print(f"   ⬆️ Uploading to Drive...")
            try:
                temp_zip_file = os.path.join(tempfile.gettempdir(), f"save_{game_id}.zip")
                compress_save(local_game_folder, temp_zip_file)

                media = MediaFileUpload(temp_zip_file, mimetype='application/zip', resumable=True)
                updated_file = service.files().update(fileId=save_file['id'], media_body=media, fields='modifiedTime').execute()
                
                new_drive_mtime = datetime.fromisoformat(updated_file['modifiedTime'].replace('Z', '+00:00')).timestamp()
                sync_state[game_id] = {"last_local": local_mtime, "last_drive": new_drive_mtime}
                save_sync_state(sync_state)
                
                clean_old_versions(service, save_file['id'])
                if os.path.exists(temp_zip_file):
                    try: os.remove(temp_zip_file)
                    except: pass
                    
                report["upload"].append(drive_game_name)
                print("   ✅ Success!")
            except Exception as e:
                print(f"   ❌ Upload error: {e}")
                report["error"].append(drive_game_name)

        elif action == "DOWNLOAD":
            print(f"   ⬇️ Downloading and Restoring to Eden...")
            try:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_zip_name, archive_zip_path = f"archive_pc_{timestamp_str}.zip", os.path.join(tempfile.gettempdir(), f"archive_pc_{timestamp_str}.zip")
                compress_save(local_game_folder, archive_zip_path)

                archive_folder_id = create_or_find_folder(service, "archive eden", drive_game_folder['id'])
                media_archive = MediaFileUpload(archive_zip_path, mimetype='application/zip')
                service.files().create(body={'name': archive_zip_name, 'parents': [archive_folder_id]}, media_body=media_archive).execute()
                clean_eden_archives(service, archive_folder_id, MAX_ARCHIVES)

                download_path = os.path.join(tempfile.gettempdir(), "download_transfert.zip")
                with open(download_path, 'wb') as fh: fh.write(service.files().get_media(fileId=save_file['id']).execute())

                for item in os.listdir(local_game_folder):
                    item_path = os.path.join(local_game_folder, item)
                    shutil.rmtree(item_path) if os.path.isdir(item_path) else os.remove(item_path)

                with zipfile.ZipFile(download_path, 'r') as zip_ref: zip_ref.extractall(local_game_folder)

                for root_dir, _, files in os.walk(local_game_folder):
                    for file in files: os.utime(os.path.join(root_dir, file), (drive_mtime, drive_mtime))

                sync_state[game_id] = {"last_local": drive_mtime, "last_drive": drive_mtime}
                save_sync_state(sync_state)

                for temp_file in [archive_zip_path, download_path]:
                    if os.path.exists(temp_file):
                        try: os.remove(temp_file)
                        except: pass
                
                report["download"].append(drive_game_name)
                print("   ✅ Success!")
            except Exception as e:
                print(f"   ❌ Download error: {e}")
                report["error"].append(drive_game_name)

    print("\n" + "="*55)
    print("📊 SYNCHRONIZATION REPORT")
    print("="*55)
    
    if report["upload"]:
        print(f"⬆️  Uploaded to Drive ({len(report['upload'])}):")
        for game in report["upload"]: print(f"    - {game}")
        print()
    if report["download"]:
        print(f"⬇️  Downloaded to PC ({len(report['download'])}):")
        for game in report["download"]: print(f"    - {game}")
        print()
    if report["skip"]:
        print(f"⏭️  Already up to date ({len(report['skip'])}):")
        for game in report["skip"]: print(f"    - {game}")
        print()
    if report["error"]:
        print(f"❌ Errors encountered ({len(report['error'])}):")
        for game in report["error"]: print(f"    - {game}")
        print()
    if report["not_found"]:
        print(f"👻 {len(report['not_found'])} base games ignored.")
        
    print("="*55)

if __name__ == '__main__':
    main()