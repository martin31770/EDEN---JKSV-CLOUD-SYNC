# ☁️ Guide: Configuring Remote Storage (Google Drive) on JKSV

JKSV includes a native feature allowing you to send your Switch saves directly to your Google Drive account. Since Google tightened its security, JKSV no longer uses a universal key. Therefore, you must generate your own access file (Completely free).

Here is the step-by-step procedure.

---

## 🛠️ Step 1: Create the Google API Key (On PC)

The goal here is to tell Google: *"I authorize my personal JKSV application to access my Drive"*.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and log in with your Google account.
2. In the top left corner, click on the project drop-down menu, then on **New project**. Name it `JKSV Sync` and click **Create**. (Wait a few seconds for it to be created and select it).
3. In the left menu, go to **APIs & Services** > **Library**.
4. In the search bar, type `Google Drive API`. Click on it and choose **Enable**.
5. Next, go to the **OAuth consent screen** tab (on the left):
   - Check **External** and click Create.
   - Fill in the required fields with any name (e.g., *JKSV App*) and your email address. Click *Save and continue* until the end.
   - Back on the consent screen, click the **Publish App** button (very important to prevent your key from expiring every 7 days).
6. Go to the **Credentials** tab (still on the left):
   - Click on **+ CREATE CREDENTIALS** (at the top of the screen) then on **OAuth client ID**.
   - Application type: Choose **TVs and Limited Input devices**.
   - Name it and click Create.
7. A window will pop up: click on **DOWNLOAD JSON**.

---

## 💾 Step 2: Place the file on the Switch

1. Take the JSON file you just downloaded on your PC.
2. Rename this file exactly like this: **`client_secret.json`**
3. Insert your Switch's SD card into your PC (or connect it via MTP/DBI).
4. Place the `client_secret.json` file in the following folder:
   👉 `sd:/config/JKSV/`
   *(If the `config` or `JKSV` folder does not exist at the root of your SD card, create it manually).*

---

## ⚙️ Step 3: Configure JKSV (Mandatory)

For Cloud upload to work, **saves must absolutely be zipped**.

1. Turn on your Switch and launch JKSV (it is recommended to launch the Homebrew Menu in **Full RAM Mode**, meaning holding the **R** button while launching an actual game from the home screen, this prevents internet crashes).
2. In JKSV, scroll all the way down the user profile list and open **Settings**.
3. Look for the **"Export Saves to ZIP"** option and toggle it to **ON**.
4. Go back.

---

## 🔗 Step 4: Link with your Google account

1. In JKSV, select your user, choose a game, and create a local save (New Backup) as usual.
2. Once the local backup is created, select it with the D-pad/stick, and **press the ZR trigger**.
3. JKSV will detect the `client_secret.json` file and display a message on the screen with a **unique code**.
4. On your PC or smartphone, open a web browser and go to: **[https://google.com/device](https://google.com/device)**.
5. Enter the code displayed on your Switch screen.
6. Log in to your Google account and accept the requested permissions.

---

## 🎮 Step 5: Daily Usage

That's it! The console is now linked to your Google Drive account.

- **To send (Upload) to Google Drive:** On any local save in JKSV, press **ZR**. A small `[R]` icon (for *Remote*) will appear next to the save name to indicate that it is successfully on the Cloud.
  *(On the Drive, files will be stored in a folder named `JKSV`).*

- **To download (Download) from Google Drive:**
  Saves present on your Cloud will appear in JKSV (marked with the Cloud symbol or `[R]`). You just need to press **A** on them to download them to your SD card and restore them.

After JKSV configuration :
  
  # ☁️ Eden Cloud Sync - Switch <-> PC Save Synchronizer

**Eden Cloud Sync** is an open-source utility with a modern graphical interface allowing you to automatically synchronize your Nintendo Switch game saves between your console (via the JKSV tool and Google Drive) and your PC emulator (Eden, Yuzu, Ryujinx, etc.).

Never lose your progress again when moving from your couch to your desk! 🚀

## ✨ Main Features

- 🔄 **Bidirectional Synchronization:** Automatically detects the most recent save (PC or Cloud) and restores or uploads it.
- 🤖 **Auto-Sync Mode (Watchdog):** Runs invisibly in the background. Detects the launch and closure of your emulator to trigger synchronization on its own.
- 🛡️ **Smart Conflict Management:** If you played offline on both platforms, an alert window will ask you which save to keep.
- 📦 **Automatic Archiving:** Always keeps the last 2 versions of your PC saves on Google Drive in a backup folder.
- 📚 **Massive Database:** Includes a tool capable of automatically downloading and linking the Title IDs of over 10,000 Switch games.
- 🎨 **Modern GUI:** Configure your folders and watch real-time logs via an intuitive dashboard (Dark Mode).

---

## 🛠️ Requirements & Installation

1. **Python 3.8+** installed on your PC (check *Add Python to PATH* during installation).
2. Clone this project into a folder.
3. Install the dependencies via the terminal: `pip install -r requirements.txt`
4. Launch **`app.py`** and open the settings to start the configuration, you will need to insert the path to your user folder containing your Eden saves (often "save/000000xxxxxx")!

---

## 🔑 Obtain your Google API Key (credentials.json)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Log in with the Google account linked to your JKSV.
3. Create a new project ("Switch Sync").
4. Go to **APIs & Services** > **Library** > Search for **Google Drive API** and enable it.
5. Go to **OAuth consent screen** > **External** > Fill in the info and publish the app.
6. Go to **Credentials** > **Create Credentials** > **OAuth client ID** > **Desktop app**.
7. Download the JSON file, rename it to **`credentials.json`**, and import it from the settings of the Eden Cloud Sync app.

---
---