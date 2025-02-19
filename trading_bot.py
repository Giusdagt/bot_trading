# trading_bot.py - Modulo principale per il trading automatico
import ccxt
import json
import numpy as np
import pandas as pd
import os
import logging
import requests
import threading
import script
import bridge_module
from ai_model import AIModel
from trading_environment import TradingEnv
from drl_agent import DRLAgent
import portfolio_optimization
import risk_management
import tensorflow as tf
import shutil
import time
import subprocess
from flask_socketio import SocketIO

# Crea l'istanza di SocketIO
socketio = SocketIO()

# Funzione per inviare messaggi Telegram
def send_message_telegram(chat_id, message, token="your_telegram_bot_token"):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Errore nell'invio del messaggio Telegram: {e}")

class TradingBot:
    def __init__(self, config_file="config.json"):
        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.accounts = self.config['api_keys']
        self.risk_management = risk_management.RiskManagement(max_risk=0.02, max_drawdown=0.1)
        self.portfolio_optimization = portfolio_optimization.PortfolioOptimization()
        self.bots = []

        for account in self.accounts:
            api_key = account['api_key']
            api_secret = account['api_secret']
            exchange = ccxt.binance({'apiKey': api_key, 'secret': api_secret})
            try:
                exchange.check_required_credentials()
            except Exception as e:
                logging.error(f"Errore nelle credenziali Binance: {e}")
                continue

            trading_pair = [symbol for symbol in exchange.load_markets() if symbol.endswith("/EUR") or symbol.endswith("/USDT")]
            timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "D1"]

            bot = self.create_bot(exchange, trading_pair, timeframes)
            self.bots.append(bot)

    def create_bot(self, exchange, trading_pair, timeframes):
        env = TradingEnv(exchange, trading_pair, timeframes)
        agent = DRLAgent(env)
        ai_model = AIModel(input_shape=(10, 1))  # LSTM Model
        return {
            "exchange": exchange,
            "env": env,
            "agent": agent,
            "ai_model": ai_model
        }

    def send_data_to_dashboard(self, account_name, balance, profit_loss):
        """Invia i dati aggiornati alla dashboard."""
        data = {"account_name": account_name, "balance": balance, "profit_loss": profit_loss}
        socketio.emit('update_account', data)

    def adjust_trading_behavior(self, account_data):
        """Adatta il comportamento di trading in base alle perdite o guadagni di un singolo account"""
        balance = account_data['balance']
        profit_loss = account_data['profit_loss']

        if profit_loss < -0.1:  
            logging.info(f"Account in perdita ({profit_loss}), riduzione del rischio.")
            self.risk_management.set_max_risk(0.01)
        else:
            logging.info(f"Account stabile ({profit_loss}), rischio normale.")
            self.risk_management.set_max_risk(0.02)

    def trade_account(self, bot, account_name, episodes):
        logging.info(f"🚀 Avvio trading per {account_name}...")
        env = bot['env']
        agent = bot['agent']
        ai_model = bot['ai_model']
        total_reward = 0
        chat_id = self.get_telegram_chat_id(account_name)

        for episode in range(episodes):
            logging.info(f"🔄 Episodio {episode + 1}/{episodes} per {account_name}")
            state = env.reset()
            done = False

            while not done:
                try:
                    predicted_price = ai_model.predict(state.reshape(1, -1, 1))
                    action = 0 if predicted_price > state[-1] else 2 if predicted_price < state[-1] else 1
                    next_state, reward, done, _ = env.step(action)
                    agent.train(episodes=1)
                    state = next_state
                    total_reward += reward

                    balance = 100  # ✅ Saldo iniziale fisso a 100€
                    profit_loss = reward  # ✅ Il profitto/perdita viene aggiornato in base al trading reale
                    balance += profit_loss  # ✅ Il saldo aumenta o diminuisce in base al risultato del trade

                    self.adjust_trading_behavior({'balance': balance, 'profit_loss': profit_loss})
                    self.send_data_to_dashboard(account_name, balance, profit_loss)

                    if done:
                        self.send_trade_close_message(chat_id, balance, profit_loss)
                except Exception as e:
                    logging.error(f"❌ Errore durante l'esecuzione dell'episodio: {e}")
                    break

            logging.info(f"✅ Episodio {episode + 1} - Total Reward: {total_reward}")

        logging.info(f"✔️ Trading completato per {account_name}.")

    def get_telegram_chat_id(self, account_name):
        """Ottieni l'ID chat Telegram in base al nome dell'account"""
        chat_ids = {
            "danny": "7508111845:AAHqpY_VpkN8rgHDvir6q3qT2Danxvm4MXU",
            "giuseppe": "7727880063:AAG0PlSbFUZ-ddbErzhHdpcrQmx1XDZzfZQ",
        }
        return chat_ids.get(account_name, None)

    def send_trade_close_message(self, chat_id, balance, profit_loss):
        """Invia un messaggio di chiusura posizione su Telegram"""
        message = f"Posizione chiusa!\nSaldo: {balance} EUR\nProfitto/Perdita: {profit_loss} EUR"
        send_message_telegram(chat_id, message)

# Avvio del bot
if __name__ == "__main__":
    bot = TradingBot()
    bot.trade_account(bot.bots[0], "danny", episodes=10)
    bot.trade_account(bot.bots[1], "giuseppe", episodes=10)
