import gym
from gym import spaces
import numpy as np
import pandas as pd
import data_handler
from risk_management import RiskManagement
import indicators
import drl_agent
import logging
import os
import json
import requests
from logging.handlers import RotatingFileHandler

# 📌 Configurazione logging avanzata con rotazione dei file
BACKUP_DIR = "/mnt/usb_trading_data/trading_performance" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

log_file = os.path.join(BACKUP_DIR, 'trading_env.log')
handler = RotatingFileHandler(log_file, maxBytes=1e6, backupCount=5)
logging.basicConfig(handlers=[handler], level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 URL per il backup su Cloud
CLOUD_BACKTEST_URL = "https://your-cloud-backtesting.com/run"  # Esempio di API cloud
CLOUD_BACKUP_URL = "https://your-cloud-backup-service.com/upload"

def backup_to_cloud(file_path):
    """Esegue il backup dei dati di trading su cloud."""
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(CLOUD_BACKUP_URL, files={'file': f})
        if response.status_code == 200:
            logging.info("✅ Backup su cloud riuscito.")
        else:
            logging.error("❌ Backup su cloud fallito.")
    except Exception as e:
        logging.error(f"❌ Errore durante il backup su cloud: {e}")

class TradingEnv(gym.Env):
    """
    Ambiente di trading AI con supporto per scalping e multi-account.
    """
    def __init__(self, data: pd.DataFrame, initial_balances={"Danny": 100, "Giuseppe": 100}):
        super(TradingEnv, self).__init__()
        self.data = data_handler.load_normalized_data(data)
        self.current_step = 0
        self.accounts = {account: {"balance": initial_balances[account], "shares_held": 0, "net_worth": initial_balances[account]} for account in initial_balances}
        self.max_steps = len(self.data)

        # Spazio delle azioni: [0 = Sell, 1 = Hold, 2 = Buy]
        self.action_space = spaces.Discrete(3)

        # Spazio delle osservazioni: Dati di mercato + indicatori
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(self.data.shape[1] + len(indicators.get_indicators_list()),), dtype=np.float32
        )

        # Moduli di gestione del rischio per ogni account
        self.risk_management = {account: RiskManagement(self.accounts[account]["balance"], account) for account in self.accounts}

        # AI Trading Agent (DRL) per ogni account
        self.drl_agents = {account: drl_agent.DRLAgent(model_type='PPO', data=self.data) for account in self.accounts}

        # 📌 Modalità scalping per alta volatilità
        self.scalping_mode = {account: False for account in self.accounts}

    def reset(self):
        """Resetta l'ambiente e registra lo stato iniziale per il backtesting."""
        self.current_step = 0
        for account in self.accounts:
            self.accounts[account]["balance"] = self.accounts[account]["net_worth"]
            self.accounts[account]["shares_held"] = 0
            self.scalping_mode[account] = False
        self.log_performance("RESET")
        return self._get_observation()

    def step(self, actions):
        """Esegue un'azione nel mercato per ogni account e registra i dati di performance."""
        for account, action in actions.items():
            self._take_action(account, action)

            # 📌 Attivazione Scalping se il mercato è volatile
            if self._is_scalping_condition():
                logging.info(f"⚡ Attivazione scalping per {account}")
                self.scalping_mode[account] = True

        self.current_step += 1
        done = self.current_step >= self.max_steps - 1
        rewards = {account: self.accounts[account]["net_worth"] - self.accounts[account]["balance"] for account in self.accounts}
        self.log_performance(actions)
        return self._get_observation(), rewards, done, {}

    def _take_action(self, account, action):
        """Esegue un'azione di trading per un account con gestione del rischio e delle commissioni."""
        current_price = self.data.iloc[self.current_step]['close']
        risk_limit = self.risk_management[account].get_risk_level()
        trading_fee = 0.001  # 0.1% commissione di trading

        if action == 0:  # SELL
            if self.accounts[account]["shares_held"] > 0:
                self.accounts[account]["balance"] += (self.accounts[account]["shares_held"] * current_price) * (1 - trading_fee)
                self.accounts[account]["shares_held"] = 0

        elif action == 2:  # BUY
            if self.accounts[account]["balance"] > 0:
                allowed_balance = self.risk_management[account].get_max_investment(self.accounts[account]["balance"])
                invest_amount = min(allowed_balance, risk_limit)
                self.accounts[account]["shares_held"] += (invest_amount / current_price) * (1 - trading_fee)
                self.accounts[account]["balance"] -= invest_amount

        # Aggiorna il net worth
        self.accounts[account]["net_worth"] = self.accounts[account]["balance"] + (self.accounts[account]["shares_held"] * current_price)

    def _is_scalping_condition(self):
        """Determina se il mercato è adatto per lo scalping."""
        volatility = np.std(self.data.iloc[max(0, self.current_step-10):self.current_step]['close'])
        return volatility > 0.02  # Soglia per attivare scalping
