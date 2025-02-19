# data_handler.py
import os
import pandas as pd
import asyncio
import json
import logging
import websockets
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import data_api_module
from indicators import TradingIndicators
import shutil

# Configurazioni di salvataggio e backup
SAVE_DIRECTORY = "/mnt/usb_trading_data/processed_data" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_data/processed_data"
HISTORICAL_DATA_FILE = os.path.join(SAVE_DIRECTORY, "historical_data.parquet")
SCALPING_DATA_FILE = os.path.join(SAVE_DIRECTORY, "scalping_data.parquet")
RAW_DATA_FILE = "market_data.json"
MAX_AGE = 30 * 24 * 60 * 60  # 30 giorni in secondi

# WebSocket URL per dati in tempo reale per scalping
WEBSOCKET_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"

# Configurazione logging avanzato
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Creazione dello scaler per la normalizzazione dei dati
scaler = MinMaxScaler()

async def process_websocket_message(message):
    """Elabora il messaggio ricevuto dal WebSocket per dati real-time per scalping."""
    try:
        data = json.loads(message)
        price = float(data["p"])  # Prezzo dell'ultima operazione
        timestamp = datetime.fromtimestamp(data["T"] / 1000.0)  # Converti timestamp

        df = pd.DataFrame([[timestamp, price]], columns=["timestamp", "price"])
        df.set_index("timestamp", inplace=True)

        # Calcolo indicatori tecnici in tempo reale per scalping
        df["rsi"] = TradingIndicators.relative_strength_index(df)
        df["macd"], df["macd_signal"] = TradingIndicators.moving_average_convergence_divergence(df)
        df["ema"] = TradingIndicators.exponential_moving_average(df)
        df["bollinger_upper"], df["bollinger_lower"] = TradingIndicators.bollinger_bands(df)

        # Normalizzazione dei dati per scalping
        df = normalize_data(df)

        # Salvataggio dati per scalping
        save_processed_data(df, SCALPING_DATA_FILE)
        logging.info(f"✅ Dati scalping aggiornati e salvati: {df.tail(1)}")

    except Exception as e:
        logging.error(f"❌ Errore nell'elaborazione del messaggio WebSocket: {e}")

async def consume_websocket():
    """Consuma dati dal WebSocket per operazioni di scalping."""
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        logging.info("✅ Connessione WebSocket stabilita per dati real-time.")
        try:
            async for message in websocket:
                await process_websocket_message(message)
        except websockets.ConnectionClosed:
            logging.warning("⚠️ Connessione WebSocket chiusa. Riconnessione in corso...")
            await asyncio.sleep(5)
            await consume_websocket()
        except Exception as e:
            logging.error(f"❌ Errore durante la ricezione dei dati WebSocket: {e}")
            await asyncio.sleep(5)
            await consume_websocket()

async def fetch_and_prepare_historical_data():
    """Scarica, elabora e normalizza i dati storici."""
    try:
        if not should_update_data(HISTORICAL_DATA_FILE):
            logging.info("✅ Dati storici già aggiornati.")
            return load_processed_data(HISTORICAL_DATA_FILE)

        logging.info("📥 Avvio del processo di scaricamento ed elaborazione dei dati storici...")
        ensure_directory_exists(SAVE_DIRECTORY)

        if not os.path.exists(RAW_DATA_FILE):
            logging.warning("⚠️ File JSON grezzo non trovato. Tentativo di scaricamento dati...")
            await data_api_module.main_fetch_all_data("eur")

        return process_historical_data()

    except Exception as e:
        logging.error(f"❌ Errore durante il processo di dati storici: {e}")
        return pd.DataFrame()

def process_historical_data():
    """Elabora e normalizza i dati storici."""
    try:
        with open(RAW_DATA_FILE, "r") as file:
            raw_data = json.load(file)

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
                    logging.error(f"⚠️ Errore nel parsing dei dati storici per {crypto.get('id', 'unknown')}: {e}")

        df = pd.DataFrame(historical_data_list)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Calcolo degli indicatori tecnici sui dati storici
        df["rsi"] = TradingIndicators.relative_strength_index(df)
        df["macd"], df["macd_signal"] = TradingIndicators.moving_average_convergence_divergence(df)
        df["ema"] = TradingIndicators.exponential_moving_average(df)
        df["bollinger_upper"], df["bollinger_lower"] = TradingIndicators.bollinger_bands(df)

        # Normalizzazione dei dati storici
        df = normalize_data(df)

        save_processed_data(df, HISTORICAL_DATA_FILE)
        logging.info(f"✅ Dati storici normalizzati e salvati.")
        return df

    except Exception as e:
        logging.error(f"❌ Errore durante l'elaborazione dei dati storici: {e}")
        return pd.DataFrame()

def normalize_data(df):
    """Normalizza i dati per il trading AI."""
    try:
        cols_to_normalize = ["close", "open", "high", "low", "volume", "rsi", "macd", "macd_signal", "ema", "bollinger_upper", "bollinger_lower"]
        df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])
        return df
    except Exception as e:
        logging.error(f"❌ Errore durante la normalizzazione dei dati: {e}")
        return df


::contentReference[oaicite:0]{index=0}
 
