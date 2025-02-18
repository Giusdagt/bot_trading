#data_loader
import json
import os
import logging
import shutil

# Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Percorsi per backup su USB o cloud
BACKUP_DIR = "/mnt/usb_trading_data/config_backup" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_backup"
CONFIG_FILE = "config.json"
MARKET_API_FILE = "market_data_apis.json"
MARKET_DATA_FILE = "market_data.json"

# 📌 Assicurarsi che la directory di backup esista
os.makedirs(BACKUP_DIR, exist_ok=True)

# ===========================
# 🔹 FUNZIONI DI UTILITÀ
# ===========================

def load_config(json_file=CONFIG_FILE):
    """Carica il file config.json (trading). Se il file non esiste, prova a recuperarlo da backup."""
    if not os.path.exists(json_file):
        logging.warning(f"⚠️ Il file {json_file} non esiste! Tentativo di ripristino da backup...")
        restore_backup(json_file)

    with open(json_file, 'r') as f:
        return json.load(f)

def load_market_data_apis(json_file=MARKET_API_FILE):
    """Carica il file market_data_apis.json (API di mercato). Se non esiste, tenta il ripristino."""
    if not os.path.exists(json_file):
        logging.warning(f"⚠️ Il file {json_file} non esiste! Tentativo di ripristino da backup...")
        restore_backup(json_file)

    with open(json_file, 'r') as f:
        return json.load(f)['exchanges']

def save_market_data(data, json_file=MARKET_DATA_FILE):
    """Salva i dati di mercato e crea un backup su USB/cloud."""
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)
    create_backup(json_file)
    logging.info(f"✅ Dati di mercato salvati in {json_file}")

def get_eur_trading_pairs(market_data):
    """Recupera tutte le coppie di trading in EUR dalle API di mercato."""
    eur_pairs = []
    for market in market_data:
        pair = market.get("symbol", "")
        if "/EUR" in pair:
            eur_pairs.append(pair)
    
    if not eur_pairs:
        logging.warning("⚠️ Nessuna coppia EUR trovata, utilizzo backup.")
        return load_backup("eur_pairs_backup.json")

    save_backup(eur_pairs, "eur_pairs_backup.json")
    return eur_pairs

# 📌 Backup automatico dei file di configurazione
def create_backup(filename):
    """Crea un backup del file specificato nella directory di backup."""
    try:
        backup_path = os.path.join(BACKUP_DIR, filename)
        shutil.copy(filename, backup_path)
        logging.info(f"✅ Backup creato per {filename} in {BACKUP_DIR}")
    except Exception as e:
        logging.error(f"⚠️ Errore nel backup di {filename}: {e}")

def restore_backup(filename):
    """Ripristina un file da backup se disponibile."""
    backup_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(backup_path):
        shutil.copy(backup_path, filename)
        logging.info(f"✅ File {filename} ripristinato con successo da backup.")
    else:
        logging.error(f"❌ Backup non trovato per {filename}. Il file deve essere ricreato manualmente.")

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
        if os.path.exists(MARKET_DATA_FILE):
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