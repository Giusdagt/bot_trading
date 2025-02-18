import os
import time
import pandas as pd
import asyncio
import json
import logging
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import data_api_module
from indicators import TradingIndicators

# Configurazioni
SAVE_DIRECTORY = "/mnt/usb_trading_data/processed_data" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_data/processed_data"
DATA_FILE = "processed_data.parquet"
RAW_DATA_FILE = "market_data.json"
MAX_AGE = 30 * 24 * 60 * 60  # 30 giorni in secondi
ESSENTIAL_COLUMNS = ["timestamp", "coin_id", "close", "open", "high", "low", "volume"]

# Configurazione logging avanzato
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def ensure_directory_exists(directory):
    """Crea la directory se non esiste."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def should_update_data(filename=DATA_FILE, max_age_days=1):
    """Controlla se i dati devono essere aggiornati."""
    file_path = os.path.join(SAVE_DIRECTORY, filename)
    if not os.path.exists(file_path):
        return True
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return datetime.now() - file_time > timedelta(days=max_age_days)

async def fetch_and_prepare_data():
    """Scarica, elabora e salva i dati, con supporto a cloud e backup USB."""
    try:
        if not should_update_data():
            logging.info("I dati sono già aggiornati. Carico i dati esistenti.")
            return load_processed_data()

        logging.info("Avvio del processo di scaricamento ed elaborazione dei dati...")
        ensure_directory_exists(SAVE_DIRECTORY)

        # Controllo e generazione del file grezzo
        if not os.path.exists(RAW_DATA_FILE):
            logging.warning("File JSON grezzo non trovato. Tentativo di scaricamento dati...")
            await data_api_module.main_fetch_all_data("eur")

        # Elaborazione dei dati grezzi
        return process_raw_data()

    except Exception as e:
        logging.error(f"Errore durante il processo di dati: {e}")
        return pd.DataFrame()

def process_raw_data():
    """Elabora i dati e li salva come parquet, con supporto per API multiple."""
    try:
        with open(RAW_DATA_FILE, "r") as json_file:
            raw_data = json.load(json_file)

        if not raw_data or not isinstance(raw_data, list):
            raise ValueError("Errore: Dati di mercato non disponibili o non validi.")

        historical_data_list = []
        for crypto in raw_data:
            prices = crypto.get("historical_prices", [])
            for entry in prices:
                try:
                    timestamp = entry.get("timestamp")
                    open_price = entry.get("open")
                    high_price = entry.get("high")
                    low_price = entry.get("low")
                    close_price = entry.get("close")
                    volume = entry.get("volume")

                    if timestamp and close_price:
                        historical_data_list.append({
                            "timestamp": timestamp,
                            "coin_id": crypto.get("id", "unknown"),
                            "close": close_price,
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "volume": volume,
                        })
                except Exception as e:
                    logging.error(f"Errore nel parsing dei dati storici per {crypto.get('id', 'unknown')}: {e}")

        df_historical = pd.DataFrame(historical_data_list)

        if df_historical.empty:
            raise ValueError("Errore: Nessun dato storico trovato.")

        df_historical["timestamp"] = pd.to_datetime(df_historical["timestamp"], format="%Y-%m-%d", errors='coerce')

        if df_historical["timestamp"].isnull().any():
            raise ValueError("Errore: Alcuni valori 'timestamp' non sono stati convertiti correttamente.")

        df_historical.set_index("timestamp", inplace=True)
        df_historical.sort_index(inplace=True)

        # Aggiunta indicatori tecnici
        df_historical = TradingIndicators.calculate_indicators(df_historical)

        save_processed_data(df_historical)
        return df_historical

    except Exception as e:
        logging.error(f"Errore durante l'elaborazione dei dati grezzi: {e}")
        return pd.DataFrame()

def save_processed_data(df, filename=DATA_FILE):
    """Salva i dati elaborati su USB o cloud."""
    try:
        ensure_directory_exists(SAVE_DIRECTORY)
        file_path = os.path.join(SAVE_DIRECTORY, filename)
        df.to_parquet(file_path, index=True)
        logging.info(f"Dati salvati in: {file_path}")
    except Exception as e:
        logging.error(f"Errore durante il salvataggio dei dati: {e}")

def load_processed_data(filename=DATA_FILE):
    """Carica i dati elaborati da backup se disponibili."""
    try:
        file_path = os.path.join(SAVE_DIRECTORY, filename)
        if os.path.exists(file_path):
            df = pd.read_parquet(file_path)
            logging.info(f"Dati caricati da: {file_path}")
            return df
        else:
            logging.warning(f"Nessun file trovato in: {file_path}")
            return pd.DataFrame()
    except Exception as e:
        logging.error(f"Errore durante il caricamento dei dati: {e}")
        return pd.DataFrame()

def delete_old_data():
    """Elimina i file più vecchi di MAX_AGE per ottimizzare lo spazio."""
    now = time.time()
    for filename in os.listdir(SAVE_DIRECTORY):
        file_path = os.path.join(SAVE_DIRECTORY, filename)
        if os.path.isfile(file_path) and (now - os.path.getmtime(file_path) > MAX_AGE):
            os.remove(file_path)
            logging.info(f"File eliminato: {file_path}")

if __name__ == "__main__":
    logging.info("Eseguendo test su data_handler...")
    asyncio.run(fetch_and_prepare_data())
    delete_old_data()