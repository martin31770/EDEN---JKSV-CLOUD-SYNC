import psutil
import time
import subprocess
import json
import os

# Se placer dans le bon dossier
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Charger le nom de l'émulateur depuis le fichier config
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    process_name = config.get("processus_emulateur", "eden.exe")
except Exception:
    process_name = "eden.exe"

def is_running(name):
    """Vérifie si un processus tourne actuellement en mémoire."""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() == name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

print(f"👀 Surveillant de l'émulateur démarré ({process_name}).")
print("Tu peux réduire cette fenêtre, elle tournera en fond.")
print("La synchronisation se lancera toute seule à la fermeture du jeu.\n")

en_cours_avant = is_running(process_name)

while True:
    en_cours_maintenant = is_running(process_name)
    
    # Si le jeu vient juste d'être lancé
    if en_cours_maintenant and not en_cours_avant:
        print(f"[{time.strftime('%H:%M:%S')}] 🎮 Jeu démarré ! Mode surveillance active...")
    
    # Si le jeu vient juste d'être fermé
    elif not en_cours_maintenant and en_cours_avant:
        print(f"[{time.strftime('%H:%M:%S')}] 🛑 Émulateur fermé. Lancement de la synchronisation...")
        
        # On appelle discrètement le script principal
        subprocess.run(["python", "sync_jksv.py"])
        
        print(f"[{time.strftime('%H:%M:%S')}] 👀 Retour à la surveillance...")
        
    en_cours_avant = en_cours_maintenant
    
    # Le script se met en pause 5 secondes pour ne pas pomper sur la batterie/CPU
    time.sleep(5)