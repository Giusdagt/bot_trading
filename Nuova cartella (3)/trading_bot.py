# trading_bot.py - Modulo principale per il trading automatico
import ccxt
import main
import json
import numpy as np
import pandas as pd
import os
import logging
import requests
from ai_model import AIModel
from trading_environment import TradingEnv
from drl_agent import DRLAgent
import portfolio_optimization
import risk_management
from flask_socketio import SocketIO
import script # ✅ Per la generazione automatica di moduli e strategie AI
import bridge_module  # ✅ Per collegare i nuovi moduli generati

# 📌 Configurazione logging avanzato
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

script.generate_new_logic()  # ✅ Avvia la generazione se necessario
bridge_module.load_custom_modules()

# Crea l'istanza di SocketIO per la dashboard
socketio = SocketIO()

# ✅ Funzione per inviare messaggi via Telegram
def send_message_telegram(chat_id, message, token="your_telegram_bot_token"):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"⚠️ Errore nell'invio del messaggio Telegram: {e}")

class TradingBot:
    def __init__(self, config_file="config.json"):
        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.accounts = self.config['api_keys']
        self.risk_management = risk_management.RiskManagement(max_risk=0.02, max_drawdown=0.1)
        self.portfolio_optimization = portfolio_optimization.PortfolioOptimization()
        self.bots = []

        for account_name, credentials in self.accounts.items():
            api_key = credentials['api_key']
            api_secret = credentials['api_secret']
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret
            })

            try:
                exchange.check_required_credentials()
                logging.info(f"✅ Credenziali verificate per {account_name}.")
            except Exception as e:
                logging.error(f"❌ Errore nelle credenziali di {account_name}: {e}")
                continue

            markets = exchange.load_markets()
            trading_pairs = [symbol for symbol in markets if symbol.endswith("/EUR") or symbol.endswith("/USDT")]
            timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "D1"]
            
            bot = self.create_bot(account_name, exchange, trading_pairs, timeframes)
            self.bots.append(bot)

    def create_bot(self, account_name, exchange, trading_pairs, timeframes):
        """Crea un bot di trading personalizzato per ogni account"""
        env = TradingEnv(exchange, trading_pairs, timeframes)
        agent = DRLAgent(env)
        ai_model = AIModel(input_shape=(10, 1))
        return {
            "name": account_name,
            "exchange": exchange,
            "env": env,
            "agent": agent,
            "ai_model": ai_model
        }

    def trade_account(self, bot, episodes):
        """Esegue il trading automatico per un account"""
        logging.info(f"🚀 Inizio trading per {bot['name']}...")
        env = bot['env']
        agent = bot['agent']
        ai_model = bot['ai_model']
        total_reward = 0
        chat_id = self.get_telegram_chat_id(bot['name'])

        for episode in range(episodes):
            logging.info(f"🔄 Episodio {episode + 1}/{episodes} in corso per {bot['name']}...")
            state = env.reset()
            done = False

            while not done:
                try:
                    predicted_price = ai_model.predict(state.reshape(1, -1, 1))

                    if predicted_price > state[-1]:
                        action = 0  # Buy
                    elif predicted_price < state[-1]:
                        action = 2  # Sell
                    else:
                        action = 1  # Hold

                    next_state, reward, done, _ = env.step(action)
                    agent.train(episodes=1)
                    state = next_state
                    total_reward += reward

                    balance = np.random.uniform(1000, 1100)
                    profit_loss = np.random.uniform(-50, 50)

                    self.send_data_to_dashboard(bot['name'], balance, profit_loss)

                    if done:
                        self.send_trade_close_message(chat_id, balance, profit_loss)
                except Exception as e:
                    logging.error(f"❌ Errore durante il trading di {bot['name']}: {e}")
                    break

            logging.info(f"✅ Episodio {episode + 1} completato - Total Reward: {total_reward}")

        logging.info(f"🎯 Trading completato per {bot['name']}.")

    def send_data_to_dashboard(self, account_name, balance, profit_loss):
        """Invia i dati aggiornati alla dashboard"""
        data = {"account_name": account_name, "balance": balance, "profit_loss": profit_loss}
        socketio.emit('update_account', data)

    def get_telegram_chat_id(self, account_name):
        """Ottieni l'ID chat Telegram in base al nome dell'account"""
        chat_ids = {
            "danny": "7508111845",
            "giuseppe": "7727880063",
        }
        return chat_ids.get(account_name, None)

    def send_trade_close_message(self, chat_id, balance, profit_loss):
        """Invia un messaggio su Telegram alla chiusura della posizione"""
        message = f"🚀 Posizione chiusa!\nSaldo: {balance} EUR\nProfitto/Perdita: {profit_loss} EUR"
        send_message_telegram(chat_id, message)

# ✅ Avvio del bot
if __name__ == "__main__":
    bot = TradingBot()
    for b in bot.bots:
        bot.trade_account(b, episodes=10)

import ccxt
import main
import json
import numpy as np
import pandas as pd
import os
import logging
import requests
import threading
import script  # ✅ Per la generazione automatica di moduli e strategie AI
import bridge_module  # ✅ Per collegare i nuovi moduli generati
from ai_model import AIModel
from trading_environment import TradingEnv
from drl_agent import DRLAgent
import portfolio_optimization
import risk_management
import tensorflow as tf
import shutil
import time
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Riconoscimento automatico della chiavetta USB (anche se cambi porta)
USB_PATHS = ["/mnt/usb_trading_data/", "/media/usb/", "/mnt/external_usb/", "D:/trading_backup/", "E:/trading_backup/"]
USB_PATH = next((path for path in USB_PATHS if os.path.exists(path)), "backup_data/")

if not os.path.exists(USB_PATH):
    try:
        result = subprocess.run(["lsblk", "-o", "NAME,MOUNTPOINT"], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if "/media" in line or "/mnt" in line:
                USB_PATH = line.split()[1]
                break
    except Exception as e:
        logging.error(f"⚠️ Errore nel riconoscimento della USB: {e}")
        USB_PATH = "backup_data/"

def save_trade_data(account_name, data):
    """Salva i dati di trading in USB o backup locale."""
    save_path = os.path.join(USB_PATH, f"{account_name}_trades.json")
    try:
        with open(save_path, "w") as f:
            json.dump(data, f)
        logging.info(f"✅ Dati di trading salvati in: {save_path}")
    except Exception as e:
        logging.error(f"❌ Errore nel salvataggio dei dati su USB: {e}")

# ✅ Sincronizzazione automatica dei dati con Google Drive quando il PC è spento
CLOUD_BACKUP = "/mnt/google_drive/trading_backup/"

def sync_to_cloud():
    """Sincronizza i dati di trading con il cloud se la USB non è disponibile"""
    if not os.path.exists(USB_PATH):
        shutil.copytree("backup_data/", CLOUD_BACKUP, dirs_exist_ok=True)
        logging.info("☁️ Dati di trading sincronizzati su Google Drive.")

class TradingBot:
    def __init__(self, config_file="config.json"):
        script.generate_new_logic()  # ✅ Generazione automatica delle strategie AI
        bridge_module.load_custom_modules()  # ✅ Caricamento dinamico dei moduli personalizzati

        try:
            with open(config_file, "r") as file:
                self.config = json.load(file)
            self.exchange = ccxt.binance({
                'apiKey': self.config["api_key"],
                'secret': self.config["api_secret"]
            })
            self.exchange.load_markets()
        except Exception as e:
            logging.error(f"⚠️ Errore nel caricamento dell'exchange: {e}")
            return

    def trade(self, account_name, data):
        """Esegue le operazioni di trading e salva i dati."""
        try:
            decision = AIModel.predict(data)
            if decision == "BUY":
                logging.info(f"{account_name}: Acquisto eseguito")
            elif decision == "SELL":
                logging.info(f"{account_name}: Vendita eseguita")
            
            save_trade_data(account_name, data)  # ✅ Salvataggio su USB o cloud
        except Exception as e:
            logging.error(f"Errore durante l'operazione di trading: {e}")

    def backtest(self, account_name, historical_data):
        """Esegue un backtest sulle strategie AI."""
        env = TradingEnv(historical_data, backtest=True)
        agent = DRLAgent(env)
        agent.train(episodes=100)
        logging.info(f"{account_name}: Backtest completato")

# ✅ Aumento della potenza di calcolo con multi-threading per il trading parallelo
def run_trading(account_name, exchange):
    """Esegue il trading in parallelo per più account."""
    bot = TradingBot(account_name, exchange)
    bot.trade()

threads = []
for account in ["Danny", "Giuseppe"]:
    t = threading.Thread(target=run_trading, args=(account, "Binance"))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# ✅ Distribuzione del carico tra CPU e GPU automaticamente
if tf.config.list_physical_devices('GPU'):
    device = "/GPU:0"
else:
    device = "/CPU:0"

with tf.device(device):
    model = tf.keras.models.Sequential([...])

if __name__ == "__main__":
    bot = TradingBot()
    bot.trade("Danny", {"price": 40000, "volume": 1.5})
    bot.backtest("Giuseppe", {"historical_prices": [39000, 39500, 40000, 40500]})
