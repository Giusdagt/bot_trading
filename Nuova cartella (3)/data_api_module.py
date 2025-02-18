# data_api_module.py
import json
import os
import logging
import sys
import aiohttp
import asyncio
import random
from datetime import datetime
from data_loader import load_market_data_apis

# Impostazione del loop per Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configurazione del logging avanzato
logging.basicConfig(level=logging.INFO)

# Numero di giorni di dati storici da scaricare
DAYS_HISTORY = 60  # Default: 60 giorni

# Limite massimo di richieste per minuto (CoinGecko = 30)
REQUESTS_PER_MINUTE = 30
request_count = 0  # Contatore richieste

# Caricare le API disponibili
services = load_market_data_apis()
coingecko_service = next((ex for ex in services if ex["name"].lower() == "coingecko"), None)

if not coingecko_service:
    logging.error("Errore: CoinGecko non trovato nel JSON.")
    sys.exit(1)

API_KEY = coingecko_service["api_key"]

# 📌 Backup dei dati in locale o su USB
STORAGE_PATH = "/mnt/usb_trading_data/market_data.json" if os.path.exists("/mnt/usb_trading_data") else "market_data.json"

# ===========================
# 🔹 FUNZIONI DI UTILITÀ
# ===========================

def calculate_throttle_delay(requests_per_minute):
    return max(2, 60 / requests_per_minute)

async def fetch_market_data(session, currency, delay, retries=5):
    """Scarica i dati di mercato attuali e salva un backup in caso di errore."""
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={currency}&order=market_cap_desc&per_page=250&page=1&sparkline=false&x_cg_demo_api_key={API_KEY}"

    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    save_backup(data, "market_data_backup.json")
                    return data
                elif response.status in {400, 429}:
                    wait_time = random.randint(20, 40)
                    logging.warning(f"Errore {response.status}. Attesa {wait_time} secondi...")
                    await asyncio.sleep(wait_time)
        except Exception as e:
            logging.error(f"Errore nella richiesta API {currency}: {e}")
            await asyncio.sleep(delay)

    return load_backup("market_data_backup.json")

async def fetch_historical_data(session, coin_id, currency, delay, days=DAYS_HISTORY, retries=5):
    """Scarica i dati storici, con gestione avanzata degli errori e failover."""
    global request_count

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={currency}&days={days}&interval=daily&x_cg_demo_api_key={API_KEY}"
    logging.info(f"Scaricando dati storici per {coin_id} ({currency}) da {url}")

    request_count += 1
    if request_count >= REQUESTS_PER_MINUTE:
        logging.warning("⚠️ Raggiunto il limite di richieste! Attesa di 60 secondi...")
        await asyncio.sleep(60)
        request_count = 0

    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    save_backup(data, f"{coin_id}_historical_backup.json")
                    return format_historical_data(data)

        except Exception as e:
            logging.error(f"Errore nella richiesta storica {coin_id}: {e}")
            await asyncio.sleep(delay)

    return load_backup(f"{coin_id}_historical_backup.json")

async def main_fetch_all_data(currency):
    """Scarica sia i dati di mercato attuali che quelli storici, con supporto a backup USB."""
    async with aiohttp.ClientSession() as session:
        delay = calculate_throttle_delay(30)

        market_data = await fetch_market_data(session, currency, delay)

        if not market_data:
            logging.error("❌ Errore: dati di mercato non disponibili, uso backup.")
            market_data = load_backup("market_data_backup.json")

        final_data = []
        for crypto in market_data[:10]:
            coin_id = crypto.get("id")
            if not coin_id:
                continue

            historical_data = await fetch_historical_data(session, coin_id, currency, delay)
            crypto["historical_prices"] = historical_data
            final_data.append(crypto)

        save_backup(final_data, STORAGE_PATH)
        return final_data

def save_backup(data, filename):
    """Salva un backup locale o su USB dei dati API."""
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    logging.info(f"✅ Backup dati salvato in {filename}.")

def load_backup(filename):
    """Carica i dati salvati in precedenza in caso di errore API."""
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    logging.warning(f"⚠️ Backup {filename} non trovato, impossibile recuperare dati.")
    return []

if __name__ == "__main__":
    asyncio.run(main_fetch_all_data("eur"))