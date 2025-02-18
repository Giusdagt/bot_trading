import pandas as pd
import numpy as np
import ccxt
import logging
import os
import json
import requests

# Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Percorsi per backup su USB o cloud
BACKUP_DIR = "/mnt/usb_trading_data/trading_pairs" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

class DynamicTradingManager:
    def __init__(self, top_n=5, volatility_threshold=0.02, min_volume=100000, backup_file="eur_pairs_backup.json"):
        """Inizializza il gestore di trading dinamico con gestione avanzata del rischio e failover API."""
        self.top_n = top_n
        self.volatility_threshold = volatility_threshold
        self.min_volume = min_volume
        self.backup_file = os.path.join(BACKUP_DIR, backup_file)

    def get_best_pairs(self, client):
        """Seleziona le migliori coppie di trading EUR basandosi su volatilità e volume, con gestione avanzata degli errori."""
        try:
            markets = client.load_markets()
            pair_data = []

            for pair, info in markets.items():
                if '/EUR' in pair:  # Filtriamo solo coppie EUR
                    try:
                        ticker = client.fetch_ticker(pair)
                        high = ticker['high']
                        low = ticker['low']
                        volume = ticker['quoteVolume']

                        volatility = (high - low) / low if low > 0 else 0

                        if volatility >= self.volatility_threshold and volume >= self.min_volume:
                            pair_data.append((pair, volatility, volume))
                    except Exception as e:
                        logging.warning(f"⚠️ Errore nel caricamento dati per {pair}: {e}")
                        continue  # Se fallisce un'iterazione, passa alla prossima
            
            if not pair_data:
                logging.warning("⚠️ Nessuna coppia EUR trovata, utilizzo backup.")
                return self.load_backup_pairs()

            # Ordiniamo per volatilità e volume
            pair_data.sort(key=lambda x: (x[1], x[2]), reverse=True)
            best_pairs = [pair[0] for pair in pair_data[:self.top_n]]

            # Salvataggio backup
            self.save_backup_pairs(best_pairs)
            return best_pairs

        except Exception as e:
            logging.error(f"❌ Errore nel recupero delle coppie di trading: {e}")
            return self.load_backup_pairs()

    def save_backup_pairs(self, pairs):
        """Salva un backup delle migliori coppie EUR selezionate."""
        try:
            with open(self.backup_file, "w") as file:
                json.dump(pairs, file, indent=4)
            logging.info(f"✅ Backup coppie EUR salvato in {self.backup_file}")
        except Exception as e:
            logging.error(f"⚠️ Errore nel salvataggio del backup coppie EUR: {e}")

    def load_backup_pairs(self):
        """Carica il backup delle coppie EUR selezionate se le API falliscono."""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, "r") as file:
                    pairs = json.load(file)
                logging.info(f"📂 Backup coppie EUR caricato con successo.")
                return pairs
            else:
                logging.warning("⚠️ Nessun backup disponibile.")
                return []
        except Exception as e:
            logging.error(f"❌ Errore nel caricamento del backup coppie EUR: {e}")
            return []

    def decide_action(self, pair, prediction, last_close):
        """Decide l'azione di trading in base alla previsione AI e al livello di rischio."""
        risk_level = self.calculate_risk_level(pair)
        if risk_level > 0.05:  # Se il rischio è troppo alto, riduci le operazioni
            logging.warning(f"⚠️ Rischio elevato per {pair}, limitando le operazioni.")
            return "HOLD"

        if prediction > last_close * 1.01:
            return "BUY"
        elif prediction < last_close * 0.99:
            return "SELL"
        return "HOLD"

    def calculate_risk_level(self, pair):
        """Calcola il livello di rischio basato sulla volatilità recente e sulla liquidità."""
        # Simulazione di un calcolo avanzato di rischio
        risk_score = np.random.uniform(0.01, 0.07)
        logging.info(f"📊 Rischio calcolato per {pair}: {risk_score}")
        return risk_score

# 📌 Esempio di utilizzo con failover API
if __name__ == "__main__":
    try:
        client = ccxt.binance()
        dtm = DynamicTradingManager()
        best_pairs = dtm.get_best_pairs(client)
        logging.info(f"🔹 Migliori coppie EUR selezionate: {best_pairs}")

    except Exception as e:
        logging.error(f"❌ Errore nell'esecuzione principale: {e}")