import json
import urllib.request
import os
import re

# === LA LIGNE MAGIQUE POUR LE DOSSIER ===
os.chdir(os.path.dirname(os.path.abspath(__file__)))
FICHIER_MAPPING = "mapping_jeux.json"

def nettoyer_nom_jeu(nom):
    """Retire les caractères interdits par Windows/FAT32 pour coller aux dossiers JKSV"""
    nom = re.sub(r'[<>:"/\\|?*]', '', str(nom))
    nom = nom.replace('™', '').replace('®', '').replace('©', '')
    return nom.strip()

def main():
    print("=== 🚀 Mise à jour massive de la base de données ===")
    
    mapping_local = {}
    if os.path.exists(FICHIER_MAPPING):
        try:
            with open(FICHIER_MAPPING, 'r', encoding='utf-8') as f:
                mapping_local = json.load(f)
            print(f"📁 {len(mapping_local)} jeux actuellement dans ton fichier.")
        except json.JSONDecodeError:
            print("⚠️ Ton fichier actuel est mal formaté, on va le recréer.")

    print("🌍 Connexion aux serveurs mondiaux (Tinfoil)...")
    url_principale = "https://tinfoil.media/repo/db/titles.json"
    
    try:
        # On se déguise en Google Chrome pour ne pas être bloqué par la sécurité de Tinfoil
        req = urllib.request.Request(url_principale, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req) as response:
            db_totale = json.loads(response.read().decode('utf-8'))
            
        nouveaux_ajouts = 0
        print("⚙️ Téléchargement réussi ! Traitement de plusieurs milliers de jeux...")
        
        for title_id, data in db_totale.items():
            # Les jeux de base finissent toujours par "000" (on ignore les DLC)
            if title_id.endswith("000") and "name" in data:
                nom_nettoye = nettoyer_nom_jeu(data["name"])
                if title_id not in mapping_local:
                    mapping_local[title_id] = nom_nettoye
                    nouveaux_ajouts += 1

        with open(FICHIER_MAPPING, 'w', encoding='utf-8') as f:
            json.dump(mapping_local, f, indent=4, ensure_ascii=False)
            
        print(f"\n🎉 Succès ! {nouveaux_ajouts} nouveaux jeux ont été ajoutés.")
        print(f"📚 Ton fichier '{FICHIER_MAPPING}' contient maintenant {len(mapping_local)} jeux !")
        
    except Exception as e:
        print(f"⚠️ Le serveur principal a refusé la connexion ({e}).")
        print("🔄 Basculement sur le serveur de secours (SwitchBrew)...")
        
        try:
            # Serveur de secours si Tinfoil est en panne
            url_secours = "https://fmartingr.github.io/switch-games-json/switch_games.json"
            req = urllib.request.Request(url_secours, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                db_secours = json.loads(response.read().decode('utf-8'))
            
            nouveaux_ajouts = 0
            for jeu in db_secours:
                title_id = jeu.get("title_id", "")
                nom = jeu.get("description", jeu.get("name", ""))
                
                if title_id and title_id.endswith("000") and nom:
                    nom_nettoye = nettoyer_nom_jeu(nom)
                    if title_id not in mapping_local:
                        mapping_local[title_id] = nom_nettoye
                        nouveaux_ajouts += 1

            with open(FICHIER_MAPPING, 'w', encoding='utf-8') as f:
                json.dump(mapping_local, f, indent=4, ensure_ascii=False)
                
            print(f"\n🎉 Succès via le serveur de secours ! {nouveaux_ajouts} nouveaux jeux ajoutés.")
            print(f"📚 Ton fichier '{FICHIER_MAPPING}' contient maintenant {len(mapping_local)} jeux !")
            
        except Exception as e2:
            print(f"❌ Échec total. Les deux serveurs sont inaccessibles : {e2}")

    input("\nAppuie sur Entrée pour quitter...")

if __name__ == '__main__':
    main()