Dans un premier temps

# ☁️ Guide : Configurer le Stockage Distant (Google Drive) sur JKSV

JKSV intègre une fonctionnalité native permettant d'envoyer vos sauvegardes Switch directement sur votre compte Google Drive. Étant donné que Google a renforcé sa sécurité, JKSV ne possède plus de clé universelle. Vous devez donc générer votre propre fichier d'accès (Totalement gratuit).

Voici la marche à suivre étape par étape.

---

## 🛠️ Étape 1 : Créer la clé API Google (Sur PC)

L'objectif ici est de dire à Google : *"J'autorise mon application personnelle JKSV à accéder à mon Drive"*.

1. Rendez-vous sur la [Google Cloud Console](https://console.cloud.google.com/) et connectez-vous avec votre compte Google.
2. En haut à gauche, cliquez sur le menu déroulant des projets, puis sur **Nouveau projet**. Nommez-le `JKSV Sync` et cliquez sur **Créer**. (Attendez quelques secondes qu'il se crée et sélectionnez-le).
3. Dans le menu de gauche, allez dans **API et services** > **Bibliothèque**.
4. Dans la barre de recherche, tapez `Google Drive API`. Cliquez dessus et choisissez **Activer**.
5. Allez ensuite dans l'onglet **Écran de consentement OAuth** (à gauche) :
   - Cochez **Externe** et cliquez sur Créer.
   - Remplissez les champs obligatoires avec n'importe quel nom (ex: *JKSV App*) et votre adresse e-mail. Cliquez sur *Enregistrer et continuer* jusqu'à la fin.
   - De retour sur l'écran de consentement, cliquez sur le bouton **Publier l'application** (très important pour éviter que votre clé n'expire tous les 7 jours).
6. Allez dans l'onglet **Identifiants** (toujours à gauche) :
   - Cliquez sur **+ CRÉER DES IDENTIFIANTS** (en haut de l'écran) puis sur **ID client OAuth**.
   - Type d'application : Choisissez **Entrée TV et limitée.
   - Nommez-la et cliquez sur Créer.
7. Une fenêtre s'ouvre : cliquez sur **TÉLÉCHARGER LE FICHIER JSON**.

---

## 💾 Étape 2 : Placer le fichier sur la Switch

1. Prenez le fichier JSON que vous venez de télécharger sur votre PC.
2. Renommez ce fichier exactement de cette manière : **`client_secret.json`**
3. Insérez la carte SD de votre Switch dans votre PC (ou connectez-la via MTP/DBI).
4. Placez le fichier `client_secret.json` dans le dossier suivant :
   👉 `sd:/config/JKSV/`
   *(Si le dossier `config` ou `JKSV` n'existe pas à la racine de votre carte SD, créez-le manuellement).*

---

## ⚙️ Étape 3 : Paramétrer JKSV (Obligatoire)

Pour que l'envoi vers le Cloud fonctionne, **les sauvegardes doivent impérativement être zippées**.

1. Allumez votre Switch et lancez JKSV (il est recommandé de lancer le Homebrew Menu en **Mode Full RAM**, c'est-à-dire en maintenant le bouton **R** tout en lançant un vrai jeu depuis l'écran d'accueil, cela évite les crashs internet).
2. Dans JKSV, descendez tout en bas de la liste des profils utilisateurs et ouvrez les **Paramètres** (Settings).
3. Cherchez l'option **"Export Saves to ZIP"** et passez-la sur **ON**.
4. Revenez en arrière.

---

## 🔗 Étape 4 : Association avec votre compte Google

1. Dans JKSV, sélectionnez votre utilisateur, choisissez un jeu, et créez une sauvegarde locale (New Backup) de manière classique.
2. Une fois la sauvegarde locale créée, sélectionnez-la avec les flèches, et **appuyez sur la gâchette ZR**.
3. JKSV va détecter le fichier `client_secret.json` et afficher un message à l'écran avec un **code unique**.
4. Sur votre PC ou votre smartphone, ouvrez un navigateur web et allez sur : **[https://google.com/device](https://google.com/device)**.
5. Entrez le code affiché sur l'écran de votre Switch.
6. Connectez-vous à votre compte Google et acceptez les autorisations demandées.

---

## 🎮 Étape 5 : Utilisation au quotidien

C'est terminé ! La console est maintenant liée à votre compte Google Drive.

- **Pour envoyer (Upload) vers Google Drive :** Sur n'importe quelle sauvegarde locale dans JKSV, appuyez sur **ZR**. Une petite icône `[R]` (pour *Remote*) apparaîtra devant le nom de la sauvegarde pour indiquer qu'elle est bien sur le Cloud.
  *(Sur le Drive, les fichiers seront stockés dans un dossier appelé `JKSV`).*

- **Pour télécharger (Download) depuis Google Drive :**
  Les sauvegardes présentes sur votre Cloud apparaîtront dans JKSV (marquées du symbole Cloud ou `[R]`). Il vous suffit d'appuyer sur **A** dessus pour les télécharger sur votre carte SD et les restaurer.
















Ensuite

# ☁️ Eden Cloud Sync - Switch <-> PC Save Synchronizer

**Eden Cloud Sync** est un utilitaire open-source doté d'une interface graphique moderne permettant de synchroniser automatiquement vos sauvegardes de jeux Nintendo Switch entre votre console (via l'outil JKSV et Google Drive) et votre émulateur PC (Eden, Yuzu, Ryujinx, etc.).

Ne perdez plus jamais votre progression en passant de votre canapé à votre bureau ! 🚀

## ✨ Fonctionnalités Principales

- 🔄 **Synchronisation Bidirectionnelle :** Détecte automatiquement la sauvegarde la plus récente (PC ou Cloud) et la restaure ou l'envoie.
- 🤖 **Mode Auto-Sync (Chien de garde) :** Tourne de manière invisible en arrière-plan. Détecte le lancement et la fermeture de votre émulateur pour lancer la synchronisation tout seul.
- 🛡️ **Gestion Intelligente des Conflits :** Si vous avez joué sur les deux plateformes hors-ligne, une fenêtre d'alerte vous demandera quelle sauvegarde conserver.
- 📦 **Archivage Automatique :** Conserve toujours les 2 dernières versions de vos sauvegardes PC sur Google Drive dans un dossier de sécurité.
- 📚 **Base de Données Massive :** Inclut un outil capable de télécharger et d'associer automatiquement les Title IDs de plus de 10 000 jeux Switch.
- 🎨 **Interface Graphique Moderne :** Paramétrez vos dossiers et observez les logs en temps réel via un tableau de bord intuitif (Mode Sombre).

---

## 🛠️ Prérequis et Installation

1. **Python 3.8+** installé sur votre PC (cochez *Add Python to PATH* lors de l'installation).
2. Clonez ce projet dans un dossier.
3. Installez les dépendances via le terminal : `pip install -r requirements.txt`
4. Lancez **`app.py`** et lancez les paramètres pour commencer la config, vous devrez insérer le chemin d'accès de votre utilisateur contenant vos saves eden (souvent "save/000000xxxxxx") !

---

## 🔑 Obtenir sa clé API Google (credentials.json)

1. Rendez-vous sur la [Google Cloud Console](https://console.cloud.google.com/).
2. Connectez-vous avec le compte Google lié à votre JKSV.
3. Créez un nouveau projet ("Switch Sync").
4. Allez dans **API et services** > **Bibliothèque** > Cherchez **Google Drive API** et activez-la.
5. Allez dans **Écran de consentement OAuth** > **Externe** > Remplissez les infos et publiez l'application.
6. Allez dans **Identifiants** > **Créer des identifiants** > **ID client OAuth** > **Application de bureau**.
7. Téléchargez le fichier JSON, renommez-le en **`credentials.json`** et importez-le depuis les paramètres de l'application Eden Cloud Sync.

---
---

