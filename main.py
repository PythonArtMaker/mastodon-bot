import os
import time
import random
from mastodon import Mastodon
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import schedule

# === Configuratie ===
MASTODON_API_BASE_URL = "https://mastodon.social"  # Vervang door jouw Mastodon-server
MASTODON_ACCESS_TOKEN = "cvWcM0e3V2xJMekADCEDhqKWEgFrdOBQ1WJkGKdSfqA"
GOOGLE_DRIVE_FOLDER_ID = "1STnwYb3CeT2LkJEvCDcZmBbrORUmiXDY"  # Alleen de map-ID, geen URL
TOEGESTANE_EXTENSIES = (".png", ".jpg", ".jpeg")
GEPOST_LOG = "gepost.txt"

# === Mastodon authenticatie ===
mastodon = Mastodon(
    access_token=MASTODON_ACCESS_TOKEN,
    api_base_url=MASTODON_API_BASE_URL
)

# === Google Drive authenticatie ===
gauth = GoogleAuth()
gauth.LoadClientConfigFile("credentials.json")
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# === Geposte bestanden bijhouden ===
if not os.path.exists(GEPOST_LOG):
    open(GEPOST_LOG, 'w').close()

with open(GEPOST_LOG, 'r') as f:
    geposte_bestanden = set(f.read().splitlines())

def post_random_afbeelding():
    global geposte_bestanden

    # Ophalen van bestanden uit de opgegeven Google Drive-map
    query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"
    bestanden = drive.ListFile({'q': query}).GetList()

    # Filteren van toegestane bestanden (plaatjes) die nog niet gepost zijn
    toegestane_bestanden = [
        bestand for bestand in bestanden
        if bestand['title'].lower().endswith(TOEGESTANE_EXTENSIES)
        and bestand['title'] not in geposte_bestanden
    ]

    if not toegestane_bestanden:
        print("Geen nieuwe afbeeldingen om te posten.")
        return

    # Kies een willekeurig bestand
    bestand = random.choice(toegestane_bestanden)
    bestandsnaam = bestand['title']

    # Downloaden van het bestand
    bestand.GetContentFile(bestandsnaam)

    try:
        # Uploaden naar Mastodon
        media = mastodon.media_post(bestandsnaam)
        mastodon.status_post(status="", media_ids=[media])
        print(f"Gepost: {bestandsnaam}")

        # Bijwerken van het logbestand
        with open(GEPOST_LOG, 'a') as log:
            log.write(f"{bestandsnaam}\n")
        geposte_bestanden.add(bestandsnaam)
    except Exception as e:
        print(f"Fout bij het posten van {bestandsnaam}: {e}")
    finally:
        # Verwijderen van het lokale bestand
        os.remove(bestandsnaam)

# === Planning ===
schedule.every(1).minutes.do(post_random_afbeelding)

print("Bot gestart. Wacht op volgende post...")
while True:
    schedule.run_pending()
    time.sleep(1)
