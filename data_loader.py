#data_loader
import json
import os
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Configurazione logging avanzato
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Percorsi per backup su USB o cloud
BACKUP_DIR = Path("/mnt/usb_trading_data/config_backup") if Path("/mnt/usb_trading_data").exists() else Path("D:/trading_backup")
CLOUD_BACKUP_DIR = Path("/mnt/google_drive/trading_backup")

CONFIG_FILE = "config.json"
MARKET_API_FILE = "market_data_apis.json"
MARKET_DATA_FILE = "market_data.json"

# 📌 Assicurarsi che la directory di backup esista
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
CLOUD_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ===========================
# 🔹 FUNZIONI DI UTILITÀ
# ===========================

def load_config(json_file=CONFIG_FILE):
    """Carica il file config.json (trading). Se il file non esiste, prova a recuperarlo da backup o cloud."""
    if not Path(json_file).exists():
        logging.warning(f"⚠️ Il file {json_file} non esiste! Tentativo di ripristino...")
        restore_backup(json_file)

    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"❌ Errore nel decodificare {json_file}: {e}")
        return None

def load_market_data_apis(json_file=MARKET_API_FILE):
    """Carica il file market_data_apis.json (API di mercato). Se non esiste, tenta il ripristino."""
    if not Path(json_file).exists():
        logging.warning(f"⚠️ Il file {json_file} non esiste! Tentativo di ripristino...")
        restore_backup(json_file)

    try:
        with open(json_file, 'r') as f:
            return json.load(f)['exchanges']
    except json.JSONDecodeError as e:
        logging.error(f"❌ Errore nel decodificare {json_file}: {e}")
        return None

def save_market_data(data, json_file=MARKET_DATA_FILE):
    """Salva i dati di mercato e crea un backup su USB/cloud."""
    try:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=4)
        create_backup(json_file)
        logging.info(f"✅ Dati di mercato salvati in {json_file}")
    except Exception as e:
        logging.error(f"❌ Errore durante il salvataggio dei dati di mercato: {e}")

def get_eur_trading_pairs(market_data):
    """Recupera tutte le coppie di trading in EUR dalle API di mercato."""
    eur_pairs = [market["symbol"] for market in market_data if "/EUR" in market.get("symbol", "")]

    if not eur_pairs:
        logging.warning("⚠️ Nessuna coppia EUR trovata, utilizzo backup.")
        return load_backup("eur_pairs_backup.json")

    save_backup(eur_pairs, "eur_pairs_backup.json")
    return eur_pairs

# ===========================
# 🔹 FUNZIONI DI BACKUP
# ===========================

def create_backup(filename):
    """Crea un backup del file specificato nella directory di backup e su cloud."""
    try:
        file_path = Path(filename)
        if file_path.exists():
            backup_path = BACKUP_DIR / file_path.name
            shutil.copy(file_path, backup_path)
            cloud_backup_path = CLOUD_BACKUP_DIR / file_path.name
            shutil.copy(file_path, cloud_backup_path)
            logging.info(f"✅ Backup creato per {filename} in {BACKUP_DIR} e sincronizzato su Cloud.")
        else:
            logging.warning(f"⚠️ Il file {filename} non esiste e non può essere copiato.")
    except Exception as e:
        logging.error(f"❌ Errore nel backup di {filename}: {e}")

def restore_backup(filename):
    """Ripristina un file da backup locale o cloud se disponibile."""
    backup_path = BACKUP_DIR / filename
    cloud_backup_path = CLOUD_BACKUP_DIR / filename

    if backup_path.exists():
        shutil.copy(backup_path, filename)
        logging.info(f"✅ File {filename} ripristinato con successo da backup locale.")
    elif cloud_backup_path.exists():
        shutil.copy(cloud_backup_path, filename)
        logging.info(f"✅ File {filename} ripristinato con successo da backup Cloud.")
    else:
        logging.error(f"❌ Backup non trovato per {filename}. Il file deve essere ricreato manualmente.")

def save_backup(data, filename):
    """Salva un backup dei dati di configurazione su USB e Cloud."""
    try:
        backup_file = BACKUP_DIR / filename
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=4)

        cloud_file = CLOUD_BACKUP_DIR / filename
        shutil.copy(backup_file, cloud_file)

        logging.info(f"✅ Backup dei dati salvato in {backup_file} e sincronizzato su Cloud.")
    except Exception as e:
        logging.error(f"❌ Errore durante il salvataggio del backup: {e}")

def load_backup(filename):
    """Carica un backup da USB o Cloud se disponibile."""
    backup_file = BACKUP_DIR / filename
    cloud_file = CLOUD_BACKUP_DIR / filename

    if backup_file.exists():
        with open(backup_file, 'r') as f:
            return json.load(f)
    elif cloud_file.exists():
        with open(cloud_file, 'r') as f:
            return json.load(f)
    else:
        logging.warning(f"⚠️ Backup non disponibile per {filename}.")
        return None

# ===========================
# 🔹 ESEMPIO DI UTILIZZO
# ===========================

if __name__ == "__main__":
    try:
        # Carica le configurazioni di trading
        config = load_config()
        logging.info(f"🔹 Config trading: {config}")

        # Carica le API di mercato
        market_data_apis = load_market_data_apis()
        logging.info(f"🔹 API di mercato: {market_data_apis}")

        # Carica i dati salvati (se presenti)
        if Path(MARKET_DATA_FILE).exists():
            with open(MARKET_DATA_FILE, 'r') as f:
                market_data = json.load(f)
            logging.info(f"📊 Market data salvato: {market_data}")

            # 📌 Recupera tutte le coppie EUR in modo automatico
            eur_pairs = get_eur_trading_pairs(market_data)
            logging.info(f"✅ Coppie EUR trovate: {eur_pairs}")
        else:
            logging.warning("⚠️ Nessun dato di mercato salvato trovato.")

    except FileNotFoundError as e:
        logging.error(f"❌ Errore: {e}")
