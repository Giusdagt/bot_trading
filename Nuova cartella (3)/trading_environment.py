import gym
from gym import spaces
import numpy as np
import pandas as pd
import data_handler
import indicators
import risk_management
import portfolio_optimization
import logging
import os
import json
import requests
import time
import script # ✅ Se necessario, genera nuove logiche di trading

script.generate_new_logic()

# 📌 Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Percorsi per backup delle performance di simulazione
BACKUP_DIR = "/mnt/usb_trading_data/trading_simulation" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

CLOUD_BACKTEST_URL = "https://your-cloud-backtesting.com/run"

class TradingEnv(gym.Env):
    """
    Ambiente di trading AI con supporto per scalping ultra-rapido, gestione del rischio avanzata e logging dettagliato.
    """
    def __init__(self, data, initial_balances=None, max_steps=500, max_assets=5, scalping=True):
        super(TradingEnv, self).__init__()

        # ✅ Recupero automatico del saldo iniziale di ogni account
        if initial_balances is None:
            self.accounts = self.get_dynamic_balances()
        else:
            self.accounts = {account: {"balance": initial_balances[account], "shares_held": 0, "net_worth": initial_balances[account]} for account in initial_balances}

        self.current_step = 0
        self.max_steps = max_steps
        self.max_assets = max_assets
        self.scalping = scalping  

        # ✅ Aggiorna il capitale di partenza dinamicamente
        self.update_account_balances()

        self.data = self._verify_and_prepare_data(data)
        self.tickers = self.select_best_trading_pairs()

        # Moduli di gestione del rischio
        self.risk_management = {account: risk_management.RiskManagement(self.accounts[account]["balance"]) for account in self.accounts}

    def get_dynamic_balances(self):
        """
        Recupera dinamicamente i saldi aggiornati di ogni account.
        """
        simulated_account_data = {
            "Danny": {"balance": 100},  
            "Giuseppe": {"balance": 200}  
        }
        return simulated_account_data

    def update_account_balances(self):
        """
        Aggiorna i saldi degli account basandosi sulle operazioni eseguite.
        """
        for account in self.accounts:
            self.accounts[account]["balance"] = self.accounts[account]["net_worth"]
            self.accounts[account]["shares_held"] = 0
        logging.info(f"📊 Saldi aggiornati dinamicamente: {self.accounts}")

    def _verify_and_prepare_data(self, data):
        """Verifica la struttura dei dati e prepara i dati per scalping."""
        if "timestamp" not in data.columns:
            raise ValueError("❌ Errore: Nessuna colonna 'timestamp' trovata nei dati.")

        data["timestamp"] = pd.to_datetime(data["timestamp"], unit='ms', errors='coerce')
        data = data.drop_duplicates(subset=["timestamp", "coin_id"]).set_index("timestamp").sort_index()

        # ✅ Se scalping attivo, seleziona timeframe ultra-veloci
        if self.scalping:
            data = data.resample('5s').ffill()  

        return data

    def step(self, actions):
        """Esegue le operazioni di trading per entrambi gli account, adattando le strategie di scalping."""
        for account, action in actions.items():
            self._take_action(account, action)

        self.current_step += 1
        done = self.current_step >= self.max_steps
        rewards = {account: self.accounts[account]["net_worth"] - self.accounts[account]["balance"] for account in self.accounts}

        # ✅ Controllo del drawdown per scalping
        for account in self.accounts:
            if rewards[account] < -0.05 * self.accounts[account]["balance"]:
                logging.warning(f"⚠️ Drawdown elevato per {account}, fermo le operazioni per protezione.")
                done = True  

        self.log_performance(actions)
        return self._get_state(), rewards, done, {}

    def _take_action(self, account, action):
        """Esegue un'azione di trading con scalping attivo e gestione avanzata del rischio."""
        current_price = self.data.iloc[self.current_step]['close']
        trading_fee = 0.0005 if self.scalping else 0.001  

        if action == 0 and self.accounts[account]["shares_held"] > 0:
            self.accounts[account]["balance"] += (self.accounts[account]["shares_held"] * current_price) * (1 - trading_fee)
            self.accounts[account]["shares_held"] = 0
        elif action == 2 and self.accounts[account]["balance"] > 0:
            invest_amount = self.accounts[account]["balance"] * 0.05 if self.scalping else 0.1  
            self.accounts[account]["shares_held"] += (invest_amount / current_price) * (1 - trading_fee)
            self.accounts[account]["balance"] -= invest_amount

        self.accounts[account]["net_worth"] = self.accounts[account]["balance"] + (self.accounts[account]["shares_held"] * current_price)

    def log_performance(self, actions):
        """
        Registra le operazioni e analizza le performance dello scalping.
        """
        for account, action in actions.items():
            logging.info(f"📈 {account} → Azione: {action}, Balance: {self.accounts[account]['balance']:.2f}, Net Worth: {self.accounts[account]['net_worth']:.2f}")

# ==============================
# 🔹 ESEMPIO DI UTILIZZO
# ==============================

if __name__ == "__main__":
    data = data_handler.load_normalized_data()
    env = TradingEnv(data=data)  # ✅ Ora il bot rileva automaticamente i saldi